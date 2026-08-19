"""Week 2: hand the benchmark your face recognizer and your clusterer.

Two separate benchmarks share this file, because the capstone is two halves
of one project. Fill in whichever you are working on; a half you have not
started can keep raising NotImplementedError and the other half still scores.

Nothing else in this directory has a required shape.

    cogworks check --benchmark vision-recognition
    cogworks run   --benchmark vision-recognition
    cogworks run   --benchmark vision-clustering
"""

from __future__ import annotations

from typing import List, Optional, Sequence

import numpy as np

# An image is an (H, W, 3) uint8 RGB array. The benchmark decodes files for
# you, so your code never opens a path and never depends on a codec.
Image = np.ndarray
PersonId = str
ClusterId = int


class RecognitionSubmission:
    """Part 1: know who is in a photo, and admit when you do not."""

    def __init__(self) -> None:
        # Your database of profiles starts empty. Load your FaceNet model
        # here if your code needs one; the benchmark's image is built with it
        # already downloaded, so this costs no network.
        raise NotImplementedError("set up your database and model here")

    def enroll(self, person_id: PersonId, images: Sequence[Image]) -> None:
        """Add one person, from one or more photos of them.

        Compute a descriptor per photo and store them under ``person_id``.
        The course's suggestion is to average them into one profile vector,
        which is worth doing: a profile built from several photos sits closer
        to a new photo of that person than a profile built from one.

        Called once per person, before any recognize() call.
        """
        raise NotImplementedError("call your descriptor and profile code")

    def recognize(self, images: Sequence[Image]) -> List[Optional[PersonId]]:
        """Name each face, one answer per input image, in the same order.

        Return the person's id, or ``None`` for "I do not know this person".

        ``None`` is a real answer and the benchmark scores it. Some of these
        photos are of people you never enrolled, and matching them to the
        nearest name you happen to have is wrong. This is the cutoff the
        course asks you to choose, and both directions cost you: too generous
        and every stranger becomes somebody, too strict and nobody is ever
        recognized.

        If a photo has no detectable face, ``None`` is the right answer.
        """
        raise NotImplementedError("call your matcher")


class ClusteringSubmission:
    """Part 2: group photos by person, without being told who anyone is."""

    def __init__(self) -> None:
        raise NotImplementedError("set up your model here")

    def cluster(self, images: Sequence[Image], *, seed: int) -> Sequence[ClusterId]:
        """Group the photos. Return one integer label per image, in order.

        The label values do not matter, only which images share one. Labels
        [0,0,1] and [7,7,2] score identically.

        ``seed`` is keyword-only and you must use it for every random choice
        your algorithm makes, including the order Whispers visits nodes. The
        benchmark runs the same images under several seeds and reports how
        much your answer moves. A result that swings wildly between seeds is
        telling you something real about the algorithm.
        """
        raise NotImplementedError("call your whispers implementation")


def create_recognition_submission(resources=None) -> RecognitionSubmission:
    """The benchmark calls this for vision-recognition."""

    return RecognitionSubmission()


def create_clustering_submission(resources=None) -> ClusteringSubmission:
    """The benchmark calls this for vision-clustering."""

    return ClusteringSubmission()


# `cogworks run --benchmark vision-recognition` looks for create_submission
# and falls back to the named factories above. Point this at whichever half
# you are working on so the plain command does the thing you expect.
create_submission = create_recognition_submission
