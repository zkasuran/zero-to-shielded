# product-demo

The standard hackathon cut. Use it when you have a working product with a live URL and
a repo, and the job is to prove both are real in about two minutes.

## The spine

1. `card` title. Names what it does and the stake.
2. `card` problem. The pain in the user's words, before you show anything.
3. `web` live site. The deployed product, running, at the URL a judge can visit. This is
   the scene that proves the thing is reachable.
4. `code` source. The part that produces what you just saw, read from a real file.
5. `card` close. What it proves, what it does not, the links.

## Why this shape

The house rule wants a live URL scene and a source or build scene in every cut. A cut
that is all website never proves the code is real. A cut that is all terminal never
proves a judge can reach it. This template carries both by default, so you cannot ship
one that fails that gate.

Open on the problem, not the product. A viewer who does not feel the pain does not care
that you solved it.

## What to swap

- `palette`: pick a free one. `python3 preflight.py projects/*.json` prints the free list.
- The `web` scene `file` becomes `url`, pointed at your deployed site. Set `section` to a
  real element id and `items` to the attribute on the things you reveal one at a time. If
  your page has no `data-step` hooks, use a CSS selector: `"items": "css:.card"`.
- The `code` scene `file`, `from` and `to`, pointed at a real source file and the slice
  worth reading.
- Every `TODO` in the narration, the header, the cards and the `upload` block.

## Pacing

Around two minutes. The `web` scene holds longest because it carries the payoff. Keep the
opening cards tight.
