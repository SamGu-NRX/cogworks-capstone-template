# Lab: vector -- the caller's data changed while you were ranking

Four items -- `img-01` through `img-04`, 8-dimensional descriptors that
stand in for enrollment features -- and a `QUERY`. Rank the items by
cosine similarity against the query and return `(item_id, cosine)` pairs,
best first. The expected ranking is public, to 6 decimal places:
`img-01` (1.0), `img-02` (0.801784), `img-04` (0.668153), `img-03`
(0.176777). No ties, deliberately: a tie would make the lesson ambiguous.

Cosine similarity needs unit vectors, so somebody normalizes. The
question is who. `reference.py` treats the caller's dict as read-only:
normalization builds new floats and never writes back. `broken.py`
normalizes **in place** -- each list in the caller's dict is overwritten
with its own unit-length version, mid-call, as a side effect.

## The question

Your caller's vectors changed while you were ranking. Who owns the
normalization, what did the snapshot see that a score-only test missed,
and which line repairs it?

Run the runner first and count what still passes in the BEFORE block: the
ranking check passes, the id check passes. A test that only scores the
output -- the exact ranking, the exact ids -- ships this code to the
benchmark. The check that catches it takes a *snapshot* of the input
before the call and asserts equality after. That snapshot is the entire
technique: cheap, boring, and the only witness to a crime committed
against the caller.

It matters beyond the toy because in the capstone your enrollment features
live across calls. Normalize in place once and every call after the first
is ranking *unit vectors re-normalized* -- same answers here, because unit
vectors are idempotent under normalization -- while any caller doing
something else with those values inherits floats it never created. In
real embeddings, magnitude can mean something. You gave it away.

## The repair

```bash
python learning-labs/run.py --lab vector
```

BEFORE block: two passes (the traps) and one failure,
`check_input_untouched`, whose message shows the caller's dict before and
after: `[2.0, 0.0, 4.0]...` became `[0.354, 0.0, 0.707]...`.

Open `broken.py` and find the line that writes through the reference the
caller lent you. The repair is to build the normalized values as new
floats and return pairs keyed by the *original* ids -- one line changes,
and the ranking it returns does not move by a digit. That is the point:
the output was never wrong. Then run the runner again, and when it is
intact, compare with `reference.py` and notice how little had to change
to stop breaking your caller's data.
