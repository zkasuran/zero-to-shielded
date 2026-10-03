"""Motion: easing, camera moves, the marker sweep, the cursor, captions and progress.

Everything here is drawn as a small patch pasted onto a copy of the cached page, so a
frame costs one memcpy, a couple of small pastes and one resize rather than a full
redraw. That performance posture is load bearing: this runs once per frame over thousands
of frames, so a new style has to stay a patch, never a full-canvas filter per frame.

The shipped look is the default and it is unchanged. `ease` is still the cubic in-out the
build depends on, and the default marker, cursor, caption and progress draw exactly as
before. The variety is opt-in through the style sub-dicts (theme.ACTIVE.marker, .cursor,
.caption, .progress), so a project that sets none of them renders identically to the kit
that had no styles at all.
"""

from __future__ import annotations

import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

import theme

WIDTH, HEIGHT = theme.CANVAS
OUT_W, OUT_H = theme.OUTPUT
ASPECT = OUT_W / OUT_H
Box = tuple[int, int, int, int]


# ---------------------------------------------------------------------------
# Easing. `ease` stays exactly the cubic in-out the build has always called, because the
# existing look depends on it. The rest are named and reached through ease_by, for the
# camera moves and any project that asks for a different feel.
# ---------------------------------------------------------------------------

def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


def _clamp(t: float) -> float:
    return max(0.0, min(1.0, t))


def ease_by(name: str, t: float) -> float:
    """A named easing curve, clamped to [0, 1] and pinned to 0 at t=0 and 1 at t=1."""
    t = _clamp(t)
    if name in ("linear", None):
        return t
    if name == "cubic" or name == "ease":
        return ease(t)
    if name == "quad-in":
        return t * t
    if name == "quad-out":
        return 1 - (1 - t) ** 2
    if name == "quad":
        return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2
    if name == "cubic-in":
        return t ** 3
    if name == "cubic-out":
        return 1 - (1 - t) ** 3
    if name == "quart-in":
        return t ** 4
    if name == "quart-out":
        return 1 - (1 - t) ** 4
    if name == "quart":
        return 8 * t ** 4 if t < 0.5 else 1 - (-2 * t + 2) ** 4 / 2
    if name == "expo-in":
        return 0.0 if t == 0 else 2 ** (10 * t - 10)
    if name == "expo-out":
        return 1.0 if t == 1 else 1 - 2 ** (-10 * t)
    if name == "back":
        c1, c3 = 1.70158, 2.70158
        return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2
    if name == "elastic":
        if t in (0.0, 1.0):
            return t
        c4 = (2 * math.pi) / 3
        return 2 ** (-10 * t) * math.sin((t * 10 - 0.75) * c4) + 1
    if name == "bounce":
        n1, d1 = 7.5625, 2.75
        if t < 1 / d1:
            return n1 * t * t
        if t < 2 / d1:
            t -= 1.5 / d1
            return n1 * t * t + 0.75
        if t < 2.5 / d1:
            t -= 2.25 / d1
            return n1 * t * t + 0.9375
        t -= 2.625 / d1
        return n1 * t * t + 0.984375
    return ease(t)


# ---------------------------------------------------------------------------
# Boxes and camera moves.
# ---------------------------------------------------------------------------

def full_box() -> Box:
    return (0, 0, WIDTH, HEIGHT)


def zoom_box(scale: float, cx: float = 0.5, cy: float = 0.5) -> Box:
    """A box at the given zoom, centred by default, for the gentle drift on cards.

    cx and cy move the centre, so a ken burns move can drift toward a corner rather than
    only pulling straight back. The default centre reproduces the original card drift.
    """
    width = round(WIDTH / scale)
    height = round(width / ASPECT)
    left = round((WIDTH - width) * cx)
    top = round((HEIGHT - height) * cy)
    left = max(0, min(left, WIDTH - width))
    top = max(0, min(top, HEIGHT - height))
    return (left, top, left + width, top + height)


def lerp_box(start: Box, end: Box, t: float, curve: str = "cubic") -> Box:
    e = ease(t) if curve == "cubic" else ease_by(curve, t)
    return tuple(round(start[index] + (end[index] - start[index]) * e) for index in range(4))  # type: ignore[return-value]


def ken_burns(t: float, direction: str = "in", amount: float = 0.08) -> Box:
    """A slow continuous drift over the whole segment, for a card or a still.

    `in` pushes toward the centre, `out` pulls back, and a compass direction drifts the
    crop toward that edge while zoomed. The move is small on purpose: it keeps a still
    frame from reading as a freeze without turning into a slideshow effect.
    """
    t = _clamp(t)
    if direction == "in":
        return zoom_box(1.0 + amount * t)
    if direction == "out":
        return zoom_box(1.0 + amount * (1 - t))
    scale = 1.0 + amount
    targets = {
        "left": (0.5 - 0.5 * t, 0.5), "right": (0.5 + 0.5 * t, 0.5),
        "up": (0.5, 0.5 - 0.5 * t), "down": (0.5, 0.5 + 0.5 * t),
    }
    cx, cy = targets.get(direction, (0.5, 0.5))
    return zoom_box(scale, cx, cy)


def pan(t: float, start: Box, end: Box, curve: str = "linear") -> Box:
    """Move across the canvas at constant zoom, holding the box size of `start`."""
    return lerp_box(start, end, t, curve)


def punch_in(t: float, scale: float = 1.08, hold: float = 0.5) -> Box:
    """A fast small zoom for a beat, then a hold. Reads as emphasis, not a camera move."""
    t = _clamp(t)
    if t < hold:
        return zoom_box(1.0 + (scale - 1.0) * ease_by("quad-out", t / hold))
    return zoom_box(scale)


def shake(t: float, box: Box, amount: int = 14, cycles: int = 5) -> Box:
    """A short settle, useful on a failure line. Decays to the given box."""
    t = _clamp(t)
    decay = (1 - t)
    dx = round(math.sin(t * cycles * 2 * math.pi) * amount * decay)
    dy = round(math.cos(t * cycles * 2.3 * math.pi) * amount * decay)
    return (box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)


def focus_box(
    boxes: list[Box], indexes: list[int], min_width: int = 1780, window: Box | None = None
) -> Box:
    """A 16:9 box around the lines being talked about, clamped to the canvas.

    Anchored to the left of the marked text rather than centred on it, because text
    reads from the left and keeping that margin in frame makes the move read as a zoom
    into the window instead of a crop that has lost it. When the window fits inside the
    crop on an axis, the crop is nudged to hold the whole window on that axis, so a
    line near the bottom of a tall page cannot slice the window in half.

    min_width is in reference-canvas pixels, so on a taller or wider canvas it scales
    with the frame rather than staying a fixed pixel count that would zoom too far.
    """
    min_width = round(min_width * (min(WIDTH, HEIGHT) / 1440))
    picked = [boxes[index] for index in indexes if 0 <= index < len(boxes)]
    if not picked:
        return full_box()
    left = min(box[0] for box in picked) - 90
    right = max(box[2] for box in picked) + 140
    top = min(box[1] for box in picked) - 120
    bottom = max(box[3] for box in picked) + 150
    width = max(right - left, min_width)
    height = round(width / ASPECT)
    if height < bottom - top:
        height = bottom - top
        width = round(height * ASPECT)
    width = min(width, WIDTH)
    height = min(round(width / ASPECT), HEIGHT)
    width = min(round(height * ASPECT), WIDTH)

    middle = (top + bottom) / 2
    left = min(max(left, 0), WIDTH - width)
    top = min(max(middle - height / 2, 0), HEIGHT - height)
    if window is not None:
        if height >= window[3] - window[1]:
            top = min(max(top, window[3] - height), window[1])
        if width >= window[2] - window[0]:
            left = min(max(left, window[2] - width), window[0])
        # The caption band is burned into the delivered frame, so in canvas terms its
        # height scales with the crop. Push the crop down far enough that the window's
        # own footer, which is where the honesty label lives, stays above the band.
        # Never so far that the line being spoken leaves the frame: that clamp wins.
        reserve = height * theme.CAPTION_RESERVE / theme.OUTPUT[1]
        want = window[3] - height + reserve
        if want > top:
            top = min(want, HEIGHT - height, min(box[1] for box in picked) - 40)
        left = min(max(left, 0), WIDTH - width)
        top = min(max(top, 0), HEIGHT - height)
    return (round(left), round(top), round(left) + width, round(top) + height)


# ---------------------------------------------------------------------------
# The marker. `highlight` is the shipped default and is byte-for-byte the old mark().
# ---------------------------------------------------------------------------

def _mark_style() -> dict:
    return getattr(theme.ACTIVE, "marker", {}) or {}


def mark(image: Image.Image, box: Box, colour: tuple[int, int, int], progress: float) -> None:
    """Sweep a marker across the line while it is spoken, in the active marker style.

    The default `highlight` is the original: ink blended into the page at 0.15 under a
    rounded mask, so the paper takes the colour and the text keeps its own. underline,
    box, strike and glow are alternatives for a project that wants a different emphasis.
    Every one wipes in with `progress` so it tracks the voice.
    """
    style = _mark_style().get("style", "highlight")
    span = round((box[2] - box[0]) * max(0.0, min(1.0, progress)))
    if span < 6:
        return
    if style == "underline":
        return _mark_underline(image, box, colour, span)
    if style == "box":
        return _mark_box(image, box, colour, span)
    if style == "strike":
        return _mark_strike(image, box, colour, span)
    if style == "glow":
        return _mark_glow(image, box, colour, span)
    _mark_highlight(image, box, colour, span)


def _mark_highlight(image, box, colour, span):
    opacity = _mark_style().get("opacity", 0.15)
    left = max(box[0] - 12, 0)
    top = max(box[1] - 5, 0)
    right = min(box[0] + span + 14, image.width)
    bottom = min(box[3] + 7, image.height)
    if right - left < 6 or bottom - top < 6:
        return
    region = image.crop((left, top, right, bottom)).convert("RGB")
    ink = Image.new("RGB", region.size, colour)
    blended = Image.blend(region, ink, opacity)
    mask = Image.new("L", region.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, region.width - 1, region.height - 1), radius=10, fill=180)
    image.paste(blended, (left, top), mask)


def _mark_underline(image, box, colour, span):
    draw = ImageDraw.Draw(image, "RGBA")
    y = min(box[3] + 4, image.height - 4)
    thick = max(3, round(6 * (min(image.width, image.height) / 1440)))
    draw.rounded_rectangle((box[0], y, box[0] + span, y + thick), radius=thick // 2, fill=(*colour, 235))


def _mark_box(image, box, colour, span):
    draw = ImageDraw.Draw(image, "RGBA")
    right = box[0] + span
    draw.rounded_rectangle((box[0] - 8, box[1] - 4, right + 8, box[3] + 4), radius=12,
                           outline=(*colour, 235), width=max(3, round(4 * min(image.width, image.height) / 1440)))


def _mark_strike(image, box, colour, span):
    draw = ImageDraw.Draw(image, "RGBA")
    y = (box[1] + box[3]) // 2
    thick = max(3, round(5 * min(image.width, image.height) / 1440))
    draw.line((box[0], y, box[0] + span, y), fill=(*colour, 235), width=thick)


def _mark_glow(image, box, colour, span):
    left = max(box[0] - 20, 0)
    top = max(box[1] - 14, 0)
    right = min(box[0] + span + 20, image.width)
    bottom = min(box[3] + 14, image.height)
    if right - left < 6 or bottom - top < 6:
        return
    layer = Image.new("RGBA", (right - left, bottom - top), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle((0, 0, right - left - 1, bottom - top - 1), radius=16, fill=(*colour, 90))
    layer = layer.filter(ImageFilter.GaussianBlur(10))
    image.paste(Image.alpha_composite(image.crop((left, top, right, bottom)).convert("RGBA"), layer).convert("RGB"),
                (left, top))


# ---------------------------------------------------------------------------
# The cursor. `arrow` is the shipped default and is byte-for-byte the old cursor().
# ---------------------------------------------------------------------------

def cursor(image: Image.Image, x: int, y: int, ripple: float | None, accent: tuple[int, int, int]) -> None:
    """The pointer, in the active cursor style. `arrow` is the original."""
    style = (getattr(theme.ACTIVE, "cursor", {}) or {}).get("style", "arrow")
    if style == "none":
        return
    if style == "dot":
        return _cursor_dot(image, x, y, ripple, accent)
    if style == "hand":
        return _cursor_hand(image, x, y, ripple, accent)
    if style == "caret":
        return _cursor_caret(image, x, y, ripple, accent)
    _cursor_arrow(image, x, y, ripple, accent)


def _cursor_arrow(image, x, y, ripple, accent):
    size = 210
    patch = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(patch)
    if ripple is not None and ripple < 1.0:
        radius = 22 + round(58 * ease(ripple))
        alpha = round(150 * (1 - ripple))
        draw.ellipse((70 - radius, 70 - radius, 70 + radius, 70 + radius), outline=(*accent, alpha), width=6)
    arrow = [(70, 66), (70, 128), (86, 113), (97, 137), (108, 132), (97, 108), (117, 106)]
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([(px + 5, py + 7) for px, py in arrow], fill=(20, 20, 30, 120))
    patch.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(6)))
    draw.polygon(arrow, fill=(255, 255, 255, 255), outline=(28, 32, 44, 255))
    image.paste(patch, (x - 70, y - 66), patch)


def _cursor_dot(image, x, y, ripple, accent):
    size = 220
    patch = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(patch)
    c = size // 2
    if ripple is not None and ripple < 1.0:
        radius = 30 + round(60 * ease(ripple))
        draw.ellipse((c - radius, c - radius, c + radius, c + radius), outline=(*accent, round(150 * (1 - ripple))), width=6)
    draw.ellipse((c - 34, c - 34, c + 34, c + 34), fill=(*accent, 60))
    draw.ellipse((c - 16, c - 16, c + 16, c + 16), fill=(*accent, 235), outline=(255, 255, 255, 235), width=3)
    image.paste(patch, (x - c, y - c), patch)


def _cursor_hand(image, x, y, ripple, accent):
    size = 210
    patch = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(patch)
    if ripple is not None and ripple < 1.0:
        radius = 22 + round(58 * ease(ripple))
        draw.ellipse((70 - radius, 70 - radius, 70 + radius, 70 + radius), outline=(*accent, round(150 * (1 - ripple))), width=6)
    # a simple pointing hand: a rounded palm with one extended finger
    draw.rounded_rectangle((60, 78, 104, 140), radius=18, fill=(255, 255, 255, 255), outline=(28, 32, 44, 255), width=3)
    draw.rounded_rectangle((70, 46, 86, 96), radius=8, fill=(255, 255, 255, 255), outline=(28, 32, 44, 255), width=3)
    image.paste(patch, (x - 70, y - 66), patch)


def _cursor_caret(image, x, y, ripple, accent):
    # a text caret for typing shots. ripple doubles as the blink phase.
    draw = ImageDraw.Draw(image, "RGBA")
    visible = ripple is None or (ripple % 1.0) < 0.6
    if not visible:
        return
    h = round(46 * min(image.width, image.height) / 1440)
    draw.rectangle((x, y - h // 2, x + max(3, h // 16), y + h // 2), fill=(*accent, 235))


# ---------------------------------------------------------------------------
# Progress. `bar` is the shipped default and is byte-for-byte the old progress().
# ---------------------------------------------------------------------------

def progress(image: Image.Image, ratio: float, accent: tuple[int, int, int],
             boundaries: list[float] | None = None) -> None:
    """The progress indicator, in the active style. `bar` is the original.

    Drawn on the delivered frame so a zoom can never crop it. `segments` needs the scene
    boundary ratios to draw ticks and falls back to the plain bar without them, and `ring`
    is a corner arc for a portrait cut where a full-width bar eats too much frame.
    """
    style = (getattr(theme.ACTIVE, "progress", {}) or {}).get("style", "bar")
    if style == "none":
        return
    if style == "ring":
        return _progress_ring(image, ratio, accent)
    if style == "segments" and boundaries:
        return _progress_segments(image, ratio, accent, boundaries)
    _progress_bar(image, ratio, accent)


def _progress_bar(image, ratio, accent):
    width, height = image.size
    bar = 8
    patch = Image.new("RGBA", (width, bar), (255, 255, 255, 90))
    filled = round(width * max(0.0, min(1.0, ratio)))
    if filled > 0:
        ImageDraw.Draw(patch).rectangle((0, 0, filled, bar), fill=(*accent, 235))
    image.paste(patch, (0, height - bar), patch)


def _progress_segments(image, ratio, accent, boundaries):
    width, height = image.size
    bar = 10
    patch = Image.new("RGBA", (width, bar), (0, 0, 0, 0))
    draw = ImageDraw.Draw(patch)
    edges = sorted(set([0.0] + [b for b in boundaries if 0 < b < 1] + [1.0]))
    gap = max(2, round(width * 0.004))
    for start, end in zip(edges, edges[1:]):
        x0 = round(width * start) + gap
        x1 = round(width * end) - gap
        draw.rounded_rectangle((x0, 2, x1, bar - 1), radius=(bar - 3) // 2, fill=(255, 255, 255, 90))
        if ratio >= end:
            fill_x1 = x1
        elif ratio <= start:
            fill_x1 = x0
        else:
            fill_x1 = round(x0 + (x1 - x0) * (ratio - start) / (end - start))
        if fill_x1 > x0:
            draw.rounded_rectangle((x0, 2, fill_x1, bar - 1), radius=(bar - 3) // 2, fill=(*accent, 235))
    image.paste(patch, (0, height - bar - 2), patch)


def _progress_ring(image, ratio, accent):
    width, height = image.size
    r = round(34 * min(width, height) / 1080)
    margin = round(28 * min(width, height) / 1080)
    cx, cy = width - margin - r, margin + r
    patch = Image.new("RGBA", (2 * r + 8, 2 * r + 8), (0, 0, 0, 0))
    draw = ImageDraw.Draw(patch)
    c = r + 4
    draw.ellipse((c - r, c - r, c + r, c + r), outline=(255, 255, 255, 150), width=5)
    draw.arc((c - r, c - r, c + r, c + r), -90, -90 + 360 * max(0.0, min(1.0, ratio)), fill=(*accent, 245), width=5)
    image.paste(patch, (cx - c, cy - c), patch)


# ---------------------------------------------------------------------------
# Captions. `band` is the shipped default and is byte-for-byte the old caption().
# ---------------------------------------------------------------------------

def caption(image: Image.Image, text: str, accent: tuple[int, int, int],
            words: list[tuple[float, float, str]] | None = None, now: float | None = None) -> None:
    """The line being spoken, burned into the delivered frame, in the active style.

    `band` is the original centre band. `top` moves it up for a portrait cut where the
    bottom is covered by platform UI. `boxed` is a floating rounded caption. `karaoke`
    lifts the word being spoken in the accent colour, and needs word timings, so it
    degrades to the plain band when they are absent.
    """
    if not text:
        return
    style = (getattr(theme.ACTIVE, "caption", {}) or {})
    kind = style.get("style", "band")
    position = style.get("position", "bottom")
    if kind == "none":
        return
    if kind == "boxed":
        return _caption_boxed(image, text, accent, position)
    if kind == "karaoke" and words and now is not None:
        return _caption_karaoke(image, text, accent, position, words, now)
    _caption_band(image, text, accent, position)


def _band_top(image_height: int, position: str) -> int:
    band = theme.CAPTION_BAND
    if position == "top":
        return 8
    return image_height - 8 - band


def _caption_band(image, text, accent, position):
    width, height = image.size
    band = theme.CAPTION_BAND
    top = _band_top(height, position)
    scrim = Image.new("RGBA", (width, band), (17, 23, 35, 216))
    image.paste(scrim, (0, top), scrim)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, top, width, top + 2), fill=accent)
    box = draw.textbbox((0, 0), text, font=theme.CAPTION)
    draw.text(((width - (box[2] - box[0])) // 2 - box[0], top + (band - (box[3] - box[1])) // 2 - box[1]),
              text, font=theme.CAPTION, fill=(245, 247, 252))


def _caption_boxed(image, text, accent, position):
    width, height = image.size
    draw = ImageDraw.Draw(image, "RGBA")
    tb = draw.textbbox((0, 0), text, font=theme.CAPTION)
    tw, th = tb[2] - tb[0], tb[3] - tb[1]
    pad = round(24 * height / 1080)
    band = th + 2 * pad
    top = _band_top(height, position)
    x0 = (width - tw) // 2 - pad
    draw.rounded_rectangle((x0, top, x0 + tw + 2 * pad, top + band), radius=band // 3, fill=(17, 23, 35, 230))
    draw.text((x0 + pad - tb[0], top + pad - tb[1]), text, font=theme.CAPTION, fill=(245, 247, 252))


def _caption_karaoke(image, text, accent, position, words, now):
    width, height = image.size
    band = theme.CAPTION_BAND
    top = _band_top(height, position)
    scrim = Image.new("RGBA", (width, band), (17, 23, 35, 216))
    image.paste(scrim, (0, top), scrim)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, top, width, top + 2), fill=accent)
    pieces = [w for (_, _, w) in words] if words else text.split()
    full = " ".join(pieces)
    total_w = draw.textlength(full, font=theme.CAPTION)
    x = (width - total_w) // 2
    y = top + (band - theme.CAPTION.size) // 2
    for start, end, word in words:
        spoken = start <= now < end or now >= end
        colour = accent if (start <= now) else (245, 247, 252)
        draw.text((x, y), word, font=theme.CAPTION, fill=colour if spoken or start <= now else (245, 247, 252))
        x += draw.textlength(word + " ", font=theme.CAPTION)


# ---------------------------------------------------------------------------
# Overlays a project or a transition can call: vignette, grain, fade.
# ---------------------------------------------------------------------------

def vignette(image: Image.Image, amount: float = 0.35) -> None:
    """Darken the corners. Cheap: one radial mask multiplied in, computed at low res."""
    w, h = image.size
    small = Image.new("L", (64, 36), 0)
    dr = ImageDraw.Draw(small)
    dr.ellipse((-16, -9, 80, 45), fill=255)
    mask = small.resize((w, h), Image.BICUBIC).point(lambda v: round(255 - (255 - v) * amount))
    black = Image.new("RGB", (w, h), (0, 0, 0))
    image.paste(Image.composite(image, black, mask), (0, 0))


def grain(image: Image.Image, amount: float = 0.03) -> None:
    noise = Image.effect_noise(image.size, 12).convert("RGB")
    image.paste(Image.blend(image, noise, amount), (0, 0))


def fade(image: Image.Image, amount: float, colour: tuple[int, int, int] = (0, 0, 0)) -> Image.Image:
    """Blend toward a colour by amount in [0, 1], for a dip transition drawn in Python."""
    if amount <= 0:
        return image
    return Image.blend(image, Image.new("RGB", image.size, colour), min(1.0, amount))


def deliver(image: Image.Image, box: Box) -> Image.Image:
    if box == full_box():
        return image.resize(theme.OUTPUT, Image.BICUBIC)
    return image.crop(box).resize(theme.OUTPUT, Image.BICUBIC)
