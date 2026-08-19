"""Week 1: hand the benchmark your song identifier.

Fill in the two methods below so they call your code. That is the whole job
of this file. Ten lines when you are done, and it should stay ten lines: if
you find yourself writing a spectrogram in here, move it into your own module
and call that instead.

Nothing else in this directory has a required shape. Name your files whatever
your team agreed on.

Check your work without spending anything:

    cogworks check --benchmark audio-identification    # what did it find?
    cogworks run   --benchmark audio-identification    # score it, offline
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np


class Submission:
    """Your song identifier, in the shape the benchmark expects."""

    def __init__(self) -> None:
        # Build your database here. It starts empty; enroll() fills it.
        #
        # If your code keeps its database in a module-level dict or a pickle
        # on disk, that is fine, but reset it here rather than reusing state
        # from a previous run. The benchmark calls enroll() from scratch every
        # time and a stale database is the most common source of a score that
        # looks impossible.
        raise NotImplementedError("build your database here")

    def enroll(self, song_id: str, samples: np.ndarray, sample_rate: int) -> None:
        """Add one song to the database.

        ``samples`` is a fresh, writeable, C-contiguous float32 mono signal in
        [-1, 1]. ``sample_rate`` is 44100. Mutating the array in place is safe;
        it is yours.

        ``song_id`` is the string you must give back from identify(). Store it.

        Called once per song, before any identify() call. Whatever your code
        calls this step (add, add_song, add_reference, register) the benchmark
        will find it, but wiring it here explicitly is clearer for your team.
        """
        raise NotImplementedError("call your fingerprint-and-store code")

    def identify(
        self, samples: np.ndarray, sample_rate: int
    ) -> List[Tuple[str, float]]:
        """Name the song this clip came from.

        Return ranked candidates, best first, as (song_id, score) pairs. The
        score is your own confidence, on whatever scale your matcher produces;
        the benchmark only compares them to each other.

        Return ``[]`` when you believe the clip is not from any enrolled song.
        Some clips genuinely are not, and saying so correctly is part of the
        score. Always guessing costs you.

        Three other shapes are accepted if they fit your code better: a bare
        list of song ids, a single id or None, or (song_id, artist, score)
        triples. The confidence-margin diagnostic needs scores, so it reads as
        "not measured" for the shapes without them.
        """
        raise NotImplementedError("call your matcher")

    # Optional. Delete if you do not have them. Neither affects your score;
    # both add a diagnostic that makes a bad number readable.
    #
    # def fingerprint(self, samples: np.ndarray, sample_rate: int):
    #     """Your fingerprints for one signal. Lets the benchmark report how
    #     many you generate per second, which is the first thing to look at
    #     when nothing matches."""
    #
    # def finalize_database(self) -> None:
    #     """Called once after the last enroll(). Sort, index, or write to disk
    #     here if your matcher wants a built database rather than an
    #     incremental one."""


def create_submission(resources=None) -> Submission:
    """The benchmark calls this. Leave the signature alone."""

    return Submission()
