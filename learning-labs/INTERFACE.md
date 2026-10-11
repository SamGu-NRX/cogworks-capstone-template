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

Per lab, five moving parts:

| Module | What it holds |
| --- | --- |
| `labs/<lab>/fixtures.py` | The authored inputs AND the public expected results, as named constants |
| `labs/<lab>/reference.py` | A working implementation of the lab's function |
| `labs/<lab>/broken.py` | A broken implementation with a `TODO: repair` comment; its docstring names exactly which check it fails and why |
| `labs/<lab>/checks.py` | The strict check functions -- one source of truth used by both the pytest suite and `run.py` -- plus `QUESTION` and the `LESSON` manifest |
| `labs/<lab>/README.md` | The experimental question and the repair walk-through |

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
pairs: `reference.py` must pass every check in it, `broken.py` must fail
exactly the `False` entries and pass exactly the `True` entries. Checks
copy fixture data before calling the implementation, so the constants are
never mutated by the harness.

## Commands

From the repo root:

    python -m pytest -q learning-labs/tests
    python learning-labs/run.py --all
    python learning-labs/run.py --lab audio
    python learning-labs/run.py --lab vector
    python learning-labs/run.py --lab grid

Also supported: `cd learning-labs && python run.py --all` (and the `--lab`
variants). Paths are resolved from the runner's own location, never from
the current directory. `run.py` exits 0 iff every selected lesson is
intact: broken.py fails exactly its documented checks, passes exactly its
documented traps, and reference.py passes everything.

## Supported environment

- CPython >= 3.9
- stock pytest (the only dependency)
- no network, no datasets, nothing to install beyond pytest

## Stability promise

The public expected results in each `fixtures.py` ARE the contract of
these lessons. They will not change quietly: if a constant ever changes,
that is a new lesson, and it says so here first. The same goes for the
`LESSON` manifests -- which checks a broken implementation fails is part
of the lesson, not an implementation detail.
