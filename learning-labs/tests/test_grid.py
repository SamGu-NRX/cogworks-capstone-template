"""Strict contract tests for the grid lab, run against the REFERENCE
flood fill and the public expected results. The broken fill is
test_lessons.py's job."""

from labs.grid import checks, fixtures, reference


def test_reference_leaves_the_callers_grid_alone():
    checks.check_input_untouched(reference.label_region)


def test_reference_nails_the_first_call():
    checks.check_first_call_exact(reference.label_region)


def test_reference_nails_two_sequential_calls():
    checks.check_two_calls_exact(reference.label_region)


def test_expected_grids_match_their_documented_region_sizes():
    counted_one = sum(
        cell == fixtures.CALL_ONE_LABEL
        for row in fixtures.EXPECTED_GRID_ONE
        for cell in row
    )
    counted_two = sum(
        cell == fixtures.CALL_TWO_LABEL
        for row in fixtures.EXPECTED_GRID_TWO
        for cell in row
    )
    assert counted_one == fixtures.EXPECTED_REGION_SIZE_ONE
    assert counted_two == fixtures.EXPECTED_REGION_SIZE_TWO


def test_grids_have_the_documented_shape():
    for grid in (
        fixtures.GRID_ONE,
        fixtures.GRID_TWO,
        fixtures.EXPECTED_GRID_ONE,
        fixtures.EXPECTED_GRID_TWO,
    ):
        assert len(grid) == 6 and all(len(row) == 8 for row in grid), (
            "every fixture grid must be 6 rows by 8 columns"
        )
