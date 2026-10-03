"""A code diff as a scene, from a real repo, a pair of files or a patch.

Most demo videos in this kit are showing a change: a bug fixed, a guard added, a
function rewritten. The only way to show that today is a static card of the after
state, which proves nothing about what moved. This draws the change itself, added rows
on a green wash and removed on a red one, so the narration can point at the exact line.

Nothing is hand typed. A git range is run for real and the raw diff is kept in
artifacts the way term.py keeps stdout, a file pair is diffed with difflib, and a patch
is read from disk. The syntax colouring is reused from code.py so the code stays
readable through the wash.
"""

from __future__ import annotations

import difflib
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

import bg
import code as codecard
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


@dataclass
class Row:
    kind: str  # add | del | context | hunk | meta
    text: str
    old_no: int | None = None
    new_no: int | None = None


def _git_diff(repo: Path, rev: str, path: str | None, work: Path, name: str) -> str:
    """Run git diff for real and keep the raw output as the receipt."""
    # --no-renames so a moved file shows its real added and removed lines. With rename
    # detection on, git collapses a move to a header only "similarity index 100%" block,
    # which reads on screen as an empty diff and trips the no-change guard below.
    cmd = ["git", "-C", str(repo), "diff", "--no-color", "--no-renames", rev]
    if path:
        cmd += ["--", path]
    done = subprocess.run(cmd, capture_output=True, text=True, timeout=120, check=False)
    if done.returncode not in (0, 1):
        raise RuntimeError(f"git diff failed in {repo}: {done.stderr.strip()[:200]}")
    work.mkdir(parents=True, exist_ok=True)
    (work / f"{name}.diff").write_text(
        f"# git -C {repo} diff {rev} {path or ''}\n\n{done.stdout}", encoding="utf-8"
    )
    return done.stdout


def _file_pair(before: Path, after: Path) -> str:
    """A unified diff of two files, so a before and after pair reads like a real patch."""
    a = before.read_text(encoding="utf-8").splitlines(keepends=True)
    b = after.read_text(encoding="utf-8").splitlines(keepends=True)
    return "".join(difflib.unified_diff(a, b, fromfile=before.name, tofile=after.name, n=3))


def _parse(text: str, only_hunk: int | None) -> list[Row]:
    """Turn unified diff text into typed rows with old and new line numbers.

    Tracking both line numbers is what lets the split view line the two sides up and the
    unified view show an honest gutter. A `hunk` selector keeps one @@ block when a full
    file diff would overflow the panel.
    """
    rows: list[Row] = []
    old_no = new_no = 0
    hunk_index = -1
    for line in text.splitlines():
        if line.startswith("diff ") or line.startswith("index ") or line.startswith("--- ") or line.startswith("+++ "):
            if line.startswith(("--- ", "+++ ")):
                rows.append(Row("meta", line))
            continue
        if line.startswith("@@"):
            hunk_index += 1
            # parse @@ -a,b +c,d @@
            try:
                segment = line.split("@@")[1].strip()
                old_part, new_part = segment.split(" ")
                old_no = int(old_part[1:].split(",")[0])
                new_no = int(new_part[1:].split(",")[0])
            except (IndexError, ValueError):
                old_no = new_no = 1
            rows.append(Row("hunk", line))
            continue
        if only_hunk is not None and hunk_index != only_hunk and hunk_index >= 0:
            # still advance counters so a later selected hunk stays honest
            if line.startswith("+"):
                new_no += 1
            elif line.startswith("-"):
                old_no += 1
            else:
                old_no += 1
                new_no += 1
            continue
        if line.startswith("+"):
            rows.append(Row("add", line[1:], None, new_no)); new_no += 1
        elif line.startswith("-"):
            rows.append(Row("del", line[1:], old_no, None)); old_no += 1
        else:
            rows.append(Row("context", line[1:] if line.startswith(" ") else line, old_no, new_no))
            old_no += 1; new_no += 1
    return rows


# The wash sits under the code, so it has to be light enough to read through. motion.mark
# blends ink at 0.15 for exactly this reason, so the diff washes stay in the same range.
def _wash(kind: str) -> tuple[int, int, int] | None:
    if kind == "add":
        g = theme.GREEN
        return _tint(g)
    if kind == "del":
        r = theme.RED
        return _tint(r)
    return None


def _tint(colour: tuple[int, int, int]) -> tuple[int, int, int]:
    """A very pale version of a semantic colour, for the row background."""
    return tuple(round(c + (255 - c) * 0.82) for c in colour)


def _panel_box(row_count: int) -> tuple[int, int, int, int]:
    width, height = theme.CANVAS
    margin = theme.WINDOW_MARGIN
    line_h = theme.px(40)
    body = min(height - theme.px(240), max(theme.px(360), row_count * line_h + theme.px(150)))
    top = max(theme.px(110), (height - body) // 2)
    return (margin + theme.px(30), top, width - margin - theme.px(30), top + body)


def _header(draw, box, title, accent):
    left, top, right, _ = box
    draw.rounded_rectangle(box, radius=theme.px(30), fill=theme.PANEL, outline=theme.PANEL_EDGE, width=3)
    draw.rounded_rectangle((left, top, right, top + theme.px(74)), radius=theme.px(30), fill=theme.CHROME_BAR)
    draw.rectangle((left, top + theme.px(44), right, top + theme.px(74)), fill=theme.CHROME_BAR)
    draw.text((left + theme.px(44), top + theme.px(24)), title, font=theme.CHROME, fill=theme.INK_SOFT)


def _render_unified(base, rows, title, accent):
    count = len(rows)

    def page_for(visible: int) -> Page:
        image = base.copy()
        box = _panel_box(count)
        bg.drop_shadow(image, box, radius=theme.px(30))
        draw = ImageDraw.Draw(image)
        _header(draw, box, title, accent)
        left, top, right, bottom = box
        gutter = left + theme.px(150)
        y = top + theme.px(100)
        line_h = theme.px(40)
        boxes: list[tuple[int, int, int, int]] = []
        for index, row in enumerate(rows):
            boxes.append((left + theme.px(24), y - theme.px(4), right - theme.px(24), y + theme.px(34)))
            if index < visible:
                wash = _wash(row.kind)
                if wash:
                    draw.rectangle((left + theme.px(16), y - theme.px(4), right - theme.px(16), y + theme.px(34)), fill=wash)
                if row.kind == "hunk":
                    draw.text((left + theme.px(44), y), row.text, font=theme.CODE_SMALL, fill=theme.VIOLET)
                elif row.kind == "meta":
                    draw.text((left + theme.px(44), y), row.text, font=theme.CODE_SMALL, fill=theme.INK_SOFT)
                else:
                    old = f"{row.old_no:>4}" if row.old_no else "    "
                    new = f"{row.new_no:>4}" if row.new_no else "    "
                    draw.text((left + theme.px(20), y), old, font=theme.CODE_SMALL, fill=(196, 204, 216))
                    draw.text((left + theme.px(80), y), new, font=theme.CODE_SMALL, fill=(196, 204, 216))
                    sign = {"add": "+", "del": "-"}.get(row.kind, " ")
                    sign_col = {"add": theme.GREEN, "del": theme.RED}.get(row.kind, theme.INK_SOFT)
                    draw.text((gutter, y), sign, font=theme.CODE_SMALL, fill=sign_col)
                    x = gutter + theme.px(26)
                    for text, colour in codecard._spans(row.text):
                        draw.text((x, y), text, font=theme.CODE_SMALL, fill=colour)
                        x += draw.textlength(text, font=theme.CODE_SMALL)
            y += line_h
            if y > bottom - theme.px(50):
                break
        while len(boxes) < count:
            boxes.append(boxes[-1] if boxes else box)
        return Page(image=image, window=box, row_boxes=boxes)

    return page_for, count


def _render_split(base, rows, title, accent):
    count = len(rows)

    def page_for(visible: int) -> Page:
        image = base.copy()
        box = _panel_box(count)
        bg.drop_shadow(image, box, radius=theme.px(30))
        draw = ImageDraw.Draw(image)
        _header(draw, box, title, accent)
        left, top, right, bottom = box
        mid = (left + right) // 2
        draw.line((mid, top + theme.px(78), mid, bottom - theme.px(10)), fill=(226, 231, 240), width=2)
        y = top + theme.px(100)
        line_h = theme.px(40)
        boxes: list[tuple[int, int, int, int]] = []
        for index, row in enumerate(rows):
            boxes.append((left + theme.px(20), y - theme.px(4), right - theme.px(20), y + theme.px(34)))
            if index < visible:
                if row.kind in ("del", "context"):
                    if row.kind == "del":
                        draw.rectangle((left + theme.px(16), y - theme.px(4), mid - theme.px(6), y + theme.px(34)), fill=_tint(theme.RED))
                    _spans_at(draw, left + theme.px(24), y, row, "old")
                if row.kind in ("add", "context"):
                    if row.kind == "add":
                        draw.rectangle((mid + theme.px(6), y - theme.px(4), right - theme.px(16), y + theme.px(34)), fill=_tint(theme.GREEN))
                    _spans_at(draw, mid + theme.px(24), y, row, "new")
                if row.kind in ("hunk", "meta"):
                    draw.text((left + theme.px(44), y), row.text, font=theme.CODE_SMALL,
                              fill=theme.VIOLET if row.kind == "hunk" else theme.INK_SOFT)
            y += line_h
            if y > bottom - theme.px(50):
                break
        while len(boxes) < count:
            boxes.append(boxes[-1] if boxes else box)
        return Page(image=image, window=box, row_boxes=boxes)

    return page_for, count


def _spans_at(draw, x0, y, row, side):
    no = row.old_no if side == "old" else row.new_no
    draw.text((x0, y), f"{no:>4}" if no else "    ", font=theme.CODE_SMALL, fill=(196, 204, 216))
    x = x0 + theme.px(60)
    for text, colour in codecard._spans(row.text):
        draw.text((x, y), text, font=theme.CODE_SMALL, fill=colour)
        x += draw.textlength(text, font=theme.CODE_SMALL)


@style.scene("diff")
def prepare(segment, project, work, base, style_, palette):
    accent = palette["accent"]
    if "repo" in segment:
        raw = _git_diff(Path(segment["repo"]), segment.get("rev", "HEAD~1..HEAD"),
                        segment.get("file"), work, segment.get("name", "diff"))
        provenance = f"git diff {segment.get('rev', 'HEAD~1..HEAD')}  {segment.get('file', '')}".strip()
    elif "before" in segment and "after" in segment:
        raw = _file_pair(Path(segment["before"]), Path(segment["after"]))
        provenance = f"{Path(segment['before']).name} -> {Path(segment['after']).name}"
    elif "patch" in segment:
        raw = Path(segment["patch"]).read_text(encoding="utf-8")
        provenance = Path(segment["patch"]).name
    else:
        raise RuntimeError("diff scene needs one of: repo+rev, before+after, or patch")

    rows = _parse(raw, segment.get("hunk"))
    limit = segment.get("max_lines", 26)
    if len(rows) > limit:
        rows = rows[:limit] + [Row("meta", f"... {len(rows) - limit} more lines in {segment.get('name', 'the diff')}.diff")]
    if not any(r.kind in ("add", "del") for r in rows):
        raise RuntimeError(f"diff {segment.get('name')} has no added or removed lines, nothing to show")

    title = segment.get("title", provenance)
    mode = segment.get("mode", "unified")
    # split needs two columns, which is unreadable in portrait, so fall back to unified there
    if mode == "split" and theme.CANVAS[0] < theme.CANVAS[1]:
        mode = "unified"
    page_for, count = (_render_split if mode == "split" else _render_unified)(base, rows, title, accent)

    def resolve(needle: str) -> list[int]:
        return [i for i, row in enumerate(rows) if needle in row.text][:1]

    return page_for, count, resolve
