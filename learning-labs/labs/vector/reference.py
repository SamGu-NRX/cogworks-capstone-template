"""The working vector ranker.

rank_by_similarity(vectors, query) ranks the vectors by cosine similarity
to the query, best first, as (item_id, score) pairs keyed by the ORIGINAL
ids. Raw cosines come back; checks round to 6 dp.

The ownership rule this lab is about: the caller's data belongs to the
caller. This implementation normalizes into NEW float lists and never
writes to ``vectors`` -- the caller's dict is byte-for-byte the same after
the call, because ranking is a read.
"""

from __future__ import annotations

import math


def rank_by_similarity(
    vectors: dict[str, list[float]], query: list[float]
) -> list[tuple[str, float]]:
    query_norm = math.sqrt(sum(x * x for x in query))
    unit_query = [x / query_norm for x in query]  # new floats, new list

    ranked = []
    for item_id, vector in vectors.items():
        norm = math.sqrt(sum(x * x for x in vector))
        unit = [x / norm for x in vector]  # new floats, new list
        score = sum(a * b for a, b in zip(unit, unit_query))
        ranked.append((item_id, score))

    ranked.sort(key=lambda pair: pair[1], reverse=True)
    return ranked
