"""Regenerate NARRATION-MANIFEST.md from the project files.

    python3 manifest.py projects/*.json

The manifest is the fallback path for reading narration by hand (the Fish Audio web
app, or any other recorder) instead of through the API: save each clip at the path in
the table and rebuild with AUDIO_ONLY=1. Cue files are keyed by a digest of the
engine, the voice, the rate and the words, so the paths have to be generated from the
same projects the build reads. Editing this by hand goes stale on the first reword.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import build
import voice

ROOT = Path(__file__).resolve().parent
ENGINE = "fish"

HEAD = """# Narration manifest

One row per cue. To read the narration by hand instead of through the API, save each
clip as mp3 at exactly the path in the first column, then rebuild the sound only:

```bash
VOICE_ENGINE=fish MUSIC=~/Downloads/joyinsound-no-copyright-music-398375.mp3 \\
  AUDIO_ONLY=1 python3 build.py projects/<project>.json
```

The build reads the real duration of each file and lays the video out around it, so
clips do not need to match any target length. Paths carry a digest of the engine, the
voice, the rate and the words, which is why this file is generated: run
`python3 manifest.py projects/*.json` after any narration edit.
"""


def rows(path: Path) -> tuple[str, list[tuple[str, str]], int]:
    project = json.loads(path.read_text(encoding="utf-8"))
    speaker = project.get("fish_voice", project.get("voice", voice.VOICE))
    rate = project.get("rate", voice.RATE)
    out: list[tuple[str, str]] = []
    for index, segment in enumerate(project["segments"]):
        for position, (text, _focus, _raw) in enumerate(build.entries(segment)):
            stamp = hashlib.sha256(f"{ENGINE}|{speaker}|{rate}|{text}".encode("utf-8")).hexdigest()[:10]
            name = f"cue-{index:02d}-{position:02d}-{ENGINE}-{stamp}.mp3"
            out.append((f"artifacts/{project['id']}/{name}", text))
    return project["id"], out, sum(len(text) for _, text in out)


def main(paths: list[Path]) -> None:
    blocks: list[str] = []
    cues = characters = 0
    for path in paths:
        name, table, size = rows(path)
        cues += len(table)
        characters += size
        lines = [f"\n## {name}\n", f"{len(table)} cues, {size} characters.\n",
                 "| file | line |", "| --- | --- |"]
        lines += [f"| `{where}` | {text} |" for where, text in table]
        blocks.append("\n".join(lines) + "\n")
    body = HEAD + f"\nAcross every project here: {cues} cues, {characters} characters.\n" + "".join(blocks)
    (ROOT / "NARRATION-MANIFEST.md").write_text(body, encoding="utf-8")
    print(f"NARRATION-MANIFEST.md  {cues} cues, {characters} characters")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("usage: manifest.py <project.json> [more.json ...]")
    main([Path(argument) for argument in sys.argv[1:]])
