"""Lesson-integrity meta-tests.

The integrity of a lesson has two fixed sides, and neither of them is the
file the student edits:

- ``control.py`` is the immutable, deliberately broken implementation. Its
  bytes are pinned in ``learning-labs/controls.json`` (sha256) and its
  BEHAVIOR must match the lab's LESSON manifest exactly: fail exactly the
  documented checks, pass exactly the traps. The lesson cannot silently
  stop teaching, no matter what happens to broken.py.
- ``reference.py`` must pass every check.

Nothing here asserts anything about ``broken.py`` as the student leaves
it: that file is the student's to edit, and the suite must stay green at
every step of a repair. The check that grades a repair is
``python learning-labs/validate.py`` (exit 0 = every strict check passes
on the student file while every control stays demonstrably broken). The
regressions below exercise that exact workflow on a pristine copy of the
shipped defect (the hash-pinned control.py), so every claim here is
independent of the student's broken.py and the suite stays green at
every step of a real repair.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

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

LABS_ROOT = Path(__file__).resolve().parents[1]
CONTROLS = json.loads((LABS_ROOT / "controls.json").read_text(encoding="utf-8"))

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

FUNCTION_NAMES = {
    "audio": "match_clip",
    "grid": "label_region",
    "vector": "rank_by_similarity",
}

# The canonical repair per lab, as exact old -> new source replacements on
# broken.py. Keep in sync with the "## The repair" section of each lab's
# README: these pairs ARE the documented repair, in executable form.
CANONICAL_REPAIRS: dict[str, tuple[tuple[str, str], ...]] = {
    "audio": (
        (
            "            window = song[offset:offset + len(clip) - 1]  # one sample short",
            "            window = song[offset:offset + len(clip)]",
        ),
    ),
    "vector": (
        (
            "        vectors[item_id] = [x / norm for x in vector]  # THE BUG: caller's dict\n"
            "        score = sum(a * b for a, b in zip(vectors[item_id], unit_query))",
            "        unit_vector = [x / norm for x in vector]\n"
            "        score = sum(a * b for a, b in zip(unit_vector, unit_query))",
        ),
    ),
    "grid": (
        (
            "_visited: set[tuple[int, int]] = set()  # THE BUG: module level, never cleared\n\n\ndef label_region(",
            "\ndef label_region(",
        ),
        (
            "    target = grid[start[0]][start[1]]\n\n    stack = [start]",
            "    out = [row[:] for row in grid]\n"
            "    visited: set[tuple[int, int]] = set()\n"
            "    target = out[start[0]][start[1]]\n\n    stack = [start]",
        ),
        (
            "        if grid[r][c] != target:\n"
            "            continue\n"
            "        grid[r][c] = label  # THE BUG: writes into the caller's grid\n"
            "        if (r, c) in _visited:\n"
            "            continue  # stale state: the fill dies here, quietly\n"
            "        _visited.add((r, c))",
            "        if out[r][c] != target:\n"
            "            continue\n"
            "        out[r][c] = label\n"
            "        if (r, c) in visited:\n"
            "            continue\n"
            "        visited.add((r, c))",
        ),
        ("        if r + 1 < len(grid):", "        if r + 1 < len(out):"),
        ("        if c + 1 < len(grid[0]):", "        if c + 1 < len(out[0]):"),
        ("    return grid", "    return out"),
    ),
}


def test_reference_passes_every_check():
    for lab, checks, reference, _broken, _control in LABS:
        assert failing_checks(checks, reference) == [], (
            f"{lab}: reference.py must pass every check in its LESSON manifest"
        )


def test_control_behaves_exactly_as_documented():
    for lab, checks, _reference, _broken, control in LABS:
        problems = control_problems(checks, control)
        assert problems == [], (lab, problems)


def test_control_files_are_immutable():
    assert set(CONTROLS) == {"audio", "grid", "vector"}, (
        f"controls.json must pin all three labs, got {sorted(CONTROLS)}"
    )
    for lab, expected in sorted(CONTROLS.items()):
        control_path = LABS_ROOT / "labs" / lab / "control.py"
        digest = hashlib.sha256(control_path.read_bytes()).hexdigest()
        assert digest == expected, (
            f"labs/{lab}/control.py changed on disk. The control is the "
            "immutable, deliberately broken copy the integrity tests watch; "
            "restore it with git checkout -- learning-labs/labs/"
            f"{lab}/control.py and edit broken.py instead -- that file is yours."
        )


def test_validator_rejects_the_broken_implementation():
    """validate.py must report exactly the documented failures for a broken
    implementation. Proven against control.py -- the pristine, immutable
    copy of the shipped defect -- so this regression says nothing about
    whatever state the student's broken.py is in today."""
    for lab, checks, _reference, _broken, control in LABS:
        failing = {name for name, _message in failing_checks(checks, control)}
        documented = {name for name, passes in checks.LESSON if not passes}
        assert failing == documented, (
            f"{lab}: the validator reports {sorted(failing)} for the broken "
            f"implementation; the LESSON manifest says {sorted(documented)}"
        )


def test_documented_repair_makes_a_broken_copy_pass(tmp_path):
    """Regression for the actual repair workflow: start from the pristine
    broken implementation (a temp copy of control.py -- byte-identical to
    the shipped defect, and hash-pinned, so this test is independent of
    the student's broken.py), apply the documented repair to the copy, and
    the validator must accept the result: every strict check passing,
    while control.py itself stays demonstrably broken."""
    for lab, checks, _reference, _broken, control in LABS:
        source = (LABS_ROOT / "labs" / lab / "control.py").read_text(
            encoding="utf-8"
        )
        for old, new in CANONICAL_REPAIRS[lab]:
            count = source.count(old)
            assert count == 1, (
                f"{lab}: the documented repair targets this line exactly "
                f"once in control.py, found {count}: {old!r} (are "
                f"labs/{lab}/README.md and the CANONICAL_REPAIRS pairs "
                "still in sync with the pinned control?)"
            )
            source = source.replace(old, new)

        module = _module_from_source(f"labs_{lab}_repaired", source, tmp_path)
        impl = getattr(module, FUNCTION_NAMES[lab])
        assert failing_checks(checks, impl) == [], (
            f"{lab}: the documented repair, applied to a pristine copy of "
            "the broken implementation, must pass every strict check -- "
            "validate.py would exit 0 for this repair"
        )


def _module_from_source(name: str, source: str, tmp_path: Path) -> ModuleType:
    path = tmp_path / f"{name}.py"
    path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
