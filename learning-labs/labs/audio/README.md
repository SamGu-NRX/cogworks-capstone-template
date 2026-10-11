# Lab: audio -- the off-by-one that still answers the question

Two songs, `SONG_A` and `SONG_B`: 160 deterministic samples each, values in
[-1, 1]. `SONG_A` is a chirp, `SONG_B` is a two-tone beep, and `CLIP` is
`SONG_A` cut at offset 37, all 40 samples of it. Your matcher gets the
database and the clip and returns `(best_id, best_score, best_offset)`,
where the score is the fraction of the clip's samples that align exactly
at the best offset, tried across every window in every song.

The expected results are public: `("song-a", 1.0, 37)`. `broken.py` returns
`("song-a", 0.975, 37)` -- the same song, the same offset, one sample shy
on the score.

## The question

The loose question -- which song? -- already has the right answer. Which
boundary is off by one, why does a strict test see it when `best_id` does
not, and what does that protect when your real submission returns shapes
to a benchmark?

Think about what a slice of `len(clip) - 1` samples does to a score that
is a fraction: 39 out of 40 comparisons can still be perfect, the 40th is
just *not counted*, and nobody downstream complains unless somebody
asserted the total. A benchmark that asks your submission for a ranked
list cannot tell "right answer, incomplete" from "right answer" -- it
scores what you returned. The strict check is you, earlier, refusing to
round that difference away.

## The repair

```bash
python learning-labs/run.py --lab audio
```

Read the BEFORE block: `check_best_id` still passes (that is the trap --
if your only test asks for the best id, `broken.py` ships) and
`check_exact_alignment` fails with the diff: expected 1.0, got 0.975.

Open `broken.py`. The loop is

```python
window = song[offset:offset + len(clip) - 1]
```

Ask, before touching anything: how many samples does `song[a:b]` contain,
and how many do you owe the caller? Fix the slice -- the fix is one
character. Then prove the repair:

```bash
python learning-labs/validate.py --lab audio
```

It runs both checks against *your* `broken.py` and exits 0 only when
every check passes -- `check_best_id` included, so you cannot repair by
breaking the loose test. If you are tempted to "fix" the score by
changing the denominator instead of the window, the gate catches that
too: `check_exact_alignment` will still be waiting at 0.975. When it
exits 0, compare with `reference.py`, which computes the same answer with
a window that covers every sample it scores.
