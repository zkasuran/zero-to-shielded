"""A source file as a card, with light syntax colour.

The lines come from a real file in the repository, sliced by line number or by
marker, so what is on screen is what a reviewer would read in the pull request.
"""

from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw

import bg
import theme
from panel import Panel

WIDTH, HEIGHT = theme.CANVAS

KEY = (28, 92, 190)
STRING = (13, 122, 76)
COMMENT = (140, 150, 166)
PUNCT = (104, 116, 134)
NUMBER = (162, 92, 0)


def read_lines(path: Path, start: str | None, end: str | None, limit: int = 22) -> tuple[list[str], int]:
    """The sliced view plus the file line number it starts at, so the gutter is honest."""
    lines = path.read_text(encoding="utf-8").splitlines()
    first = 0
    if start is not None:
        first = next((index for index, line in enumerate(lines) if start in line), 0)
    last = len(lines)
    if end is not None:
        last = next((index + 1 for index, line in enumerate(lines[first:], first) if end in line), len(lines))
    view = [line.rstrip() for line in lines[first:last]]
    return view[:limit], first + 1


def _spans(line: str) -> list[tuple[str, tuple[int, int, int]]]:
    stripped = line.strip()
    if stripped.startswith("#") or stripped.startswith("//"):
        return [(line, COMMENT)]
    match = re.match(r"^(\s*-?\s*)([A-Za-z_][\w.-]*)(:)(.*)$", line)
    if match is not None:
        head, key, colon, rest = match.groups()
        spans = [(head, PUNCT), (key, KEY), (colon, PUNCT)]
        spans.extend(_value_spans(rest))
        return spans
    return _value_spans(line)


def _value_spans(text: str) -> list[tuple[str, tuple[int, int, int]]]:
    out: list[tuple[str, tuple[int, int, int]]] = []
    for chunk in re.split(r'("[^"]*"|\$\{\{[^}]*\}\}|\b\d+\b)', text):
        if not chunk:
            continue
        if chunk.startswith('"') or chunk.startswith("${{"):
            out.append((chunk, STRING))
        elif chunk.isdigit():
            out.append((chunk, NUMBER))
        else:
            out.append((chunk, theme.INK))
    return out


def file_card(
    base: Image.Image,
    title: str,
    lines: list[str],
    accent: tuple[int, int, int],
    visible: int | None = None,
    footer: str | None = None,
    first_line: int = 1,
) -> Panel:
    image = base.copy()
    height = min(HEIGHT - 200, max(400, 150 + len(lines) * 40 + 90))
    top = max(120, (HEIGHT - height) // 2)
    box = (theme.WINDOW_MARGIN + 60, top, WIDTH - theme.WINDOW_MARGIN - 60, top + height)
    bg.drop_shadow(image, box, radius=30)
    left, _, right, bottom = box
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=30, fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)
    draw.rounded_rectangle((left, top, right, top + 74), radius=30, fill=(244, 246, 250))
    draw.rectangle((left, top + 44, right, top + 74), fill=(244, 246, 250))
    draw.text((left + 44, top + 24), title, font=theme.CHROME, fill=theme.INK_SOFT)

    boxes: list[tuple[int, int, int, int]] = []
    shown = len(lines) if visible is None else visible
    y = top + 116
    for index, line in enumerate(lines):
        boxes.append((left + 40, y - 4, right - 40, y + 38))
        if index < shown:
            draw.text((left + 44, y), f"{first_line + index:>3}", font=theme.CODE_SMALL, fill=(196, 204, 216))
            x = left + 120
            for text, colour in _spans(line):
                draw.text((x, y), text, font=theme.CODE_SMALL, fill=colour)
                x += draw.textlength(text, font=theme.CODE_SMALL)
        y += 40
        if y > bottom - 70:
            break
    while len(boxes) < len(lines):
        boxes.append(boxes[-1] if boxes else box)
    if footer is not None:
        draw.text((left + 44, bottom - 52), footer, font=theme.CHROME, fill=theme.INK_SOFT)
    return Panel(image=image, window=box, row_boxes=boxes)
