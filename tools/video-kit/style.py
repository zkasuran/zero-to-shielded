"""The style engine: one resolved Style per build, and the scene registry.

Everything that used to be a constant in `theme.py` now has a default here and can be
overridden per project. A project file that carries no `style` block resolves to exactly
the numbers the kit shipped with, so the 32 existing projects render byte-identical.

Three things live here:

* `Style`, the resolved settings for one build (geometry, type, chrome, motion, audio,
  encoder). `resolve(project)` builds it from a project file.
* The aspect and quality presets, so a project asks for `"aspect": "9:16"` rather than
  computing pixel sizes.
* The scene registry. A renderer module registers itself with `@scene("chart")` and
  `build.prepare` looks the type up rather than growing another `if` branch. That is what
  keeps a new scene type from touching `build.py` at all.

Geometry rule: the canvas is the delivered frame times `canvas_scale`, and everything is
rendered on the canvas then cropped and resized down. A scale above 1 is what buys a zoom
that costs nothing in sharpness, so it is the quality knob that matters most.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent

# Delivered frame per aspect. 16:9 is the historic default and its numbers are the ones
# every shipped video used. The rest are the surfaces a submission actually gets asked
# for: a vertical cut for Shorts and TikTok, a square for a feed post, 4:5 for the taller
# feed crop that Instagram and LinkedIn both accept.
ASPECTS: dict[str, tuple[int, int]] = {
    "16:9": (1920, 1080),
    "9:16": (1080, 1920),
    "1:1": (1080, 1080),
    "4:5": (1080, 1350),
}

# canvas_scale, x264 preset, crf, fps. `standard` reproduces the shipped look exactly:
# 1920x1080 delivered off a 2560x1440 canvas at CRF 19, preset veryfast.
QUALITY: dict[str, dict] = {
    "draft": {"canvas_scale": 1.0, "preset": "ultrafast", "crf": 28, "fps": 30},
    "standard": {"canvas_scale": 4 / 3, "preset": "veryfast", "crf": 19, "fps": 30},
    "high": {"canvas_scale": 1.5, "preset": "slow", "crf": 17, "fps": 30},
    "max": {"canvas_scale": 2.0, "preset": "slower", "crf": 15, "fps": 60},
}

# Font stacks. `system` is what every shipped video used and stays the default, so a
# rebuild of an old project cannot change its look. `inter` is the opt-in upgrade and is
# resolved against fonts/ inside the kit, with a fallback to the system stack when the
# files are not vendored yet.
FONT_STACKS: dict[str, dict[str, str]] = {
    "system": {
        "sans": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "sans_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "mono_bold": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    },
    "inter": {
        "sans": str(ROOT / "fonts" / "Inter-Regular.ttf"),
        "sans_bold": str(ROOT / "fonts" / "Inter-Bold.ttf"),
        "mono": str(ROOT / "fonts" / "JetBrainsMono-Regular.ttf"),
        "mono_bold": str(ROOT / "fonts" / "JetBrainsMono-Bold.ttf"),
    },
}

# Type sizes and spacing, in canvas pixels at the reference canvas (short edge 1440).
# Every one is multiplied by the geometry scale, so a project on a different canvas keeps
# the same optical size rather than the same pixel count.
TYPE: dict[str, int] = {
    "code": 30,
    "code_bold": 30,
    "code_small": 27,
    "chrome": 25,
    "card": 82,
    "card_mono": 58,
    "kicker": 34,
    "footer": 30,
    "panel_label": 34,
    "panel_value": 30,
    "bubble": 31,
    "bubble_who": 24,
    "doc_h1": 44,
    "doc_key": 29,
    "doc_value": 32,
}

METRICS: dict[str, int] = {
    "line_height": 39,
    "window_margin": 130,
    "pad_x": 56,
    "pad_top": 96,
    "radius": 30,
}

# Ink and panel. A dark mode is a different set of the same names rather than a branch in
# every renderer, which is why they are grouped.
LIGHT_INK: dict[str, tuple[int, int, int]] = {
    "panel": (252, 253, 255),
    "panel_edge": (255, 255, 255),
    "chrome_bar": (244, 246, 250),
    "ink": (26, 33, 46),
    "ink_soft": (104, 116, 134),
    "card_ink": (23, 28, 40),
    "card_soft": (74, 84, 102),
    "green": (13, 122, 76),
    "red": (188, 44, 48),
    "amber": (162, 92, 0),
    "blue": (28, 92, 190),
    "violet": (108, 62, 200),
}

DARK_INK: dict[str, tuple[int, int, int]] = {
    "panel": (22, 26, 36),
    "panel_edge": (46, 54, 72),
    "chrome_bar": (30, 35, 48),
    "ink": (232, 237, 246),
    "ink_soft": (146, 158, 180),
    "card_ink": (240, 244, 252),
    "card_soft": (176, 188, 208),
    # Lifted for a dark panel: the light-mode values are tuned for contrast against
    # near-white and go muddy on dark, so each is the same hue at a higher luminance.
    "green": (74, 214, 146),
    "red": (255, 122, 122),
    "amber": (246, 184, 76),
    "blue": (122, 176, 255),
    "violet": (186, 150, 255),
}

# The default token to colour table for terminal output. It used to be a hardcoded tuple
# inside `theme.colour_for`, which meant every project that wanted a word coloured had to
# edit a shared file and every project inherited every other project's vocabulary. It is
# a default now, and a project can extend or replace it with `style.colour_rules`.
#
# Order matters and is load bearing: refusals are tested before approvals, because
# "approved" is a substring of "not_approved".
DEFAULT_COLOUR_RULES: list[tuple[str, str]] = [
    ("GREEN, which is the defect", "red"),
    ("[red]", "red"),
    ("FAIL", "red"),
    ("controls provoked their check", "green"),
    ("absent from both surfaces", "green"),
    ("PASS no ", "green"),
    ("positive control", "blue"),
    ("unsigned transactions built", "blue"),
    ("verified: false", "red"),
    ("not_approved", "red"),
    ("not_confirmed", "red"),
    ("no_common_slot", "red"),
    ("does not follow", "red"),
    ("declined", "red"),
    ("refused", "red"),
    ("config error", "red"),
    ("bad arguments:", "red"),
    ("calls placed: 0", "red"),
    ("LEAK", "red"),
    ("nobody authorized", "red"),
    ("code_mismatch", "amber"),
    ("no_answer", "amber"),
    ("voicemail", "amber"),
    ("partially_met", "amber"),
    ("proposal_only", "amber"),
    ("outside_authorized_window", "amber"),
    ("privacy check", "amber"),
    ("Approval code", "amber"),
    ("approved", "green"),
    ("RESULT: green", "green"),
    ("digests identical", "green"),
    ("tests passed, 0 failed", "green"),
    ("booked", "green"),
    ("goal_met", "green"),
    ("confirmed", "green"),
    ("verdicts hold", "green"),
    ("replay cleanly", "green"),
    ("Verdict", "blue"),
    ("Outcome", "blue"),
]


@dataclass
class Style:
    """Everything one build needs to know about how it should look and encode."""

    aspect: str = "16:9"
    quality: str = "standard"
    mode: str = "light"

    output: tuple[int, int] = (1920, 1080)
    canvas: tuple[int, int] = (2560, 1440)
    fps: int = 30
    scale: float = 1.0
    """Canvas short edge over the reference 1440, so type and spacing keep optical size."""

    fonts: dict[str, str] = field(default_factory=lambda: dict(FONT_STACKS["system"]))
    font_scale: float = 1.0
    type_sizes: dict[str, int] = field(default_factory=lambda: dict(TYPE))
    metrics: dict[str, int] = field(default_factory=lambda: dict(METRICS))
    ink: dict[str, tuple[int, int, int]] = field(default_factory=lambda: dict(LIGHT_INK))

    caption: dict = field(default_factory=lambda: {
        "style": "band", "position": "bottom", "font_size": 34, "band": 62, "width_ratio": 0.906,
    })
    progress: dict = field(default_factory=lambda: {"style": "bar", "height": 8})
    cursor: dict = field(default_factory=lambda: {"style": "arrow", "size": 210})
    marker: dict = field(default_factory=lambda: {"style": "highlight", "opacity": 0.15, "sweep": 1.6})
    window: dict = field(default_factory=lambda: {
        "chrome": "mac", "shadow_blur": 34, "shadow_alpha": 92, "radius": 30,
    })
    brand: dict = field(default_factory=dict)
    transitions: dict = field(default_factory=lambda: {"default": "cut", "seconds": 0.5})
    audio: dict = field(default_factory=dict)

    encoder: dict = field(default_factory=lambda: {
        # colour defaults to None so a rebuild of an existing project is byte-identical.
        # A project opts into bt709 tagging with render.colour, which YouTube prefers and
        # which leaves the picture pixel-identical (only the SPS metadata gains the tag).
        # workers defaults to 1: serial, exactly the shipped behaviour, and safe for web
        # scenes that launch a browser. A project opts into parallel with render.workers
        # (N, or 0 for auto = cpu-2). The parallel picture is proven pixel-identical.
        "preset": "veryfast", "crf": 19, "bitrate": None, "workers": 1,
        "colour": None, "tune": None,
    })

    colour_rules: list[tuple[str, str]] = field(default_factory=lambda: list(DEFAULT_COLOUR_RULES))

    timing: dict = field(default_factory=lambda: {
        "gap": 0.35, "lead": 0.3, "cap": 176.0, "transition": 0.62,
        "cursor_move": 0.45, "cadence": 0.45, "hold": 1.6, "pad": 0.9,
    })

    def px(self, value: float) -> int:
        """A reference-canvas measurement in this build's canvas pixels."""
        return max(1, round(value * self.scale))

    def type_px(self, name: str) -> int:
        return max(8, round(self.type_sizes[name] * self.scale * self.font_scale))

    def metric(self, name: str) -> int:
        return self.px(self.metrics[name])

    @property
    def caption_reserve(self) -> int:
        """Caption band plus progress bar, in delivered pixels."""
        if self.caption.get("style") == "none":
            return self.progress.get("height", 8)
        return round(self.caption["band"] * self._caption_scale()) + 8

    def _caption_scale(self) -> float:
        """Captions are burned into the DELIVERED frame, so they scale with output height."""
        return self.output[1] / 1080


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (over or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = copy.deepcopy(value)
    return out


def _hex_to_rgb(value) -> tuple[int, int, int]:
    if isinstance(value, (list, tuple)):
        return (int(value[0]), int(value[1]), int(value[2]))
    text = str(value).lstrip("#")
    if len(text) == 3:
        text = "".join(character * 2 for character in text)
    if len(text) != 6:
        raise ValueError(f"not a colour: {value!r}")
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def resolve(project: dict) -> Style:
    """Build the Style for one project file.

    A project with no `style` and no `render` block resolves to the shipped defaults, so
    this is safe to put in front of every existing project.
    """
    spec = project.get("style", {}) or {}
    render = project.get("render", {}) or {}

    quality_name = render.get("quality", spec.get("quality", "standard"))
    if quality_name not in QUALITY:
        raise ValueError(f"unknown quality {quality_name!r}, have {sorted(QUALITY)}")
    quality = dict(QUALITY[quality_name])

    aspect = spec.get("aspect", "16:9")
    if aspect not in ASPECTS:
        raise ValueError(f"unknown aspect {aspect!r}, have {sorted(ASPECTS)}")
    output = tuple(render.get("output") or ASPECTS[aspect])

    canvas_scale = float(render.get("canvas_scale", quality["canvas_scale"]))
    # Even dimensions or libx264 refuses the yuv420p stream.
    canvas = (
        round(output[0] * canvas_scale) // 2 * 2,
        round(output[1] * canvas_scale) // 2 * 2,
    )
    scale = min(canvas) / 1440.0

    style = Style(
        aspect=aspect,
        quality=quality_name,
        mode=spec.get("mode", "light"),
        output=(int(output[0]), int(output[1])),
        canvas=canvas,
        fps=int(render.get("fps", quality["fps"])),
        scale=scale,
    )

    stack = spec.get("fonts", {}) or {}
    stack_name = stack.get("stack", "system")
    if stack_name not in FONT_STACKS:
        raise ValueError(f"unknown font stack {stack_name!r}, have {sorted(FONT_STACKS)}")
    fonts = dict(FONT_STACKS[stack_name])
    # A vendored stack that was never fetched falls back rather than crashing a build the
    # night before a deadline. Say so loudly at resolve time instead of at draw time.
    missing = [role for role, path in fonts.items() if not Path(path).exists()]
    if missing:
        if stack_name != "system":
            print(f"  style: font stack {stack_name!r} missing {', '.join(missing)}, using system")
        fonts = dict(FONT_STACKS["system"])
    for role in ("sans", "sans_bold", "mono", "mono_bold"):
        if role in stack:
            fonts[role] = stack[role]
    style.fonts = fonts
    style.font_scale = float(stack.get("scale", 1.0))

    style.type_sizes = _deep_merge(TYPE, spec.get("type", {}))
    style.metrics = _deep_merge(METRICS, spec.get("metrics", {}))

    ink = dict(DARK_INK if style.mode == "dark" else LIGHT_INK)
    for name, value in (spec.get("ink", {}) or {}).items():
        ink[name] = _hex_to_rgb(value)
    style.ink = ink

    style.caption = _deep_merge(style.caption, spec.get("caption", {}))
    if project.get("captions") is False:
        style.caption["style"] = "none"
    style.progress = _deep_merge(style.progress, spec.get("progress", {}))
    style.cursor = _deep_merge(style.cursor, spec.get("cursor", {}))
    style.marker = _deep_merge(style.marker, spec.get("marker", {}))
    style.window = _deep_merge(style.window, spec.get("window", {}))
    style.window["radius"] = style.window.get("radius", style.metrics["radius"])
    style.brand = dict(spec.get("brand", {}) or {})
    style.transitions = _deep_merge(style.transitions, project.get("transitions", {}))
    style.audio = dict(project.get("audio", {}) or {})

    style.encoder = _deep_merge(style.encoder, {
        "preset": quality["preset"], "crf": quality["crf"],
    })
    # Every other key in `render` flows through to the encoder untouched, so a new knob is
    # a key in the project file rather than an edit here.
    style.encoder = _deep_merge(style.encoder, {
        key: value for key, value in render.items()
        if key not in ("quality", "output", "canvas_scale", "fps")
    })

    rules = spec.get("colour_rules")
    if isinstance(rules, dict):
        style.colour_rules = [
            *( [] if rules.get("replace") else list(DEFAULT_COLOUR_RULES) ),
            *[(str(token), str(name)) for token, name in rules.get("rules", [])],
        ]
        # Project rules are checked first, so a project can override an inherited verdict
        # rather than only adding to it.
        if not rules.get("replace"):
            style.colour_rules = [
                *[(str(token), str(name)) for token, name in rules.get("rules", [])],
                *list(DEFAULT_COLOUR_RULES),
            ]
    elif isinstance(rules, list):
        style.colour_rules = [(str(token), str(name)) for token, name in rules]

    timing = {"cap": float(project.get("cap", style.timing["cap"]))}
    if "cadence" in project:
        timing["cadence"] = float(project["cadence"])
    style.timing = _deep_merge(style.timing, timing)
    style.timing = _deep_merge(style.timing, project.get("timing", {}))
    return style


# ---------------------------------------------------------------------------
# The scene registry.
#
# A renderer module calls @scene("chart") on a prepare function. `build.prepare` looks the
# segment type up here instead of growing another branch, so adding a scene type means
# adding a module and never touching build.py. That is the whole point: eleven scene types
# arriving at once cannot all edit the same if-chain.
# ---------------------------------------------------------------------------

Prepared = tuple[Callable[[int], object], int, Callable[[str], list]]
_SCENES: dict[str, Callable] = {}
_SCENE_MODULES: list[str] = []


def scene(kind: str):
    """Register a prepare function for a segment type.

    The function is called as `fn(segment, project, work, base, style, palette)` and returns
    `(page_for, count, resolve)`:

    * `page_for(visible)` returns an object with `.image` (a canvas-sized PIL Image),
      `.boxes` (one canvas-space box per row, in order) and optionally `.window`.
    * `count` is how many rows the scene reveals.
    * `resolve(needle)` maps a focus string to a list of row indexes, `[]` when it matches
      nothing so preflight can fail on a stale marker.
    """

    def register(function):
        if kind in _SCENES:
            raise RuntimeError(f"scene type {kind!r} is already registered by {_SCENES[kind].__module__}")
        _SCENES[kind] = function
        return function

    return register


def get(kind: str):
    if kind not in _SCENES:
        raise RuntimeError(f"unknown segment type {kind!r}, have {sorted(_SCENES)}")
    return _SCENES[kind]


def known() -> list[str]:
    return sorted(_SCENES)


def load_scene_modules() -> None:
    """Import every module that registers a scene type.

    Import is the registration, so this is what makes a scene type exist. Keep the list
    alphabetical and add one line per new renderer module.
    """
    import importlib

    for name in (
        "cards", "chart", "code", "compose", "device", "diagram", "diff",
        "doc", "grid", "panel", "receipt", "scene", "stage", "web",
    ):
        if name in _SCENE_MODULES:
            continue
        try:
            importlib.import_module(name)
            _SCENE_MODULES.append(name)
        except ModuleNotFoundError:
            # A renderer module that is not written yet is not a build failure. An unknown
            # segment type still fails loudly in get(), which is where it should.
            continue
