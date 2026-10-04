"""Build one demo video from a project file.

    python3 build.py projects/phone-approval-gate.json

Audio first, picture second. Cues are synthesised and measured, then each segment
is sized to the words it carries. The picture then follows the words: the frame
zooms to the thing being talked about, a highlighter sweeps it, and a cursor walks
over and clicks.

Scenes are chosen per project rather than from one template, and every scene reads
real artifacts: captured stdout, a real pipeline run with real exit codes, a real
source file, the real ledger, the real call report.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path

from PIL import Image

import bg
import cards
import code as codecard
import doc
import grid
import motion
import panel as panels
import receipt
import scene
import style as style_module
import term
import theme
import transition
import voice
import web

ROOT = Path(__file__).resolve().parent
GAP = 0.35
LEAD = 0.3
CAP = 176.0
TRANSITION = 0.62
CURSOR_MOVE = 0.45
MARK_SWEEP = 1.6
MUSIC = os.environ.get("MUSIC")
AUDIO_ONLY = os.environ.get("AUDIO_ONLY") == "1"
BITRATE = os.environ.get("VIDEO_BITRATE")
"""Target video bitrate, e.g. `VIDEO_BITRATE=8M`.

Unset means constant quality, which is what the CALL-E set shipped with and which
lands a two minute video around 13 MB. Some programs set a floor on the file they
accept, and a flat monospace picture at CRF 19 is far too efficient to reach it, so
this switches the same picture to a rate target instead of raising the quality knob
until it happens to be big enough.
"""
_PIPELINES: dict[tuple[str, str], str] = {}


def entries(segment: dict) -> list[tuple[str, list, dict]]:
    """Each narration entry as (text, focus, settings-source).

    The third item is the raw entry, so the voice layer can read per-cue overrides
    (speaker, voice, rate, pitch) without this function having to know about any of them.
    """
    out: list[tuple[str, list, dict]] = []
    for entry in segment.get("narration", []):
        if isinstance(entry, str):
            out.append((entry, [], {}))
            continue
        focus = entry.get("focus", [])
        out.append((entry["text"], focus if isinstance(focus, list) else [focus], entry))
    return out


def run_pipeline(script: Path, app: Path, mode: str, artifacts: Path, name: str) -> str:
    key = (str(script), mode)
    if key not in _PIPELINES:
        done = subprocess.run(
            [str(script), str(app), mode], capture_output=True, text=True, timeout=900, check=False
        )
        _PIPELINES[key] = done.stdout + done.stderr
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / f"{name}.pipeline").write_text(
            f"{script} {app} {mode}\nexit {done.returncode}\n\n{_PIPELINES[key]}", encoding="utf-8"
        )
    return _PIPELINES[key]


def steps_from(output: str) -> list[panels.Row]:
    rows: list[panels.Row] = []
    for line in output.splitlines():
        if not line.startswith("STEP|"):
            continue
        _, label, code, duration = line.split("|", 3)
        if code == "0":
            rows.append(panels.Row(label, duration, "pass"))
        elif code == "skipped":
            rows.append(panels.Row(label, "skipped", "plain"))
        else:
            rows.append(panels.Row(label, f"exit {code}", "fail"))
    return rows


def prepare(segment: dict, project: dict, work: Path, base: Image.Image, accent, mark):
    """Returns (page_for, count, resolve) for any scene type."""
    kind = segment["type"]

    if kind == "term":
        captured = term.capture(Path(segment["cwd"]), segment["cmd"], work, segment["name"])
        lines = term.slice_output(
            captured,
            segment.get("from"),
            segment.get("to"),
            segment.get("max_lines", term.MAX_LINES),
            segment.get("wrap", term.WRAP_AT),
        )
        if not lines:
            raise RuntimeError(f"segment {segment['name']} sliced to nothing")
        header = segment.get("header", project.get("header", ""))
        prompt = segment.get("prompt", " ".join(segment["cmd"]))
        return (
            lambda visible: scene.page(base, header, prompt, lines, visible, segment.get("footer"), accent),
            len(lines),
            lambda needle: [index for index, line in enumerate(lines) if needle in line][:1],
        )

    if kind == "web":
        url = segment.get("url") or f"file://{Path(segment['file']).resolve()}"
        shot = web.capture(
            url, work, segment["name"], segment["section"],
            segment.get("items", "data-step"),
            tuple(segment.get("viewport", web.VIEWPORT)),
            segment.get("wait_ms", 400),
            segment.get("hide"),
        )
        header = segment.get("header", project.get("header", ""))
        return (
            lambda visible: web.card(base, shot, visible, header, segment.get("footer"), accent),
            len(shot.boxes),
            lambda needle: [
                index for index, text in enumerate(shot.texts) if needle.lower() in text.lower()
            ][:1],
        )

    if kind == "steps":
        output = run_pipeline(
            ROOT / segment["script"], Path(segment["app"]), segment.get("mode", "approve"), work, segment["name"]
        )
        rows = steps_from(output)
        if not rows:
            raise RuntimeError(f"pipeline {segment['name']} produced no steps")
        return (
            lambda visible: panels.panel(base, segment.get("title"), rows, accent, visible, segment.get("footer")),
            len(rows),
            lambda needle: [index for index, row in enumerate(rows) if needle in row.label][:1],
        )

    if kind == "receipts":
        rows = receipt.channel_rows(Path(segment["file"]))
        if not rows:
            raise RuntimeError(f"segment {segment['name']} found no steps in {segment['file']}")
        return (
            lambda visible: panels.panel(base, segment.get("title"), rows, accent, visible, segment.get("footer")),
            len(rows),
            lambda needle: [
                index for index, row in enumerate(rows) if needle in row.label or needle in row.value
            ][:1],
        )

    if kind == "code":
        lines, first_line = codecard.read_lines(
            Path(segment["file"]), segment.get("from"), segment.get("to"), segment.get("max_lines", 22)
        )
        if not lines:
            raise RuntimeError(f"segment {segment['name']} sliced to nothing")
        return (
            lambda visible: codecard.file_card(
                base, segment["title"], lines, accent, visible, segment.get("footer"), first_line
            ),
            len(lines),
            lambda needle: [index for index, line in enumerate(lines) if needle in line][:1],
        )

    if kind == "grid":
        ledger = grid.read_ledger(segment["ledger"])
        count = sum(1 for entry in ledger if entry["kind"] == "gather")
        return (
            lambda visible: grid.matrix(base, ledger, accent, visible, segment.get("footer")),
            count,
            lambda needle: [
                index for index, entry in enumerate(e for e in ledger if e["kind"] == "gather")
                if needle in entry["result"]["party_id"]
            ][:1],
        )

    if kind == "chips":
        data = json.loads(Path(segment["errand"]).read_text(encoding="utf-8"))
        items = [(item["label"], item["value"]) for item in data["disclosure"]]
        return (
            lambda visible: panels.chips(base, segment["title"], items, accent, visible, segment.get("footer")),
            len(items),
            lambda needle: [index for index, item in enumerate(items) if needle in item[0]][:1],
        )

    if kind == "report":
        data = json.loads(Path(segment["report"]).read_text(encoding="utf-8"))
        return (
            lambda visible: doc.report(base, data, accent, visible),
            len(data["answers"]),
            lambda needle: [index for index, answer in enumerate(data["answers"]) if needle in answer["text"]][:1],
        )

    if kind == "bubbles":
        data = json.loads(Path(segment["report"]).read_text(encoding="utf-8"))
        turns = data["transcript"][: segment.get("max_turns", 6)]
        return (
            lambda visible: doc.bubbles(
                base, turns, accent, visible, segment.get("footer"),
                segment.get("title", "Transcript, verbatim"),
            ),
            len(turns),
            lambda needle: [index for index, turn in enumerate(turns) if needle in turn["text"]][:1],
        )

    # Anything not handled above is a registered scene type: a renderer module that called
    # `@style.scene("chart")`. Adding a scene type means adding a module, never a branch here.
    style_module.load_scene_modules()
    return style_module.get(kind)(segment, project, work, base, theme.ACTIVE, theme.palette(project.get("palette", "citrus")))


def _encode_args() -> list[str]:
    """The x264 rate and quality flags for this build, from the resolved style.

    Order of precedence keeps the shipped default intact: the VIDEO_BITRATE env still
    forces a rate target the way it always did, then a bitrate set in the project file,
    otherwise constant quality at the style's crf. An unset style resolves to preset
    veryfast and crf 19, which is exactly what the CALL-E set shipped with, so a project
    with no render block encodes byte-for-byte as before.
    """
    enc = theme.ACTIVE.encoder
    preset = enc.get("preset", "veryfast")
    bitrate = BITRATE or enc.get("bitrate")
    if bitrate:
        rate = ["-b:v", str(bitrate), "-minrate", str(bitrate), "-maxrate", str(bitrate), "-bufsize", "24M"]
    else:
        rate = ["-crf", str(enc.get("crf", 19))]
    args = ["-preset", preset, *rate]
    if enc.get("tune"):
        args += ["-tune", str(enc["tune"])]
    # Colour metadata. YouTube wants bt709 tagged and the kit never set it, so an untagged
    # upload was left to the platform to guess. Only added when the style asks for it, so
    # the default file is unchanged unless a project opts in.
    if enc.get("colour") == "bt709":
        args += ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
    return args


def render_frames(out: Path, seconds: float, painter) -> None:
    total = max(1, round(seconds * theme.FPS))
    process = subprocess.Popen(
        [
            "ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
            "-s", f"{theme.OUTPUT[0]}x{theme.OUTPUT[1]}", "-r", str(theme.FPS), "-i", "-", "-an",
            "-c:v", "libx264", *_encode_args(), "-pix_fmt", "yuv420p", str(out),
        ],
        stdin=subprocess.PIPE,
    )
    assert process.stdin is not None
    for index in range(total):
        process.stdin.write(painter(index / theme.FPS).tobytes())
    process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError(f"render failed: {out}")


def scene_painter(page_for, count, resolve, beats, seconds, offset, total_video, accent, mark, hold, cadence, captions=True):
    """One painter for every scene: reveal, zoom, marker sweep, cursor, progress.

    Content lands at a steady cadence rather than being stretched over the whole
    segment, because a line the narration is already talking about has to be on
    screen. Anything a cue points at is revealed immediately, however far down it is.
    """
    pages: dict[int, object] = {}
    reveal = min(max(seconds - hold, 0.8), max(count * cadence, 1.0))
    state: dict = {
        "box": motion.full_box(), "from": motion.full_box(), "since": -9.0, "target": None,
        "cursor": None, "cursor_from": None, "cursor_since": -9.0,
    }

    def page(visible: int):
        if visible not in pages:
            pages[visible] = page_for(visible)
        return pages[visible]

    def paint(t: float):
        active = next((beat for beat in beats if beat[0] <= t < beat[1]), None)
        indexes: list[int] = []
        for needle in (active[2] if active else []):
            for index in (resolve(needle) if isinstance(needle, str) else [int(needle)]):
                if 0 <= index < count:
                    indexes.append(index)
        indexes = sorted(set(indexes))

        streamed = count if t >= reveal or count == 0 else round(count * (t / max(reveal, 0.01)))
        visible = max(streamed, max(indexes) + 1 if indexes else 0)
        current = page(visible)
        # a page that moves on its own (a captured stage scene) hands back its own frame
        image = current.frame(t) if hasattr(current, "frame") else current.image.copy()
        boxes = current.boxes
        indexes = [index for index in indexes if index < len(boxes)]

        desired = motion.focus_box(boxes, indexes, window=getattr(current, "window", None)) if indexes else motion.full_box()
        if state["target"] != desired:
            state["from"] = state["box"]
            state["target"] = desired
            state["since"] = t
        state["box"] = motion.lerp_box(state["from"], desired, (t - state["since"]) / TRANSITION)

        if indexes and active is not None:
            swept = (t - active[0]) / min(MARK_SWEEP, max(active[1] - active[0], 0.4))
            for index in indexes:
                motion.mark(image, boxes[index], mark, swept)
            target = boxes[indexes[0]]
            point = (target[0] - 40, target[1] + 30)
            if state["cursor"] != point:
                state["cursor_from"] = state["cursor"] or (target[0] + 320, target[3] + 260)
                state["cursor"] = point
                state["cursor_since"] = t
            travel = motion.ease((t - state["cursor_since"]) / CURSOR_MOVE)
            start = state["cursor_from"] or point
            at = (
                round(start[0] + (point[0] - start[0]) * travel),
                round(start[1] + (point[1] - start[1]) * travel),
            )
            landed = (t - state["cursor_since"] - CURSOR_MOVE) / 0.7
            motion.cursor(image, at[0], at[1], landed if 0 <= landed < 1 else None, accent)

        frame = motion.deliver(image, state["box"])
        motion.progress(frame, (offset + t) / total_video, accent)
        if captions:
            motion.caption(frame, spoken_now(beats, t), accent)
        return frame

    return paint


def spoken_now(beats, t: float) -> str:
    """The caption piece whose voice is playing right now, or nothing in a gap."""
    for beat in beats:
        for start, end, line in beat[3]:
            if start <= t < end:
                return line
    return ""


def card_painter(base, segment, beats, seconds, offset, total_video, accent, captions=True):
    image = cards.page(
        base, segment["lines"], segment.get("kicker"), segment.get("footer"),
        segment.get("mono", False), accent,
    )
    start = motion.zoom_box(1.05)
    end = motion.full_box()

    def paint(t: float):
        frame = motion.deliver(image, motion.lerp_box(start, end, min(t / max(seconds, 0.01), 1.0)))
        motion.progress(frame, (offset + t) / total_video, accent)
        if captions:
            motion.caption(frame, spoken_now(beats, t), accent)
        return frame

    return paint


def caption_pieces(text: str, at: float, seconds: float) -> list[tuple[float, float, str]]:
    """One cue split into single line pieces, each with the slice of the cue it owns.

    A burned in caption has to be readable at a glance, so it gets one line in the band
    and a long cue is shown in sequence instead of stacked into a paragraph. The pieces
    are balanced rather than greedily packed, because a second line of three words after
    a full one reads like a mistake. Times come from the same measured cue the segment
    is sized by, so the band cannot drift from the voice or from captions.srt.
    """
    words = text.split()
    if not words:
        return []
    limit = theme.CAPTION_WIDTH
    total = theme.CAPTION.getlength(text)
    pieces = max(1, math.ceil(total / limit))
    target = total / pieces
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if not current or (theme.CAPTION.getlength(trial) <= target and len(lines) < pieces - 1) \
                or theme.CAPTION.getlength(trial) <= limit and len(lines) >= pieces - 1:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    span = sum(len(line) for line in lines) or 1
    out: list[tuple[float, float, str]] = []
    start = at
    for index, line in enumerate(lines):
        share = seconds * len(line) / span
        end = at + seconds if index == len(lines) - 1 else start + share
        out.append((start, end, line))
        start = end
    return out


def layout(project: dict, work: Path) -> tuple[list[dict], list[voice.Cue], float]:
    """Measure every cue, then size each segment to the words it carries.

    Audio first. Cue starts are absolute, so a line that runs long stretches its own
    segment instead of pushing everything after it out of sync.
    """
    plans: list[dict] = []
    all_cues: list[voice.Cue] = []
    clock = 0.0
    for index, segment in enumerate(project["segments"]):
        beats: list[tuple[float, float, list, list]] = []
        cues: list[voice.Cue] = []
        at = LEAD
        for position, (text, focus, raw) in enumerate(entries(segment)):
            if isinstance(raw, dict) and "pause" in raw:
                cue = voice.silence(float(raw["pause"]), work / f"cue-{index:02d}-{position:02d}.mp3")
            else:
                settings = voice.speaker_settings(project, raw)
                # the engine reads the line after the project lexicon; the cue keeps the
                # written line, so captions, the SRT and timing.json never show the respelling
                cue = voice.synth(
                    text,
                    work / f"cue-{index:02d}-{position:02d}.mp3",
                    settings["voice"], settings["rate"],
                    settings["pitch"], settings["volume"], settings["engine"],
                    say=voice.spoken(text, project.get("lexicon")),
                )
            beats.append((at, at + cue.seconds + GAP, focus,
                          caption_pieces(text, at, cue.seconds)))
            cues.append(cue)
            # a cue can widen or tighten the gap after it, so a script can breathe at one
            # beat without moving the global cadence
            gap = float(raw.get("gap", GAP)) if isinstance(raw, dict) else GAP
            at += cue.seconds + gap
        spoken = at - GAP if cues else 0.0
        seconds = max(segment.get("min_seconds", 2.5), LEAD + spoken + segment.get("pad", 0.9))
        for start, cue in zip([beat[0] for beat in beats], cues):
            cue.start = clock + start
        all_cues.extend(cues)
        plans.append({"segment": segment, "beats": beats, "seconds": seconds, "offset": clock, "cues": cues})
        clock += seconds
    return plans, all_cues, clock


def repin_cues(plans: list[dict], composited: list[float]) -> None:
    """Move every cue onto the composited timeline once transitions are known.

    layout pins each cue at naive_offset + at. A transition slides its segment earlier by
    the overlaps before it, so the cue has to move with the segment or the voice drifts
    off the picture. The relative position within the segment is unchanged, so this only
    shifts each cue by how far its segment moved.
    """
    for index, plan in enumerate(plans):
        shift = composited[index] - plan["offset"]
        for cue in plan["cues"]:
            cue.start += shift


def painter_for(plan: dict, project: dict, work: Path, base: Image.Image, accent, mark, total: float):
    segment = plan["segment"]
    if segment["type"] == "card":
        return card_painter(base, segment, plan["beats"], plan["seconds"], plan["offset"], total, accent, captions=project.get("captions", True))
    page_for, count, resolve = prepare(segment, project, work, base, accent, mark)
    return scene_painter(
        page_for, count, resolve, plan["beats"], plan["seconds"], plan["offset"],
        total, accent, mark, segment.get("hold", 1.6), segment.get("cadence", 0.45),
        captions=project.get("captions", True),
    )


def _render_one_segment(args: tuple) -> str:
    """Render one segment to its own mp4 in a worker process.

    A painter holds PIL images and closures, so it cannot be pickled across a process
    pool. Each worker gets the RESOLVED project as JSON (the render override already
    merged in) and re-prepares only its own segment. Carrying the merged project rather
    than re-reading the base file matters: a 9:16 short or a segment subset lives only in
    that merged dict, so a worker reading the base path would silently render the wrong
    cut. Re-preparing is cheap because the terminal capture, web shot and pipeline run are
    cached in artifacts by the warm pass, so a worker reads the receipt not the command.
    """
    project_json, index, work_str, name, canvas_key, total = args
    project = json.loads(project_json)
    theme.configure(style_module.resolve(project))
    work = Path(work_str)
    base = bg.background(name, work / f"background-{name}-{canvas_key}.png")
    accent, mark = theme.palette(name)["accent"], theme.palette(name)["mark"]
    plans, _, _ = layout(project, work)
    plan = plans[index]
    piece = work / f"seg-{index:02d}.mp4"
    render_frames(piece, plan["seconds"], painter_for(plan, project, work, base, accent, mark, total))
    return str(piece)


def _render_pieces(plans, project, project_path, work, base, accent, mark, clock, name, canvas_key, workers):
    """Render every segment to a piece file, in parallel when asked.

    workers == 1 keeps the original single-process loop, which is the safe default and the
    path the pixel-identical baseline was proven on. A higher count, or 0 for auto, farms
    segments to a process pool. Output order is preserved because each piece is named by
    its index rather than by completion order.
    """
    pieces = [work / f"seg-{index:02d}.mp4" for index in range(len(plans))]
    if AUDIO_ONLY:
        return pieces
    if workers == 0:
        workers = min(max(1, (os.cpu_count() or 2) - 2), len(plans))
    if workers <= 1 or len(plans) <= 1:
        for index, plan in enumerate(plans):
            render_frames(pieces[index], plan["seconds"],
                          painter_for(plan, project, work, base, accent, mark, clock))
        return pieces
    # The first pass over prepare() populated the caches (term stdout, web shots, pipeline
    # runs), so warm them once here before the pool so workers hit the receipt not the
    # command. Cheap scenes (card) skip this.
    from concurrent.futures import ProcessPoolExecutor
    project_json = json.dumps(project)
    jobs = [(project_json, index, str(work), name, canvas_key, clock) for index in range(len(plans))]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        list(pool.map(_render_one_segment, jobs))
    return pieces


def _one_render(project_path: Path, project: dict, resolved, render_spec) -> dict:
    base_id = project["id"]
    render_name = (render_spec or {}).get("name", "")
    suffix = f"-{render_name}" if render_name else ""

    # A render entry can override style and render settings and pick a subset of segments,
    # so a short is a real re-edit rather than a crop. Merge the override, re-resolve, then
    # reconfigure so this cut draws at its own aspect and quality.
    if render_spec:
        merged = dict(project)
        for key in ("style", "render"):
            if key in render_spec:
                merged[key] = {**project.get(key, {}), **render_spec[key]}
        wanted = render_spec.get("segments")
        if wanted:
            by_name = {s.get("name", s.get("title", "")): s for s in project["segments"]}
            merged["segments"] = [by_name[n] for n in wanted if n in by_name] or project["segments"]
        project = merged
        resolved = theme.configure(style_module.resolve(project))

    work = ROOT / "artifacts" / base_id
    work.mkdir(parents=True, exist_ok=True)
    out = ROOT / "out" / f"{base_id}{suffix}.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)

    name = project.get("palette", "citrus")
    canvas_key = f"{resolved.canvas[0]}x{resolved.canvas[1]}"
    # The cached field is keyed by the canvas it was drawn at, so a 9:16 build cannot pick
    # up the 16:9 field and stretch it.
    base = bg.background(name, work / f"background-{name}-{canvas_key}.png")
    accent = theme.palette(name)["accent"]
    mark = theme.palette(name)["mark"]

    # The project's transitions block names the default kind under "default", but a
    # per-segment override and the planner both read "kind", so map it across. Without this
    # a project-wide default of crossfade is read as the literal kind "default" and every
    # boundary silently falls back to a cut.
    _trans = project.get("transitions", {})
    trans_default = {"kind": _trans.get("default", "cut"), "seconds": _trans.get("seconds", 0.5)}
    plans, all_cues, clock = layout(project, work)
    overlaps = transition.plan_overlaps(plans, trans_default)
    kinds = transition.kinds_for(plans, trans_default)
    durations = [plan["seconds"] for plan in plans]
    composited = _composited_offsets(plans, overlaps)
    # Pin the voice to the composited timeline, so a dissolve cannot slide narration out of
    # sync. With every overlap zero this is a no-op and the audio track is unchanged.
    repin_cues(plans, composited)

    cap = float(project.get("cap", CAP))
    composited_total = transition.total_after(durations, overlaps)
    if composited_total > cap:
        raise RuntimeError(f"total {composited_total:.1f}s is over the {cap:.0f}s cap, cut a segment")

    workers = int(resolved.encoder.get("workers", 0))
    # A first serial pass over prepare warms the caches so parallel workers never race on a
    # command run. For the default workers<=1 this pass IS the render.
    if workers > 1 and not AUDIO_ONLY:
        for plan in plans:
            if plan["segment"]["type"] != "card":
                prepare(plan["segment"], project, work, base, accent, mark)
    pieces = _render_pieces(plans, project, project_path, work, base, accent, mark,
                            clock, name, canvas_key, workers)

    silent = work / f"picture{suffix}.mp4"
    if not AUDIO_ONLY:
        transition.assemble(pieces, overlaps, kinds, durations, silent,
                            resolved.fps, resolved.output, _encode_args(), run)
    elif not silent.exists():
        raise RuntimeError("AUDIO_ONLY needs a picture.mp4 from an earlier full build")

    narration = voice.track(all_cues, composited_total, work / f"narration{suffix}.wav",
                            Path(MUSIC) if MUSIC else None)
    run([
        "ffmpeg", "-loglevel", "error", "-y", "-i", str(silent), "-i", str(narration),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-shortest", str(out),
    ])

    # The timing the build actually measured, so upload.py writes captions and chapters that
    # match the delivered file rather than re-deriving numbers that could drift. The scene
    # start is the composited offset after transitions, not the naive sum, so a timestamp in
    # the package lands on the frame it names even when a dissolve shortened the timeline.
    composited = _composited_offsets(plans, overlaps)
    timing_name = f"timing{suffix}.json"
    (work / timing_name).write_text(
        json.dumps(
            {
                "id": base_id,
                "render": render_name,
                "aspect": resolved.aspect,
                "palette": name,
                "total": transition.total_after(durations, overlaps),
                "music": Path(MUSIC).name if MUSIC else None,
                "transitions": [k for k in kinds if k != "cut"],
                "segments": [
                    {
                        "index": index,
                        "type": plan["segment"]["type"],
                        "name": plan["segment"].get("name")
                        or plan["segment"].get("title")
                        or plan["segment"].get("lines", [""])[0],
                        "start": composited[index],
                        "seconds": plan["seconds"],
                    }
                    for index, plan in enumerate(plans)
                ],
                "cues": [
                    {"text": cue.text, "start": cue.start, "seconds": cue.seconds}
                    for cue in all_cues
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = [
        f"  {index:02d} {plan['segment']['type']:8s} {plan['seconds']:6.2f}s  at {composited[index]:6.2f}s  "
        f"{(plan['segment'].get('name') or plan['segment'].get('title') or plan['segment'].get('lines', [''])[0])[:40]}"
        for index, plan in enumerate(plans)
    ]
    label = f"{base_id}{suffix}" + (f" [{resolved.aspect}]" if suffix else "")
    print(f"\n{label}: {len(plans)} segments, {len(all_cues)} cues, palette {name}"
          + (f", music {Path(MUSIC).name}" if MUSIC else ", no music")
          + (f", transitions {sum(1 for k in kinds if k != 'cut')}" if any(overlaps) else ""))
    print("\n".join(report))
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration,size", "-of", "csv=p=0", str(out)],
        capture_output=True, text=True, check=True,
    )
    print(f"\n{out}  {probe.stdout.strip()}")
    return {"out": out, "timing": work / timing_name}


def _composited_offsets(plans: list, overlaps: list[float]) -> list[float]:
    """Each segment's start on the composited timeline, after transitions eat the overlaps."""
    offsets = []
    running = 0.0
    for index, plan in enumerate(plans):
        running -= overlaps[index] if index < len(overlaps) else 0.0
        offsets.append(round(running, 3))
        running += plan["seconds"]
    return offsets


def build(project_path: Path) -> None:
    """Build every cut a project asks for.

    With no `renders` key this is one default cut, written to out/<id>.mp4, exactly as
    before. With a `renders` list it produces one file per entry, so a single project can
    ship a 16:9 master and a 9:16 short from the same scenes.
    """
    project = json.loads(project_path.read_text(encoding="utf-8"))
    resolved = theme.configure(style_module.resolve(project))
    renders = project.get("renders")
    if not renders:
        _one_render(project_path, project, resolved, None)
        return
    for spec in renders:
        # Reconfigure to the base style before each cut, so one render's override does not
        # leak into the next.
        resolved = theme.configure(style_module.resolve(project))
        _one_render(project_path, project, resolved, spec)


def run(command: list[str]) -> None:
    done = subprocess.run(command, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise RuntimeError(f"{command[0]} failed: {done.stderr.strip()[:400]}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: build.py <project.json>")
    build(Path(sys.argv[1]))
