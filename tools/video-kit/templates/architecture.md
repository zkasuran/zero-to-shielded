# architecture

How a system fits together. Built around the `diagram` scene. Use it when the first thing
a judge needs is the shape of the thing, not a feature.

## The spine

1. `card` title. Names the system and the one hard part.
2. `diagram` topology. Nodes and edges, revealed one at a time so the narration walks it.
3. `term` proof. One real run behind one of the boxes, so the diagram is not just a
   drawing.
4. `card` close. The one design decision worth remembering.

## Why this shape

A diagram alone is a claim. Following it with a real run of one node is what makes the
claim check out. Reveal order matters: nodes come first in declaration order, then edges,
so the narration can name a box before the wire that leaves it.

## The diagram scene

Nodes are declared inline, so this scene needs no external file. Each node has:

- `id`: unique, used by edges and by focus needles.
- `label`: what it says on screen. Falls back to `id`.
- `kind`: `box`, `service`, `store`, `decision`, `actor` or `cloud`. The shape carries the
  kind, so a store reads as a cylinder and a decision as a diamond.
- `highlight`: `red`, `green` or `amber` to colour one node.
- `note`: a small caption under the node.
- `at`: `[col, row]` to pin a node to a grid cell instead of letting the layout place it.

Edges have `from` and `to` (both must be node ids, or the scene raises), an optional
`label`, `highlight`, `style` (`thick` or `dashed`), `route` (`straight` or `elbow`) and
`both` for a double arrow.

`layout` is `flow` (lanes left to right, the default), `stack` (top to bottom), `grid` or
`hub` (first node centred, the rest on a ring). The graph is measured after placement and
scaled to fit, so a wide graph shrinks rather than running off the edge.

A focus needle matches a node id or label, then an edge label.

## What to swap

- `palette`: a free one.
- The whole `nodes` and `edges` list, rewritten to your real system.
- The `term` proof scene, pointed at a real command in your repo.
- Every `TODO`.
