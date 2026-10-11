"""Checks for the audio lab -- the one source of truth for "correct".

Both the pytest suite (learning-labs/tests) and the runner
(learning-labs/run.py) call these functions, so a lesson has exactly one
definition of correct. Each check takes a match_clip implementation and
asserts with readable messages; AssertionError is the failure shape.

check_best_id is the LOOSE question ("which song?"). It is deliberately
weak, and deliberately included, because the broken matcher passes it.

LESSON at the bottom is the lesson manifest: every check, paired with
whether the BROKEN matcher is supposed to pass it. reference.py must pass
every check; broken.py must fail exactly the False entries. run.py and
test_lessons.py both read this, so the manifest is the contract of the
lesson in one place.
"""

from __future__ import annotations

from labs.audio import fixtures

QUESTION = (
    "The loose question -- which song? -- already has the right answer. "
    "Which boundary is off by one, why does a strict test see it when "
    "best_id does not, and what does that protect when your real "
    "submission returns shapes to a benchmark?"
)


def check_best_id(match_clip) -> None:
    """LOOSE check: which song did the clip come from?

    The broken matcher passes this. That is the trap the lab is about, not
    a bug in the check.
    """
    song_id, _score, _offset = match_clip(fixtures.DATABASE, fixtures.CLIP)
    assert song_id == fixtures.EXPECTED_BEST_ID, (
        f"expected the clip's best match to be {fixtures.EXPECTED_BEST_ID!r}, "
        f"got {song_id!r}"
    )


def check_exact_alignment(match_clip) -> None:
    """STRICT check: the exact (song_id, score, offset), plus the alignment
    length the fixture data supports at the reported offset."""
    result = match_clip(fixtures.DATABASE, fixtures.CLIP)
    assert isinstance(result, tuple) and len(result) == 3, (
        "match_clip must return a (song_id, score, offset) tuple, "
        f"got {result!r}"
    )
    song_id, score, offset = result

    assert song_id == fixtures.EXPECTED_BEST_ID, (
        f"expected best id {fixtures.EXPECTED_BEST_ID!r}, got {song_id!r}"
    )

    assert offset == fixtures.EXPECTED_OFFSET, (
        f"expected the alignment to start at offset {fixtures.EXPECTED_OFFSET}, "
        f"got {offset}"
    )

    assert round(score, 6) == fixtures.EXPECTED_BEST_SCORE, (
        f"expected best score {fixtures.EXPECTED_BEST_SCORE} -- all "
        f"{len(fixtures.CLIP)} clip samples aligned at offset "
        f"{fixtures.EXPECTED_OFFSET} -- but got {round(score, 6)}: right song, "
        "right offset, short score. Count the samples your window compares."
    )

    length = _alignment_length(
        fixtures.DATABASE[fixtures.EXPECTED_BEST_ID], fixtures.CLIP, offset
    )
    assert length == fixtures.EXPECTED_ALIGNMENT_LENGTH, (
        f"expected {fixtures.EXPECTED_ALIGNMENT_LENGTH} clip samples to align "
        f"exactly at offset {offset}; the fixture data supports {length}"
    )


def _alignment_length(song: list[float], clip: list[float], offset: int) -> int:
    """How many clip samples line up exactly, starting at that offset."""
    length = 0
    for i, clip_sample in enumerate(clip):
        if song[offset + i] != clip_sample:
            break
        length += 1
    return length


# (check name, should the BROKEN matcher pass it?)
LESSON = (
    ("check_best_id", True),
    ("check_exact_alignment", False),
)
