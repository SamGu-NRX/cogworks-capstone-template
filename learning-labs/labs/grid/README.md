# Lab: grid -- the first call is perfect and the second is impossible

A 6x8 grid of ints: 0 is background, other values are region ids. Flood
fill from a start cell, 4-connected (no diagonals), relabel the region,
return a **new** grid. Two authored grids, two calls:

- call 1: `label_region(GRID_ONE, (1, 1), 9)` -- a 4-cell block labeled 1
- call 2: `label_region(GRID_TWO, (3, 3), 7)` -- a 6-cell region labeled 3

Both expected outputs and both region sizes are public constants in
`fixtures.py`. The grids are rigged so the two target regions overlap in
*coordinates*: `(1, 1)`, `(1, 2)`, `(2, 1)`, `(2, 2)` are region cells in
both. Coordinates are not identity, and a second grid is not a second run
-- that is the whole trap.

## The question

The first call is perfect and the second is impossible. Where does state
hide between calls, and why does the capstone's `Submission.__init__` say
to build the database fresh every run?

Run the runner and read the BEFORE block carefully, because the shape of
the failure is the lesson. `check_input_untouched` fails immediately:
`broken.py` writes labels into the caller's grid and hands it back. But
`check_first_call_exact` **passes** -- given one fresh grid, the fill is
perfect. Only `check_two_calls_exact` fails, and its diff shows the
second grid half-filled: 3 of 6 cells relabeled, the corner left alone.

The state that survived is a module-level `_visited` set in `broken.py`,
holding the *coordinates* the first call touched. On the second call,
those coordinates are skipped before their neighbors are ever explored,
so the fill dies quietly at the boundary of last call's business. A
module-level mutable default is a database that persists across runs --
which is, verbatim, the most common source of an impossible score in the
capstone: your week 1 submission keeps enrolled songs between benchmark
runs, run 2 is scored against run 1's leftovers, and the number on the
leaderboard cannot be explained. `Submission.__init__` builds the
database fresh every run because *state is not free just because the
function that owns it is still loaded*.

## The repair

```bash
python learning-labs/run.py --lab grid
```

Two bugs, one lesson each, and both fixes are already in `reference.py`
as two lines of housekeeping: `visited` becomes a set built inside the
function (fresh per call), and the result is built as `[row[:] for row in
grid]` so the caller's rows are copied, never written. Make both changes
in `broken.py`, and grade yourself with the gate as you go:

```bash
python learning-labs/validate.py --lab grid
```

Repair the mutation first: the gate still exits 1, but
`check_input_untouched` joins the pass column while
`check_two_calls_exact` keeps failing -- partial progress is visible
after every change, never silently swallowed. Then repair the state, run
it again, and watch it exit 0: the second grid fills completely. The
second call was never wrong. It was just first in line behind the first
call's leftovers.
