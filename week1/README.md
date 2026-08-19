# Week 1: audio identification

Identify a song from a short clip, the way Shazam does.

Your code goes in this directory. The only file with a required shape is
`submission.py`, which hands the benchmark two methods. Read its docstrings;
they say what each one gets and what it must return.

## A split that works

The capstone page lists the stages, and they make clean module boundaries.
One reasonable split for a team of four:

| stage | what it owns |
| --- | --- |
| spectrogram | audio in, time-frequency array out |
| peaks | spectrogram in, local-maximum coordinates out |
| fanout | peaks in, (f1, f2, dt) fingerprints out |
| database + query | fingerprints in, ranked song ids out |

Write those four signatures down before anyone writes a body. Then everyone
can build against something real, and the merge on Thursday is a merge rather
than a negotiation.

The last one is two jobs and usually goes to whoever finishes first.

## Getting a number early

Stub every stage to return the right shape with the wrong values, wire them
together, and run:

    cogworks run --benchmark audio-identification

It will score near zero. That is the point: the pipeline runs end to end on
day one, and from then on every improvement is measurable instead of
theoretical.

## What the score means

`identification_score` is top-1 accuracy over clips cut from songs you
enrolled, after perturbation. Every query also lands in one of four outcomes,
and those are what to read when the number is low:

- `retrieval_failure` means no shared fingerprints at all. Your fingerprints
  are not surviving whatever was done to the clip. Look at the peak
  threshold first.
- `ranking_failure` means the right song is in your list but buried. Your
  fingerprints are fine and your vote is wrong. Look at how you count offset
  agreement.

Those two point at different halves of the pipeline, which is why they are
reported separately.
