"""Week 3: hand the benchmark your semantic image search.

Four methods, in two groups. The first two are the embeddings the whole
project rests on; the second two are the application built on top of them.

Nothing else in this directory has a required shape.

    cogworks check --benchmark language-search
    cogworks run   --benchmark language-search
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np


class Submission:
    """Your caption-to-image search, in the shape the benchmark expects."""

    def __init__(self) -> None:
        # Load your trained W_embed here, plus GloVe and your IDF table. The
        # benchmark's image carries the GloVe vectors already, so this costs
        # no network.
        #
        # Load trained weights from a file you committed. Training inside
        # __init__ is allowed but it spends your evaluation budget on work
        # you already did.
        raise NotImplementedError("load your weights, GloVe, and IDF table")

    def embed_text(self, captions: Sequence[str]) -> np.ndarray:
        """Embed captions. Returns (len(captions), D) float32, D your choice.

        This is the IDF-weighted sum of GloVe vectors from the course, on its
        own, before any image is involved. Two things the benchmark checks
        that are easy to get wrong:

        A word you have never seen contributes a zero vector rather than
        raising. Query captions contain words your training set did not, and
        a KeyError here costs you the whole component.

        IDF is computed across every caption in the dataset, not per query.

        Rows should be L2-normalized unless you have a reason otherwise; the
        benchmark compares by cosine similarity.
        """
        raise NotImplementedError("call your caption embedding code")

    def embed_images(self, descriptors: np.ndarray) -> np.ndarray:
        """Embed image descriptors. Takes (N, 512), returns (N, D).

        This is W_embed, the matrix you trained with margin ranking loss
        against confusors. Same D as embed_text, because the point of the
        training was to put both in one space. If these two disagree on D the
        benchmark says so rather than scoring you near chance for a shape bug.
        """
        raise NotImplementedError("apply your trained W_embed")

    def prepare_database(
        self, image_ids: Sequence[int], descriptors: np.ndarray
    ) -> None:
        """Build the searchable database. Called once before any search().

        Embed the descriptors, store them next to their ids, and keep whatever
        index your search() wants. The ids are the integers you must give back
        from search(); do not renumber them.
        """
        raise NotImplementedError("build your searchable database")

    def search(self, query: str, k: int) -> List[int]:
        """Return the ids of the k best images for this query, best first.

        This is the application end to end: a query string in, ranked image
        ids out. Return image ids from the database you were given, not row
        indices into your own array. Returning ids that are not in the pool is
        a common bug and the benchmark counts them for you.
        """
        raise NotImplementedError("call your query path")


def create_submission(resources=None) -> Submission:
    """The benchmark calls this. Leave the signature alone."""

    return Submission()
