# cli-tool

A command line tool, shown doing real work. Terminal-led. Use it when the product is a
binary or a script and the proof is what it prints.

## The spine

1. `card` title. The chore it removes.
2. `term` help. `--help` or a version line, so a viewer sees the surface.
3. `term` real run. The tool on real input, real output captured from the run.
4. `code` how. One short slice of the source, so it is not a black box.
5. `card` close. Install, link, what is rough.

## Why this shape

The real run is the climax. Everything on screen in a terminal scene is a viewport into
stdout that was captured by running the command, so the histogram or the report is the
program's own output. The `code` scene at the end answers "is this real" without turning
into a lecture.

## The term scene

- `cwd`: where the command runs.
- `cmd`: the command as a list of arguments.
- `prompt`: what shows after the `$`. Defaults to the joined `cmd`, but you often want a
  cleaner line than the real invocation, so set it.
- `from` and `to`: slice the captured output to the interesting window by substring.
- `max_lines`: the viewport height. `wrap` widens the column past the default for a table
  with long rows.

The command runs once per build and the raw stdout is kept in `artifacts/<id>/`. A focus
needle matches a captured line.

## What to swap

- `palette`: a free one.
- Every `term` scene, pointed at your real tool.
- The `code` scene, pointed at your real source.
- Every `TODO`.
