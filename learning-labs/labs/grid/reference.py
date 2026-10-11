"""The working flood fill.

label_region(grid, start, label) relabels every cell of the 4-connected
region containing ``start`` and returns a NEW grid. The caller's grid is
byte-for-byte the same after the call -- rows are copied, never written.

Two housekeeping rules do all the contract work:

    visited -- a FRESH set per call. It exists for this call only.
    result  -- a FRESH grid per call. The caller keeps theirs.

4-connected means up, down, left, right -- no diagonals.
"""

from __future__ import annotations


def label_region(
    grid: list[list[int]], start: tuple[int, int], label: int
) -> list[list[int]]:
    visited: set[tuple[int, int]] = set()  # fresh per call
    result = [row[:] for row in grid]  # new grid, new rows
    target = result[start[0]][start[1]]

    stack = [start]
    while stack:
        r, c = stack.pop()
        if (r, c) in visited or result[r][c] != target:
            continue
        visited.add((r, c))
        result[r][c] = label
        if r > 0:
            stack.append((r - 1, c))
        if r + 1 < len(result):
            stack.append((r + 1, c))
        if c > 0:
            stack.append((r, c - 1))
        if c + 1 < len(result[0]):
            stack.append((r, c + 1))
    return result
