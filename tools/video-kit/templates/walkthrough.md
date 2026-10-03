# walkthrough

A longer explanatory cut that reads code beside what it does. Use it for a teaching video
or a deep dive where the point is understanding, not a demo.

## The spine

1. `card` title. What the viewer will understand by the end.
2. `code` part one, then `term` part one run.
3. `code` part two, then `term` part two run.
4. `card` close.

Each code scene is paired with the run that proves it, in sequence.

## Pending scene: compose

The brief's target scene for this genre is `compose`, code beside its output in one frame.
It is not registered yet. Until `compose.py` lands, this template alternates a `code`
scene with the `term` scene that runs it. In sequence it reads the same way: read the
code, then watch it run.

When `compose.py` is registered (check with `python3 -c "import style;
style.load_scene_modules(); print(style.known())"`), fold each code and term pair into one
`compose` block so both are on screen together. Read `compose.py`'s own
`@style.scene("compose")` prepare function for the keys it accepts before writing one. This
file will not describe an interface that is not written yet, so do not guess.

## Why the paired shape works

A walkthrough lives or dies on the code and its result being tied together. Alternating
them keeps that tie even without a split frame: the term scene right after a code scene is
understood as the output of what was just read. It just costs a cut between them that
`compose` would remove.

## Pacing

Longer than the others, so watch the cap. The default cap is 176 seconds. If it runs long,
cut a pair rather than rushing the read. A slower rate (`"rate": "+2%"`) suits an
explainer.

## What to swap

- `palette`: a free one.
- Every `code` scene, pointed at your real source.
- Every `term` scene, pointed at the command that runs it.
- Every `TODO`.
