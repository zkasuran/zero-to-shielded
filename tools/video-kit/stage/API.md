# Stage: animated HTML scenes for the video kit

A `stage` segment is a scene drawn by a real web page and captured frame by frame in
headless Chromium, so motion design (characters, diagrams, camera moves, cursor, typing,
a recording of the real companion site) is written in HTML, CSS and SVG and still timed
to the narration by the kit. The kit keeps doing what it does: synthesise the cues, size
the segment, burn captions, draw the progress bar, mix music, assemble, write timing.json.

## Project file

```json
{"type": "stage", "name": "e1-phrase", "html": "episodes/stage/e1.html", "scene": "phrase",
 "params": {"any": "json"}, "narration": ["cue 0 text", "cue 1 text"]}
```

- `html`: path relative to the repo root. `scene`: the id the page registers. `params`:
  free JSON handed to the scene. `name`: unique per project. No `focus` on stage cues
  (the scene does its own camera, marker and cursor).
- Frames are cached under `artifacts/<id>/stage-<name>-<hash>/`, keyed on the page, every
  file it imports, the scene, params, cue timings, fps and canvas size.

## Serving

The engine runs one local HTTP server per capture:

- `/__repo/<path>` serves `<repo>/<path>` (stage pages, the engine, series library, footage)
- `/<path>` serves `<repo>/site/<path>` (the real companion site, its fonts and `js/cast.js`)

So a stage page and the real site share one origin: an `<iframe src="/tools/address/?capture=1&theme=dark">`
can be scripted from the stage page. Stage pages import the engine from
`/__repo/tools/video-kit/stage/stage.js` and the series library from
`/__repo/episodes/stage/lib/*.js`.

## Page contract

Viewport 1920x1080 CSS px, device scale factor = canvas width / 1920 (standard 4/3, high 1.5,
max 2). The engine injects `window.STAGE_INPUT` before load:

```js
{ scene: "phrase", params: {...}, seconds: 18.4, fps: 30, offset: 42.7,
  cues: [{ start: 0.3, end: 4.1, text: "...",
           words: [[0.34, 0.61, "In"], [0.61, 1.02, "Zodl,"], ...] }, ...] }   // segment-local seconds
```

`text` is the written line (never a lexicon respelling), `end` is when its voice stops,
`words` are the engine's word times (`[]` when it reports none; Kokoro and edge do).
`offset` is where the segment starts in the video. It is only injected into the top frame.
Frames are captured with `page.screenshot` at the viewport, after `stageSeek(t)` settles.

Quick look while writing a scene (DPR 1, one contact sheet, at most 1600 px a side):
`python3 tools/video-kit/stage_preview.py episodes/stage/e1.html phrase --seconds 12 --times 1,4,8 --cues "0.3-3.9|line;4.2-8|line" --out look.png`,
or `--project projects/zts-e1.json --segment e1-phrase` for the real cue timings.

The page must expose:

- `window.stageReady`: a Promise that resolves when fonts, images, iframes and video
  metadata are loaded and the scene is built.
- `window.stageSeek(t)`: render the scene at local time `t` seconds. It may return a
  Promise (for example while a `<video>` seeks). **It must be a pure function of `t`**:
  the engine may seek any frame in any order (frames are captured in parallel chunks).

## Engine API (`stage.js`)

Generic, no series styling (the default caption look is the only exception). The page
imports the engine and registers scenes; the engine boots itself after DOMContentLoaded.

```js
import { Stage, ease, track, rng, hash } from "/__repo/tools/video-kit/stage/stage.js";

Stage.scene("phrase", async (S) => { ... }, { narration: ["preview cue 1"], seconds: 9, params: {} });
Stage.wait(promise)          // boot waits for it before building (a stylesheet, say)
```

Without `STAGE_INPUT` the page previews itself: `?scene=&seconds=&cues=N` (N evenly
spaced cues; their text comes from `meta.narration` when given), `&t=2.5` shows one
frame, `&play=1` loops in real time (preview only), `&offset=`, `&params={json}`.

The scene object `S` (build may be async; everything below is pure in `t`):

| member | what |
|---|---|
| `S.root` | the 1920x1080 scene layer, inside the camera |
| `S.overlay` | above the camera, not zoomed (cursor, honesty labels) |
| `S.top` | above everything (captions) |
| `S.seconds, S.fps, S.params, S.offset` | from STAGE_INPUT. `offset` = segment start on the episode clock, so `S.offset + t` drives continuous backgrounds |
| `S.cues` | `[{start, end, text, words}]`, words as sent by the kit (`[[s, e, text]]` or `{start, end, text}`) |
| `S.cue(i)`, `S.cueEnd(i)` | start and end of cue i, negative i counts from the end, out of range clamps |
| `S.word(i, "Swap", nth)`, `S.wordSpan(i, phrase)` | when a word or phrase is said inside cue i: real word times when present, else the caption estimate |
| `S.el(tag, {class, text, html, attrs, style, tf}, parent)` | create an element (parent defaults to `S.root`; `tf` = base transform kept under tweens) |
| `S.rectOf(el)` | scene-px rect `{x, y, w, h, cx, cy}`, measured at build time |
| `S.tween(el, {at, dur, ease, from, to, stagger})` | props `opacity x y scale scaleX scaleY rotate blur` and numeric `--custom` props. Per property the latest started tween wins; a missing `from` starts from the value at `at` |
| `S.enter(el, {at, dur, ease, from})`, `S.exit(el, {at, dur, to})`, `S.set(el, values, at)` | shorthands |
| `S.valueOf(el, prop, t)` | a tweened value at any t |
| `S.on(fn(t, S))` | per-frame hook, may return a Promise |
| `S.defer(promise)` | stageReady waits for it (async loads inside components) |
| `S.camera([{at, x, y, zoom, dur, ease} \| {at, el \| fit: rect, pad, maxZoom}])` | eased centre plus zoom of the camera layer. The first key is the start state, every later key a move from wherever the camera is at its `at` (zoom eases in log space) |
| `S.camAt(t)`, `S.project(x, y, t, depth)` | camera state; scene point to screen point |
| `S.layer(depth, {above, bleed})` | a layer that follows the camera by `depth` (0 fixed, 1 camera; 0.1 to 0.4 for parallax) |
| `S.track(keys, base)` | the same keyed easing as the camera for any values |
| `S.cursor([{at, x, y \| el, click, dur, ease, arc}], {hide, size, trail})` | macOS style cursor in the overlay, soft shadow, curved eased path, press plus ripple on click, a motion trail only when fast. Scene px, projected through the camera |
| `S.type(el, text, {at, cps, seed, caret, events, until})` | typing with a seeded human cadence; inputs get `.value` (plus `input` events if `events`), other elements text and a t-driven caret |
| `S.scramble(el, {text, at, until, seed, rate, mode, order, spans})` | seeded glyph scramble. `mode`: `decrypt` (glyphs, then letters lock in), `encrypt`, `noise` (never resolves) |
| `S.video(el, {at, from, to})` | `currentTime = from + (t - at)`, clamped, awaits `seeked` |
| `S.site(iframe)` | same-origin page helper, see below |
| `S.captions({maxChars, size, y, color, highlight, fade})` | narration captions inside the frame (the kit's own are off): bottom centred, 44 px Inter 600 cream on a dark blurred pill, current word gold (word times when present, else proportional by characters), cues longer than about 52 characters split on sentence and comma breaks, nothing between cues |

`S.site(iframe)` returns `{win, doc, ready, scroll(keys), scrollAt(t), reveal(keys, scope),
rect(sel, {at}), point(sel, {at, ax, ay}), box()}`. `scroll([{at, y} | {at, dur, to:
"#checklist", offset, ease}])` scrolls the page as a function of t. `reveal([{at, k}],
"#checklist")` calls the site's `window.setReveal(k, scope)` as a step function of t.
`rect` maps an element inside the page to scene px at the scroll position of time `at`,
so the camera and the cursor can aim at real elements. CSS and WAAPI animations inside the
page are paused and seeked to t; transitions are switched off (a constructed stylesheet,
because the site's CSP refuses injected `<style>`).

`window.stageSeek(t)` clamps t to [0, seconds], applies tweens, camera and hooks, awaits
their promises and fonts, then resolves after two requestAnimationFrames. Seeks are
serialised. CSS transitions are off on the stage page; CSS and WAAPI animations are
paused and seeked to t (they play as if started at t = 0).

`ease`: linear, inQuad, outQuad, inCubic, outCubic, inOutCubic, outQuart, inOutQuart,
outQuint, inOutQuint, inOutSine, outBack, outExpo, inOutExpo, outElastic, spring
(critically damped, lands on 1). Any function `p => value` works too.

The series library (`episodes/stage/lib/series.js`) builds the Zero to Shielded look on
top of this; `episodes/stage/demo.html` is the reference page.

## Layout rules for every scene

- Keep the bottom 150 px clear: the kit burns captions and the progress bar there.
- Safe area x 96 to 1824, y 64 to 900.
- Every diagram or illustration carries a visible `Diagram` label for the whole scene.
  Never draw an app screen. Wallet steps are step diagrams: the exact button label from
  docs/FACTS.md in a gold chip, with "In Zodl, tap ..." wording.
