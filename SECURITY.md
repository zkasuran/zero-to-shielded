# Security

The companion site (`site/`) is static HTML, CSS and a few small JavaScript modules. It
has no server code, no accounts, no forms and no database.

## What the site does

- Plays the episodes: a self-hosted mp4 or YouTube from `youtube-nocookie.com`. The
  YouTube player loads only after you press play. Until then nothing is fetched from
  YouTube, except the thumbnail from `i.ytimg.com` when an episode has a YouTube id and
  no local poster.
- Keeps your checklist ticks, your theme choice and your best Address detective streak in
  your own browser (`localStorage` keys `zts-progress`, `zts-theme`,
  `zts-detective-best`). They never leave the device. Junk or blocked storage is handled:
  the page falls back to memory for the visit.
- Checks Zcash addresses on your device (`site/js/address.js`). It reads the prefix and
  verifies the checksum: Base58Check with double SHA-256 for `t1`/`t3`, Bech32 for
  `zs1`, Bech32m for `u1` and `tex1`. What you paste is only ever set as text, never as
  HTML. It is not stored or sent.

## What the site never does

- No tracking, no cookies, no analytics, no third-party scripts or fonts.
- It never asks for a recovery phrase or a key. There is no field for one. If someone
  pastes a list of 12 or more words or something shaped like a secret key into the
  address checker, the page clears it at once and says why.
- No network request carries anything you typed. `connect-src 'self'` only allows the
  transcript files on the same site.

## Content Security Policy

Every page carries this policy in a `<meta>` tag. The one inline script (it sets light or
dark before the first paint) is allowed by its SHA-256 hash, which
`site/tools/csp.mjs` computes from the pages so it cannot drift. `node --test site/test/`
fails if any page or `vercel.json` is out of date.

```
default-src 'none'; script-src 'self' 'sha256-<hash of the theme script>'; style-src 'self';
img-src 'self' data: https://i.ytimg.com; media-src 'self'; font-src 'self';
connect-src 'self'; frame-src https://www.youtube-nocookie.com; base-uri 'none';
form-action 'none'; object-src 'none'
```

There are no inline styles or style blocks, so `style-src` needs no `unsafe-inline`.
Motion uses classes, CSSOM custom properties and the Web Animations API.

On Vercel, `site/vercel.json` also sends real HTTP headers on every route: the same CSP
plus `frame-ancestors 'none'`, `Strict-Transport-Security`, `X-Content-Type-Options:
nosniff`, `Referrer-Policy: no-referrer`, `Permissions-Policy: camera=(),
microphone=(), geolocation=(), payment=()`, `Cross-Origin-Opener-Policy: same-origin`
and `X-Frame-Options: DENY`.

The YouTube iframe sets `referrerpolicy="strict-origin-when-cross-origin"` for itself,
because the YouTube embed refuses to play with no referrer. It sends only the site's
origin and only once you press play.

## Known limits

- **GitHub Pages ignores `_headers` and every custom header.** There, the meta CSP is the
  only protection. A meta CSP cannot carry `frame-ancestors`, so on Pages another site can
  frame this one. HSTS, nosniff, Permissions-Policy and COOP are not sent either.
  On Vercel, `vercel.json` sends all of them as real headers.
- The `u1` check covers the prefix and the Bech32m checksum. A unified address is
  F4Jumbled; the checker does not invert that, so it does not list the receivers inside
  and cannot tell whether a `u1` from another wallet also holds a transparent receiver.
  The page says so.
- A valid checksum means the address was not mistyped. It cannot tell you whose address
  it is.
- Anyone with access to your browser profile can read the checklist ticks. They hold no
  secrets.

## Reporting a problem

Please open a private security advisory on the GitHub repository
(https://github.com/zkasuran/zero-to-shielded/security/advisories/new) rather than a
public issue.
