# Repair outcomes (decoupled student file)

The revision that separates each lesson's fixed side -- immutable
`control.py` twins, hash-pinned in `controls.json`, plus `reference.py` --
from `broken.py`, the one file you edit, and adds `validate.py`, the
command that grades a repair:

    python learning-labs/validate.py --all      # exit 0 = every strict
                                                # check passes on YOUR
                                                # broken.py, controls still
                                                # demonstrably broken

Everything below was observed on that revision, from the repository root,
in one shell, in the order shown. Under each "observed transcript"
heading, the command's output is byte for byte as observed. The three
`broken.py` files were restored to their shipped state afterwards
(`git checkout --`); the immutable controls were never touched, and their
sha256 digests are printed at the end as proof.

What to notice: pytest is green at the first and third steps -- the suite
never asserts anything about `broken.py` -- while `validate.py` flips
from exit 1 to exit 0 between them and back to 1 after the restore. That
flip, not any pytest result, is the signal that a repair landed.

## The workflow, in order

1. Shipped tree, nothing edited: the integrity suite, the tour, the gate.
2. The documented repairs -- the ones each lab's README walks -- applied
   to all three `broken.py` files, as a student's editor would.
3. Repaired tree: the gate, the integrity suite, and the tour again.
4. The three `broken.py` files restored to their shipped state; the gate
   again; the control hashes.

## Observed transcript: pytest on the shipped tree

    python3 -m pytest -q learning-labs/tests

Exit code: 0.

```text
....................                                                     [100%]
20 passed in 0.07s
```

## Observed transcript: validate.py --all on the shipped tree

    python learning-labs/validate.py --all

Exit code: 1 -- correct before anything is edited: all three labs are
"not repaired", each control still broken exactly as documented.

```text
repair validation: does your broken.py pass every strict check yet?
========================================================================

audio
------------------------------------------------------------------------
  question: The loose question -- which song? -- already has the right answer. Which boundary is off by one, why does a strict test see it when best_id does not, and what does that protect when your real submission returns shapes to a benchmark?

  your broken.py: 1 of 2 checks failing
    [FAIL] check_exact_alignment
           expected best score 1.0 -- all 40 clip samples aligned at offset 37 -- but got 0.975: right song, right offset, short score. Count the samples your window compares.
           keep repairing; run this again after each change

  control.py (immutable): still broken exactly as documented [ok] -- fails check_exact_alignment

  verdict: not repaired yet

grid
------------------------------------------------------------------------
  question: The first call is perfect and the second is impossible. Where does state hide between calls, and why does the capstone's Submission.__init__ say to build the database fresh every run?

  your broken.py: 2 of 3 checks failing
    [FAIL] check_input_untouched
           label_region must return a new grid, not the caller's object
    [FAIL] check_two_calls_exact
           second call (GRID_TWO): row 1 differs -- expected [0, 7, 7, 0, 0, 0, 0, 0], got [0, 3, 3, 0, 0, 0, 0, 0]
           keep repairing; run this again after each change

  control.py (immutable): still broken exactly as documented [ok] -- fails check_input_untouched, check_two_calls_exact

  verdict: not repaired yet

vector
------------------------------------------------------------------------
  question: Your caller's vectors changed while you were ranking. Who owns the normalization, what did the snapshot see that a score-only test missed, and which line repairs it?

  your broken.py: 1 of 3 checks failing
    [FAIL] check_input_untouched
           the caller's dict changed during the call: vectors['img-01'] started as [2.0, 0.0, 4.0]... and ended as [0.354, 0.0, 0.707]... -- unit-length values instead of the caller's raw ones. Who owns the normalization?
           keep repairing; run this again after each change

  control.py (immutable): still broken exactly as documented [ok] -- fails check_input_untouched

  verdict: not repaired yet

========================================================================
  audio: not repaired
  grid: not repaired
  vector: not repaired
not every lab repaired yet (exit 1)
```

## The documented repairs, applied

The repair each README walks through was applied to the three `broken.py`
files: the audio window slice extended to full length, the vector
normalization written to a local instead of through the caller's dict,
and the grid fill's `visited` set moved inside the function with the
caller's rows copied. Output:

```text
audio: documented repair applied to broken.py
vector: documented repair applied to broken.py
grid: documented repair applied to broken.py
```

## Observed transcript: validate.py --all after repairing all three

    python learning-labs/validate.py --all

Exit code: 0 -- every strict check passes on each repaired `broken.py`,
including the trap checks, while every immutable control is still
demonstrably broken.

```text
repair validation: does your broken.py pass every strict check yet?
========================================================================

audio
------------------------------------------------------------------------
  question: The loose question -- which song? -- already has the right answer. Which boundary is off by one, why does a strict test see it when best_id does not, and what does that protect when your real submission returns shapes to a benchmark?

  your broken.py: every strict check passes (2 of 2)

  control.py (immutable): still broken exactly as documented [ok] -- fails check_exact_alignment

  verdict: repaired -- every strict check passes, and the
  immutable control is still demonstrably broken

grid
------------------------------------------------------------------------
  question: The first call is perfect and the second is impossible. Where does state hide between calls, and why does the capstone's Submission.__init__ say to build the database fresh every run?

  your broken.py: every strict check passes (3 of 3)

  control.py (immutable): still broken exactly as documented [ok] -- fails check_input_untouched, check_two_calls_exact

  verdict: repaired -- every strict check passes, and the
  immutable control is still demonstrably broken

vector
------------------------------------------------------------------------
  question: Your caller's vectors changed while you were ranking. Who owns the normalization, what did the snapshot see that a score-only test missed, and which line repairs it?

  your broken.py: every strict check passes (3 of 3)

  control.py (immutable): still broken exactly as documented [ok] -- fails check_input_untouched

  verdict: repaired -- every strict check passes, and the
  immutable control is still demonstrably broken

========================================================================
  audio: repaired
  grid: repaired
  vector: repaired
every selected lab repaired (exit 0)
```

## Observed transcript: pytest after the repair

    python3 -m pytest -q learning-labs/tests

Exit code: 0 -- the suite is green after a correct repair, as it was
before it. It tests the pinned controls and the references, never the
student file.

```text
....................                                                     [100%]
20 passed in 0.06s
```

## Observed transcript: run.py --all after the repair (tail)

    python learning-labs/run.py --all

Exit code: 0. The tour is stable: every lesson still intact, and the
per-lab summary now reports the student state informationally.

```text
  confirms it: python learning-labs/validate.py --lab vector

========================================================================
  audio: intact; broken.py: passes all checks
  grid: intact; broken.py: passes all checks
  vector: intact; broken.py: passes all checks
every lesson intact (exit 0) -- prove your repair with:
    python learning-labs/validate.py --all
```

## Restore, then the gate again

    git checkout -- learning-labs/labs/audio/broken.py \
                    learning-labs/labs/vector/broken.py \
                    learning-labs/labs/grid/broken.py
    python learning-labs/validate.py --all

Exit code: 1 -- back to the shipped state, the gate reads "not repaired"
for all three labs again, same as step one (tail shown).

```text

  verdict: not repaired yet

========================================================================
  audio: not repaired
  grid: not repaired
  vector: not repaired
not every lab repaired yet (exit 1)
```

## Control digests, after the whole workflow

    sha256sum learning-labs/labs/*/control.py

Unchanged from the values pinned in `controls.json`:

```text
366643f3d83c662c596980989db6418f2f2dabdcc0ec793f50fed1e652d55333  audio/control.py
f5ce0938d2de972374d7ebd548c61e4a4b548dfae3f38093430c754f76dcd1fc  grid/control.py
ef46c41365e9175439ac595fdb0b80129a346018ec720c1059b48b0ce68373c4  vector/control.py
```
