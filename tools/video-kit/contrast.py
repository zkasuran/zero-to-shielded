"""Contrast and colour-vision checks for the palette roster.

A palette is chosen by eye, and an eye is exactly the instrument that misses a contrast
failure. This is the gate: WCAG relative luminance and contrast ratios for the accent,
the ink and every semantic colour, plus a red against green separation check under
simulated colour-vision deficiency.

That last one carries the most weight here. The kit's whole visual grammar is that a
refusal is red and a pass is green, so if those two collapse for a viewer the video stops
communicating its main point whatever its contrast numbers say.

    python3 contrast.py            audit every palette, exit non-zero on a failure
    python3 contrast.py citrus     audit one

Existing palettes are reported, never silently corrected. A shipped video's theme is a
matter of record and changing it would change what a rebuild produces.
"""

from __future__ import annotations

import sys

import style as style_module
import theme

# WCAG 2.1 thresholds. 4.5:1 is AA for normal text, 7:1 is AAA, and the accent is used for
# titles and UI so it is held to the text bar rather than the large-text bar.
AA_TEXT = 4.5
AAA_TEXT = 7.0


def _linear(channel: float) -> float:
    c = channel / 255.0
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(colour) -> float:
    """WCAG relative luminance."""
    r, g, b = (_linear(c) for c in colour[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b) -> float:
    """WCAG contrast ratio, always >= 1, order independent."""
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def blend(fg, bg, alpha: float):
    """Composite fg over bg at alpha, for checking a mark that sits under the text."""
    return tuple(round(fg[i] * alpha + bg[i] * (1 - alpha)) for i in range(3))


# Brettel-style simulation, reduced to the two common dichromacies. The exact matrices
# differ between published models, so these are used only to answer one question: do red
# and green stay apart. That is a comparison, not a colour-accurate render.
def simulate(colour, kind: str):
    r, g, b = (_linear(c) * 100 for c in colour[:3])
    if kind == "deuteranopia":
        lr = 0.625 * r + 0.375 * g + 0.0 * b
        lg = 0.700 * r + 0.300 * g + 0.0 * b
        lb = 0.0 * r + 0.300 * g + 0.700 * b
    elif kind == "protanopia":
        lr = 0.567 * r + 0.433 * g + 0.0 * b
        lg = 0.558 * r + 0.442 * g + 0.0 * b
        lb = 0.0 * r + 0.242 * g + 0.758 * b
    else:
        lr, lg, lb = r, g, b

    def back(v):
        v = max(0.0, min(100.0, v)) / 100.0
        v = 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1 / 2.4)) - 0.055
        return max(0, min(255, round(v * 255)))

    return (back(lr), back(lg), back(lb))


def distance(a, b) -> float:
    """Plain euclidean distance in sRGB, enough to answer "are these still apart"."""
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5


# Two colours this far apart after simulation are still tellable apart on a screen. Set
# from the light-mode green and red, which are the pair the grammar depends on.
SEPARATION = 40.0


def check_palette(name: str, mode: str = "light") -> list[str]:
    """Every contrast rule for one palette in one ink mode. Returns a list of failures."""
    palette = theme.PALETTES[name]
    resolved = style_module.resolve({"palette": name, "style": {"mode": mode}})
    ink = resolved.ink
    panel = ink["panel"]
    problems: list[str] = []

    accent = palette["accent"]
    if ratio(accent, panel) < AA_TEXT:
        problems.append(f"accent on panel {ratio(accent, panel):.2f}:1 < {AA_TEXT}")
    if ratio(ink["ink"], panel) < AAA_TEXT:
        problems.append(f"ink on panel {ratio(ink['ink'], panel):.2f}:1 < {AAA_TEXT}")

    for semantic in ("green", "red", "amber", "blue", "violet"):
        r = ratio(ink[semantic], panel)
        if r < AA_TEXT:
            problems.append(f"{semantic} on panel {r:.2f}:1 < {AA_TEXT}")

    # red against green under the two common dichromacies
    for kind in ("deuteranopia", "protanopia"):
        d = distance(simulate(ink["red"], kind), simulate(ink["green"], kind))
        if d < SEPARATION:
            problems.append(f"red vs green under {kind} {d:.0f} < {SEPARATION:.0f}")

    # the mark is blended into the page under the text, so the text must survive it
    marked = blend(palette["mark"], panel, resolved.marker.get("opacity", 0.15))
    r = ratio(ink["ink"], marked)
    if r < AA_TEXT:
        problems.append(f"ink on marked row {r:.2f}:1 < {AA_TEXT}")
    r = ratio(ink["red"], marked)
    if r < 3.0:
        problems.append(f"red on marked row {r:.2f}:1 < 3.0")

    return problems


def audit(names=None, mode: str = "light") -> int:
    names = names or sorted(theme.PALETTES)
    failed = 0
    print(f"{'palette':12s} {'field':10s} {'accent':>8s} {'ink':>7s} {'red':>7s} {'green':>7s}  verdict")
    for name in names:
        palette = theme.PALETTES[name]
        want = palette.get("mode", "light")
        use = mode if mode != "auto" else want
        resolved = style_module.resolve({"palette": name, "style": {"mode": use}})
        ink, panel = resolved.ink, resolved.ink["panel"]
        problems = check_palette(name, use)
        verdict = "ok" if not problems else f"FAIL {len(problems)}"
        if problems:
            failed += 1
        print(f"{name:12s} {palette.get('field', 'vertical'):10s} "
              f"{ratio(palette['accent'], panel):7.2f} {ratio(ink['ink'], panel):6.2f} "
              f"{ratio(ink['red'], panel):6.2f} {ratio(ink['green'], panel):6.2f}  {verdict}")
        for line in problems:
            print(f"             - {line}")
    print(f"\n{len(names)} palettes, {failed} with at least one failure")
    return failed


def derive(seed, field: str = "vertical", mode: str = "light") -> dict:
    """Build a full palette from one seed colour, checked before it is returned.

    Hand-rolling six values per palette is how a contrast failure gets in, so this derives
    them: pale gradient ends from the seed hue, an accent darkened until it clears the text
    bar on the panel, and a mark pale enough to sit under ink. Raises when the seed cannot
    reach the bar, rather than returning something that fails the gate.
    """
    import colorsys

    r, g, b = (c / 255 for c in seed[:3])
    h, _, s = colorsys.rgb_to_hls(r, g, b)
    sat = max(0.45, s)

    def rgb(hue, light, satur):
        return tuple(round(c * 255) for c in colorsys.hls_to_rgb(hue % 1.0, light, satur))

    panel = style_module.DARK_INK["panel"] if mode == "dark" else style_module.LIGHT_INK["panel"]
    # Walk from the mid tones outward and take the FIRST lightness that clears the bar, so
    # the accent keeps as much of the seed hue as contrast allows. Walking from the extreme
    # end instead returns a near-black or near-white that passes the ratio and loses the
    # colour, which is how a roster of "distinct" palettes ends up looking identical.
    if mode == "dark":
        steps = [x / 100 for x in range(55, 96, 2)]
    else:
        steps = [x / 100 for x in range(50, 7, -2)]
    accent = next((c for c in (rgb(h, light, sat) for light in steps) if ratio(c, panel) >= AA_TEXT), None)
    if accent is None:
        raise ValueError(f"no accent from seed {seed} reaches {AA_TEXT}:1 on the {mode} panel")

    if mode == "dark":
        top, bottom = rgb(h, 0.26, sat * 0.8), rgb(h + 0.08, 0.12, sat * 0.7)
    else:
        top, bottom = rgb(h, 0.90, sat * 0.7), rgb(h + 0.08, 0.72, sat * 0.8)
    mark = rgb(h, 0.88, sat * 0.6)

    return {
        "field": field,
        "mode": mode,
        "top": top,
        "bottom": bottom,
        "accent": accent,
        "mark": mark,
        "blobs": [
            ((0.18, 0.18), 0.52, rgb(h, 0.86, sat * 0.6), 0.85),
            ((0.86, 0.22), 0.44, rgb(h + 0.06, 0.76, sat * 0.7), 0.68),
            ((0.60, 0.90), 0.46, rgb(h - 0.06, 0.82, sat * 0.6), 0.55),
        ],
    }


if __name__ == "__main__":
    names = sys.argv[1:] or None
    raise SystemExit(1 if audit(names, mode="auto") else 0)
