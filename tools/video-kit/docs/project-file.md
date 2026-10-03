# The project file

A video is one JSON file in `projects/`. It carries the identity, the theme, the voice,
the scenes in order and the words spoken over them, plus an `upload` block for the package.
This is the complete reference for every key it accepts, derived from the code.

A project with no `style` and no `render` block resolves to the exact numbers the kit
shipped with, so the settings below are all optional except `id` and `segments`. Anything
the kit does not read it ignores, so a `"note"` key is a safe place for a comment (JSON
carries none).

## Top level

| key | type | default | what it does |
| --- | --- | --- | --- |
| `id` | string | required | the project id. Names `projects/<id>.json`, `artifacts/<id>/` and `out/<id>.mp4`. |
| `segments` | list | required | the scenes, in order. Each is an object with a `type`. See [Segments](#segments). |
| `header` | string | `""` | the window chrome caption, shown on terminal, web, code and diff scenes. A segment can override it with its own `header`. |
| `palette` | string | `"citrus"` | the theme name from `theme.PALETTES`. One theme per video: `preflight.py` fails two projects on the same one. |
| `voice` | string | `"en-US-AndrewNeural"` | the narration voice, passed to the TTS engine. One voice per video. |
| `rate` | string | `"+3%"` | the speech rate, an edge-tts style percentage. |
| `captions` | bool | `true` | burned-in narration captions. `false` turns them off (sets the caption style to `none`). |
| `cap` | number | `176` | the hard length ceiling in seconds. `build.py` refuses a cut that runs longer. |
| `cadence` | number | `0.45` | seconds per row reveal, the default for every scene. A segment can override it. |
| `timing` | object | see below | fine timing knobs. Rarely set. |
| `transitions` | object | `{"default": "cut", "seconds": 0.5}` | scene-to-scene transition settings. Read into the Style. |
| `audio` | object | `{}` | audio settings, read into the Style. |
| `style` | object | `{}` | look and geometry. See [The style block](#the-style-block). |
| `render` | object | `{}` | output size, quality and encoder. See [The render block](#the-render-block). |
| `upload` | object | none | the upload package words. `upload.py` refuses a project without it. See [The upload block](#the-upload-block). |

`timing` sub-keys, all seconds, all rarely touched: `gap` (0.35, silence after a cue),
`lead` (0.3, silence before the first cue in a segment), `hold` (1.6, extra time a scene
holds after its last reveal), `pad` (0.9), `transition` (0.62, the zoom ease), plus
`cursor_move`, `cadence` and `cap` that the top-level keys already expose.

## Segments

Every segment is an object with a `type`. These keys are shared across scene types:

| key | type | default | what it does |
| --- | --- | --- | --- |
| `type` | string | required | the scene type. See the table below. |
| `name` | string | the type | a label, used in the build report, in chapter mapping and as the artifact filename for scenes that capture. |
| `narration` | list | `[]` | the cues spoken over the scene. A cue is a string, or `{"text": ..., "focus": ...}`. See [Narration and focus](#narration-and-focus). |
| `footer` | string | none | a line along the bottom of the window, usually the honesty label. |
| `pad` | number | 0.9 | seconds of quiet added to the segment length past the narration. |
| `hold` | number | 1.6 | seconds the scene holds after the last row is revealed, before the zoom eases out. |
| `cadence` | number | 0.45 | seconds per row reveal for this segment. |
| `min_seconds` | number | 2.5 | a floor on the segment length, so a short card does not flash by. |

Segment length is measured from the audio: the cues are synthesised, their real durations
are summed, then `pad` and `min_seconds` set the floor. Nothing is guessed.

### Scene types

Registered scene types are looked up at build time. Confirm what is live with
`python3 -c "import style; style.load_scene_modules(); print(style.known())"`.

| type | reads | rows are | status |
| --- | --- | --- | --- |
| `card` | inline `lines` | the card text | built in |
| `term` | a real command's stdout | output lines | built in |
| `web` | a real page section | revealed items | built in |
| `code` | a real source file | code lines | built in |
| `diff` | a git range, file pair or patch | diff lines | registered |
| `chart` | a JSON/CSV file or inline rows | bars, points or meters | registered |
| `diagram` | inline nodes and edges | nodes then edges | registered |
| `steps` | a pipeline script's `STEP|` lines | pipeline steps | built in |
| `receipts` | an evidence JSON file | lifecycle rows | built in |
| `grid` | a coordination ledger | party rows | built in |
| `chips` | an errand file's disclosure | chip pairs | built in |
| `report` | a report JSON | answer rows | built in |
| `bubbles` | a transcript JSON | chat turns | built in |
| `compose` | code beside output | pending, not registered yet | pending |
| `device` | a screenshot in a phone frame | pending, not registered yet | pending |
| `overlay` | pending | pending, not registered yet | pending |

`compose`, `device` and `overlay` are named in the roster but may not be registered. A
project that names an unregistered type fails loudly at build with `unknown segment type`.
Check the live list before using one, and read that module's own `@style.scene(...)`
prepare function for its exact keys. This reference will not describe keys for a module
that is not written.

Full per-type keys are in [docs/scenes.md](scenes.md). The short version:

- `card`: `lines` (list, required), `kicker`, `footer`, `mono` (bool, big monospace). A
  card has no rows, so a `focus` on its narration is ignored.
- `term`: `cwd`, `cmd` (list, required), `prompt`, `from`, `to`, `max_lines` (26), `wrap`
  (104), `header`.
- `web`: `url` or `file`, `section` (required), `items` (`data-step`), `viewport`
  (`[1180, 600]`), `wait_ms` (400), `header`.
- `code`: `file` (required), `title` (required), `from`, `to`, `max_lines` (22).
- `diff`: one of (`repo` + `rev`), (`before` + `after`) or `patch`; `file`, `title`,
  `mode` (`unified` or `split`), `hunk`, `max_lines` (26).
- `chart`: `chart` (`bar`, `column`, `line`, `progress`, `sparkline`); `rows` or `series`
  or `file` (+ `path`, `label_key`, `value_key`, or `x`/`y` for CSV); `title`, `unit`,
  `source`, `thresholds`, `x_labels`, `max`.
- `diagram`: `nodes` (required), `edges`, `layout` (`flow`), `title`, `footer`.
- `steps`: `script` (required), `app` (required), `mode` (`approve`), `title`.
- `receipts`: `file` (required), `title`.
- `grid`: `ledger` (required).
- `chips`: `errand` (required), `title`.
- `report`: `report` (required).
- `bubbles`: `report` (required), `max_turns` (6), `title`.

## Narration and focus

`narration` is a list. Each entry is either a plain string, or an object:

```json
{ "text": "The removed line is the bug, the added line is the fix.",
  "focus": "elapsed" }
```

`focus` is a substring. The build resolves it against the rows of the scene, and from the
match it derives the zoom box, the highlighter sweep and the cursor target, all timed to
the cue. `focus` can be a list of substrings to mark more than one row. What a needle
matches per scene is in [docs/scenes.md](scenes.md). A needle that matches nothing fails in
`preflight.py`, which is the point: a stale marker fails before a ten minute render, not
during it.

A cue with no `focus` still plays, it just carries no zoom or marker for that beat.

## The style block

`style` sets the look and the geometry. Every key is optional.

| key | type | default | what it does |
| --- | --- | --- | --- |
| `aspect` | string | `"16:9"` | delivered frame. `16:9` (1920x1080), `9:16` (1080x1920), `1:1` (1080x1080), `4:5` (1080x1350). |
| `quality` | string | `"standard"` | the quality preset. Also settable in `render`. See [The render block](#the-render-block). |
| `mode` | string | `"light"` | `light` or `dark`. `dark` swaps the whole ink table for the dark set. |
| `fonts` | object | system stack | `{"stack": "system"|"inter", "scale": 1.0, "sans": ..., "sans_bold": ..., "mono": ..., "mono_bold": ...}`. A vendored stack that was never fetched falls back to system with a printed warning. |
| `type` | object | `{}` | per-name type size overrides, e.g. `{"code": 32}`. Names are in `style.TYPE`. |
| `metrics` | object | `{}` | spacing overrides: `line_height`, `window_margin`, `pad_x`, `pad_top`, `radius`. |
| `ink` | object | `{}` | colour overrides by name, hex or `[r,g,b]`. Names are in `style.LIGHT_INK`: `panel`, `ink`, `green`, `red` and the rest. |
| `caption` | object | band style | `{"style": "band"|"none", "position": "bottom", "font_size": 34, "band": 62, "width_ratio": 0.906}`. |
| `progress` | object | `{"style": "bar", "height": 8}` | the progress bar. |
| `cursor` | object | `{"style": "arrow", "size": 210}` | the cursor. |
| `marker` | object | `{"style": "highlight", "opacity": 0.15, "sweep": 1.6}` | the highlighter sweep. |
| `window` | object | mac chrome | `{"chrome": "mac", "shadow_blur": 34, "shadow_alpha": 92, "radius": 30}`. |
| `brand` | object | `{}` | free-form brand settings read into the Style. |
| `colour_rules` | list or object | the default table | per-project terminal colour rules. See below. |

The `caption`, `progress`, `cursor`, `marker`, `window` and `brand` blocks are free-form
sub-dicts merged over the defaults. Their exact styles are read by `motion.py`, which
another hand is extending, so use the defaults unless you have read what a given style key
does in that module. Setting one the renderer does not know is harmless, it just does
nothing.

`colour_rules` colours words in terminal output. As a list it replaces the default table:
`[["approved", "green"], ["FAIL", "red"]]`. As an object it extends it:
`{"rules": [["myword", "amber"]]}`, or `{"replace": true, "rules": [...]}` to start fresh.
Project rules are checked before the defaults, so a project can override an inherited
verdict. Colour names are `green`, `red`, `amber`, `blue`, `violet`, `ink`, `ink_soft`.
Order matters: refusals are listed before approvals because `approved` is inside
`not_approved`.

## The render block

`render` sets the output size and the encoder. Every key is optional.

| key | type | default | what it does |
| --- | --- | --- | --- |
| `quality` | string | `"standard"` | `draft`, `standard`, `high`, `max`. Sets canvas scale, x264 preset, CRF and fps. `standard` reproduces the shipped look. |
| `output` | `[w, h]` | from aspect | override the delivered pixel size. |
| `canvas_scale` | number | from quality | the canvas is the output times this. Above 1 buys a zoom that costs no sharpness. `standard` is 4/3. |
| `fps` | int | from quality | frames per second. |
| `preset` | string | from quality | x264 preset. |
| `crf` | int | from quality | x264 constant rate factor. |
| `bitrate` | string | none | a target bitrate, e.g. `"8M"`, when a program sets a file-size floor. Also settable as the `VIDEO_BITRATE` env var. |
| `colour` | string | `"bt709"` | colour primaries. |
| `tune` | string | none | x264 tune. |
| `workers` | int | 0 | parallel render workers. |

The quality presets:

| quality | canvas_scale | preset | crf | fps |
| --- | --- | --- | --- | --- |
| `draft` | 1.0 | ultrafast | 28 | 30 |
| `standard` | 4/3 | veryfast | 19 | 30 |
| `high` | 1.5 | slow | 17 | 30 |
| `max` | 2.0 | slower | 15 | 60 |

Any key in `render` that is not one of the geometry keys flows through to the encoder
untouched, so a new x264 knob is a key here rather than a code change.

## The upload block

`upload.py` reads this to build the click-to-copy package. It refuses a project without
it. Keys:

| key | type | what it does |
| --- | --- | --- |
| `title` | string | the video title. Gate: under 100 characters. |
| `description` | string | the full description. Gate: under 5000 characters. `{chapters}` is replaced with the chapter timestamps. |
| `tags` | list | the tags. Gate: under 500 characters joined. |
| `category` | string | the YouTube category, e.g. `"Science & Technology"`. |
| `language` | string | the video and caption language. |
| `chapters` | list | `{"at": 0, "title": ...}` for the first, then `{"segment": "<name>", "title": ...}` for the rest. Times are read from the measured `timing.json`. Gate: first at 0:00, at least three, each at least 10 seconds. |
| `climaxes` | list | segment names to shade in the timing table, the beats that must not lose time. |
| `thumbnail` | object | `{"layout": ..., "badge": ..., "name": ..., "claim": [...], "figure": [...]}`. One layout per demo: `preflight.py` fails a reused non-`stack` layout. |
| `then` | list | reminder lines for after the URL exists, e.g. where to paste it. |

The description order the house rule wants: what the product does, what each integration
contributes, the live links, one line on what was newly built, the chapters, the honesty
paragraph, the measured numbers, the licence, the AI disclosure with the synthesised
narration line. Anything asserted there must already be true in the brief.

## A minimal file

```json
{
  "id": "my-demo",
  "palette": "sky",
  "segments": [
    { "type": "card", "lines": ["My project."],
      "narration": ["One line on what it does."] },
    { "type": "term", "name": "run", "cwd": "/path/to/app",
      "cmd": ["python3", "demo.py"], "prompt": "python3 demo.py",
      "narration": [{ "text": "It runs.", "focus": "done" }] }
  ]
}
```

That builds. It will not pass `upload.py` until it carries an `upload` block, and it
should carry a live `web` scene and a `code` or `term` scene before it ships, which is the
house rule the genre templates already satisfy.
