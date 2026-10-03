# Requirements: Zero to Shielded

## Introduction

A beginner with a phone and no crypto experience watches a short video series and uses a
companion site and ends with their first shielded Zcash transaction sent and received.
Entry for the ZECATHON Wildcard track (@zksnarks_), deadline Oct 4 2026.

## Requirement 1: Coverage of every named topic

**User story:** As the judge, I want each topic in the bounty covered explicitly, so that I
can confirm the entry is complete.

1. WHEN the series is published THEN it SHALL contain chapters titled with the words
   "Wallet setup", "Getting ZEC", "Shielding", "Unshielding", "Sending", "Receiving".
2. WHEN a viewer finishes episode 4 THEN they SHALL have sent and received a shielded
   transaction, shown end to end in real app footage.
3. The site checklist SHALL list the same six steps with the same words.

## Requirement 2: Current and correct

1. All wallet instructions SHALL use Zodl (formerly Zashi) and its current screens.
2. Every factual claim SHALL be listed in `docs/FACTS.md` with a primary-source URL.
3. Episode 3 SHALL mention Ironwood migration in one plain sentence.
4. The series SHALL say once that older guides call the app Zashi.

## Requirement 3: Beginner-first

1. Each episode SHALL open with the outcome and close with the next step + site URL.
2. Each term SHALL be defined on first use, matching the glossary in 40-zcash-facts.md.
3. Captions SHALL be burned in and exported as SRT.
4. Each episode SHALL be at most 140 seconds.
5. Safety SHALL be stated at the phrase step: write it on paper, never type it into a
   website, nobody legitimate asks for it.

## Requirement 4: Real, honest, licensed

1. No mocked wallet UI. Diagrams labelled as diagrams.
2. No recovery phrase, key or personal data visible in any frame.
3. Every third-party asset has a quoted grant in `DATA-SOURCES.md`.
4. AI disclosure line present in README and every description.

## Requirement 5: Web experience

1. Light and dark, category menu with submenus, product-first hero (see 30-web.md).
2. Episode pages with player, chapter seek, transcript, next button.
3. Progress checklist persisted locally, defensive parsing.
4. Address checker, client side, with checksum validation and tests from real ZIP vectors.
5. Strict CSP, zero console errors, both themes at 390 and 1360 wide.

## Requirement 6: Submission package

1. Each episode has an upload package: title (<=100), description (<=5000) with chapters,
   honesty paragraph, licence, AI line; thumbnail 3840x2160 < 2 MB; captions; chapters.
2. A thread draft: post 1 tags @zksnarks_ and states the outcome and the site URL, one
   reply per episode (each <= 280 chars, with the native video), last reply links repo.
3. `./verify.sh` prints ALL GREEN.
