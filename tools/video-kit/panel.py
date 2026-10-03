"""Structured panels: step lists, chip rows and key-value cards.

Where the terminal window shows what a program printed, a panel shows what a
program *produced*: the steps of a real pipeline run with their real exit codes,
the disclosure budget from a real errand file, the outcome fields from a real
report. Every value passed in here comes from a file on disk or a command that
actually ran.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image, ImageDraw

import bg
import theme

WIDTH, HEIGHT = theme.CANVAS


@dataclass
class Row:
    label: str
    value: str = ""
    status: str = "plain"  # pass | fail | warn | running | plain


@dataclass
class Panel:
    image: Image.Image
    window: tuple[int, int, int, int]
    row_boxes: list[tuple[int, int, int, int]] = field(default_factory=list)

    @property
    def boxes(self) -> list[tuple[int, int, int, int]]:
        return self.row_boxes


ICONS = {
    "pass": (theme.GREEN, "✓"),
    "fail": (theme.RED, "✕"),
    "warn": (theme.AMBER, "!"),
    "running": (theme.BLUE, "●"),
    "plain": (theme.INK_SOFT, "•"),
}


def _window(rows: int, has_title: bool) -> tuple[int, int, int, int]:
    height = min(HEIGHT - 170, max(420, (110 if has_title else 60) + rows * 78 + 90))
    top = max(110, (HEIGHT - height) // 2)
    return (theme.WINDOW_MARGIN + 60, top, WIDTH - theme.WINDOW_MARGIN - 60, top + height)


def panel(
    base: Image.Image,
    title: str | None,
    rows: list[Row],
    accent: tuple[int, int, int],
    visible: int | None = None,
    footer: str | None = None,
) -> Panel:
    image = base.copy()
    box = _window(len(rows), title is not None)
    bg.drop_shadow(image, box, radius=34)
    left, top, right, bottom = box
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=34, fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)

    y = top + 44
    if title is not None:
        draw.text((left + 56, y), title, font=theme.KICKER, fill=accent)
        y += 74
        draw.line((left + 56, y - 12, right - 56, y - 12), fill=(228, 232, 240), width=2)

    shown = len(rows) if visible is None else visible
    boxes: list[tuple[int, int, int, int]] = []
    for index, row in enumerate(rows):
        colour, glyph = ICONS.get(row.status, ICONS["plain"])
        boxes.append((left + 40, y - 6, right - 40, y + 62))
        if index < shown:
            draw.ellipse((left + 56, y + 12, left + 90, y + 46), outline=colour, width=3)
            draw.text((left + 66, y + 14), glyph, font=theme.CHROME, fill=colour)
            draw.text((left + 116, y + 8), row.label, font=theme.PANEL_LABEL, fill=theme.INK)
            if row.value:
                width = draw.textlength(row.value, font=theme.PANEL_VALUE)
                draw.text((right - 60 - width, y + 14), row.value, font=theme.PANEL_VALUE, fill=colour if row.status != "plain" else theme.INK_SOFT)
        y += 78

    if footer is not None:
        draw.text((left + 56, bottom - 62), footer, font=theme.CHROME, fill=theme.INK_SOFT)
    return Panel(image=image, window=box, row_boxes=boxes)


def chips(
    base: Image.Image,
    title: str,
    items: list[tuple[str, str]],
    accent: tuple[int, int, int],
    visible: int | None = None,
    footer: str | None = None,
) -> Panel:
    """One rounded chip per authorized detail. Used for the disclosure budget."""
    image = base.copy()
    rows = (len(items) + 1) // 2
    height = min(HEIGHT - 200, max(400, 150 + rows * 118 + 80))
    top = max(130, (HEIGHT - height) // 2)
    box = (theme.WINDOW_MARGIN + 60, top, WIDTH - theme.WINDOW_MARGIN - 60, top + height)
    bg.drop_shadow(image, box, radius=34)
    left, _, right, bottom = box
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=34, fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)
    draw.text((left + 56, top + 44), title, font=theme.KICKER, fill=accent)

    boxes: list[tuple[int, int, int, int]] = []
    shown = len(items) if visible is None else visible
    column_width = (right - left - 152) // 2
    for index, (label, value) in enumerate(items):
        column, row = index % 2, index // 2
        x = left + 56 + column * (column_width + 40)
        y = top + 150 + row * 118
        chip = (x, y, x + column_width, y + 92)
        boxes.append(chip)
        if index < shown:
            draw.rounded_rectangle(chip, radius=24, fill=(246, 248, 252), outline=(226, 232, 242), width=2)
            draw.text((x + 28, y + 16), label, font=theme.CHROME, fill=theme.INK_SOFT)
            draw.text((x + 28, y + 48), value, font=theme.PANEL_LABEL, fill=theme.INK)
    if footer is not None:
        draw.text((left + 56, bottom - 60), footer, font=theme.CHROME, fill=theme.INK_SOFT)
    return Panel(image=image, window=box, row_boxes=boxes)
