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
{ scene: "phrase", params: {...}, seconds: 18.4, fps: 30,
  cues: [{ start: 0.3, end: 4.1, text: "..." }, ...] }   // segment-local seconds
```

The page must expose:

- `window.stageReady`: a Promise that resolves when fonts, images, iframes and video
  metadata are loaded and the scene is built.
- `window.stageSeek(t)`: render the scene at local time `t` seconds. It may return a
  Promise (for example while a `<video>` seeks). **It must be a pure function of `t`**:
  the engine may seek any frame in any order (frames are captured in parallel chunks).

## Engine API (`stage.js`)

```js
import { Stage, ease } from "/__repo/tools/video-kit/stage/stage.js";

Stage.scene("phrase", (S) => {
  // S.root      the 1920x1080 scene element (inside the camera layer)
  // S.overlay   a layer above the camera (cursor, labels that must not zoom)
  // S.seconds, S.fps, S.params, S.cues ([{start, end, text}])
  // S.cue(i)    start of cue i; S.cueEnd(i) its end; negative i counts from the end
  // S.el(tag, {class, text, html, attrs}, parent) -> element (parent defaults to S.root)

  S.tween(el, { at: S.cue(1), dur: 0.6, ease: "outCubic",
                from: { opacity: 0, y: 24, scale: 0.96, blur: 8 },
                to:   { opacity: 1, y: 0,  scale: 1,    blur: 0 } });
  // props: opacity, x, y, scale, scaleX, scaleY, rotate (deg), blur (px), and any CSS
  // custom property written as "--name" (number). Several tweens on one element compose
  // per property: the latest tween that has started wins for that property.

  S.on((t) => { /* custom per-frame drawing, pure in t: canvas, text scramble, counters */ });

  S.camera([ { at: 0, x: 960, y: 540, zoom: 1 },
             { at: S.cue(2), dur: 0.9, x: 1400, y: 380, zoom: 1.8, ease: "inOutCubic" } ]);
  // the camera centres (x, y) in scene px and zooms; Screen Studio style eased moves

  S.cursor([ { at: S.cue(2) + 0.2, x: 1180, y: 610 },
             { at: S.cue(2) + 1.0, x: 1290, y: 640, click: true } ]);
  // eased path between points, a click ripple where click is true; hidden before the
  // first point and after `hide` if given

  S.type(inputEl, "u1ay3aaw...", { at: S.cue(3), cps: 28 });   // pure: chars = f(t)
  S.site(iframeEl, { at, ... })   // helpers to seek CSS/WAAPI animations inside a same-origin iframe
  S.video(videoEl, { at, from, to })  // play a footage clip: currentTime = from + (t - at)
});
```

`ease`: linear, inCubic, outCubic, inOutCubic, outBack, outExpo, inOutExpo, outElastic,
spring (critically damped).

## Layout rules for every scene

- Keep the bottom 150 px clear: the kit burns captions and the progress bar there.
- Safe area x 96 to 1824, y 64 to 900.
- Every diagram or illustration carries a visible `Diagram` label for the whole scene.
  Never draw an app screen. Wallet steps are step diagrams: the exact button label from
  docs/FACTS.md in a gold chip, with "In Zodl, tap ..." wording.
