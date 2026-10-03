"""Run a real command and keep its output.

The command is executed for real, its stdout and stderr are saved verbatim to
artifacts, and only a viewport of that captured text is ever shown. Nothing on
screen is typed by hand, so a line in the video can always be traced back to a line
the program printed.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from textwrap import wrap

WRAP_AT = 104
MAX_LINES = 26
TIMEOUT = 900
_CACHE: dict[tuple[str, str], str] = {}


def capture(cwd: Path, cmd: list[str], artifacts: Path, name: str) -> str:
    """Run the command once per build and keep the raw output for auditing.

    Output goes straight to the artifact file rather than through a pipe. A demo
    script that follows its own log in the background (`tail -f | grep &`) can leave
    that follower running after the script exits, and a lingering child holds the
    pipe open, so reading to end of file waits for a process that will never finish.
    A file cannot be held open against us, and it is the receipt we wanted anyway.
    """
    key = (str(cwd), " ".join(cmd))
    if key not in _CACHE:
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / f"{name}.command").write_text(f"cd {cwd}\n{' '.join(cmd)}\n", encoding="utf-8")
        log = artifacts / f"{name}.stdout"
        with log.open("w", encoding="utf-8") as sink:
            subprocess.run(
                cmd, cwd=cwd, stdout=sink, stderr=subprocess.STDOUT, timeout=TIMEOUT, check=False
            )
        _CACHE[key] = log.read_text(encoding="utf-8", errors="replace")
    return _CACHE[key]


def slice_output(
    output: str, start: str | None, end: str | None, limit: int = MAX_LINES, wrap_at: int = WRAP_AT
) -> list[str]:
    """A viewport into the captured output. Never a rewrite of it.

    `wrap_at` exists because a fixed column breaks a printed table: a report row that
    ends in a sha256 is wider than the default and wrapping it turns one row into two.
    Widen it per segment rather than editing the program that printed it. About 120
    monospace columns still fit inside the window, so that is the ceiling.
    """
    lines = output.splitlines()
    first = 0
    if start is not None:
        first = next((index for index, line in enumerate(lines) if start in line), 0)
    last = len(lines)
    if end is not None:
        last = next(
            (index + 1 for index, line in enumerate(lines[first:], first) if end in line),
            len(lines),
        )
    view: list[str] = []
    for line in lines[first:last]:
        # Keep a wrapped line under its own column. Without this the continuation starts
        # at the left margin and a long value reads as a broken row rather than one line.
        indent = line[: len(line) - len(line.lstrip())]
        view.extend(
            wrap(line, width=wrap_at, drop_whitespace=False, subsequent_indent=indent + "  ")
            or [""]
        )
    if len(view) > limit:
        view = view[:limit] + [f"... [{len(view) - limit} more lines in the captured output]"]
    return view
