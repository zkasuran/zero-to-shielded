"""Capture a real web page and show a viewport of it in the floating window.

The kit's rule is that everything on screen is real. A terminal scene runs a command
and slices its stdout; a code card reads a file. This does the same for a page: it
drives a real Chromium at a fixed viewport, screenshots the section named by the
segment and keeps every screenshot in `artifacts/` as the receipt. Nothing is drawn
by hand and no text is retyped.

The page cooperates in exactly two ways, which is the whole contract:

  * the section to show has an `id`, named by the segment's `section`
  * inside it, each thing worth revealing one at a time carries `data-step`, and the
    page exposes `window.setReveal(k)` which reveals the first k of them without
    moving anything. Reveal by opacity, never by `display`, because the boxes this
    module hands back to the zoom are measured once at full reveal and a layout that
    reflows between states would leave the marker pointing at the wrong line.

Focus needles are substrings of an item's own text, the same as a terminal scene, so
a project file reads the same whichever kind of scene it is pointing at.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

import theme

VIEWPORT = (1180, 600)
SCALE = 2
CONTENT_WIDTH = 2000
CHROME = 66
PAD = 40
FOOTER_BAND = 84


@dataclass
class Shot:
    """Every reveal state of one section, plus the boxes and text of its items."""

    images: list[Image.Image]
    boxes: list[tuple[float, float, float, float]]
    texts: list[str]
    size: tuple[int, int]


def capture(url: str, artifacts: Path, name: str, section: str, items: str,
            viewport: tuple[int, int] = VIEWPORT, wait_ms: int = 400,
            hide: list[str] | None = None) -> Shot:
    """Screenshot one section of a real page once per reveal state.

    Two escape hatches exist for a page we do not own, because the citable live URL
    is sometimes somebody else's. `items` may be a full CSS selector when it is
    written as `css:<selector>`, since a third-party page has no `data-step`, and a
    page with no `window.setReveal` is captured at full reveal for every state
    instead of failing. Nothing else changes: the boxes, the texts and the receipt
    are measured off the real page exactly the same way.
    """
    from playwright.sync_api import sync_playwright

    item_selector = items[4:] if items.startswith("css:") else f"[{items}]"
    reveal = (
        "([k, scope]) => { if (typeof window.setReveal === 'function') "
        "{ window.setReveal(k, scope); return true; } return false; }"
    )

    artifacts.mkdir(parents=True, exist_ok=True)
    images: list[Image.Image] = []
    with sync_playwright() as driver:
        browser = driver.chromium.launch()
        page = browser.new_page(viewport={"width": viewport[0], "height": viewport[1]},
                                device_scale_factor=SCALE)
        # A live capture rides the real network, so a transient blip (ERR_NETWORK_CHANGED,
        # a slow TLS handshake) can fail one goto that succeeds on the next try. Retry the
        # navigation a few times with a short backoff rather than losing a whole render.
        last_error = None
        for attempt in range(4):
            try:
                page.goto(url, wait_until="load", timeout=45000)
                last_error = None
                break
            except Exception as error:  # noqa: BLE001 - retried, re-raised on the last attempt
                last_error = error
                page.wait_for_timeout(1500 * (attempt + 1))
        if last_error is not None:
            raise RuntimeError(f"{name}: could not load {url} after retries: {last_error}")
        page.wait_for_timeout(wait_ms)
        # A page we do not control often floats a position:sticky or fixed nav over the
        # top of the section once it is scrolled to block:start, and element.screenshot
        # re-aligns the element to the top so the overlay lands on the content. Hiding
        # those bars for the capture removes the occlusion without changing the section's
        # own layout, because a sticky bar sits outside the section. Opt in per segment.
        if hide:
            page.add_style_tag(
                content=" ".join(f"{selector}{{display:none !important;}}" for selector in hide)
            )
            page.wait_for_timeout(160)
        target = page.locator(section)
        if target.count() != 1:
            raise RuntimeError(f"{name}: {section} matched {target.count()} elements, wanted 1")
        page.evaluate("(id) => document.querySelector(id).scrollIntoView({block: 'start'})", section)
        page.wait_for_timeout(120)
        step = page.locator(f"{section} >> {item_selector}")
        count = step.count()
        if count == 0:
            raise RuntimeError(f"{name}: no {item_selector} items inside {section}")

        page.evaluate(reveal, [count, section])
        page.wait_for_timeout(160)
        frame = target.bounding_box()
        if frame is None:
            raise RuntimeError(f"{name}: {section} has no box, so it is not visible")
        # Measure item rects relative to the section with getBoundingClientRect in one
        # evaluate. Playwright's own bounding_box() reports the section top a few px lower
        # than its real client rect (seen here: 108.7 vs 92.7), while element.screenshot()
        # clips from the real client-rect top. Normalising the item boxes by the Playwright
        # section box therefore slid every marker up by that gap, so the highlighter and
        # cursor landed on the heading above the field instead of on the field. Measuring
        # the section and its items from the same getBoundingClientRect basis puts the
        # boxes back on the screenshot's own origin.
        measured = page.evaluate(
            """([sec, sel]) => {
                const s = document.querySelector(sec).getBoundingClientRect();
                return [...document.querySelectorAll(sec + ' ' + sel)].map((el) => {
                    const r = el.getBoundingClientRect();
                    return [r.left - s.left, r.top - s.top, r.right - s.left, r.bottom - s.top];
                });
            }""",
            [section, item_selector],
        )
        if len(measured) != count:
            raise RuntimeError(f"{name}: measured {len(measured)} boxes for {count} items")
        boxes: list[tuple[float, float, float, float]] = [
            (float(r[0]), float(r[1]), float(r[2]), float(r[3])) for r in measured
        ]
        texts: list[str] = [
            " ".join((step.nth(index).inner_text() or "").split()) for index in range(count)
        ]

        for visible in range(count + 1):
            page.evaluate(reveal, [visible, section])
            page.wait_for_timeout(120)
            shot = artifacts / f"{name}-reveal-{visible}.png"
            target.screenshot(path=str(shot))
            images.append(Image.open(shot).convert("RGB"))
        browser.close()

    (artifacts / f"{name}.boxes.json").write_text(
        json.dumps({"url": url, "section": section, "items": items, "viewport": list(viewport),
                    "scale": SCALE, "boxes": boxes, "texts": texts}, indent=2) + "\n",
        encoding="utf-8",
    )
    return Shot(images=images, boxes=boxes, texts=texts, size=images[-1].size)


@dataclass
class Page:
    image: Image.Image
    window: tuple[int, int, int, int]
    boxes: list[tuple[int, int, int, int]]
    prompt_box: tuple[int, int, int, int]


def _layout(shot: Shot, footer: bool) -> tuple[float, tuple[int, int], tuple[int, int, int, int]]:
    """Scale the screenshot to the window and centre the window on the canvas."""
    factor = CONTENT_WIDTH / shot.size[0]
    content = (CONTENT_WIDTH, round(shot.size[1] * factor))
    ceiling = theme.CANVAS[1] - 2 * 110 - CHROME - PAD - (FOOTER_BAND if footer else PAD)
    if content[1] > ceiling:
        factor = ceiling / shot.size[1]
        content = (round(shot.size[0] * factor), ceiling)
    width = content[0] + 2 * PAD
    height = CHROME + PAD + content[1] + (FOOTER_BAND if footer else PAD)
    left = (theme.CANVAS[0] - width) // 2
    top = (theme.CANVAS[1] - height) // 2
    return factor, content, (left, top, left + width, top + height)


def card(base: Image.Image, shot: Shot, visible: int, header: str, footer: str | None,
         accent: tuple[int, int, int]) -> Page:
    """The page screenshot in the same floating window every other scene uses."""
    import bg

    factor, content, box = _layout(shot, footer is not None)
    image = base.copy()
    bg.drop_shadow(image, box, radius=30)
    left, top, right, bottom = box
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=30, fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)
    draw.rounded_rectangle((left, top, right, top + CHROME), radius=30, fill=(244, 246, 250))
    draw.rectangle((left, top + 40, right, top + CHROME), fill=(244, 246, 250))
    for offset, colour in ((0, (255, 95, 87)), (34, (255, 189, 46)), (68, (39, 201, 63))):
        draw.ellipse((left + 34 + offset, top + 24, left + 52 + offset, top + 42), fill=colour)
    draw.text((left + 160, top + 22), header, font=theme.CHROME, fill=theme.INK_SOFT)

    shown = shot.images[max(0, min(visible, len(shot.images) - 1))]
    inner_left = left + PAD
    inner_top = top + CHROME + PAD // 2
    image.paste(shown.resize(content, Image.LANCZOS), (inner_left, inner_top))
    draw.rectangle((inner_left - 1, inner_top - 1, inner_left + content[0], inner_top + content[1]),
                   outline=(226, 231, 240), width=2)
    if footer is not None:
        draw.text((inner_left, bottom - 58), footer, font=theme.CHROME, fill=theme.INK_SOFT)

    scaled = factor * SCALE
    boxes = [
        (
            inner_left + round(item[0] * scaled),
            inner_top + round(item[1] * scaled),
            inner_left + round(item[2] * scaled),
            inner_top + round(item[3] * scaled),
        )
        for item in shot.boxes
    ]
    return Page(image=image, window=box, boxes=boxes,
                prompt_box=(inner_left, inner_top, inner_left + content[0], inner_top + 60))

