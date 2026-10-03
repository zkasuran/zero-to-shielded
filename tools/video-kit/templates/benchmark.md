# benchmark

A claim with numbers. Built around the `chart` scene. Use it when the entry rests on a
measured result, a speedup, a cost cut, a vote count.

## The spine

1. `card` title. States the claim as a claim, and the baseline.
2. `chart` a column or bar of the headline number, before and after.
3. `chart` a line of how it holds up as load or size climbs.
4. `term` the run. The command that produced the numbers, so the chart traces to something
   a judge can rerun.
5. `card` close. What the numbers prove and what they do not.

## Why this shape

A chart is only honest if the numbers came from somewhere. The template reads inline rows
so it preflights out of the box, but the real version points the chart at a results file
and sets `source` to name it. Ending on the run is what stops the chart being a drawing.

## The chart scene

`chart` picks the kind:

- `bar`: horizontal bars, good for a short ranked list.
- `column`: vertical bars, good for a before and after.
- `line`: one or more series over an x axis. Takes `series` as `[{name, values}]` and
  `x_labels`.
- `progress`: labelled progress meters, good for percentages. `max` sets the full mark.
- `sparkline`: one small line per row, good for many series at a glance.

Data comes from, in order: inline `rows` (`[label, value]`) or inline `series`; a `file`
ending `.csv` with `x` and `y` column names; a `file` ending `.json` reached by a dotted
`path`, with `label_key` and `value_key` naming the fields. A row whose value is not a
number is skipped rather than crashing the draw.

`unit` suffixes every value (` ms`, `%`, `x`). `thresholds` colours a bar by a rule:
`good_above`, `bad_above`, `good_below`. `source` prints under the chart.

A focus needle on a bar or column chart matches a row label. On a line chart it matches an
`x_labels` entry.

## What to swap

- `palette`: a free one.
- The inline `rows` and `series` become `file` + `path` pointed at your real results, with
  `source` naming the file.
- The `term` run scene, pointed at your real bench command.
- Every `TODO`.
