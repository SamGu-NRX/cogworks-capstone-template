"""Contract tests for the preflight result taxonomy.

These run the preflight core over synthetic adapters (never the repo's own
week code, except where the starter's expected behaviour is the subject) and
pin the meaning of every verdict plus the baseline refusal counts.
"""

from conftest import build_manifests, check, only

# The pristine template refuses every modality: all three submission.py files
# raise NotImplementedError from their constructors. These counts are the
# committed baseline; a change here means someone touched the starter or the
# taxonomy, and the diff should say which.
EXPECTED_BASELINE = {
    "modalities": 4,
    "ok": 0,
    "missing": 4,
    "invalid": 0,
    "unexercised": 0,
    "load_error": 0,
    "refusals": 4,
}


def test_real_starter_refusal_counts(real_repo_root, manifests):
    receipt = check.run_preflight(real_repo_root, manifests)
    assert receipt["counts"] == EXPECTED_BASELINE
    assert all(entry["verdict"] == "missing" for entry in receipt["results"])
    for entry in receipt["results"]:
        assert entry["refusal"] is True
        construct = next(s for s in entry["steps"] if s["method"] == "construct")
        assert construct["status"] == "missing"
        assert "NotImplementedError" in construct["detail"]


def test_stub_synthetic_repo_matches_baseline(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "stub", "week2": "stub", "week3": "stub"})
    receipt = check.run_preflight(root, manifests)
    assert receipt["counts"] == EXPECTED_BASELINE


def test_working_adapters_all_ok(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "valid", "week2": "valid", "week3": "valid"})
    receipt = check.run_preflight(root, manifests)
    counts = receipt["counts"]
    assert counts == {
        "modalities": 4,
        "ok": 4,
        "missing": 0,
        "invalid": 0,
        "unexercised": 0,
        "load_error": 0,
        "refusals": 0,
    }
    for entry in receipt["results"]:
        assert entry["refusal"] is False
        assert "not a score" in entry["next_action"]


def test_invalid_output_is_not_missing(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "invalid", "week2": "valid", "week3": "valid"})
    receipt = check.run_preflight(root, manifests)
    audio = only(receipt, "audio-identification")
    assert audio["verdict"] == "invalid"
    assert audio["refusal"] is True
    identify = next(s for s in audio["steps"] if s["method"] == "identify")
    assert identify["status"] == "invalid"
    assert "returned int" in identify["detail"]
    enroll = next(s for s in audio["steps"] if s["method"] == "enroll")
    assert enroll["status"] == "ok"
    assert "fix identify()" in audio["next_action"]


def test_recognize_length_mismatch_is_invalid(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "valid", "week2": "recog_invalid", "week3": "valid"})
    receipt = check.run_preflight(root, manifests)
    recognition = only(receipt, "vision-recognition")
    assert recognition["verdict"] == "invalid"
    assert "one answer per image" in recognition["next_action"]
    clustering = only(receipt, "vision-clustering")
    assert clustering["verdict"] == "ok"


def test_seed_instability_is_invalid(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "valid", "week2": "cluster_unstable", "week3": "valid"})
    receipt = check.run_preflight(root, manifests)
    clustering = only(receipt, "vision-clustering")
    assert clustering["verdict"] == "invalid"
    assert "same seed" in clustering["next_action"]


def test_nonimplementerror_crash_is_invalid(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "valid", "week2": "valid", "week3": "keyerror"})
    receipt = check.run_preflight(root, manifests)
    language = only(receipt, "language-search")
    assert language["verdict"] == "invalid"
    embed_text = next(s for s in language["steps"] if s["method"] == "embed_text")
    assert embed_text["status"] == "invalid"
    assert embed_text["detail"].startswith("raised KeyError")
    assert "fix embed_text()" in language["next_action"]


def test_partial_implementation_is_missing(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "valid", "week2": "valid", "week3": "partial"})
    receipt = check.run_preflight(root, manifests)
    language = only(receipt, "language-search")
    assert language["verdict"] == "missing"
    by_method = {s["method"]: s["status"] for s in language["steps"]}
    assert by_method["embed_text"] == "ok"
    assert by_method["embed_images"] == "missing"
    assert by_method["d_consistency"] == "blocked"
    # prepare_database calls the unimplemented embed_images internally, so it
    # fails too, and search is never exercised.
    assert by_method["prepare_database"] == "missing"
    assert by_method["search"] == "blocked"
    assert "implement embed_images()" in language["next_action"]


def test_missing_factory_is_missing(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "no_factory", "week2": "valid", "week3": "valid"})
    receipt = check.run_preflight(root, manifests)
    audio = only(receipt, "audio-identification")
    assert audio["verdict"] == "missing"
    assert "no callable create_submission()" in audio["steps"][0]["detail"]


def test_import_failure_is_load_error(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "unimportable", "week2": "valid", "week3": "valid"})
    receipt = check.run_preflight(root, manifests)
    audio = only(receipt, "audio-identification")
    assert audio["verdict"] == "load_error"
    assert audio["refusal"] is True
    assert "import cleanly" in audio["next_action"]
    counts = receipt["counts"]
    assert counts["load_error"] == 1 and counts["refusals"] == 1


def test_malformed_manifest_is_unexercised_not_invalid(synthetic_repo, tmp_path):
    root = synthetic_repo({"week1": "stub", "week2": "stub", "week3": "valid"})
    fixtures = build_manifests(tmp_path / "fixtures")
    path = fixtures / "language-search" / "manifest.json"
    corrupt = path.read_text().replace('"k": 2', '"k": 9')  # k > pool size
    path.write_text(corrupt)
    receipt = check.run_preflight(root, fixtures)
    language = only(receipt, "language-search")
    assert language["verdict"] == "unexercised"
    assert language["refusal"] is False  # untested is reported, never a refusal
    assert "malformed fixture" in language["steps"][0]["detail"]
    assert "language-search/manifest.json" in language["next_action"]
    counts = receipt["counts"]
    # week2 stubs refuse both of its modalities: 3 missing, 1 unexercised.
    assert counts["missing"] == 3 and counts["unexercised"] == 1
    assert counts["refusals"] == 3


def test_missing_manifest_is_unexercised(synthetic_repo, tmp_path):
    root = synthetic_repo({"week1": "valid", "week2": "valid", "week3": "valid"})
    fixtures = build_manifests(tmp_path / "fixtures")
    (fixtures / "audio-identification" / "manifest.json").unlink()
    receipt = check.run_preflight(root, fixtures)
    audio = only(receipt, "audio-identification")
    assert audio["verdict"] == "unexercised"
    assert "no fixture manifest" in audio["steps"][0]["detail"]


def test_identify_alternate_accepted_shapes(synthetic_repo, manifests):
    for behaviour in ("bare_id", "triples"):
        root = synthetic_repo({"week1": behaviour, "week2": "stub", "week3": "stub"})
        receipt = check.run_preflight(root, manifests, weeks=("week1",))
        audio = only(receipt, "audio-identification")
        assert audio["verdict"] == "ok", (behaviour, audio["steps"])


def test_deselected_weeks_are_omitted(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "valid", "week2": "stub", "week3": "stub"})
    receipt = check.run_preflight(root, manifests, weeks=("week1",))
    assert [entry["benchmark"] for entry in receipt["results"]] == ["audio-identification"]
    assert receipt["counts"]["modalities"] == 1


def test_dependency_identity_records_adapter_imports(synthetic_repo, manifests):
    root = synthetic_repo({"week1": "valid", "week2": "valid", "week3": "valid"})
    receipt = check.run_preflight(root, manifests)
    assert receipt["dependency_identity"]["numpy"] != "not installed"


def test_source_identity_pins_adapter_files(real_repo_root, manifests):
    receipt = check.run_preflight(real_repo_root, manifests)
    files = receipt["source_identity"]["files"]
    assert sorted(files) == [
        "week1/submission.py",
        "week2/submission.py",
        "week3/submission.py",
    ]
    assert all(len(digest) == 64 for digest in files.values())
    commit = receipt["source_identity"]["git_commit"]
    assert commit is None or (len(commit) == 40 and all(c in "0123456789abcdef" for c in commit))
    assert receipt["interpreter_identity"]["implementation"] == "cpython"
    assert receipt["benchmark_stack"]["status"] in ("installed", "not-installed")


def test_receipt_is_json_serializable_and_sorted(real_repo_root, manifests):
    import json

    receipt = check.run_preflight(real_repo_root, manifests)
    payload = json.dumps(receipt, indent=2, sort_keys=True)
    assert '"receipt_version": 1' in payload
    assert str(real_repo_root) not in payload  # no absolute paths leak
