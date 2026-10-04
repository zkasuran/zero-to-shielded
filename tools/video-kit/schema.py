"""Validate a project file before anything runs.

There are 32 project files and no validator, so a typo used to surface either as a crash
minutes into a render or, worse, as a silently wrong picture. This reads a project the way
the build will and reports what is wrong while it is still cheap.

    python3 schema.py projects/*.json

Errors mean the build cannot work. Warnings mean it will run but something looks wrong, a
stale input or an unknown key that is probably a typo for a real one. An unknown key is
matched against the known set so the message can name the likely intent rather than only
saying no.
"""

from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path

import style as style_module
import theme

ROOT = Path(__file__).resolve().parent

PROJECT_KEYS = {
    "id", "header", "palette", "voice", "voices", "rate", "pitch", "volume", "cap",
    "segments", "upload", "note", "captions", "cadence", "style", "render", "renders",
    "transitions", "audio", "timing", "series", "engine",
}

COMMON_SEGMENT_KEYS = {
    "type", "name", "title", "footer", "header", "pad", "narration", "hold", "cadence",
    "min_seconds", "transition",
}

# Required and optional keys per scene type. Only the types the build handles directly are
# listed; a registered scene module is checked for its type being known, not its keys,
# because the registry owns that contract.
SEGMENT_SPECS = {
    "card": ({"lines"}, {"kicker", "mono"}),
    "term": ({"cwd", "cmd"}, {"prompt", "from", "to", "max_lines", "wrap"}),
    "web": ({"section"}, {"url", "file", "items", "viewport", "wait_ms", "hide"}),
    "code": ({"file", "title"}, {"from", "to", "max_lines"}),
    "steps": ({"script", "app"}, {"mode"}),
    "receipts": ({"file"}, set()),
    "grid": ({"ledger"}, set()),
    "chips": ({"errand", "title"}, set()),
    "report": ({"report"}, set()),
    "bubbles": ({"report"}, {"max_turns"}),
    "chart": ({"chart"}, {"file", "path", "rows", "series", "x", "y", "unit", "source",
                          "thresholds", "label_key", "value_key", "x_labels", "max"}),
    "diagram": ({"nodes"}, {"edges", "layout"}),
    "diff": (set(), {"repo", "rev", "file", "before", "after", "patch", "mode", "hunk", "max_lines"}),
    "device": (set(), {"frame", "url", "file", "section", "items", "viewport", "wait_ms"}),
    "compose": ({"panes"}, {"layout", "gap", "inset"}),
    "overlay": ({"elements"}, {"under"}),
}


def _suggest(key: str, known) -> str:
    match = difflib.get_close_matches(key, sorted(known), n=1, cutoff=0.7)
    return f", did you mean {match[0]!r}" if match else ""


def check(path: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    try:
        project = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as problem:
        return [f"cannot read: {problem}"], []

    for key in ("id", "segments"):
        if key not in project:
            errors.append(f"missing required key {key!r}")
    if errors:
        return errors, warnings

    for key in project:
        if key not in PROJECT_KEYS:
            warnings.append(f"unknown project key {key!r}{_suggest(key, PROJECT_KEYS)}")

    palette = project.get("palette", "citrus")
    if palette not in theme.PALETTES:
        errors.append(f"unknown palette {palette!r}{_suggest(palette, theme.PALETTES)}")

    try:
        resolved = style_module.resolve(project)
    except (ValueError, KeyError) as problem:
        errors.append(f"style does not resolve: {problem}")
        resolved = None
    if resolved is not None:
        for role, font_path in resolved.fonts.items():
            if not Path(font_path).exists():
                warnings.append(f"font {role} missing at {font_path}")

    style_module.load_scene_modules()
    known_types = set(style_module.known()) | set(SEGMENT_SPECS)

    segments = project.get("segments") or []
    if not segments:
        errors.append("no segments")
    for index, segment in enumerate(segments):
        where = f"segment {index:02d}"
        kind = segment.get("type")
        if not kind:
            errors.append(f"{where}: no type")
            continue
        if kind not in known_types:
            errors.append(f"{where}: unknown type {kind!r}{_suggest(kind, known_types)}")
            continue
        required, optional = SEGMENT_SPECS.get(kind, (set(), set()))
        for key in required:
            if key not in segment:
                errors.append(f"{where} ({kind}): missing {key!r}")
        allowed = COMMON_SEGMENT_KEYS | required | optional
        for key in segment:
            if key not in allowed:
                warnings.append(f"{where} ({kind}): unknown key {key!r}{_suggest(key, allowed)}")

        # inputs the build will actually open
        for key in ("file", "ledger", "errand", "report", "patch", "before", "after"):
            value = segment.get(key)
            if isinstance(value, str) and not value.startswith(("http://", "https://")):
                if not Path(value).exists():
                    errors.append(f"{where} ({kind}): {key} not found: {value}")
        if "cwd" in segment and not Path(segment["cwd"]).exists():
            errors.append(f"{where} ({kind}): cwd not found: {segment['cwd']}")
        if "repo" in segment and not (Path(segment["repo"]) / ".git").exists():
            errors.append(f"{where} ({kind}): repo is not a git checkout: {segment['repo']}")
        if kind == "term" and not isinstance(segment.get("cmd"), list):
            errors.append(f"{where}: cmd must be a list of arguments")
        url = segment.get("url")
        if isinstance(url, str) and not url.startswith(("http://", "https://", "file://")):
            errors.append(f"{where} ({kind}): url has no scheme: {url}")

        for entry in segment.get("narration", []):
            if isinstance(entry, str):
                continue
            if not isinstance(entry, dict):
                errors.append(f"{where}: narration entry is not a string or object")
                continue
            if "text" not in entry and "pause" not in entry:
                errors.append(f"{where}: narration entry has neither text nor pause")
            focus = entry.get("focus", [])
            if not isinstance(focus, (str, int, list)):
                errors.append(f"{where}: focus must be a string, an index or a list")
            speaker = entry.get("speaker")
            if speaker and speaker not in (project.get("voices") or {}):
                errors.append(f"{where}: narration names speaker {speaker!r} with no entry in voices")

    upload = project.get("upload")
    if upload is not None:
        for key in ("title", "description"):
            if key not in upload:
                errors.append(f"upload block missing {key!r}")
        title = upload.get("title", "")
        if len(title) > 100:
            errors.append(f"upload title is {len(title)} characters, over YouTube's 100")
        description = upload.get("description", "")
        if isinstance(description, list):
            description = "\n".join(description)
        if len(description) > 5000:
            errors.append(f"upload description is {len(description)} characters, over YouTube's 5000")

    return errors, warnings


def main(paths) -> int:
    failed = 0
    total_warnings = 0
    for path in paths:
        errors, warnings = check(Path(path))
        total_warnings += len(warnings)
        if errors or warnings:
            print(f"\n{Path(path).name}")
        for line in errors:
            print(f"  ERROR   {line}")
        for line in warnings:
            print(f"  warning {line}")
        if errors:
            failed += 1
    print(f"\n{len(paths)} projects, {failed} with errors, {total_warnings} warnings")
    return failed


if __name__ == "__main__":
    targets = sys.argv[1:] or sorted(str(p) for p in (ROOT / "projects").glob("*.json"))
    raise SystemExit(1 if main(targets) else 0)
