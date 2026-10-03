# Shot list (human records on a phone with Zodl)

This footage is what makes the entry win: real app, current screens. Record in portrait,
screen recording on (iOS Control Centre or Android Quick Settings), Do Not Disturb on,
battery and clock visible is fine. Tap slowly, pause 1 second on every screen.

Use a fresh wallet made for this recording. Fund it with a small amount only.

| Clip | File name | What to record | Privacy |
|---|---|---|---|
| A | `A-install.mp4` | Store page for Zodl, tap Install/Open | none |
| B | `B-create.mp4` | First launch, create new wallet, every onboarding screen | none |
| C | `C-phrase.mp4` | Recovery phrase screen and the confirm step | **phrase must be blurred before use; if the OS blocks recording here, record the screen before and after** |
| D | `D-home.mp4` | Wallet home, empty | none |
| E | `E-receive.mp4` | Receive screen: shielded address/QR, then the transparent address option | addresses are fine for a throwaway wallet, but lead will crop |
| F | `F-swap.mp4` | Swap: choose an asset, see the quote, (optional) complete it | amounts visible, keep small |
| G | `G-arrive.mp4` | Funds arriving (transparent, if funded from an exchange) | balance visible: OK if small |
| H | `H-shield.mp4` | The "shield" prompt, tap it, shielded balance after | |
| I | `I-send.mp4` | Send: paste/scan address, amount, write a note, review screen with fee, confirm | |
| J | `J-received.mp4` | On a second wallet/phone: the payment and note arriving | |
| K | `K-unshield.mp4` | Send a small amount to a `t1` or `tex1` address (e.g. your own transparent address) and the review screen | |
| L | `L-ironwood.mp4` | Ironwood migration prompt, if this wallet shows one | |
| M | `M-settings.mp4` | Settings: Tor or privacy options, if any | |

Drop files into `footage/raw/` (gitignored). The lead crops and blurs into
`footage/clean/` and records in `footage/clean/INDEX.md` which clip covers which beat.

Minimum to win: B, C, E, H, I, J. Everything else has a diagram fallback.
