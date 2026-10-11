"""Checks for the grid lab -- the one source of truth for "correct".

Both the pytest suite (learning-labs/tests) and the runner
(learning-labs/run.py) call these functions, so a lesson has exactly one
definition of correct. Each check takes a label_region implementation and
asserts with readable messages; AssertionError is the failure shape.

Every check copies the fixture grids before calling the implementation, so
the public constants are never mutated by the harness -- and a broken
implementation cannot corrupt a later check.

One unusual helper deserves your attention: _fresh_state clears a
module-level ``_visited`` set if the implementation has one. That is not
harness magic for its own sake -- it gives the module the state a fresh
process would have, and the way it finds the state (fn.__globals__) is
literally the answer to the lab's question, "where does state hide?".
The reference has no module state, so for it the helper does nothing.

LESSON at the bottom is the lesson manifest: every check, paired with
whether the BROKEN fill is supposed to pass it. reference.py must pass
every check; broken.py must fail exactly the False entries. run.py and
test_lessons.py both read this.
"""

from __future__ import annotations

from labs.grid import fixtures

QUESTION = (
    "The first call is perfect and the second is impossible. Where does "
    "state hide between calls, and why does the capstone's "
    "Submission.__init__ say to build the database fresh every run?"
)


def _fresh_state(label_region) -> None:
    """Give the implementation the module state a fresh process would have."""
    visited = label_region.__globals__.get("_visited")
    if visited is not None:
        visited.clear()


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _grid_diff(call: str, got: list[list[int]], expected: list[list[int]]) -> str:
    for index, (got_row, want_row) in enumerate(zip(got, expected)):
        if got_row != want_row:
            return f"{call}: row {index} differs -- expected {want_row}, got {got_row}"
    return (
        f"{call}: grids differ in shape -- expected {len(expected)} rows, "
        f"got {len(got)}"
    )


def _region_size(grid: list[list[int]], label: int) -> int:
    return sum(1 for row in grid for cell in row if cell == label)


def check_input_untouched(label_region) -> None:
    """STRICT check: the caller's grid is byte-for-byte unchanged after the
    call, and the result is a new grid object with new rows."""
    _fresh_state(label_region)
    grid = _copy(fixtures.GRID_ONE)
    snapshot = _copy(fixtures.GRID_ONE)

    result = label_region(grid, fixtures.CALL_ONE_START, fixtures.CALL_ONE_LABEL)

    assert result is not grid, (
        "label_region must return a new grid, not the caller's object"
    )
    assert all(a is not b for a, b in zip(result, grid)), (
        "label_region must build new rows, not reuse the caller's rows"
    )
    assert grid == snapshot, (
        "the caller's grid was relabeled during the call: "
        + _grid_diff("input after the call", grid, snapshot)
    )


def check_first_call_exact(label_region) -> None:
    """STRICT check, single call: the first call on a fresh grid produces
    exactly the expected output. broken.py passes this -- which is what
    makes the second call's failure so expensive to find."""
    _fresh_state(label_region)
    grid = _copy(fixtures.GRID_ONE)

    result = label_region(grid, fixtures.CALL_ONE_START, fixtures.CALL_ONE_LABEL)

    assert result == fixtures.EXPECTED_GRID_ONE, (
        _grid_diff("first call (GRID_ONE)", result, fixtures.EXPECTED_GRID_ONE)
    )
    size = _region_size(result, fixtures.CALL_ONE_LABEL)
    assert size == fixtures.EXPECTED_REGION_SIZE_ONE, (
        f"first call relabeled {size} cells; the region containing "
        f"{fixtures.CALL_ONE_START} has {fixtures.EXPECTED_REGION_SIZE_ONE}"
    )


def check_two_calls_exact(label_region) -> None:
    """STRICT check: two sequential calls on two different grids must each
    produce exactly the expected output. The first call being perfect is
    the setup; the second call is where stale state shows."""
    _fresh_state(label_region)

    grid_one = _copy(fixtures.GRID_ONE)
    result_one = label_region(
        grid_one, fixtures.CALL_ONE_START, fixtures.CALL_ONE_LABEL
    )
    assert result_one == fixtures.EXPECTED_GRID_ONE, (
        _grid_diff("first call (GRID_ONE)", result_one, fixtures.EXPECTED_GRID_ONE)
    )
    size_one = _region_size(result_one, fixtures.CALL_ONE_LABEL)
    assert size_one == fixtures.EXPECTED_REGION_SIZE_ONE, (
        f"first call relabeled {size_one} cells; the region containing "
        f"{fixtures.CALL_ONE_START} has {fixtures.EXPECTED_REGION_SIZE_ONE}"
    )

    grid_two = _copy(fixtures.GRID_TWO)
    result_two = label_region(
        grid_two, fixtures.CALL_TWO_START, fixtures.CALL_TWO_LABEL
    )
    assert result_two == fixtures.EXPECTED_GRID_TWO, (
        _grid_diff("second call (GRID_TWO)", result_two, fixtures.EXPECTED_GRID_TWO)
    )
    size_two = _region_size(result_two, fixtures.CALL_TWO_LABEL)
    assert size_two == fixtures.EXPECTED_REGION_SIZE_TWO, (
        f"second call relabeled {size_two} cells; the region containing "
        f"{fixtures.CALL_TWO_START} has {fixtures.EXPECTED_REGION_SIZE_TWO}. "
        "The first call was perfect and nothing about this call changed -- "
        "except what the function remembered."
    )


# (check name, should the BROKEN fill pass it?)
LESSON = (
    ("check_input_untouched", False),
    ("check_first_call_exact", True),
    ("check_two_calls_exact", False),
)
