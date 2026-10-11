# Pytest counts (M1)

Observed on the commit that introduced the labs, from the repository root.

## Environment observed

- CPython 3.13.14 (`python --version`)
- pytest 9.0.3 (`python -m pytest --version`), stock, no plugins beyond
  pre-existing site packages (anyio/Faker, not used by these tests)
- OS: Linux

## Command

    python -m pytest -q learning-labs/tests

Run from the repository root, exactly as documented in INTERFACE.md.

## Observed output

    ..................                                                       [100%]
    18 passed in 0.24s

Exit code 0.

## What the 18 tests are

- `test_audio.py` (5): reference answers the loose question; reference
  matches the public alignment exactly; the fixture clip really is song-a
  cut at the documented offset/length; the expected alignment length is the
  whole clip; song values stay in [-1, 1].
- `test_vector.py` (5): reference matches the public ranking exactly (6 dp);
  reference returns the input ids intact; reference leaves the caller's
  data alone; the expected ranking names exactly the fixture ids; expected
  scores are distinct and in cosine range.
- `test_grid.py` (5): reference leaves the caller's grid alone; reference
  nails the first call; reference nails two sequential calls; expected
  grids match their documented region sizes; grids have the documented
  6x8 shape.
- `test_lessons.py` (3): each reference passes every check in its lab's
  LESSON manifest; each broken.py fails exactly its documented checks
  (`pytest.raises(AssertionError)`); each broken.py still passes its trap
  checks (the loose/trap passes the lesson depends on).

Verbose listing of the same run: 18 items, all PASSED, collected from
`learning-labs/tests/test_audio.py`, `test_grid.py`, `test_lessons.py`,
`test_vector.py`.
