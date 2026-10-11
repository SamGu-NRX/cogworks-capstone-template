"""Strict contract tests for the vector lab, run against the REFERENCE
ranker and the public expected results. The broken ranker is
test_lessons.py's job."""

from labs.vector import checks, fixtures, reference


def test_reference_matches_the_public_ranking_exactly():
    checks.check_ranking_exact(reference.rank_by_similarity)


def test_reference_returns_the_input_ids_intact():
    checks.check_ids_intact(reference.rank_by_similarity)


def test_reference_leaves_the_callers_data_alone():
    checks.check_input_untouched(reference.rank_by_similarity)


def test_expected_ranking_covers_exactly_the_input_keys():
    assert {item_id for item_id, _ in fixtures.EXPECTED_RANKING} == set(
        fixtures.VECTORS
    ), "the expected ranking must name exactly the fixture ids"


def test_expected_scores_are_distinct_and_cosine_ranged():
    scores = [score for _item_id, score in fixtures.EXPECTED_RANKING]
    assert all(-1.0 <= score <= 1.0 for score in scores), (
        "cosines must land in [-1, 1]"
    )
    assert len(set(scores)) == len(scores), (
        "the expected ranking must have no ties, or the lesson is ambiguous"
    )
