"""Build the upload package for a finished video.

    python3 upload.py projects/<id>.json

Reads the timing the build measured (`artifacts/<id>/timing.json`) rather than re-deriving
it, so the captions and the chapters match the delivered file to the frame. Writes into
`artifacts/<id>/upload/`, and the caller copies that to `work/<lane>/upload-<id>/`.

    UPLOAD-<id>.html the whole upload in one self-contained page: title, description, tags,
                     chapters, the thumbnail embedded and downloadable, the captions as a copy
                     block and a download, every in and out time the build measured, the rest
                     of the form field by field, the gates and where the URL goes
    thumbnail.png    3840x2160 on the video's own theme, generated, never downloaded
    captions.srt     every narration cue at its measured in and out time
    chapters.txt     the scene table as timestamps

The sidecar files exist only because YouTube wants real files to upload. Both are embedded in
the page as downloads too, so the human never needs a second window open.

The limits it gates against are YouTube's own: a title is capped at 100 characters, a
description at 5000, a thumbnail is recommended at 3840x2160 in 16:9 with a 640px minimum
width and the mobile upload path caps it at 2 MB, and chapters must start at 0:00, number at
least three and each run at least 10 seconds. Tags have no published limit and YouTube says
they play a minimal role, so the 500 character ceiling here is a house convention against
keyword stuffing.

The words come from an `upload` block in the project file, so the brief and the package
cannot drift: the project file is the one place they are written down.
"""

from __future__ import annotations

import base64
import html
import json
import sys
from pathlib import Path

import thumb

ROOT = Path(__file__).resolve().parent

TITLE_MAX = 100
DESCRIPTION_MAX = 5000
TAGS_MAX = 500
THUMB_MAX_BYTES = 2 * 1024 * 1024
CHAPTER_MIN_SECONDS = 10
CHAPTER_MIN_COUNT = 3
CUE_MIN_SECONDS = 0.8

# Per-platform limits, each number checked against the platform's own docs on 2026-09-22
# rather than remembered, because a wrong limit fails silently at the upload form. The
# `cite` field records where each came from so a later session can re-check it.
#
# YouTube:  title 100, description 5000 (help.youtube.com creator basics).
# YouTube Shorts: same text fields, but the video must be 3 minutes or shorter and vertical
#   (support.google.com, Shorts creation).
# X: a free post is 280 characters, a Premium post up to 25,000 (help.x.com "types of
#   posts"); a link costs 23 of them (business.x.com creative specs). Free video tops out
#   at 2m20s, Premium far longer, but the deliverable here is the post text.
# LinkedIn: 3,000 characters per post, ~150 shown before "see more"; native video 3s to 15
#   minutes on desktop, 10 on mobile (contentin.io / socialrails LinkedIn post specs).
# Devpost: the submission form has no published character caps, so these are house
#   conventions to keep a tagline short and a summary scannable, not quoted limits.
PLATFORMS = {
    "youtube": {
        "label": "YouTube",
        "aspect": "16:9",
        "fields": {"title": 100, "description": 5000, "tags": 500},
        "chapters": True,
        "cite": "support.google.com/youtube, title 100 and description 5000",
    },
    "shorts": {
        "label": "YouTube Shorts",
        "aspect": "9:16",
        "fields": {"title": 100, "description": 5000},
        "max_seconds": 180,
        "cite": "support.google.com/youtube, a Short is 3 minutes or shorter and vertical",
    },
    "x": {
        "label": "X",
        "aspect": "16:9",
        "fields": {"post": 280, "post_premium": 25000},
        "link_cost": 23,
        "cite": "help.x.com types-of-posts (280 free, 25000 premium), business.x.com (link costs 23)",
    },
    "linkedin": {
        "label": "LinkedIn",
        "aspect": "16:9",
        "fields": {"post": 3000, "headline": 70},
        "preview_chars": 150,
        "cite": "contentin.io / socialrails LinkedIn post specs 2026, 3000 chars, ~150 before see-more",
    },
    "devpost": {
        "label": "Devpost",
        "aspect": "16:9",
        "fields": {"tagline": 120, "summary": 1500},
        "cite": "house convention: Devpost publishes no field caps, these keep the entry scannable",
    },
}


def stamp(seconds: float, srt: bool = False) -> str:
    total = int(seconds)
    h, m, s = total // 3600, (total % 3600) // 60, total % 60
    if srt:
        ms = int(round((seconds - total) * 1000))
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
def captions(cues: list[dict], total: float) -> str:
    """One SRT block per narration cue, at the exact times the build measured."""
    out: list[str] = []
    for index, cue in enumerate(cues, start=1):
        start = cue["start"]
        end = min(total, start + cue["seconds"])
        out.append(f"{index}\n{stamp(start, True)} --> {stamp(end, True)}\n{cue['text']}\n")
    return "\n".join(out)


def chapters(spec: list[dict], segments: list[dict]) -> list[tuple[float, str]]:
    """Chapter titles come from the project file, their times from the measured segments.

    A chapter entry names the segment it opens on, so a re-cut that moves a segment moves
    its chapter with it instead of leaving a timestamp pointing at the wrong scene.
    """
    by_name = {segment["name"]: segment for segment in segments}
    rows: list[tuple[float, str]] = []
    for entry in spec:
        at = entry.get("at")
        if at is None:
            segment = by_name.get(entry["segment"])
            if segment is None:
                raise SystemExit(
                    f"chapter '{entry['title']}' names segment '{entry['segment']}', "
                    f"which is not in this build: {sorted(by_name)}"
                )
            at = segment["start"]
        rows.append((float(at), entry["title"]))
    return rows


def check_chapters(rows: list[tuple[float, str]], total: float) -> list[str]:
    problems: list[str] = []
    if len(rows) < CHAPTER_MIN_COUNT:
        problems.append(f"{len(rows)} chapters, YouTube needs at least {CHAPTER_MIN_COUNT}")
    if not rows or rows[0][0] > 0.4:
        problems.append("the first chapter must start at 0:00")
    for (at, title), (nxt, _) in zip(rows, rows[1:] + [(total, "")]):
        if nxt <= at:
            problems.append(f"chapters are not ascending at '{title}'")
        elif nxt - at < CHAPTER_MIN_SECONDS:
            problems.append(f"'{title}' runs {nxt - at:.1f}s, under the {CHAPTER_MIN_SECONDS}s floor")
    return problems
PAGE_HEAD = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Upload: {title}</title>
<style>
:root{{--ink:#101828;--muted:#667085;--line:#e4e7ec;--bg:#f6f7f9;--ok:#08795a;--warn:#b42318;--accent:#1f6feb}}
*{{box-sizing:border-box}}
body{{margin:0;padding:28px 20px 60px;background:var(--bg);color:var(--ink);
font:15px/1.6 "Inter","Segoe UI",system-ui,sans-serif}}
main{{max-width:900px;margin:0 auto}}
h1{{font-size:21px;margin:0 0 4px}}
p.sub{{margin:0 0 22px;color:var(--muted);font-size:13.5px}}
section{{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:14px}}
.head{{display:flex;align-items:baseline;gap:10px;margin-bottom:10px;flex-wrap:wrap}}
h2{{font-size:14px;margin:0;text-transform:uppercase;letter-spacing:.05em}}
.count{{font-size:12px;color:var(--muted);font-variant-numeric:tabular-nums}}
.count.over{{color:var(--warn);font-weight:700}}
.hint{{margin:0 0 10px;color:var(--muted);font-size:13px}}
pre{{margin:0;padding:12px 14px;background:#0f172a;color:#e2e8f0;border-radius:9px;
white-space:pre-wrap;word-break:break-word;font:13px/1.6 "SFMono-Regular",Consolas,monospace;
max-height:340px;overflow:auto}}
.actions{{margin-left:auto;display:flex;gap:8px;flex-wrap:wrap}}
button,a.dl{{padding:6px 13px;border:1px solid var(--line);border-radius:8px;background:#fff;
color:var(--ink);font:600 13px/1 inherit;cursor:pointer;text-decoration:none}}
button:hover,a.dl:hover{{border-color:#ccd2da}}
button.done{{background:var(--ok);border-color:var(--ok);color:#fff}}
ol{{margin:0;padding-left:20px}}
li{{margin-bottom:6px}}
code{{background:var(--bg);padding:1px 5px;border-radius:4px;font-size:13px}}
.gate{{font-size:13.5px}}
.gate .pass{{color:var(--ok);font-weight:600}}
.gate .fail{{color:var(--warn);font-weight:700}}
.shots{{display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap}}
.shots figure{{margin:0}}
.shots figcaption{{margin-top:6px;color:var(--muted);font-size:12px}}
img.thumb{{width:520px;max-width:100%;border:1px solid var(--line);border-radius:9px;display:block}}
img.proof{{width:168px;border:1px solid var(--line);border-radius:4px;display:block}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:6px 9px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{color:var(--muted);font-weight:600;text-transform:uppercase;letter-spacing:.04em;font-size:11px}}
td.t{{font-variant-numeric:tabular-nums;white-space:nowrap;
font-family:"SFMono-Regular",Consolas,monospace;color:var(--accent)}}
tr.climax td{{background:#fffaf0}}
dl.form{{margin:0;display:grid;grid-template-columns:190px 1fr auto;gap:8px 12px;align-items:baseline}}
dl.form dt{{color:var(--muted);font-size:12.5px;font-weight:600}}
dl.form dd{{margin:0;font-size:13.5px}}
dl.form dd.v{{font-family:"SFMono-Regular",Consolas,monospace}}
</style></head><body><main>
<h1>{title_escaped}</h1>
<p class="sub">Everything the upload form asks for, in this one file. Every block copies with
one click, the caption file and the thumbnail download from here, and nothing needs another
document open beside it. Video: <code>{video}</code>, {length}.
Public, never unlisted: a submission that links an unlisted video is a broken link to a judge
who is not signed in.</p>
"""

PAGE_TAIL = """<script>
for (const button of document.querySelectorAll("button[data-for]")) {
  button.addEventListener("click", async () => {
    const text = document.getElementById(button.dataset.for).textContent;
    await navigator.clipboard.writeText(text);
    const was = button.textContent;
    button.textContent = "copied";
    button.classList.add("done");
    setTimeout(() => { button.textContent = was; button.classList.remove("done"); }, 1400);
  });
}
</script></main></body></html>
"""


def block(
    key: str, heading: str, body: str, hint: str = "", limit: int | None = None,
    download: tuple[str, str] | None = None,
) -> str:
    count = ""
    if limit is not None:
        over = " over" if len(body) > limit else ""
        count = f'<span class="count{over}">{len(body)} / {limit} characters</span>'
    actions = f'<button data-for="{key}">Copy</button>'
    if download:
        filename, href = download
        actions += f'<a class="dl" download="{filename}" href="{href}">Download {filename}</a>'
    return (
        f'<section><div class="head"><h2>{heading}</h2>{count}'
        f'<span class="actions">{actions}</span></div>'
        + (f'<p class="hint">{hint}</p>' if hint else "")
        + f'<pre id="{key}">{html.escape(body)}</pre></section>\n'
    )


def data_uri(path: Path, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def _thumbnail_block(thumb_path: Path) -> str:
    """The thumbnail lives in the page, not just beside it.

    A thumbnail cannot be copied into a file picker, so it is embedded for the eye and offered
    as a download for the upload. The 168 pixel copy beside it is the gate the rule asks for,
    rendered rather than described: if the headline stops reading at that width, it fails here.
    """
    mime = "image/jpeg" if thumb_path.suffix == ".jpg" else "image/png"
    uri = data_uri(thumb_path, mime)
    kb = thumb_path.stat().st_size / 1024
    return (
        '<section><div class="head"><h2>Thumbnail</h2>'
        f'<span class="count">{Image_size(thumb_path)}, {kb:.0f} KB</span>'
        f'<span class="actions"><a class="dl" download="{thumb_path.name}" href="{uri}">'
        f'Download {thumb_path.name}</a></span></div>'
        '<p class="hint">Generated on this video\'s own palette, never a downloaded image and '
        'never a frame grab. The small copy is the sidebar-width gate: if the headline stops '
        'reading there, regenerate it with fewer words.</p>'
        '<div class="shots">'
        f'<figure><img class="thumb" src="{uri}" alt="thumbnail at full width">'
        '<figcaption>full size</figcaption></figure>'
        f'<figure><img class="proof" src="{uri}" alt="thumbnail at sidebar width">'
        '<figcaption>168px, as a sidebar shows it</figcaption></figure>'
        '</div></section>\n'
    )


def _times_block(timing: dict, rows: list[tuple[float, str]], climaxes: list[str]) -> str:
    """Every in and out time the build measured: the scenes, then the narration cues."""
    total = timing["total"]
    by_name = {segment["name"]: segment for segment in timing["segments"]}
    chapter_at = {round(at, 2): title for at, title in rows}

    scenes = []
    for segment in timing["segments"]:
        start, end = segment["start"], segment["start"] + segment["seconds"]
        chapter = chapter_at.get(round(start, 2), "")
        klass = ' class="climax"' if segment["name"] in climaxes else ""
        scenes.append(
            f'<tr{klass}><td class="t">{stamp(start)}</td><td class="t">{stamp(end)}</td>'
            f'<td class="t">{segment["seconds"]:.2f}s</td><td>{segment["type"]}</td>'
            f'<td>{html.escape(str(segment["name"]))}</td>'
            f'<td>{html.escape(chapter)}</td></tr>'
        )

    cues = []
    for index, cue in enumerate(timing["cues"], start=1):
        start = cue["start"]
        end = min(total, start + cue["seconds"])
        cues.append(
            f'<tr><td class="t">{index}</td><td class="t">{stamp(start, True)}</td>'
            f'<td class="t">{stamp(end, True)}</td>'
            f'<td>{html.escape(cue["text"])}</td></tr>'
        )

    return (
        '<section><div class="head"><h2>In and out times, as the build measured them</h2>'
        f'<span class="count">{len(timing["segments"])} scenes, {len(timing["cues"])} cues, '
        f'{stamp(total)} total</span></div>'
        '<p class="hint">Not re-derived. These are the numbers the render used, so a timestamp '
        'here is a timestamp in the delivered file. Shaded rows are the climaxes that must never '
        'lose time in a re-cut.</p>'
        '<table><thead><tr><th>In</th><th>Out</th><th>Runs</th><th>Type</th><th>Scene</th>'
        '<th>Chapter it opens</th></tr></thead><tbody>' + "".join(scenes) + '</tbody></table>'
        '<p class="hint" style="margin-top:14px">Narration cues, which are the caption in and '
        'out times:</p>'
        '<table><thead><tr><th>#</th><th>In</th><th>Out</th><th>Line</th></tr></thead>'
        '<tbody>' + "".join(cues) + '</tbody></table></section>\n'
    )
# BLOCKS-ANCHOR

def _fields_block(spec: dict, thumb_path: Path, total: float) -> str:
    """The form fields that are a choice rather than prose. Each one copies on its own, because
    some of them are typed into a box rather than picked from a menu."""
    minutes, seconds = divmod(total, 60)
    rows = [
        ("Visibility", "Public", "Never unlisted, and never scheduled past the submission deadline."),
        ("Category", spec.get("category", "Science & Technology"), ""),
        ("Video language", spec.get("language", "English"), ""),
        ("Caption language", spec.get("language", "English"), "Upload captions.srt as subtitles."),
        ("Made for kids", "No, not made for kids", ""),
        (
            "Altered content",
            spec.get("altered", "No"),
            "The narration is synthesised speech and the description says so, which is a "
            "disclosure rather than a realistic depiction of a real person or event.",
        ),
        ("Recording date", spec.get("recorded", "leave blank"), ""),
        ("Playlist", spec.get("playlist", "none"), ""),
        ("Length", f"{int(minutes)}:{seconds:04.1f}", "Measured on the delivered file."),
        ("Thumbnail file", thumb_path.name, "Downloadable from the block above."),
        ("Caption file", "captions.srt", "Downloadable from the block below."),
    ]
    body = []
    for index, (label, value, note) in enumerate(rows):
        key = f"field{index}"
        body.append(
            f"<dt>{html.escape(label)}</dt>"
            f'<dd class="v" id="{key}">{html.escape(value)}</dd>'
            f'<dd><button data-for="{key}">Copy</button></dd>'
        )
        if note:
            body.append(f'<dt></dt><dd class="hint" style="margin:0">{html.escape(note)}</dd><dd></dd>')
    return (
        '<section><div class="head"><h2>The rest of the form</h2></div>'
        f'<dl class="form">{"".join(body)}</dl></section>\n'
    )


def _gate_block(
    title: str, description: str, tags: str,
    rows: list[tuple[float, str]], srt: str, timing: dict, thumb_path: Path, total: float,
) -> str:
    checks = [
        (f"title {len(title)} characters", len(title) <= TITLE_MAX, f"limit {TITLE_MAX}"),
        (f"description {len(description)} characters", len(description) <= DESCRIPTION_MAX,
         f"limit {DESCRIPTION_MAX}"),
        (f"tags {len(tags)} characters", len(tags) <= TAGS_MAX, f"house limit {TAGS_MAX}"),
        (f"{len(rows)} chapters", len(rows) >= CHAPTER_MIN_COUNT, f"minimum {CHAPTER_MIN_COUNT}"),
        ("first chapter at 0:00", bool(rows) and rows[0][0] <= 0.4, "YouTube requires it"),
        ("every chapter at least 10s", not check_chapters(rows, total), "YouTube requires it"),
        (f"{len(timing['cues'])} caption cues", srt.strip().endswith(timing["cues"][-1]["text"]),
         "last cue present in the SRT"),
        ("last caption inside the video",
         timing["cues"][-1]["start"] + timing["cues"][-1]["seconds"] <= total + 0.05,
         f"video is {total:.2f}s"),
        (f"thumbnail {thumb_path.stat().st_size / 1024:.0f} KB",
         thumb_path.stat().st_size <= THUMB_MAX_BYTES, "2 MB mobile cap"),
        (f"thumbnail {Image_size(thumb_path)}", Image_size(thumb_path) == "3840x2160",
         "3840x2160 recommended, 16:9"),
    ]
    body = "".join(
        f'<li><span class="{"pass" if ok else "fail"}">{"pass" if ok else "FAIL"}</span> '
        f"{html.escape(label)} <span class=\"count\">{html.escape(note)}</span></li>"
        for label, ok, note in checks
    )
    return (
        '<section class="gate"><div class="head"><h2>Gates, checked when this was generated</h2>'
        "</div><ol>" + body + "</ol>"
        "<p class=\"hint\">Two gates a script cannot run for you: open the thumbnail at full size "
        "and then shrunk to about 168 pixels wide to confirm it still reads, and fetch every URL "
        "the description cites anonymously for a 200. A description that links a private repo or a "
        "dead site is worse than no description.</p></section>\n"
    )


def _next_block(spec: dict) -> str:
    steps = spec.get("then", [])
    body = "".join(f"<li>{html.escape(step)}</li>" for step in steps)
    return (
        '<section><div class="head"><h2>Once the URL exists</h2></div>'
        f"<ol>{body}</ol></section>\n"
    )


def _platform_blocks(spec: dict) -> str:
    """One copy-block section per extra platform the project asks for.

    A submission goes to more than YouTube: a Shorts cut, an X post, a LinkedIn post, a
    Devpost entry. Each surface has its own fields and its own real limits, so each gets its
    own block with a live count against the number that platform actually enforces. A
    project opts in with an `upload.platforms` map; with none the package is YouTube only,
    exactly as before.
    """
    wanted = spec.get("platforms")
    if not wanted:
        return ""
    sections = ["<h2 class=\"divider\">Other platforms</h2>\n"]
    for key, content in wanted.items():
        profile = PLATFORMS.get(key)
        if profile is None:
            sections.append(f'<section><p class="hint">unknown platform {html.escape(key)}, skipped</p></section>\n')
            continue
        sections.append(f'<h3 class="platform">{profile["label"]}  '
                        f'<span class="cite">{html.escape(profile["cite"])}</span></h3>\n')
        for field, limit in profile["fields"].items():
            value = content.get(field)
            if value is None:
                continue
            text = "\n".join(value) if isinstance(value, list) else str(value)
            hint = ""
            if key == "linkedin" and field == "post":
                hint = f"About {profile['preview_chars']} characters show before the see-more fold, so lead with the hook."
            if key == "x" and field == "post":
                hint = f"A link costs {profile['link_cost']} of these, so a post with the video URL has about {280 - profile['link_cost']} for words."
            sections.append(block(f"{key}-{field}", f"{profile['label']} {field}", text, hint, limit=limit))
        if profile.get("max_seconds"):
            sections.append(f'<section><p class="hint">{profile["label"]} caps the video at '
                           f'{profile["max_seconds"] // 60} minutes, and it must be {profile["aspect"]}. '
                           f'Use the matching render cut, not the 16:9 master.</p></section>\n')
    return "".join(sections)


def _platform_problems(spec: dict) -> list[str]:
    """Limit checks for every requested platform, so a too-long post fails here not at the form."""
    problems: list[str] = []
    for key, content in (spec.get("platforms") or {}).items():
        profile = PLATFORMS.get(key)
        if profile is None:
            problems.append(f"unknown platform {key!r} in upload.platforms")
            continue
        for field, limit in profile["fields"].items():
            value = content.get(field)
            if value is None:
                continue
            text = "\n".join(value) if isinstance(value, list) else str(value)
            if len(text) > limit:
                problems.append(f"{profile['label']} {field} is {len(text)} characters, over {limit}")
    return problems


def main(project_path: Path) -> int:
    project = json.loads(project_path.read_text(encoding="utf-8"))
    pid = project["id"]
    spec = project.get("upload")
    if not spec:
        raise SystemExit(f"{project_path} has no 'upload' block, so there is nothing to publish")

    work = ROOT / "artifacts" / pid
    timing_path = work / "timing.json"
    if not timing_path.exists():
        raise SystemExit(f"{timing_path} is missing. Run build.py first, upload.py reads its timing")
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    total = timing["total"]

    out = work / "upload"
    out.mkdir(parents=True, exist_ok=True)

    rows = chapters(spec["chapters"], timing["segments"])
    chapter_text = "\n".join(f"{stamp(at)} {title}" for at, title in rows)
    (out / "chapters.txt").write_text(chapter_text + "\n", encoding="utf-8")

    srt = captions(timing["cues"], total)
    (out / "captions.srt").write_text(srt, encoding="utf-8")

    thumb_path = thumb.write(
        out / "thumbnail.png",
        palette=timing["palette"],
        name=spec["thumbnail"]["name"],
        claim=spec["thumbnail"]["claim"],
        badge=spec["thumbnail"].get("badge"),
        figure=tuple(spec["thumbnail"]["figure"]) if spec["thumbnail"].get("figure") else None,
        layout=spec["thumbnail"].get("layout", "stack"),
    )

    title = spec["title"]
    description = spec["description"].replace("{chapters}", chapter_text).strip() + "\n"
    tags = ", ".join(spec["tags"])

    page = [PAGE_HEAD.format(
        title=pid,
        title_escaped=html.escape(title),
        video=f"DEMO-{pid}.mp4",
        length=f"{int(total // 60)}:{total % 60:04.1f}",
    )]
    page.append(block("title", "Title", title, limit=TITLE_MAX))
    page.append(block(
        "description", "Description", description,
        "The chapter timestamps are already in it. A description that carries them overrides "
        "YouTube's automatic chapters, which is the point of writing them.",
        limit=DESCRIPTION_MAX,
    ))
    page.append(block(
        "tags", "Tags", tags,
        "YouTube publishes no tag limit and says tags play a minimal role. The 500 character "
        "ceiling is a house convention against keyword stuffing.",
        limit=TAGS_MAX,
    ))
    page.append(block("chapters", "Chapters, on their own", chapter_text,
                      "Already inside the description. Here separately in case it needs re-pasting."))
    page.append(_thumbnail_block(thumb_path))
    page.append(block(
        "captions", "Captions", srt,
        "One block per narration cue at the measured times. Copy it into a caption editor, or "
        "download the file and upload it as subtitles.",
        download=("captions.srt", "data:text/plain;charset=utf-8;base64,"
                  + base64.b64encode(srt.encode("utf-8")).decode("ascii")),
    ))
    page.append(_times_block(timing, rows, spec.get("climaxes", [])))
    page.append(_fields_block(spec, thumb_path, total))
    page.append(_platform_blocks(spec))
    page.append(_gate_block(title, description, tags, rows, srt, timing, thumb_path, total))
    page.append(_next_block(spec))
    page.append(PAGE_TAIL)

    page_path = out / f"UPLOAD-{pid}.html"
    page_path.write_text("".join(page), encoding="utf-8")

    problems = check_chapters(rows, total)
    if len(title) > TITLE_MAX:
        problems.append(f"title is {len(title)} characters, over {TITLE_MAX}")
    if len(description) > DESCRIPTION_MAX:
        problems.append(f"description is {len(description)} characters, over {DESCRIPTION_MAX}")
    if len(tags) > TAGS_MAX:
        problems.append(f"tags are {len(tags)} characters, over the house {TAGS_MAX}")
    size = thumb_path.stat().st_size
    if size > THUMB_MAX_BYTES:
        problems.append(f"thumbnail is {size / 1048576:.2f} MB, over the 2 MB mobile cap")
    short = [c for c in timing["cues"] if c["seconds"] < CUE_MIN_SECONDS]
    if short:
        problems.append(f"{len(short)} caption cues run under {CUE_MIN_SECONDS}s")
    last = timing["cues"][-1]
    if last["start"] + last["seconds"] > total + 0.05:
        problems.append("the last caption ends after the video does")
    problems.extend(_platform_problems(spec))

    print(f"{pid}: upload package in {out}")
    print(f"  title        {len(title)}/{TITLE_MAX} characters")
    print(f"  description  {len(description)}/{DESCRIPTION_MAX} characters")
    print(f"  tags         {len(tags)}/{TAGS_MAX} characters, {len(spec['tags'])} tags")
    print(f"  chapters     {len(rows)}, first at {stamp(rows[0][0])}, last at {stamp(rows[-1][0])}")
    print(f"  captions     {len(timing['cues'])} cues, last out {stamp(total)}")
    print(f"  thumbnail    {size / 1024:.0f} KB, {Image_size(thumb_path)}")
    print(f"  page         {page_path.name}")
    if problems:
        print("\nFAIL")
        for problem in problems:
            print(f"  {problem}")
        return 1
    print("\nevery gate passed. Look at the thumbnail at full size and at 168px wide before upload.")
    return 0


def Image_size(path: Path) -> str:
    from PIL import Image

    with Image.open(path) as image:
        return f"{image.width}x{image.height}"


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    raise SystemExit(main(Path(sys.argv[1])))



