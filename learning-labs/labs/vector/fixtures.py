"""Vector lab fixtures and public expected results.

Public on purpose: four authored 8-dim descriptors, one query, and the
exact cosine ranking the checks test against. Nothing is hidden, nothing
comes from a dataset, and every value is a plain Python float.

img-01 is parallel to the query (it is the query scaled 2x), which is the
point: cosine ignores magnitude, so normalization must not change the
ranking -- and must not change the caller's data either.
"""

from __future__ import annotations

QUERY: list[float] = [1.0, 0.0, 2.0, 0.0, 1.0, 0.0, 1.0, 1.0]

VECTORS: dict[str, list[float]] = {
    "img-01": [2.0, 0.0, 4.0, 0.0, 2.0, 0.0, 2.0, 2.0],
    "img-02": [0.0, 1.0, 2.0, 0.0, 1.0, 0.0, 0.0, 1.0],
    "img-03": [1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0],
    "img-04": [0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 1.0, 2.0],
}

# Public expected results: exact ranking, cosine rounded to 6 dp.
# Checks compare scores after round(score, 6); the gaps between these four
# are far larger than float noise.
EXPECTED_RANKING: list[tuple[str, float]] = [
    ("img-01", 1.0),
    ("img-02", 0.801784),
    ("img-04", 0.668153),
    ("img-03", 0.176777),
]
