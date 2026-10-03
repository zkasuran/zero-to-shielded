# House rules (non-negotiable)

## Honesty

- **Everything on screen is real.** Wallet screens come from real phone recordings in
  `footage/raw/`. Never draw, mock or AI-generate a wallet UI. Diagrams and animated
  explainers are fine and are visibly diagrams, not app screens.
- If a shot is a diagram or a staged step, it carries an on-screen label for the whole
  shot ("diagram", "illustration, not the app").
- Never state a Zcash fact you have not verified against a primary source (zodl.com,
  support.zodl.com, zcash.github.io, zips.z.cash, z.cash, the Zodl GitHub repos). Record
  each fact with its URL in `docs/FACTS.md` before it goes into a script.
- No real recovery phrase, private key or spending key ever appears on screen, in a file
  or in a commit. Blur or crop the phrase screen in footage. A phrase on screen is a
  hard fail even if it is a throwaway wallet, because viewers copy what they see.
- No price, investment or financial advice. ZEC price never appears.
- AI disclosure: the README and every video description carry one line: "Scripts,
  narration and editing were produced with AI assistance (Kiro). Narration is a
  synthesised voice. App footage is real and recorded by the author."

## Voice (every outward word: narration, captions, site copy, README, tweets)

Write it clean from the first token. Do not emit these:

- No em dashes. Use a comma, a period, parentheses or a rewrite.
- No comma before "and" or "or". No Oxford comma.
<!-- voice-gate:off -->
- No AI tells: "it's worth noting", "in conclusion", "delve", "robust", "seamless",
  "leverage", "utilize", "furthermore", "moreover", "firstly", "unlock", "empower",
  forced three-item lists, throat-clearing, hedging.
<!-- voice-gate:on -->
- Short direct sentences. Plain words a 14 year old understands. Second person ("you").
- Define every term the first time (shielded, transparent, recovery phrase, memo/note).
- Never refer to "the operator", "this environment", "I was asked". Write as the author.

Gate: `node tools/voice-gate.mjs <files>` must exit 0. It runs inside `./verify.sh`.

## Licensing

- Code (site, scripts): `LICENSE` (LicenseRef-zkasuran-SAND-1.0). Keep it.
- Videos, narration, scripts: **CC BY-ND 4.0**, stated in each video description and in
  `LICENSE-MEDIA.md`. Reposting with credit is welcome (we want Zcash accounts to share
  it), edits are not.
- Every third-party input (music, fonts, icons, logos, screenshots that are not ours)
  gets a row in `DATA-SOURCES.md` with the exact granting sentence quoted. No quotable
  grant, it does not ship. "Free" and "no copyright" are not licences.
- Logos: the Zcash and Zodl marks appear only as they appear inside the real app
  footage or as plain text names. Do not redraw brand logos.

## Repo hygiene

- Repo stays **private** until the submit stage, then flips public (human or lead does it).
- `submit/`, `*.mp4`, `upload-*/`, `.env*`, `footage/raw/` are gitignored. Never commit
  raw footage (it may contain balances or addresses). Commit only cropped, checked clips
  under `footage/clean/` if size allows, else keep them out and document.
- Pin every dependency exactly. Commit lockfiles. `npm audit` at 0.
