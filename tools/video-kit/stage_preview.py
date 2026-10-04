"""Look at a stage scene at a few instants without building a video.

    python3 stage_preview.py episodes/stage/demo.html demo --seconds 12 --times 0.5,2,4.2 \\
        --cues "0.3-3.9|First line;4.2-8.0|Second line" --params '{"tone": "dark"}' --out look.png

    python3 stage_preview.py --project projects/zts-e1.json --segment e1-phrase \\
        --times 1,5,9 --out look.png

Renders the page at each time at DPR 1 (1920x1080) through the same server and page
contract the build captures with, then writes ONE contact sheet no larger than 1600 px on
either side, every tile labelled with its time and the cue playing. Page errors fail it the
way they fail a capture.

With --project and --segment the html, scene, params and the real cue timings come from the
project (cues are synthesised first when they are not cached yet), so a tile here is the
frame the build will capture at that time. Without --times it shows the middle of every cue.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))

import stage  # noqa: E402
import style  # noqa: E402
import theme  # noqa: E402

CAP = 1600
GAP = 8
BAND = 30


def parse_cues(spec: str | None) -> list[dict]:
    """ "0.3-3.9|text;4.2-8.0|text" as cue dicts in segment-local seconds."""
    cues = []
    for part in (spec or "").split(";"):
        part = part.strip()
        if not part:
            continue
        span, _, text = part.partition("|")
        start, _, end = span.partition("-")
        try:
            cues.append({"start": float(start), "end": float(end), "text": text.strip(), "words": []})
        except ValueError:
            raise SystemExit(f"--cues: cannot read {part!r}, want START-END|text") from None
    return cues


def _cue_at(cues: list[dict], t: float):
    return next(((index, cue) for index, cue in enumerate(cues) if cue["start"] <= t < cue["end"]), None)


def contact_sheet(shots: list[tuple[float, Image.Image]], cues: list[dict]) -> Image.Image:
    count = len(shots)
    cols = 1 if count == 1 else 2 if count <= 6 else 3
    rows = math.ceil(count / cols)
    tile_w = (CAP - GAP * (cols - 1)) // cols
    tile_h = round(tile_w * 9 / 16)
    if rows * (BAND + tile_h) + GAP * (rows - 1) > CAP:
        tile_h = (CAP - GAP * (rows - 1)) // rows - BAND
        tile_w = round(tile_h * 16 / 9)
    sheet = Image.new("RGB", (cols * tile_w + GAP * (cols - 1), rows * (BAND + tile_h) + GAP * (rows - 1)),
                      (24, 26, 32))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(theme.SANS, 16)
    for index, (t, image) in enumerate(shots):
        row, col = divmod(index, cols)
        x, y = col * (tile_w + GAP), row * (BAND + tile_h + GAP)
        playing = _cue_at(cues, t)
        label = f"t={t:.2f}s" + (f"   cue {playing[0]}: {playing[1]['text']}" if playing else "   (no cue)")
        while font.getlength(label) > tile_w - 12 and len(label) > 8:
            label = label[:-2].rstrip() + "…"
        draw.text((x + 6, y + 7), label, font=font, fill=(236, 238, 244))
        sheet.paste(image.resize((tile_w, tile_h), Image.LANCZOS), (x, y + BAND))
    assert max(sheet.size) <= CAP, sheet.size
    return sheet


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("html", nargs="?", help="stage page, relative to the repo root")
    parser.add_argument("scene", nargs="?", help="the scene id the page registers")
    parser.add_argument("--seconds", type=float, help="segment length (project mode measures it)")
    parser.add_argument("--times", help="comma separated local times, e.g. 0.5,2,4.2")
    parser.add_argument("--cues", help='"START-END|text;START-END|text" in local seconds')
    parser.add_argument("--params", help="JSON object handed to the scene")
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--project", help="a project file, for real cue timings")
    parser.add_argument("--segment", help="the stage segment name in --project")
    parser.add_argument("--out", required=True, help="the contact sheet PNG to write")
    args = parser.parse_args(argv)

    offset = 0.0
    if args.project:
        if not args.segment:
            parser.error("--project needs --segment NAME")
        project = json.loads(Path(args.project).read_text(encoding="utf-8"))
        theme.configure(style.resolve(project))
        segment = next((s for s in project["segments"]
                        if s.get("type") == "stage" and s.get("name") == args.segment), None)
        if segment is None:
            names = [s.get("name") for s in project["segments"] if s.get("type") == "stage"]
            parser.error(f"no stage segment {args.segment!r} in {args.project}; have {names}")
        work = KIT / "artifacts" / project["id"]
        timing = stage.segment_timing(segment, project, work)
        html = args.html or segment["html"]
        scene = args.scene or segment["scene"]
        params = json.loads(args.params) if args.params else segment.get("params", {}) or {}
        seconds, offset, cues, fps = timing["seconds"], timing["offset"], timing["cues"], theme.FPS
        label = args.segment
    else:
        if not args.html or not args.scene or args.seconds is None:
            parser.error("give HTML SCENE --seconds S, or --project P --segment NAME")
        html, scene, seconds, fps = args.html, args.scene, args.seconds, args.fps
        params = json.loads(args.params) if args.params else {}
        cues = parse_cues(args.cues)
        label = scene
    if not isinstance(params, dict):
        parser.error("--params must be a JSON object")

    if args.times:
        times = [float(value) for value in args.times.split(",") if value.strip()]
    elif cues:
        times = [round((cue["start"] + cue["end"]) / 2, 2) for cue in cues if cue["end"] > cue["start"]][:9]
    else:
        times = [round(seconds * (k + 0.5) / 6, 2) for k in range(6)]
    if not times:
        parser.error("no times to render")

    print(f"{label}: {html} scene {scene!r}, {seconds:.2f}s at {fps} fps, offset {offset:.2f}s")
    for index, cue in enumerate(cues):
        print(f"  cue {index}  {cue['start']:6.2f} - {cue['end']:6.2f}  {cue['text'][:70]}")
    stage_input = {"scene": scene, "params": params, "seconds": seconds, "fps": fps,
                   "offset": offset, "cues": cues}
    html_rel, _ = stage.repo_path(html)
    shots: list[tuple[float, Image.Image]] = []
    with stage.serve() as server:
        with stage.Session(server.url(html_rel, scene), stage_input, 1.0, label) as session:
            print(f"  ready in {session.ready_seconds:.2f}s")
            for t in times:
                if not 0 <= t <= seconds:
                    print(f"  note: t={t} is outside 0..{seconds:.2f}")
                started = time.perf_counter()
                png = session.shot(t)
                shots.append((t, Image.open(io.BytesIO(png)).convert("RGB")))
                print(f"  t={t:6.2f}s  {1000 * (time.perf_counter() - started):5.0f} ms")
            for line in list(dict.fromkeys(session.console_errors))[:6]:
                print(f"  WARNING console error: {line[:300]}")
            for line in list(dict.fromkeys(session.bad_requests))[:6]:
                print(f"  WARNING request: {line[:300]}")
    sheet = contact_sheet(shots, cues)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    print(f"{out}  {sheet.size[0]}x{sheet.size[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
