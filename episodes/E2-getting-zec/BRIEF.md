# E2 · Getting ZEC: swap in the app or buy on an exchange: brief

Outcome: ZEC is arriving in your wallet.

Project file `episodes/E2-getting-zec/zts-e2.json`. Master `DEMO-E2.mp4` (gitignored; backed up in parts on the `media-renders` branch with its SHA-256 in `SHA256SUMS`). Times below are measured, from `tools/video-kit/artifacts/zts-e2/timing.json`.

## Scenes

| # | scene | kind | on-screen label | in | out | length | footage slot |
|---|---|---|---|---|---|---|---|
| 1 | `e2-open` | opening card | none | 0:00.00 | 0:07.35 | 7.4 s |  |
| 2 | `e2-routes` | illustration | Illustration | 0:07.35 | 0:18.22 | 10.9 s |  |
| 3 | `e2-swap` | step diagram | Diagram, not the app | 0:18.22 | 0:39.50 | 21.3 s | F-swap.mp4 |
| 4 | `e2-exchange` | illustration | Illustration | 0:39.50 | 0:59.19 | 19.7 s |  |
| 5 | `e2-receive` | step diagram | Diagram, not the app | 0:59.19 | 1:23.17 | 24.0 s | E-receive.mp4 |
| 6 | `e2-arrive` | illustration | Illustration | 1:23.17 | 1:41.92 | 18.8 s | G-arrive.mp4 |
| 7 | `e2-site` | site recording | none | 1:41.92 | 1:48.42 | 6.5 s |  |
| 8 | `e2-end` | end card | none | 1:48.42 | 1:58.82 | 10.4 s |  |

## Narration cues

Voice: Kokoro-82M `af_heart`, rate -20%. Each cue is spoken as written; the lexicon only changes how the engine says a word (captions keep the written form).

| # | scene | in | out | words | facts |
|---|---|---|---|---|---|
| 1 | `e2-open` | 0:00.30 | 0:06.45 | By the end of this video, ZEC will be on its way to your wallet. There are two ways to get it. |  |
| 2 | `e2-routes` | 0:07.65 | 0:17.02 | Route one: swap crypto you already have, right inside Zodl. Route two: buy ZEC on an exchange and send it to your wallet. |  |
| 3 | `e2-swap` | 0:18.52 | 0:27.03 | Route one. On the home screen, tap Swap. You can swap other crypto into shielded ZEC right inside Zodl. | F05, F19 |
| 4 | `e2-swap` | 0:27.38 | 0:33.22 | Shielded means the amount, the sender and the receiver are encrypted on the blockchain. |  |
| 5 | `e2-swap` | 0:33.57 | 0:38.30 | The swap uses NEAR Intents, not a centralized exchange. | F05 |
| 6 | `e2-exchange` | 0:39.80 | 0:44.40 | Route two. Buy ZEC on an exchange, then withdraw it to your wallet. |  |
| 7 | `e2-exchange` | 0:44.75 | 0:53.74 | Most exchanges only send ZEC to a transparent address. Transparent means public on the blockchain, like Bitcoin. | F37, F30 |
| 8 | `e2-exchange` | 0:54.09 | 0:57.99 | That is fine. Zodl will offer to shield it when it arrives. | F37, F07 |
| 9 | `e2-receive` | 0:59.49 | 1:10.59 | To find your address, tap Receive. Your Zcash Shielded Address starts with u1. Zodl shows a new one each time. They all lead to the same wallet. | F27, F28 |
| 10 | `e2-receive` | 1:10.94 | 1:21.97 | Below it is your Zcash Transparent Address. It starts with t1. If an exchange will not accept your u1 address, give it the t1 address. | F30, F37 |
| 11 | `e2-arrive` | 1:23.47 | 1:31.33 | Now wait a little. New ZEC needs 10 confirmations, about 12 and a half minutes, before you can spend it. | F33 |
| 12 | `e2-arrive` | 1:31.68 | 1:40.72 | When it lands, Zodl shows Wallet Backup Required. You already wrote your words down. Follow the steps from episode 1. | F22, F23 |
| 13 | `e2-site` | 1:42.22 | 1:44.12 | Tick Getting ZEC on the site. |  |
| 14 | `e2-end` | 1:48.72 | 1:56.92 | Next, episode 3: shielding, so your ZEC goes private. See you at zero-to-shielded.vercel.app. |  |

## On-screen strings (verbatim)

- `e2-open`: "2" / "ZERO TO SHIELDED · EPISODE 2" / "Swap in the app or buy on an exchange" / "Zodl was called Zashi in older guides"
- `e2-routes`: "1 · Swap in Zodl" / "2 · Buy on an exchange"
- `e2-swap`: "Swap" / "Other crypto" / "NEAR Intents" / "Shielded ZEC" / "Shielded: the amount, the sender and the receiver are encrypted on the blockchain"
- `e2-exchange`: "Transparent" / "Transparent: public on the blockchain, like Bitcoin. Addresses start with t" / "Zodl will offer to shield it"
- `e2-receive`: "Receive" / "Zcash Shielded Address" / "u1" / "blurred" / "Private" / "shielded" / "Zcash Transparent Address" / "t1" / "blurred" / "Not Private" / "transparent" / "New each time, same wallet"
- `e2-arrive`: "about 12.5 minutes" / "Wallet Backup Required" / "Done in episode 1"
- `e2-site`: "zero-to-shielded.vercel.app" / "/#checklist" / "Getting ZEC"
- `e2-end`: "Next: Episode 3 · Shielding and unshielding" / "zero-to-shielded.vercel.app"

## Honesty framing

- The Zodl app is never drawn or mocked. Scenes show only Zodl's own words as labels; the viewer follows along on their own phone.
- No recovery phrase words appear anywhere.
- Addresses appear only as a prefix plus blurred bars.
- Every claim traces to a fact in docs/FACTS.md (fact ids in the cue table). No price talk.
- Narration is a synthesised voice (Kokoro-82M). Music is original, generated in code.

## Gates (measured on the final file, 2026-10-04)

| gate | measured | result |
|---|---|---|
| length at most 140 s (ffprobe) | 118.817 s | pass |
| video and audio streams | video h264 1920x1080 60/1, audio aac 48000 Hz 2 ch | pass |
| loudness -16 LUFS +-1 (ffmpeg ebur128) | -16.3 LUFS integrated, LRA 3.4 LU | pass |
| true peak under -1.5 dBTP | -1.9 dBTP | pass |
| music | `zts-bed.wav` (original, generated by `tools/music/compose.py`), named in the build log | pass |
| captions | 14 cues for 14 narration cues, last out 1:56.92 inside 1:58.82, shortest 1.90 s | pass |
| chapters | 0:00 Two ways · 0:18 Getting ZEC: swap in Zodl · 0:39 Getting ZEC: buy on an exchange · 0:59 Receiving: your addresses · 1:23 Getting ZEC: it arrives (shortest 18 s) | pass |
| voice gate | narration in the project file, captions.srt, the description: voice-gate: clean (2 inputs) | pass |
| frames at each climax looked at | end-card frame of the final file at 1:55; scene climaxes on a contact sheet of the earlier render, which differs only in that caption (sheet.py, at most 1600 px) | pass |
| web scene URL returns 200 anonymously | https://zero-to-shielded.vercel.app/episodes/e2/ | PENDING: the site is not deployed yet |

## Notes

- Re-rendered on 2026-10-04 so the end-card caption shows the written URL.
