"""The working audio matcher.

match_clip slides the clip across every song in the database and returns the
single best alignment as a (song_id, score, offset) tuple:

    score  -- the fraction of the clip's samples that align EXACTLY at that
              offset, so 1.0 means the whole clip lines up sample for sample
    offset -- the index in the song where the clip's first sample lands

Every offset from 0 through len(song) - len(clip) is tried, inclusive: the
last window that still fits. Scores are plain float arithmetic on the
fixture values; checks compare them after round(score, 6). An empty database
returns ("", -1.0, -1). The authored fixture has no ties, but a tie would
break to the first offset in song order (dict insertion order).
"""

from __future__ import annotations


def match_clip(
    database: dict[str, list[float]], clip: list[float]
) -> tuple[str, float, int]:
    best_id = ""
    best_score = -1.0
    best_offset = -1
    for song_id, song in database.items():
        for offset in range(len(song) - len(clip) + 1):
            window = song[offset:offset + len(clip)]
            matches = sum(1 for a, b in zip(window, clip) if a == b)
            score = matches / len(clip)
            if score > best_score:
                best_id, best_score, best_offset = song_id, score, offset
    return best_id, best_score, best_offset
