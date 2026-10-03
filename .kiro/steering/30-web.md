# The companion web experience (`site/`)

A static site deployed to GitHub Pages. It is the "web experience" half of the entry and
the home for the series. Judges skim: it must say what it does and give the action on
the first screen.

## Non-negotiables

1. **Light AND dark mode**, both first class. Inline head script sets `data-theme` before
   first paint from `localStorage` or `prefers-color-scheme`; a visible toggle persists.
   Every colour is a CSS token keyed on `data-theme`.
2. **Category top menu with submenus** that open on hover, keyboard focus and tap.
   Submenu panel touches its trigger (`top: 100%`, no gap). One `open` state source.
   Mobile gets a hamburger panel. Categories:
   - **Start**: the 5-step path, what you need (a phone, 15 minutes, a pen and paper)
   - **Episodes**: E0 to E5, each its own page (video, chapters, transcript, "I did it")
   - **Tools**: Address checker; What the blockchain sees
   - **Help**: glossary, common mistakes, where to get support (official links only)
3. **Product-first hero**: one line ("Your first private Zcash payment in 15 minutes."),
   one button ("Start episode 1") and the episode 1 player beside it. No wall of text.
4. Sticky header is opaque or blurred; `scroll-padding-top` and `scroll-margin-top` set so
   anchors land below it. Sections on an 8px rhythm, ~40-56px padding, max width ~1200px.
5. One type family, one accent (Zcash gold, AA in both themes), radius and shadow tuned
   per theme, `prefers-reduced-motion` respected.

## The features that make it an experience, not a page

- **Progress checklist**: the 6 named steps (wallet setup, getting ZEC, shielding,
  unshielding, sending, receiving). Ticks persist in `localStorage` (parse defensively,
  validate shape, survive quota errors). A finished checklist shows a "You're shielded"
  state.
- **Address checker** (client side only, nothing leaves the browser, say so on the page):
  paste an address, it tells you what kind it is and whether it is shielded:
  transparent `t1`/`t3`, Sapling `zs1`, unified `u1`, TEX `tex1`. Verify the checksum
  (Base58Check for transparent, Bech32 for Sapling, Bech32m for unified/TEX). Verify
  every prefix and encoding against ZIP 316 / ZIP 320 and the protocol spec before
  coding; add unit tests with real known-valid public example addresses from the ZIPs
  and with tampered ones. If Ironwood introduced a new address or receiver type, cover
  it, sourced. Never ask for a phrase or key anywhere on the site.
- **What the blockchain sees**: a side-by-side diagram of a transparent send versus a
  shielded send (sender, receiver, amount, note: visible or hidden). Diagram, labelled.
- Each episode page: the video (YouTube embed with `youtube-nocookie.com` or a self
  hosted mp4 if YouTube is not ready), chapter buttons that seek, the full transcript
  from the captions file and a "Next episode" button.

## Hardening

- Production build carries a strict CSP meta (`default-src 'none'`, scripts by hash,
  `frame-src` only `https://www.youtube-nocookie.com`, `img-src 'self' data: https://i.ytimg.com`).
- `_headers` is not honoured by GitHub Pages, so rely on the meta CSP and say so in
  `SECURITY.md` Known limits.
- No analytics, no third-party scripts, no cookies. Say "no tracking" in the footer.
- Zero console errors and zero CSP violations in headless Chrome at 390 and 1360 wide,
  both themes. Screenshot each and look at them.

## Stack

Prefer a single-folder static site (HTML + CSS tokens + small vanilla JS modules) with
no framework: zero dependencies deploys anywhere and screenshots clean. If a build step
is used, Vite with exact pins. Tests for the address checker with `node --test`.

## README (the repo's landing page)

In order: themed banner (`<picture>` light/dark SVG), nav row (Watch, Try the site, Tools,
How it was made), one-paragraph pitch with the single number that matters in bold
("**15 minutes** from no wallet to your first shielded payment"), the episode table
(title, length, link), real screenshots of the site in both themes, "What is real and
what is illustrated" table, how it was built, licence (SAND for code, CC BY-ND 4.0 for
media), AI disclosure line. Every link resolves anonymously.
