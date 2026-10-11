"""The immutable control for the vector lab: the deliberate bugs of
broken.py, kept under lock.

You never edit this file. The lesson-integrity tests pin its bytes
(learning-labs/controls.json carries the sha256) and assert it still fails
exactly the checks the LESSON manifest says it fails. Whatever you do to
broken.py -- repair it, break it, experiment -- the control stays broken,
so the lesson cannot silently stop teaching. Edit labs/vector/broken.py;
that file is yours.

This version fails `check_input_untouched`, and still passes
`check_ranking_exact` and `check_ids_intact`.

The bug: it normalizes each vector and writes the normalized list back into
the caller's dict (`vectors[item_id] = ...`). The caller's data is silently
rewritten mid-call -- the caller handed over a dict to be RANKED and gets
back a dict of unit vectors.

Every id and score in the RETURN VALUE is still right: cosine is
scale-invariant, so normalizing the data does not move the answer. A
score-only test reads this implementation as perfect. The snapshot check
sees it, because it compares the caller's dict before and after the call.
"""

from __future__ import annotations

import math


def rank_by_similarity(
    vectors: dict[str, list[float]], query: list[float]
) -> list[tuple[str, float]]:
    query_norm = math.sqrt(sum(x * x for x in query))
    unit_query = [x / query_norm for x in query]

    ranked = []
    for item_id, vector in vectors.items():
        norm = math.sqrt(sum(x * x for x in vector))
        vectors[item_id] = [x / norm for x in vector]  # THE BUG: caller's dict
        score = sum(a * b for a, b in zip(vectors[item_id], unit_query))
        ranked.append((item_id, score))

    ranked.sort(key=lambda pair: pair[1], reverse=True)
    return ranked
