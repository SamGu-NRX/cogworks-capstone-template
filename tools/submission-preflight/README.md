# Submission preflight

A local, offline check of the seam between your code and the capstone
benchmark: it loads each week's `submission.py`, calls the documented
factory, and exercises the documented entrypoints on tiny synthetic
fixtures. It never scores you.

## Run it

```bash
python tools/submission-preflight/check.py --week all          # human-readable report
python tools/submission-preflight/check.py --week week1        # one benchmark
python tools/submission-preflight/check.py --json receipt.json # machine receipt
python tools/submission-preflight/check.py --init-fixtures DIR # regenerate fixtures
python -m pytest -q tools/submission-preflight/tests           # the tool's own tests
```

Default fixtures live in `fixtures/` and are fully synthetic (sine waves,
4x4 pattern images, pseudo-descriptors) — nothing to download, nothing
personal.

## What the verdicts mean

| Verdict        | Meaning                                                                 | Counts as a refusal? |
|----------------|-------------------------------------------------------------------------|----------------------|
| `ok`           | Ran on the fixtures; every output matched the documented contract.       | no                   |
| `missing`      | The implementation is not there: `NotImplementedError` stub, absent factory, absent method. | yes |
| `invalid`      | It ran, but the output violates the contract (wrong shape, wrong count, not seed-stable, non-`NotImplementedError` crash). | yes |
| `unexercised`  | The preflight could not test this modality (fixture manifest missing or malformed). Reported, never a refusal. | no |
| `load_error`   | The module does not even import.                                        | yes                  |

`ok` is **not a score**: it means the seam holds, not that accuracy is good.
Accuracy is measured only by `cogworks run` on an approved benchmark
install. Importing cleanly is also not enough — the starter stubs import
cleanly by design.

The pristine template reads `4 modalities, 4 refusals` (all `missing`).
That is the expected starting state; make it move as you implement.

## The receipt

`--json` writes a deterministic receipt: same tree, same interpreter, same
fixtures → byte-identical JSON. It records which adapter files were hashed
(`source_identity`), the interpreter and third-party imports
(`interpreter_identity`, `dependency_identity`), per-fixture hashes
(`fixture_identity`), and per-modality steps with one actionable
`next_action` each. Two receipts that differ tell you *what* changed, not
just that something did.

## Adding or changing a fixture

Edit `build_default_fixtures()` in `check.py` (single source of truth),
regenerate with `--init-fixtures tools/submission-preflight/fixtures`, and
commit. The tests pin regeneration as byte-stable, so a fixture change is
always a visible diff. Malformed fixtures are a first-class outcome
(`unexercised`), so a bad hand-edit can never masquerade as a code verdict.
