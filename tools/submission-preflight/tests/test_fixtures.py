"""Tests for the shipped fixtures and the CLI surface.

The shipped fixtures under ``tools/submission-preflight/fixtures/`` are the
manifests the preflight uses by default. These tests pin that they exist,
validate against the schema, are byte-stable when regenerated, and that the
CLI flags behave (init-fixtures is non-destructive; --json is deterministic
and leaks no absolute paths).
"""

import json
import subprocess
import sys
from pathlib import Path

from conftest import check, only

TOOL_DIR = Path(__file__).resolve().parents[1]
SHIPPED_FIXTURES = TOOL_DIR / "fixtures"

BENCHMARKS = ["audio-identification", "vision-recognition", "vision-clustering", "language-search"]


def test_shipped_fixtures_exist_and_validate():
    for benchmark in BENCHMARKS:
        path = SHIPPED_FIXTURES / benchmark / "manifest.json"
        assert path.is_file(), "missing shipped fixture: " + benchmark
        loaded = check.load_manifest(path, benchmark)  # raises MalformedFixture
        assert isinstance(loaded, dict), benchmark


def test_shipped_fixtures_are_byte_stable(tmp_path):
    written = check.build_default_fixtures(tmp_path / "regen")
    assert len(written) == 4
    for benchmark in BENCHMARKS:
        original = (SHIPPED_FIXTURES / benchmark / "manifest.json").read_text()
        assert (tmp_path / "regen" / benchmark / "manifest.json").read_text() == original, benchmark


def test_shipped_fixtures_drive_the_real_starter(real_repo_root):
    receipt = check.run_preflight(real_repo_root, SHIPPED_FIXTURES)
    assert receipt["counts"] == {
        "modalities": 4,
        "ok": 0,
        "missing": 4,
        "invalid": 0,
        "unexercised": 0,
        "load_error": 0,
        "refusals": 4,
    }
    for benchmark in BENCHMARKS:
        assert only(receipt, benchmark)["verdict"] == "missing"


def test_init_fixtures_is_non_destructive(tmp_path):
    target = tmp_path / "fx"
    check.build_default_fixtures(target)
    tampered = target / "audio-identification" / "manifest.json"
    tampered.write_text("{}")  # simulate a teammate's local edit
    check.build_default_fixtures(target)  # must not overwrite
    assert json.loads(tampered.read_text()) == {}


def test_cli_init_fixtures_and_check_run(real_repo_root, tmp_path):
    fresh = tmp_path / "fresh-fx"
    result = subprocess.run(
        [sys.executable, str(TOOL_DIR / "check.py"), "--repo-root", str(real_repo_root), "--init-fixtures", str(fresh)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert (fresh / "language-search" / "manifest.json").is_file()

    # a full run against the shipped fixtures with a JSON receipt
    receipt_path = tmp_path / "receipt.json"
    result = subprocess.run(
        [sys.executable, str(TOOL_DIR / "check.py"), "--repo-root", str(real_repo_root), "--json", str(receipt_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1  # starter refuses everything: exit 1, not a crash
    assert "4 refusals" in result.stdout
    receipt = json.loads(receipt_path.read_text())
    assert receipt["counts"]["refusals"] == 4
    assert str(real_repo_root) not in receipt_path.read_text()


def test_cli_json_receipt_is_deterministic(real_repo_root, tmp_path):
    outs = []
    for run in ("a", "b"):
        path = tmp_path / ("receipt-{}.json".format(run))
        result = subprocess.run(
            [sys.executable, str(TOOL_DIR / "check.py"), "--repo-root", str(real_repo_root), "--json", str(path)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, result.stdout
        outs.append(path.read_text())
    assert outs[0] == outs[1]


def test_cli_week_selection(real_repo_root, tmp_path):
    result = subprocess.run(
        [sys.executable, str(TOOL_DIR / "check.py"), "--repo-root", str(real_repo_root), "--week", "week1"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "1 modality" in result.stdout
    assert "language-search" not in result.stdout

    bad = subprocess.run(
        [sys.executable, str(TOOL_DIR / "check.py"), "--repo-root", str(real_repo_root), "--week", "week9"],
        capture_output=True,
        text=True,
    )
    assert bad.returncode == 2  # usage error
    assert "unknown week" in bad.stderr
