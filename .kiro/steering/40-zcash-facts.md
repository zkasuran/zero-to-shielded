# Zcash facts (as of October 2026)

Verified by the lead on 2026-10-03 against the sources named. Re-read the source before
quoting any number. Anything not on this list goes into `docs/FACTS.md` with its URL
before it goes into a script.

## Verified

| Fact | Source |
|---|---|
| The Zashi wallet is now called **Zodl**, built by Zcash Open Development Lab (ZODL), the team that left Electric Coin Company in Feb 2026. The store listings keep the old IDs. | https://zodl.com/ ("Zashi is now Zodl."), https://z.cash/ecosystem/zodl-wallet/ |
| Downloads: App Store, Play Store, F-Droid, GitHub releases (`zodl-inc/zashi-android`). | https://zodl.com/ download popup |
| Zodl Swaps: swap to and from shielded ZEC inside the app, powered by NEAR Intents, no centralised exchange. | https://zodl.com/ "Swaps" |
| Zodl CrossPay: send shielded ZEC, recipient receives another asset (e.g. BTC or a stablecoin). | https://zodl.com/ "CrossPay" |
| 1-Click Shielding: Zodl can receive transparent ZEC (e.g. from exchanges); when it detects a transparent balance it prompts you to shield it with one tap. | https://zodl.com/ "1-Click Shielding" |
| Shielded Notes: encrypted notes travel with a payment, visible only to sender and recipient; a zero-amount send carries a note on its own. | https://zodl.com/ "Shielded Notes" |
| Zodl says it collects no wallet activity and uses no in-app analytics; only anonymised crash reports. | https://zodl.com/ "No Tracking" |
| Keystone hardware wallet supports shielded ZEC with Zodl. | https://zodl.com/ "Cold Storage" |
| **Ironwood** (network upgrade NU6.3) activated **July 28 2026** with a new shielded pool. Orchard funds do not expire; no migration deadline. Moving Orchard to Ironwood goes through a turnstile and the cross-pool amount is public. | https://keyst.one/zcash/updates/keystone-ironwood-migration-guide-2026-07 , https://zcash.github.io/ironwood/concepts.html |
| Zodl 3.9.0+ does automatic Ironwood migration on iOS and Android, offering "Migrate with Privacy" (recommended, split standard amounts over time) or "Migrate Immediately". Zodl recommends Tor during migration. | same Keystone guide; https://support.zodl.com/article/42-moving-your-funds-to-ironwood |
| Zodl support: https://support.zodl.com/ , Discord https://discord.gg/NcDnF2sPjY , X @zodl_app | https://zodl.com/ |

## Must verify before scripting (primary source, record in docs/FACTS.md)

- The exact current Zodl onboarding screens and button labels (from the footage, not memory).
- Whether a brand-new wallet created after Ironwood receives straight into Ironwood and
  what the default receive address looks like (`u1...`?). Read https://zcash.github.io/ironwood/
  and support.zodl.com.
- What Zodl shows as the transparent receive address and how "shield" is labelled.
- Current fee shown for a shielded send (ZIP 317 conventional fee). Show the number the
  app shows in the footage; do not quote a fee from memory.
- Exchange withdrawals: which major exchanges support withdrawing ZEC and whether any
  support shielded withdrawals. If unsure, say "most exchanges send to a transparent
  address and Zodl will offer to shield it", which is verified above. Do not name an
  exchange as supporting something you have not confirmed on its own help page.
- Unshielding: when a viewer needs it (e.g. depositing to an exchange that only accepts
  transparent or TEX addresses) and how Zodl handles a send to a `t1` or `tex1` address.
  ZIP 320 defines TEX addresses: https://zips.z.cash/zip-0320
- Unified address format and receivers: https://zips.z.cash/zip-0316

## Words we use (glossary, keep consistent across all episodes)

- **Shielded**: amount, sender and receiver are encrypted on the blockchain.
- **Transparent**: visible on the blockchain like Bitcoin. Addresses start with `t`.
- **Shielding**: moving your own ZEC from transparent to shielded.
- **Unshielding**: sending shielded ZEC to a transparent address.
- **Recovery phrase**: the list of words that restore your wallet (say the count the app
  shows in the footage; do not assume). Write on paper. Never type
  it into a website, never share it, nobody legitimate will ever ask for it.
- **Note** (memo): private message attached to a shielded payment.
- **Ironwood / Orchard**: names of shielded pools; Ironwood is the newest. Mention once,
  in episode 3, plainly: "If Zodl asks you to migrate to Ironwood, that is a normal
  upgrade, your ZEC stays shielded."
