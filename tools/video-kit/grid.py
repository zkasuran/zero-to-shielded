"""The availability grid, drawn from a real coordination ledger.

Rows are the parties in call order, columns are the candidate slots, and every
cell comes from a `gather` entry in `ledger.jsonl`: yes when that party's recorded
answer included the option, no when it did not, and an empty cell when the option
had already been ruled out so nobody was asked. The empty cells are the point.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

import bg
import theme
from panel import Panel

WIDTH, HEIGHT = theme.CANVAS


def read_ledger(path: str) -> list[dict]:
    import json

    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _heading(slot: dict) -> tuple[str, str]:
    """Day above, time below, both short enough for a column."""
    from datetime import datetime

    when = datetime.fromisoformat(slot["start"])
    day = when.strftime("%a %d %b").replace(" 0", " ")
    spoken = slot["spoken"]
    time = spoken.split(" at ", 1)[1] if " at " in spoken else when.strftime("%I:%M %p")
    return day, time


def matrix(
    base: Image.Image,
    entries: list[dict],
    accent: tuple[int, int, int],
    visible: int | None = None,
    footer: str | None = None,
) -> Panel:
    started = next((entry for entry in entries if entry["kind"] == "run_started"), None)
    if started is None:
        raise RuntimeError("ledger has no run_started entry")
    slots = started["slots"]
    gathers = [entry for entry in entries if entry["kind"] == "gather"]
    chosen = next((entry["slot_id"] for entry in entries if entry["kind"] == "slot_chosen"), None)

    image = base.copy()
    height = 344 + len(gathers) * 104
    top = max(150, (HEIGHT - height) // 2)
    box = (theme.WINDOW_MARGIN + 40, top, WIDTH - theme.WINDOW_MARGIN - 40, top + height)
    bg.drop_shadow(image, box, radius=34)
    left, _, right, bottom = box
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=34, fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)
    draw.text((left + 56, top + 40), "Who can do what", font=theme.DOC_H1, fill=theme.INK)

    name_width = 620
    column = (right - left - name_width - 112) // max(len(slots), 1)
    header_y = top + 130
    for index, slot in enumerate(slots):
        x = left + 56 + name_width + index * column
        day, time = _heading(slot)
        if slot["id"] == chosen:
            draw.rounded_rectangle((x - 16, header_y - 18, x + column - 28, bottom - 70), radius=22,
                                   fill=(247, 250, 255), outline=accent, width=3)
        draw.text((x, header_y), f"option {slot['option']}", font=theme.BUBBLE_WHO, fill=accent)
        draw.text((x, header_y + 34), day, font=theme.DOC_KEY, fill=theme.INK_SOFT)
        draw.text((x, header_y + 68), time, font=theme.PANEL_LABEL, fill=theme.INK)

    boxes: list[tuple[int, int, int, int]] = []
    shown = len(gathers) if visible is None else visible
    y = header_y + 148
    for index, gather in enumerate(gathers):
        result = gather["result"]
        offered = set(gather["feasible_before"])
        available = {
            slot["id"] for slot in slots if slot["option"] in result["available_options"]
        }
        boxes.append((left + 40, y - 10, right - 40, y + 78))
        if index < shown:
            draw.text((left + 56, y + 4), result["party_id"], font=theme.PANEL_LABEL, fill=theme.INK)
            draw.text((left + 56, y + 44), result["phone_masked"], font=theme.CHROME, fill=theme.INK_SOFT)
            for slot_index, slot in enumerate(slots):
                x = left + 56 + name_width + slot_index * column
                if slot["id"] not in offered:
                    draw.text((x + 6, y + 14), "not asked", font=theme.CHROME, fill=(200, 206, 216))
                elif slot["id"] in available:
                    draw.ellipse((x, y + 12, x + 44, y + 56), fill=theme.GREEN)
                    draw.text((x + 12, y + 18), "✓", font=theme.PANEL_VALUE, fill=(255, 255, 255))
                else:
                    draw.ellipse((x, y + 12, x + 44, y + 56), outline=theme.RED, width=3)
                    draw.line((x + 12, y + 34, x + 32, y + 34), fill=theme.RED, width=3)
        y += 104

    if footer is not None:
        draw.text((left + 56, bottom - 54), footer, font=theme.CHROME, fill=theme.INK_SOFT)
    return Panel(image=image, window=box, row_boxes=boxes)
