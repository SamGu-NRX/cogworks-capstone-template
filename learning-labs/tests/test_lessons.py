"""Lesson-integrity meta-tests: each broken.py must fail exactly the checks
its lab says it fails (and pass the ones it passes -- the traps), and each
reference.py must pass every check. The LESSON manifest in each lab's
checks.py is the single source of truth; learning-labs/run.py reads the
same one, so the pytest suite and the runner can never disagree about what
the lesson is."""

import pytest

from labs.audio import broken as audio_broken
from labs.audio import checks as audio_checks
from labs.audio import reference as audio_reference
from labs.grid import broken as grid_broken
from labs.grid import checks as grid_checks
from labs.grid import reference as grid_reference
from labs.vector import broken as vector_broken
from labs.vector import checks as vector_checks
from labs.vector import reference as vector_reference

LABS = (
    ("audio", audio_checks, audio_reference.match_clip, audio_broken.match_clip),
    ("grid", grid_checks, grid_reference.label_region, grid_broken.label_region),
    (
        "vector",
        vector_checks,
        vector_reference.rank_by_similarity,
        vector_broken.rank_by_similarity,
    ),
)


def test_reference_passes_every_check():
    for lab, checks, reference, _broken in LABS:
        for name, _broken_passes in checks.LESSON:
            getattr(checks, name)(reference)  # raises if the lesson drifts


def test_broken_fails_exactly_its_documented_checks():
    for lab, checks, _reference, broken in LABS:
        for name, broken_passes in checks.LESSON:
            if broken_passes:
                continue
            with pytest.raises(AssertionError):
                getattr(checks, name)(broken)


def test_broken_still_passes_its_trap_checks():
    for lab, checks, _reference, broken in LABS:
        for name, broken_passes in checks.LESSON:
            if broken_passes:
                getattr(checks, name)(broken)  # raises if the trap stopped trapping
