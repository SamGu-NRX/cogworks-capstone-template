# The learning-labs interface

This file documents the supported interface of `learning-labs/`. If
something is not in here, it is not supported and you should not depend on
it. Everything documented here is standard library plus pytest.

## What each lab is

Three labs: `audio`, `vector`, `grid`, under `learning-labs/labs/<lab>/`.
Each lab is a deliberately small, hand-authored problem with public
expected results. Deterministic only: no RNG, no datasets, no network, no
imports of cogworks or any benchmark package. Every value is a plain
Python float, int, or string.

Per lab, six moving parts:

| Module | What it holds |
| --- | --- |
| `labs/<lab>/fixtures.py` | The authored inputs AND the public expected results, as named constants |
| `labs/<lab>/reference.py` | A working implementation of the lab's function |
| `labs/<lab>/broken.py` | A broken implementation with a `TODO: repair` comment; its docstring names exactly which check it fails and why. The one file you are invited to edit |
| `labs/<lab>/control.py` | An immutable twin of the same broken implementation -- the pristine defect the integrity tests watch. Never edit it; `broken.py` is yours |
| `labs/<lab>/checks.py` | The strict check functions -- one source of truth used by the pytest suite, `run.py` AND `validate.py` -- plus `QUESTION` and the `LESSON` manifest |
| `labs/<lab>/README.md` | The experimental question and the repair walk-through |

One file per lab pair sits outside this table: `learning-labs/controls.json`
pins the sha256 of every `control.py`, and the pytest suite fails if any
of them changes by a single byte.

## Public functions and constants

Scores are compared after `round(score, 6)`; raw floats come back from the
implementations.

### audio

- `labs.audio.reference.match_clip(database: dict[str, list[float]], clip: list[float]) -> tuple[str, float, int]`
  (also in `labs.audio.broken`). Returns `(best_song_id, best_score, best_offset)`;
  `score` is the fraction of the clip's samples that align exactly, and every
  offset from `0` through `len(song) - len(clip)` is tried, inclusive.
- `labs.audio.fixtures`: `SONG_A`, `SONG_B`, `CLIP`, `DATABASE`,
  `EXPECTED_BEST_ID` (`"song-a"`), `EXPECTED_BEST_SCORE` (`1.0`),
  `EXPECTED_OFFSET` (`37`), `EXPECTED_ALIGNMENT_LENGTH` (`40`).
- `labs.audio.checks`: `check_best_id(fn)` (loose), `check_exact_alignment(fn)` (strict).

### vector

- `labs.vector.reference.rank_by_similarity(vectors: dict[str, list[float]], query: list[float]) -> list[tuple[str, float]]`
  (also in `labs.vector.broken`). Returns `(item_id, cosine)` pairs, best
  first, keyed by the original ids.
- `labs.vector.fixtures`: `QUERY`, `VECTORS`,
  `EXPECTED_RANKING` (`[("img-01", 1.0), ("img-02", 0.801784), ("img-04", 0.668153), ("img-03", 0.176777)]`).
- `labs.vector.checks`: `check_ranking_exact(fn)`, `check_ids_intact(fn)`,
  `check_input_untouched(fn)` (all strict).

### grid

- `labs.grid.reference.label_region(grid: list[list[int]], start: tuple[int, int], label: int) -> list[list[int]]`
  (also in `labs.grid.broken`). 4-connected flood fill; returns a NEW grid
  and leaves the caller's untouched.
- `labs.grid.fixtures`: `GRID_ONE`, `GRID_TWO`, `CALL_ONE_START` (`(1, 1)`),
  `CALL_ONE_LABEL` (`9`), `CALL_TWO_START` (`(3, 3)`), `CALL_TWO_LABEL`
  (`7`), `EXPECTED_GRID_ONE`, `EXPECTED_GRID_TWO`,
  `EXPECTED_REGION_SIZE_ONE` (`4`), `EXPECTED_REGION_SIZE_TWO` (`6`).
- `labs.grid.checks`: `check_input_untouched(fn)`, `check_first_call_exact(fn)`,
  `check_two_calls_exact(fn)` (all strict).

### checks, generally

Every check function takes the implementation under test, returns `None`,
and signals failure by raising `AssertionError` with a readable message.
Each lab's `checks.LESSON` is a tuple of `(check_name, should_broken_pass)`
pairs. Three implementations are held against it, with three different
roles:

- `reference.py` must pass every check in it.
- `control.py` must fail exactly the `False` entries and pass exactly the
  `True` entries -- it is the pristine, pinned defect. The lesson cannot
  silently stop teaching, no matter what happens to `broken.py`.
- `broken.py` is the student's to edit. The pytest suite says nothing
  about it; the command that grades it is `validate.py`.

Checks copy fixture data before calling the implementation, so the
constants are never mutated by the harness.

## Commands

From the repo root:

    python -m pytest -q learning-labs/tests
    python learning-labs/run.py --all
    python learning-labs/run.py --lab audio
    python learning-labs/run.py --lab vector
    python learning-labs/run.py --lab grid
    python learning-labs/validate.py --all
    python learning-labs/validate.py --lab audio
    python learning-labs/validate.py --lab vector
    python learning-labs/validate.py --lab grid

Also supported: `cd learning-labs && python run.py --all` (and the
`--lab` variants of both commands). Paths are resolved from the command's
own location, never from the current directory.

`run.py` is the tour. It prints, per lab: the experimental question, a
BEFORE block (every check run against `broken.py`, failures shown with
readable diffs), the same checks against `reference.py` (for diffing
after your repair works), and the behavior of the immutable `control.py`.
Its exit code is a verdict about the FIXED side of the lesson only:
control.py failing exactly as documented and reference.py passing
everything. Student edits to `broken.py` cannot flip it.

`validate.py` is the gate. It runs every strict check against *your*
`broken.py` and exits 0 only when all of them pass -- trap checks
included -- while `control.py` stays demonstrably broken. Exit 1 means
keep repairing (the failing checks and their diffs are printed); exit 2
means a control no longer behaves as documented -- restore it with
`git checkout -- learning-labs/labs/<lab>/control.py`.

## Supported environment

- CPython >= 3.9
- stock pytest (the only dependency)
- no network, no datasets, nothing to install beyond pytest

## Stability promise

The public expected results in each `fixtures.py` ARE the contract of
these lessons. They will not change quietly: if a constant ever changes,
that is a new lesson, and it says so here first. The same goes for the
`LESSON` manifests -- which checks a broken implementation fails is part
of the lesson, not an implementation detail. The third fixed thing is
`control.py`: its exact bytes are pinned in `controls.json` and the
pytest suite fails if it drifts. `broken.py` carries no such promise --
it is the one file in each lab that is yours to rewrite.
