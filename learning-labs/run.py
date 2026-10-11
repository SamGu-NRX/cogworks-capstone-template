#!/usr/bin/env python3
"""The lesson tour for the practice labs.

    python learning-labs/run.py --all
    python learning-labs/run.py --lab audio     (or vector, grid)
    cd learning-labs && python run.py --all     (also works)

For each lab it prints the experimental question, a BEFORE block (every
check in the lab's LESSON manifest run against your broken.py, the file
you are invited to edit), the same checks against reference.py (OUR
repair, for diffing after yours works), and the behavior of the lab's
immutable control.py, which must stay broken exactly as documented.

Two things are deliberately decoupled here:

- The verdict "lesson intact" describes the FIXED side of the lesson:
  control.py fails exactly as the manifest says and reference.py passes
  everything. Your edits to broken.py can never flip this verdict.
- Whether YOUR broken.py passes yet is reported as state, not judged.
  The command that grades your repair is validate.py:

    python learning-labs/validate.py --all

The exit code is 0 iff every selected lesson is intact (the fixed-side
property, stable under any student edit). Plain text. No network, no
telemetry, no record of who ran this. Paths resolve from this file's
location, never from the current directory.
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
from labs.audio import reference as audio_reference
from labs.grid import broken as grid_broken
from labs.grid import checks as grid_checks
from labs.grid import control as grid_control
from labs.grid import reference as grid_reference
from labs.vector import broken as vector_broken
from labs.vector import checks as vector_checks
from labs.vector import control as vector_control
from labs.vector import reference as vector_reference

from validate import control_problems, failing_checks

LABS = (
    (
        "audio",
        audio_checks,
        audio_reference.match_clip,
        audio_broken.match_clip,
        audio_control.match_clip,
    ),
    (
        "grid",
        grid_checks,
        grid_reference.label_region,
        grid_broken.label_region,
        grid_control.label_region,
    ),
    (
        "vector",
        vector_checks,
        vector_reference.rank_by_similarity,
        vector_broken.rank_by_similarity,
        vector_control.rank_by_similarity,
    ),
)

WIDTH = 72


def _student_block(checks, broken) -> int:
    """Run every manifest check against the student's broken.py and print
    what happens. Strictly informational: this is the tour of the shipped
    defect, and it must read the same before a repair and after one.
    Returns the number of failing checks."""
    print("  BEFORE -- your broken.py, as it stands")
    failures = failing_checks(checks, broken)
    messages = dict(failures)
    documented = {name for name, passes in checks.LESSON if not passes}
    traps = {name for name, passes in checks.LESSON if passes}
    for name, _broken_passes in checks.LESSON:
        if name in messages:
            print(f"    [FAIL] {name}")
            for line in messages[name].splitlines():
                print(f"           {line}")
            if name in documented:
                print("           the documented defect -- this is your target")
            else:
                print("           your edit broke a check that used to pass -- intended?")
        else:
            print(f"    [pass] {name}")
            if name in traps:
                print("           still passes -- the trap")
    print(f"  state: {len(failures)} of {len(checks.LESSON)} checks failing")
    return len(failures)


def _reference_block(checks, reference) -> bool:
    """Run every check against reference.py; True iff it passes everything.
    This is OUR repair -- the student's AFTER comes from validate.py."""
    print("  reference.py -- OUR repair, for diffing after yours works")
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


def _control_block(checks, control) -> bool:
    """Print the immutable control's observed behavior; True iff it fails
    exactly its documented checks and passes exactly its traps."""
    print("  control.py (immutable) -- must stay broken exactly as documented")
    problems = control_problems(checks, control)
    if problems:
        for problem in problems:
            print(f"    [DRIFT] {problem}")
        print("           the fixed side of the lesson must never move")
        return False
    for name, broken_passes in checks.LESSON:
        marker = "[pass]" if broken_passes else "[FAIL]"
        note = "as documented (the trap)" if broken_passes else "as documented"
        print(f"    {marker} {name}  {note}")
    print("    [ok] the control behaves exactly as the LESSON manifest says")
    return True


def _run_lab(name, checks, reference, broken, control) -> tuple[bool, int]:
    print(name)
    print("-" * WIDTH)
    print(f"  question: {checks.QUESTION}")
    print()
    failing = _student_block(checks, broken)
    print()
    reference_ok = _reference_block(checks, reference)
    print()
    control_ok = _control_block(checks, control)
    print()
    if control_ok and reference_ok:
        print("  verdict: lesson intact -- the immutable control fails exactly")
        print("  as documented and reference.py passes every check. Your")
        print("  edits to broken.py cannot change this verdict.")
        if failing:
            print(f"  your move: repair labs/{name}/broken.py, then prove it:")
            print(f"    python learning-labs/validate.py --lab {name}")
        else:
            print("  your broken.py already passes every check -- validate.py")
            print(f"  confirms it: python learning-labs/validate.py --lab {name}")
        intact = True
    else:
        print("  verdict: lesson broken -- the fixed side of the lesson")
        print("  (control.py, reference.py) has drifted from the manifest")
        intact = False
    print()
    return intact, failing


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Tour the practice labs: watch the strict checks fail on "
        "the shipped defect, pass on our reference, then repair broken.py "
        "and prove it with validate.py."
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
    for lab_name, _checks, _reference, _broken, _control in selected:
        intact, failing = results[lab_name]
        state = "intact" if intact else "BROKEN"
        student = (
            "passes all checks" if failing == 0 else f"{failing} check(s) failing"
        )
        print(f"  {lab_name}: {state}; broken.py: {student}")
    if all(intact for intact, _failing in results.values()):
        print("every lesson intact (exit 0) -- prove your repair with:")
        print("    python learning-labs/validate.py --all")
        return 0
    print("not every lesson intact (exit 1)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
