"""One place for the look.

Bright is the default: a vivid gradient field with a near-white window floating on
it, dark ink for the text, and saturated but dark enough accent colours that the
syntax highlighting still passes contrast on a light panel.

Every name below is a live value rather than a frozen constant. `configure(style)` rebinds
them from a resolved `style.Style`, so geometry, type, ink and the colour rules all come
from the project file. With no `style` block a project resolves to the numbers the kit
shipped with, which is why the existing set rebuilds unchanged.

Read these through the module (`theme.CANVAS`), never capture them at import time
(`WIDTH, HEIGHT = theme.CANVAS` at module level), or a build on a different aspect draws
at the previous build's size.
"""

from __future__ import annotations

from PIL import ImageFont

import style as style_module

ACTIVE: style_module.Style = style_module.Style()

CANVAS = (2560, 1440)
OUTPUT = (1920, 1080)
FPS = 30

SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"

_FONT_CACHE: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Cached, because a renderer asks for the same face and size thousands of times."""
    key = (path, int(size))
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(path, int(size))
    return _FONT_CACHE[key]


CODE = font(MONO, 30)
CODE_BOLD = font(MONO_BOLD, 30)
CHROME = font(MONO, 25)
CARD = font(SANS_BOLD, 82)
CARD_MONO = font(MONO, 58)
KICKER = font(SANS_BOLD, 34)
FOOTER = font(SANS, 30)
PANEL_LABEL = font(SANS_BOLD, 34)
PANEL_VALUE = font(MONO, 30)
BUBBLE = font(SANS, 31)
BUBBLE_WHO = font(SANS_BOLD, 24)
DOC_H1 = font(SANS_BOLD, 44)
DOC_KEY = font(SANS, 29)
DOC_VALUE = font(SANS_BOLD, 32)
CODE_SMALL = font(MONO, 27)
# burned in narration captions, drawn on the delivered frame rather than the canvas,
# so this size is in output pixels and not canvas pixels
CAPTION = font(SANS, 34)
CAPTION_BAND = 62
CAPTION_WIDTH = 1740
CAPTION_RESERVE = CAPTION_BAND + 8  # band plus the progress bar

LINE_HEIGHT = 39
WINDOW_MARGIN = 130
PAD_X = 56
PAD_TOP = 96

PANEL = (252, 253, 255)
PANEL_EDGE = (255, 255, 255)
CHROME_BAR = (244, 246, 250)
INK = (26, 33, 46)
INK_SOFT = (104, 116, 134)
CARD_INK = (23, 28, 40)
CARD_SOFT = (74, 84, 102)

GREEN = (13, 122, 76)
RED = (188, 44, 48)
AMBER = (162, 92, 0)
BLUE = (28, 92, 190)
VIOLET = (108, 62, 200)


def px(value: float) -> int:
    """A reference-canvas measurement in the active build's canvas pixels.

    A module-level shortcut for `ACTIVE.px`, so a renderer can scale a constant without
    threading the Style through every call. New renderers use this for every pixel that is
    not already a rebinding constant, so a 9:16 or a high-quality build gets the same
    optical size rather than the same pixel count.
    """
    return ACTIVE.px(value)


def type_px(name: str) -> int:
    """A named type size in the active build's canvas pixels."""
    return ACTIVE.type_px(name)


def configure(resolved: style_module.Style) -> style_module.Style:
    """Rebind every look constant from a resolved Style. Call once, before anything draws."""
    global ACTIVE, CANVAS, OUTPUT, FPS
    global SANS, SANS_BOLD, MONO, MONO_BOLD
    global CODE, CODE_BOLD, CHROME, CARD, CARD_MONO, KICKER, FOOTER
    global PANEL_LABEL, PANEL_VALUE, BUBBLE, BUBBLE_WHO, DOC_H1, DOC_KEY, DOC_VALUE, CODE_SMALL
    global CAPTION, CAPTION_BAND, CAPTION_WIDTH, CAPTION_RESERVE
    global LINE_HEIGHT, WINDOW_MARGIN, PAD_X, PAD_TOP
    global PANEL, PANEL_EDGE, CHROME_BAR, INK, INK_SOFT, CARD_INK, CARD_SOFT
    global GREEN, RED, AMBER, BLUE, VIOLET

    ACTIVE = resolved
    CANVAS, OUTPUT, FPS = resolved.canvas, resolved.output, resolved.fps
    SANS = resolved.fonts["sans"]
    SANS_BOLD = resolved.fonts["sans_bold"]
    MONO = resolved.fonts["mono"]
    MONO_BOLD = resolved.fonts["mono_bold"]

    CODE = font(MONO, resolved.type_px("code"))
    CODE_BOLD = font(MONO_BOLD, resolved.type_px("code_bold"))
    CODE_SMALL = font(MONO, resolved.type_px("code_small"))
    CHROME = font(MONO, resolved.type_px("chrome"))
    CARD = font(SANS_BOLD, resolved.type_px("card"))
    CARD_MONO = font(MONO, resolved.type_px("card_mono"))
    KICKER = font(SANS_BOLD, resolved.type_px("kicker"))
    FOOTER = font(SANS, resolved.type_px("footer"))
    PANEL_LABEL = font(SANS_BOLD, resolved.type_px("panel_label"))
    PANEL_VALUE = font(MONO, resolved.type_px("panel_value"))
    BUBBLE = font(SANS, resolved.type_px("bubble"))
    BUBBLE_WHO = font(SANS_BOLD, resolved.type_px("bubble_who"))
    DOC_H1 = font(SANS_BOLD, resolved.type_px("doc_h1"))
    DOC_KEY = font(SANS, resolved.type_px("doc_key"))
    DOC_VALUE = font(SANS_BOLD, resolved.type_px("doc_value"))

    # Captions are drawn after the crop, so they scale with the delivered frame and not
    # with the canvas.
    caption_scale = resolved.output[1] / 1080
    CAPTION = font(SANS, max(12, round(resolved.caption["font_size"] * caption_scale)))
    CAPTION_BAND = max(1, round(resolved.caption["band"] * caption_scale))
    CAPTION_WIDTH = max(120, round(resolved.output[0] * resolved.caption["width_ratio"]))
    CAPTION_RESERVE = resolved.caption_reserve

    LINE_HEIGHT = resolved.metric("line_height")
    WINDOW_MARGIN = resolved.metric("window_margin")
    PAD_X = resolved.metric("pad_x")
    PAD_TOP = resolved.metric("pad_top")

    PANEL = resolved.ink["panel"]
    PANEL_EDGE = resolved.ink["panel_edge"]
    CHROME_BAR = resolved.ink["chrome_bar"]
    INK = resolved.ink["ink"]
    INK_SOFT = resolved.ink["ink_soft"]
    CARD_INK = resolved.ink["card_ink"]
    CARD_SOFT = resolved.ink["card_soft"]
    GREEN = resolved.ink["green"]
    RED = resolved.ink["red"]
    AMBER = resolved.ink["amber"]
    BLUE = resolved.ink["blue"]
    VIOLET = resolved.ink["violet"]
    _refresh_dimensions()
    return resolved


def _refresh_dimensions() -> None:
    """Push the new canvas into every renderer that cached it at import time.

    Eight renderers open with `WIDTH, HEIGHT = theme.CANVAS`, which is a module-level
    binding made once when the module is first imported. Rebinding `theme.CANVAS` alone
    would leave every one of them drawing at whatever size the first build used, which on
    a second build at a different aspect is silently the wrong picture rather than an
    error. So the rebind is pushed rather than pulled.

    Any module inside the kit that carries WIDTH and HEIGHT is refreshed, so a renderer
    added later is covered without being listed here. Modules imported after configure()
    pick the values up on their own and are unaffected by this.
    """
    import sys
    from pathlib import Path

    here = Path(__file__).resolve().parent
    for module in list(sys.modules.values()):
        path = getattr(module, "__file__", None)
        if not path or Path(path).resolve().parent != here or module is sys.modules[__name__]:
            continue
        if hasattr(module, "WIDTH") and hasattr(module, "HEIGHT"):
            module.WIDTH, module.HEIGHT = CANVAS
        if hasattr(module, "OUT_W") and hasattr(module, "OUT_H"):
            module.OUT_W, module.OUT_H = OUTPUT
        if hasattr(module, "ASPECT"):
            module.ASPECT = OUTPUT[0] / OUTPUT[1]

PALETTES: dict[str, dict] = {
    # Added 2026-09-18 for the KeeperHub bounty cut, because the free list was empty
    # again and the rule is to add rather than double up. A radial pool crossing a
    # bright pale lime into a deep green-teal. Every other green is either a diagonal
    # (vine, razor, loop) or a light mint pool (fern), so this is the only dark green
    # radial by field and by RGB. The accent is a dark olive that no other theme
    # carries, well clear of the refusal red so a failing line still reads as red,
    # and the mark is a pale lime that multiplies over dark ink without hiding it.
    "keeper": {
        "field": "radial",
        "top": (240, 252, 202),
        "bottom": (26, 104, 88),
        "accent": (100, 108, 14),
        "mark": (228, 248, 176),
        "blobs": [
            ((0.18, 0.18), 0.52, (214, 246, 168), 0.85),
            ((0.86, 0.22), 0.44, (128, 206, 150), 0.68),
            ((0.6, 0.9), 0.46, (168, 228, 186), 0.55),
        ],
    },

    # Added 2026-09-18 for the Uniswap V4 Hook Automation Router (main track). The
    # free list was empty again, so a new palette rather than a reuse. A diagonal
    # pale-blush into deep magenta, Uniswap's own brand family, which no other theme
    # carries: berry is a darker wine radial and amethyst/iris/lilac are violet, so
    # this true pink-magenta (~325 hue) is distinct by eye and by RGB. Accent is a
    # deep magenta (168, 20, 108) readable on the near-white recording panel and well
    # clear of the refusal red, and the mark is a pale blush that multiplies over dark
    # monospace without tinting it.
    "unipink": {
        "field": "diagonal",
        "top": (252, 226, 244),
        "bottom": (196, 30, 128),
        "accent": (168, 20, 108),
        "mark": (252, 218, 240),
        "blobs": [
            ((0.18, 0.18), 0.52, (250, 200, 232), 0.85),
            ((0.86, 0.22), 0.44, (224, 108, 178), 0.68),
            ((0.6, 0.9), 0.46, (240, 170, 214), 0.55),
        ],
    },

    # Added 2026-09-10 for the Priors video (Sibyl Labs Hackathon). The free list was
    # out, so a new palette rather than a reuse. A deep teal-cyan vertical field that no
    # other theme uses: the greens (mint, moss, fern) are yellow-greens and the blues
    # (cobalt, signal, iris) are indigo, so this blue-green (~185 hue) is distinct by eye
    # and by RGB. Accent is a dark teal (8, 94, 112) readable on the near-white panel,
    # the mark a pale cyan that multiplies over dark ink without hiding a red refusal.
    # Added 2026-09-18 for Mandate, because the free list had run out. A deep
    # ink-blue field with a warm ember accent: the accent is the one warm thing
    # on a cold page, which is how the product's own UI reads. Dark enough to
    # sit on the near-white recording panel, mark pale enough to multiply over
    # dark monospace without tinting it.
    "ledger": {
        "field": "diagonal",
        "top": (214, 226, 248),
        "bottom": (86, 108, 158),
        "accent": (142, 52, 18),
        "mark": (252, 226, 206),
        "blobs": [
            ((0.22, 0.2), 0.54, (186, 204, 240), 0.85),
            ((0.84, 0.28), 0.42, (150, 172, 218), 0.66),
            ((0.58, 0.9), 0.48, (206, 190, 214), 0.5),
        ],
    },
    "keystone": {
        "field": "vertical",
        "top": (210, 246, 248),
        "bottom": (14, 116, 132),
        "accent": (8, 94, 112),
        "mark": (196, 240, 244),
        "blobs": [
            ((0.16, 0.18), 0.52, (150, 226, 232), 0.85),
            ((0.86, 0.2), 0.44, (90, 194, 208), 0.7),
            ((0.62, 0.9), 0.46, (120, 214, 224), 0.55),
        ],
    },

    # Added 2026-09-09 for the Muster BNB Build the Era video. The free list had run
    # out, and the rule is to add a palette rather than double up. A radial pool of
    # warm amber (BNB Chain's brand family) that no other theme uses as a radial: the
    # accent is a dark amber (150, 96, 0) readable on the near-white panel, distinct
    # from honey's (162,92,0) diagonal and sundown's orange, and the mark is a pale
    # gold that multiplies over dark ink without hiding red refusals. Checked by RGB
    # and by field shape against every existing theme.
    "amber": {
        "field": "radial",
        "top": (255, 246, 214),
        "bottom": (245, 194, 66),
        "accent": (150, 96, 0),
        "mark": (255, 232, 168),
        "blobs": [
            ((0.16, 0.18), 0.52, (255, 226, 140), 0.85),
            ((0.88, 0.2), 0.44, (245, 205, 96), 0.7),
            ((0.66, 0.9), 0.46, (255, 214, 120), 0.55),
        ],
    },

    # Added 2026-09-08 for voice-preflight. The free list had run out, and the rule
    # is to add a palette rather than double up. Diagonal pale mint into warm coral,
    # a burgundy accent no other theme carries (checked against all 24 by eye and by
    # RGB), and a pale peach mark that multiplies over dark ink without hiding red.
    "chime": {
        "field": "diagonal",
        "top": (232, 252, 240),
        "bottom": (255, 190, 168),
        "accent": (140, 30, 58),
        "mark": (255, 226, 210),
        "blobs": [
            ((0.18, 0.2), 0.5, (200, 246, 226), 0.85),
            ((0.86, 0.24), 0.44, (255, 196, 172), 0.7),
            ((0.6, 0.92), 0.46, (255, 214, 196), 0.55),
        ],
    },
    "sundown": {
        "field": "diagonal",
        "top": (255, 216, 170),
        "bottom": (198, 174, 255),
        "accent": (198, 84, 36),
        "mark": (255, 214, 150),
        "blobs": [
            ((0.14, 0.16), 0.52, (255, 190, 120), 0.85),
            ((0.88, 0.14), 0.42, (176, 150, 255), 0.72),
            ((0.70, 0.94), 0.46, (255, 170, 140), 0.55),
        ],
    },
    "citrus": {
        "top": (255, 232, 186),
        "bottom": (255, 176, 154),
        "accent": (222, 88, 44),
        "mark": (255, 214, 120),
        "blobs": [
            ((0.14, 0.16), 0.52, (255, 205, 120), 0.85),
            ((0.88, 0.12), 0.40, (255, 158, 170), 0.70),
            ((0.72, 0.94), 0.46, (168, 214, 255), 0.55),
        ],
    },
    "mint": {
        "top": (206, 246, 232),
        "bottom": (150, 214, 255),
        "accent": (14, 132, 128),
        "mark": (168, 240, 214),
        "blobs": [
            ((0.16, 0.14), 0.50, (170, 240, 214), 0.85),
            ((0.86, 0.18), 0.42, (150, 210, 255), 0.70),
            ((0.66, 0.92), 0.44, (232, 240, 170), 0.55),
        ],
    },
    "lilac": {
        "top": (233, 220, 255),
        "bottom": (255, 198, 220),
        "accent": (124, 58, 190),
        "mark": (226, 206, 255),
        "blobs": [
            ((0.18, 0.18), 0.50, (214, 196, 255), 0.85),
            ((0.86, 0.14), 0.40, (255, 196, 226), 0.70),
            ((0.70, 0.92), 0.46, (196, 226, 255), 0.55),
        ],
    },
    "coral": {
        "field": "diagonal",
        "top": (255, 228, 224),
        "bottom": (255, 178, 202),
        "accent": (196, 48, 92),
        "mark": (255, 200, 214),
        "blobs": [
            ((0.10, 0.86), 0.54, (255, 186, 176), 0.85),
            ((0.82, 0.10), 0.44, (255, 206, 226), 0.72),
            ((0.52, 0.48), 0.34, (255, 236, 196), 0.45),
        ],
    },
    "sky": {
        "field": "radial",
        "top": (222, 242, 255),
        "bottom": (172, 202, 255),
        "accent": (26, 96, 176),
        "mark": (178, 220, 255),
        "blobs": [
            ((0.50, 0.20), 0.56, (196, 230, 255), 0.85),
            ((0.12, 0.82), 0.44, (176, 200, 255), 0.68),
            ((0.90, 0.78), 0.40, (206, 246, 240), 0.55),
        ],
    },
    "moss": {
        "top": (230, 248, 206),
        "bottom": (168, 222, 192),
        "accent": (46, 112, 52),
        "mark": (204, 242, 176),
        "blobs": [
            ((0.20, 0.20), 0.50, (206, 244, 176), 0.85),
            ((0.84, 0.22), 0.42, (176, 230, 208), 0.70),
            ((0.62, 0.90), 0.46, (240, 240, 186), 0.52),
        ],
    },
    "honey": {
        "field": "diagonal",
        "top": (255, 244, 212),
        "bottom": (252, 210, 158),
        "accent": (150, 92, 16),
        "mark": (255, 228, 152),
        "blobs": [
            ((0.86, 0.16), 0.52, (255, 226, 158), 0.85),
            ((0.14, 0.74), 0.44, (250, 214, 186), 0.70),
            ((0.48, 0.34), 0.32, (255, 248, 214), 0.45),
        ],
    },
    "berry": {
        "field": "radial",
        "top": (255, 224, 246),
        "bottom": (222, 188, 255),
        "accent": (158, 42, 148),
        "mark": (250, 198, 244),
        "blobs": [
            ((0.44, 0.24), 0.54, (255, 202, 238), 0.85),
            ((0.86, 0.84), 0.44, (214, 186, 255), 0.70),
            ((0.10, 0.72), 0.40, (255, 224, 206), 0.50),
        ],
    },
    "slate": {
        "top": (230, 238, 252),
        "bottom": (192, 204, 236),
        "accent": (58, 74, 152),
        "mark": (202, 214, 255),
        "blobs": [
            ((0.22, 0.16), 0.50, (206, 220, 255), 0.85),
            ((0.84, 0.20), 0.42, (216, 226, 246), 0.66),
            ((0.66, 0.92), 0.46, (196, 234, 240), 0.52),
        ],
    },
    "tidal": {
        "field": "diagonal",
        "top": (206, 246, 250),
        "bottom": (255, 214, 186),
        "accent": (12, 104, 116),
        "mark": (176, 238, 244),
        "blobs": [
            ((0.14, 0.18), 0.54, (176, 236, 250), 0.85),
            ((0.88, 0.80), 0.46, (255, 200, 178), 0.72),
            ((0.56, 0.44), 0.34, (226, 248, 214), 0.44),
        ],
    },
    "aurora": {
        "field": "diagonal",
        "top": (210, 245, 232),
        "bottom": (255, 222, 196),
        "accent": (190, 74, 46),
        "mark": (255, 214, 182),
        "blobs": [
            ((0.16, 0.20), 0.52, (196, 240, 224), 0.85),
            ((0.86, 0.82), 0.46, (255, 208, 176), 0.72),
            ((0.54, 0.42), 0.34, (226, 214, 255), 0.44),
        ],
    },
    "ridge": {
        "field": "diagonal",
        "top": (255, 240, 200),
        "bottom": (210, 202, 248),
        "accent": (86, 58, 168),
        "mark": (255, 226, 158),
        "blobs": [
            ((0.14, 0.18), 0.54, (255, 224, 158), 0.85),
            ((0.88, 0.82), 0.46, (204, 196, 250), 0.72),
            ((0.54, 0.44), 0.34, (226, 236, 214), 0.44),
        ],
    },
    "vine": {
        "field": "diagonal",
        "top": (222, 244, 190),
        "bottom": (110, 200, 150),
        "accent": (24, 104, 60),
        "mark": (196, 238, 166),
        "blobs": [
            ((0.14, 0.18), 0.54, (196, 238, 160), 0.85),
            ((0.88, 0.82), 0.46, (140, 210, 170), 0.72),
            ((0.54, 0.44), 0.34, (226, 246, 200), 0.44),
        ],
    },
    "amethyst": {
        "field": "radial",
        "top": (238, 226, 255),
        "bottom": (196, 166, 236),
        "accent": (104, 48, 164),
        "mark": (226, 206, 250),
        "blobs": [
            ((0.46, 0.24), 0.54, (222, 196, 250), 0.85),
            ((0.86, 0.84), 0.44, (200, 170, 240), 0.70),
            ((0.10, 0.72), 0.40, (232, 214, 255), 0.50),
        ],
    },
    "cobalt": {
        "top": (222, 232, 255),
        "bottom": (168, 186, 248),
        "accent": (36, 64, 170),
        "mark": (200, 214, 255),
        "blobs": [
            ((0.20, 0.16), 0.50, (196, 214, 255), 0.85),
            ((0.84, 0.20), 0.42, (188, 202, 248), 0.66),
            ((0.66, 0.92), 0.46, (200, 224, 255), 0.52),
        ],
    },
    "razor": {
        "field": "diagonal",
        "top": (226, 250, 196),
        "bottom": (152, 236, 214),
        "accent": (13, 104, 78),
        "mark": (200, 244, 172),
        "blobs": [
            ((0.14, 0.18), 0.54, (202, 246, 166), 0.85),
            ((0.88, 0.82), 0.46, (150, 228, 206), 0.72),
            ((0.54, 0.44), 0.34, (224, 248, 200), 0.44),
        ],
    },
    "timber": {
        "field": "radial",
        "top": (255, 234, 194),
        "bottom": (240, 196, 150),
        "accent": (16, 108, 84),
        "mark": (255, 224, 158),
        "blobs": [
            ((0.50, 0.22), 0.56, (255, 220, 160), 0.85),
            ((0.14, 0.82), 0.44, (238, 190, 150), 0.68),
            ((0.90, 0.80), 0.40, (210, 226, 200), 0.50),
        ],
    },
    "loop": {
        "field": "diagonal",
        "top": (214, 250, 210),
        "bottom": (156, 210, 255),
        "accent": (12, 118, 98),
        "mark": (190, 244, 208),
        "blobs": [
            ((0.14, 0.18), 0.54, (190, 242, 198), 0.85),
            ((0.88, 0.82), 0.46, (170, 212, 255), 0.72),
            ((0.54, 0.44), 0.34, (226, 246, 222), 0.44),
        ],
    },
    "iris": {
        "field": "diagonal",
        "top": (216, 224, 255),
        "bottom": (204, 174, 240),
        "accent": (74, 72, 194),
        "mark": (214, 204, 252),
        "blobs": [
            ((0.14, 0.18), 0.54, (204, 212, 255), 0.85),
            ((0.88, 0.82), 0.46, (200, 170, 240), 0.72),
            ((0.54, 0.44), 0.34, (226, 222, 255), 0.44),
        ],
    },
    "fern": {
        "field": "radial",
        "top": (210, 246, 224),
        "bottom": (120, 206, 168),
        "accent": (13, 110, 84),
        "mark": (186, 240, 208),
        "blobs": [
            ((0.50, 0.22), 0.56, (188, 240, 212), 0.85),
            ((0.14, 0.82), 0.44, (150, 220, 190), 0.68),
            ((0.90, 0.80), 0.40, (206, 244, 224), 0.52),
        ],
    },
    "cipher": {
        "field": "diagonal",
        "top": (200, 244, 246),
        "bottom": (140, 196, 255),
        "accent": (11, 92, 130),
        "mark": (176, 236, 242),
        "blobs": [
            ((0.16, 0.20), 0.54, (170, 234, 240), 0.85),
            ((0.88, 0.80), 0.46, (150, 196, 255), 0.72),
            ((0.56, 0.46), 0.34, (198, 232, 236), 0.44),
        ],
    },
    "dusk": {
        "field": "radial",
        "top": (222, 214, 255),
        "bottom": (160, 180, 244),
        "accent": (38, 32, 120),
        "mark": (210, 220, 255),
        "blobs": [
            ((0.50, 0.24), 0.56, (210, 200, 255), 0.85),
            ((0.14, 0.80), 0.44, (174, 190, 244), 0.70),
            ((0.88, 0.76), 0.40, (196, 216, 255), 0.52),
        ],
    },
    "signal": {
        "field": "diagonal",
        "top": (214, 222, 255),
        "bottom": (198, 244, 226),
        "accent": (70, 82, 205),
        "mark": (206, 246, 230),
        "blobs": [
            ((0.16, 0.18), 0.52, (200, 212, 255), 0.85),
            ((0.86, 0.80), 0.46, (196, 186, 246), 0.70),
            ((0.58, 0.90), 0.40, (184, 244, 216), 0.50),
        ],
    },
    "nimparty": {
        "field": "radial",
        "top": (208, 255, 232),
        "bottom": (255, 242, 206),
        "accent": (0, 122, 74),
        "mark": (200, 246, 220),
        "blobs": [
            ((0.20, 0.22), 0.54, (170, 246, 210), 0.85),
            ((0.84, 0.30), 0.44, (255, 226, 150), 0.65),
            ((0.60, 0.88), 0.42, (150, 232, 236), 0.55),
        ],
    },
}
"""The theme roster. One theme per video, never reused across projects.

Every palette carries the gradient ends, the accent that colours titles, prompts,
cursor and progress bar, the highlighter ink, three soft blobs and an optional field
shape (`vertical` by default, or `diagonal` or `radial`), so two videos differ in the
shape of the light as well as its colour. Accents are dark enough to keep contrast on
the near-white panel; marks are pale enough to multiply over dark ink without hiding
it. Which project used which theme is recorded in `work/VIDEO-THEMES.md`.
"""


# Added 2026-09-22, derived with contrast.derive and gated by contrast.check_palette:
# every one clears 4.5:1 accent on panel, 7:1 ink, and keeps red apart from green under
# deuteranopia and protanopia. Six light and six dark, each on a field shape that is new
# to the roster, so they differ in the shape of the light as well as its colour.
PALETTES.update({
    # Warm orange on a wave field. The only wave-banded warm theme, distinct from citrus and sundown by its banding rather than only its hue.
    'ember': {
        "field": 'waves', "mode": 'light',
        "top": (243, 224, 216), "bottom": (227, 207, 141),
        "accent": (197, 78, 28), "mark": (238, 219, 211),
        "blobs": [
            ((0.18, 0.18), 0.52, (235, 213, 203), 0.85),
            ((0.86, 0.22), 0.44, (226, 204, 162), 0.68),
            ((0.6, 0.9), 0.46, (230, 188, 191), 0.55),
        ],
    },
    # Deep teal-blue on a mesh. Mesh is a new field shape, so this reads apart from keystone's flat vertical teal.
    'harbour': {
        "field": 'mesh', "mode": 'light',
        "top": (218, 235, 241), "bottom": (147, 166, 220),
        "accent": (33, 120, 150), "mark": (213, 230, 236),
        "blobs": [
            ((0.18, 0.18), 0.52, (206, 226, 233), 0.85),
            ((0.86, 0.22), 0.44, (167, 187, 221), 0.68),
            ((0.6, 0.9), 0.46, (192, 227, 223), 0.55),
        ],
    },
    # Magenta on a conic sweep. The sweep rotates the light, which no violet theme (lilac, amethyst, iris) does.
    'orchid': {
        "field": 'conic', "mode": 'light',
        "top": (238, 221, 237), "bottom": (212, 155, 181),
        "accent": (183, 62, 174), "mark": (233, 215, 232),
        "blobs": [
            ((0.18, 0.18), 0.52, (230, 209, 228), 0.85),
            ((0.86, 0.22), 0.44, (215, 173, 197), 0.68),
            ((0.6, 0.9), 0.46, (215, 195, 223), 0.55),
        ],
    },
    # Mid green over a dot pattern. The dots give it texture the flat greens (moss, fern, vine) do not have.
    'basil': {
        "field": 'dots', "mode": 'light',
        "top": (223, 238, 221), "bottom": (158, 209, 179),
        "accent": (57, 133, 50), "mark": (217, 233, 216),
        "blobs": [
            ((0.18, 0.18), 0.52, (211, 229, 210), 0.85),
            ((0.86, 0.22), 0.44, (175, 213, 186), 0.68),
            ((0.6, 0.9), 0.46, (207, 221, 197), 0.55),
        ],
    },
    # Earthy terracotta on a rule grid. The grid reads as graph paper behind the window.
    'clay': {
        "field": 'grid', "mode": 'light',
        "top": (238, 226, 221), "bottom": (209, 198, 158),
        "accent": (170, 95, 65), "mark": (233, 221, 216),
        "blobs": [
            ((0.18, 0.18), 0.52, (229, 215, 210), 0.85),
            ((0.86, 0.22), 0.44, (213, 200, 175), 0.68),
            ((0.6, 0.9), 0.46, (221, 197, 198), 0.55),
        ],
    },
    # Cool slate blue on a mesh, a calmer partner to cobalt for a data-led cut.
    'frost': {
        "field": 'mesh', "mode": 'light',
        "top": (221, 228, 238), "bottom": (162, 158, 209),
        "accent": (70, 117, 185), "mark": (216, 223, 233),
        "blobs": [
            ((0.18, 0.18), 0.52, (210, 217, 229), 0.85),
            ((0.86, 0.22), 0.44, (175, 176, 213), 0.68),
            ((0.6, 0.9), 0.46, (197, 216, 221), 0.55),
        ],
    },
    # Dark mode. Blue spotlight pooling out of near-black, for a cut that wants the panel to glow.
    'midnight': {
        "field": 'spotlight', "mode": 'dark',
        "top": (18, 55, 115), "bottom": (15, 11, 50),
        "accent": (55, 127, 246), "mark": (208, 220, 241),
        "blobs": [
            ((0.18, 0.18), 0.52, (200, 215, 239), 0.85),
            ((0.86, 0.22), 0.44, (155, 156, 233), 0.68),
            ((0.6, 0.9), 0.46, (184, 221, 234), 0.55),
        ],
    },
    # Dark mode. Mint-teal spotlight, the brightest accent in the dark set at 10:1.
    'obsidian': {
        "field": 'spotlight', "mode": 'dark',
        "top": (28, 105, 86), "bottom": (15, 39, 46),
        "accent": (57, 223, 182), "mark": (211, 238, 231),
        "blobs": [
            ((0.18, 0.18), 0.52, (204, 235, 227), 0.85),
            ((0.86, 0.22), 0.44, (163, 218, 225), 0.68),
            ((0.6, 0.9), 0.46, (189, 229, 205), 0.55),
        ],
    },
    # Dark mode. Violet over an organic noise cloud rather than a hard pool.
    'plum': {
        "field": 'noise', "mode": 'dark',
        "top": (66, 16, 117), "bottom": (50, 10, 51),
        "accent": (171, 91, 251), "mark": (224, 207, 242),
        "blobs": [
            ((0.18, 0.18), 0.52, (219, 199, 240), 0.85),
            ((0.86, 0.22), 0.44, (223, 153, 235), 0.68),
            ((0.6, 0.9), 0.46, (190, 183, 235), 0.55),
        ],
    },
    # Dark mode. Amber spotlight, the warm option in an otherwise cool dark roster.
    'carbon': {
        "field": 'spotlight', "mode": 'dark',
        "top": (117, 61, 15), "bottom": (51, 48, 10),
        "accent": (250, 129, 30), "mark": (242, 223, 207),
        "blobs": [
            ((0.18, 0.18), 0.52, (240, 217, 199), 0.85),
            ((0.86, 0.22), 0.44, (235, 219, 153), 0.68),
            ((0.6, 0.9), 0.46, (236, 187, 183), 0.55),
        ],
    },
    # Dark mode. Cyan on noise, the coolest of the dark set.
    'deepsea': {
        "field": 'noise', "mode": 'dark',
        "top": (17, 85, 116), "bottom": (11, 19, 51),
        "accent": (33, 181, 247), "mark": (207, 231, 242),
        "blobs": [
            ((0.18, 0.18), 0.52, (199, 227, 239), 0.85),
            ((0.86, 0.22), 0.44, (154, 180, 234), 0.68),
            ((0.6, 0.9), 0.46, (183, 235, 232), 0.55),
        ],
    },
    # Zero to Shielded series palette: Zcash gold on deep ink. Radial ink field (warm navy
    # centre, near-black corners), light-ink panels so windows read as paper on the night
    # field, an accent gold dark enough for AA text on the near-white panel and a pale gold
    # marker. Shared by every episode of the series (preflight allows it through `series`).
    # Text drawn straight on this field must use the light card ink set in the project.
    'shield': {
        "field": 'radial', "mode": 'light',
        "top": (30, 38, 66), "bottom": (7, 9, 17),
        "accent": (138, 92, 0), "mark": (255, 228, 150),
        "blobs": [
            ((0.16, 0.20), 0.50, (244, 183, 40), 0.10),
            ((0.86, 0.18), 0.42, (70, 96, 170), 0.16),
            ((0.62, 0.92), 0.46, (244, 183, 40), 0.07),
        ],
    },
    # Dark mode. Red-orange spotlight. The accent is close to the refusal red, so use it where nothing fails on screen.
    'forge': {
        "field": 'spotlight', "mode": 'dark',
        "top": (114, 18, 18), "bottom": (50, 30, 11),
        "accent": (245, 56, 56), "mark": (241, 208, 208),
        "blobs": [
            ((0.18, 0.18), 0.52, (239, 200, 200), 0.85),
            ((0.86, 0.22), 0.44, (233, 183, 155), 0.68),
            ((0.6, 0.9), 0.46, (234, 184, 202), 0.55),
        ],
    },
})


def palette(name: str) -> dict:
    return PALETTES[name]


def colour_for(line: str) -> tuple[int, int, int]:
    """Colour one line of captured output, by the active project's rules.

    The table used to be hardcoded here, which meant every project inherited every other
    project's vocabulary and a new word meant editing a shared file. It is
    `style.colour_rules` now, defaulted from `style.DEFAULT_COLOUR_RULES` and extendable or
    replaceable per project.

    Order is load bearing and the rules are checked in order: refusals before approvals,
    because "approved" is inside "not_approved".
    """
    text = line.strip()
    if text.startswith("$"):
        return GREEN
    names = {
        "green": GREEN, "red": RED, "amber": AMBER, "blue": BLUE, "violet": VIOLET,
        "ink": INK, "ink_soft": INK_SOFT,
    }
    for token, name in ACTIVE.colour_rules:
        if token in text:
            return names.get(name, INK)
    return INK
