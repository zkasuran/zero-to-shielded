# bug-fix-pr

A bounty or upstream fix, shown the way a reviewer reads it: the failing test, the diff,
the passing test. Built around the `diff` scene.

## The spine

1. `card` title. Names the bug.
2. `term` failing. The test that reproduces the bug, run for real, red.
3. `diff` the fix. The change itself, added lines on a green wash, removed on red.
4. `term` passing. The same test on the fix, green.
5. `card` close. What the fix changes, the PR link.

## Why this shape

Red before green is the whole argument. A static card of the after state proves nothing
about what moved, so the `diff` scene draws the change itself and the two terminal runs
bracket it with real exit codes.

For a bounty PR the content that matters is the PR body and the disclosure, not a social
thread. Most bug-fix PRs do not earn a video at all. Use this template only when a
program scores one.

## The diff scene, three ways to feed it

- `"repo": "/path", "rev": "HEAD~1..HEAD"`: runs `git diff` for real and keeps the raw
  output as a receipt. `file` narrows it to one path.
- `"before": "/a.py", "after": "/b.py"`: a unified diff of two files.
- `"patch": "/fix.patch"`: a patch already on disk.

`mode` is `unified` (one column) or `split` (before and after side by side). Split falls
back to unified on a portrait aspect because two columns do not fit. `hunk` keeps one `@@`
block when a whole file would overflow. The diff refuses if there is nothing added or
removed, so a stale range fails loudly.

## What to swap

- `palette`: a free one.
- The two `term` scenes point at your real test command in your real repo.
- The `diff` scene points at your real change.
- Every `TODO`.

The focus needle on a diff row matches the text of the line, so `"focus": "elapsed"` lands
the marker on the added line that mentions elapsed time.
