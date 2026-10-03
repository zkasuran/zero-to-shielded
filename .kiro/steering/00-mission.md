# Mission

## The bounty (verbatim from @zksnarks_ on X, Sep 29 2026)

> Kicking off ZECATHON's Wildcard track with a $5,000 USD bounty, paid in $ZEC, for the
> best onboarding video series or web experience.
> Wallet setup, getting ZEC, shielding & unshielding, sending & receiving.
> Take someone from zero to their first shielded transaction.
> Tweet your submission and tag @zksnarks_
> Deadline: Sunday, October 4.

There is no published rubric. Judge = the person behind @zksnarks_ and whoever they ask.
So we design to the four named topics plus the one outcome: **zero to first shielded tx**.

## How we win (the thesis)

1. **We ship BOTH.** "Video series OR web experience". Rivals pick one. We ship a series
   AND a site that hosts it with a step checklist and a real tool. One coherent entry,
   two ways to qualify.
2. **We are current, rivals are stale.** Since February 2026 the Zashi wallet is called
   **Zodl**. Since July 28 2026 the new **Ironwood** shielded pool is live. Most tutorials
   on the internet still say Zashi and Orchard. Every episode uses the current names and
   the current app. One line per episode says "if you see Zashi in old guides, that is
   Zodl's old name". This alone outdates most rival entries.
3. **Real app on screen.** The episodes show the real Zodl app, recorded on a phone
   (see `footage/SHOT-LIST.md`). Never a mocked wallet screen.
4. **Short, one job per episode.** Each episode ends with the viewer having done one
   thing. Under 2:20 each so it plays natively on X (free-account upload cap).
5. **Covers every named topic explicitly.** Wallet setup, getting ZEC, shielding,
   unshielding, sending, receiving. Each one has a chapter title using those exact words
   so a judge ticking boxes finds them.
6. **The submission tweet is a thread** with every episode uploaded natively (not only
   links), so the judge watches without leaving X.

## The series (target lengths)

| # | Title | Viewer has done this at the end | Target |
|---|---|---|---|
| 0 | Zero to Shielded in 5 videos | knows the path and that it takes ~15 min | 0:30 |
| 1 | Wallet setup: install Zodl and back up your phrase | a wallet with a backed-up recovery phrase | 1:30-2:00 |
| 2 | Getting ZEC: swap in the app or buy on an exchange | ZEC arriving in their wallet | 1:30-2:00 |
| 3 | Shielding and unshielding | a shielded balance; knows when and how to unshield | 1:30-2:00 |
| 4 | Sending and receiving: your first shielded transaction | sent and received a shielded tx with a private note | 1:30-2:00 |
| 5 | Stay private: five habits | knows the habits that keep it private | 1:00-1:30 |

Episode 4 is the climax. If time runs out, cut 0 and 5, never 1 to 4.

## Deliverables

- `episodes/E<n>-<slug>/`: project file, brief, rendered `DEMO-E<n>.mp4` (gitignored),
  upload package (gitignored), captions, chapters
- `site/`: the companion web experience (static, deployable to GitHub Pages)
- `README.md` built like a landing page (see 30-web.md)
- the submission thread text (built locally into `submit/`, never pushed)

## Deadline plan (all times IST, UTC+5:30)

The tweet gives no timezone. **Oct 4 18:00 IST (12:30 UTC) is our hard ship time**: it is
still Oct 4 everywhere from UTC-12 to UTC+14, so no reading of "Sunday October 4" can
call us late.

| By | Done |
|---|---|
| Oct 4 02:00 | scripts for E1-E4 locked, facts verified, palette claimed |
| Oct 4 08:00 | E1-E4 rendered and gated; footage merged where it exists |
| Oct 4 12:00 | site live on Pages, episodes embedded, README done |
| Oct 4 15:00 | E0 + E5, thread text, repo flipped public, every link 200 anonymous |
| Oct 4 18:00 | thread posted by the human |

## Out of scope

Desktop wallets, hardware wallets beyond one mention, mining, running a node, ZSAs,
price talk, any investment framing. No "buy ZEC because" anything.
