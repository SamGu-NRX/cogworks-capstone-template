"""Checks for the vector lab -- the one source of truth for "correct".

Both the pytest suite (learning-labs/tests) and the runner
(learning-labs/run.py) call these functions, so a lesson has exactly one
definition of correct. Each check takes a rank_by_similarity implementation
and asserts with readable messages; AssertionError is the failure shape.

Every check builds its OWN copy of the fixture data and hands the copy to
the implementation, so the public constants are never mutated by the
harness -- and a broken implementation cannot corrupt a later check.

LESSON at the bottom is the lesson manifest: every check, paired with
whether the BROKEN ranker is supposed to pass it. reference.py must pass
every check; broken.py must fail exactly the False entries. run.py and
test_lessons.py both read this.
"""

from __future__ import annotations

from labs.vector import fixtures

QUESTION = (
    "Your caller's vectors changed while you were ranking. Who owns the "
    "normalization, what did the snapshot see that a score-only test "
    "missed, and which line repairs it?"
)


def _fresh_vectors() -> dict[str, list[float]]:
    """A private copy of the fixture vectors, fresh per check."""
    return {item_id: list(vector) for item_id, vector in fixtures.VECTORS.items()}


def check_ranking_exact(rank_by_similarity) -> None:
    """STRICT check: exact id ranking, exact scores to 6 dp."""
    result = rank_by_similarity(_fresh_vectors(), list(fixtures.QUERY))
    assert isinstance(result, list) and all(
        isinstance(pair, tuple) and len(pair) == 2 for pair in result
    ), f"rank_by_similarity must return (item_id, score) pairs, got {result!r}"
    got = [(item_id, round(score, 6)) for item_id, score in result]
    assert got == fixtures.EXPECTED_RANKING, (
        f"expected ranking (id, cosine to 6 dp) {fixtures.EXPECTED_RANKING!r}, "
        f"got {got!r}"
    )


def check_ids_intact(rank_by_similarity) -> None:
    """STRICT check: returned pairs carry the input's ids -- the shape a
    score-only test never looks at."""
    result = rank_by_similarity(_fresh_vectors(), list(fixtures.QUERY))
    ids = [item_id for item_id, _score in result]
    assert all(isinstance(item_id, str) for item_id in ids), (
        f"every returned pair must be (item_id, score); ids came back as {ids!r}"
    )
    assert sorted(ids) == sorted(fixtures.VECTORS), (
        f"returned ids must be exactly the input keys "
        f"{sorted(fixtures.VECTORS)}, got {ids}"
    )
    assert len(ids) == len(set(ids)), (
        f"returned ids repeat: {ids}"
    )


def check_input_untouched(rank_by_similarity) -> None:
    """STRICT check: the caller's dict and query are byte-for-byte the same
    after the call. Ranking is a read."""
    vectors = _fresh_vectors()
    query = list(fixtures.QUERY)
    snapshot = {item_id: list(vector) for item_id, vector in vectors.items()}

    rank_by_similarity(vectors, query)

    assert query == fixtures.QUERY, (
        "the caller's query was rewritten during the call"
    )
    for item_id, original in snapshot.items():
        got = vectors.get(item_id)
        assert got == original, (
            f"the caller's dict changed during the call: vectors[{item_id!r}] "
            f"started as {original[:3]}... and ended as "
            f"{[round(x, 3) for x in (got or [])][:3]}... -- unit-length "
            "values instead of the caller's raw ones. Who owns the "
            "normalization?"
        )


# (check name, should the BROKEN ranker pass it?)
LESSON = (
    ("check_ranking_exact", True),
    ("check_ids_intact", True),
    ("check_input_untouched", False),
)
