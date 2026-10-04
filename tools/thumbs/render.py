#!/usr/bin/env python3
"""Render the YouTube thumbnails for Zero to Shielded, one per episode.

    python3 tools/thumbs/render.py [out_dir]      # default /tmp/zts-thumbs

Each thumbnail is an HTML page in the site's own look (Inter, gold #F4B728 on deep ink,
cream text), rendered by headless Chromium at 1280x720 CSS pixels and device scale 3, so
the file is 3840x2160. It is then saved as a JPEG under 2 MB, the cap on YouTube's mobile
upload path. The headline is at most three words and fills about half the width, so it
still reads at sidebar size (about 168 px wide). A sidebar-size copy is written beside
each one so it can be checked by eye.
"""
from __future__ import annotations

import html
import io
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
# embedded: a file:// font does not load into a set_content page
FONT = "data:font/woff2;base64," + __import__("base64").b64encode((ROOT / "site/fonts/InterVariable.woff2").read_bytes()).decode()
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/zts-thumbs")

# headline lines (large), subline (one line), the mark inside the shield, the chip text
EPISODES = {
    "e0": (["Zero to", "Shielded"], "Your first private Zcash payment", "play", "Trailer · 5 short videos"),
    "e1": (["Wallet", "setup"], "Install Zodl. Back up your phrase.", "1", "Episode 1 of 5"),
    "e2": (["Getting", "ZEC"], "Swap in the app or buy on an exchange", "2", "Episode 2 of 5"),
    "e3": (["Shield", "your ZEC"], "Shielding and unshielding in Zodl", "3", "Episode 3 of 5"),
    "e4": (["Send &", "receive"], "Your first shielded payment", "4", "Episode 4 of 5"),
    "e5": (["Stay", "private"], "Five habits that keep it private", "5", "Episode 5 of 5"),
}

SHIELD = "M120 8 L224 44 V120 C224 186 180 232 120 254 C60 232 16 186 16 120 V44 Z"

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Inter; src: url("{font}") format("woff2"); font-weight: 100 900; }}
* {{ margin: 0; box-sizing: border-box; }}
html, body {{ width: 1280px; height: 720px; overflow: hidden; }}
body {{
  font-family: Inter, sans-serif; color: #F5F1E6; position: relative;
  background:
    radial-gradient(900px 620px at 78% 46%, rgb(244 183 40 / .20), transparent 62%),
    radial-gradient(700px 500px at 8% 0%, rgb(122 162 255 / .10), transparent 60%),
    linear-gradient(160deg, #121A30 0%, #0B0F1A 70%);
}}
.grain {{ position: absolute; inset: 0; opacity: .5;
  background-image: radial-gradient(rgb(255 255 255 / .05) 1px, transparent 1px); background-size: 6px 6px; }}
.left {{ position: absolute; left: 72px; top: 64px; bottom: 60px; width: 760px;
  display: flex; flex-direction: column; }}
.series {{ display: flex; align-items: center; gap: 14px; font-weight: 800; font-size: 30px;
  letter-spacing: .14em; text-transform: uppercase; color: #F4B728; }}
.series i {{ width: 44px; height: 6px; border-radius: 3px; background: #F4B728; display: block; }}
h1 {{ margin-top: 30px; font-weight: 900; font-size: {size}px; line-height: .94; letter-spacing: -.035em;
  text-shadow: 0 6px 30px rgb(0 0 0 / .45); }}
h1 span {{ display: block; }}
h1 span.gold {{ color: #F4B728; }}
.sub {{ margin-top: 30px; font-weight: 600; font-size: 38px; line-height: 1.2; color: #D9D3C3; max-width: 740px; }}
.chip {{ margin-top: auto; align-self: flex-start; font-weight: 800; font-size: 30px; color: #141826;
  background: #F4B728; padding: 12px 24px; border-radius: 999px; }}
.shield {{ position: absolute; right: 70px; top: 50%; width: 400px; height: 440px; transform: translateY(-50%);
  filter: drop-shadow(0 24px 60px rgb(244 183 40 / .35)); }}
.shield text {{ font-family: Inter, sans-serif; font-weight: 900; }}
</style></head><body><div class="grain"></div>
<div class="left">
  <div class="series"><i></i>Zero to Shielded</div>
  <h1>{lines}</h1>
  <div class="sub">{sub}</div>
  <div class="chip">{chip}</div>
</div>
<svg class="shield" viewBox="0 0 240 262" aria-hidden="true">
  <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#FFD36B"/><stop offset="1" stop-color="#E09A00"/></linearGradient></defs>
  <path d="{shield}" fill="url(#g)" stroke="#FFE7A8" stroke-width="5" stroke-linejoin="round"/>
  <path d="{shield}" fill="none" stroke="#141826" stroke-opacity=".18" stroke-width="2" transform="translate(120 131) scale(.86) translate(-120 -131)"/>
  {mark}
</svg>
</body></html>"""


def page_html(lines, sub, mark, chip):
    longest = max(len(l) for l in lines)
    size = 168 if longest <= 7 else 150 if longest <= 9 else 132
    spans = "".join(
        f'<span class="{"gold" if i == len(lines) - 1 else ""}">{html.escape(l)}</span>' for i, l in enumerate(lines))
    return PAGE.format(font=FONT, size=size, lines=spans, sub=html.escape(sub), chip=html.escape(chip),
                       shield=SHIELD, mark=mark_svg(mark))


def mark_svg(mark):
    if mark == "play":  # the trailer: a play triangle, optically centred
        return '<path d="M98 82 L170 128 L98 174 Z" fill="#141826" stroke="#141826" stroke-width="10" stroke-linejoin="round"/>'
    return f'<text x="120" y="176" text-anchor="middle" font-size="150" fill="#141826">{html.escape(mark)}</text>'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 720}, device_scale_factor=3)
        for eid, (lines, sub, mark, chip) in EPISODES.items():
            pg.set_content(page_html(lines, sub, mark, chip), wait_until="load")
            pg.evaluate("document.fonts.ready.then(() => document.fonts.check('900 100px Inter'))") or sys.exit("Inter did not load")
            pg.wait_for_timeout(300)
            img = Image.open(io.BytesIO(pg.screenshot(type="png"))).convert("RGB")
            assert img.size == (3840, 2160), img.size
            dst = OUT / f"thumb-{eid}.jpg"
            for q in (92, 88, 84, 80, 75):
                img.save(dst, "JPEG", quality=q, optimize=True, progressive=True)
                if dst.stat().st_size < 2 * 1024 * 1024:
                    break
            img.resize((336, 189), Image.LANCZOS).save(OUT / f"thumb-{eid}-sidebar.png")
            print(f"{dst}  {img.size[0]}x{img.size[1]}  {dst.stat().st_size // 1024} KB  q={q}")
        b.close()


if __name__ == "__main__":
    main()
