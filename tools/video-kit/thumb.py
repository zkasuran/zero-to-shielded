"""The upload thumbnail, drawn on the video's own theme.

A thumbnail is the first and often only thing a judge sees, and it has to survive being
shrunk to about 168 pixels wide in a sidebar. So it gets the project name, three or four
words of claim and at most one number, all on the same generated field the video uses.
Nothing is downloaded, which is the same reason `bg.py` exists: there is no image licence
to defend.

YouTube recommends 3840x2160 at 16:9 with a minimum width of 640, and the mobile upload
path caps a thumbnail at 2 MB, so this renders at 3840x2160 and the caller checks the size.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import bg
import theme

WIDTH, HEIGHT = 3840, 2160

# The video canvas is 2560x1440, so everything here is scaled by 1.5 from the numbers that
# were tuned by eye on the cards.
TITLE = ImageFont.truetype(theme.SANS_BOLD, 300)
CLAIM = ImageFont.truetype(theme.SANS_BOLD, 150)
BADGE = ImageFont.truetype(theme.MONO, 96)
FIGURE = ImageFont.truetype(theme.SANS_BOLD, 420)
FIGURE_LABEL = ImageFont.truetype(theme.SANS_BOLD, 96)

# The surfaces a submission actually gets asked for. A cover is not one shape: a Shorts
# cover is portrait, a feed post is square and the X Articles banner is 5:2, and cropping a
# 16:9 thumbnail into any of them loses the words. Each renders its own composition.
SIZES = {
    "youtube": (3840, 2160),
    "youtube-small": (1280, 720),
    "short": (1080, 1920),
    "square": (1080, 1080),
    "banner": (3000, 1200),
    "devpost": (1200, 800),
}

_BASE_TYPE = {"title": 300, "claim": 150, "badge": 96, "figure": 420, "figure_label": 96}


class geometry:
    """Rebind the module's size and fonts for one render, then put them back.

    Every layout reads WIDTH, HEIGHT and the module fonts, so rebinding those is what makes
    all of them work at any output size without a single layout body changing. Type scales
    with the SHORT edge rather than the width, so a portrait cover gets type sized for the
    frame it is in instead of type sized for a 3840 wide one.
    """

    def __init__(self, size):
        self.size = size

    def __enter__(self):
        global WIDTH, HEIGHT, TITLE, CLAIM, BADGE, FIGURE, FIGURE_LABEL
        self._previous = (WIDTH, HEIGHT, TITLE, CLAIM, BADGE, FIGURE, FIGURE_LABEL)
        WIDTH, HEIGHT = self.size
        scale = min(self.size) / 2160
        # a portrait or square cover has far less width per line, so the type comes down
        # again or a two word product name runs off the edge
        if self.size[0] < self.size[1]:
            scale *= 0.78
        elif self.size[0] < self.size[1] * 1.4:
            scale *= 0.86
        TITLE = theme.font(theme.SANS_BOLD, max(28, round(_BASE_TYPE["title"] * scale)))
        CLAIM = theme.font(theme.SANS_BOLD, max(18, round(_BASE_TYPE["claim"] * scale)))
        BADGE = theme.font(theme.MONO, max(14, round(_BASE_TYPE["badge"] * scale)))
        FIGURE = theme.font(theme.SANS_BOLD, max(32, round(_BASE_TYPE["figure"] * scale)))
        FIGURE_LABEL = theme.font(theme.SANS_BOLD, max(14, round(_BASE_TYPE["figure_label"] * scale)))
        return self

    def __exit__(self, *exc):
        global WIDTH, HEIGHT, TITLE, CLAIM, BADGE, FIGURE, FIGURE_LABEL
        WIDTH, HEIGHT, TITLE, CLAIM, BADGE, FIGURE, FIGURE_LABEL = self._previous
        return False


def _panel(size: tuple[int, int], radius: int, fill: tuple[int, int, int, int]) -> Image.Image:
    card = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=fill)
    return card


def _chip(canvas, at, text, font, accent, pad=(46, 26)):
    draw = ImageDraw.Draw(canvas)
    box = draw.textbbox((0, 0), text, font=font)
    card = _panel((box[2] + pad[0] * 2, box[3] + pad[1] * 2 + 10), 44, (*accent, 235))
    canvas.alpha_composite(card, at)
    ImageDraw.Draw(canvas).text(
        (at[0] + pad[0], at[1] + pad[1]), text, font=font, fill=(255, 255, 255, 255)
    )
    return card.height


def _shadowed(draw, at, text, font, fill, offset=(6, 8)):
    draw.text((at[0] + offset[0], at[1] + offset[1]), text, font=font, fill=(255, 255, 255, 130))
    draw.text(at, text, font=font, fill=fill)


def _wrap(draw, text, font, limit):
    """Greedy wrap, so a long project name does not run off the right edge."""
    words, lines, line = text.split(), [], ""
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= limit or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


# ---------------------------------------------------------------------------
# Layouts. One per demo, never shared, which is why they are named rather than
# parameterised: a layout is a composition rather than a setting. `preflight.py`
# fails a layout two projects both claim.
# ---------------------------------------------------------------------------

def _layout_gate(canvas, accent, name, claim, badge, figure):
    """A rule down the frame with the name held on its left. For a gate that stops a pipeline."""
    draw = ImageDraw.Draw(canvas)
    split = int(WIDTH * 0.60)
    draw.rectangle([split - 14, 0, split + 14, HEIGHT], fill=(*accent, 240))
    margin = 200
    y = margin + 30
    if badge:
        y += _chip(canvas, (margin, y), badge, BADGE, accent) + 80
    draw = ImageDraw.Draw(canvas)
    for line in _wrap(draw, name, TITLE, split - margin - 150):
        _shadowed(draw, (margin, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 24
    y += 40
    for line in claim:
        _shadowed(draw, (margin, y), line, CLAIM, accent, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 34
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        x = split + 130
        top = (HEIGHT - box[3] - lab[3] - 120) // 2
        _shadowed(draw, (x, top), value, FIGURE, theme.CARD_INK, (8, 10))
        for i, line in enumerate(_wrap(draw, label, FIGURE_LABEL, WIDTH - x - 160)):
            draw.text((x + 8, top + box[3] + 90 + i * 120), line, font=FIGURE_LABEL, fill=accent)


def _layout_roster(canvas, accent, name, claim, badge, figure):
    """Three stacked bars down the left, the way a party-by-option grid reads."""
    draw = ImageDraw.Draw(canvas)
    margin = 190
    bar_w, bar_h, gap = 470, 190, 54
    top = (HEIGHT - (bar_h * 3 + gap * 2)) // 2
    for i in range(3):
        fill = (*accent, 245) if i == 1 else (255, 255, 255, 225)
        canvas.alpha_composite(_panel((bar_w, bar_h), 46, fill), (margin, top + i * (bar_h + gap)))
    draw = ImageDraw.Draw(canvas)
    x = margin + bar_w + 150
    y = margin + 60
    if badge:
        y += _chip(canvas, (x, y), badge, BADGE, accent) + 76
    draw = ImageDraw.Draw(canvas)
    for line in _wrap(draw, name, TITLE, WIDTH - x - margin):
        _shadowed(draw, (x, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 24
    y += 46
    for line in claim:
        _shadowed(draw, (x, y), line, CLAIM, accent, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 34
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        # From the bottom edge up, so a name that wraps to three lines cannot push
        # the number off the frame. That is what it did the first time it was drawn.
        base = HEIGHT - margin - lab[3]
        _shadowed(draw, (WIDTH - margin - box[2], base - box[3] - 40), value, FIGURE, accent, (6, 8))
        draw.text((WIDTH - margin - lab[2], base), label, font=FIGURE_LABEL, fill=theme.CARD_SOFT)


def _layout_bubble(canvas, accent, name, claim, badge, figure):
    """One wide card with a spoken tail, for an app whose output is what was said."""
    margin = 200
    card_w = WIDTH - margin * 2
    card_h = 1180
    top = (HEIGHT - card_h) // 2 - 60
    canvas.alpha_composite(_panel((card_w, card_h), 120, (255, 255, 255, 238)), (margin, top))
    tail = Image.new("RGBA", (300, 240), (0, 0, 0, 0))
    ImageDraw.Draw(tail).polygon([(0, 0), (300, 0), (90, 240)], fill=(255, 255, 255, 238))
    canvas.alpha_composite(tail, (margin + 300, top + card_h - 2))
    draw = ImageDraw.Draw(canvas)
    x, y = margin + 130, top + 110
    if badge:
        y += _chip(canvas, (x, y), badge, BADGE, accent) + 60
    draw = ImageDraw.Draw(canvas)
    for line in _wrap(draw, name, TITLE, card_w - 260):
        draw.text((x, y), line, font=TITLE, fill=theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 22
    y += 40
    for line in claim:
        draw.text((x, y), line, font=CLAIM, fill=accent)
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 30
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        base = HEIGHT - 120 - lab[3]
        at = (WIDTH - margin - max(box[2], lab[2]) - 40, base - box[3] - 30)
        _shadowed(draw, at, value, FIGURE, theme.CARD_INK, (8, 10))
        draw.text((at[0] + 8, base), label, font=FIGURE_LABEL, fill=accent)


def _layout_stamp(canvas, accent, name, claim, badge, figure):
    """Centred name under a round stamp, for a verdict an institution either gives or does not."""
    draw = ImageDraw.Draw(canvas)
    r = 380
    cx, cy = WIDTH - 520, 560
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*accent, 255), width=34)
    draw.ellipse([cx - r + 70, cy - r + 70, cx + r - 70, cy + r - 70], fill=(*accent, 228))
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=CLAIM)
        draw.text((cx - box[2] / 2, cy - box[3] / 2 - 20), value, font=CLAIM, fill=(255, 255, 255))
        # Under the ring rather than inside it. Inside, anything longer than one
        # word runs straight out of the circle and off the right edge.
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        # Centred under the ring, then pulled back inside the right margin, because
        # the ring sits close to the edge and a label wider than it overhangs.
        lx = min(cx - lab[2] / 2, WIDTH - 210 - lab[2])
        draw.text((lx, cy + r + 50), label, font=FIGURE_LABEL, fill=accent)
    margin = 210
    if badge:
        _chip(canvas, (margin, margin + 40), badge, BADGE, accent)
    draw = ImageDraw.Draw(canvas)
    title_lines = _wrap(draw, name, TITLE, WIDTH - margin * 2 - 900)
    title_h = sum(draw.textbbox((0, 0), l, font=TITLE)[3] + 26 for l in title_lines)
    claim_h = sum(draw.textbbox((0, 0), l, font=CLAIM)[3] + 32 for l in claim)
    # Measured from the bottom up, because the block's height depends on how the
    # name wraps and a fixed top left the last claim line under the frame edge.
    y = HEIGHT - margin - claim_h - 90 - 18 - 46 - title_h
    for line in title_lines:
        _shadowed(draw, (margin, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 26
    y += 46
    draw.rectangle([margin, y, margin + 620, y + 18], fill=(*accent, 245))
    y += 90 + 18
    for line in claim:
        _shadowed(draw, (margin, y), line, CLAIM, accent, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 32


def _layout_wave(canvas, accent, name, claim, badge, figure):
    """A rendered waveform band across the middle, for the app that turns a script into audio."""
    import math

    draw = ImageDraw.Draw(canvas)
    band_top, band_h = round(HEIGHT * 900 / 2160), round(HEIGHT * 460 / 2160)
    canvas.alpha_composite(
        _panel((WIDTH, band_h), 0, (255, 255, 255, 210)), (0, band_top)
    )
    draw = ImageDraw.Draw(canvas)
    mid = band_top + band_h // 2
    # bar count scales with width so a narrow cover does not drive bar_w negative. At the
    # original 3840 canvas this is 64 bars at gap 18, unchanged.
    gap = round(18 * WIDTH / 3840)
    bars = max(12, round(64 * WIDTH / 3840))
    bar_w = (WIDTH - gap * (bars + 1)) // bars
    for i in range(bars):
        # Deterministic, so the same project always draws the same wave.
        h = int((0.22 + 0.78 * abs(math.sin(i * 0.7) * math.cos(i * 0.23))) * (band_h * 0.40))
        x = gap + i * (bar_w + gap)
        draw.rounded_rectangle([x, mid - h, x + bar_w, mid + h], bar_w // 2, fill=(*accent, 235))
    margin = 210
    y = margin + 30
    if badge:
        y += _chip(canvas, (margin, y), badge, BADGE, accent) + 70
    draw = ImageDraw.Draw(canvas)
    for line in _wrap(draw, name, TITLE, WIDTH - margin * 2):
        _shadowed(draw, (margin, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 24
    y = band_top + band_h + 90
    for line in claim:
        _shadowed(draw, (margin, y), line, CLAIM, theme.CARD_INK, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 30
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        at = (WIDTH - margin - box[2] - 30, band_top + band_h + 40)
        _shadowed(draw, at, value, FIGURE, accent, (8, 10))
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        draw.text((WIDTH - margin - lab[2], at[1] + box[3] + 80),
                  label, font=FIGURE_LABEL, fill=theme.CARD_SOFT)


def _layout_tape(canvas, accent, name, claim, badge, figure):
    """A ticker tape rule under the name, for a product whose whole claim is that
    the numbers on the tape are the ones anybody can recompute.

    Built for Mandate: the figure sits on the rule rather than beside the title,
    because the number IS the claim here and a number floating in white space
    stops reading at sidebar width.
    """
    draw = ImageDraw.Draw(canvas)
    margin = 210

    if badge:
        _chip(canvas, (margin, margin + 40), badge, BADGE, accent)
        draw = ImageDraw.Draw(canvas)

    title_lines = _wrap(draw, name, TITLE, WIDTH - margin * 2)
    y = margin + 250
    for line in title_lines:
        _shadowed(draw, (margin, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 26

    # The tape: a full-width band carrying the one number, with tick marks
    # running off both edges so it reads as a strip rather than a box.
    y += 60
    band_h = 190
    draw.rectangle([0, y, WIDTH, y + band_h], fill=(*accent, 240))
    for x in range(0, WIDTH, 52):
        draw.rectangle([x, y, x + 5, y + 22], fill=(255, 255, 255, 90))
        draw.rectangle([x, y + band_h - 22, x + 5, y + band_h], fill=(255, 255, 255, 90))

    if figure:
        value, label = figure
        vb = draw.textbbox((0, 0), value, font=CLAIM)
        draw.text((margin, y + (band_h - vb[3]) / 2 - 8), value, font=CLAIM,
                  fill=(255, 255, 255))
        lb = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        draw.text((margin + vb[2] + 46, y + (band_h - lb[3]) / 2 + 6), label,
                  font=FIGURE_LABEL, fill=(255, 255, 255, 220))

    y += band_h + 76
    for line in claim:
        _shadowed(draw, (margin, y), line, CLAIM, accent, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 32


def _layout_merge(canvas, accent, name, claim, badge, figure):
    """Two branches entering from the left that join into one rule running off the
    right edge, with the number sitting in the node where they meet.

    Built for the KeeperHub bounty cut, where the whole claim is that separate
    branches were made mergeable rather than described as mergeable. The junction is
    the subject, so it is the only filled shape on the frame and it holds the count.
    """
    draw = ImageDraw.Draw(canvas)
    margin = 210

    if badge:
        _chip(canvas, (margin, margin - 60), badge, BADGE, accent)
        draw = ImageDraw.Draw(canvas)

    title_lines = _wrap(draw, name, TITLE, WIDTH - margin * 2)
    y = margin + 150
    for line in title_lines:
        _shadowed(draw, (margin, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 24

    y += 30
    for line in claim:
        _shadowed(draw, (margin, y), line, CLAIM, accent, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 30

    # The junction, in the lower third so the frame is not top heavy. Two branches
    # come in from the left edge at different heights and meet at a node, then one
    # thick rule leaves it for the right edge.
    node_x, node_y = int(WIDTH * 0.72), HEIGHT - 560
    radius = 200
    elbow = node_x - radius - 300
    for offset in (-300, 300):
        draw.line([(0, node_y + offset), (elbow, node_y + offset)], fill=(*accent, 205), width=26)
        draw.line([(elbow, node_y + offset), (node_x - radius + 20, node_y)],
                  fill=(*accent, 205), width=26)
    draw.line([(node_x + radius - 20, node_y), (WIDTH, node_y)], fill=(*accent, 240), width=54)
    draw.ellipse([node_x - radius, node_y - radius, node_x + radius, node_y + radius],
                 fill=(*accent, 245))

    if figure:
        value, label = figure
        vb = draw.textbbox((0, 0), value, font=FIGURE)
        draw.text((node_x - vb[2] / 2, node_y - vb[3] / 2 - 40), value, font=FIGURE,
                  fill=(255, 255, 255))
        lb = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        _shadowed(draw, (max(margin, node_x - radius - 80 - lb[2]), node_y - lb[3] / 2 - 10),
                  label, FIGURE_LABEL, accent, (4, 5))


def _layout_ledger(canvas, accent, name, claim, badge, figure):
    """The number is the whole point. One huge figure, the name small above it.

    For a benchmark or a measured result, where the figure is the reason to click.
    """
    draw = ImageDraw.Draw(canvas)
    margin = round(WIDTH * 0.055)
    draw.rectangle([margin, round(HEIGHT * 0.16), margin + round(WIDTH * 0.006), round(HEIGHT * 0.84)],
                   fill=(*accent, 240))
    x = margin + round(WIDTH * 0.035)
    y = round(HEIGHT * 0.18)
    for line in _wrap(draw, name, CLAIM, WIDTH - x - margin):
        draw.text((x, y), line, font=CLAIM, fill=theme.CARD_SOFT)
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + round(HEIGHT * 0.012)
    if figure:
        value, label = figure
        y += round(HEIGHT * 0.02)
        _shadowed(draw, (x, y), value, FIGURE, accent, (8, 10))
        y += draw.textbbox((0, 0), value, font=FIGURE)[3] + round(HEIGHT * 0.03)
        for line in _wrap(draw, label, FIGURE_LABEL, WIDTH - x - margin):
            draw.text((x, y), line, font=FIGURE_LABEL, fill=theme.CARD_INK)
            y += draw.textbbox((0, 0), line, font=FIGURE_LABEL)[3] + 20
    for line in claim[:1]:
        draw.text((x, HEIGHT - margin - draw.textbbox((0, 0), line, font=CLAIM)[3]),
                  line, font=CLAIM, fill=theme.CARD_SOFT)


def _layout_beam(canvas, accent, name, claim, badge, figure):
    """A wide accent beam across the middle with the name reversed out of it."""
    draw = ImageDraw.Draw(canvas)
    margin = round(WIDTH * 0.055)
    title_lines = _wrap(draw, name, TITLE, WIDTH - margin * 2)
    band_h = sum(draw.textbbox((0, 0), line, font=TITLE)[3] + 24 for line in title_lines) + round(HEIGHT * 0.09)
    top = (HEIGHT - band_h) // 2
    draw.rectangle([0, top, WIDTH, top + band_h], fill=(*accent, 245))
    y = top + round(HEIGHT * 0.045)
    for line in title_lines:
        draw.text((margin, y), line, font=TITLE, fill=(255, 255, 255, 255))
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 24
    y = top + band_h + round(HEIGHT * 0.04)
    for line in claim[:2]:
        draw.text((margin, y), line, font=CLAIM, fill=theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 20
    if badge:
        _chip(canvas, (margin, top - round(HEIGHT * 0.09)), badge, BADGE, accent)
    if figure:
        value, _ = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        _shadowed(draw, (WIDTH - margin - box[2], HEIGHT - margin - box[3]), value, FIGURE, accent, (6, 8))


def _layout_corner(canvas, accent, name, claim, badge, figure):
    """Mostly field, with the words in one corner. Reads as calm and deliberate."""
    draw = ImageDraw.Draw(canvas)
    margin = round(WIDTH * 0.07)
    block = _panel((round(WIDTH * 0.52), round(HEIGHT * 0.46)), round(WIDTH * 0.02), (255, 255, 255, 236))
    at = (margin, HEIGHT - margin - block.height)
    canvas.alpha_composite(block, at)
    draw = ImageDraw.Draw(canvas)
    x, y = at[0] + round(WIDTH * 0.03), at[1] + round(HEIGHT * 0.05)
    for line in _wrap(draw, name, TITLE, block.width - round(WIDTH * 0.06)):
        draw.text((x, y), line, font=TITLE, fill=theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 18
    y += round(HEIGHT * 0.015)
    for line in claim[:2]:
        draw.text((x, y), line, font=CLAIM, fill=accent)
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 16
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        _shadowed(draw, (WIDTH - margin - box[2], margin), value, FIGURE, accent, (8, 10))
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        draw.text((WIDTH - margin - lab[2], margin + box[3] + 30), label,
                  font=FIGURE_LABEL, fill=theme.CARD_INK)
    if badge:
        _chip(canvas, (margin, margin), badge, BADGE, accent)


def _layout_rule(canvas, accent, name, claim, badge, figure):
    """A thin rule under a left-aligned title, editorial rather than promotional."""
    draw = ImageDraw.Draw(canvas)
    margin = round(WIDTH * 0.08)
    y = round(HEIGHT * 0.26)
    if badge:
        _chip(canvas, (margin, y - round(HEIGHT * 0.11)), badge, BADGE, accent)
        draw = ImageDraw.Draw(canvas)
    for line in _wrap(draw, name, TITLE, WIDTH - margin * 2):
        draw.text((margin, y), line, font=TITLE, fill=theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 20
    y += round(HEIGHT * 0.025)
    draw.rectangle([margin, y, WIDTH - margin, y + max(4, round(HEIGHT * 0.005))], fill=(*accent, 240))
    y += round(HEIGHT * 0.05)
    for line in claim[:2]:
        draw.text((margin, y), line, font=CLAIM, fill=theme.CARD_SOFT)
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 18
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        base = HEIGHT - round(HEIGHT * 0.09) - box[3]
        _shadowed(draw, (margin, base), value, FIGURE, accent, (6, 8))
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        draw.text((margin + box[2] + 40, base + box[3] - lab[3] - 10), label,
                  font=FIGURE_LABEL, fill=theme.CARD_SOFT)


def _layout_shield(canvas, accent, name, claim, badge, figure):
    """A bold refusal motif: an accent block with a slash, for a guard or a check story."""
    draw = ImageDraw.Draw(canvas)
    margin = round(WIDTH * 0.06)
    size = round(min(WIDTH, HEIGHT) * 0.3)
    cx, cy = WIDTH - margin - size // 2, HEIGHT // 2
    draw.ellipse([cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2],
                 outline=(*accent, 245), width=max(6, round(size * 0.07)))
    offset = int(size * 0.33)
    draw.line([(cx - offset, cy + offset), (cx + offset, cy - offset)],
              fill=(*accent, 245), width=max(6, round(size * 0.07)))
    y = round(HEIGHT * 0.26)
    limit = WIDTH - margin * 2 - size - round(WIDTH * 0.04)
    for line in _wrap(draw, name, TITLE, limit):
        draw.text((margin, y), line, font=TITLE, fill=theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 18
    y += round(HEIGHT * 0.02)
    for line in claim[:2]:
        draw.text((margin, y), line, font=CLAIM, fill=accent)
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 16
    if badge:
        _chip(canvas, (margin, round(HEIGHT * 0.12)), badge, BADGE, accent)
    if figure:
        value, label = figure
        draw = ImageDraw.Draw(canvas)
        box = draw.textbbox((0, 0), value, font=FIGURE_LABEL)
        draw.text((margin, HEIGHT - round(HEIGHT * 0.1) - box[3]),
                  f"{value}  {label}", font=FIGURE_LABEL, fill=theme.CARD_SOFT)


def _layout_column(canvas, accent, name, claim, badge, figure):
    """A tall left column of accent with the title stacked beside it. Suits a portrait cover."""
    draw = ImageDraw.Draw(canvas)
    margin = round(WIDTH * 0.06)
    col_w = round(WIDTH * 0.1)
    draw.rectangle([0, 0, col_w, HEIGHT], fill=(*accent, 242))
    x = col_w + round(WIDTH * 0.05)
    y = round(HEIGHT * 0.2)
    if badge:
        _chip(canvas, (x, y - round(HEIGHT * 0.1)), badge, BADGE, accent)
        draw = ImageDraw.Draw(canvas)
    for line in _wrap(draw, name, TITLE, WIDTH - x - margin):
        _shadowed(draw, (x, y), line, TITLE, theme.CARD_INK, (5, 6))
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + 20
    y += round(HEIGHT * 0.02)
    for line in claim[:2]:
        draw.text((x, y), line, font=CLAIM, fill=accent)
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 18
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        base = HEIGHT - round(HEIGHT * 0.12) - box[3]
        _shadowed(draw, (x, base), value, FIGURE, accent, (8, 10))
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        draw.text((x, base + box[3] + 24), label, font=FIGURE_LABEL, fill=theme.CARD_SOFT)


def _layout_strike(canvas, accent, name, claim, badge, figure):
    """Two stacked claim bars: the upper one struck through, the lower one accent filled.

    Built for Still True, where the whole product is that one answer replaced another. The
    struck bar is the stale claim a plain model still repeats, the filled bar is the current
    one the grounded agent gives. Reads as a contradiction resolved even at sidebar width.
    """
    draw = ImageDraw.Draw(canvas)
    margin = round(WIDTH * 0.06)
    y = margin + round(HEIGHT * 0.02)
    if badge:
        y += _chip(canvas, (margin, y), badge, BADGE, accent) + round(HEIGHT * 0.03)
    draw = ImageDraw.Draw(canvas)
    for line in _wrap(draw, name, TITLE, WIDTH - margin * 2):
        _shadowed(draw, (margin, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + round(HEIGHT * 0.012)
    y += round(HEIGHT * 0.01)
    for line in claim[:1]:
        _shadowed(draw, (margin, y), line, CLAIM, accent, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + round(HEIGHT * 0.03)

    # The two bars, in the lower two thirds so the name sits above them.
    bar_w = WIDTH - margin * 2
    bar_h = round(HEIGHT * 0.19)
    gap = round(HEIGHT * 0.05)
    top = max(y + round(HEIGHT * 0.02), HEIGHT - margin - bar_h * 2 - gap)
    # Upper: the stale claim, a pale card with a strike ruled through it.
    canvas.alpha_composite(_panel((bar_w, bar_h), round(WIDTH * 0.02), (255, 255, 255, 224)), (margin, top))
    draw = ImageDraw.Draw(canvas)
    mid = top + bar_h // 2
    draw.line([(margin + round(WIDTH * 0.02), mid), (margin + bar_w - round(WIDTH * 0.02), mid)],
              fill=(*accent, 235), width=max(6, round(HEIGHT * 0.008)))
    draw.text((margin + round(WIDTH * 0.03), top + round(bar_h * 0.16)), "was", font=FIGURE_LABEL,
              fill=theme.CARD_SOFT)
    # Lower: the current claim, the one filled shape on the frame.
    low = top + bar_h + gap
    canvas.alpha_composite(_panel((bar_w, bar_h), round(WIDTH * 0.02), (*accent, 245)), (margin, low))
    draw = ImageDraw.Draw(canvas)
    tick = round(bar_h * 0.30)
    tx, ty = margin + round(WIDTH * 0.035), low + bar_h // 2
    draw.line([(tx, ty), (tx + tick * 0.5, ty + tick * 0.55), (tx + tick * 1.4, ty - tick * 0.7)],
              fill=(255, 255, 255, 255), width=max(8, round(HEIGHT * 0.011)), joint="curve")
    draw.text((tx + tick * 2, low + round(bar_h * 0.16)), "now", font=FIGURE_LABEL,
              fill=(255, 255, 255, 235))
    if figure:
        value, label = figure
        vb = draw.textbbox((0, 0), value, font=FIGURE)
        vx = WIDTH - margin - vb[2] - round(WIDTH * 0.04)
        _shadowed(draw, (vx, low + (bar_h - vb[3]) // 2 - round(HEIGHT * 0.02)),
                  value, FIGURE, (255, 255, 255), (6, 8))
        lb = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        draw.text((vx - lb[2] - round(WIDTH * 0.02), low + (bar_h - lb[3]) // 2),
                  label, font=FIGURE_LABEL, fill=(255, 255, 255, 235))


def _layout_graph(canvas, accent, name, claim, badge, figure):
    """A small node-link cluster with typed edges, name and claim on its left.

    Built for Still True Path Two, a knowledge base whose whole idea is that the links
    between facts carry meaning. One amber contradiction edge, one blue dashed
    supersession and one green support run from a centre node to three others, the same
    three relation colours the app's own legend uses. Reads as a graph that argues with
    itself even at sidebar width, and no other layout draws a graph.
    """
    import math

    draw = ImageDraw.Draw(canvas)
    contra = (245, 176, 32)   # amber, a contradiction
    supersede = (46, 158, 235)  # blue, one fact replacing another
    support = (36, 176, 132)  # green, agreement

    short = min(WIDTH, HEIGHT)
    cx, cy = int(WIDTH * 0.74), HEIGHT // 2
    ring = round(short * 0.27)
    node_r = max(10, round(short * 0.034))
    edge_w = max(6, round(short * 0.012))
    centre = (cx, cy)
    outer = [
        (cx + int(ring * math.cos(a)), cy + int(ring * math.sin(a)))
        for a in (-math.pi / 2, math.pi / 6, math.pi * 5 / 6)
    ]
    for (ox, oy), colour, dashed in (
        (outer[0], contra, False),
        (outer[1], supersede, True),
        (outer[2], support, False),
    ):
        if dashed:
            steps = 28
            for i in range(steps):
                if i % 2:
                    continue
                t0, t1 = i / steps, (i + 1) / steps
                x0 = centre[0] + (ox - centre[0]) * t0
                y0 = centre[1] + (oy - centre[1]) * t0
                x1 = centre[0] + (ox - centre[0]) * t1
                y1 = centre[1] + (oy - centre[1]) * t1
                draw.line([(x0, y0), (x1, y1)], fill=(*colour, 255), width=edge_w)
        else:
            draw.line([centre, (ox, oy)], fill=(*colour, 255), width=edge_w)
    for (ox, oy) in outer:
        draw.ellipse([ox - node_r, oy - node_r, ox + node_r, oy + node_r], fill=(*theme.CARD_INK, 255))
    big = round(node_r * 1.5)
    draw.ellipse([cx - big, cy - big, cx + big, cy + big], fill=(*accent, 255),
                 outline=(255, 255, 255, 255), width=max(3, edge_w // 2))

    margin = round(WIDTH * 0.06)
    limit = int(WIDTH * 0.52)
    if badge:
        _chip(canvas, (margin, round(HEIGHT * 0.13)), badge, BADGE, accent)
        draw = ImageDraw.Draw(canvas)
    y = round(HEIGHT * 0.26)
    for line in _wrap(draw, name, TITLE, limit):
        _shadowed(draw, (margin, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + round(HEIGHT * 0.012)
    y += round(HEIGHT * 0.02)
    for line in claim[:2]:
        _shadowed(draw, (margin, y), line, CLAIM, accent, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + round(HEIGHT * 0.02)
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        base = HEIGHT - round(HEIGHT * 0.1) - box[3]
        _shadowed(draw, (margin, base), value, FIGURE, accent, (6, 8))
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        draw.text((margin + box[2] + 40, base + box[3] - lab[3] - 10), label,
                  font=FIGURE_LABEL, fill=theme.CARD_SOFT)


def _layout_beacon(canvas, accent, name, claim, badge, figure):
    """A hub with verified tokens wired into it and one clone cut off, for an authenticity story.

    Built for Steward. A filled accent hub is the shared bStocks beacon. Four dark token nodes
    wire into it with solid lines, the genuine tokens that resolve to the beacon. One node sits
    apart, drawn as an outline ring with a cross, its link struck through: the scam clone the
    same check rejects. Reads as authenticity resolved by a beacon even at sidebar width, and
    no other layout draws a hub with one severed spoke.
    """
    import math

    draw = ImageDraw.Draw(canvas)
    short = min(WIDTH, HEIGHT)
    cx, cy = int(WIDTH * 0.76), int(HEIGHT * 0.44)
    ring = round(short * 0.28)
    hub_r = max(16, round(short * 0.072))
    node_r = max(9, round(short * 0.03))
    edge_w = max(5, round(short * 0.011))

    # Four genuine spokes over the upper and left arc, wired in with solid lines.
    genuine = [-math.pi * 0.92, -math.pi * 0.62, -math.pi * 0.32, math.pi * 0.72]
    for a in genuine:
        ox, oy = cx + int(ring * math.cos(a)), cy + int(ring * math.sin(a))
        draw.line([(cx, cy), (ox, oy)], fill=(*accent, 220), width=edge_w)
        draw.ellipse([ox - node_r, oy - node_r, ox + node_r, oy + node_r], fill=(*theme.CARD_INK, 255))
    # The clone: a severed spoke lower right, an outline ring with a cross, no wire to the hub.
    sx, sy = cx + int(ring * 1.02 * math.cos(math.pi * 0.28)), cy + int(ring * 1.02 * math.sin(math.pi * 0.28))
    mx, my = (cx + sx) // 2, (cy + sy) // 2
    for t0, t1 in ((0.08, 0.34), (0.66, 0.92)):
        draw.line([(cx + (sx - cx) * t0, cy + (sy - cy) * t0), (cx + (sx - cx) * t1, cy + (sy - cy) * t1)],
                  fill=(*theme.CARD_SOFT, 150), width=max(4, edge_w - 3))
    cut = round(node_r * 0.7)
    draw.line([(mx - cut, my - cut), (mx + cut, my + cut)], fill=(*accent, 235), width=edge_w)
    draw.line([(mx - cut, my + cut), (mx + cut, my - cut)], fill=(*accent, 235), width=edge_w)
    draw.ellipse([sx - node_r, sy - node_r, sx + node_r, sy + node_r], outline=(*theme.CARD_SOFT, 235),
                 width=max(4, edge_w - 2))
    draw.line([(sx - node_r * 0.6, sy - node_r * 0.6), (sx + node_r * 0.6, sy + node_r * 0.6)],
              fill=(*theme.CARD_SOFT, 235), width=max(4, edge_w - 2))
    draw.line([(sx - node_r * 0.6, sy + node_r * 0.6), (sx + node_r * 0.6, sy - node_r * 0.6)],
              fill=(*theme.CARD_SOFT, 235), width=max(4, edge_w - 2))
    # The hub, the one filled focal shape, drawn last so the spokes tuck under it.
    draw.ellipse([cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r], fill=(*accent, 245),
                 outline=(255, 255, 255, 255), width=max(3, edge_w // 2))

    margin = round(WIDTH * 0.06)
    limit = int(WIDTH * 0.47)
    y = round(HEIGHT * 0.24)
    if badge:
        _chip(canvas, (margin, y - round(HEIGHT * 0.12)), badge, BADGE, accent)
        draw = ImageDraw.Draw(canvas)
    for line in _wrap(draw, name, TITLE, limit):
        _shadowed(draw, (margin, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + round(HEIGHT * 0.012)
    y += round(HEIGHT * 0.02)
    for line in claim[:2]:
        _shadowed(draw, (margin, y), line, CLAIM, accent, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + round(HEIGHT * 0.02)
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        base = HEIGHT - round(HEIGHT * 0.1) - box[3]
        _shadowed(draw, (margin, base), value, FIGURE, accent, (6, 8))
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        _shadowed(draw, (margin + box[2] + 40, base + box[3] - lab[3] - 10), label,
                  FIGURE_LABEL, theme.CARD_INK, (3, 4))


def _layout_ladder(canvas, accent, name, claim, badge, figure):
    """A ranked route ladder on the right, the cheapest executable venue filled as the winner
    and the gated venues drawn as struck outlines, for a best-execution product.

    Built for OpenTape. Four venue bars stacked and ranked: one accent-filled bar with a white
    knob is the route you can actually reach, one dark bar is another open venue, and two
    outline bars carry a diagonal strike, the gated issuer legs the engine shows but will not
    offer. Reads as one book ranked with the reachable route chosen even at sidebar width, and
    no other layout draws a ranked ladder with gated rows. `tape` is Mandate's ticker strip.
    """
    draw = ImageDraw.Draw(canvas)
    short = min(WIDTH, HEIGHT)
    lx = int(WIDTH * 0.60)
    span = int(WIDTH * 0.33)
    rows = 4
    gap = round(short * 0.05)
    bar_h = round(short * 0.115)
    total = rows * bar_h + (rows - 1) * gap
    top = (HEIGHT - total) // 2
    radius = round(bar_h * 0.3)
    stroke = max(4, round(short * 0.006))
    widths = [0.70, 1.0, 0.88, 0.62]
    best = 1
    gated = {2, 3}
    for i in range(rows):
        y0 = top + i * (bar_h + gap)
        x1 = lx + int(span * widths[i])
        if i == best:
            draw.rounded_rectangle([lx, y0, x1, y0 + bar_h], radius, fill=(*accent, 245),
                                   outline=(255, 255, 255, 255), width=max(3, stroke - 2))
            knob = round(bar_h * 0.24)
            kx, ky = lx + round(bar_h * 0.5), y0 + bar_h // 2
            draw.ellipse([kx - knob, ky - knob, kx + knob, ky + knob], fill=(255, 255, 255, 255))
        elif i in gated:
            draw.rounded_rectangle([lx, y0, x1, y0 + bar_h], radius, outline=(*theme.CARD_SOFT, 235),
                                   width=stroke)
            for t0, t1 in ((0.10, 0.30), (0.70, 0.90)):
                sx0 = lx + int((x1 - lx) * t0)
                sx1 = lx + int((x1 - lx) * t1)
                draw.line([(sx0, y0 + bar_h * 0.78), (sx1, y0 + bar_h * 0.22)],
                          fill=(*theme.CARD_SOFT, 220), width=max(3, stroke - 2))
        else:
            draw.rounded_rectangle([lx, y0, x1, y0 + bar_h], radius, fill=(*theme.CARD_INK, 235))

    margin = round(WIDTH * 0.06)
    limit = int(WIDTH * 0.48)
    y = round(HEIGHT * 0.24)
    if badge:
        _chip(canvas, (margin, y - round(HEIGHT * 0.12)), badge, BADGE, accent)
        draw = ImageDraw.Draw(canvas)
    for line in _wrap(draw, name, TITLE, limit):
        _shadowed(draw, (margin, y), line, TITLE, theme.CARD_INK)
        y += draw.textbbox((0, 0), line, font=TITLE)[3] + round(HEIGHT * 0.012)
    y += round(HEIGHT * 0.02)
    for line in claim[:2]:
        _shadowed(draw, (margin, y), line, CLAIM, accent, (4, 5))
        y += draw.textbbox((0, 0), line, font=CLAIM)[3] + round(HEIGHT * 0.02)
    if figure:
        value, label = figure
        box = draw.textbbox((0, 0), value, font=FIGURE)
        base = HEIGHT - round(HEIGHT * 0.1) - box[3]
        _shadowed(draw, (margin, base), value, FIGURE, accent, (6, 8))
        lab = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
        _shadowed(draw, (margin + box[2] + 40, base + box[3] - lab[3] - 10), label,
                  FIGURE_LABEL, theme.CARD_INK, (3, 4))


LAYOUTS = {
    "stack": None,  # the original, held by every demo built before 2026-09-08
    "gate": _layout_gate,
    "roster": _layout_roster,
    "bubble": _layout_bubble,
    "stamp": _layout_stamp,
    "wave": _layout_wave,
    "tape": _layout_tape,
    "merge": _layout_merge,
    # Added 2026-09-22. Each is a different composition rather than the same one recoloured,
    # and each is written against WIDTH and HEIGHT so it renders at any surface size.
    "ledger": _layout_ledger,
    "beam": _layout_beam,
    "corner": _layout_corner,
    "rule": _layout_rule,
    "shield": _layout_shield,
    "column": _layout_column,
    # Added 2026-09-24 for Still True: a contradiction resolved, one claim struck and
    # one filled, which no other layout draws.
    "strike": _layout_strike,
    # Added 2026-09-24 for Still True Path Two: a typed node-link cluster, amber
    # contradiction, blue dashed supersession, green support, which no other layout draws.
    "graph": _layout_graph,
    # Added 2026-09-24 for Steward: a beacon hub with genuine tokens wired in and one clone
    # cut off, an authenticity motif no other layout draws.
    "beacon": _layout_beacon,
    # Added 2026-09-24 for OpenTape: a ranked route ladder, the cheapest executable venue
    # filled as the winner and the gated venues drawn as struck outlines, a best-execution
    # motif no other layout draws (`tape` is Mandate's ticker strip, a different shape).
    "ladder": _layout_ladder,
}


def render(
    palette: str,
    name: str,
    claim: list[str],
    badge: str | None = None,
    figure: tuple[str, str] | None = None,
    layout: str = "stack",
    size: tuple[int, int] | str | None = None,
) -> Image.Image:
    """One thumbnail. `claim` is at most two short lines, `figure` is one number and its label.

    `size` picks the surface: a (w, h) pair, or a name from SIZES. It defaults to YouTube's
    3840x2160, so an existing caller renders exactly what it always did.
    """
    if len(claim) > 2:
        raise ValueError("a thumbnail reads at 168px wide, so it gets at most two claim lines")
    if layout not in LAYOUTS:
        raise ValueError(f"unknown thumbnail layout {layout!r}, have {sorted(LAYOUTS)}")
    if isinstance(size, str):
        if size not in SIZES:
            raise ValueError(f"unknown size {size!r}, have {sorted(SIZES)}")
        size = SIZES[size]
    target = tuple(size) if size else (3840, 2160)

    with geometry(target):
        field = bg.background(palette).resize((WIDTH, HEIGHT), Image.LANCZOS)
        canvas = field.convert("RGBA")
        accent = theme.palette(palette)["accent"]

        if layout != "stack":
            LAYOUTS[layout](canvas, accent, name, claim, badge, figure)
            return canvas.convert("RGB")

        draw = ImageDraw.Draw(canvas)
        margin = round(210 * min(WIDTH, HEIGHT) / 2160)
        y = margin + round(40 * min(WIDTH, HEIGHT) / 2160)

        if badge:
            pad_x, pad_y = 46, 26
            box = draw.textbbox((0, 0), badge, font=BADGE)
            chip = _panel((box[2] + pad_x * 2, box[3] + pad_y * 2 + 10), 44, (*accent, 235))
            canvas.alpha_composite(chip, (margin, y))
            ImageDraw.Draw(canvas).text(
                (margin + pad_x, y + pad_y), badge, font=BADGE, fill=(255, 255, 255, 255)
            )
            y += chip.height + 90

        draw = ImageDraw.Draw(canvas)
        for line in _wrap(draw, name, TITLE, WIDTH - margin * 2):
            draw.text((margin + 6, y + 8), line, font=TITLE, fill=(255, 255, 255, 130))
            draw.text((margin, y), line, font=TITLE, fill=theme.CARD_INK)
            y += draw.textbbox((0, 0), line, font=TITLE)[3] + 70

        for line in claim:
            draw.text((margin + 4, y + 5), line, font=CLAIM, fill=(255, 255, 255, 120))
            draw.text((margin, y), line, font=CLAIM, fill=accent)
            y += draw.textbbox((0, 0), line, font=CLAIM)[3] + 34

        if figure:
            value, label = figure
            box = draw.textbbox((0, 0), value, font=FIGURE)
            label_box = draw.textbbox((0, 0), label, font=FIGURE_LABEL)
            width = max(box[2], label_box[2]) + 180
            card = _panel((width, box[3] + label_box[3] + 250), 72, (255, 255, 255, 232))
            at = (WIDTH - margin - width, HEIGHT - margin - card.height)
            canvas.alpha_composite(card, at)
            draw = ImageDraw.Draw(canvas)
            draw.text((at[0] + 90, at[1] + 60), value, font=FIGURE, fill=accent)
            draw.text(
                (at[0] + 96, at[1] + 80 + box[3] + 60), label, font=FIGURE_LABEL, fill=theme.CARD_SOFT
            )

        return canvas.convert("RGB")


def write(path: Path, max_bytes: int = 2 * 1024 * 1024, **kwargs) -> Path:
    """Writes the thumbnail and returns the file that actually fits the cap.

    A generated field carries a gradient and a little grain, which PNG compresses badly: at
    3840x2160 it lands near 3 MB, over the 2 MB the mobile upload path allows. YouTube takes
    JPG as happily as PNG, and a gradient is exactly what JPEG is good at, so fall back to it
    rather than dropping the resolution YouTube recommends.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    image = render(**kwargs)
    image.save(path, "PNG", optimize=True)
    if path.stat().st_size <= max_bytes:
        return path

    jpeg = path.with_suffix(".jpg")
    for quality in (94, 90, 86, 80):
        image.save(jpeg, "JPEG", quality=quality, subsampling=0, optimize=True, progressive=True)
        if jpeg.stat().st_size <= max_bytes:
            path.unlink(missing_ok=True)
            return jpeg
    raise RuntimeError(
        f"thumbnail will not fit {max_bytes} bytes even at quality 80, simplify the field"
    )
