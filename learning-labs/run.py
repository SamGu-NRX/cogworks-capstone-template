#!/usr/bin/env python3
"""The lesson runner for the practice labs.

    python learning-labs/run.py --all
    python learning-labs/run.py --lab audio     (or vector, grid)
    cd learning-labs && python run.py --all     (also works)

For each lab it prints the lab's experimental question, then runs every
check in the lab's LESSON manifest twice: once against broken.py (the
BEFORE block) and once against reference.py (the AFTER block). A lab's
lesson is intact when broken.py fails exactly the checks the manifest says
it fails, passes exactly the ones it says it passes, and reference.py
passes everything. The exit code is 0 iff every selected lesson is intact.

Plain text. No network, no telemetry, no record of who ran this.
Paths resolve from this file's location, never from the current directory.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

LABS_ROOT = Path(__file__).resolve().parent
if str(LABS_ROOT) not in sys.path:
    sys.path.insert(0, str(LABS_ROOT))

from labs.audio import broken as audio_broken
from labs.audio import checks as audio_checks
from labs.audio import reference as audio_reference
from labs.grid import broken as grid_broken
from labs.grid import checks as grid_checks
from labs.grid import reference as grid_reference
from labs.vector import broken as vector_broken
from labs.vector import checks as vector_checks
from labs.vector import reference as vector_reference

LABS = (
    ("audio", audio_checks, audio_reference.match_clip, audio_broken.match_clip),
    ("grid", grid_checks, grid_reference.label_region, grid_broken.label_region),
    (
        "vector",
        vector_checks,
        vector_reference.rank_by_similarity,
        vector_broken.rank_by_similarity,
    ),
)

WIDTH = 72


def _before_block(checks, broken) -> bool:
    """Run every check against broken.py; True iff it behaved as documented."""
    print("  BEFORE -- broken.py (the version you must repair)")
    behaved = True
    for name, broken_passes in checks.LESSON:
        check = getattr(checks, name)
        failure_message = None
        try:
            check(broken)
            passed = True
        except AssertionError as failure:
            passed = False
            failure_message = str(failure).strip() or "(assertion with no message)"

        if passed and broken_passes:
            print(f"    [pass] {name}")
            print("           still passes -- the trap, as documented")
        elif not passed and not broken_passes:
            print(f"    [FAIL] {name}")
            for line in failure_message.splitlines():
                print(f"           {line}")
            print("           fails as documented")
        else:
            behaved = False
            print(f"    [{'pass' if passed else 'FAIL'}] {name}")
            print(
                f"           UNEXPECTED: the manifest says broken.py should "
                f"{'pass' if broken_passes else 'fail'} this -- the lesson has drifted"
            )
    return behaved


def _after_block(checks, reference) -> bool:
    """Run every check against reference.py; True iff it passes everything."""
    print("  AFTER -- reference.py (a working version, for comparison)")
    passed_all = True
    for name, _broken_passes in checks.LESSON:
        check = getattr(checks, name)
        try:
            check(reference)
            print(f"    [pass] {name}")
        except AssertionError as failure:
            passed_all = False
            message = str(failure).strip() or "(assertion with no message)"
            print(f"    [FAIL] {name}")
            for line in message.splitlines():
                print(f"           {line}")
            print("           the reference must pass every check")
    return passed_all


def _run_lab(name, checks, reference, broken) -> bool:
    print(name)
    print("-" * WIDTH)
    print(f"  question: {checks.QUESTION}")
    print()
    before_ok = _before_block(checks, broken)
    print()
    after_ok = _after_block(checks, reference)
    print()
    if before_ok and after_ok:
        print("  verdict: lesson intact -- broken.py fails exactly as")
        print("  documented and reference.py passes every check")
        intact = True
    else:
        print("  verdict: lesson broken -- see the UNEXPECTED or [FAIL] lines")
        print("  above; broken.py and reference.py must behave as the")
        print("  manifest in checks.py says")
        intact = False
    print()
    return intact


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the practice labs: watch the strict checks fail on "
        "broken.py, pass on reference.py, and repair from there."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="run every lab")
    group.add_argument(
        "--lab", choices=["audio", "vector", "grid"], help="run one lab"
    )
    args = parser.parse_args(argv)

    if args.lab is not None:
        selected = [entry for entry in LABS if entry[0] == args.lab]
    else:  # no flags at all means all of them, same as --all
        selected = list(LABS)

    print("learning-labs: practice labs for testing a capstone interface")
    print("=" * WIDTH)
    print()

    results = {entry[0]: _run_lab(*entry) for entry in selected}

    print("=" * WIDTH)
    for lab_name, _checks, _reference, _broken in selected:
        state = "intact" if results[lab_name] else "BROKEN"
        print(f"  {lab_name}: {state}")
    if all(results.values()):
        print("every lesson intact (exit 0)")
        return 0
    print("not every lesson intact (exit 1)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
