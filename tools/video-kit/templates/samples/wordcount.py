"""A small CLI that does real work on a real file, for the cli-tool template.

    python3 wordcount.py <file>

Prints line, word and character counts, then the five most common words. It reads a
file on disk and computes the numbers, so a terminal scene pointed at it shows a
command doing genuine work rather than printing a canned banner.
"""

import collections
import re
import sys
from pathlib import Path


def main(target: str) -> int:
    path = Path(target)
    if not path.exists():
        print(f"wordcount: {target}: no such file")
        return 1
    text = path.read_text(encoding="utf-8", errors="replace")
    words = re.findall(r"[A-Za-z']+", text.lower())
    counts = collections.Counter(words)
    print(f"file    {path.name}")
    print(f"lines   {text.count(chr(10)) + 1}")
    print(f"words   {len(words)}")
    print(f"chars   {len(text)}")
    print("top words")
    for word, count in counts.most_common(5):
        bar = "#" * min(count, 40)
        print(f"  {word:<12} {count:>4}  {bar}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: wordcount.py <file>")
    raise SystemExit(main(sys.argv[1]))
