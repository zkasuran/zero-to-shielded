# CALL-E video kit

A generator for demo videos. It takes a project file that names scenes, real files and
narration then renders a narrated, captioned mp4 plus the upload package a submission form
asks for. Everything on screen is drawn or captured from something real: a command that
ran, a source file, a live page, a measured number. Nothing is a stock template with the
words swapped.

## Five minute start

```bash
python3 scaffold.py my-demo /path/to/app "What it does in one line." --template product-demo
python3 preflight.py projects/my-demo.json     # draws every scene once, resolves every focus needle
MUSIC=~/Downloads/joyinsound-no-copyright-music-398375.mp3 python3 build.py projects/my-demo.json
python3 upload.py projects/my-demo.json         # thumbnail, captions, chapters, a click-to-copy page
```

`scaffold.py` copies a genre template, claims a theme and a thumbnail layout no other
project uses, inspects the app directory to suggest a scene spine then prints the exact
next commands. Replace the template's sample paths with your app's real URL, files and
commands, then preflight and build.

## What a video is made of

A project file is JSON: an id, a palette, a voice and a list of segments. Each segment is
one scene. The full reference for every key is `docs/project-file.md`.

```json
{
  "id": "my-demo",
  "palette": "harbour",
  "voice": "en-US-AndrewNeural",
  "segments": [
    {"type": "card", "lines": ["What it does."], "narration": ["The opening line."]},
    {"type": "code", "file": "src/gate.ts", "from": "function verify", "to": "^}",
     "title": "the check", "narration": [{"text": "It verifies before it acts.", "focus": "verify"}]}
  ]
}
```

Audio comes first. Every narration cue is synthesised and measured, then each segment is
sized to the words it carries, so nothing drifts and nothing is clipped. A cue can name the
line it is about with `focus` and the frame zooms to that line, a highlighter sweeps it and
a cursor walks over and clicks, all timed to the voice.

## Scenes

| type | shows | reads |
| --- | --- | --- |
| `card` | a title or caption card | its own lines |
| `term` | a terminal window | the captured stdout of a real command |
| `code` | a source file with light syntax colour | a real file, sliced by line or marker |
| `web` | a viewport of a live page | a real Chromium screenshot |
| `diff` | a code change, added green and removed red | a git range, a file pair or a patch |
| `chart` | bar, column, line, sparkline or progress | a real JSON or CSV file |
| `diagram` | nodes and edges of an architecture | a declarative spec |
| `device` | a page inside a phone, tablet, laptop or browser frame | a capture or a still |
| `compose` | two or more scenes in one frame | its panes, each a full scene |
| `overlay` | lower thirds, callouts, badges and stat blocks | a base scene or the field |
| `panel` `grid` `report` `bubbles` `chips` `receipts` | step lists, matrices, reports, transcripts | a real ledger or report file |

Every scene returns its image, its window box and the pixel box of each row, so one painter
drives the zoom, the marker and the cursor for all of them. Adding a scene type is one
module that registers with `@style.scene("name")`, never an edit to `build.py`.

## Look, aspect and quality

One theme per video, never reused, so a set never reads as one template. `theme.py` holds
the palette roster: gradient ends, an accent, a highlighter mark, three blobs and a field
shape. `preflight.py` fails two projects on the same theme. A palette can be generated and
checked with `contrast.py`, which enforces WCAG contrast and keeps red apart from green
under the common colour-vision deficiencies, because a refusal being red and a pass being
green is the whole visual grammar.

A project renders at any aspect (`16:9`, `9:16`, `1:1`, `4:5`) and any quality tier
(`draft`, `standard`, `high`, `max`). One project can emit several cuts at once with a
`renders` list, so a landscape master and a vertical short come from the same scenes.
Segments join with a hard cut by default. A crossfade, dip, wipe or slide joins them when a
segment asks for one, so the narration stays pinned to the composited timeline so a dissolve never
slides the voice out of sync.

## The upload package

```bash
python3 upload.py projects/my-demo.json
```

`upload.py` writes `artifacts/<id>/upload/`: the thumbnail, `captions.srt` and `chapters.txt`
at the times the build measured, plus `UPLOAD-<id>.html`, one self-contained page with a copy
button per field and a live character count against each platform's real limit. It reads the
timing the build recorded, so a timestamp in the page is a timestamp in the file rather than
a re-derived guess. It exits non-zero when a limit is broken. A project can carry an
`upload.platforms` map to get a copy block per surface, YouTube, Shorts, X, LinkedIn and Devpost, each held to the limit that platform actually enforces.

## Voices and music

`edge-tts` is the default and costs nothing. A project can set one voice, name a roster of speakers or override the voice, rate, pitch and
engine on a single cue, so a video can have
a narrator plus a second voice for a quoted line. Where the engine reports word timings the
karaoke caption style tracks the read word by word. `minimax`, `fish` and `gmi` are the
paid alternatives, switched with `VOICE_ENGINE`.

Music loops under the narration, fades in and out and is sidechain ducked against the voice,
so the bed moves out of the way rather than the voice being pulled down. Only ship a track
whose licence can be pointed at. The house track is the no-copyright
`joyinsound-no-copyright-music-398375.mp3`.

## Verified

The audio was measured on the finished files, not assumed:

| Video | Integrated | True peak |
| --- | --- | --- |
| phone-approval-gate | -16.1 LUFS | -2.0 dBTP |
| multi-party-scheduler | -16.0 LUFS | -1.9 dBTP |
| call-on-behalf | -16.0 LUFS | -2.0 dBTP |
| moonwalk | -16.2 LUFS | -1.9 dBTP |

A sample-domain limiter at -1.5 dBFS still measured -1.4 dBTP, because true peak counts
inter-sample peaks a sample limiter cannot see, so the final stage is
`alimiter=limit=0.79:level=disabled` after the normalisation. `level=disabled` matters:
ffmpeg's limiter auto-levels up to its own ceiling by default, which pushed one mix to
-0.0 dBTP before it was switched off.

Backgrounds are generated rather than downloaded, so there is no image licence to defend,
and the field is cached per canvas so a rebuild is fast. Cue audio is cached under a digest
of the engine, voice, rate, pitch and words, so an edited line is re-read and an unchanged
line is never paid for twice.

## Tests

```bash
python3 -m pytest tests -q          # the suite
python3 schema.py projects/*.json   # validate every project file
python3 contrast.py                 # audit every palette for contrast and colour blindness
python3 tests/test_golden.py --update   # regenerate the golden frame digests, deliberately
```

The golden suite renders the pure scenes and compares a SHA256 per frame against a stored
manifest, so a refactor that moves a line by two pixels fails a test rather than shipping a
changed video.

## Files

`style.py` is the resolved config for one build and the scene registry. `theme.py` holds
the palette roster and rebinds the look constants per project. `bg.py` draws the field.
`build.py` measures the audio, lays out the timing and assembles. `transition.py` joins the
pieces. `motion.py` does the easing, camera moves, marker, cursor, captions and progress.
`voice.py` does the narration and the mix. The scene renderers are `scene.py`, `cards.py`,
`code.py`, `diff.py`, `chart.py`, `diagram.py`, `device.py`, `compose.py`, `doc.py`,
`grid.py`, `panel.py`, `web.py` and `receipt.py`. `thumb.py` and `upload.py` build the
upload package. `preflight.py`, `frame.py` and `schema.py` are the pre-render gates.
`scaffold.py` starts a new project. The genre templates are in `templates/`, the full
reference is in `docs/`.

The first shipped set, the CALL-E hackathon videos and the handoff notes for them, is in
`HISTORY.md`.
