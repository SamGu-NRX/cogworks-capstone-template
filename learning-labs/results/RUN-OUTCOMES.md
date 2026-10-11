# Run outcomes (M2)

Observed on the commit that introduced the runner, from the repository
root. Everything below the "commands" heading is the transcript the
commands produced, byte for byte as observed.

## The commands

    python learning-labs/run.py --all
    python learning-labs/run.py --lab audio
    python learning-labs/run.py --lab vector
    python learning-labs/run.py --lab grid

All five invocations were run and observed (plus
`cd learning-labs && python run.py --all`, which produces identical
output below its header -- paths resolve from the runner's own location).
Each exits 0 when every lesson is intact, nonzero otherwise. The `--lab`
runs each produced the same BEFORE/AFTER/verdict structure for their one
lab; `--lab vector`'s full transcript is appended at the bottom as a
sample.

## Observed transcript: python learning-labs/run.py --all

Exit code: 0.

```text
learning-labs: practice labs for testing a capstone interface
========================================================================

audio
------------------------------------------------------------------------
  question: The loose question -- which song? -- already has the right answer. Which boundary is off by one, why does a strict test see it when best_id does not, and what does that protect when your real submission returns shapes to a benchmark?

  BEFORE -- broken.py (the version you must repair)
    [pass] check_best_id
           still passes -- the trap, as documented
    [FAIL] check_exact_alignment
           expected best score 1.0 -- all 40 clip samples aligned at offset 37 -- but got 0.975: right song, right offset, short score. Count the samples your window compares.
           fails as documented

  AFTER -- reference.py (a working version, for comparison)
    [pass] check_best_id
    [pass] check_exact_alignment

  verdict: lesson intact -- broken.py fails exactly as
  documented and reference.py passes every check

grid
------------------------------------------------------------------------
  question: The first call is perfect and the second is impossible. Where does state hide between calls, and why does the capstone's Submission.__init__ say to build the database fresh every run?

  BEFORE -- broken.py (the version you must repair)
    [FAIL] check_input_untouched
           label_region must return a new grid, not the caller's object
           fails as documented
    [pass] check_first_call_exact
           still passes -- the trap, as documented
    [FAIL] check_two_calls_exact
           second call (GRID_TWO): row 1 differs -- expected [0, 7, 7, 0, 0, 0, 0, 0], got [0, 3, 3, 0, 0, 0, 0, 0]
           fails as documented

  AFTER -- reference.py (a working version, for comparison)
    [pass] check_input_untouched
    [pass] check_first_call_exact
    [pass] check_two_calls_exact

  verdict: lesson intact -- broken.py fails exactly as
  documented and reference.py passes every check

vector
------------------------------------------------------------------------
  question: Your caller's vectors changed while you were ranking. Who owns the normalization, what did the snapshot see that a score-only test missed, and which line repairs it?

  BEFORE -- broken.py (the version you must repair)
    [pass] check_ranking_exact
           still passes -- the trap, as documented
    [pass] check_ids_intact
           still passes -- the trap, as documented
    [FAIL] check_input_untouched
           the caller's dict changed during the call: vectors['img-01'] started as [2.0, 0.0, 4.0]... and ended as [0.354, 0.0, 0.707]... -- unit-length values instead of the caller's raw ones. Who owns the normalization?
           fails as documented

  AFTER -- reference.py (a working version, for comparison)
    [pass] check_ranking_exact
    [pass] check_ids_intact
    [pass] check_input_untouched

  verdict: lesson intact -- broken.py fails exactly as
  documented and reference.py passes every check

========================================================================
  audio: intact
  grid: intact
  vector: intact
every lesson intact (exit 0)
```

## Observed transcript: python learning-labs/run.py --lab vector

Exit code: 0.

```text
learning-labs: practice labs for testing a capstone interface
========================================================================

vector
------------------------------------------------------------------------
  question: Your caller's vectors changed while you were ranking. Who owns the normalization, what did the snapshot see that a score-only test missed, and which line repairs it?

  BEFORE -- broken.py (the version you must repair)
    [pass] check_ranking_exact
           still passes -- the trap, as documented
    [pass] check_ids_intact
           still passes -- the trap, as documented
    [FAIL] check_input_untouched
           the caller's dict changed during the call: vectors['img-01'] started as [2.0, 0.0, 4.0]... and ended as [0.354, 0.0, 0.707]... -- unit-length values instead of the caller's raw ones. Who owns the normalization?
           fails as documented

  AFTER -- reference.py (a working version, for comparison)
    [pass] check_ranking_exact
    [pass] check_ids_intact
    [pass] check_input_untouched

  verdict: lesson intact -- broken.py fails exactly as
  documented and reference.py passes every check

========================================================================
  vector: intact
every lesson intact (exit 0)
```

## How to read a BEFORE block

`[FAIL]` lines are the strict checks `broken.py` is supposed to fail --
each failure message names what was owed and what came back instead.
`[pass] still passes -- the trap, as documented` lines are the loose
checks `broken.py` survives, which is exactly why the strict checks exist.
A verdict of "lesson intact" means broken.py failed and passed exactly as
its lab's LESSON manifest says; if you repair `broken.py` and the verdict
does not flip, the runner tells you which line drifted.
