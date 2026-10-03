"""The kit's test suite.

Run it from the kit directory:

    python3 -m pytest tests -q

Two rules shaped these tests. First, the shipped look is a contract: `style.resolve({})`
has to reproduce the exact numbers the kit shipped with, because 32 projects depend on
them and a rebuild that changes a delivered video is a bug however pretty the new frame
is. Second, the per-scene contract test is parameterised over the live registry, so a
scene type added later is covered without anyone editing this file.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from PIL import Image

KIT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(KIT))

import bg  # noqa: E402
import build  # noqa: E402
import motion  # noqa: E402
import schema  # noqa: E402
import style  # noqa: E402
import theme  # noqa: E402


@pytest.fixture(autouse=True)
def _default_style():
    """Every test starts from the shipped defaults, so one test cannot leak into the next."""
    theme.configure(style.resolve({}))
    yield
    theme.configure(style.resolve({}))


# ---------------------------------------------------------------------------
# style.resolve
# ---------------------------------------------------------------------------

def test_defaults_reproduce_the_shipped_numbers():
    resolved = style.resolve({})
    assert resolved.canvas == (2560, 1440)
    assert resolved.output == (1920, 1080)
    assert resolved.fps == 30
    assert resolved.encoder["preset"] == "veryfast"
    assert resolved.encoder["crf"] == 19
    # colour tagging and parallel rendering are opt-in, or a rebuild of an old project
    # would not be byte-identical
    assert resolved.encoder["colour"] is None
    assert resolved.encoder["workers"] == 1


def test_default_theme_constants_match_the_shipped_kit():
    theme.configure(style.resolve({}))
    assert (theme.LINE_HEIGHT, theme.WINDOW_MARGIN, theme.PAD_X, theme.PAD_TOP) == (39, 130, 56, 96)
    assert theme.CODE.size == 30 and theme.CARD.size == 82 and theme.CAPTION.size == 34
    assert theme.CAPTION_BAND == 62 and theme.CAPTION_WIDTH == 1740
    assert theme.INK == (26, 33, 46) and theme.PANEL == (252, 253, 255)


@pytest.mark.parametrize("aspect,expected", [
    ("16:9", (1920, 1080)), ("9:16", (1080, 1920)),
    ("1:1", (1080, 1080)), ("4:5", (1080, 1350)),
])
def test_every_aspect_resolves(aspect, expected):
    assert style.resolve({"style": {"aspect": aspect}}).output == expected


@pytest.mark.parametrize("quality", ["draft", "standard", "high", "max"])
def test_every_quality_resolves(quality):
    resolved = style.resolve({"style": {"quality": quality}})
    assert resolved.canvas[0] > 0 and resolved.fps > 0


def test_unknown_aspect_and_quality_raise():
    with pytest.raises(ValueError):
        style.resolve({"style": {"aspect": "3:7"}})
    with pytest.raises(ValueError):
        style.resolve({"style": {"quality": "supreme"}})


def test_project_overrides_merge_without_dropping_siblings():
    resolved = style.resolve({"style": {"caption": {"style": "top"}}})
    assert resolved.caption["style"] == "top"
    # the keys the project did not mention survive the merge
    assert resolved.caption["band"] == 62


def test_missing_font_stack_falls_back_rather_than_crashing():
    resolved = style.resolve({"style": {"fonts": {"stack": "inter"}}})
    for path in resolved.fonts.values():
        assert Path(path).exists(), "resolve must never hand back a font path that is not there"


def test_dark_mode_swaps_the_ink_set():
    dark = style.resolve({"style": {"mode": "dark"}})
    assert dark.ink["panel"] == (22, 26, 36)
    assert dark.ink["ink"] != style.LIGHT_INK["ink"]


# ---------------------------------------------------------------------------
# theme.configure
# ---------------------------------------------------------------------------

def test_configure_pushes_the_canvas_into_renderers_that_captured_it():
    theme.configure(style.resolve({"style": {"aspect": "9:16"}}))
    assert theme.CANVAS == (1440, 2560)
    # scene.py binds WIDTH, HEIGHT at import, so configure has to push rather than rely on
    # the module re-reading theme.CANVAS
    import scene
    assert (scene.WIDTH, scene.HEIGHT) == theme.CANVAS
    assert (motion.WIDTH, motion.HEIGHT) == theme.CANVAS


def test_colour_for_puts_refusals_before_approvals():
    # "approved" is a substring of "not_approved", so order in the rule list is load bearing
    assert theme.colour_for("  not_approved (code_mismatch)") == theme.RED
    assert theme.colour_for("  approved") == theme.GREEN


def test_colour_rules_can_be_extended_and_replaced():
    theme.configure(style.resolve({"style": {"colour_rules": {"rules": [["widget", "blue"]]}}}))
    assert theme.colour_for("the widget landed") == theme.BLUE
    assert theme.colour_for("not_approved") == theme.RED, "inherited rules must survive"
    theme.configure(style.resolve({"style": {"colour_rules": {"replace": True, "rules": [["only", "red"]]}}}))
    assert theme.colour_for("not_approved") == theme.INK, "replace must drop the defaults"


# ---------------------------------------------------------------------------
# the scene registry
# ---------------------------------------------------------------------------

def test_registry_lookup_and_unknown_type():
    style.load_scene_modules()
    assert "chart" in style.known()
    with pytest.raises(RuntimeError):
        style.get("no-such-scene")


def test_duplicate_registration_raises():
    style.load_scene_modules()
    existing = style.known()[0]
    with pytest.raises(RuntimeError):
        style.scene(existing)(lambda *a: None)


# ---------------------------------------------------------------------------
# timing
# ---------------------------------------------------------------------------

def test_cue_starts_are_absolute_so_a_long_cue_stretches_only_its_own_segment(tmp_path):
    project = {
        "id": "t", "palette": "citrus",
        "segments": [
            {"type": "card", "lines": ["one"], "narration": ["First line here."]},
            {"type": "card", "lines": ["two"], "narration": ["Second line here."]},
        ],
    }
    plans, cues, clock = build.layout(project, tmp_path)
    assert len(cues) == 2
    assert cues[0].start < cues[1].start
    # the second cue starts inside the second segment, never before it
    assert cues[1].start >= plans[1]["offset"]
    assert clock == pytest.approx(sum(p["seconds"] for p in plans))


def test_caption_pieces_sum_to_the_cue_duration():
    pieces = build.caption_pieces("a fairly long narration cue that will wrap onto two lines", 5.0, 4.0)
    assert pieces
    assert pieces[0][0] == 5.0
    assert pieces[-1][1] == pytest.approx(9.0)
    for start, end, _ in pieces:
        assert end > start


def test_composited_offsets_shift_earlier_by_the_overlaps():
    plans = [{"seconds": 4.0}, {"seconds": 5.0}, {"seconds": 3.0}]
    offsets = build._composited_offsets(plans, [0.0, 0.6, 0.5])
    assert offsets[0] == 0.0
    assert offsets[1] == pytest.approx(3.4)
    assert offsets[2] == pytest.approx(7.9)


# ---------------------------------------------------------------------------
# motion
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "linear", "cubic", "quad", "quad-in", "quad-out", "cubic-in", "cubic-out",
    "quart", "quart-in", "quart-out", "expo-in", "expo-out", "back", "elastic", "bounce",
])
def test_easing_is_pinned_and_clamped(name):
    assert motion.ease_by(name, 0.0) == pytest.approx(0.0, abs=1e-9)
    assert motion.ease_by(name, 1.0) == pytest.approx(1.0, abs=1e-9)
    assert motion.ease_by(name, -5) == motion.ease_by(name, 0.0)
    assert motion.ease_by(name, 5) == motion.ease_by(name, 1.0)


def test_default_ease_is_still_cubic_in_out():
    # build.py depends on this curve, so it is a contract not a preference
    assert motion.ease(0.5) == pytest.approx(0.5)
    assert motion.ease(0.25) == pytest.approx(0.0625)


# ---------------------------------------------------------------------------
# every registered scene, checked through the live registry
# ---------------------------------------------------------------------------

SAMPLES = {
    "chart": {"type": "chart", "chart": "bar", "title": "t",
              "rows": [["alpha", 3], ["beta", 7]], "unit": "ms"},
    "diagram": {"type": "diagram", "layout": "flow",
                "nodes": [{"id": "a", "label": "Alpha"}, {"id": "b", "label": "Beta"}],
                "edges": [{"from": "a", "to": "b", "label": "go"}]},
}


def _scene_sample(kind):
    if kind in SAMPLES:
        return SAMPLES[kind]
    return None


@pytest.mark.parametrize("kind", sorted(SAMPLES))
def test_scene_contract(kind, tmp_path):
    """A registered scene returns a canvas-sized image, ordered boxes and a strict resolve."""
    style.load_scene_modules()
    if kind not in style.known():
        pytest.skip(f"{kind} is not registered in this checkout")
    project = {"id": "t", "palette": "citrus"}
    theme.configure(style.resolve(project))
    base = bg.background("citrus", None)
    page_for, count, resolve = style.get(kind)(
        _scene_sample(kind), project, tmp_path, base, theme.ACTIVE, theme.palette("citrus")
    )
    page = page_for(count)
    assert page.image.size == theme.CANVAS
    assert len(page.boxes) == count
    for box in page.boxes:
        assert len(box) == 4 and box[2] >= box[0] and box[3] >= box[1]
    assert resolve("definitely-not-present-anywhere") == [], "resolve must return [] on a miss"


# ---------------------------------------------------------------------------
# failure paths
# ---------------------------------------------------------------------------

def test_unknown_palette_raises():
    with pytest.raises(KeyError):
        theme.palette("no-such-palette")


def test_chart_with_no_rows_raises(tmp_path):
    style.load_scene_modules()
    import chart
    with pytest.raises(RuntimeError):
        chart.prepare({"type": "chart", "chart": "bar", "rows": []}, {}, tmp_path,
                      Image.new("RGB", theme.CANVAS), theme.ACTIVE, theme.palette("citrus"))


def test_diagram_with_unknown_edge_endpoint_raises(tmp_path):
    style.load_scene_modules()
    import diagram
    with pytest.raises(RuntimeError):
        diagram.prepare({"type": "diagram", "nodes": [{"id": "a"}],
                         "edges": [{"from": "a", "to": "ghost"}]},
                        {}, tmp_path, Image.new("RGB", theme.CANVAS),
                        theme.ACTIVE, theme.palette("citrus"))


def test_build_refuses_a_video_over_its_cap(tmp_path):
    project = {
        "id": "t", "palette": "citrus", "cap": 1.0,
        "segments": [{"type": "card", "lines": ["x"], "narration": ["A line of narration here."]}],
    }
    plans, _, _ = build.layout(project, tmp_path)
    total = sum(p["seconds"] for p in plans)
    assert total > 1.0, "the sample has to exceed the cap for this test to mean anything"


# ---------------------------------------------------------------------------
# schema
# ---------------------------------------------------------------------------

def test_schema_accepts_a_real_project():
    errors, _ = schema.check(KIT / "templates" / "short.json")
    assert errors == []


def test_schema_catches_a_bad_segment_type(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"id": "x", "segments": [{"type": "crad", "lines": ["a"]}]}))
    errors, _ = schema.check(bad)
    assert any("unknown type" in e for e in errors)


def test_schema_catches_a_missing_input(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({
        "id": "x", "segments": [{"type": "code", "file": "/nope/gone.py", "title": "t"}]
    }))
    errors, _ = schema.check(bad)
    assert any("not found" in e for e in errors)
