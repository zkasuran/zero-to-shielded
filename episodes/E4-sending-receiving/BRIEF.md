# E4 · Sending and receiving: your first shielded transaction: brief

Outcome: You sent and received a shielded payment with a private note.

Project file `episodes/E4-sending-receiving/zts-e4.json`. Master `DEMO-E4.mp4` (gitignored; backed up in parts on the `media-renders` branch with its SHA-256 in `SHA256SUMS`). Times below are measured, from `tools/video-kit/artifacts/zts-e4/timing.json`.

## Scenes

| # | scene | kind | on-screen label | in | out | length | footage slot |
|---|---|---|---|---|---|---|---|
| 1 | `e4-open` | opening card | none | 0:00.00 | 0:08.04 | 8.0 s |  |
| 2 | `e4-receive` | step diagram | Diagram, not the app | 0:08.04 | 0:25.85 | 17.8 s | E-receive.mp4 |
| 3 | `e4-send` | step diagram | Diagram, not the app | 0:25.85 | 0:45.01 | 19.2 s | I-send.mp4 |
| 4 | `e4-confirm` | step diagram | Diagram, not the app | 0:45.01 | 1:09.43 | 24.4 s | I-send.mp4 |
| 5 | `e4-arrive` | illustration | Illustration | 1:09.43 | 1:23.89 | 14.5 s | J-received.mp4 |
| 6 | `e4-chain` | diagram | Diagram | 1:23.89 | 1:33.70 | 9.8 s |  |
| 7 | `e4-done` | celebration | Illustration | 1:33.70 | 1:39.20 | 5.5 s |  |
| 8 | `e4-site` | site recording | none | 1:39.20 | 1:46.20 | 7.0 s |  |
| 9 | `e4-end` | end card | none | 1:46.20 | 1:56.36 | 10.2 s |  |

## Narration cues

Voice: Kokoro-82M `af_heart`, rate -20%. Each cue is spoken as written; the lexicon only changes how the engine says a word (captions keep the written form).

| # | scene | in | out | words | facts |
|---|---|---|---|---|---|
| 1 | `e4-open` | 0:00.30 | 0:07.14 | By the end of this video, you will have sent and received your first shielded payment, with a private note. |  |
| 2 | `e4-receive` | 0:08.34 | 0:12.34 | Every payment has two sides. Let's start with receiving. |  |
| 3 | `e4-receive` | 0:12.69 | 0:19.00 | To get paid, tap Receive. Copy your Zcash Shielded Address. It starts with u1. | F27, F28, F30 |
| 4 | `e4-receive` | 0:19.35 | 0:24.65 | Send it to the person paying you. They can also scan it if you tap QR Code. | F30 |
| 5 | `e4-send` | 0:26.15 | 0:32.02 | Now sending. Tap Send. Paste the address into Send to, then type the amount. | F35 |
| 6 | `e4-send` | 0:32.37 | 0:42.10 | In Message, you can add a note. A note is a private message that travels with the payment. Only you and the person you pay can read it. | F35, F08 |
| 7 | `e4-send` | 0:42.45 | 0:43.81 | Then tap Review. | F35 |
| 8 | `e4-confirm` | 0:45.31 | 0:51.93 | Before anything is sent, Zodl shows the Confirmation screen. Check the address and the fee. | F35 |
| 9 | `e4-confirm` | 0:52.28 | 1:01.94 | Zcash fees follow a public rule called ZIP 317. The smallest fee is 0.0001 ZEC. | F34 |
| 10 | `e4-confirm` | 1:02.29 | 1:07.93 | Tap Send. When Zodl shows Sent!, your first shielded payment is on its way. | F35 |
| 11 | `e4-arrive` | 1:09.73 | 1:15.64 | On your friend's phone, the payment arrives with your note. Only the two of you can read it. | F08 |
| 12 | `e4-arrive` | 1:15.99 | 1:22.69 | Ask them to send a little back to your u1 address. Now you have received a shielded payment too. |  |
| 13 | `e4-chain` | 1:24.19 | 1:32.50 | And what does the blockchain show? Only scrambled data. Not who paid. Not who got paid. Not how much. Not the note. | F51, F08 |
| 14 | `e4-done` | 1:34.00 | 1:35.83 | You did it. You're shielded. |  |
| 15 | `e4-site` | 1:39.50 | 1:43.53 | Tick Sending and Receiving on the site to finish your checklist. |  |
| 16 | `e4-end` | 1:46.50 | 1:54.46 | Episode 5 shows five habits that keep it private. Find it at zero-to-shielded.vercel.app. |  |

## On-screen strings (verbatim)

- `e4-open`: "4" / "ZERO TO SHIELDED · EPISODE 4" / "Your first shielded transaction" / "Zodl was called Zashi in older guides"
- `e4-receive`: "Receive" / "Zcash Shielded Address" / "u1" / "blurred" / "Copy" / "QR Code"
- `e4-send`: "u1" / "blurred" / "0.05 ZEC" / "Thanks for lunch!" / "Review" / "Note: a private message that travels with a shielded payment"
- `e4-confirm`: "Confirmation" / "Total Amount" / "Send to" / "Amount" / "Fee" / "Message" / "ZIP 317 · smallest fee 0.0001 ZEC" / "Send" / "Sent!"
- `e4-arrive`: "Thanks for lunch!"
- `e4-chain`: "What the blockchain sees" / "Sender" / "Receiver" / "Amount" / "Note"
- `e4-done`: "You're shielded."
- `e4-site`: "zero-to-shielded.vercel.app" / "/#checklist" / "Sending" / "Receiving" / "You're shielded"
- `e4-end`: "Next: Episode 5 · Stay private" / "zero-to-shielded.vercel.app"

## Honesty framing

- The Zodl app is never drawn or mocked. Scenes show only Zodl's own words as labels; the viewer follows along on their own phone.
- No recovery phrase words appear anywhere.
- Addresses appear only as a prefix plus blurred bars.
- Every claim traces to a fact in docs/FACTS.md (fact ids in the cue table). No price talk.
- Narration is a synthesised voice (Kokoro-82M). Music is original, generated in code.

## Gates (measured on the final file, 2026-10-04)

| gate | measured | result |
|---|---|---|
| length at most 140 s (ffprobe) | 116.364 s | pass |
| video and audio streams | video h264 1920x1080 60/1, audio aac 48000 Hz 2 ch | pass |
| loudness -16 LUFS +-1 (ffmpeg ebur128) | -16.5 LUFS integrated, LRA 3.5 LU | pass |
| true peak under -1.5 dBTP | -1.9 dBTP | pass |
| music | `zts-bed.wav` (original, generated by `tools/music/compose.py`), named in the build log | pass |
| captions | 16 cues for 16 narration cues, last out 1:54.46 inside 1:56.36, shortest 1.36 s | pass |
| chapters | 0:00 Receiving: share your address · 0:25 Sending: your first shielded transaction · 0:45 Confirm and send · 1:09 Receiving: the note arrives · 1:33 You're shielded (shortest 20 s) | pass |
| voice gate | narration in the project file, captions.srt, the description: voice-gate: clean (2 inputs) | pass |
| frames at each climax looked at | contact sheet of every scene climax from the final file (sheet.py, at most 1600 px) | pass |
| web scene URL returns 200 anonymously | https://zero-to-shielded.vercel.app/episodes/e4/ | PENDING: the site is not deployed yet |

## Notes

- Re-rendered on 2026-10-04 with written-form captions.
