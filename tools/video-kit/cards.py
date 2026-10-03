"""Caption and title cards.

Large dark text on the bright generated field, drawn once per card. The card image
is handed back so the frame loop can drift it, which keeps a still card from
feeling like a freeze.
"""

from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

import theme

WIDTH, HEIGHT = theme.CANVAS

# The card drifts in at 1.05x (see build.card_painter), which crops the frame edges.
# A line has to clear that crop or it gets sliced at the edge, so this is the widest a
# card line may render before the type is shrunk to fit.
SAFE_W = round(WIDTH / 1.05) - 90


def _centre(draw: ImageDraw.ImageDraw, text: str, font, y: int, fill, shadow: bool = True) -> None:
    width = draw.textbbox((0, 0), text, font=font)[2]
    x = (WIDTH - width) // 2
    if shadow:
        draw.text((x + 3, y + 4), text, font=font, fill=(255, 255, 255, 120))
    draw.text((x, y), text, font=font, fill=fill)


def page(
    base: Image.Image,
    lines: list[str],
    kicker: str | None,
    footer: str | None,
    mono: bool,
    accent: tuple[int, int, int],
) -> Image.Image:
    image = base.copy()
    draw = ImageDraw.Draw(image)
    path = theme.MONO if mono else theme.SANS_BOLD
    size = (theme.CARD_MONO if mono else theme.CARD).size
    font = ImageFont.truetype(path, size)
    # Only ever shrinks: a card whose lines already clear the drift crop is unchanged,
    # a card with a long line drops font size until its widest line fits SAFE_W.
    def _widest(f) -> int:
        return max((draw.textbbox((0, 0), line, font=f)[2] for line in lines), default=0)
    while size > 42 and _widest(font) > SAFE_W:
        size -= 2
        font = ImageFont.truetype(path, size)
    heights = []
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        heights.append(box[3] - box[1])
    block = sum(height + 46 for height in heights) - 46
    y = (HEIGHT - block) // 2
    if kicker is not None:
        _centre(draw, kicker, theme.KICKER, y - 130, accent)
    for line, height in zip(lines, heights):
        _centre(draw, line, font, y, theme.CARD_INK)
        y += height + 46
    if footer is not None:
        _centre(draw, footer, theme.FOOTER, HEIGHT - 150, theme.CARD_SOFT)
    return image
