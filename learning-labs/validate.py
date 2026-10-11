#!/usr/bin/env python3
"""Repair validation for the practice labs: did YOUR repair land?

    python learning-labs/validate.py --all
    python learning-labs/validate.py --lab audio   (or vector, grid)
    cd learning-labs && python validate.py --lab audio   (also works)

For each selected lab it runs every strict check in the lab's LESSON
manifest against your broken.py -- the file you are invited to edit -- and
then checks that the lab's immutable control.py still fails exactly the
checks it is supposed to fail. Exit code:

  0   every selected lab's broken.py passes every strict check, and every
      control is still demonstrably broken. Your repair is proven.
  1   your broken.py still fails at least one strict check. The failing
      checks and their messages are printed; keep repairing.
  2   a control.py no longer behaves exactly as its manifest documents --
      the fixed side of the lesson has been tampered with. Restore it:
      git checkout -- learning-labs/labs/<lab>/control.py

run.py is the tour; this is the gate. pytest never looks at your
broken.py, so the suite stays green at every step of your repair -- this
command is the check that flips.

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
from labs.audio import control as audio_control
from labs.grid import broken as grid_broken
from labs.grid import checks as grid_checks
from labs.grid import control as grid_control
from labs.vector import broken as vector_broken
from labs.vector import checks as vector_checks
from labs.vector import control as vector_control

LABS = (
    ("audio", audio_checks, audio_broken.match_clip, audio_control.match_clip),
    ("grid", grid_checks, grid_broken.label_region, grid_control.label_region),
    (
        "vector",
        vector_checks,
        vector_broken.rank_by_similarity,
        vector_control.rank_by_similarity,
    ),
)

WIDTH = 72


def failing_checks(checks, impl) -> list[tuple[str, str]]:
    """Run every manifest check against impl; return (name, message) pairs
    for every failure. Used by validate.py, run.py, and the pytest suite,
    so "passes every strict check" has exactly one meaning."""
    failures: list[tuple[str, str]] = []
    for name, _broken_passes in checks.LESSON:
        check = getattr(checks, name)
        try:
            check(impl)
        except AssertionError as failure:
            message = str(failure).strip() or "(assertion with no message)"
            failures.append((name, message))
    return failures


def control_problems(checks, control) -> list[str]:
    """Empty iff the control fails exactly the documented checks and passes
    exactly the traps. Anything else means the fixed side of the lesson
    has been tampered with."""
    problems: list[str] = []
    for name, broken_passes in checks.LESSON:
        check = getattr(checks, name)
        try:
            check(control)
            passed = True
        except AssertionError:
            passed = False
        if passed != broken_passes:
            observed = "passed" if passed else "failed"
            expected = "pass" if broken_passes else "fail"
            problems.append(
                f"{name}: the immutable control {observed} but the "
                f"LESSON manifest says it must {expected}"
            )
    return problems


def _control_line(checks, control) -> bool:
    """Print the control's observed behavior; True iff it is intact-broken."""
    problems = control_problems(checks, control)
    if problems:
        for problem in problems:
            print(f"  control.py (immutable): TAMPERED -- {problem}")
        print(
            "             restore it: git checkout -- "
            "learning-labs/labs/<lab>/control.py"
        )
        return False
    documented_failures = [
        name for name, broken_passes in checks.LESSON if not broken_passes
    ]
    print(
        "  control.py (immutable): still broken exactly as documented [ok]"
        f" -- fails {', '.join(documented_failures)}"
    )
    return True


def _validate_lab(name, checks, broken, control) -> tuple[bool, bool]:
    """Returns (repaired, control_ok)."""
    print(name)
    print("-" * WIDTH)
    print(f"  question: {checks.QUESTION}")
    print()

    failures = failing_checks(checks, broken)
    total = len(checks.LESSON)
    if failures:
        print(f"  your broken.py: {len(failures)} of {total} checks failing")
        for check_name, message in failures:
            print(f"    [FAIL] {check_name}")
            for line in message.splitlines():
                print(f"           {line}")
        print("           keep repairing; run this again after each change")
    else:
        print(f"  your broken.py: every strict check passes ({total} of {total})")
    print()

    control_ok = _control_line(checks, control)
    print()

    if failures:
        print("  verdict: not repaired yet")
    elif control_ok:
        print("  verdict: repaired -- every strict check passes, and the")
        print("  immutable control is still demonstrably broken")
    else:
        print("  verdict: your file passes, but the control is tampered (exit 2)")
    print()
    return (not failures, control_ok)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Prove your repair: every strict check must pass on your "
        "broken.py while each immutable control stays demonstrably broken."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="validate every lab")
    group.add_argument(
        "--lab", choices=["audio", "vector", "grid"], help="validate one lab"
    )
    args = parser.parse_args(argv)

    if args.lab is not None:
        selected = [entry for entry in LABS if entry[0] == args.lab]
    else:  # no flags at all means all of them, same as --all
        selected = list(LABS)

    print("repair validation: does your broken.py pass every strict check yet?")
    print("=" * WIDTH)
    print()

    outcomes = {entry[0]: _validate_lab(*entry) for entry in selected}

    print("=" * WIDTH)
    any_tampered = False
    any_unrepaired = False
    for lab_name, _checks, _broken, _control in selected:
        repaired, control_ok = outcomes[lab_name]
        state = "repaired" if repaired else "not repaired"
        if not control_ok:
            any_tampered = True
            state += " -- CONTROL TAMPERED"
        elif not repaired:
            any_unrepaired = True
        print(f"  {lab_name}: {state}")

    if any_tampered:
        print("a control no longer behaves as documented (exit 2)")
        return 2
    if any_unrepaired:
        print("not every lab repaired yet (exit 1)")
        return 1
    print("every selected lab repaired (exit 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
