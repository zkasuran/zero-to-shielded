# short

A 9:16 vertical cut under 60 seconds, for Shorts and TikTok. This is a different edit, not
a crop of the long one.

## The spine

1. `card` hook. The surprising thing, said first, big.
2. `web` it works. One glimpse of the real product, phone-width.
3. `chart` the number. One payoff figure.
4. `card` call to action.

Four beats, one cue each. The cut is `"style": {"aspect": "9:16"}` and `"cap": 58`, so
`build.py` refuses it if it runs past 58 seconds.

## Why a short is its own edit

A long cut explains. A short hooks. If you crop a two minute cut to vertical you keep the
pace of an explainer, which is death on a feed. So the structure is inverted: the payoff
comes first, the cues are short, the cadence is faster (`"cadence": 0.3`), and there is no
room for a problem card. Say the surprising thing in the first four seconds or lose the
viewer.

## Pacing

Every segment carries a small `pad` and a short `hold`, and the two cards carry
`min_seconds` so they do not undershoot. Keep each narration cue to one sentence. If the
build refuses on the cap, cut a beat rather than speeding the voice past comfort.

## What to swap

- `palette`: a free one.
- The `web` scene `file` becomes `url`, phone-width.
- The `chart` rows, pointed at a real number.
- Every `TODO`.
