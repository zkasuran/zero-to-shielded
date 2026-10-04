# Deploying the site

The site is plain static files in this folder. There is no build step on the host and
no runtime dependency.

## Vercel (the live site)

Dashboard: import the GitHub repo, set **Root Directory** to `site`, Framework Preset
**Other**, leave Build Command and Output Directory empty. Name the project
`zero-to-shielded` so the address is https://zero-to-shielded.vercel.app

CLI, from the repo root:

```bash
cd site && npx vercel@62.2.0 --prod
```

`vercel@62.2.0` is the exact CLI version pinned here (the latest on 2026-10-04). On the
first run, answer `zero-to-shielded` for the project name and `./` for the directory.

`vercel.json` sends the security headers (CSP with `frame-ancestors 'none'`, HSTS,
nosniff, no referrer, Permissions-Policy, COOP) and cache rules for `/fonts` and
`/media`. `.vercelignore` keeps `test/` and the scripts in `tools/` off the host.

## Adding the videos

Put the files in `site/media/` with these exact names:

| File | What |
|---|---|
| `zts-e1.mp4` | the episode video (E0 to E5: `zts-e0.mp4` to `zts-e5.mp4`) |
| `zts-e1.jpg` | its poster, 16:9 |
| `zts-e1.srt` | its captions; the episode page turns them into the transcript |

Then run the build so every page knows which files exist. Commit the result:

```bash
node site/tools/build.mjs
node --test site/test/
```

A player only points at files that exist when you run the build, so a missing file never
causes a 404.

Watch out: the root `.gitignore` ignores `*.mp4`. A Git-connected Vercel deploy only sees
committed files, so it would have the pages but not the videos. Two safe options:

- deploy with the CLI from the machine that has the files. The CLI uploads everything in
  `site/` except what `.vercelignore` lists.
- or use YouTube ids (next section) and commit only the `.jpg` and `.srt` files. Then
  delete any local `zts-e*.mp4` before you build, so no page points at an mp4.

## YouTube

In `site/js/episodes.js` set `youtubeId` to the 11 characters after `watch?v=` in the
video's YouTube address, then run `node site/tools/build.mjs`. The episode then plays from
`youtube-nocookie.com`, only after the visitor presses play. Chapter buttons
restart the embed at their time.

## Chapters

Edit `chapters` for each episode in `site/js/episodes.js` (`t` is seconds), set
`chaptersDraft: false`, then run the build.

## Checks before you deploy

```bash
node --test site/test/                         # unit tests, page sync, CSP, links, contrast, voice
python3 -m http.server 8765 --directory site & # then, with Playwright installed:
python3 site/tools/browser-check.py            # zero console errors and CSP violations
python3 site/tools/interaction-check.py        # checklist, storage, menu, tools end to end
```
