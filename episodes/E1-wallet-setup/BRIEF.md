# E1 · Wallet setup: install Zodl and back up your phrase: brief

Outcome: You have a wallet and your recovery phrase is on paper.

Project file `episodes/E1-wallet-setup/zts-e1.json`. Master `DEMO-E1.mp4` (gitignored; backed up in parts on the `media-renders` branch with its SHA-256 in `SHA256SUMS`). Times below are measured, from `tools/video-kit/artifacts/zts-e1/timing.json`.

## Scenes

| # | scene | kind | on-screen label | in | out | length | footage slot |
|---|---|---|---|---|---|---|---|
| 1 | `e1-open` | opening card | none | 0:00.00 | 0:09.68 | 9.7 s |  |
| 2 | `e1-wallet` | illustration | Illustration | 0:09.68 | 0:25.01 | 15.3 s |  |
| 3 | `e1-install` | step diagram | Diagram, not the app | 0:25.01 | 0:40.80 | 15.8 s | A-install.mp4 |
| 4 | `e1-create` | step diagram | Diagram, not the app | 0:40.80 | 0:51.09 | 10.3 s | ['B-create.mp4', 'D-home.mp4'] |
| 5 | `e1-phrase` | illustration | Illustration | 0:51.09 | 1:04.97 | 13.9 s |  |
| 6 | `e1-backup` | step diagram | Diagram, not the app | 1:04.97 | 1:27.85 | 22.9 s | C-phrase.mp4 |
| 7 | `e1-later` | step diagram | Diagram, not the app | 1:27.85 | 1:42.67 | 14.8 s | C-phrase.mp4 |
| 8 | `e1-site` | site recording | none | 1:42.67 | 1:49.67 | 7.0 s |  |
| 9 | `e1-end` | end card | none | 1:49.67 | 1:59.77 | 10.1 s |  |

## Narration cues

Voice: Kokoro-82M `af_heart`, rate -20%. Each cue is spoken as written; the lexicon only changes how the engine says a word (captions keep the written form).

| # | scene | in | out | words | facts |
|---|---|---|---|---|---|
| 1 | `e1-open` | 0:00.30 | 0:08.78 | By the end of this video, you will have a private Zcash wallet on your phone. Your recovery phrase will be safe on paper. | F10, F21 |
| 2 | `e1-wallet` | 0:09.98 | 0:17.78 | First, what is a wallet? It is an app that holds your keys. Your keys let you spend your ZEC, the coin of Zcash. |  |
| 3 | `e1-wallet` | 0:18.13 | 0:23.81 | You do not need an email address or a phone number. Only you control this wallet. | F10 |
| 4 | `e1-install` | 0:25.31 | 0:32.04 | We will use Zodl. Zodl is a Zcash wallet for your phone. Older guides call it Zashi. | F01 |
| 5 | `e1-install` | 0:32.39 | 0:39.60 | Get Zodl from the App Store or the Play Store. On Android you can also use F-Droid or GitHub. | F04 |
| 6 | `e1-create` | 0:41.10 | 0:43.81 | Open Zodl and tap Create New Wallet. | F18 |
| 7 | `e1-create` | 0:44.16 | 0:49.89 | That is it. Your home screen has four buttons: Receive, Send, Pay and Swap. | F19 |
| 8 | `e1-phrase` | 0:51.39 | 0:58.99 | Now the most important step. Your wallet has a recovery phrase. It is 24 words in a set order. | F21 |
| 9 | `e1-phrase` | 0:59.34 | 1:03.77 | If you lose your phone, those words bring your wallet back on a new one. |  |
| 10 | `e1-backup` | 1:05.27 | 1:11.34 | Back it up right now. Open Advanced Settings, then tap Zodl Recovery Phrase. | F24 |
| 11 | `e1-backup` | 1:11.69 | 1:16.75 | Write the 24 words on paper, in order. Check every word twice. | F25 |
| 12 | `e1-backup` | 1:17.10 | 1:26.35 | Three rules. Keep it on paper. Never type it into a website. Nobody legitimate will ever ask for it, not even Zodl. | F25, F17 |
| 13 | `e1-later` | 1:28.15 | 1:32.79 | When your first ZEC arrives, Zodl shows Wallet Backup Required. | F22 |
| 14 | `e1-later` | 1:33.14 | 1:41.47 | Tap Start, then Next, then Reveal security details. Check the words against your paper, then tap I've saved it. | F23 |
| 15 | `e1-site` | 1:42.97 | 1:48.26 | Your wallet is set up. Tick Wallet setup on the site to track your progress. |  |
| 16 | `e1-end` | 1:49.97 | 1:57.87 | Next, episode 2: getting your first ZEC. Every step is at zero-to-shielded.vercel.app. |  |

## On-screen strings (verbatim)

- `e1-open`: "1" / "ZERO TO SHIELDED · EPISODE 1" / "Install Zodl and back up your phrase" / "Zodl was called Zashi in older guides"
- `e1-wallet`: "Email" / "Phone number" / "Account"
- `e1-install`: "Zashi" / "Zodl" / "App Store" / "Play Store" / "F-Droid" / "GitHub"
- `e1-create`: "Open Zodl" / "Create New Wallet" / "Create New Wallet" / "Receive" / "Send" / "Pay" / "Swap" / "On iPhone: Create new wallet"
- `e1-phrase`: none
- `e1-backup`: "phrase blurred" / "Advanced Settings" / "Zodl Recovery Phrase" / "Keep it on paper" / "Never type it into a website" / "Nobody legitimate will ever ask for it"
- `e1-later`: "Wallet Backup Required" / "Start" / "Next" / "Reveal security details" / "I've saved it"
- `e1-site`: "zero-to-shielded.vercel.app" / "/#checklist" / "Wallet setup"
- `e1-end`: "Next: Episode 2 · Getting ZEC" / "zero-to-shielded.vercel.app"

## Honesty framing

- The Zodl app is never drawn or mocked. Scenes show only Zodl's own words as labels; the viewer follows along on their own phone.
- No recovery phrase words appear anywhere.
- Addresses appear only as a prefix plus blurred bars.
- Every claim traces to a fact in docs/FACTS.md (fact ids in the cue table). No price talk.
- Narration is a synthesised voice (Kokoro-82M). Music is original, generated in code.

## Gates (measured on the final file, 2026-10-04)

| gate | measured | result |
|---|---|---|
| length at most 140 s (ffprobe) | 119.767 s | pass |
| video and audio streams | video h264 1920x1080 60/1, audio aac 48000 Hz 2 ch | pass |
| loudness -16 LUFS +-1 (ffmpeg ebur128) | -16.3 LUFS integrated, LRA 2.8 LU | pass |
| true peak under -1.5 dBTP | -2.0 dBTP | pass |
| music | `zts-bed.wav` (original, generated by `tools/music/compose.py`), named in the build log | pass |
| captions | 16 cues for 16 narration cues, last out 1:57.87 inside 1:59.77, shortest 2.71 s | pass |
| chapters | 0:00 What you will do · 0:25 Wallet setup: install Zodl and create your wallet · 0:51 Wallet setup: back up your recovery phrase · 1:42 Next step (shortest 17.8 s) | pass |
| voice gate | narration in the project file, captions.srt, the description: voice-gate: clean (2 inputs) | pass |
| frames at each climax looked at | contact sheet of every scene climax from the final file (sheet.py, at most 1600 px) | pass |
| web scene URL returns 200 anonymously | https://zero-to-shielded.vercel.app/episodes/e1/ | PENDING: the site is not deployed yet |

## Notes

- Re-rendered on 2026-10-04 for the opening title spacing and written-form captions.
