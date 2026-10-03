"""Device frames: mount a captured page or a still inside a drawn device.

Every scene in the kit floats one near-white rounded window with mac traffic lights,
whatever it is showing, so a phone product and a desktop one look the same. This draws a
real frame around the picture: a phone, a tablet, a laptop, a desktop browser with the
live URL in its bar, a titled terminal, or the bare capture. All geometry, no downloaded
image, so there is no licence to defend.

The capture reuses web.capture, so the receipt discipline is unchanged. The one careful
part is the box transform: the screenshot is scaled and inset into the device screen, so
each captured box has to move by the same scale and offset or the marker lands off target.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from PIL import Image, ImageDraw

import bg
import style
import theme
import web


@dataclass
class Page:
    image: Image.Image
    window: tuple[int, int, int, int]
    row_boxes: list[tuple[int, int, int, int]] = field(default_factory=list)

    @property
    def boxes(self) -> list[tuple[int, int, int, int]]:
        return self.row_boxes


def _screen_rect(frame: str, canvas, viewport_ratio: float):
    """Where the screen sits, and the device body box, for one frame kind.

    Returns (screen_box, body_box, bezel). The screen box is where the screenshot goes,
    the body box is what the zoom keeps in frame, and the bezel drives the corner radius.
    Sizes scale from the canvas so a phone fills a 9:16 frame and floats inside a 16:9 one.
    """
    w, h = canvas
    portrait = h >= w

    if frame == "phone":
        # a tall handset, centred, sized to leave room for a caption on a wide canvas
        body_h = int(h * (0.94 if portrait else 0.86))
        body_w = int(body_h * 0.49)
        if body_w > w * 0.7:
            body_w = int(w * 0.44)
            body_h = int(body_w / 0.49)
        bx = (w - body_w) // 2
        by = (h - body_h) // 2
        bezel = theme.px(18)
        screen = (bx + bezel, by + bezel + theme.px(20), bx + body_w - bezel, by + body_h - bezel - theme.px(20))
        return screen, (bx, by, bx + body_w, by + body_h), bezel
    if frame == "tablet":
        body_h = int(h * (0.9 if portrait else 0.84))
        body_w = int(body_h * (0.74 if portrait else 1.34))
        if body_w > w * 0.86:
            body_w = int(w * 0.82); body_h = int(body_w / 1.34)
        bx, by = (w - body_w) // 2, (h - body_h) // 2
        bezel = theme.px(34)
        screen = (bx + bezel, by + bezel, bx + body_w - bezel, by + body_h - bezel)
        return screen, (bx, by, bx + body_w, by + body_h), bezel
    if frame == "laptop":
        lid_w = int(w * 0.8)
        lid_h = int(lid_w * 0.62)
        bx = (w - lid_w) // 2
        by = int(h * 0.1)
        bezel = theme.px(26)
        screen = (bx + bezel, by + bezel, bx + lid_w - bezel, by + lid_h - bezel)
        return screen, (bx, by, bx + lid_w, by + lid_h + theme.px(60)), bezel
    if frame == "browser":
        body_w = int(w * 0.9)
        chrome = theme.px(84)
        # size the body to the shot aspect, capped to the canvas
        body_h = int(h * 0.86)
        bx, by = (w - body_w) // 2, (h - body_h) // 2
        screen = (bx, by + chrome, bx + body_w, by + body_h)
        return screen, (bx, by, bx + body_w, by + body_h), theme.px(16)
    if frame == "terminal":
        body_w = int(w * 0.88)
        chrome = theme.px(66)
        body_h = int(h * 0.82)
        bx, by = (w - body_w) // 2, (h - body_h) // 2
        screen = (bx, by + chrome, bx + body_w, by + body_h)
        return screen, (bx, by, bx + body_w, by + body_h), theme.px(20)
    # none: the bare capture with a shadow, centred at 0.86 of the frame
    body_w = int(w * 0.86)
    body_h = int(h * 0.82)
    bx, by = (w - body_w) // 2, (h - body_h) // 2
    return (bx, by, bx + body_w, by + body_h), (bx, by, bx + body_w, by + body_h), theme.px(12)


def _draw_body(image, draw, frame, body, screen, bezel, url, accent):
    """Draw the device shell around the screen rectangle."""
    ink = theme.INK
    # A device shell is a physical object, so it stays dark in both modes rather than
    # inverting. On a dark page the near-black body would vanish into the field, so it
    # lifts to a slate that still reads as hardware.
    shell = (58, 64, 78) if theme.ACTIVE.mode == "dark" else (28, 32, 42)
    bx0, by0, bx1, by1 = body
    if frame in ("phone", "tablet"):
        draw.rounded_rectangle(body, radius=bezel + theme.px(20), fill=shell)
        if frame == "phone":
            # a pill cutout at the top
            cx = (bx0 + bx1) // 2
            draw.rounded_rectangle((cx - theme.px(60), by0 + theme.px(24), cx + theme.px(60), by0 + theme.px(44)),
                                   radius=theme.px(10), fill=(12, 14, 20))
            # side buttons
            draw.rounded_rectangle((bx1 - theme.px(2), by0 + theme.px(140), bx1 + theme.px(6), by0 + theme.px(240)),
                                   radius=theme.px(3), fill=shell)
        else:
            # home indicator dot for the tablet
            draw.ellipse((bx1 - bezel + theme.px(6), (by0 + by1) // 2 - theme.px(8),
                          bx1 - bezel + theme.px(22), (by0 + by1) // 2 + theme.px(8)), outline=(90, 96, 110), width=2)
    elif frame == "laptop":
        draw.rounded_rectangle(body[:2] + (body[2], body[3] - theme.px(60)), radius=theme.px(20), fill=shell)
        # the wedge base
        base_top = body[3] - theme.px(60)
        draw.rounded_rectangle((bx0 - theme.px(60), base_top, bx1 + theme.px(60), base_top + theme.px(40)),
                               radius=theme.px(16), fill=(60, 66, 78))
        draw.rounded_rectangle((( bx0 + bx1)//2 - theme.px(70), base_top, (bx0+bx1)//2 + theme.px(70), base_top + theme.px(14)),
                               radius=theme.px(7), fill=(40, 44, 54))
    elif frame == "browser":
        draw.rounded_rectangle(body, radius=theme.px(16), fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)
        chrome_b = (bx0, by0, bx1, screen[1])
        draw.rounded_rectangle((bx0, by0, bx1, by0 + theme.px(84)), radius=theme.px(16), fill=theme.CHROME_BAR)
        draw.rectangle((bx0, by0 + theme.px(40), bx1, screen[1]), fill=theme.CHROME_BAR)
        for off, col in ((0, (255, 95, 87)), (34, (255, 189, 46)), (68, (39, 201, 63))):
            draw.ellipse((bx0 + theme.px(28) + theme.px(off), by0 + theme.px(24),
                          bx0 + theme.px(46) + theme.px(off), by0 + theme.px(42)), fill=col)
        # the URL bar with the real URL, which the honesty rule wants readable
        bar = (bx0 + theme.px(150), by0 + theme.px(18), bx1 - theme.px(60), by0 + theme.px(58))
        draw.rounded_rectangle(bar, radius=theme.px(20), fill=theme.PANEL, outline=(210, 216, 226), width=2)
        if url:
            draw.text((bar[0] + theme.px(24), by0 + theme.px(24)), url, font=theme.CHROME, fill=theme.INK_SOFT)
    elif frame == "terminal":
        draw.rounded_rectangle(body, radius=theme.px(20), fill=(24, 27, 36))
        draw.rounded_rectangle((bx0, by0, bx1, by0 + theme.px(66)), radius=theme.px(20), fill=(38, 42, 54))
        draw.rectangle((bx0, by0 + theme.px(33), bx1, by0 + theme.px(66)), fill=(38, 42, 54))
        for off, col in ((0, (255, 95, 87)), (34, (255, 189, 46)), (68, (39, 201, 63))):
            draw.ellipse((bx0 + theme.px(28) + theme.px(off), by0 + theme.px(22),
                          bx0 + theme.px(44) + theme.px(off), by0 + theme.px(38)), fill=col)


@style.scene("device")
def prepare(segment, project, work, base, style_, palette):
    accent = palette["accent"]
    frame = segment.get("frame", "phone")
    canvas = theme.CANVAS

    # get the picture to mount, and the boxes and texts that go with it
    if "file" in segment:
        shot_img = Image.open(segment["file"]).convert("RGB")
        shots = [shot_img]
        raw_boxes: list = []
        texts: list = []
        url = segment.get("url", "")
    else:
        url = segment.get("url")
        if not url:
            raise RuntimeError(
                f"device scene {segment.get('name')} needs a url to capture or a file to mount"
            )
        cap = web.capture(
            url, work, segment["name"], segment["section"],
            segment.get("items", "data-step"),
            tuple(segment.get("viewport", (390, 844) if frame == "phone" else web.VIEWPORT)),
            segment.get("wait_ms", 400),
        )
        shots = cap.images
        raw_boxes = cap.boxes
        texts = cap.texts

    screen, body, bezel = _screen_rect(frame, canvas, 1.0)
    sx0, sy0, sx1, sy1 = screen
    inner_w, inner_h = sx1 - sx0, sy1 - sy0
    src_w, src_h = shots[-1].size
    # scale the shot to the screen width, top-anchored so a tall page shows its head
    scale = inner_w / src_w
    drawn_h = min(inner_h, round(src_h * scale))
    count = max(1, len(raw_boxes))

    def page_for(visible: int) -> Page:
        image = base.copy()
        bg.drop_shadow(image, body, radius=bezel + theme.px(10))
        draw = ImageDraw.Draw(image)
        _draw_body(image, draw, frame, body, screen, bezel, url, accent)
        shot = shots[min(visible, len(shots) - 1)] if len(shots) > 1 else shots[0]
        placed = shot.resize((inner_w, round(src_h * scale)), Image.LANCZOS)
        crop = placed.crop((0, 0, inner_w, drawn_h))
        image.paste(crop, (sx0, sy0))
        # Box transform: web capture boxes are CSS pixels relative to the section, and the
        # shot is CSS * web.SCALE pixels wide. `scale` maps shot pixels into the screen, so
        # a CSS box moves by web.SCALE * scale and then shifts to the screen origin, exactly
        # as the picture did. Get this wrong and the marker lands off the element.
        boxes = []
        for b in raw_boxes:
            boxes.append((
                round(sx0 + b[0] * web.SCALE * scale),
                round(sy0 + b[1] * web.SCALE * scale),
                round(sx0 + b[2] * web.SCALE * scale),
                round(sy0 + b[3] * web.SCALE * scale),
            ))
        if not boxes:
            boxes = [screen]
        return Page(image=image, window=body, row_boxes=boxes)

    def resolve(needle: str) -> list[int]:
        return [i for i, t in enumerate(texts) if needle.lower() in t.lower()][:1]

    return page_for, count, resolve
