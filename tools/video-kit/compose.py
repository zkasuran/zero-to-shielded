"""Composition and overlays: more than one scene in a frame, and a graphics layer.

The single most useful thing the kit could not do was show two scenes at once. Code
beside the terminal output it produces is the clearest way to prove a claim, and until
now they could only be consecutive shots. `compose` places two or more real scenes in
one frame. `overlay` adds a lower third, callouts and stat blocks over a base scene or
the bare field.

The one thing to get right is the box transform. The zoom, the marker and the cursor all
aim at `boxes`, so a pane's boxes have to be scaled and shifted into the composed frame
exactly as its picture was, or the highlight lands in the wrong place. That transform is
the reason this module exists as its own renderer rather than a project convention.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image, ImageDraw

import bg
import style
import theme


@dataclass
class Page:
    image: Image.Image
    window: tuple[int, int, int, int]
    row_boxes: list[tuple[int, int, int, int]] = field(default_factory=list)

    @property
    def boxes(self) -> list[tuple[int, int, int, int]]:
        return self.row_boxes


def _fit(inner_w: int, inner_h: int, src_w: int, src_h: int):
    """Scale factor and offset to fit a pane image into a region, keeping aspect.

    Letterbox inside the region rather than distort, because a stretched terminal reads
    as broken. Returns (scale, off_x, off_y) so the caller can both paste the picture and
    move that pane's boxes by the same transform.
    """
    scale = min(inner_w / src_w, inner_h / src_h)
    draw_w, draw_h = round(src_w * scale), round(src_h * scale)
    off_x = (inner_w - draw_w) // 2
    off_y = (inner_h - draw_h) // 2
    return scale, off_x, off_y, draw_w, draw_h


def _regions(layout: str, count: int, gap: int, canvas, inset_corner: str):
    """Pixel regions for each pane, by layout. Portrait forces a vertical stack.

    A split-v in portrait is two thin columns nobody can read, so at a taller-than-wide
    canvas split-v falls back to split-h. That keeps a compose scene usable in a 9:16 cut
    without the project having to know the aspect.
    """
    w, h = canvas
    portrait = h > w
    if layout == "split-v" and portrait:
        layout = "split-h"

    if layout == "split-v":
        half = (w - gap) // 2
        return [(0, 0, half, h), (half + gap, 0, w, h)]
    if layout == "split-h":
        half = (h - gap) // 2
        return [(0, 0, w, half), (0, half + gap, w, h)]
    if layout == "grid":
        cw, ch = (w - gap) // 2, (h - gap) // 2
        return [(0, 0, cw, ch), (cw + gap, 0, w, ch),
                (0, ch + gap, cw, h), (cw + gap, ch + gap, w, h)][:count]
    if layout == "pip":
        pip_w, pip_h = round(w * 0.34), round(h * 0.34)
        margin = round(min(w, h) * 0.03)
        corners = {
            "bottom-right": (w - pip_w - margin, h - pip_h - margin),
            "bottom-left": (margin, h - pip_h - margin),
            "top-right": (w - pip_w - margin, margin),
            "top-left": (margin, margin),
        }
        px, py = corners.get(inset_corner, corners["bottom-right"])
        return [(0, 0, w, h), (px, py, px + pip_w, py + pip_h)]
    raise RuntimeError(f"unknown compose layout {layout!r}, have split-v, split-h, grid, pip")


@style.scene("compose")
def prepare(segment, project, work, base, style_, palette):
    """Two or more scenes in one frame, each keeping its own window chrome.

    build.prepare is imported here rather than at module top because build imports the
    scene registry, so a top-level import would be circular. Each pane is prepared through
    the same registry, so a compose pane can itself be any scene type, chart included.
    """
    import build

    layout = segment.get("layout", "split-v")
    gap = theme.px(segment.get("gap", 40))
    panes = segment["panes"]
    if not panes:
        raise RuntimeError("compose scene has no panes")

    canvas = theme.CANVAS
    regions = _regions(layout, len(panes), gap, canvas, segment.get("inset", "bottom-right"))
    if len(panes) > len(regions):
        raise RuntimeError(f"compose layout {layout!r} holds {len(regions)} panes, got {len(panes)}")

    accent = palette["accent"]
    prepared = []
    total = 0
    for pane, region in zip(panes, regions):
        page_for, count, resolve = build.prepare(pane, project, work, base, accent, palette["mark"])
        prepared.append({"page_for": page_for, "count": count, "resolve": resolve, "region": region})
        total += count

    def page_for(visible: int) -> Page:
        image = base.copy()
        boxes: list[tuple[int, int, int, int]] = []
        seen = 0
        for item in prepared:
            region = item["region"]
            rx0, ry0, rx1, ry1 = region
            inner_w, inner_h = rx1 - rx0, ry1 - ry0
            # each pane is fully revealed up to the running total, so the reveal walks
            # pane by pane in declaration order
            local_visible = max(0, min(item["count"], visible - seen))
            pane_page = item["page_for"](item["count"])  # draw full, reveal is handled by placement order
            src = pane_page.image
            scale, off_x, off_y, draw_w, draw_h = _fit(inner_w, inner_h, src.width, src.height)
            placed = src.resize((draw_w, draw_h), Image.BICUBIC)
            image.paste(placed, (rx0 + off_x, ry0 + off_y))
            # transform this pane's boxes into the composed frame by the same scale+offset
            for b in pane_page.boxes:
                boxes.append((
                    round(rx0 + off_x + b[0] * scale),
                    round(ry0 + off_y + b[1] * scale),
                    round(rx0 + off_x + b[2] * scale),
                    round(ry0 + off_y + b[3] * scale),
                ))
            seen += item["count"]
        return Page(image=image, window=None, row_boxes=boxes)

    def resolve(needle: str) -> list[int]:
        offset = 0
        for item in prepared:
            found = item["resolve"](needle)
            if found:
                return [offset + found[0]]
            offset += item["count"]
        return []

    return page_for, total, resolve


# ---------------------------------------------------------------------------
# overlay: a graphics layer over a base scene or the bare field.
# ---------------------------------------------------------------------------

def _under(segment, project, work, base, palette):
    """Render the optional base scene the overlay sits on, or return the bare field."""
    if "under" not in segment:
        return base.copy(), None
    import build
    page_for, count, resolve = build.prepare(segment["under"], project, work, base,
                                             palette["accent"], palette["mark"])
    return page_for(count).image.copy(), None


@style.scene("overlay")
def prepare_overlay(segment, project, work, base, style_, palette):
    accent = palette["accent"]
    under, _ = _under(segment, project, work, base, palette)
    elements = segment["elements"]
    count = len(elements)
    w, h = theme.CANVAS

    def render_element(draw, image, el, index):
        kind = el.get("kind", "lower-third")
        if kind == "lower-third":
            band_h = theme.px(160)
            y = h - band_h - theme.px(120)
            draw.rectangle((theme.px(80), y, w - theme.px(80), y + band_h), fill=(*_rgba(accent, 235)[:3],))
            draw.text((theme.px(120), y + theme.px(24)), el.get("title", ""), font=theme.CARD_MONO, fill=(255, 255, 255))
            if el.get("subtitle"):
                draw.text((theme.px(120), y + theme.px(104)), el["subtitle"], font=theme.PANEL_LABEL, fill=(240, 244, 252))
            return (theme.px(80), y, w - theme.px(80), y + band_h)
        if kind == "callout":
            at = el.get("at", [w // 2, h // 2])
            bx, by = theme.px(el.get("box", [200, 200])[0]), theme.px(el.get("box", [200, 200])[1])
            label = el.get("label", "")
            tw = draw.textlength(label, font=theme.PANEL_LABEL)
            box = (bx, by, bx + round(tw) + theme.px(48), by + theme.px(72))
            draw.line((box[0], (box[1] + box[3]) // 2, at[0], at[1]), fill=accent, width=theme.px(4))
            draw.ellipse((at[0] - theme.px(10), at[1] - theme.px(10), at[0] + theme.px(10), at[1] + theme.px(10)), fill=accent)
            draw.rounded_rectangle(box, radius=theme.px(16), fill=theme.PANEL, outline=accent, width=theme.px(3))
            draw.text((box[0] + theme.px(24), box[1] + theme.px(16)), label, font=theme.PANEL_LABEL, fill=theme.INK)
            return box
        if kind == "badge":
            x = theme.px(120) + index * theme.px(360)
            y = theme.px(120)
            label = el.get("label", "")
            tw = draw.textlength(label, font=theme.CHROME)
            box = (x, y, x + round(tw) + theme.px(56), y + theme.px(60))
            draw.rounded_rectangle(box, radius=theme.px(30), fill=el.get("colour_rgb", accent))
            draw.text((x + theme.px(28), y + theme.px(14)), label, font=theme.CHROME, fill=(255, 255, 255))
            return box
        if kind == "stat":
            cx = w // 2
            y = h // 2 - theme.px(120)
            number = el.get("number", "")
            nb = draw.textbbox((0, 0), number, font=theme.CARD)
            draw.text((cx - (nb[2] - nb[0]) // 2, y), number, font=theme.CARD, fill=accent)
            cap = el.get("caption", "")
            cb = draw.textbbox((0, 0), cap, font=theme.KICKER)
            draw.text((cx - (cb[2] - cb[0]) // 2, y + theme.px(130)), cap, font=theme.KICKER, fill=theme.INK)
            return (cx - theme.px(300), y, cx + theme.px(300), y + theme.px(200))
        raise RuntimeError(f"unknown overlay element {kind!r}")

    def page_for(visible: int) -> Page:
        image = under.copy()
        draw = ImageDraw.Draw(image, "RGBA")
        boxes = []
        for index, el in enumerate(elements):
            # measure the box for every element so focus works, draw only revealed ones
            if index < visible:
                boxes.append(tuple(round(v) for v in render_element(draw, image, el, index)))
            else:
                boxes.append((0, 0, 1, 1))
        # fill any measured-but-not-drawn boxes with a real box so focus can still aim
        for index, el in enumerate(elements):
            if boxes[index] == (0, 0, 1, 1):
                tmp = Image.new("RGB", image.size)
                boxes[index] = tuple(round(v) for v in render_element(ImageDraw.Draw(tmp, "RGBA"), tmp, el, index))
        return Page(image=image, window=None, row_boxes=boxes)

    def resolve(needle: str) -> list[int]:
        low = needle.lower()
        for index, el in enumerate(elements):
            hay = " ".join(str(el.get(k, "")) for k in ("title", "subtitle", "label", "caption", "number")).lower()
            if low in hay:
                return [index]
        return []

    return page_for, count, resolve


def _rgba(colour, alpha):
    return (colour[0], colour[1], colour[2], alpha)
