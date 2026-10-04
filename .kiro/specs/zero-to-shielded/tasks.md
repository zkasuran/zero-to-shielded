# Tasks

Work top to bottom. Tick each box in a commit. Priority: P0 must ship, P1 should, P2 if
time. Never start a P1 while a P0 is open, except the site skeleton (needed for `web`
scenes).

## P0: foundations (target done Oct 4 02:00 IST)

- [x] 1. Install the toolchain (20-video.md), run `cd tools/video-kit && python3 -m pytest -q tests` (expect 47 passed) and `./verify.sh` baseline.
  Done: Python 3.12.13, pins in `tools/video-kit/requirements.txt`, ffmpeg 7.0.2 static, Chromium 140 (Playwright 1.55.0), DejaVu 2.37. 47 passed. verify.sh ALL GREEN after fixing its outward-file `find` (it matched nothing before).
- [x] 2. Create `docs/FACTS.md`: every "Must verify" item in 40-zcash-facts.md resolved with a primary-source URL and quote. Anything unresolved is marked UNVERIFIED and kept out of scripts.
  Done: 52 rows (47 VERIFIED, 3 UNVERIFIED, 2 CONTRADICTED), labels pinned to zodl-android 9f4e719 and zodl-ios 6a7dc6b. edge-tts audio has no quotable grant (see Licence quotes).
- [ ] 3. Add the `shield` palette to `tools/video-kit/theme.py`; render one check frame; confirm accent AA on the panel with `contrast.py`.
- [x] 4. Site skeleton: home + E1-E4 pages + checklist, light/dark, menu. Deploy to GitHub Pages (orphan `gh-pages` branch or Pages from `/site` via Actions). The URL must return 200 before any `web` scene is captured. NOTE: Pages on a private repo needs a paid plan; if Pages fails while private, tell the lead, who will flip the repo public at that point.
  Done: full static site in `site/` (14 pages, Vercel-ready `vercel.json` with real security headers). Deploy is the one open item: the Pages API returns 403 on this private repo and Vercel needs the lead's account. See `site/README-DEPLOY.md`. Planned URL https://zero-to-shielded.vercel.app (returned DEPLOYMENT_NOT_FOUND on 2026-10-04, so the name is free).
- [ ] 5. Read `footage/SHOT-LIST.md` and `footage/clean/` to see what real footage exists. Map each script beat to a clip or to the labelled-diagram fallback.

## P0: episodes 1 to 4 (target Oct 4 08:00 IST)

- [ ] 6. E1 project file + BRIEF.md, preflight, frames looked at, build, upload package, gates recorded.
- [ ] 7. E2 same.
- [ ] 8. E3 same.
- [ ] 9. E4 same (climax episode, spend the extra care here).
- [ ] 10. Cross-episode check: same voice, palette, opening card, glossary words; each <= 140 s.

## P0: submission (target Oct 4 15:00 IST)

- [ ] 11. README per 30-web.md, with real site screenshots both themes.
- [ ] 12. `LICENSE-MEDIA.md` (CC BY-ND 4.0 notice), `DATA-SOURCES.md` complete, `SECURITY.md` with Known limits.
- [ ] 13. `docs/THREAD.md` (this one IS committed, no personal data): post 1 + one reply per episode + final reply; char counts; voice gate clean.
- [ ] 14. `./verify.sh` ALL GREEN. Commit. Write `docs/HANDOFF.md`: what shipped, measured lengths, what is pending (music, footage gaps), exact upload order.

## P1

- [x] 15. Address checker tool page + tests from ZIP vectors. (60 unified, 15 ZIP 320 pairs, 26 transparent, BIP 173/350 vectors; tampered copies fail.)
- [x] 16. "What the blockchain sees" page.
- [ ] 17. Transcripts on episode pages from captions.srt; chapter seek buttons.
- [ ] 18. E5 Stay private.
- [ ] 19. 4:5 crops for X.

## P2

- [ ] 20. E0 trailer from the E1-E4 climaxes.
- [x] 21. Help page: glossary, common mistakes, official support links. (Plus Phrase Guard at /learn/phrase-guard/.)

## Human-only (the lead and zkasuran handle these, do not block on them)

- Record phone footage per SHOT-LIST.md and drop into `footage/raw/`, then lead crops/blurs into `footage/clean/`.
- Fund the wallet with a small amount (spending real money is the human's call).
- Upload episodes to X / YouTube, flip repo public, post the thread tagging @zksnarks_.
