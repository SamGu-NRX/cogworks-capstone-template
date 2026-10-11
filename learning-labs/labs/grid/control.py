"""The immutable control for the grid lab: the deliberate bugs of
broken.py, kept under lock.

You never edit this file. The lesson-integrity tests pin its bytes
(learning-labs/controls.json carries the sha256) and assert it still fails
exactly the checks the LESSON manifest says it fails. Whatever you do to
broken.py -- repair it, break it, experiment -- the control stays broken,
so the lesson cannot silently stop teaching. Edit labs/grid/broken.py;
that file is yours.

Two bugs, one lesson each:

1. It fails `check_input_untouched`: it writes labels straight into the
   caller's grid and returns the caller's object instead of a new grid.
2. It fails `check_two_calls_exact`: ``_visited`` lives at module level and
   is never cleared, so the second call starts where the first one ended.
   Cells the first call visited are relabeled but never EXPANDED on the
   second call, which truncates the fill: on the fixture's second call,
   3 of the region's 6 cells get labeled and the top-left corner of the
   region keeps its old value. The first call still looks perfect. The
   second is impossible -- until you ask where state hides between calls.

This is the toy version of the warning in week1/submission.py: a stale
database across runs is the most common source of a score that looks
impossible. Build state fresh every run.
"""

from __future__ import annotations

_visited: set[tuple[int, int]] = set()  # THE BUG: module level, never cleared


def label_region(
    grid: list[list[int]], start: tuple[int, int], label: int
) -> list[list[int]]:
    target = grid[start[0]][start[1]]

    stack = [start]
    while stack:
        r, c = stack.pop()
        if grid[r][c] != target:
            continue
        grid[r][c] = label  # THE BUG: writes into the caller's grid
        if (r, c) in _visited:
            continue  # stale state: the fill dies here, quietly
        _visited.add((r, c))
        if r > 0:
            stack.append((r - 1, c))
        if r + 1 < len(grid):
            stack.append((r + 1, c))
        if c > 0:
            stack.append((r, c - 1))
        if c + 1 < len(grid[0]):
            stack.append((r, c + 1))
    return grid
