"""Stage: animated HTML scenes, captured frame by frame in headless Chromium.

A `stage` segment is drawn by a real web page and captured one frame per video frame, so
motion design is written in HTML, CSS and SVG and still timed to the narration by the kit.
The page contract (window.STAGE_INPUT, window.stageReady, window.stageSeek) is
stage/API.md. The kit keeps doing what it does around it: synthesise and measure the cues,
size the segment, then burn captions and the progress bar over the captured frames.

    {"type": "stage", "name": "e1-phrase", "html": "episodes/stage/e1.html",
     "scene": "phrase", "params": {...}, "narration": ["cue 0", "cue 1"]}

prepare() measures this segment's cues through build.layout, captures every frame once
into artifacts/<id>/stage-<name>-<key12>/ and hands the painter a page whose frame(t) is
the captured picture at t. The key covers the page, the series library, the engine, the
site it embeds, the timings and the canvas, so an edit anywhere recaptures and an
unchanged scene is never captured twice. Frames are split into contiguous chunks across
STAGE_WORKERS browsers (default min(6, cpu-1)) because seek-and-screenshot is the cost.

`stage_preview.py` renders a few instants of the same page into one contact sheet without
a build, which is the quick look while a scene is being written.
"""

from __future__ import annotations

import hashlib
import http.server
import io
import json
import math
import os
import queue as queue_module
import re
import shutil
import struct
import sys
import threading
import time
import urllib.parse
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

from PIL import Image

import style
import theme

KIT = Path(__file__).resolve().parent
REPO = KIT.parents[1]
SITE = REPO / "site"
ENGINE_JS = KIT / "stage" / "stage.js"
SERIES = REPO / "episodes" / "stage"
FOOTAGE = REPO / "footage" / "clean"

VIEWPORT = (1920, 1080)
"""CSS pixels. The device scale factor makes the screenshot the canvas size."""
READY_TIMEOUT = 60.0
SEEK_TIMEOUT_MS = 20000
DONE = "done.json"
CAPTURE_VERSION = "stage-capture-1"
"""Part of the cache key, so a change to how frames are captured recaptures them."""
MIN_CHUNK = 24
"""Fewer frames than this per browser and its start-up costs more than it saves."""
POSTER_AT = 0.6
LOG_EVERY = 5.0
MEDIA = {".mp4", ".m4v", ".mov", ".webm", ".mkv"}
BIG = 16 * 1024 * 1024
"""Media and anything larger than this is keyed by size and mtime rather than content."""
SKIP_DIRS = {".git", "node_modules", "__pycache__"}

MIME = {
    ".html": "text/html; charset=utf-8", ".htm": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8", ".mjs": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8", ".json": "application/json; charset=utf-8",
    ".map": "application/json; charset=utf-8", ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8", ".srt": "text/plain; charset=utf-8",
    ".vtt": "text/vtt; charset=utf-8", ".xml": "application/xml",
    ".svg": "image/svg+xml", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".avif": "image/avif", ".ico": "image/x-icon",
    ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf", ".otf": "font/otf",
    ".mp4": "video/mp4", ".m4v": "video/mp4", ".webm": "video/webm", ".mov": "video/quicktime",
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".ogg": "audio/ogg",
    ".wasm": "application/wasm", ".pdf": "application/pdf",
}

# Resolves window.stageReady once and reports its state on every poll.
READY_PROBE = """() => {
  const probe = window.__stageCapture;
  if (!probe) {
    if (!window.stageReady) return "absent";
    window.__stageCapture = { state: "pending" };
    Promise.resolve(window.stageReady).then(
      () => { window.__stageCapture.state = "ready"; },
      (e) => { window.__stageCapture.state = "failed:" + String((e && (e.stack || e.message)) || e); });
    return "pending";
  }
  return probe.state;
}"""

SEEK = """async ([t, limit]) => {
  const result = window.stageSeek(t);
  if (result && typeof result.then === "function") {
    let timer;
    await Promise.race([result, new Promise((_, reject) => {
      timer = setTimeout(() => reject(new Error(`stageSeek(${t}) did not settle in ${limit} ms`)), limit);
    })]);
    clearTimeout(timer);
  }
  return true;
}"""


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def frame_count(seconds: float, fps: int) -> int:
    """The same count build.render_frames paints, so every painted frame has a capture."""
    return max(1, round(seconds * fps))


def frame_name(index: int) -> str:
    return f"{index:06d}.png"


def poster_index(total: int) -> int:
    return max(0, min(total - 1, round(POSTER_AT * total)))


def device_scale(canvas) -> float:
    """Canvas width over 1920 for a 16:9 canvas; a different aspect fits inside it."""
    return min(canvas[0] / VIEWPORT[0], canvas[1] / VIEWPORT[1])


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "stage"


def _same_aspect(size, canvas) -> bool:
    return abs(size[0] / size[1] - canvas[0] / canvas[1]) < 0.01


def repo_path(html: str) -> tuple[str, Path]:
    """A stage page as (repo-relative posix path, absolute path). It must live in the repo,
    because the capture server only serves the repo (under /__repo/) and the site."""
    raw = Path(html)
    absolute = raw if raw.is_absolute() else REPO / raw
    absolute = Path(os.path.normpath(absolute))
    try:
        relative = absolute.relative_to(REPO).as_posix()
    except ValueError:
        raise RuntimeError(f"stage html {html!r} is outside the repo {REPO}") from None
    if not absolute.is_file():
        raise RuntimeError(f"stage html not found: {relative} (paths are relative to {REPO})")
    return relative, absolute


def default_workers() -> int:
    env = os.environ.get("STAGE_WORKERS", "").strip()
    if env:
        return max(1, int(env))
    return min(6, max(1, (os.cpu_count() or 2) - 1))


# ---------------------------------------------------------------------------
# timing: the cues as the build measured them, in segment-local seconds
# ---------------------------------------------------------------------------

_LAYOUTS: dict = {}


def _layout(project: dict, work: Path):
    """build.layout, memoised for one project state, since every stage segment asks."""
    import build  # lazy: build imports the scene registry, which imports this module

    key = (str(work), json.dumps(project, sort_keys=True, default=str))
    if key not in _LAYOUTS:
        _LAYOUTS.clear()
        _LAYOUTS[key] = build.layout(project, Path(work))
    return _LAYOUTS[key]


def _plan_for(segment: dict, plans: list[dict]) -> dict:
    for plan in plans:
        if plan["segment"] is segment:
            return plan
    name = segment.get("name")
    named = [plan for plan in plans if name and plan["segment"].get("name") == name]
    if len(named) == 1:
        return named[0]
    if len(named) > 1:
        raise RuntimeError(f"stage segment name {name!r} is used {len(named)} times; names must be unique")
    # a stage pane inside a compose, or the base under an overlay, rides its parent's clock
    for plan in plans:
        parent = plan["segment"]
        inner = list(parent.get("panes") or []) + ([parent["under"]] if parent.get("under") else [])
        if any(item is segment or (name and item.get("name") == name) for item in inner):
            return plan
    raise RuntimeError(f"stage segment {name!r} is not in the project, so it has no timing")


_MARKUP = re.compile(r"\[([^\]]*)\]\(/[^)]*/\)")


def _said(replacement) -> list[str]:
    """The words the engine says for a lexicon replacement (phoneme markup keeps its word)."""
    return _MARKUP.sub(r"\1", str(replacement)).split()


def _share(tokens: list[str], said: list[str]):
    """How many spoken words each written token of a lexicon phrase takes: tokens that read
    as themselves (ZIP and zip, ZEC and ZEC) take one word from either end, the rest share
    the middle. None when they cannot be placed."""
    key = lambda s: re.sub(r"[^\w']", "", s).lower()  # noqa: E731
    counts = [0] * len(tokens)
    lo, hi, slo, shi = 0, len(tokens), 0, len(said)
    while lo < hi - 1 and slo < shi and key(tokens[lo]) == key(said[slo]):
        counts[lo] = 1; lo += 1; slo += 1  # noqa: E702
    while hi - 1 > lo and shi > slo and key(tokens[hi - 1]) == key(said[shi - 1]):
        counts[hi - 1] = 1; hi -= 1; shi -= 1  # noqa: E702
    rest, words = hi - lo, shi - slo
    if words < rest:
        return None
    base, extra = divmod(words, rest)
    for k in range(rest):
        counts[lo + k] = base + (1 if k < extra else 0)
    return counts


def _written_words(words: list, text: str, lexicon: dict | None) -> list:
    """Carry the engine's word times over to the written words of the line.

    The engine reads the line after the lexicon ("ZIP 317" is read "zip three seventeen"),
    so its words are the respelling. Captions keep the written form (episodes/SCRIPTS.md), so
    each written token of a respelled phrase takes the times of the spoken words it became:
    "ZIP" gets "zip", "317." gets "three seventeen.". A line with no respelled phrase (phoneme
    markup keeps its word) comes back unchanged, and so do counts that do not line up.
    """
    if not words or not lexicon or not text:
        return words
    keys = tuple(key for key in lexicon if key)
    if not keys:
        return words
    import voice  # the same phrase matching the engine input went through

    pattern = voice._lexicon_pattern(keys)
    found = list(pattern.finditer(text))
    if not any(_said(lexicon[m.group(0)]) != m.group(0).split() for m in found):
        return words
    units: list[list] = []  # [written token, spoken word count]

    def plain(chunk: str) -> None:
        tokens = chunk.split()
        if tokens and units and chunk[:1].strip():  # punctuation glued to the phrase before it
            units[-1][0] += tokens.pop(0)
        units.extend([token, 1] for token in tokens)

    pos = 0
    for match in found:
        plain(text[pos:match.start()])
        tokens, said = match.group(0).split(), _said(lexicon[match.group(0)])
        counts = _share(tokens, said)
        if counts is None:
            return words
        units.extend([token, count] for token, count in zip(tokens, counts))
        pos = match.end()
    plain(text[pos:])
    if sum(count for _, count in units) != len(words) or any(count < 1 for _, count in units):
        return words
    out, i = [], 0
    for token, count in units:
        out.append([words[i][0], words[i + count - 1][1], token])
        i += count
    return out


def _cue_words(cue, start: float, lexicon: dict | None = None) -> list:
    words = cue.words
    if words is None:
        marks = Path(cue.path).with_suffix(".words.json")
        if marks.exists():
            try:
                words = json.loads(marks.read_text(encoding="utf-8"))
            except ValueError:
                words = None
    words = _written_words([[float(w[0]), float(w[1]), str(w[2])] for w in (words or [])], cue.text, lexicon)
    return [[round(start + float(w[0]), 4), round(start + float(w[1]), 4), str(w[2])] for w in words]


def segment_timing(segment: dict, project: dict, work: Path) -> dict:
    """seconds, offset and cues [{start, end, text, words}] for one segment, segment-local.

    The cue text is the written line (never the lexicon respelling), start is when its voice
    starts, end is when its voice stops, and words are the engine's word times moved onto
    the segment clock. offset is where the segment starts in the uncomposited video.
    """
    plans, _, _ = _layout(project, work)
    plan = _plan_for(segment, plans)
    cues = []
    for beat, cue in zip(plan["beats"], plan["cues"]):
        start = float(beat[0])
        cues.append({
            "start": round(start, 4),
            "end": round(start + cue.seconds, 4),
            "text": cue.text,
            "words": _cue_words(cue, start, project.get("lexicon")),
        })
    return {"seconds": plan["seconds"], "offset": plan["offset"], "cues": cues}


# ---------------------------------------------------------------------------
# the cache key
# ---------------------------------------------------------------------------

def _digest_file(digest, path: Path, label: str) -> None:
    if not path.is_file():
        digest.update(f"{label}:missing\n".encode("utf-8"))
        return
    stat = path.stat()
    if path.suffix.lower() in MEDIA or stat.st_size > BIG:
        digest.update(f"{label}:{stat.st_size}:{stat.st_mtime_ns}\n".encode("utf-8"))
        return
    digest.update(f"{label}:{stat.st_size}\n".encode("utf-8"))
    digest.update(path.read_bytes())


def _digest_tree(digest, root: Path, label: str) -> None:
    if not root.is_dir():
        digest.update(f"{label}:missing\n".encode("utf-8"))
        return
    found = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for name in files:
            found.append(Path(folder) / name)
    for path in sorted(found, key=lambda p: p.relative_to(root).as_posix()):
        _digest_file(digest, path, f"{label}/{path.relative_to(root).as_posix()}")


def cache_key(html_path: Path, stage_input: dict, canvas) -> str:
    digest = hashlib.sha256()
    digest.update(f"{CAPTURE_VERSION}\n".encode("utf-8"))
    _digest_file(digest, html_path, f"html:{html_path.relative_to(REPO).as_posix()}")
    # Only the shared library: each episode page is keyed by its own html above, so editing
    # e2.html never recaptures e1.
    _digest_tree(digest, SERIES / "lib", "episodes/stage/lib")
    _digest_file(digest, ENGINE_JS, "stage.js")
    _digest_tree(digest, SITE, "site")
    _digest_tree(digest, FOOTAGE, "footage/clean")
    digest.update(json.dumps(stage_input, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    digest.update(f"\ncanvas:{canvas[0]}x{canvas[1]}".encode("utf-8"))
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# the capture server: /__repo/<path> from the repo, /<path> from the site
# ---------------------------------------------------------------------------

def _parse_range(header: str, size: int):
    match = re.fullmatch(r"\s*bytes\s*=\s*(\d*)\s*-\s*(\d*)\s*(?:,.*)?", header)
    if not match or size == 0:
        return None
    first, last = match.groups()
    if not first and not last:
        return None
    if not first:  # a suffix range: the last N bytes
        count = int(last)
        return (max(0, size - count), size - 1) if count else None
    start = int(first)
    end = size - 1 if not last else min(int(last), size - 1)
    if start >= size or end < start:
        return None
    return start, end


class _Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "stage/1"

    def log_message(self, format, *args):  # noqa: A002 - the base class names it
        pass

    def do_HEAD(self):  # noqa: N802 - the base class names it
        self._serve(head=True)

    def do_GET(self):  # noqa: N802
        self._serve(head=False)

    def _plain(self, status: int, text: str, extra: dict | None = None) -> None:
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _serve(self, head: bool) -> None:
        split = urllib.parse.urlsplit(self.path)
        path = urllib.parse.unquote(split.path)
        if path == "/__repo" or path.startswith("/__repo/"):
            root, rel = REPO, path[len("/__repo"):]
        else:
            root, rel = SITE, path
        parts = [part for part in rel.replace("\\", "/").split("/") if part not in ("", ".")]
        if ".." in parts:
            return self._plain(403, "outside the served roots")
        target = root.joinpath(*parts)
        if target.is_dir():
            if not split.path.endswith("/"):
                location = split.path + "/" + (f"?{split.query}" if split.query else "")
                return self._plain(301, "moved", {"Location": location})
            target = target / "index.html"
        elif not target.exists() and parts and target.with_name(target.name + ".html").is_file():
            target = target.with_name(target.name + ".html")  # the site deploys with cleanUrls
        if not target.is_file():
            self.server.misses.append(path)
            return self._plain(404, f"not found: {path}")
        self._send_file(target, head)

    def _send_file(self, target: Path, head: bool) -> None:
        size = target.stat().st_size
        start, end, status = 0, size - 1, 200
        wanted = self.headers.get("Range")
        if wanted:
            span = _parse_range(wanted, size)
            if span is None:
                return self._plain(416, "bad range", {"Content-Range": f"bytes */{size}"})
            (start, end), status = span, 206
        length = max(0, end - start + 1)
        self.send_response(status)
        self.send_header("Content-Type", MIME.get(target.suffix.lower(), "application/octet-stream"))
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Cache-Control", "no-cache")
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.end_headers()
        if head or not length:
            return
        with target.open("rb") as handle:
            handle.seek(start)
            remaining = length
            while remaining > 0:
                chunk = handle.read(min(1 << 16, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)


class _Server(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self):
        super().__init__(("127.0.0.1", 0), _Handler)  # port 0: the OS picks a free one
        self.misses: list[str] = []

    @property
    def port(self) -> int:
        return self.server_address[1]

    def url(self, html_rel: str, scene: str) -> str:
        return (f"http://127.0.0.1:{self.port}/__repo/{urllib.parse.quote(html_rel)}"
                f"?scene={urllib.parse.quote(str(scene))}")

    def handle_error(self, request, client_address):
        # the browser drops a media connection whenever it seeks; that is not an error
        if isinstance(sys.exc_info()[1], (ConnectionError, TimeoutError)):
            return
        super().handle_error(request, client_address)


@contextmanager
def serve():
    """One local server for one capture, on a free port, torn down after."""
    server = _Server()
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()


# ---------------------------------------------------------------------------
# one browser on one stage page
# ---------------------------------------------------------------------------

def _init_script(stage_input: dict) -> str:
    return f"if (window === window.top) {{ window.STAGE_INPUT = {json.dumps(stage_input)}; }}"


CARET = "*, *::before, *::after { caret-color: transparent !important; }"


class Session:
    """A headless Chromium on a stage page, ready to seek. Fails loudly on any page error.

    Frames come from page.screenshot(type="png") at the viewport. STAGE_SCREENSHOT=fast
    takes the same capture through CDP with optimizeForSpeed: pixel-identical (checked at
    2560x1440), about three times faster, and PNGs about 1.8 times larger on disk.
    """

    def __init__(self, url: str, stage_input: dict, dpr: float, label: str = "stage"):
        self.url, self.stage_input, self.dpr, self.label = url, stage_input, dpr, label
        self.page_errors: list[str] = []
        self.console_errors: list[str] = []
        self.bad_requests: list[str] = []
        self.ready_seconds = 0.0
        self._driver = self._browser = None
        self._cdp = None
        self.page = None

    def __enter__(self) -> "Session":
        from playwright.sync_api import sync_playwright

        self._driver = sync_playwright().start()
        try:
            self._browser = self._driver.chromium.launch()
            context = self._browser.new_context(
                viewport={"width": VIEWPORT[0], "height": VIEWPORT[1]}, device_scale_factor=self.dpr,
            )
            context.add_init_script(script=_init_script(self.stage_input))
            self.page = context.new_page()
            self.page.on("pageerror", lambda error: self.page_errors.append(
                (getattr(error, "stack", None) or str(error)).strip()))
            self.page.on("console", self._on_console)
            self.page.on("requestfailed", lambda request: self.bad_requests.append(
                f"failed {request.url} ({request.failure})"))
            self.page.on("response", lambda response: self.bad_requests.append(
                f"{response.status} {response.url}") if response.status >= 400 else None)
            started = time.perf_counter()
            try:
                self.page.goto(self.url, wait_until="load", timeout=READY_TIMEOUT * 1000)
            except Exception as error:  # noqa: BLE001 - re-raised with the page's own errors
                raise RuntimeError(self.report(f"could not load the page: {error}")) from None
            self._wait_ready()
            self.ready_seconds = time.perf_counter() - started
            if os.environ.get("STAGE_SCREENSHOT", "").strip().lower() == "fast":
                # a CDP session of our own carries no emulation, so it gets the same metrics
                self._cdp = context.new_cdp_session(self.page)
                self._cdp.send("Emulation.setDeviceMetricsOverride", {
                    "width": VIEWPORT[0], "height": VIEWPORT[1], "deviceScaleFactor": self.dpr, "mobile": False,
                })
                for frame in self.page.frames:  # page.screenshot hides the caret; so does this
                    try:  # a constructed sheet, because the site's CSP refuses inline <style>
                        frame.evaluate("(css) => { const sheet = new CSSStyleSheet(); sheet.replaceSync(css);"
                                       " document.adoptedStyleSheets = [...document.adoptedStyleSheets, sheet]; }",
                                       CARET)
                    except Exception:  # noqa: BLE001 - a frame that went away has no caret
                        pass
        except BaseException:
            self.close()
            raise
        return self

    def _screenshot(self) -> bytes:
        if self._cdp is None:
            return self.page.screenshot(type="png")
        import base64

        shot = self._cdp.send("Page.captureScreenshot", {
            "format": "png", "captureBeyondViewport": False, "optimizeForSpeed": True,
            "clip": {"x": 0, "y": 0, "width": VIEWPORT[0], "height": VIEWPORT[1], "scale": 1},
        })
        return base64.b64decode(shot["data"])

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        for closer in (self._browser, self._driver):
            if closer is not None:
                try:
                    closer.close() if closer is self._browser else closer.stop()
                except Exception:  # noqa: BLE001 - closing a browser that already died
                    pass
        self._browser = self._driver = None

    def _on_console(self, message) -> None:
        if message.type == "error":
            where = (message.location or {}).get("url", "")
            self.console_errors.append(f"{message.text}" + (f"  [{where}]" if where else ""))

    def report(self, reason: str) -> str:
        lines = [f"stage {self.label}: {reason}", f"  page: {self.url}"]
        for title, items in (("page errors", self.page_errors), ("console errors", self.console_errors),
                             ("failed requests", self.bad_requests)):
            if items:
                lines.append(f"  {title}:")
                lines += [f"    {item[:600]}" for item in list(dict.fromkeys(items))[:12]]
        return "\n".join(lines)

    def _wait_ready(self) -> None:
        deadline = time.monotonic() + READY_TIMEOUT
        while True:
            if self.page_errors:
                raise RuntimeError(self.report("the page threw before it was ready"))
            if any(item.split("?")[0].endswith((".js", ".mjs")) for item in self.bad_requests):
                raise RuntimeError(self.report("a script the page imports did not load"))
            state = self.page.evaluate(READY_PROBE)
            if state == "ready":
                break
            if state.startswith("failed:"):
                raise RuntimeError(self.report(f"window.stageReady rejected: {state[7:]}"))
            if time.monotonic() > deadline:
                what = "never defined window.stageReady" if state == "absent" else "window.stageReady never resolved"
                raise RuntimeError(self.report(f"{what} within {READY_TIMEOUT:.0f} s"))
            self.page.wait_for_timeout(100)
        if not self.page.evaluate("() => typeof window.stageSeek === 'function'"):
            raise RuntimeError(self.report("the page has no window.stageSeek(t)"))
        if self.page_errors:
            raise RuntimeError(self.report("the page threw while getting ready"))

    def shot(self, t: float, timings: dict | None = None) -> bytes:
        """The viewport as PNG bytes at local time t."""
        started = time.perf_counter()
        try:
            self.page.evaluate(SEEK, [t, SEEK_TIMEOUT_MS])
        except Exception as error:  # noqa: BLE001 - re-raised with the page's own errors
            raise RuntimeError(self.report(f"stageSeek({t:.3f}) failed: {error}")) from None
        seeked = time.perf_counter()
        png = self._screenshot()
        if self.page_errors:
            raise RuntimeError(self.report(f"the page threw at t={t:.3f}"))
        if os.environ.get("STAGE_STRICT") == "1" and self.console_errors:
            raise RuntimeError(self.report(f"console error by t={t:.3f} (STAGE_STRICT=1)"))
        if timings is not None:
            timings["seek"] = timings.get("seek", 0.0) + seeked - started
            timings["shot"] = timings.get("shot", 0.0) + time.perf_counter() - seeked
        return png


# ---------------------------------------------------------------------------
# capture: every frame of one segment, in parallel chunks
# ---------------------------------------------------------------------------

def _store(png: bytes, path: Path, canvas) -> None:
    """Write one frame atomically, resized to the canvas if the browser rounded the size."""
    size = struct.unpack(">II", png[16:24])
    partial = path.with_name(path.stem + ".partial.png")
    if tuple(size) != tuple(canvas) and _same_aspect(size, canvas):
        with Image.open(io.BytesIO(png)) as shot:
            shot.convert("RGB").resize(tuple(canvas), Image.LANCZOS).save(partial, "PNG", compress_level=1)
    else:
        partial.write_bytes(png)
    os.replace(partial, path)


def _capture_frames(job: dict, progress) -> dict:
    frames_dir = Path(job["dir"])
    timings: dict = {}
    opened = time.perf_counter()
    with Session(job["url"], job["stage_input"], job["dpr"], job["label"]) as session:
        started = time.perf_counter()
        for index in job["indices"]:
            png = session.shot(index / job["fps"], timings)
            mark = time.perf_counter()
            _store(png, frames_dir / frame_name(index), job["canvas"])
            timings["write"] = timings.get("write", 0.0) + time.perf_counter() - mark
            progress(1)
        timings["loop"] = time.perf_counter() - started
        timings["ready"] = session.ready_seconds
        timings["total"] = time.perf_counter() - opened
        timings["console"] = list(dict.fromkeys(session.console_errors))[:8]
        timings["requests"] = list(dict.fromkeys(session.bad_requests))[:8]
    timings["frames"] = len(job["indices"])
    return timings


WIRE = "\x1estage "
"""Prefix of the lines a capture worker reports on, so stray output cannot be misread."""


def _worker_cli(job_file: str) -> int:
    """`python3 stage.py --worker JOB.json`: one browser over one chunk of frames.

    A plain child interpreter rather than multiprocessing, so the caller's main module is
    never re-imported (an unguarded script cannot fork-bomb) and torch or the server thread
    in the parent are never inherited. It reports on stdout and always exits cleanly, so
    the parent reads the real error rather than a bare exit code.
    """
    job = json.loads(Path(job_file).read_text(encoding="utf-8"))
    try:
        stats = _capture_frames(job, lambda count: print(f"{WIRE}progress {count}", flush=True))
        print(f"{WIRE}done {json.dumps(stats)}", flush=True)
    except BaseException as error:  # noqa: BLE001 - every failure goes back to the parent
        print(f"{WIRE}error {json.dumps(str(error))}", flush=True)
    return 0


def _pump(process, number: int, events) -> None:
    for line in process.stdout:
        if not line.startswith(WIRE):
            print(line, end="", flush=True)
            continue
        kind, _, payload = line[len(WIRE):].rstrip("\n").partition(" ")
        events.put((kind, number, int(payload) if kind == "progress" else json.loads(payload)))
    events.put(("exit", number, process.wait()))


def _run_pool(jobs: list[dict], progress, frames_dir: Path) -> list[dict]:
    import subprocess

    events: queue_module.Queue = queue_module.Queue()
    processes, job_files = [], []
    finished: dict[int, dict] = {}
    try:
        for job in jobs:
            job_file = frames_dir / f"job-{job['worker']}.json"
            job_file.write_text(json.dumps(job), encoding="utf-8")
            job_files.append(job_file)
            process = subprocess.Popen(
                [sys.executable, str(Path(__file__).resolve()), "--worker", str(job_file)],
                stdout=subprocess.PIPE, text=True, cwd=str(KIT),
            )
            processes.append(process)
            threading.Thread(target=_pump, args=(process, job["worker"], events), daemon=True).start()
        while len(finished) < len(processes):
            try:
                kind, number, payload = events.get(timeout=1.0)
            except queue_module.Empty:
                continue
            if kind == "progress":
                progress(payload)
            elif kind == "done":
                finished[number] = payload
            elif kind == "error":
                raise RuntimeError(payload)
            elif kind == "exit" and number not in finished:
                raise RuntimeError(f"stage capture browser {number} exited {payload} before it finished")
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except Exception:  # noqa: BLE001 - one that will not stop is killed
                process.kill()
        for job_file in job_files:
            job_file.unlink(missing_ok=True)
    return [finished[n] for n in range(len(processes))]


def _split(indices: list[int], parts: int) -> list[list[int]]:
    size = len(indices)
    return [indices[size * k // parts: size * (k + 1) // parts] for k in range(parts) if size * (k + 1) // parts > size * k // parts]


def capture(html_rel: str, stage_input: dict, canvas, frames_dir: Path,
            label: str = "stage", workers: int | None = None) -> dict:
    """Capture every frame of one stage segment into frames_dir, then write the done marker.

    Frames already on disk are kept (they are keyed, so an interrupted capture resumes). Any
    page error, a stageReady that never resolves or a seek that fails stops the capture with
    the page's own errors in the message.
    """
    fps = int(stage_input["fps"])
    total = frame_count(stage_input["seconds"], fps)
    canvas = (int(canvas[0]), int(canvas[1]))
    frames_dir.mkdir(parents=True, exist_ok=True)
    for leftover in frames_dir.glob("*.partial.png"):
        leftover.unlink()
    missing = [index for index in range(total) if not (frames_dir / frame_name(index)).exists()]
    dpr = device_scale(canvas)
    count = max(1, min(workers or default_workers(), math.ceil(len(missing) / MIN_CHUNK) or 1))
    chunks = _split(missing, count)
    started = time.perf_counter()
    stats: list[dict] = []
    if missing:
        print(f"  stage {label}: capturing {len(missing)}/{total} frames at {canvas[0]}x{canvas[1]} "
              f"(DPR {dpr:.4g}) with {len(chunks)} browser{'s' if len(chunks) != 1 else ''}", flush=True)
        state = {"done": 0, "logged": started}

        def progress(done: int) -> None:
            state["done"] += done
            now = time.perf_counter()
            if now - state["logged"] >= LOG_EVERY:
                state["logged"] = now
                rate = state["done"] / max(now - started, 1e-6)
                print(f"  stage {label}: {state['done']}/{len(missing)} frames, {rate:.1f} frames/s", flush=True)

        with serve() as server:
            jobs = [{"url": server.url(html_rel, stage_input["scene"]), "stage_input": stage_input,
                     "dpr": dpr, "canvas": canvas, "dir": str(frames_dir), "indices": chunk,
                     "fps": fps, "label": label, "worker": number}
                    for number, chunk in enumerate(chunks)]
            if len(jobs) == 1:
                stats = [_capture_frames(jobs[0], progress)]
            else:
                stats = _run_pool(jobs, progress, frames_dir)
            misses = sorted(set(server.misses))
    else:
        misses = []
    elapsed = time.perf_counter() - started
    absent = [index for index in range(total) if not (frames_dir / frame_name(index)).exists()]
    if absent:
        raise RuntimeError(f"stage {label}: {len(absent)} frames missing after capture, first {absent[0]}")

    warnings = list(dict.fromkeys(item for stat in stats for item in stat.get("console", [])))
    requests = list(dict.fromkeys(item for stat in stats for item in stat.get("requests", [])))
    for line in warnings[:6]:
        print(f"  stage {label}: WARNING console error: {line[:300]}", flush=True)
    for line in (requests + [f"404 {miss}" for miss in misses])[:6]:
        print(f"  stage {label}: WARNING request: {line[:300]}", flush=True)
    shots = sum(stat.get("frames", 0) for stat in stats)
    browser_ms = (1000 * sum(stat.get("seek", 0) + stat.get("shot", 0) + stat.get("write", 0) for stat in stats)
                  / shots) if shots else 0.0
    summary = {
        "frames": total, "fps": fps, "seconds": stage_input["seconds"], "canvas": list(canvas),
        "dpr": dpr, "captured": len(missing), "browsers": len(chunks), "capture_seconds": round(elapsed, 2),
        "frames_per_second": round(len(missing) / elapsed, 2) if missing and elapsed else None,
        "ms_per_frame_per_browser": round(browser_ms, 1) if shots else None,
        "seek_ms": round(1000 * sum(s.get("seek", 0) for s in stats) / shots, 1) if shots else None,
        "screenshot_ms": round(1000 * sum(s.get("shot", 0) for s in stats) / shots, 1) if shots else None,
        "ready_seconds": [round(s.get("ready", 0), 2) for s in stats],
        "console_errors": warnings[:20], "scene": stage_input["scene"], "html": html_rel,
    }
    (frames_dir / DONE).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if missing:
        print(f"  stage {label}: {len(missing)} frames in {elapsed:.1f}s, "
              f"{summary['frames_per_second']} frames/s, {summary['ms_per_frame_per_browser']} ms/frame "
              f"per browser (seek {summary['seek_ms']}, screenshot {summary['screenshot_ms']})", flush=True)
    return summary


def _complete(frames_dir: Path, total: int) -> bool:
    marker = frames_dir / DONE
    if not marker.exists():
        return False
    try:
        frames = json.loads(marker.read_text(encoding="utf-8")).get("frames")
    except ValueError:
        return False
    return frames == total and (frames_dir / frame_name(total - 1)).exists()


def prune(keep: Path, label: str, canvas, fps: int) -> None:
    """Drop this segment's stale captures at the same canvas and fps (a different canvas, a
    9:16 cut say, is a different picture and is kept)."""
    pattern = re.compile(rf"^stage-{re.escape(_safe(label))}-[0-9a-f]{{12}}$")
    for sibling in keep.parent.iterdir():
        if sibling == keep or not sibling.is_dir() or not pattern.match(sibling.name):
            continue
        try:
            meta = json.loads((sibling / DONE).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            meta = None
        if meta is None or (list(meta.get("canvas", [])) == list(canvas) and meta.get("fps") == fps):
            shutil.rmtree(sibling, ignore_errors=True)


# ---------------------------------------------------------------------------
# the page the painter reads
# ---------------------------------------------------------------------------

def fit(image: Image.Image, canvas, base: Image.Image | None) -> Image.Image:
    """A capture at the canvas size: resized when only rounding differs, letterboxed on the
    field when the canvas is another aspect (a 16:9 scene in a 9:16 cut)."""
    canvas = tuple(canvas)
    if image.size == canvas:
        return image
    if _same_aspect(image.size, canvas):
        return image.resize(canvas, Image.LANCZOS)
    scale = min(canvas[0] / image.width, canvas[1] / image.height)
    size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    out = base.copy().convert("RGB") if base is not None and base.size == canvas else Image.new("RGB", canvas)
    out.paste(image.resize(size, Image.LANCZOS), ((canvas[0] - size[0]) // 2, (canvas[1] - size[1]) // 2))
    return out


class StagePage:
    """A captured stage scene as the painter sees it.

    `.image` is the poster (the frame at 60%), which is what preflight, compose and overlay
    read. `.frame(t)` is the captured frame at segment-local t, which is what the painter
    reads every frame. Frames are decoded from disk on demand, two ahead on a background
    thread, and only a couple are ever held, so a long scene costs no memory.
    """

    def __init__(self, frames_dir: Path, total: int, fps: int, canvas, base=None, label: str = "stage"):
        self.dir, self.total, self.fps = Path(frames_dir), total, fps
        self.canvas = (int(canvas[0]), int(canvas[1]))
        self.label = label
        self.boxes = [(0, 0, self.canvas[0], self.canvas[1])]
        self.window = None
        self._base = base
        self._poster: Image.Image | None = None
        self._cache: OrderedDict[int, Image.Image] = OrderedDict()
        self._pending: dict = {}
        self._pool: ThreadPoolExecutor | None = None
        self._run = {"first": None, "count": 0}

    def _read(self, index: int) -> Image.Image:
        with Image.open(self.dir / frame_name(index)) as shot:
            image = shot.convert("RGB")
        return fit(image, self.canvas, self._base)

    @property
    def image(self) -> Image.Image:
        if self._poster is None:
            self._poster = self._read(poster_index(self.total))
        return self._poster

    def _get(self, index: int) -> Image.Image:
        if index in self._cache:
            self._cache.move_to_end(index)
            return self._cache[index]
        pending = self._pending.pop(index, None)
        image = pending.result() if pending is not None else self._read(index)
        self._cache[index] = image
        while len(self._cache) > 2:
            self._cache.popitem(last=False)
        return image

    def _prefetch(self, index: int) -> None:
        if index >= self.total or index in self._cache or index in self._pending:
            return
        if self._pool is None:
            self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"stage-{self.label}")
        for stale in [key for key in self._pending if key < index - 2]:
            self._pending.pop(stale)
        self._pending[index] = self._pool.submit(self._read, index)

    def frame(self, t: float) -> Image.Image:
        index = max(0, min(self.total - 1, round(t * self.fps)))
        image = self._get(index)
        self._prefetch(index + 1)
        self._prefetch(index + 2)
        self._note(index)
        return image.copy()

    def _note(self, index: int) -> None:
        """Print the paint rate once a full sequential pass reaches the last frame."""
        now = time.perf_counter()
        if index == 0 or self._run["first"] is None:
            self._run.update(first=now, count=0)
        self._run["count"] += 1
        if index == self.total - 1 and self._run["count"] >= self.total * 0.9 and self.total > 1:
            spent = max(now - self._run["first"], 1e-6)
            print(f"  stage {self.label}: painted {self._run['count']} frames in {spent:.1f}s, "
                  f"{self._run['count'] / spent:.1f} frames/s", flush=True)
            self._run.update(first=None, count=0)


def _resolve(needle) -> list[int]:
    """A stage scene draws its own camera and marker, so a text needle matches nothing (and
    preflight says so). An index still passes, for a deliberate full-frame beat."""
    if isinstance(needle, str):
        return []
    return [int(needle)]


@style.scene("stage")
def prepare(segment, project, work, base, style_, palette):
    label = segment.get("name") or "stage"
    names = [s.get("name") or "stage" for s in project.get("segments", []) if s.get("type") == "stage"]
    if names.count(label) > 1:
        raise RuntimeError(f"stage segment name {label!r} is used {names.count(label)} times; "
                           "give every stage segment its own name (it keys the frame cache)")
    for key in ("html", "scene"):
        if not segment.get(key):
            raise RuntimeError(f"stage {label}: missing {key!r}")
    params = segment.get("params", {})
    if params is None:
        params = {}
    html_rel, html_path = repo_path(segment["html"])
    canvas = (int(theme.CANVAS[0]), int(theme.CANVAS[1]))
    fps = int(theme.FPS)
    timing = segment_timing(segment, project, Path(work))
    stage_input = {
        "scene": segment["scene"], "params": params, "seconds": timing["seconds"], "fps": fps,
        "offset": timing["offset"], "cues": timing["cues"],
    }
    key = cache_key(html_path, stage_input, canvas)
    frames_dir = Path(work) / f"stage-{_safe(label)}-{key[:12]}"
    total = frame_count(timing["seconds"], fps)
    if _complete(frames_dir, total):
        print(f"  stage {label}: {total} frames cached in {frames_dir.name}", flush=True)
    else:
        capture(html_rel, stage_input, canvas, frames_dir, label=label)
        prune(frames_dir, label, canvas, fps)
    page = StagePage(frames_dir, total, fps, canvas, base, label)
    return (lambda visible: page), 1, _resolve


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        raise SystemExit(_worker_cli(sys.argv[2]))
    raise SystemExit("stage.py is a scene module; preview a scene with stage_preview.py")
