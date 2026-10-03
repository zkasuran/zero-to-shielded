"""Architecture diagrams as a scene: nodes and edges from a declarative spec.

Every scene in the kit shows output, code or a page. None of them show how a system
fits together, which is the first thing a judge wants in the opening thirty seconds.
This draws that: boxes, services, stores, actors and decisions, wired by labelled
edges, revealed one element at a time so the narration can walk the architecture.

The graph is measured after placement and scaled to fit the canvas with a margin, so a
wide graph shrinks rather than running off the edge. An edge naming an endpoint that is
not a node raises, because a diagram that silently drops a wire is worse than one that
fails loudly.
"""

from __future__ import annotations

import math
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


# A node is a unit box in a virtual grid before it is scaled to the canvas. Sizes are in
# reference-canvas pixels so they scale like the rest of the kit.
NODE_W = 300
NODE_H = 150
GAP_X = 150
GAP_Y = 130


def _auto_place(nodes: list[dict], layout: str) -> dict[str, tuple[int, int]]:
    """Give every node a grid cell when the spec did not pin one with `at`.

    flow lays lanes left to right, stack top to bottom, grid honours explicit cells, and
    hub puts the first node in the middle with the rest on a ring. The cells are virtual,
    the pixel placement happens later, so this only has to be consistent not final.
    """
    placed: dict[str, tuple[int, int]] = {}
    free = [n for n in nodes if "at" not in n]
    for node in nodes:
        if "at" in node:
            placed[node["id"]] = tuple(node["at"])

    if layout == "hub" and nodes:
        centre = nodes[0]
        placed.setdefault(centre["id"], (0, 0))
        spokes = [n for n in nodes[1:] if n["id"] not in placed]
        for index, node in enumerate(spokes):
            angle = 2 * math.pi * index / max(len(spokes), 1)
            placed[node["id"]] = (round(3 * math.cos(angle)), round(3 * math.sin(angle)))
        return placed

    if layout == "stack":
        for row, node in enumerate(free):
            placed.setdefault(node["id"], (0, row))
        return placed

    if layout == "grid":
        width = max(1, math.ceil(math.sqrt(len(free))))
        for index, node in enumerate(free):
            placed.setdefault(node["id"], (index % width, index // width))
        return placed

    # flow: lanes left to right, wrapping so a long pipe does not run off the canvas
    per_col = max(1, math.ceil(len(free) / max(1, math.ceil(len(free) / 4))))
    for index, node in enumerate(free):
        placed.setdefault(node["id"], (index // per_col, index % per_col))
    return placed


def _fit(cells: dict[str, tuple[int, int]], area: tuple[int, int, int, int]):
    """Map virtual grid cells to pixel node boxes, scaled to fit the plot area.

    The node keeps a fixed aspect: the scale is the smaller of the x and y fits, so a
    graph that is wide and short does not get stretched tall. Returns a function from a
    node id to its pixel box.
    """
    xs = [c[0] for c in cells.values()]
    ys = [c[1] for c in cells.values()]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = (max_x - min_x) * (NODE_W + GAP_X) + NODE_W
    span_y = (max_y - min_y) * (NODE_H + GAP_Y) + NODE_H
    left, top, right, bottom = area
    avail_w, avail_h = right - left, bottom - top
    scale = min(avail_w / span_x, avail_h / span_y, 1.6)
    node_w, node_h = NODE_W * scale, NODE_H * scale
    step_x, step_y = (NODE_W + GAP_X) * scale, (NODE_H + GAP_Y) * scale
    used_w = (max_x - min_x) * step_x + node_w
    used_h = (max_y - min_y) * step_y + node_h
    off_x = left + (avail_w - used_w) / 2
    off_y = top + (avail_h - used_h) / 2

    def box_of(node_id: str) -> tuple[float, float, float, float]:
        cx, cy = cells[node_id]
        x = off_x + (cx - min_x) * step_x
        y = off_y + (cy - min_y) * step_y
        return (x, y, x + node_w, y + node_h)

    return box_of, node_w, node_h


def _wrap(draw, text: str, font, max_width: float) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else current + " " + word
        if draw.textlength(trial, font=font) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_node(draw, box, node, accent, highlight):
    """One node in the flat bright style, its shape carrying its kind."""
    left, top, right, bottom = box
    cx, cy = (left + right) / 2, (top + bottom) / 2
    kind = node.get("kind", "box")
    edge = {"red": theme.RED, "green": theme.GREEN, "amber": theme.AMBER}.get(highlight, accent)
    fill = theme.PANEL
    width = max(2, theme.px(3))
    radius = theme.px(18)

    if kind == "store":
        # a cylinder: two ellipse caps and a body
        ry = (bottom - top) * 0.16
        draw.rectangle((left, top + ry, right, bottom - ry), fill=fill, outline=None)
        draw.ellipse((left, bottom - 2 * ry, right, bottom), fill=fill, outline=edge, width=width)
        draw.rectangle((left, top + ry, right, bottom - ry), fill=fill)
        draw.line((left, top + ry, left, bottom - ry), fill=edge, width=width)
        draw.line((right, top + ry, right, bottom - ry), fill=edge, width=width)
        draw.ellipse((left, top, right, top + 2 * ry), fill=fill, outline=edge, width=width)
    elif kind == "decision":
        draw.polygon([(cx, top), (right, cy), (cx, bottom), (left, cy)], fill=fill, outline=edge)
        for pair in (((cx, top), (right, cy)), ((right, cy), (cx, bottom)),
                     ((cx, bottom), (left, cy)), ((left, cy), (cx, top))):
            draw.line(pair, fill=edge, width=width)
    elif kind == "cloud":
        draw.rounded_rectangle(box, radius=(bottom - top) // 2, fill=fill, outline=edge, width=width)
    elif kind == "actor":
        head_r = (bottom - top) * 0.16
        draw.ellipse((cx - head_r, top, cx + head_r, top + 2 * head_r), fill=fill, outline=edge, width=width)
        draw.line((cx, top + 2 * head_r, cx, bottom - head_r * 1.4), fill=edge, width=width)
        draw.line((cx - head_r * 1.6, (top + bottom) / 2, cx + head_r * 1.6, (top + bottom) / 2), fill=edge, width=width)
        draw.line((cx, bottom - head_r * 1.4, cx - head_r * 1.4, bottom), fill=edge, width=width)
        draw.line((cx, bottom - head_r * 1.4, cx + head_r * 1.4, bottom), fill=edge, width=width)
    elif kind == "service":
        draw.rounded_rectangle(box, radius=radius, fill=fill, outline=edge, width=max(width, theme.px(4)))
        draw.line((left + radius, top + theme.px(8), right - radius, top + theme.px(8)), fill=edge, width=theme.px(4))
    else:  # box
        draw.rectangle(box, fill=fill, outline=edge, width=width)

    label = node.get("label", node["id"])
    font = theme.PANEL_LABEL
    lines = _wrap(draw, label, font, (right - left) - theme.px(24))
    # shrink the label rather than overflow the node
    while lines and len(lines) * (font.size + theme.px(6)) > (bottom - top) - theme.px(16) and font.size > 16:
        font = theme.font(theme.SANS_BOLD, font.size - 2)
        lines = _wrap(draw, label, font, (right - left) - theme.px(24))
    total_h = len(lines) * (font.size + theme.px(6))
    y = cy - total_h / 2
    ink = edge if highlight else theme.INK
    for line in lines:
        lw = draw.textlength(line, font=font)
        draw.text((cx - lw / 2, y), line, font=font, fill=ink)
        y += font.size + theme.px(6)
    note = node.get("note")
    if note:
        nw = draw.textlength(note, font=theme.CHROME)
        draw.text((cx - nw / 2, bottom + theme.px(6)), note, font=theme.CHROME, fill=theme.INK_SOFT)


def _anchor(box, other_centre):
    """Where an edge meets a node border, on the side facing the other node."""
    left, top, right, bottom = box
    cx, cy = (left + right) / 2, (top + bottom) / 2
    dx, dy = other_centre[0] - cx, other_centre[1] - cy
    if abs(dx) < 1 and abs(dy) < 1:
        return (cx, cy)
    # scale to the box border, whichever edge the ray hits first
    scale_x = (right - cx) / abs(dx) if dx else math.inf
    scale_y = (bottom - cy) / abs(dy) if dy else math.inf
    scale = min(scale_x, scale_y)
    return (cx + dx * scale, cy + dy * scale)


def _draw_edge(draw, a_box, b_box, edge, accent):
    ca = ((a_box[0] + a_box[2]) / 2, (a_box[1] + a_box[3]) / 2)
    cb = ((b_box[0] + b_box[2]) / 2, (b_box[1] + b_box[3]) / 2)
    start = _anchor(a_box, cb)
    end = _anchor(b_box, ca)
    colour = {"red": theme.RED, "green": theme.GREEN, "amber": theme.AMBER}.get(
        edge.get("highlight"), theme.INK_SOFT)
    width = theme.px(6) if edge.get("style") == "thick" else theme.px(3)
    dash = edge.get("style") == "dashed"

    routing = edge.get("route", "straight")
    if routing == "elbow":
        mid_x = (start[0] + end[0]) / 2
        pts = [start, (mid_x, start[1]), (mid_x, end[1]), end]
    else:
        pts = [start, end]

    if dash:
        _dashed(draw, pts, colour, width)
    else:
        draw.line(pts, fill=colour, width=width, joint="curve")

    # arrowhead at the end, pointing along the last segment
    _arrow(draw, pts[-2], pts[-1], colour, theme.px(16))
    if edge.get("both"):
        _arrow(draw, pts[1], pts[0], colour, theme.px(16))

    label = edge.get("label")
    if label:
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
        lw = draw.textlength(label, font=theme.CHROME)
        pad = theme.px(8)
        draw.rectangle((mx - lw / 2 - pad, my - theme.CHROME.size / 2 - pad // 2,
                        mx + lw / 2 + pad, my + theme.CHROME.size / 2 + pad // 2),
                       fill=theme.PANEL)
        draw.text((mx - lw / 2, my - theme.CHROME.size / 2), label, font=theme.CHROME, fill=colour)


def _dashed(draw, pts, colour, width):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        if length == 0:
            continue
        step = theme.px(24)
        count = max(1, int(length // step))
        for i in range(count):
            if i % 2:
                continue
            t0, t1 = i / count, min((i + 1) / count, 1.0)
            draw.line((x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0,
                       x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1), fill=colour, width=width)


def _arrow(draw, tail, head, colour, size):
    angle = math.atan2(head[1] - tail[1], head[0] - tail[0])
    for spread in (math.radians(150), math.radians(-150)):
        draw.line((head[0], head[1],
                   head[0] + size * math.cos(angle + spread),
                   head[1] + size * math.sin(angle + spread)), fill=colour, width=theme.px(3))


@style.scene("diagram")
def prepare(segment, project, work, base, style_, palette):
    accent = palette["accent"]
    nodes = segment["nodes"]
    edges = segment.get("edges", [])
    layout = segment.get("layout", "flow")
    ids = {node["id"] for node in nodes}
    for edge in edges:
        for end in (edge["from"], edge["to"]):
            if end not in ids:
                raise RuntimeError(f"diagram edge names unknown node {end!r}, have {sorted(ids)}")

    cells = _auto_place(nodes, layout)
    width, height = theme.CANVAS
    margin = theme.WINDOW_MARGIN
    title = segment.get("title")
    area = (margin, margin + (theme.px(80) if title else 0), width - margin,
            height - margin - (theme.px(40) if segment.get("footer") else 0))
    box_of, _, _ = _fit(cells, area)
    node_boxes = {node["id"]: box_of(node["id"]) for node in nodes}
    order = nodes + edges  # reveal nodes first, then edges, in declaration order
    count = len(order)

    def page_for(visible: int) -> Page:
        image = base.copy()
        draw = ImageDraw.Draw(image)
        if title:
            draw.text((margin, margin), title, font=theme.KICKER, fill=accent)
        footer = segment.get("footer")
        if footer:
            draw.text((margin, height - margin - theme.px(4)), footer, font=theme.CHROME, fill=theme.INK_SOFT)
        # edges under nodes, but only those whose reveal index has arrived
        for index, edge in enumerate(edges):
            if len(nodes) + index < visible:
                _draw_edge(draw, node_boxes[edge["from"]], node_boxes[edge["to"]], edge, accent)
        for index, node in enumerate(nodes):
            if index < visible:
                _draw_node(draw, node_boxes[node["id"]], node, accent, node.get("highlight"))
        boxes = [tuple(round(v) for v in node_boxes[node["id"]]) for node in nodes]
        for edge in edges:
            a, b = node_boxes[edge["from"]], node_boxes[edge["to"]]
            boxes.append((round(min(a[0], b[0])), round(min(a[1], b[1])),
                          round(max(a[2], b[2])), round(max(a[3], b[3]))))
        return Page(image=image, window=None, row_boxes=boxes)

    def resolve(needle: str) -> list[int]:
        low = needle.lower()
        for index, node in enumerate(nodes):
            if low in node["id"].lower() or low in node.get("label", "").lower():
                return [index]
        for index, edge in enumerate(edges):
            if low in edge.get("label", "").lower():
                return [len(nodes) + index]
        return []

    return page_for, count, resolve
