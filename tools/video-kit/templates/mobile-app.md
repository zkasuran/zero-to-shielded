# mobile-app

A phone app, shown vertical. Use it when the product runs on a phone and a landscape cut
would waste most of the frame.

## The spine

1. `card` title.
2. `web` screens. A phone-width capture of the live app, revealed screen by screen.
3. `code` source. One slice of the app logic.
4. `card` close. Where to get it.

The whole cut is `"style": {"aspect": "9:16"}`, so it is vertical from the first frame.

## Pending scene: device

The brief's target scene for this genre is `device`, a phone frame drawn around a real
screenshot. It is not registered yet. Until `device.py` lands, this template ships on a
`web` scene with a phone-width viewport (`"viewport": [390, 844]`), which captures the real
app at a phone size and preflights today. That is honest: it is the real UI, just without
the drawn bezel.

When `device.py` is registered (`python3 -c "import style; style.load_scene_modules();
print(style.known())"` will list `device`), swap the `web` block for a `device` block.
Read `device.py`'s own `@style.scene("device")` prepare function for the exact keys it
accepts before you write one, because this file cannot describe an interface that is not
written yet. Do not guess the keys. The rest of the template does not change.

## Why the web scene works here anyway

The house rule wants a live URL scene, and a phone-width `web` capture is one. It proves
the app is deployed and reachable at a size a phone user sees. The drawn frame is polish,
not proof.

## What to swap

- `palette`: a free one.
- The `web` scene `file` becomes `url`, pointed at your deployed app. Keep the phone-width
  `viewport`.
- The `code` scene, pointed at real source.
- Every `TODO`.
