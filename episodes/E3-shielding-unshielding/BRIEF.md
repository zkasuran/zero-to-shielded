# E3 · Shielding and unshielding: brief

Outcome: Your ZEC is shielded and you know when to unshield.

Project file `episodes/E3-shielding-unshielding/zts-e3.json`. Master `DEMO-E3.mp4` (gitignored; backed up in parts on the `media-renders` branch with its SHA-256 in `SHA256SUMS`). Times below are measured, from `tools/video-kit/artifacts/zts-e3/timing.json`.

## Scenes

| # | scene | kind | on-screen label | in | out | length | footage slot |
|---|---|---|---|---|---|---|---|
| 1 | `e3-open` | opening card | none | 0:00.00 | 0:08.24 | 8.2 s |  |
| 2 | `e3-sees` | diagram | Diagram | 0:08.24 | 0:35.23 | 27.0 s |  |
| 3 | `e3-shield` | step diagram | Diagram, not the app | 0:35.23 | 0:54.28 | 19.1 s | H-shield.mp4 |
| 4 | `e3-ironwood` | illustration | Illustration | 0:54.28 | 1:09.59 | 15.3 s | L-ironwood.mp4 |
| 5 | `e3-unshield` | diagram | Diagram | 1:09.59 | 1:38.53 | 28.9 s | K-unshield.mp4 |
| 6 | `e3-checker` | site recording | none | 1:38.53 | 1:54.78 | 16.3 s |  |
| 7 | `e3-end` | end card | none | 1:54.78 | 2:03.02 | 8.2 s |  |

## Narration cues

Voice: Kokoro-82M `af_heart`, rate -20%. Each cue is spoken as written; the lexicon only changes how the engine says a word (captions keep the written form).

| # | scene | in | out | words | facts |
|---|---|---|---|---|---|
| 1 | `e3-open` | 0:00.30 | 0:07.34 | By the end of this video, your ZEC will be shielded. You will also know when to unshield and what it shows. |  |
| 2 | `e3-sees` | 0:08.54 | 0:15.88 | First, what does the blockchain see? The blockchain is a public record of payments. Anyone can look at it. |  |
| 3 | `e3-sees` | 0:16.23 | 0:23.37 | A transparent payment is like a postcard. Anyone can read who sent it, who got it and how much. | F51, F30 |
| 4 | `e3-sees` | 0:23.72 | 0:34.03 | A shielded payment is like a sealed letter. The amount, the sender and the receiver are encrypted. Only the people in the payment can read it. | F51, F08 |
| 5 | `e3-shield` | 0:35.53 | 0:39.89 | Shielding means moving your own ZEC from transparent to shielded. |  |
| 6 | `e3-shield` | 0:40.24 | 0:46.82 | When ZEC lands at your transparent address, Zodl shows Unshielded Balance. Tap Shield. | F31, F07 |
| 7 | `e3-shield` | 0:47.17 | 0:52.78 | If a sheet opens, tap Shield again. When Zodl shows Shielded!, you are done. | F31 |
| 8 | `e3-ironwood` | 0:54.58 | 1:01.25 | Your shielded ZEC goes into Ironwood, the newest shielded pool. You do not have to do anything. | F26, F32 |
| 9 | `e3-ironwood` | 1:01.60 | 1:08.39 | If Zodl asks you to migrate to Ironwood, that is a normal upgrade, your ZEC stays shielded. | F13, F16 |
| 10 | `e3-unshield` | 1:09.89 | 1:16.83 | Unshielding is the opposite. You send ZEC from your shielded balance to a transparent address. | F42 |
| 11 | `e3-unshield` | 1:17.18 | 1:27.35 | You only need it when you must pay an address that starts with t1 or tex1. Some exchanges use tex1 addresses for deposits. | F42, F39 |
| 12 | `e3-unshield` | 1:27.70 | 1:37.33 | When you unshield, the amount and that address are public. You cannot add a note. For a tex1 address, Zodl does the two steps for you. | F43, F41 |
| 13 | `e3-checker` | 1:38.83 | 1:43.58 | Not sure what an address is? Paste it into the address checker on the site. |  |
| 14 | `e3-checker` | 1:43.93 | 1:53.58 | Your Zodl u1 address is shielded. A t1 or tex1 address is transparent. Nothing you paste leaves your browser. | F27, F28, F46, F39 |
| 15 | `e3-end` | 1:55.08 | 2:01.12 | Tick Shielding and Unshielding. Next, episode 4: your first shielded payment. |  |

## On-screen strings (verbatim)

- `e3-open`: "3" / "ZERO TO SHIELDED · EPISODE 3" / "Shielding and unshielding" / "Zodl was called Zashi in older guides"
- `e3-sees`: "From Maya" / "To Sam" / "0.5 ZEC"
- `e3-shield`: "Shielding: moving your own ZEC from transparent to shielded" / "Unshielded Balance" / "Shield" / "Shield" / "Shielded!"
- `e3-ironwood`: "Ironwood: the newest shielded pool" / "Ironwood" / "If Zodl asks you to migrate, that is a normal upgrade"
- `e3-unshield`: "t1…" / "tex1…" / "Amount: public" / "Address: public" / "Note: not possible" / "tex1: Zodl does the two steps for you"
- `e3-checker`: "zero-to-shielded.vercel.app" / "/tools/address/#checker" / "u1" / "Shielded" / "t1" / "Transparent" / "tex1" / "Transparent" / "Nothing you paste leaves your browser"
- `e3-end`: "Shielding" / "Unshielding" / "Next: Episode 4 · Sending and receiving" / "zero-to-shielded.vercel.app"

## Honesty framing

- The Zodl app is never drawn or mocked. Scenes show only Zodl's own words as labels; the viewer follows along on their own phone.
- No recovery phrase words appear anywhere.
- Addresses appear only as a prefix plus blurred bars.
- Every claim traces to a fact in docs/FACTS.md (fact ids in the cue table). No price talk.
- Narration is a synthesised voice (Kokoro-82M). Music is original, generated in code.

## Gates (measured on the final file, 2026-10-04)

| gate | measured | result |
|---|---|---|
| length at most 140 s (ffprobe) | 123.017 s | pass |
| video and audio streams | video h264 1920x1080 60/1, audio aac 48000 Hz 2 ch | pass |
| loudness -16 LUFS +-1 (ffmpeg ebur128) | -16.3 LUFS integrated, LRA 3.2 LU | pass |
| true peak under -1.5 dBTP | -2.0 dBTP | pass |
| music | `zts-bed.wav` (original, generated by `tools/music/compose.py`), named in the build log | pass |
| captions | 15 cues for 15 narration cues, last out 2:01.12 inside 2:03.02, shortest 4.36 s | pass |
| chapters | 0:00 What the blockchain sees · 0:35 Shielding: tap Shield · 0:54 Ironwood · 1:09 Unshielding: when you need it · 1:38 Check an address (shortest 15 s) | pass |
| voice gate | narration in the project file, captions.srt, the description: voice-gate: clean (2 inputs) | pass |
| frames at each climax looked at | contact sheet of every scene climax from the final file (sheet.py, at most 1600 px) | pass |
| web scene URL returns 200 anonymously | https://zero-to-shielded.vercel.app/episodes/e3/ | pass: 200 on 2026-10-04 (curl, signed out) |

## Notes

- The checker scene shows the ZIP test-vector addresses as a prefix plus blurred bars.
- Rendered before the caption fix. Its narration has no multi-word lexicon tokens, so the captions already match the written script.

Published on YouTube 2026-10-04: https://youtu.be/ydsSzy9AXWg (public, oEmbed 200 signed out).
