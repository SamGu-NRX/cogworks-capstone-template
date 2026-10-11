"""Grid lab fixtures and public expected results.

Public on purpose: two authored 6x8 grids of ints -- 0 is background, the
other values are region ids -- and the exact expected output of two
flood-fill calls:

    call 1: label the region containing (1, 1) in GRID_ONE   -> 9
    call 2: label the region containing (3, 3) in GRID_TWO   -> 7

The two target regions deliberately share cells at the same coordinates
((1, 1), (1, 2), (2, 1), (2, 2) are in both). That overlap is what makes
state left behind by call 1 visible in call 2: coordinates are not identity,
and a second grid is not a second run.
"""

from __future__ import annotations

GRID_ONE: list[list[int]] = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 2, 2, 0],
    [0, 0, 0, 0, 0, 2, 2, 0],
]

GRID_TWO: list[list[int]] = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 3, 3, 0, 0, 0, 0, 0],
    [0, 3, 3, 3, 0, 0, 0, 0],
    [0, 0, 0, 3, 0, 0, 0, 0],
    [2, 2, 0, 0, 0, 0, 0, 0],
    [2, 2, 0, 0, 0, 0, 0, 0],
]

CALL_ONE_START: tuple[int, int] = (1, 1)
CALL_ONE_LABEL: int = 9
CALL_TWO_START: tuple[int, int] = (3, 3)
CALL_TWO_LABEL: int = 7

# Public expected results: the full labeled grids and the region sizes.
# These ARE the contract of this lab.
EXPECTED_GRID_ONE: list[list[int]] = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 9, 9, 0, 0, 0, 0, 0],
    [0, 9, 9, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 2, 2, 0],
    [0, 0, 0, 0, 0, 2, 2, 0],
]

EXPECTED_GRID_TWO: list[list[int]] = [
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 7, 7, 0, 0, 0, 0, 0],
    [0, 7, 7, 7, 0, 0, 0, 0],
    [0, 0, 0, 7, 0, 0, 0, 0],
    [2, 2, 0, 0, 0, 0, 0, 0],
    [2, 2, 0, 0, 0, 0, 0, 0],
]

EXPECTED_REGION_SIZE_ONE: int = 4
EXPECTED_REGION_SIZE_TWO: int = 6
