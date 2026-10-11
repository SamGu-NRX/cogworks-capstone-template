# Fresh-environment replay (M3)

Observed on the commit that introduced this file. The point of this
milestone is portability: a brand-new clone of the pushed branch, a
brand-new virtualenv containing nothing but pytest, and the two documented
commands. No dev-environment state, no installed packages beyond the
standard library plus pytest, no network access at run time.

## How the fresh environment was built

    rm -rf /tmp/labs-replay-venv /tmp/labs-replay-clone
    python -m venv /tmp/labs-replay-venv
    /tmp/labs-replay-venv/bin/python -m pip install --quiet pytest
    git clone --branch obv/products-l3-capstone-practice-labs-20261010 \
        https://github.com/SamGu-NRX/cogworks-capstone-template.git \
        /tmp/labs-replay-clone

Observed on the fresh environment before running anything:

- Python 3.13.14 (`/tmp/labs-replay-venv/bin/python --version`)
- pytest 9.1.1 (`/tmp/labs-replay-venv/bin/python -m pytest --version`)
  -- note: a DIFFERENT pytest than the development environment's 9.0.3,
  because the venv installed the current release. That drift is part of
  the evidence: the labs pass on both.
- fresh clone at `c32c529` (feat: lesson runner and course-voice
  READMEs), i.e. exactly what the pushed branch serves.

## Replay 1: pytest, from the fresh clone root

Command:

    cd /tmp/labs-replay-clone
    /tmp/labs-replay-venv/bin/python -m pytest -q learning-labs/tests

Observed output (exit code 0):

    ..................                                                       [100%]
    18 passed in 0.05s

Same 18 tests, same pass count as the development environment
(results/PYTEST-COUNTS.md), collected and passed with nothing installed
but pytest.

## Replay 2: the lesson runner, from the fresh clone root

Command:

    /tmp/labs-replay-venv/bin/python learning-labs/run.py --all

Observed: exit code 0, all three lessons intact. Full transcript:

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

## Replay 3: single lab, from inside learning-labs/

Command:

    cd learning-labs
    /tmp/labs-replay-venv/bin/python run.py --lab audio

Observed: exit code 0, last lines:

    ========================================================================
      audio: intact
    every lesson intact (exit 0)

## Conclusion

Both documented commands work in a fresh clone with a stock-pytest-only
virtualenv: `18 passed` from pytest, `every lesson intact (exit 0)` from
the runner, and the in-directory invocation resolves paths from the
runner's own location as documented in INTERFACE.md. Portability holds.
