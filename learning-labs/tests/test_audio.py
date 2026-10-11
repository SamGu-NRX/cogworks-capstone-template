"""Strict contract tests for the audio lab, run against the REFERENCE
matcher and the public expected results. The broken matcher is
test_lessons.py's job."""

from labs.audio import checks, fixtures, reference


def test_reference_answers_the_loose_question():
    checks.check_best_id(reference.match_clip)


def test_reference_matches_the_public_alignment_exactly():
    checks.check_exact_alignment(reference.match_clip)


def test_fixture_clip_is_cut_from_song_a_at_the_expected_offset():
    start = fixtures.EXPECTED_OFFSET
    end = start + fixtures.EXPECTED_ALIGNMENT_LENGTH
    assert fixtures.CLIP == fixtures.SONG_A[start:end], (
        "CLIP must be SONG_A cut at the documented offset and length"
    )


def test_expected_alignment_length_is_the_whole_clip():
    assert fixtures.EXPECTED_ALIGNMENT_LENGTH == len(fixtures.CLIP)


def test_song_values_stay_in_the_documented_range():
    for song in (fixtures.SONG_A, fixtures.SONG_B, fixtures.CLIP):
        assert all(-1.0 <= sample <= 1.0 for sample in song), (
            "every sample must be in [-1, 1]"
        )
