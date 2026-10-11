# Practice labs

Three small labs where you practice the thing the capstone never explicitly
teaches: testing an interface. Week 1 is audio, week 2 is vision, week 3 is
language -- and every one of them scores your code by calling methods on an
object you hand it. When a number looks impossible, the bug is almost never
in the algorithm. It is in the contract: a return shape one field short, a
function that edits the data it was lent, state that quietly survives from
one run into the next. These labs are toy versions of exactly those bugs,
with the answers printed in full.

Everything here runs offline in a few seconds. No account, no network, no
limit.

## The labs

| Lab | Toy problem | What the strict test catches |
| --- | --- | --- |
| audio | align a 40-sample clip against two authored songs, exact samples | a window slice one sample short: right song, right offset, score 0.975 where 1.0 is owed |
| vector | rank four 8-dim descriptors by cosine against a query | normalization that rewrites the caller's dict mid-call -- every returned id and score is right, and your input is gone |
| grid | 4-connected flood fill on a 6x8 grid, returning a new grid | labels written into the caller's grid, and a visited set that survives the call -- the second fill is truncated by the first |

Each lab ships the same five parts: `fixtures.py` (the authored inputs and
the public expected results), `reference.py` (a working version),
`broken.py` (a broken version that says in its docstring exactly which
check it fails), `checks.py` (the strict checks -- one source of truth used
by both pytest and the runner), and a README that poses the question and
walks the repair.

## Running it

From the repository root:

```bash
python -m pytest -q learning-labs/tests     # the strict suite, 18 tests
python learning-labs/run.py --all           # the lesson runner
python learning-labs/run.py --lab audio     # one lab at a time
```

The runner prints, per lab: the experimental question, a BEFORE block
(every check run against `broken.py`, failures shown with readable diffs),
an AFTER block (the same checks against `reference.py`), and a verdict. It
exits 0 only when every lesson is intact -- meaning broken.py fails
exactly the checks its lab says it fails. Also works from inside the
directory: `cd learning-labs && python run.py --all`.

Exact observed outputs from each milestone live in
[results/](results/). Every module path, signature, constant, and command
is documented in [INTERFACE.md](INTERFACE.md).

## The repair loop

This is the whole exercise, and it takes about fifteen minutes per lab:

1. `python learning-labs/run.py --lab audio` and read the BEFORE block.
   Notice which checks pass and which fail. Some of the passes are the
   trap.
2. Open `labs/audio/broken.py`. Its docstring names the check it fails and
   why, but read the code first and see if you can find the line.
3. Repair it. Not by copying `reference.py` -- by understanding the
   boundary, the ownership, or the state that the strict check is
   standing guard over.
4. Run again. The verdict flips to intact when `broken.py` fails exactly
   as documented and nothing else. If you "repair" it by breaking a check
   that was passing, the runner tells you the lesson has drifted.
5. Compare with `reference.py`. Usually the fix is one line, and the
   interesting part is why that line was wrong.

`python -m pytest -q learning-labs/tests` passes at every step of this
loop -- it tests the reference, not your repair. Your repair is checked by
the runner. That split is deliberate, and it is the same split the
capstone has: your own suite green, the benchmark red.

## What this is not

These are toy lessons with public answers, authored for practice. The
official evaluation runs on hidden data with hidden labels and a limited
number of runs; nothing here predicts those numbers, and no score in this
directory transfers to it. Nothing here is graded, nothing records who you
are, and understanding is checked by you against the tests, not inferred
from your activity. This is not a package either: nothing to install
beyond pytest, nothing to configure, no plugin, no import of cogworks or
any benchmark code.
