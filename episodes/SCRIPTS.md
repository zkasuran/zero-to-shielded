# Zero to Shielded: series scripts (locked 2026-10-04)

The words here are final. Scene builders copy narration cues verbatim into the project files
(`episodes/E<n>-<slug>/zts-e<n>.json`, one string per cue, in order). Every fact carries its
`docs/FACTS.md` ID. On-screen strings are verbatim too. Voice rules apply to every word:
no em dashes, no comma before "and" or "or", plain words, "you".

## Series rules (all episodes)

- **Cast** (from `site/js/cast.js`): **Maya** is the learner (the viewer's stand-in, she pays),
  **Sam** is her friend (he gets paid), **the Watcher** is "anyone looking at the public
  blockchain" (a curious lens-eyed figure on a tower of blocks).
- **Look:** palette `shield`: deep ink field (#0B0F1A to #1E2642 radial), Zcash gold
  #F4B728, cream text #F5F1E6, transparent = cool blue #7AA2FF, shielded = gold. Inter.
- **Honesty:** wallet steps are **step diagrams**, never an app screen. Each carries the
  label `Diagram, not the app` for the whole shot. Button names appear exactly as in
  FACTS.md in gold chips. Illustrations carry `Illustration`. Site recordings carry
  the URL bar `zero-to-shielded.vercel.app` and show the real site.
- **Phrase rule:** no word of any recovery phrase ever appears, real or fake. Phrase slots
  are numbered blurred bars only.
- **Opening card** (every episode, same template, ~4 s): big episode number, kicker
  `ZERO TO SHIELDED · EPISODE n`, title, small line `Zodl was called Zashi in older guides`.
- **End card** (every episode): next step + `zero-to-shielded.vercel.app`.
- **Footage slots:** every wallet-step scene names the clip from `footage/SHOT-LIST.md`
  that replaces its diagram once real footage exists in `footage/clean/`.
- TTS pronunciations (engine substitution, captions keep the written form): Zodl
  /zˈɑdᵊl/, ZEC /zˈɛk/, `zero-to-shielded.vercel.app` "zero to shielded dot vercel dot app",
  `support.zodl.com` "support dot zodl dot com", `0.0001 ZEC` "zero point zero zero zero one ZEC".

---

## E1 · Wallet setup: install Zodl and back up your phrase

Target 1:45. Outcome: a wallet with a recovery phrase backed up on paper. Checklist: Wallet setup.

| # | name | scene | visual | footage slot |
|---|---|---|---|---|
| 1 | e1-open | opening card | number 1, title "Install Zodl and back up your phrase" | |
| 2 | e1-wallet | illustration | Maya with a phone (blank glowing screen, shield glyph). A gold key slides into the phone. Chips `Email` `Phone number` `Account` drop in and get struck through. Label `Illustration` | |
| 3 | e1-install | step diagram | the word `Zashi` morphs letter by letter into `Zodl` (old name, new name). Then four text chips: `App Store` `Play Store` `F-Droid` `GitHub` (text only, no logos) | A |
| 4 | e1-create | step diagram | flow: `Open Zodl` → gold chip `Create New Wallet` (tap ripple) → a home diagram: four chips `Receive` `Send` `Pay` `Swap`. Small note `On iPhone: Create new wallet` | B, D |
| 5 | e1-phrase | illustration | a paper card with 24 numbered blurred slots (no words). Maya's phone drops and shatters into particles; the paper glows and a new phone assembles from the same particles (the words bring the wallet back) | |
| 6 | e1-backup | step diagram (climax) | path chips `Advanced Settings` → `Zodl Recovery Phrase`; then a pen writes 24 blurred lines on paper. Then the safety card, three rules appear one by one with icons: `Keep it on paper` `Never type it into a website` `Nobody legitimate will ever ask for it` | C (phrase blurred) |
| 7 | e1-later | step diagram | a coin lands, banner chip `Wallet Backup Required`, then chips in a row lighting one by one: `Start` → `Next` → `Reveal security details` → `I've saved it` | C |
| 8 | e1-site | site recording | real site home `#checklist` at zero-to-shielded.vercel.app, cursor ticks `Wallet setup`, camera zooms to it | |
| 9 | e1-end | end card | `Next: Episode 2 · Getting ZEC` + URL | |

Narration (cue per line):

1. e1-open
   - By the end of this video, you will have a private Zcash wallet on your phone. Your recovery phrase will be safe on paper. (F10, F21)
2. e1-wallet
   - First, what is a wallet? It is an app that holds your keys. Your keys let you spend your ZEC, the coin of Zcash.
   - You do not need an email address or a phone number. Only you control this wallet. (F10)
3. e1-install
   - We will use Zodl. Zodl is a Zcash wallet for your phone. Older guides call it Zashi. (F01)
   - Get Zodl from the App Store or the Play Store. On Android you can also use F-Droid or GitHub. (F04)
4. e1-create
   - Open Zodl and tap Create New Wallet. (F18)
   - That is it. Your home screen has four buttons: Receive, Send, Pay and Swap. (F19)
5. e1-phrase
   - Now the most important step. Your wallet has a recovery phrase. It is 24 words in a set order. (F21)
   - If you lose your phone, those words bring your wallet back on a new one.
6. e1-backup
   - Back it up right now. Open Advanced Settings, then tap Zodl Recovery Phrase. (F24)
   - Write the 24 words on paper, in order. Check every word twice. (F25)
   - Three rules. Keep it on paper. Never type it into a website. Nobody legitimate will ever ask for it, not even Zodl. (F25, F17)
7. e1-later
   - When your first ZEC arrives, Zodl shows Wallet Backup Required. (F22)
   - Tap Start, then Next, then Reveal security details. Check the words against your paper, then tap I've saved it. (F23)
8. e1-site
   - Your wallet is set up. Tick Wallet setup on the site to track your progress.
9. e1-end
   - Next, episode 2: getting your first ZEC. Every step is at zero-to-shielded.vercel.app.

## E2 · Getting ZEC: swap in the app or buy on an exchange

Target 1:45. Outcome: ZEC on its way to the wallet. Checklist: Getting ZEC.

| # | name | scene | visual | footage slot |
|---|---|---|---|---|
| 1 | e2-open | opening card | number 2, title "Swap in the app or buy on an exchange" | |
| 2 | e2-routes | illustration | Maya at a fork: path left `1 · Swap in Zodl`, path right `2 · Buy on an exchange`, both ending at her wallet | |
| 3 | e2-swap | step diagram | gold chip `Swap` on a home diagram; coins labelled `Other crypto` flow through a node `NEAR Intents` and turn into a gold shield `Shielded ZEC`. Then the definition card: `Shielded: the amount, the sender and the receiver are encrypted on the blockchain` | F |
| 4 | e2-exchange | illustration | an exchange building (generic, unbranded) sends a blue coin along a glass pipe marked `Transparent` to Maya's wallet. Definition card: `Transparent: public on the blockchain, like Bitcoin. Addresses start with t`. Then a gold chip `Zodl will offer to shield it` | |
| 5 | e2-receive | step diagram | gold chip `Receive`; two address cards: `Zcash Shielded Address` `u1…` (gold, badge `Private`) and `Zcash Transparent Address` `t1…` (blue, badge `Not Private`). Addresses shown as `u1` + blurred tail, never a full address. A rotating arrow on the u1 card: `New each time, same wallet` | E |
| 6 | e2-arrive | illustration | blocks stack 1 to 10 with a ring timer `about 12.5 minutes`; a coin travels into the wallet. Then banner chip `Wallet Backup Required` and a check mark `Done in episode 1` | G |
| 7 | e2-site | site recording | real site `#checklist`, cursor ticks `Getting ZEC` | |
| 8 | e2-end | end card | `Next: Episode 3 · Shielding and unshielding` | |

Narration:

1. e2-open
   - By the end of this video, ZEC will be on its way to your wallet. There are two ways to get it.
2. e2-routes
   - Route one: swap crypto you already have, right inside Zodl. Route two: buy ZEC on an exchange and send it to your wallet.
3. e2-swap
   - Route one. On the home screen, tap Swap. You can swap other crypto into shielded ZEC right inside Zodl. (F05, F19)
   - Shielded means the amount, the sender and the receiver are encrypted on the blockchain.
   - The swap uses NEAR Intents, not a centralized exchange. (F05)
4. e2-exchange
   - Route two. Buy ZEC on an exchange, then withdraw it to your wallet.
   - Most exchanges only send ZEC to a transparent address. Transparent means public on the blockchain, like Bitcoin. (F37, F30)
   - That is fine. Zodl will offer to shield it when it arrives. (F37, F07)
5. e2-receive
   - To find your address, tap Receive. Your Zcash Shielded Address starts with u1. Zodl shows a new one each time. They all lead to the same wallet. (F27, F28)
   - Below it is your Zcash Transparent Address. It starts with t1. If an exchange will not accept your u1 address, give it the t1 address. (F30, F37)
6. e2-arrive
   - Now wait a little. New ZEC needs 10 confirmations, about 12 and a half minutes, before you can spend it. (F33)
   - When it lands, Zodl shows Wallet Backup Required. You already wrote your words down. Follow the steps from episode 1. (F22, F23)
7. e2-site
   - Tick Getting ZEC on the site.
8. e2-end
   - Next, episode 3: shielding, so your ZEC goes private. See you at zero-to-shielded.vercel.app.

## E3 · Shielding and unshielding

Target 1:55. Outcome: a shielded balance; knows when and how to unshield. Checklist: Shielding, Unshielding.

| # | name | scene | visual | footage slot |
|---|---|---|---|---|
| 1 | e3-open | opening card | number 3, title "Shielding and unshielding" | |
| 2 | e3-sees | diagram (the big idea) | The Watcher on a tower of blocks. Left: Maya sends Sam a **postcard** (blue, transparent): the Watcher's lens reads `From Maya` `To Sam` `0.5 ZEC`. Right: Maya sends a **sealed envelope** (gold, shielded): the Watcher's lens shows only scrambling glyphs that never resolve; Sam opens it and the text decrypts for him alone. Label `Diagram` | |
| 3 | e3-shield | step diagram (climax) | definition `Shielding: moving your own ZEC from transparent to shielded`. Banner chip `Unshielded Balance` → gold chip `Shield` (tap) → sheet chip `Shield` again → big `Shielded!`. A blue coin passes through a gold shield and comes out gold | H |
| 4 | e3-ironwood | illustration | a calm card: `Ironwood: the newest shielded pool`. A gold coin settles into a pool labelled `Ironwood`. Second line `If Zodl asks you to migrate, that is a normal upgrade` | L |
| 5 | e3-unshield | diagram | the reverse: gold coin leaves the shield and turns blue on its way to an address card `t1…` or `tex1…`. Badges appear `Amount: public` `Address: public` `Note: not possible`. Small chip `tex1: Zodl does the two steps for you` | K |
| 6 | e3-checker | site recording | real `/tools/address/` `#checker` with the three example rows (u1 Shielded, t1 Transparent, tex1 Transparent); cursor points at each verdict; camera follows. Banner text on the page: `Nothing you paste leaves your browser` | |
| 7 | e3-end | end card | ticks `Shielding` `Unshielding`; `Next: Episode 4 · Sending and receiving` | |

Narration:

1. e3-open
   - By the end of this video, your ZEC will be shielded. You will also know when to unshield and what it shows.
2. e3-sees
   - First, what does the blockchain see? The blockchain is a public record of payments. Anyone can look at it.
   - A transparent payment is like a postcard. Anyone can read who sent it, who got it and how much. (F51, F30)
   - A shielded payment is like a sealed letter. The amount, the sender and the receiver are encrypted. Only the people in the payment can read it. (F51, F08)
3. e3-shield
   - Shielding means moving your own ZEC from transparent to shielded.
   - When ZEC lands at your transparent address, Zodl shows Unshielded Balance. Tap Shield. (F31, F07)
   - If a sheet opens, tap Shield again. When Zodl shows Shielded!, you are done. (F31)
4. e3-ironwood
   - Your shielded ZEC goes into Ironwood, the newest shielded pool. You do not have to do anything. (F26, F32)
   - If Zodl asks you to migrate to Ironwood, that is a normal upgrade, your ZEC stays shielded. (F13, F16)
5. e3-unshield
   - Unshielding is the opposite. You send ZEC from your shielded balance to a transparent address. (F42)
   - You only need it when you must pay an address that starts with t1 or tex1. Some exchanges use tex1 addresses for deposits. (F42, F39)
   - When you unshield, the amount and that address are public. You cannot add a note. For a tex1 address, Zodl does the two steps for you. (F43, F41)
6. e3-checker
   - Not sure what an address is? Paste it into the address checker on the site.
   - Your Zodl u1 address is shielded. A t1 or tex1 address is transparent. Nothing you paste leaves your browser. (F27, F28, F46, F39)
7. e3-end
   - Tick Shielding and Unshielding. Next, episode 4: your first shielded payment.

## E4 · Sending and receiving: your first shielded transaction

Target 2:00, the climax. Outcome: sent and received a shielded payment with a note. Checklist: Sending, Receiving.

| # | name | scene | visual | footage slot |
|---|---|---|---|---|
| 1 | e4-open | opening card | number 4, title "Your first shielded transaction" | |
| 2 | e4-receive | step diagram | Sam: gold chip `Receive` → card `Zcash Shielded Address` `u1…` (blurred tail) with two chips `Copy` and `QR Code`. The address flies as a gold ribbon from Sam to Maya | E |
| 3 | e4-send | step diagram | Maya: form diagram with labelled fields as chips in order: `Send to` (address pastes in, blurred tail), `Amount` (`0.05 ZEC` types in), `Message` (note types in: `Thanks for lunch!`), then gold chip `Review`. Definition card `Note: a private message that travels with a shielded payment` | I |
| 4 | e4-confirm | step diagram (climax) | a checklist diagram titled `Confirmation` with rows `Total Amount` `Send to` `Amount` `Fee` `Message`, each gets a check; card `ZIP 317 · smallest fee 0.0001 ZEC`; gold chip `Send` (tap) → `Sent!` with a gold burst; a sealed gold envelope launches | I |
| 5 | e4-arrive | illustration | the envelope arrives at Sam; it opens and the note decrypts `Thanks for lunch!` for Sam; then Sam sends a smaller envelope back to Maya | J |
| 6 | e4-chain | diagram | the Watcher's lens over the block: four rows `Sender` `Receiver` `Amount` `Note`, each a scramble of glyphs that never resolves; label `What the blockchain sees` | |
| 7 | e4-done | celebration | Maya and Sam cheer; gold shield burst; huge `You're shielded.` | |
| 8 | e4-site | site recording | real site `#checklist`, cursor ticks `Sending` then `Receiving`; the `You're shielded` state appears | |
| 9 | e4-end | end card | `Next: Episode 5 · Stay private` | |

Narration:

1. e4-open
   - By the end of this video, you will have sent and received your first shielded payment, with a private note.
2. e4-receive
   - Every payment has two sides. Let's start with receiving.
   - To get paid, tap Receive. Copy your Zcash Shielded Address. It starts with u1. (F27, F28, F30)
   - Send it to the person paying you. They can also scan it if you tap QR Code. (F30)
3. e4-send
   - Now sending. Tap Send. Paste the address into Send to, then type the amount. (F35)
   - In Message, you can add a note. A note is a private message that travels with the payment. Only you and the person you pay can read it. (F35, F08)
   - Then tap Review. (F35)
4. e4-confirm
   - Before anything is sent, Zodl shows the Confirmation screen. Check the address and the fee. (F35)
   - Zcash fees follow a public rule called ZIP 317. The smallest fee is 0.0001 ZEC. (F34)
   - Tap Send. When Zodl shows Sent!, your first shielded payment is on its way. (F35)
5. e4-arrive
   - On your friend's phone, the payment arrives with your note. Only the two of you can read it. (F08)
   - Ask them to send a little back to your u1 address. Now you have received a shielded payment too.
6. e4-chain
   - And what does the blockchain show? Only scrambled data. Not who paid. Not who got paid. Not how much. Not the note. (F51, F08)
7. e4-done
   - You did it. You're shielded.
8. e4-site
   - Tick Sending and Receiving on the site to finish your checklist.
9. e4-end
   - Episode 5 shows five habits that keep it private. Find it at zero-to-shielded.vercel.app.

## E5 · Stay private: five habits

Target 1:15. Outcome: knows the habits.

| # | name | scene | visual |
|---|---|---|---|
| 1 | e5-open | opening card | number 5, title "Five habits" |
| 2 | e5-habits | illustration, one scene with five beats | a vertical stack of five habit cards, each flips in with an icon as its cue plays: `1 Keep your ZEC shielded` (gold shield), `2 Avoid matching amounts` (two equal coins split apart), `3 Turn on Tor` (chips `Advanced Settings` → `Tor Protection` → `Enable` → `Save changes`), `4 Guard your phrase` (paper + lock), `5 Check the address` (magnifier over `u1…`) |
| 3 | e5-guard | site recording | real `/learn/phrase-guard/` page, camera glides over it; or `/tools/address/` if the guard page has no capture hook |
| 4 | e5-end | end card | `support.zodl.com` and `zero-to-shielded.vercel.app`; line `Zodl will never ask for your recovery phrase` |

Narration:

1. e5-open
   - By the end of this video, you will know five habits that keep your payments private.
2. e5-habits
   - One. Keep your ZEC shielded. If ZEC lands at your t1 address, shield it. (F50, F31)
   - Two. Do not shield an amount and then send the same amount to a transparent address soon after. That pattern is easy to spot. (F50, F43)
   - Three. Turn on Tor Protection. It sends your connection through the Tor network for extra privacy. Open Advanced Settings, tap Tor Protection, choose Enable, then tap Save changes. (F47)
   - Four. Guard your recovery phrase. Keep it on paper. Anyone who asks for it is trying to scam you. (F25)
   - Five. Check the address before you send. A t1 address is public. If you are not sure, use the address checker on the site. (F30)
3. e5-guard
   - Test yourself with Phrase Guard on the site. Six quick questions, safe or scam.
4. e5-end
   - Need help? Go to support.zodl.com. Zodl will never ask for your recovery phrase. That is the whole path, zero to shielded. (F17)

## E0 · Zero to Shielded in 5 videos (trailer, build last)

Target 0:30. Fast cuts reusing E1 to E4 scenes (opening shield, phrase rules, Shield tap, envelope vs postcard, You're shielded).

1. e0-hook: Your first private Zcash payment starts here.
2. e0-path: Five short videos. Set up Zodl. Get your first ZEC. Shield it. Send a private note.
3. e0-why: A shielded payment hides who paid, who got paid and how much. (F51)
4. e0-end: Start with episode 1 at zero-to-shielded.vercel.app.

## Chapters (YouTube, bounty words on purpose)

- E1: 0:00 What you will do · Wallet setup: install Zodl (e1-install) · Wallet setup: create your wallet (e1-create) · Wallet setup: back up your recovery phrase (e1-phrase) · Next step (e1-site)
- E2: 0:00 Two ways · Getting ZEC: swap in Zodl (e2-swap) · Getting ZEC: buy on an exchange (e2-exchange) · Receiving: your addresses (e2-receive) · Getting ZEC: it arrives (e2-arrive)
- E3: 0:00 What the blockchain sees · Shielding: tap Shield (e3-shield) · Ironwood (e3-ironwood) · Unshielding: when you need it (e3-unshield) · Check an address (e3-checker)
- E4: 0:00 Receiving: share your address (from 0) · Sending: your first shielded transaction (e4-send) · Confirm and send (e4-confirm) · Receiving: the note arrives (e4-arrive) · You're shielded (e4-done)
- E5: 0:00 Five habits · Keep it shielded (e5-habits) · Test yourself (e5-guard)

Chapter rule: at least 3, first at 0:00, each at least 10 s. Merge a chapter into the previous
one when its segment is shorter than 10 s.
