"""Transitions between segments, and the picture assembly that applies them.

The kit joined segments with `ffmpeg -f concat -c copy`, a hard cut every time. This
adds crossfade, a dip to black or white, a wipe and a slide push, each a native ffmpeg
xfade so there is no per-frame Python cost.

The one real trap here is narration drift. Cues are laid at absolute times, so a
transition that overlaps two segments by `d` seconds makes the video `d` shorter and
would slide every later cue out of sync. The fix lives in build.layout: it is told the
overlaps up front and pins each cue to the segment's real composited position, so the
audio never drifts however long the transition. This module only has to report the
overlap it wants and then build the filter graph that matches.

Default is a cut, and a cut has zero overlap and assembles with concat copy, so a
project that names no transition produces the byte-identical picture the kit always did.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# The four families map to native xfade transition names, so the dissolve is done in the
# encoder rather than frame by frame in Python.
XFADE = {
    "crossfade": "fade",
    "dip": "fadeblack",
    "dipwhite": "fadewhite",
    "wipe": "wipeleft",
    "wiperight": "wiperight",
    "slide": "slideleft",
    "slideright": "slideright",
    "circle": "circleopen",
}


def spec_for(segment: dict, default: dict) -> dict:
    """The transition INTO a segment: its own `transition` key, else the project default."""
    raw = segment.get("transition", default)
    if isinstance(raw, str):
        return {"kind": raw, "seconds": default.get("seconds", 0.5)}
    merged = dict(default)
    merged.update(raw or {})
    return merged


def plan_overlaps(plans: list[dict], default: dict) -> list[float]:
    """One overlap per segment boundary, index i = overlap between piece i-1 and i.

    The first segment has no incoming transition, so overlap[0] is always 0. An overlap
    is capped so it can never be longer than either neighbouring segment, which keeps a
    short card from being swallowed whole by a long dissolve.
    """
    overlaps = [0.0]
    for index in range(1, len(plans)):
        spec = spec_for(plans[index]["segment"], default)
        kind = spec.get("kind", "cut")
        if kind == "cut" or kind not in XFADE:
            overlaps.append(0.0)
            continue
        want = float(spec.get("seconds", 0.5))
        room = min(plans[index - 1]["seconds"], plans[index]["seconds"]) * 0.5
        overlaps.append(max(0.0, min(want, room)))
    return overlaps


def kinds_for(plans: list[dict], default: dict) -> list[str]:
    """The xfade transition name per boundary, aligned with plan_overlaps."""
    out = ["cut"]
    for index in range(1, len(plans)):
        spec = spec_for(plans[index]["segment"], default)
        out.append(spec.get("kind", "cut"))
    return out


def assemble(pieces: list[Path], overlaps: list[float], kinds: list[str], durations: list[float],
             out: Path, fps: int, size: tuple[int, int], encode_args: list[str], run) -> None:
    """Join the rendered pieces, applying any transitions.

    With every overlap zero this is the original concat copy, so the default cut path is
    unchanged and costs nothing. With any overlap it chains xfade filters, which has to
    re-encode because a dissolve creates new frames, so the encode args are applied here
    too rather than copying the stream.
    """
    if not any(overlaps):
        listing = out.parent / "concat.txt"
        listing.write_text("".join(f"file '{piece}'\n" for piece in pieces), encoding="utf-8")
        run(["ffmpeg", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0",
             "-i", str(listing), "-c", "copy", str(out)])
        return

    cmd = ["ffmpeg", "-loglevel", "error", "-y"]
    for piece in pieces:
        cmd += ["-i", str(piece)]
    # Normalise every input to the same fps, format and SAR so xfade accepts them.
    filters = []
    labels = []
    for index in range(len(pieces)):
        label = f"v{index}"
        filters.append(
            f"[{index}:v]fps={fps},format=yuv420p,settb=AVTB,setsar=1[{label}]"
        )
        labels.append(label)

    prev = labels[0]
    running = durations[0]
    for index in range(1, len(pieces)):
        d = overlaps[index]
        name = XFADE.get(kinds[index], "fade")
        offset = running - d
        target = f"x{index}"
        filters.append(
            f"[{prev}][{labels[index]}]xfade=transition={name}:duration={d:.3f}:offset={offset:.3f}[{target}]"
        )
        prev = target
        running += durations[index] - d

    cmd += ["-filter_complex", ";".join(filters), "-map", f"[{prev}]",
            "-c:v", "libx264", *encode_args, "-pix_fmt", "yuv420p", str(out)]
    run(cmd)


def total_after(durations: list[float], overlaps: list[float]) -> float:
    """The composited duration once the overlaps are removed."""
    return sum(durations) - sum(overlaps)
