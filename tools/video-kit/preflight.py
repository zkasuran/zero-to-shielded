"""Prove a project can be drawn before spending ten minutes rendering it.

    python3 preflight.py projects/phone-approval-gate.json

Every segment is prepared for real (commands run, pipelines run, files read) and one
full frame is written to artifacts/<id>/preflight/. Every focus needle is resolved
against the scene it points at, so a slice marker that moved, a file that is not
there or a needle that matches nothing fails here rather than half way through a
render.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bg
import build
import cards
import motion
import style as style_module
import theme

ROOT = Path(__file__).resolve().parent


def check(path: Path) -> int:
    project = json.loads(path.read_text(encoding="utf-8"))
    resolved = theme.configure(style_module.resolve(project))
    work = ROOT / "artifacts" / project["id"]
    shots = work / "preflight"
    shots.mkdir(parents=True, exist_ok=True)
    name = project.get("palette", "citrus")
    base = bg.background(name, work / f"background-{name}-{resolved.canvas[0]}x{resolved.canvas[1]}.png")
    accent, mark = theme.palette(name)["accent"], theme.palette(name)["mark"]

    problems: list[str] = []
    for index, segment in enumerate(project["segments"]):
        kind = segment["type"]
        label = segment.get("name", segment.get("title", kind))
        if kind == "card":
            image = cards.page(
                base, segment["lines"], segment.get("kicker"), segment.get("footer"),
                segment.get("mono", False), accent,
            )
            boxes: list[tuple[int, int, int, int]] = []
            resolve = None
        else:
            page_for, count, resolve = build.prepare(segment, project, work, base, accent, mark)
            page = page_for(count)
            image, boxes = page.image.copy(), page.boxes
            print(f"  {index:02d} {kind:8s} {count:2d} rows  {label}")
        for text, focus, _raw in build.entries(segment):
            for needle in focus:
                found = resolve(needle) if isinstance(needle, str) else [int(needle)]
                if not found:
                    problems.append(f"{path.name} segment {index:02d} ({label}): focus {needle!r} matches nothing")
                for spot in found:
                    if spot < len(boxes):
                        motion.mark(image, boxes[spot], mark, 1.0)
        motion.deliver(image, motion.full_box()).save(shots / f"{index:02d}-{kind}.png")

    for line in problems:
        print(f"  FAIL {line}")
    return len(problems)


def themes() -> int:
    """One theme per video. Two projects on the same palette is a failure, not a taste call.

    A set of videos that share a field reads as one template with the words swapped,
    which is exactly what the house rule exists to stop. Free themes are printed so the
    next project can claim one.
    """
    # A `series` key groups episodes that are meant to read as one set (one opening card,
    # one palette). The rule then holds per series: a palette may belong to one video or to
    # one series, never to two of either.
    taken: dict[str, dict[str, list[str]]] = {}
    for path in sorted((ROOT / "projects").glob("*.json")):
        project = json.loads(path.read_text(encoding="utf-8"))
        owner = project.get("series") or project["id"]
        taken.setdefault(project.get("palette", "citrus"), {}).setdefault(owner, []).append(project["id"])
    problems = 0
    print("\nthemes")
    for name, owners in sorted(taken.items()):
        field = theme.palette(name).get("field", "vertical")
        projects = [pid for group in owners.values() for pid in group]
        print(f"  {name:8s} {field:8s} {', '.join(projects)}")
        if len(owners) > 1:
            problems += 1
            print(f"  FAIL {name} is used by {len(owners)} videos or series: {', '.join(sorted(owners))}")
    free = [name for name in theme.PALETTES if name not in taken]
    print(f"  free: {', '.join(free) if free else 'none, add a palette to theme.py'}")
    return problems


def layouts() -> int:
    """One thumbnail layout per demo, the same rule the palette gets and for the same reason.

    A theme recoloured onto one fixed composition is still one composition, so two demos
    sharing a layout read as a template. `stack` is exempt: it is the original layout and
    every demo built before 2026-09-08 holds it, so failing it would fail history rather
    than a choice anybody is making now.
    """
    import thumb

    taken: dict[str, list[str]] = {}
    for path in sorted((ROOT / "projects").glob("*.json")):
        project = json.loads(path.read_text(encoding="utf-8"))
        spec = project.get("upload")
        if not spec:
            continue
        taken.setdefault(spec.get("thumbnail", {}).get("layout", "stack"), []).append(project["id"])
    problems = 0
    print("\nthumbnail layouts")
    for name, projects in sorted(taken.items()):
        print(f"  {name:8s} {', '.join(projects)}")
        if name not in thumb.LAYOUTS:
            problems += 1
            print(f"  FAIL {name} is not in thumb.LAYOUTS: {sorted(thumb.LAYOUTS)}")
        elif name != "stack" and len(projects) > 1:
            problems += 1
            print(f"  FAIL layout {name} is claimed by {len(projects)} demos: {', '.join(projects)}")
    free = [n for n in thumb.LAYOUTS if n != "stack" and n not in taken]
    print(f"  free: {', '.join(free) if free else 'none, add a layout to thumb.py'}")
    return problems


def estimate(path: Path) -> float:
    """A rough duration estimate from the narration, so a video heading over its cap shows
    before ten minutes of rendering rather than after.

    Speech runs about 2.6 words a second at the kit's default rate, plus the lead and the
    per-segment pad. This is not the measured total the build produces, it is a cheap early
    warning, so it is deliberately approximate and says so.
    """
    project = json.loads(path.read_text(encoding="utf-8"))
    words = 0
    pad = 0.0
    for segment in project.get("segments", []):
        pad += segment.get("pad", 0.9) + 0.3
        for entry in segment.get("narration", []):
            text = entry if isinstance(entry, str) else entry.get("text", "")
            words += len(text.split())
    return words / 2.6 + pad


def cap_check(path: Path) -> int:
    project = json.loads(path.read_text(encoding="utf-8"))
    cap = float(project.get("cap", 176.0))
    seconds = estimate(path)
    verdict = "ok" if seconds < cap else "OVER CAP"
    print(f"  estimate ~{seconds:.0f}s against {cap:.0f}s cap  {verdict}")
    return 1 if seconds >= cap else 0


def contrast_check(path: Path) -> int:
    """Fail a project on a palette that does not clear the contrast gate, when contrast.py
    is present. Imported defensively so the kit still runs without it."""
    try:
        import contrast
    except ImportError:
        return 0
    project = json.loads(path.read_text(encoding="utf-8"))
    name = project.get("palette", "citrus")
    mode = theme.PALETTES.get(name, {}).get("mode", "light")
    problems = contrast.check_palette(name, mode)
    for line in problems:
        print(f"  contrast FAIL {name}: {line}")
    return len(problems)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: preflight.py <project.json> [more.json ...]")
    failures = 0

    # schema first: a structural error should fail before any rendering is attempted
    try:
        import schema
        targets = [Path(a) for a in sys.argv[1:]]
        for target in targets:
            errors, warnings = schema.check(target)
            if errors or warnings:
                print(f"\n{target.name} (schema)")
            for line in errors:
                print(f"  ERROR   {line}")
                failures += 1
            for line in warnings:
                print(f"  warning {line}")
    except ImportError:
        pass

    for argument in sys.argv[1:]:
        target = Path(argument)
        print(f"\n{target.name}")
        failures += check(target)
        failures += cap_check(target)
        failures += contrast_check(target)
    failures += themes()
    failures += layouts()
    raise SystemExit(1 if failures else 0)
