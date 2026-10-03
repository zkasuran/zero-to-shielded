"""Backgrounds, generated rather than downloaded.

A bright field with soft colour blobs, blurred, with a little grain so it does not
band on a dark screen. Drawn once per project and cached, because it is the same field
behind every frame.

The field shape comes from the palette: `vertical` is a top to bottom ramp, `diagonal`
runs the ramp corner to corner, `radial` pools the light in the middle. One theme per
video, so two videos from this workspace never share a field.

Generating rather than downloading keeps the video free of image licences, which the
hackathon rules ask for, and keeps the contrast behind the window under our control.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import theme

WIDTH, HEIGHT = theme.CANVAS
Colour = tuple[int, int, int]


def _gradient(top: Colour, bottom: Colour) -> Image.Image:
    strip = Image.new("RGB", (2, 160))
    draw = ImageDraw.Draw(strip)
    for row in range(160):
        ratio = row / 159
        draw.line(
            [(0, row), (1, row)],
            fill=tuple(round(top[index] + (bottom[index] - top[index]) * ratio) for index in range(3)),
        )
    return strip.resize((WIDTH, HEIGHT), Image.BICUBIC)


def _diagonal(top: Colour, bottom: Colour) -> Image.Image:
    """The same ramp run corner to corner, so the light falls across the frame."""
    small = Image.new("RGB", (96, 54))
    draw = ImageDraw.Draw(small)
    for y in range(54):
        for x in range(96):
            ratio = (x / 95 + y / 53) / 2
            draw.point((x, y), fill=tuple(
                round(top[index] + (bottom[index] - top[index]) * ratio) for index in range(3)
            ))
    return small.resize((WIDTH, HEIGHT), Image.BICUBIC)


def _radial(top: Colour, bottom: Colour) -> Image.Image:
    """Light pooled in the middle, darker at the corners."""
    small = Image.new("RGB", (96, 54))
    draw = ImageDraw.Draw(small)
    for y in range(54):
        for x in range(96):
            dx, dy = (x - 47.5) / 47.5, (y - 26.5) / 26.5
            ratio = min(1.0, (dx * dx + dy * dy) ** 0.5 / 1.35)
            draw.point((x, y), fill=tuple(
                round(top[index] + (bottom[index] - top[index]) * ratio) for index in range(3)
            ))
    return small.resize((WIDTH, HEIGHT), Image.BICUBIC)


def _mesh(top: Colour, bottom: Colour) -> Image.Image:
    """Several colour points blended smoothly, the modern mesh-gradient look.

    Built at 96x54 by inverse-distance weighting a handful of seeded points, then scaled
    up. The points are derived from the two palette ends rather than random, so a mesh
    field is reproducible and a rebuild of an old project cannot drift.
    """
    small = Image.new("RGB", (96, 54))
    draw = ImageDraw.Draw(small)
    mid = tuple(round((top[i] + bottom[i]) / 2) for i in range(3))
    points = [
        ((0.15, 0.2), top), ((0.85, 0.15), mid), ((0.2, 0.85), mid),
        ((0.9, 0.8), bottom), ((0.5, 0.5), tuple(round((top[i] * 2 + bottom[i]) / 3) for i in range(3))),
    ]
    for y in range(54):
        for x in range(96):
            fx, fy = x / 95, y / 53
            weights, acc = 0.0, [0.0, 0.0, 0.0]
            for (px, py), colour in points:
                d = ((fx - px) ** 2 + (fy - py) ** 2) ** 0.5 + 0.06
                w = 1.0 / (d * d)
                weights += w
                for i in range(3):
                    acc[i] += colour[i] * w
            draw.point((x, y), fill=tuple(round(acc[i] / weights) for i in range(3)))
    return small.resize((WIDTH, HEIGHT), Image.BICUBIC)


def _conic(top: Colour, bottom: Colour) -> Image.Image:
    """A sweep around the centre, so the light rotates rather than runs."""
    import math

    small = Image.new("RGB", (96, 54))
    draw = ImageDraw.Draw(small)
    for y in range(54):
        for x in range(96):
            angle = math.atan2((y - 26.5) / 26.5, (x - 47.5) / 47.5)
            ratio = (angle + math.pi) / (2 * math.pi)
            # fold so the sweep meets itself instead of banding at the seam
            ratio = 1 - abs(1 - 2 * ratio)
            draw.point((x, y), fill=tuple(
                round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3)
            ))
    return small.resize((WIDTH, HEIGHT), Image.BICUBIC)


def _waves(top: Colour, bottom: Colour) -> Image.Image:
    """Soft banded curves, a calmer field for a dense page."""
    import math

    small = Image.new("RGB", (192, 108))
    draw = ImageDraw.Draw(small)
    for y in range(108):
        for x in range(192):
            phase = math.sin(x / 26.0) * 0.18 + math.sin(x / 11.0) * 0.06
            ratio = min(1.0, max(0.0, y / 107 + phase))
            draw.point((x, y), fill=tuple(
                round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3)
            ))
    return small.resize((WIDTH, HEIGHT), Image.BICUBIC)


def _dots(top: Colour, bottom: Colour) -> Image.Image:
    """A regular dot pattern over the ramp, drawn at full size so the dots stay crisp."""
    canvas = _gradient(top, bottom)
    draw = ImageDraw.Draw(canvas, "RGBA")
    step = round(WIDTH / 28)
    radius = max(3, step // 12)
    for y in range(step // 2, HEIGHT, step):
        for x in range(step // 2, WIDTH, step):
            draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(255, 255, 255, 62))
    return canvas


def _grid(top: Colour, bottom: Colour) -> Image.Image:
    """A faint rule grid over the ramp. Reads as graph paper behind the window."""
    canvas = _diagonal(top, bottom)
    draw = ImageDraw.Draw(canvas, "RGBA")
    step = round(WIDTH / 24)
    for x in range(0, WIDTH, step):
        draw.line((x, 0, x, HEIGHT), fill=(255, 255, 255, 46), width=2)
    for y in range(0, HEIGHT, step):
        draw.line((0, y, WIDTH, y), fill=(255, 255, 255, 46), width=2)
    return canvas


def _noise(top: Colour, bottom: Colour) -> Image.Image:
    """An organic cloudy field: heavy blurred noise tinted between the two ends.

    The noise is seeded from a fixed pattern rather than Image.effect_noise, so the field
    is reproducible. A random cloud would make every rebuild a different picture.
    """
    import math

    small = Image.new("L", (96, 54))
    px = small.load()
    for y in range(54):
        for x in range(96):
            v = (math.sin(x * 0.31) * math.cos(y * 0.27)
                 + math.sin((x + y) * 0.13) * 0.7
                 + math.cos((x - y) * 0.19) * 0.5)
            px[x, y] = max(0, min(255, round(128 + v * 52)))
    mask = small.resize((WIDTH, HEIGHT), Image.BICUBIC).filter(ImageFilter.GaussianBlur(40))
    return Image.composite(
        Image.new("RGB", (WIDTH, HEIGHT), top),
        Image.new("RGB", (WIDTH, HEIGHT), bottom),
        mask,
    )


def _spotlight(top: Colour, bottom: Colour) -> Image.Image:
    """A bright pool with a strong dark surround, which is what a dark cut needs.

    Steeper than `radial`: the falloff is squared so the corners go properly dark rather
    than merely dimmer, which is the difference between a light field and a dark one.
    """
    small = Image.new("RGB", (96, 54))
    draw = ImageDraw.Draw(small)
    for y in range(54):
        for x in range(96):
            dx, dy = (x - 47.5) / 47.5, (y - 26.5) / 26.5
            ratio = min(1.0, ((dx * dx + dy * dy) ** 0.5 / 1.15) ** 1.7)
            draw.point((x, y), fill=tuple(
                round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3)
            ))
    return small.resize((WIDTH, HEIGHT), Image.BICUBIC)


FIELDS = {
    # The first three are the shipped fields and must stay byte-identical: every existing
    # project draws one of them and a rebuild has to produce the same picture.
    "vertical": _gradient,
    "diagonal": _diagonal,
    "radial": _radial,
    "mesh": _mesh,
    "conic": _conic,
    "waves": _waves,
    "dots": _dots,
    "grid": _grid,
    "noise": _noise,
    "spotlight": _spotlight,
}


def _blob(canvas: Image.Image, centre: tuple[float, float], radius: float, colour: Colour, alpha: float) -> None:
    size = round(min(WIDTH, HEIGHT) * radius)
    mask = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(mask)
    cx, cy = round(centre[0] * WIDTH), round(centre[1] * HEIGHT)
    draw.ellipse((cx - size, cy - size, cx + size, cy + size), fill=round(255 * alpha))
    canvas.paste(
        Image.new("RGB", (WIDTH, HEIGHT), colour),
        (0, 0),
        mask.filter(ImageFilter.GaussianBlur(radius=size * 0.6)),
    )


def background(name: str, cache: Path | None = None) -> Image.Image:
    if cache is not None and cache.exists():
        return Image.open(cache).convert("RGB")
    palette = theme.palette(name)
    canvas = FIELDS[palette.get("field", "vertical")](palette["top"], palette["bottom"])
    for centre, radius, colour, alpha in palette["blobs"]:
        _blob(canvas, centre, radius, colour, alpha)
    canvas = canvas.filter(ImageFilter.GaussianBlur(radius=26))
    grain = Image.effect_noise((WIDTH, HEIGHT), 10).convert("RGB")
    canvas = Image.blend(canvas, grain, 0.03)
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        canvas.save(cache)
    return canvas


def drop_shadow(canvas: Image.Image, box: tuple[int, int, int, int], radius: int, blur: int = 34, alpha: int = 92) -> None:
    """A soft shadow so the window reads as floating over the field."""
    layer = Image.new("L", (WIDTH, HEIGHT), 0)
    draw = ImageDraw.Draw(layer)
    left, top, right, bottom = box
    draw.rounded_rectangle((left + 4, top + 20, right + 4, bottom + 26), radius=radius, fill=alpha)
    canvas.paste(
        Image.new("RGB", (WIDTH, HEIGHT), (46, 34, 68)),
        (0, 0),
        layer.filter(ImageFilter.GaussianBlur(radius=blur)),
    )
