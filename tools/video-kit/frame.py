"""Render single frames at chosen timestamps, without rendering the video.

    python3 frame.py projects/phone-approval-gate.json 27 60 78 92

Uses the same layout the build uses, so a timestamp here is the timestamp in the
finished file. Written to artifacts/<id>/frames/at-<seconds>.png. This is the scrub
check: it costs a second per frame instead of ten minutes per video, so the beats
can be checked before committing to a render.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bg
import build
import theme

ROOT = Path(__file__).resolve().parent
WARM = 3.0
"""Seconds of frames painted before the wanted one.

Zoom, marker and cursor are all stateful, so painting a single frame cold would
show every transition at zero progress. The warm-up replays the run in to the
timestamp and throws those frames away.
"""


def main(project_path: Path, times: list[float]) -> None:
    project = json.loads(project_path.read_text(encoding="utf-8"))
    work = ROOT / "artifacts" / project["id"]
    shots = work / "frames"
    shots.mkdir(parents=True, exist_ok=True)
    name = project.get("palette", "citrus")
    base = bg.background(name, work / f"background-{name}.png")
    accent, mark = theme.palette(name)["accent"], theme.palette(name)["mark"]

    plans, _, total = build.layout(project, work)
    print(f"{project['id']}  {total:.2f}s total")
    for when in times:
        plan = next(
            (item for item in plans if item["offset"] <= when < item["offset"] + item["seconds"]),
            None,
        )
        if plan is None:
            print(f"  {when:7.2f}s  past the end")
            continue
        segment = plan["segment"]
        inside = when - plan["offset"]
        label = segment.get("name", segment.get("title", segment["type"]))
        spoken = next((beat for beat in plan["beats"] if beat[0] <= inside < beat[1]), None)
        cue = "silence" if spoken is None else f"focus {spoken[2] or 'none'}"
        print(f"  {when:7.2f}s  {segment['type']:8s} {label:22s} +{inside:5.2f}s  {cue}")
        painter = build.painter_for(plan, project, work, base, accent, mark, total)
        frame = None
        warm = max(0.0, inside - WARM)
        for step in range(round((inside - warm) * theme.FPS) + 1):
            frame = painter(min(warm + step / theme.FPS, inside))
        frame.save(shots / f"at-{when:g}.png")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("usage: frame.py <project.json> <seconds> [more seconds ...]")
    main(Path(sys.argv[1]), [float(value) for value in sys.argv[2:]])
