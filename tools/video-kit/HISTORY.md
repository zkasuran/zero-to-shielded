# CALL-E demo videos: build kit and handoff

Three finished videos, built from the real apps. Upload is the only step left, and
it needs a browser login, so it is yours.

This kit is the house standard for every demo video from here on. The rule that
governs it, including the one-line ask before any video is built and the register of
one theme per video, is CLAUDE.md under "Demo videos".

## What is built

`build.py` writes `out/<project>.mp4`, and the finished file then lives with the
project it shows, because that is where the human goes looking for it. `out/` is a
build directory, not an archive. The index of every shipped video is
`work/VIDEOS.md`.

| Shipped file | Length | Size | Project |
| --- | --- | --- | --- |
| `work/calle-approval-gate/DEMO-phone-approval-gate.mp4` | 2:06 | 12.5 MB | CALL-E PR #41 |
| `work/calle-scheduler/DEMO-multi-party-scheduler.mp4` | 1:58 | 11.7 MB | CALL-E PR #42 |
| `work/calle-onbehalf/DEMO-call-on-behalf.mp4` | 2:14 | 13.0 MB | CALL-E PR #43 |
| `work/moonwalk/DEMO-moonwalk.mp4` | 2:18 | 14.5 MB | MoonWalk, Encode x Circle |
| `work/ignyte-stablecoin/DEMO-sanad.mp4` | 2:46 | 20.1 MB | Sanad, Ignyte Track 4 |

All five are 1920x1080, 30 fps, H.264 yuv420p with faststart, AAC 192k at 48 kHz.
Loudness measured at -16.0 to -16.2 LUFS integrated with true peak between -1.5 and
-4.4 dBTP on every one. All are under the three minute rule with room to spare.

After a rebuild, copy the new file over the shipped one:
`cp out/<project>.mp4 ../<lane>/DEMO-<project>.mp4`. Each project's brief carries that
line in its rebuild section.

The first three are the CALL-E hackathon set and the rest of this file is mostly about
them. MoonWalk (Encode x Circle) is driven by `projects/moonwalk.json` on the `sky`
theme with its own brief at `work/moonwalk/CODEX-VIDEO-BRIEF.md`, and Sanad (Ignyte
Track 4) by `projects/sanad.json` on `honey` with
`work/ignyte-stablecoin/CODEX-VIDEO-BRIEF.md`: this kit is the house standard, so a new
lane adds a project file here rather than forking it. Per-project build scratch, the
captured stdout, the segment clips and the silent picture, stays in
`artifacts/<project>/`.

## How they were made

Audio first, picture second. Every narration cue is synthesised with edge-tts and
measured before a frame is rendered, so each segment is exactly as long as the
words it carries. Nothing drifts and nothing gets clipped.

Each video has its own spine. The three apps do different things, so they are shown
in different ways rather than poured into one terminal template:

| Project | Scenes it uses | The artifact each one reads |
| --- | --- | --- |
| phone-approval-gate | card, code, terminal, pipeline panel x2 | the real workflow YAML, a real `gate.sh` run in both modes, the real audit chain |
| multi-party-scheduler | card, availability grid x2, terminal x3 | two real coordination ledgers, the real demo output |
| call-on-behalf | card, chips, report document, chat transcript, terminal x2 | the real errand file, the real `report.json`, its verbatim transcript |

The scene library is in `panel.py` (step lists and chip rows), `doc.py` (the call
report as a document, the transcript as bubbles), `grid.py` (the party by option
matrix), `code.py` (a source file with light syntax colour) and `scene.py` (the
terminal window). Every one of them reads a file on disk or the output of a command
that actually ran, and every one hands back the pixel box of each row so the zoom,
the marker and the cursor have something to aim at.

Terminal segments run the real command in the real app directory, capture stdout
and stderr, and render that captured text as a typewriter reveal. The raw captures
are kept in `artifacts/<project>/*.stdout` next to the command that produced them,
so any frame in any video can be traced back to the program that printed it. No
line on screen was typed by hand.

The pipeline panels in video one are not a mock CI screenshot. `pipelines/gate.sh`
runs `npm run check`, `npm test`, then the real CLI against `pipelines/fake-calle.mjs`,
then either the deploy stand-in or nothing, and prints one `STEP|label|code|duration`
line per step. The panel is drawn from those lines, so the green run and the red run
are two real runs with their real exit codes: 0 when the person reads the code back,
20 when they cannot, with `deploy` skipped. The full transcript of each run is kept
in `artifacts/<project>/*.pipeline`.

## The upload package

A rendered mp4 is not the deliverable. `upload.py` builds everything the upload form asks
for, so the human's job is paste and click:

```bash
python3 upload.py projects/<id>.json      # after a build, then again after any wording change
```

It writes `artifacts/<id>/upload/`, which the lane copies to `work/<lane>/upload-<id>/`.

**`UPLOAD-<id>.html` is the package**, one self-contained page with no external reference in
it. Sixteen copy buttons and two downloads for Twinrail's. In order: the title, the
description with the chapters already inlined, the tags, the chapters on their own, the
thumbnail embedded at full size and again at 168 pixels wide, the captions as a copy block
and a download, every in and out time the build measured, the rest of the form field by
field, the gates it checked, then where the URL goes. Each text block carries a live
character count against its limit.

The sidecar files exist only because YouTube wants real files to upload. The page offers
both as downloads anyway:

| File | What it is |
| --- | --- |
| `thumbnail.png` or `.jpg` | 3840x2160 on the project's own palette, drawn by `thumb.py`, never downloaded |
| `captions.srt` | one block per narration cue at the exact times the build measured |
| `chapters.txt` | the scene table as timestamps, already inlined in the description |

The words come from an `upload` block in the project file, so there is one place to edit them
and the brief cannot drift from the package. The timing comes from `artifacts/<id>/timing.json`,
which `build.py` writes as it renders, so a timestamp in the page is a timestamp in the
delivered file rather than something re-derived afterwards. The page shows it as two tables:
the scenes with in, out and duration against the chapter each opens with the climaxes shaded,
then every narration cue with its SRT in and out times.

It exits non-zero when a limit is broken. The limits are YouTube's own: title 100
characters, description 5000, thumbnail 3840x2160 recommended at 16:9 with a 2 MB cap on the
mobile upload path, plus chapters that start at `0:00`, number at least three and each run at
least 10 seconds. Tags have no published limit and YouTube says they play a minimal role, so the
500 character ceiling is a house convention against keyword stuffing.

A generated field is a gradient with grain, which PNG compresses badly: at 3840x2160 it lands
near 3 MB. So `thumb.write` tries PNG, then falls back to JPEG at descending quality until it
fits, rather than dropping the resolution YouTube recommends. Twinrail's landed at 639 KB.

Two gates a script cannot run, both required before upload: look at the thumbnail in the page,
at both sizes it renders there, then fetch every URL the description cites anonymously for a
200.

## The look

Bright, and everything on screen is generated rather than downloaded, so there is
no image licence to defend.

`bg.py` draws the field once per project and caches it: a bright ramp, three soft
colour blobs, a blur and a little grain. The recording window floats on that field:
near-white panel, window chrome, soft drop shadow, dark ink, and syntax colours
darkened so they still pass contrast on a light panel. Dense monospace stays on the
light panel, because the brightness belongs around the text and not behind it. The
panel is sized for the whole shot, so it does not grow as lines arrive.

### One theme per video, never reused

A set of videos that share a field reads as one template with the words swapped. So
every video claims a theme no other video from this workspace uses. `PALETTES` in
`theme.py` carries the roster: gradient ends, the accent (titles, prompt, cursor,
progress bar), the highlighter ink, three blobs, and a field shape, so two videos
differ in the shape of the light as well as its colour.

| Theme | Field | Holder |
| --- | --- | --- |
| citrus | vertical | phone-approval-gate |
| mint | vertical | multi-party-scheduler |
| lilac | vertical | call-on-behalf |
| coral | diagonal | free |
| sky | radial | free |
| moss | vertical | free |
| honey | diagonal | free |
| berry | radial | free |
| slate | vertical | free |

`preflight.py` prints who holds what and fails if two project files share a theme.
The cross-lane register is `work/VIDEO-THEMES.md`; claim a theme there before
building and record it after. When the free list runs out, add a palette rather than
doubling up: bright gradient ends, an accent dark enough to read on the near-white
panel, and a mark pale enough to multiply over dark ink without hiding it. Render one
check frame before committing to it.

## Motion that follows the narration

Every narration cue can name the line it is about:

```json
{ "text": "Not approved, code mismatch. The deploy step never runs.",
  "focus": "Attempt for release-owner: not_approved (code_mismatch)." }
```

From that one field the build derives three things, all timed to the cue:

- **Zoom.** The frame eases into a 16:9 box around that line and back out when the
  cue ends. The canvas is rendered at 2560x1440 and delivered at 1920x1080, so a
  zoom of up to 1.4x costs nothing in sharpness. The box is anchored to the left of
  the marked text, and it is nudged to keep the whole window in frame on any axis
  where the window fits, so a line near the bottom of a long page cannot slice the
  window in half.
- **The marker.** A highlighter sweep wipes across the line while it is spoken. The
  ink is multiplied into the page rather than pasted over it, so white paper takes
  the colour and red text stays red. That matters here, because the lines worth
  marking are usually the refusals.
- **The cursor.** A pointer travels to the line with easing, with a soft shadow and
  a click ripple when it lands.

Content lands at a steady cadence (0.45s per row by default, `cadence` in the
project file) rather than being stretched across the whole segment, and anything a
cue points at is revealed immediately however far down the page it is. Without that
rule the narration talks about a line that has not arrived yet, and the zoom, the
marker and the cursor all sit out the beat.

A progress bar is drawn on the delivered frame, after the crop, so a zoom can never
cut it off. Cards drift from a slight zoom back to full frame so a still card does
not feel like a freeze.

Rendering all of that is the slow part: about three and a half minutes per video on
this machine. Two cheap gates come first, and both are worth running before any
render:

```bash
python3 preflight.py projects/*.json          # every segment drawn once, every focus needle resolved
python3 frame.py projects/call-on-behalf.json 52 88   # single frames at real timestamps
```

`preflight.py` prepares every segment for real, writes one frame each to
`artifacts/<id>/preflight/`, and fails loudly on a focus needle that matches
nothing. `frame.py` uses the same layout the build uses, so a timestamp there is
the timestamp in the finished file, and it warms the painter for three seconds first
because the zoom, marker and cursor are stateful.

## Voices

Two engines, switched with one environment variable.

`edge` is the default. It is Microsoft edge-tts through the venv in the OKX lane,
it costs nothing, and it is what every shipped video uses (`en-US-AndrewNeural` at
+3%, `en-US-AvaNeural` at +2% for call-on-behalf, `en-GB-RyanNeural` at +2% for
moonwalk, one voice per video so a set never sounds like one narrator reading four
scripts).

`fish` calls the Fish Audio API for a better read:

```bash
VOICE_ENGINE=fish FISH_VOICE=<voice_id> MUSIC=~/Downloads/joyinsound-no-copyright-music-398375.mp3 \
  AUDIO_ONLY=1 python3 build.py projects/phone-approval-gate.json
```

The token is read from `FISH_TOKEN` or `~/.cache/calle-video/fish.token` (mode
0600, outside the repository, never committed and never printed). Cue files are
keyed by a digest of the engine, the voice, the rate and the words, so switching
engines or editing a line re-reads that line and nothing else, and switching back is
instant because both sets stay cached.

**Blocked on credit, not on code.** The session token authenticates fine and can
read the voice library, but `POST /v1/tts` returns 402: "Insufficient API credit.
API credit is managed independently from platform credit." The account shows
`api credit: 0.000000`. Add funds at https://fish.audio/app/developers, pick a
voice id from the library, and each audio rebuild takes about eight seconds because the
picture is reused.

Volume, if it helps size the top-up: 63 cues and 7,319 characters across the four
videos. `NARRATION-MANIFEST.md` lists every cue with the exact path to save it at, and
`manifest.py` regenerates it after any narration edit.

## The music bed

All four carry `joyinsound-no-copyright-music-398375.mp3` from `~/Downloads`, the
same track already used in the shipped cassandra video. It loops under the
narration at `volume=-21dB`, fades in over 1.5 seconds, fades out over the last 3,
and is sidechain ducked against the voice (`threshold=0.02:ratio=8:attack=40:release=600`)
so the music moves out of the way instead of the voice being pulled down. A
limiter sits before the final normalisation.

Measured on the finished files:

| Video | Integrated | True peak |
| --- | --- | --- |
| phone-approval-gate | -16.1 LUFS | -2.0 dBTP |
| multi-party-scheduler | -16.0 LUFS | -1.9 dBTP |
| call-on-behalf | -16.0 LUFS | -2.0 dBTP |
| moonwalk | -16.2 LUFS | -1.9 dBTP |

A sample-domain limiter at -1.5 dBFS still measured -1.4 dBTP, because true peak counts
inter-sample peaks a sample limiter cannot see. The final stage is now
`alimiter=limit=0.79:level=disabled` after the normalisation, which lands every file
between -1.9 and -2.0 dBTP. `level=disabled` matters: ffmpeg's limiter auto-levels the
output up to its own ceiling by default, which pushed one mix to -0.0 dBTP before it was
switched off.

Measured across all four: speech sits between -18.8 and -19.2 dB mean over a 20 second
window, and the music-only fade-out at the end between -30.0 and -32.6, so the bed is
eleven to fourteen decibels down and ducks further while anybody is talking. Nothing
clips.

**One licence check before upload.** The rules require the video to be free of
unlicensed music. That filename is the Pixabay pattern and the track has been used
in a shipped video from this workspace already, so keep the source page link with
the submission in case anybody asks. If you would rather not rely on it, one command
per video ships a music-free cut through the same -16 LUFS normalisation:

```bash
AUDIO_ONLY=1 python3 build.py projects/phone-approval-gate.json
```

Leaving `MUSIC` unset is what makes it silent. Setting it puts the bed back:

```bash
MUSIC=~/Downloads/joyinsound-no-copyright-music-398375.mp3 \
  AUDIO_ONLY=1 python3 build.py projects/phone-approval-gate.json
```

`AUDIO_ONLY=1` reuses the rendered picture and only rebuilds the sound, so either
version takes seconds rather than minutes.

## What the videos say about themselves

Every video opens with `Every line in this video is real output from the
repository` and every call scene carries `local fake CALL-E, no real call placed`
for its whole duration. That is the honest position while there is no CALL-E
account: the apps are real and the output is real, and no phone rang.

When the account lands, a live call can be added without rebuilding anything else.
Add one segment to the project file with the live command and its own narration
cue, drop the fake-CALL-E footer on that segment, and re-run the build.

## Rebuilding or editing

```bash
cd work/calle-video
python3 build.py projects/phone-approval-gate.json
python3 build.py projects/multi-party-scheduler.json
python3 build.py projects/call-on-behalf.json
```

Starting a fourth video:

```bash
python3 scaffold.py <project-id> <app-dir> "The headline."
```

That claims the next free theme, writes a project file that already passes preflight
and renders, and prints the scene types to choose from. Replace its middle with scenes
drawn from what that project actually produces, then record the theme in
`work/VIDEO-THEMES.md`.

Narration, captions, slices and pacing all live in `projects/*.json`. Synthesised
cues are cached under a digest of the engine, the voice, the rate and the words, so
a wording change re-reads only that line and an unchanged line is never paid for
twice. The build refuses to finish if the total runs over 176 seconds, and it
refuses a segment whose slice markers find nothing, so a stale marker fails loudly
instead of shipping an empty frame.

Files: `theme.py` holds the theme roster, fonts and the syntax colour rule, `bg.py`
generates the field, `scene.py` draws the terminal window, `panel.py` draws step
lists and chip rows, `doc.py` draws the report and the transcript, `grid.py` draws
the availability matrix, `code.py` draws a source file, `cards.py` draws cards,
`motion.py` does the zoom, marker, cursor and progress bar, `term.py` runs a real
command and slices its output, `pipelines/` holds the local CI run and its fake
CALL-E, `voice.py` does TTS and the narration mix, `build.py` lays out the timing
and assembles, `scaffold.py` starts a new project on a free theme, `preflight.py`
and `frame.py` are the pre-render gates, `manifest.py` regenerates the narration
manifest.

Every scene renderer returns an object with an `image`, a `window` box and a
`boxes` list, so one painter drives all of them. Adding a scene type means writing
that renderer and one branch in `prepare()`.

## Verification already done

- `preflight.py` on all four projects: every segment prepared and drawn, every focus
  needle resolved to a real row, no two projects on the same theme. Zero failures.
- `frame.py` at the climax timestamps of all four, then the same timestamps pulled out
  of the finished mp4s with ffprobe and checked by eye: content revealed, zoom landed,
  marker on the right line, cursor arrived.
- `ffprobe` on all four: duration, one H.264 stream at 1920x1080 30fps, one AAC stream
  at 48 kHz stereo, sizes above.
- Loudness pass on all four: -16.0 to -16.2 LUFS integrated, true peak -1.9 to -2.0
  dBTP.
- Em dash gate on every narration string, caption and doc in the kit: clean.
- Locked lines confirmed present in the captured artifacts for each project:
  `not_approved (code_mismatch)` and `STEP|phone approval gate|20|` with
  `STEP|deploy|skipped|-`, `released plumber.`, `privacy check nothing outside your
  list was said`, `calls placed: 0`, and for moonwalk `guarded     True`,
  `CapExceeded, refused on chain` and `eth_call ok, this transaction would succeed`.
- Both CALL-E pipeline runs kept as receipts in
  `artifacts/phone-approval-gate/pipeline-{approve,mismatch}.pipeline`, exit 0 and
  exit 20 with the verdict line. MoonWalk's panel is rendered from
  `work/moonwalk/evidence/channel-20260729T154745Z.json`, the receipt its own demo
  wrote on Arc.

## What you do

1. Watch each one once with headphones. They are around two minutes each.
2. Upload public to YouTube, not unlisted. Title and description for each are in the
   matching brief, ready to paste:
   - `work/calle-approval-gate/CODEX-VIDEO-BRIEF.md` section 9
   - `work/calle-scheduler/CODEX-VIDEO-BRIEF.md` section 9
   - `work/calle-onbehalf/CODEX-VIDEO-BRIEF.md` section 9
   - `work/moonwalk/CODEX-VIDEO-BRIEF.md` section 9
   Each description already carries the honesty note for that video, the AI assistance
   line and the synthesised narration note.
3. For the three CALL-E videos, paste each URL into its Devpost submission and as a
   comment on its PR. The comment text is in each `DEVPOST-SUBMISSION.html`. For
   MoonWalk, the URL goes into the Encode Checkpoint 3 form (due 9 Aug) and into
   `work/moonwalk/FORM-FILL.html` if you want it kept with the other paste blocks.
