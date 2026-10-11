"""The immutable control for the audio lab: the deliberate bugs of
broken.py, kept under lock.

You never edit this file. The lesson-integrity tests pin its bytes
(learning-labs/controls.json carries the sha256) and assert it still fails
exactly the checks the LESSON manifest says it fails. Whatever you do to
broken.py -- repair it, break it, experiment -- the control stays broken,
so the lesson cannot silently stop teaching. Edit labs/audio/broken.py;
that file is yours.

This version fails `check_exact_alignment` and still passes
`check_best_id`.

The bug is one sample long: the song window slice ends at
`offset + len(clip) - 1` instead of `offset + len(clip)`, so only the first
39 of the clip's 40 samples are ever compared. zip() quietly drops the rest.
The clip still lines up best at offset 37 in song-a -- which is why the
loose question still answers "song-a" -- but the score comes back
39/40 = 0.975 instead of 1.0, because the contract scores the fraction of
the WHOLE clip that aligns. A test that only asks "which song?" reads this
implementation as perfect. A strict test that checks the exact score, the
offset, and the alignment length does not.
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
            window = song[offset:offset + len(clip) - 1]  # one sample short
            matches = sum(1 for a, b in zip(window, clip) if a == b)
            score = matches / len(clip)
            if score > best_score:
                best_id, best_score, best_offset = song_id, score, offset
    return best_id, best_score, best_offset
