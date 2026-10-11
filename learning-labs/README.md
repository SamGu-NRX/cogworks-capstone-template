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

Each lab ships the same six parts: `fixtures.py` (the authored inputs and
the public expected results), `reference.py` (a working version),
`broken.py` (a broken version that says in its docstring exactly which
check it fails -- the one file you are invited to edit), `control.py`
(an immutable twin of the same defect, hash-pinned in `controls.json`:
the pristine copy the integrity tests watch, never touched by anyone),
`checks.py` (the strict checks -- one source of truth used by pytest,
the runner, and the validator), and a README that poses the question and
walks the repair.

## Running it

From the repository root:

```bash
python -m pytest -q learning-labs/tests     # integrity suite, 20 tests
python learning-labs/run.py --all           # the tour: watch the checks fail
python learning-labs/run.py --lab audio     # one lab at a time
python learning-labs/validate.py --all      # the gate: did YOUR repair land?
python learning-labs/validate.py --lab audio
```

The runner prints, per lab: the experimental question, a BEFORE block
(every check run against `broken.py`, failures shown with readable diffs),
the same checks against `reference.py` (for diffing after your repair
works), and the immutable `control.py` still failing exactly as
documented. Its verdict describes the fixed side of the lesson, so it
reads the same before you touch anything and after your repair lands.

`validate.py` is the command that grades you: it runs every strict check
against *your* `broken.py` and exits 0 only when all of them pass --
traps included. Also works from inside the directory: `cd learning-labs
&& python run.py --all` (and the `validate.py` equivalent).

Exact observed outputs from each milestone live in [results/](results/),
including a full fail-repair-pass-restore execution of the new workflow in
[results/REPAIR-OUTCOMES.md](results/REPAIR-OUTCOMES.md). Every module
path, signature, constant, and command is documented in
[INTERFACE.md](INTERFACE.md).

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
4. Prove it: `python learning-labs/validate.py --lab audio`. Exit 0 means
   every strict check passes on your `broken.py`, traps included -- you
   cannot repair by breaking a check that was passing, because the gate
   refuses to flip until all of them hold. Until then it prints the
   failing checks with their diffs, and partial progress counts: fix the
   grid lab's mutation first and the gate shows exactly one check still
   red.
5. Compare with `reference.py`. Usually the fix is one line, and the
   interesting part is why that line was wrong.

`python -m pytest -q learning-labs/tests` passes at every step of this
loop -- it tests the fixed side of each lesson (the pinned controls, the
reference), never your `broken.py`. Your repair is graded by
`validate.py`. That split is deliberate, and it is the same split the
capstone has: your own suite green, the benchmark red -- except here the
benchmark is yours to run, for free, as often as you like.

## What this is not

These are toy lessons with public answers, authored for practice. The
official evaluation runs on hidden data with hidden labels and a limited
number of runs; nothing here predicts those numbers, and no score in this
directory transfers to it. Nothing here is graded, nothing records who you
are, and understanding is checked by you against the tests, not inferred
from your activity. This is not a package either: nothing to install
beyond pytest, nothing to configure, no plugin, no import of cogworks or
any benchmark code.
