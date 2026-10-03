"""Data charts as a scene, drawn from real numbers on disk.

The kit could show a terminal, a code card or a web page, but never a chart, so a
benchmark result or a vote count had to be read aloud over a wall of text. This draws
it. Bars, columns, a line, sparklines and progress meters, each row revealed in turn so
the narration can walk a viewer through the figures one at a time.

The house rule is that nothing on screen is invented, so the numbers come from a JSON
file, a CSV file or an inline list, and a `source` line under the chart says where they
came from. A chart whose data file is missing raises rather than drawing an empty frame.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from pathlib import Path

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


def _walk(data, dotted: str | None):
    """Follow a dotted path into parsed JSON, so a project points at results.cases."""
    if not dotted:
        return data
    node = data
    for part in dotted.split("."):
        if isinstance(node, list):
            node = node[int(part)]
        else:
            node = node[part]
    return node


def _read_rows(segment: dict) -> list[tuple[str, float]]:
    """One (label, value) list from whichever source the segment names.

    Inline rows win, then a CSV with named x and y columns, then a JSON path. A row
    whose value is not a number is skipped rather than crashing the draw, because a
    header row slipping into the data is the common mistake and it should not take the
    whole render down.
    """
    if "rows" in segment:
        raw = segment["rows"]
    elif segment.get("file", "").endswith(".csv"):
        x, y = segment.get("x"), segment.get("y")
        raw = []
        with Path(segment["file"]).open(encoding="utf-8") as handle:
            for record in csv.DictReader(handle):
                label = record[x] if x else next(iter(record.values()))
                raw.append([label, record[y] if y else list(record.values())[1]])
    elif "file" in segment:
        data = json.loads(Path(segment["file"]).read_text(encoding="utf-8"))
        node = _walk(data, segment.get("path"))
        key, value = segment.get("label_key", "label"), segment.get("value_key", "value")
        raw = []
        for item in node:
            if isinstance(item, dict):
                raw.append([item.get(key), item.get(value)])
            else:
                raw.append(list(item)[:2])
    else:
        raise RuntimeError(f"chart {segment.get('name')} names no rows, file or inline data")

    rows: list[tuple[str, float]] = []
    for label, value in raw:
        try:
            rows.append((str(label), float(value)))
        except (TypeError, ValueError):
            continue
    if not rows:
        raise RuntimeError(f"chart {segment.get('name')} resolved to no numeric rows")
    return rows


def _series(segment: dict) -> list[tuple[str, list[float]]]:
    """Named series of y values, for the line chart and stacked sparklines.

    Inline `series` wins. A file whose JSON carries its own `series` list (or one reached
    by `path`) is read the same way, so a line chart points at a real metrics file rather
    than only at values pasted into the project. Anything else falls back to the single
    series a bar chart would have drawn.
    """
    if "series" in segment:
        raw = segment["series"]
    elif "file" in segment and segment["file"].endswith(".json"):
        data = json.loads(Path(segment["file"]).read_text(encoding="utf-8"))
        node = _walk(data, segment.get("path"))
        if isinstance(node, dict) and "series" in node:
            raw = node["series"]
        elif isinstance(node, list) and node and isinstance(node[0], dict) and "values" in node[0]:
            raw = node
        else:
            rows = _read_rows(segment)
            return [(segment.get("title", "series"), [value for _, value in rows])]
    else:
        rows = _read_rows(segment)
        return [(segment.get("title", "series"), [value for _, value in rows])]
    return [(str(s["name"]), [float(v) for v in s["values"]]) for s in raw]


def _fmt(value: float, unit: str) -> str:
    """A number a viewer can read: thousands separators, and no trailing .0 on an integer."""
    if value == int(value):
        text = f"{int(value):,}"
    else:
        text = f"{value:,.2f}".rstrip("0").rstrip(".")
    return f"{text}{unit}" if unit else text


def _panel_box() -> tuple[int, int, int, int]:
    """A floating window sized to the canvas, the same shape every other scene uses.

    Read the canvas here rather than at import, so a 9:16 build gets a portrait panel
    instead of the last build's landscape one.
    """
    width, height = theme.CANVAS
    margin = theme.WINDOW_MARGIN
    top = max(theme.px(96), round(height * 0.11))
    bottom = height - top
    return (margin, top, width - margin, bottom)


def _frame(base: Image.Image, title: str | None, footer: str | None, source: str | None,
           accent) -> tuple[Image.Image, ImageDraw.ImageDraw, tuple[int, int, int, int]]:
    """The panel chrome shared by every chart kind: shadow, rounded card, title, source."""
    image = base.copy()
    box = _panel_box()
    bg.drop_shadow(image, box, radius=theme.px(30))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(box, radius=theme.px(30), fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)
    left, top, right, bottom = box
    if title:
        draw.text((left + theme.px(56), top + theme.px(40)), title, font=theme.KICKER, fill=accent)
    if source:
        draw.text((left + theme.px(56), bottom - theme.px(52)), f"source: {source}",
                  font=theme.CHROME, fill=theme.INK_SOFT)
    if footer:
        width = draw.textlength(footer, font=theme.CHROME)
        draw.text((right - theme.px(56) - width, bottom - theme.px(52)), footer,
                  font=theme.CHROME, fill=theme.INK_SOFT)
    return image, draw, box


def _plot_area(box: tuple[int, int, int, int], title: bool, source: bool,
               label_gutter: int) -> tuple[int, int, int, int]:
    """The rectangle inside the panel that the data lives in, after chrome is reserved."""
    left, top, right, bottom = box
    return (
        left + theme.px(56) + label_gutter,
        top + (theme.px(120) if title else theme.px(56)),
        right - theme.px(80),
        bottom - (theme.px(96) if source else theme.px(56)),
    )


def _semantic(value: float, rules: dict, accent):
    """Colour a bar by a threshold rule, so a pass reads green and a miss reads red."""
    if not rules:
        return accent
    if "good_above" in rules and value >= rules["good_above"]:
        return theme.GREEN
    if "bad_above" in rules and value >= rules["bad_above"]:
        return theme.RED
    if "good_below" in rules and value <= rules["good_below"]:
        return theme.GREEN
    return accent


def _bar(base, rows, segment, accent, horizontal: bool):
    title, footer = segment.get("title"), segment.get("footer")
    source, unit = segment.get("source"), segment.get("unit", "")
    rules = segment.get("thresholds", {})
    count = len(rows)

    def page_for(visible: int) -> Page:
        longest = max((theme.CHROME.getlength(label) for label, _ in rows), default=0)
        gutter = round(longest) + theme.px(24) if horizontal else 0
        image, draw, box = _frame(base, title, footer, source, accent)
        area = _plot_area(box, title is not None, source is not None, gutter)
        ax_left, ax_top, ax_right, ax_bottom = area
        peak = max((value for _, value in rows), default=1.0) or 1.0
        boxes: list[tuple[int, int, int, int]] = []

        if horizontal:
            slot = (ax_bottom - ax_top) / max(count, 1)
            thickness = slot * 0.62
            for index, (label, value) in enumerate(rows):
                y0 = ax_top + slot * index + (slot - thickness) / 2
                length = (value / peak) * (ax_right - ax_left)
                box_i = (ax_left, round(y0), ax_left + round(length), round(y0 + thickness))
                boxes.append((box[0] + theme.px(40), round(y0), ax_right, round(y0 + thickness)))
                if index < visible:
                    draw.text((box[0] + theme.px(56), round(y0 + thickness / 2 - theme.CHROME.size / 2)),
                              label, font=theme.CHROME, fill=theme.INK)
                    draw.rounded_rectangle(box_i, radius=theme.px(6), fill=_semantic(value, rules, accent))
                    draw.text((ax_left + round(length) + theme.px(14),
                               round(y0 + thickness / 2 - theme.PANEL_VALUE.size / 2)),
                              _fmt(value, unit), font=theme.PANEL_VALUE, fill=theme.INK)
        else:
            slot = (ax_right - ax_left) / max(count, 1)
            thickness = slot * 0.6
            for index, (label, value) in enumerate(rows):
                x0 = ax_left + slot * index + (slot - thickness) / 2
                length = (value / peak) * (ax_bottom - ax_top - theme.px(30))
                box_i = (round(x0), round(ax_bottom - length), round(x0 + thickness), ax_bottom)
                boxes.append((round(x0), ax_top, round(x0 + thickness), ax_bottom + theme.px(30)))
                if index < visible:
                    draw.rounded_rectangle(box_i, radius=theme.px(6), fill=_semantic(value, rules, accent))
                    vw = draw.textlength(_fmt(value, unit), font=theme.CHROME)
                    draw.text((round(x0 + thickness / 2 - vw / 2), round(ax_bottom - length) - theme.px(34)),
                              _fmt(value, unit), font=theme.CHROME, fill=theme.INK)
                    lw = draw.textlength(label, font=theme.CHROME)
                    draw.text((round(x0 + thickness / 2 - lw / 2), ax_bottom + theme.px(6)),
                              label, font=theme.CHROME, fill=theme.INK_SOFT)
        return Page(image=image, window=box, row_boxes=boxes)

    resolve = lambda needle: [i for i, (label, _) in enumerate(rows) if needle.lower() in label.lower()][:1]
    return page_for, count, resolve


def _line(base, series, segment, accent):
    title, footer, source = segment.get("title"), segment.get("footer"), segment.get("source")
    labels = segment.get("x_labels")
    length = max((len(values) for _, values in series), default=0)
    palette_cycle = [accent, theme.BLUE, theme.GREEN, theme.AMBER, theme.VIOLET]
    count = length

    def page_for(visible: int) -> Page:
        image, draw, box = _frame(base, title, footer, source, accent)
        area = _plot_area(box, title is not None, source is not None, theme.px(60))
        ax_left, ax_top, ax_right, ax_bottom = area
        flat = [v for _, values in series for v in values] or [0.0, 1.0]
        lo, hi = min(flat), max(flat)
        span = (hi - lo) or 1.0
        for tick in range(5):
            gy = ax_top + (ax_bottom - ax_top) * tick / 4
            draw.line((ax_left, gy, ax_right, gy), fill=(228, 232, 240), width=1)
            val = hi - span * tick / 4
            draw.text((box[0] + theme.px(56), gy - theme.CHROME.size / 2), _fmt(val, segment.get("unit", "")),
                      font=theme.CHROME, fill=theme.INK_SOFT)

        def point(idx, value):
            x = ax_left if length <= 1 else ax_left + (ax_right - ax_left) * idx / (length - 1)
            y = ax_bottom - (value - lo) / span * (ax_bottom - ax_top)
            return (x, y)

        boxes = [(round(point(i, hi)[0]) - theme.px(20), ax_top,
                  round(point(i, hi)[0]) + theme.px(20), ax_bottom) for i in range(length)]
        for si, (name, values) in enumerate(series):
            colour = palette_cycle[si % len(palette_cycle)]
            pts = [point(i, v) for i, v in enumerate(values) if i < visible]
            if len(pts) >= 2:
                draw.line(pts, fill=colour, width=theme.px(4), joint="curve")
            for p in pts:
                draw.ellipse((p[0] - theme.px(7), p[1] - theme.px(7), p[0] + theme.px(7), p[1] + theme.px(7)),
                             fill=colour)
            if pts:
                draw.text((pts[-1][0] + theme.px(12), pts[-1][1] - theme.px(30)), name,
                          font=theme.CHROME, fill=colour)
        if labels:
            for i, label in enumerate(labels[:length]):
                px = point(i, lo)[0]
                lw = draw.textlength(str(label), font=theme.CHROME)
                draw.text((px - lw / 2, ax_bottom + theme.px(8)), str(label), font=theme.CHROME, fill=theme.INK_SOFT)
        return Page(image=image, window=box, row_boxes=boxes)

    def resolve(needle: str):
        if labels:
            return [i for i, label in enumerate(labels) if needle.lower() in str(label).lower()][:1]
        return []
    return page_for, count, resolve


def _progress(base, rows, segment, accent):
    title, footer, source = segment.get("title"), segment.get("footer"), segment.get("source")
    unit = segment.get("unit", "%")
    peak = segment.get("max", 100.0)
    count = len(rows)

    def page_for(visible: int) -> Page:
        image, draw, box = _frame(base, title, footer, source, accent)
        left, top, right, bottom = box
        area = _plot_area(box, title is not None, source is not None, 0)
        ax_left, ax_top, ax_right, ax_bottom = area
        slot = (ax_bottom - ax_top) / max(count, 1)
        boxes = []
        for index, (label, value) in enumerate(rows):
            y = ax_top + slot * index + slot * 0.2
            bar_h = theme.px(26)
            track = (ax_left, round(y + theme.px(34)), ax_right, round(y + theme.px(34) + bar_h))
            boxes.append((left + theme.px(40), round(y), ax_right, round(y + slot * 0.8)))
            if index < visible:
                draw.text((ax_left, round(y)), label, font=theme.PANEL_LABEL, fill=theme.INK)
                pct = _fmt(value, unit)
                pw = draw.textlength(pct, font=theme.PANEL_VALUE)
                draw.text((ax_right - pw, round(y)), pct, font=theme.PANEL_VALUE, fill=accent)
                draw.rounded_rectangle(track, radius=bar_h // 2, fill=(230, 234, 242))
                filled = (min(value, peak) / peak) * (ax_right - ax_left)
                if filled > bar_h:
                    draw.rounded_rectangle((track[0], track[1], track[0] + round(filled), track[3]),
                                           radius=bar_h // 2, fill=_semantic(value, segment.get("thresholds", {}), accent))
        return Page(image=image, window=box, row_boxes=boxes)

    resolve = lambda needle: [i for i, (label, _) in enumerate(rows) if needle.lower() in label.lower()][:1]
    return page_for, count, resolve


def _sparkline(base, series, segment, accent):
    title, footer, source = segment.get("title"), segment.get("footer"), segment.get("source")
    count = len(series)

    def page_for(visible: int) -> Page:
        image, draw, box = _frame(base, title, footer, source, accent)
        area = _plot_area(box, title is not None, source is not None, theme.px(220))
        ax_left, ax_top, ax_right, ax_bottom = area
        slot = (ax_bottom - ax_top) / max(count, 1)
        boxes = []
        for index, (name, values) in enumerate(series):
            y0 = ax_top + slot * index
            y1 = y0 + slot * 0.7
            boxes.append((box[0] + theme.px(40), round(y0), ax_right, round(y1)))
            if index < visible and values:
                lo, hi = min(values), max(values)
                span = (hi - lo) or 1.0
                pts = [
                    (ax_left + (ax_right - ax_left) * i / max(len(values) - 1, 1),
                     y1 - (v - lo) / span * (y1 - y0))
                    for i, v in enumerate(values)
                ]
                draw.text((box[0] + theme.px(56), round((y0 + y1) / 2 - theme.CHROME.size / 2)),
                          name, font=theme.CHROME, fill=theme.INK)
                if len(pts) >= 2:
                    draw.line(pts, fill=accent, width=theme.px(3), joint="curve")
                draw.ellipse((pts[-1][0] - theme.px(6), pts[-1][1] - theme.px(6),
                              pts[-1][0] + theme.px(6), pts[-1][1] + theme.px(6)), fill=accent)
                last = _fmt(values[-1], segment.get("unit", ""))
                draw.text((ax_right + theme.px(12), round((y0 + y1) / 2 - theme.CHROME.size / 2)),
                          last, font=theme.CHROME, fill=theme.INK_SOFT)
        return Page(image=image, window=box, row_boxes=boxes)

    resolve = lambda needle: [i for i, (name, _) in enumerate(series) if needle.lower() in name.lower()][:1]
    return page_for, count, resolve


@style.scene("chart")
def prepare(segment, project, work, base, style_, palette):
    accent = palette["accent"]
    kind = segment.get("chart", "bar")
    if kind == "bar":
        return _bar(base, _read_rows(segment), segment, accent, horizontal=True)
    if kind == "column":
        return _bar(base, _read_rows(segment), segment, accent, horizontal=False)
    if kind == "line":
        return _line(base, _series(segment), segment, accent)
    if kind == "progress":
        return _progress(base, _read_rows(segment), segment, accent)
    if kind == "sparkline":
        return _sparkline(base, _series(segment), segment, accent)
    raise RuntimeError(f"unknown chart kind {kind!r}, have bar, column, line, progress, sparkline")
