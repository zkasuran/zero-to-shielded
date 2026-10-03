# Design: Zero to Shielded

## Layout

```
AGENTS.md                      entry point for any agent
.kiro/steering/                rules (always loaded)
.kiro/specs/zero-to-shielded/  this spec
docs/FACTS.md                  every claim + source URL (create first)
episodes/E<n>-<slug>/
  zts-e<n>.json                kit project file (source of truth for words + scenes)
  BRIEF.md                     scene table, cue list, strings, gates with measured results
  DEMO-E<n>.mp4                rendered (gitignored)
  upload-zts-e<n>/             upload package (gitignored)
footage/
  SHOT-LIST.md                 what the human records on the phone
  raw/                         phone recordings (gitignored, may hold personal data)
  clean/                       cropped, phrase-blurred clips used by scenes
site/                          static companion site (GitHub Pages)
tools/video-kit/               renderer (tests must stay green)
tools/voice-gate.mjs           outward-words gate
verify.sh                      one release gate
```

## Episode scripts (spine; write final words in each project file)

**E1 Wallet setup** (target 1:45)
1. Card: "By the end you'll have a private Zcash wallet, backed up." (5s)
2. Diagram: what a wallet is (your keys on your phone, no account, no email). (15s)
3. Device: install Zodl from the store; note "older guides call it Zashi". (15s)
4. Device: create wallet. (15s)
5. Device: recovery phrase screen, phrase BLURRED; card overlay "paper, never a website,
   nobody will ask". (25s, climax)
6. Device: confirm backup, wallet home. (15s)
7. Web: site checklist ticks "Wallet setup", URL on screen. (10s)

**E2 Getting ZEC** (target 1:50)
1. Card outcome. 2. Diagram: two routes (swap in app or exchange withdrawal).
3. Device: Zodl Swap flow up to the quote (or the real swap if the human funded it).
4. Device: receive screen, transparent address for exchange withdrawals; explain why
   exchanges often use transparent. 5. Device: funds arrive. 6. Web: checklist.

**E3 Shielding and unshielding** (target 1:55)
1. Card outcome. 2. Diagram "What the blockchain sees": transparent vs shielded.
3. Device: Zodl detects transparent balance, one-tap Shield (climax). 4. Device: shielded balance.
5. Diagram + device: unshielding = sending to a `t1` / `tex1` address, when you need it
   (exchange deposit), what becomes visible. 6. One line on Ironwood migration prompt.
7. Web: address checker telling `u1` vs `t1` apart, URL on screen.

**E4 Sending and receiving: your first shielded transaction** (target 2:00)
1. Card outcome. 2. Device: receive, share address or QR. 3. Device: send, paste or scan,
   amount, private note. 4. Device: review, fee shown by the app, confirm (climax).
5. Device: recipient sees payment + note. 6. Diagram: what the chain shows (nothing
   readable). 7. Card: "You're shielded." 8. Web: completed checklist state.

**E5 Stay private: five habits** (target 1:15): keep funds shielded; do not move
distinctive amounts in and out right away; use Tor setting in Zodl if offered (verify);
never share the phrase; check addresses with the site's checker. Ends with support links.

**E0 Trailer** (0:30): fast cut of the climaxes from E1-E4 + site URL. Build last.

## Fallback when footage is missing for a step

Order of preference: (1) real footage; (2) official screenshots from support.zodl.com ONLY
if their terms permit reuse and the clause is quoted in DATA-SOURCES.md; (3) a labelled
diagram of the step with the button names as text ("In Zodl, tap Receive"). Never a
redrawn app screen.

## Site information architecture

Start (path, what you need) | Episodes (E0-E5) | Tools (address checker, what the chain
sees) | Help (glossary, mistakes, official support). Pages: `/`, `/start/`, `/episodes/e1/`
... `/episodes/e5/`, `/tools/address/`, `/tools/chain/`, `/help/`.

## Address checker design

Pure module `site/js/address.js` exporting `classify(str) -> {kind, shielded, valid, reason}`.
Normalise (trim, strip whitespace, lowercase only for Bech32 kinds). Size cap 512 chars.
Base58Check (double SHA-256 via WebCrypto or a small audited implementation) for `t1`/`t3`,
Bech32 for `zs1`, Bech32m for `u1`/`tex1` (unified addresses are F4Jumbled; checksum
validation does not require un-jumbling, decoding receivers does; checksum + HRP is enough
for this tool, state that). Tests: `site/test/address.test.mjs` with vectors from the ZIPs.
