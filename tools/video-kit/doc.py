"""Document scenes: the call report as a card, and the transcript as bubbles.

Both read the real `report.json` the app wrote, so every field on screen is a
value the program produced. The transcript is the accessibility deliverable, so it
gets speaker labels, timestamps and enough room to read.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

import bg
import theme
from panel import Panel

WIDTH, HEIGHT = theme.CANVAS

BADGE = {
    "goal_met": (theme.GREEN, "goal met"),
    "partially_met": (theme.AMBER, "partly met"),
    "not_met": (theme.RED, "not met"),
    "callee_declined_automated": (theme.RED, "they refuse automated callers"),
    "voicemail": (theme.AMBER, "voicemail"),
    "not_reached": (theme.RED, "not reached"),
    "api_error": (theme.RED, "call failed"),
}


def _when(iso: str) -> str:
    """The committed time as a person would say it, from the recorded ISO value."""
    from datetime import datetime

    try:
        when = datetime.fromisoformat(iso)
    except ValueError:
        return iso
    return when.strftime("%A, %B %d at %I:%M %p").replace(" 0", " ")


def _card(image: Image.Image, box, radius: int = 34) -> ImageDraw.ImageDraw:
    bg.drop_shadow(image, box, radius=radius)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=radius, fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)
    return draw


def report(base: Image.Image, data: dict, accent: tuple[int, int, int], visible: int | None = None) -> Panel:
    image = base.copy()
    box = (theme.WINDOW_MARGIN + 40, 150, WIDTH - theme.WINDOW_MARGIN - 40, HEIGHT - 170)
    draw = _card(image, box)
    left, top, right, bottom = box
    boxes: list[tuple[int, int, int, int]] = []

    draw.text((left + 60, top + 46), f"Call report  {data['errand_id']}", font=theme.DOC_H1, fill=theme.INK)
    colour, label = BADGE.get(data["outcome"], (theme.INK_SOFT, data["outcome"]))
    width = draw.textlength(label.upper(), font=theme.BUBBLE_WHO) + 56
    draw.rounded_rectangle((right - 60 - width, top + 52, right - 60, top + 96), radius=22, fill=colour)
    draw.text((right - 60 - width + 28, top + 62), label.upper(), font=theme.BUBBLE_WHO, fill=(255, 255, 255))

    y = top + 132
    for key, value in (
        ("on behalf of", data["on_behalf_of"]),
        ("called", f"{data['callee_name']}  {data['callee_phone_masked']}"),
    ):
        draw.text((left + 60, y), key, font=theme.DOC_KEY, fill=theme.INK_SOFT)
        draw.text((left + 340, y - 3), value, font=theme.DOC_VALUE, fill=theme.INK)
        y += 52

    y += 26
    draw.text((left + 60, y), "What was agreed", font=theme.KICKER, fill=accent)
    y += 58
    committed = data.get("committed_datetime")
    draw.text((left + 60, y), _when(committed) if committed else "nothing was agreed",
              font=theme.DOC_VALUE, fill=theme.INK)
    if committed:
        trail = f"{committed}"
        if data.get("confirmation_code"):
            trail += f"   confirmation {data['confirmation_code']}"
        draw.text((left + 60, y + 46), trail, font=theme.DOC_KEY, fill=theme.INK_SOFT)
    y += 116

    draw.text((left + 60, y), "Your questions", font=theme.KICKER, fill=accent)
    y += 56
    shown = len(data["answers"]) if visible is None else visible
    for index, answer in enumerate(data["answers"]):
        boxes.append((left + 50, y - 6, right - 50, y + 84))
        if index < shown:
            draw.text((left + 60, y), answer["text"][:78], font=theme.DOC_KEY, fill=theme.INK_SOFT)
            state = answer["answer"] if answer["answered"] else "not answered"
            draw.text((left + 60, y + 36), state[:74], font=theme.DOC_VALUE,
                      fill=theme.INK if answer["answered"] else theme.RED)
        y += 96

    y += 10
    draw.text((left + 60, y), "What was said about you", font=theme.KICKER, fill=accent)
    y += 56
    for key, value, colour in (
        ("said", ", ".join(data["disclosed"]) or "nothing", theme.INK),
        ("not needed", ", ".join(data["authorized_but_unused"]) or "nothing left over", theme.INK_SOFT),
        (
            "privacy check",
            "nothing outside your list was said" if not data["leaks"]
            else f"{len(data['leaks'])} finding(s): " + ", ".join(f"{f['kind']} ({f['masked']})" for f in data["leaks"]),
            theme.GREEN if not data["leaks"] else theme.RED,
        ),
    ):
        draw.text((left + 60, y), key, font=theme.DOC_KEY, fill=theme.INK_SOFT)
        draw.text((left + 340, y - 3), value[:70], font=theme.DOC_VALUE, fill=colour)
        y += 52

    return Panel(image=image, window=box, row_boxes=boxes)


def _wrap(draw: ImageDraw.ImageDraw, text: str, limit: float) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if current and draw.textlength(candidate, font=theme.BUBBLE) > limit:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    return lines


def bubbles(base: Image.Image, turns: list[dict], accent: tuple[int, int, int],
            visible: int | None = None, footer: str | None = None,
            title: str = "Transcript, verbatim") -> Panel:
    """A real transcript as chat bubbles.

    Speaker labels and the stamp come from the turn when it carries them, so a phone
    call transcript reads as "them" and a chat channel reads as whoever was typing,
    without either scene inventing a label the log does not support.
    """
    image = base.copy()
    draw = ImageDraw.Draw(image)
    inner = WIDTH - 2 * (theme.WINDOW_MARGIN + 120) - 112
    wrapped = [_wrap(draw, turn["text"], inner * 0.62) for turn in turns]
    heights = [54 + len(lines) * 40 for lines in wrapped]
    height = min(HEIGHT - 220, 170 + sum(heights) + 26 * (len(turns) - 1) + (120 if footer else 60))
    top = max(110, (HEIGHT - height) // 2)
    box = (theme.WINDOW_MARGIN + 120, top, WIDTH - theme.WINDOW_MARGIN - 120, top + height)
    draw = _card(image, box)
    left, top, right, bottom = box
    draw.text((left + 56, top + 40), title, font=theme.DOC_H1, fill=theme.INK)

    boxes: list[tuple[int, int, int, int]] = []
    shown = len(turns) if visible is None else visible
    y = top + 130
    for index, turn in enumerate(turns):
        assistant = turn["speaker"] == "bot"
        lines = wrapped[index]
        width = round(inner * 0.66)
        x = left + 56 if assistant else right - 56 - width
        bubble = (x, y, x + width, y + heights[index])
        boxes.append(bubble)
        if index < shown:
            draw.rounded_rectangle(bubble, radius=26, fill=(243, 246, 251) if assistant else theme.PANEL,
                                   outline=(226, 232, 242) if assistant else accent, width=3)
            who = turn.get("who") or ("assistant" if assistant else "them")
            stamp = turn.get("stamp") or f"{turn.get('offset_seconds') or 0:02d}s"
            draw.text((x + 28, y + 14), f"{who}  {stamp}", font=theme.BUBBLE_WHO,
                      fill=theme.INK_SOFT if assistant else accent)
            for row, line in enumerate(lines):
                draw.text((x + 28, y + 48 + row * 40), line, font=theme.BUBBLE, fill=theme.INK)
        y += heights[index] + 26
        if y > bottom - (100 if footer else 60):
            break
    while len(boxes) < len(turns):
        boxes.append(boxes[-1] if boxes else box)
    if footer is not None:
        draw.text((left + 56, bottom - 62), footer, font=theme.CHROME, fill=theme.INK_SOFT)
    return Panel(image=image, window=box, row_boxes=boxes)
