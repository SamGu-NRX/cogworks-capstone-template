# Week 2: facial recognition

Two halves of one project. Recognize people you have seen, and group photos
of people you have not.

Your code goes in this directory. `submission.py` has both contracts; fill in
whichever half you are on.

## A split that works

| stage | what it owns |
| --- | --- |
| detection + descriptors | image in, face boxes and 512-d descriptors out |
| profiles + database | descriptors in, named profiles, save and load |
| matching + cutoff | a descriptor in, a name or None out |
| whispers | descriptors in, cluster labels out |

The cutoff is one number and it decides two things at once: whether strangers
get rejected and whether newly added people get recognized. Whoever owns it
should own both, or the two halves will fight.

## The thing that surprised last year's teams

A profile built from one photo sits further from a new photo of that person
than a profile built from several does. So a cutoff tuned on well-enrolled
people rejects anyone you just added. The benchmark reports those two cases
separately for exactly this reason: if post-enrollment accuracy is zero while
unknown rejection is perfect, the recognizer is not broken, the cutoff is one
number doing two jobs.

## Whispers and randomness

The benchmark runs your clusterer under several seeds and reports the spread.
Use the `seed` argument for every random choice, including node visit order.
A result that swings across seeds is worth understanding rather than
averaging away.
