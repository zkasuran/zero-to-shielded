# Music

Original background music for the Zero to Shielded videos. Calm lo-fi in D major at 92 BPM:
a warm pad, a soft electric piano, a round sub bass, light brushes and a bell every 8 bars.

| file | what it is | length |
|---|---|---|
| `zts-bed.wav` | Bed for every episode. 48 bars that loop end to start with no gap or click. Drums rest in the first 4 and last 4 bars so the loop point breathes. | 125.217 s |
| `zts-trailer.wav` | For the 30 s trailer. Pad alone, full groove at 7 s, a lift at 20 s, a held Dmaj9 at 27.8 s that is silent by 34 s. Does not loop. | 34.000 s |
| `preview-ducked.wav` | Level check only, do not publish. A speech-like noise signal over the bed at -21 dB with ducking. | 12.000 s |
| `levels.json` | Numbers measured while rendering, plus the SHA-256 of each file. | |

All files are 48 kHz 24-bit stereo WAV.

## How it was made

The music is original. `tools/music/compose.py` generates every sound from code at render
time: band-limited oscillators, FM synthesis, additive bells, a sine bass and filtered noise.
No samples. No third-party audio. No AI music model. The script was written with AI
assistance (Kiro) and holds no audio data. Seeds are fixed, so a re-render gives the same bytes.

## Regenerate

```bash
python3 tools/music/compose.py   # about 30 s; Python 3.12, numpy 2.3.3, ffmpeg 7
python3 tools/music/check.py     # full validation report, exits 1 if a check fails
```

Use the bed in an episode build from `tools/video-kit`:

```bash
MUSIC=../../music/zts-bed.wav python3 build.py projects/zts-e1.json
```

## Measured

`ffmpeg -i <file> -af ebur128=peak=true -f null -`

| file | integrated | true peak | loudness range |
|---|---|---|---|
| `zts-bed.wav` | -14.0 LUFS | -2.3 dBTP | 1.7 LU |
| `zts-trailer.wav` | -14.0 LUFS | -2.3 dBTP | 9.6 LU |
| `preview-ducked.wav` | -16.0 LUFS | -2.2 dBTP | 1.4 LU |

The 1.5 to 4 kHz band (where speech is clearest) holds 0.5 % of the bed's energy. Through the
video kit's ducking a voice at -20 LUFS sits about 24 LU above the bed while it speaks.

## Licence

Original music by the Zero to Shielded author, released with the videos under CC BY-ND 4.0.
