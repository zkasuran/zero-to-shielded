"""The terminal window.

One page image per reveal step: the background field, a near-white window floating
on it with a soft shadow, the command, and as many captured output lines as are
visible at that moment. The page also hands back the pixel box of every line, which
is what the zoom, the marker sweep and the cursor aim at.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image, ImageDraw

import bg
import theme

WIDTH, HEIGHT = theme.CANVAS


@dataclass
class Page:
    image: Image.Image
    window: tuple[int, int, int, int]
    line_boxes: list[tuple[int, int, int, int]] = field(default_factory=list)
    prompt_box: tuple[int, int, int, int] = (0, 0, 0, 0)

    @property
    def boxes(self) -> list[tuple[int, int, int, int]]:
        return self.line_boxes


def window_box(line_count: int, footer: bool) -> tuple[int, int, int, int]:
    body = theme.LINE_HEIGHT * max(line_count, 1)
    height = min(HEIGHT - 150, max(430, theme.PAD_TOP + 62 + body + (104 if footer else 60)))
    top = max(96, (HEIGHT - height) // 2)
    return (theme.WINDOW_MARGIN, top, WIDTH - theme.WINDOW_MARGIN, top + height)


def _wrap_pixels(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Greedy word wrap measured in real pixels, so a footer never runs off the
    window regardless of the resolved canvas size or the font."""
    words = text.split(" ")
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if not current or draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def page(
    base: Image.Image,
    header: str,
    prompt: str,
    lines: list[str],
    visible: int,
    footer: str | None,
    accent: tuple[int, int, int],
) -> Page:
    image = base.copy()
    box = window_box(len(lines), footer is not None)
    bg.drop_shadow(image, box, radius=30)
    left, top, right, bottom = box
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=30, fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)
    draw.rounded_rectangle((left, top, right, top + 66), radius=30, fill=(244, 246, 250))
    draw.rectangle((left, top + 40, right, top + 66), fill=(244, 246, 250))
    for offset, colour in ((0, (255, 95, 87)), (34, (255, 189, 46)), (68, (39, 201, 63))):
        draw.ellipse((left + 34 + offset, top + 24, left + 52 + offset, top + 42), fill=colour)
    draw.text((left + 160, top + 22), header, font=theme.CHROME, fill=theme.INK_SOFT)

    text_left = left + theme.PAD_X
    y = top + theme.PAD_TOP
    draw.text((text_left, y), "$", font=theme.CODE_BOLD, fill=accent)
    draw.text((text_left + 34, y), prompt, font=theme.CODE, fill=theme.INK)
    prompt_box = (text_left, y, right - theme.PAD_X, y + theme.LINE_HEIGHT)
    y += 62

    boxes: list[tuple[int, int, int, int]] = []
    previous = theme.INK
    for index, line in enumerate(lines):
        width = draw.textlength(line, font=theme.CODE) if line else 0
        boxes.append((text_left, y, text_left + max(round(width), 60), y + theme.LINE_HEIGHT))
        colour = theme.colour_for(line)
        # A wrapped line keeps the colour of the line it belongs to. term.slice_output
        # indents a continuation past its own row, so a deeply indented row under a
        # coloured one is the rest of that row, and a red failure quote never breaks
        # into black halfway through.
        if colour == theme.INK and previous != theme.INK and line.startswith(" " * 9):
            colour = previous
        if index < visible:
            draw.text((text_left, y), line, font=theme.CODE, fill=colour)
        previous = colour if line.strip() else theme.INK
        y += theme.LINE_HEIGHT
        if y > bottom - 90:
            break
    while len(boxes) < len(lines):
        boxes.append(boxes[-1] if boxes else prompt_box)

    if footer is not None:
        # A focused cue zooms the delivered frame into a crop no wider than
        # motion.focus_box's min_width (1780 reference px, scaled to the canvas),
        # anchored near the text left. A footer drawn to the full window width has its
        # tail sliced off by that crop, so wrap it to the crop's usable width instead,
        # the same envelope the body lines already sit inside.
        focus_width = round(1780 * (min(WIDTH, HEIGHT) / 1440))
        max_width = min(right - theme.PAD_X - text_left, focus_width - 2 * theme.PAD_X)
        foot_lines = _wrap_pixels(draw, footer, theme.CHROME, max_width)
        ascent, descent = theme.CHROME.getmetrics()
        foot_step = ascent + descent + 6
        start_y = bottom - 42 - foot_step * (len(foot_lines) - 1)
        for offset, foot_line in enumerate(foot_lines):
            draw.text((text_left, start_y + offset * foot_step), foot_line, font=theme.CHROME, fill=theme.INK_SOFT)
    return Page(image=image, window=box, line_boxes=boxes, prompt_box=prompt_box)
