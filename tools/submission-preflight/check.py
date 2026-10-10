#!/usr/bin/env python3
"""Local submission preflight for the CogWorks capstone.

What this is: a preflight for the seam between your code and the benchmark.
It loads each week's ``submission.py``, calls the documented factory, and
exercises the documented entrypoints on tiny fixtures, then reports what it
found as one of five verdicts:

    ok           ran on the fixtures and every output matched the contract
    missing      the implementation is not there (NotImplementedError stub,
                 absent factory, or absent method)
    invalid      it ran, but the output violates the documented contract
    unexercised  the preflight could not exercise this modality (fixture
                 manifest missing or malformed) -- "untested", not "broken"
    load_error   the module does not even import

What this is not: a score. The preflight never measures accuracy and never
runs the benchmark stack. Importing the module cleanly is also not enough
here -- a green import plus a NotImplementedError search tells you nothing,
because the starter stubs import cleanly by design. This tool calls the real
entrypoints on real (tiny) inputs and inspects what comes back.

The receipt it writes is deterministic: same tree, same interpreter, same
fixtures -> byte-identical JSON. It records source, interpreter and
dependency identity so a receipt shared with a teammate says exactly what
was checked.

Usage:

    python tools/submission-preflight/check.py --week all \
        --fixtures tools/submission-preflight/fixtures

Exit codes: 0 every selected modality is ok; 1 any refusal (missing,
invalid, load_error) or unexercised modality; 2 usage error.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

try:
    from importlib import metadata as _metadata
except ImportError:  # pragma: no cover - Python < 3.8
    _metadata = None

try:
    import numpy as _np
except ImportError:  # the adapters all import numpy; without it they
    _np = None  # load_error before any output validation runs.

RECEIPT_VERSION = 1
TOOL_DIR = Path(__file__).resolve().parent
DEFAULT_FIXTURES_REL = "tools/submission-preflight/fixtures"
RERUN_TEMPLATE = (
    "python tools/submission-preflight/check.py --week {week} "
    "--fixtures " + DEFAULT_FIXTURES_REL
)
DETAIL_MAX = 240

# Module names the published benchmark package could provide. Probed with
# find_spec (which does not execute anything) purely to record availability.
BENCHMARK_MODULE_CANDIDATES = ("cogbench", "cogworks_benchmark", "cogworks")

VERDICTS = ("ok", "missing", "invalid", "unexercised", "load_error")
# A refusal means "this modality cannot be submitted yet". An unexercised
# modality was not tested at all, so it is reported separately, never
# silently treated as fine.
REFUSAL_VERDICTS = ("missing", "invalid", "load_error")

# The documented entrypoints, transcribed from the three submission.py files
# at the template's starting commit (see git log, "the CogWorks capstone
# starting point"). Three files, four factories, four benchmark modalities:
# week2 ships two benchmarks that share one submission file.
MODALITIES = (
    {
        "week": "week1",
        "benchmark": "audio-identification",
        "source": "week1/submission.py",
        "factory": "create_submission",
        "fixture": "audio-identification/manifest.json",
    },
    {
        "week": "week2",
        "benchmark": "vision-recognition",
        "source": "week2/submission.py",
        "factory": "create_recognition_submission",
        "fixture": "vision-recognition/manifest.json",
    },
    {
        "week": "week2",
        "benchmark": "vision-clustering",
        "source": "week2/submission.py",
        "factory": "create_clustering_submission",
        "fixture": "vision-clustering/manifest.json",
    },
    {
        "week": "week3",
        "benchmark": "language-search",
        "source": "week3/submission.py",
        "factory": "create_submission",
        "fixture": "language-search/manifest.json",
    },
)


class MalformedFixture(Exception):
    """A fixture manifest exists but does not describe valid inputs."""


# ---------------------------------------------------------------------------
# small deterministic helpers


def _clip(text, limit=DETAIL_MAX):
    text = " ".join(str(text).split())
    if len(text) > limit:
        text = text[: limit - 3] + "..."
    return text


def _fmt_exc(exc):
    return _clip("{}: {}".format(type(exc).__name__, exc))


def _sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path):
    return _sha256_bytes(Path(path).read_bytes())


def _display(path, repo_root):
    """Path relative to the repo when possible, else as given."""
    try:
        return Path(path).resolve().relative_to(repo_root).as_posix()
    except ValueError:
        return Path(path).as_posix()


def git_head(repo_root):
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if out.returncode != 0:
        return None
    return out.stdout.decode().strip() or None


def step(method, status, detail=""):
    return {"method": method, "status": status, "detail": _clip(detail)}


def classify_call(fn, args=(), kwargs=None):
    """Call one adapter entrypoint and classify the outcome.

    NotImplementedError is the starter stub's signature, so it means
    "missing implementation". Any other exception means the adapter ran and
    misbehaved: "invalid", with the error in the detail.
    """
    try:
        value = fn(*args, **(kwargs or {}))
    except NotImplementedError as exc:
        return "missing", "raises NotImplementedError ({})".format(exc), None
    except Exception as exc:  # noqa: BLE001 - reported, never swallowed
        return "invalid", "raised {}".format(_fmt_exc(exc)), None
    return "ok", "", value


# ---------------------------------------------------------------------------
# fixture manifests (tiny, inspectable JSON; shapes follow the contracts in
# each week's submission.py docstrings)


def _require(condition, message):
    if not condition:
        raise MalformedFixture(message)


def _numbers(values, label, low=None, high=None):
    _require(isinstance(values, list) and len(values) > 0, label + ": expected a non-empty list of numbers")
    for index, value in enumerate(values):
        _require(
            isinstance(value, (int, float)) and not isinstance(value, bool),
            "{}[{}]: expected a number, got {}".format(label, index, type(value).__name__),
        )
        value = float(value)
        _require(
            value == value and value not in (float("inf"), float("-inf")),
            "{}[{}]: expected a finite number".format(label, index),
        )
        if low is not None:
            _require(value >= low, "{}[{}]: expected >= {}".format(label, index, low))
        if high is not None:
            _require(value <= high, "{}[{}]: expected <= {}".format(label, index, high))
    return [float(v) for v in values]


def _int_list(values, label):
    _require(isinstance(values, list) and len(values) > 0, label + ": expected a non-empty list of ints")
    for index, value in enumerate(values):
        _require(
            isinstance(value, int) and not isinstance(value, bool),
            "{}[{}]: expected an int, got {}".format(label, index, type(value).__name__),
        )
    return [int(v) for v in values]


def _images(raw_images, label, shape):
    height, width, channels = shape
    per_image = height * width * channels
    _require(isinstance(raw_images, list) and raw_images, label + ": expected a non-empty list of images")
    images = []
    for index, raw in enumerate(raw_images):
        _require(isinstance(raw, dict) and "data" in raw, "{}[{}]: expected an object with a 'data' field".format(label, index))
        values = _int_list(raw["data"], "{}[{}].data".format(label, index))
        _require(
            len(values) == per_image,
            "{}[{}].data: got {} values, expected {} ({}x{}x{})".format(
                label, index, len(values), per_image, height, width, channels
            ),
        )
        images.append(values)
    return images


def _load_audio_manifest(raw):
    _require(isinstance(raw, dict), "expected a JSON object")
    _require(raw.get("version") == 1, "version: expected 1")
    _require(
        isinstance(raw.get("sample_rate"), int) and not isinstance(raw["sample_rate"], bool),
        "sample_rate: expected an int, got {}".format(type(raw.get("sample_rate")).__name__),
    )
    _require(raw["sample_rate"] > 0, "sample_rate: expected > 0")
    enroll = raw.get("enroll")
    _require(isinstance(enroll, list) and enroll, "enroll: expected a non-empty list of songs")
    songs = []
    for index, song in enumerate(enroll):
        _require(isinstance(song, dict), "enroll[{}]: expected an object".format(index))
        _require(isinstance(song.get("id"), str) and song["id"], "enroll[{}].id: expected a non-empty string".format(index))
        samples = _numbers(song.get("samples"), "enroll[{}].samples".format(index), low=-1.0, high=1.0)
        songs.append({"id": song["id"], "samples": samples})
    ids = [song["id"] for song in songs]
    _require(len(set(ids)) == len(ids), "enroll: duplicate song ids")
    queries_raw = raw.get("queries")
    _require(isinstance(queries_raw, list) and queries_raw, "queries: expected a non-empty list")
    queries = []
    for index, query in enumerate(queries_raw):
        _require(isinstance(query, dict), "queries[{}]: expected an object".format(index))
        samples = _numbers(query.get("samples"), "queries[{}].samples".format(index), low=-1.0, high=1.0)
        queries.append({"samples": samples})
    return {"sample_rate": raw["sample_rate"], "enroll": songs, "queries": queries}


def _load_image_manifest(raw, with_queries):
    _require(isinstance(raw, dict), "expected a JSON object")
    _require(raw.get("version") == 1, "version: expected 1")
    shape = raw.get("image_shape")
    _require(
        isinstance(shape, list) and len(shape) == 3 and all(isinstance(v, int) and v > 0 for v in shape),
        "image_shape: expected [height, width, 3] with positive ints",
    )
    _require(shape[2] == 3, "image_shape: expected 3 channels (RGB), got {}".format(shape[2]))
    data = {"image_shape": tuple(shape)}
    if with_queries:
        enroll = raw.get("enroll")
        _require(isinstance(enroll, list) and enroll, "enroll: expected a non-empty list of people")
        people = []
        for index, person in enumerate(enroll):
            _require(isinstance(person, dict), "enroll[{}]: expected an object".format(index))
            _require(
                isinstance(person.get("person_id"), str) and person["person_id"],
                "enroll[{}].person_id: expected a non-empty string".format(index),
            )
            people.append(
                {
                    "person_id": person["person_id"],
                    "images": _images(person.get("images"), "enroll[{}].images".format(index), tuple(shape)),
                }
            )
        ids = [p["person_id"] for p in people]
        _require(len(set(ids)) == len(ids), "enroll: duplicate person ids")
        data["enroll"] = people
        data["queries"] = _images(raw.get("queries"), "queries", tuple(shape))
    else:
        data["images"] = _images(raw.get("images"), "images", tuple(shape))
        seed = raw.get("seed")
        _require(
            isinstance(seed, int) and not isinstance(seed, bool),
            "seed: expected an int, got {}".format(type(seed).__name__),
        )
        data["seed"] = seed
    return data


def _load_language_manifest(raw):
    _require(isinstance(raw, dict), "expected a JSON object")
    _require(raw.get("version") == 1, "version: expected 1")
    captions = raw.get("captions")
    _require(isinstance(captions, list) and captions, "captions: expected a non-empty list")
    for index, caption in enumerate(captions):
        _require(isinstance(caption, str), "captions[{}]: expected a string, got {}".format(index, type(caption).__name__))
    descriptors = raw.get("descriptors")
    _require(isinstance(descriptors, dict), "descriptors: expected an object with shape and data")
    shape = descriptors.get("shape")
    _require(
        isinstance(shape, list) and len(shape) == 2 and all(isinstance(v, int) and v > 0 for v in shape),
        "descriptors.shape: expected [N, 512]",
    )
    _require(shape[1] == 512, "descriptors.shape: the contract fixes 512 columns, got {}".format(shape[1]))
    values = _numbers(descriptors.get("data"), "descriptors.data")
    _require(
        len(values) == shape[0] * shape[1],
        "descriptors.data: got {} values, expected {} ({}x{})".format(len(values), shape[0] * shape[1], shape[0], shape[1]),
    )
    image_ids = _int_list(raw.get("image_ids"), "image_ids")
    _require(len(set(image_ids)) == len(image_ids), "image_ids: expected unique ids")
    _require(len(image_ids) == shape[0], "image_ids: expected {} ids for {} descriptors".format(shape[0], shape[0]))
    query = raw.get("query")
    _require(isinstance(query, str) and query, "query: expected a non-empty string")
    k = raw.get("k")
    _require(isinstance(k, int) and not isinstance(k, bool), "k: expected an int")
    _require(1 <= k <= len(image_ids), "k: expected between 1 and {}".format(len(image_ids)))
    return {
        "captions": captions,
        "descriptors_shape": tuple(shape),
        "descriptors": values,
        "image_ids": image_ids,
        "query": query,
        "k": k,
    }


def load_manifest(path, benchmark):
    """Read and validate one fixture manifest, or raise MalformedFixture."""
    if not Path(path).is_file():
        raise MalformedFixture("no fixture manifest at {}".format(path))
    try:
        raw = json.loads(Path(path).read_text())
    except (OSError, ValueError) as exc:
        raise MalformedFixture("manifest is not readable JSON ({})".format(_fmt_exc(exc)))
    if benchmark == "audio-identification":
        return _load_audio_manifest(raw)
    if benchmark == "vision-recognition":
        return _load_image_manifest(raw, with_queries=True)
    if benchmark == "vision-clustering":
        return _load_image_manifest(raw, with_queries=False)
    if benchmark == "language-search":
        return _load_language_manifest(raw)
    raise MalformedFixture("unknown benchmark id: {}".format(benchmark))


# ---------------------------------------------------------------------------
# output validators (the documented contracts; anything they reject is
# "invalid", not "wrong answer" -- the preflight never scores)


def _as_list(value, what):
    if isinstance(value, (list, tuple)):
        return list(value)
    return None


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_int(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if _np is not None and isinstance(value, _np.integer):
        return True
    return False


def validate_audio_identify(value, enrolled_ids):
    """week1 identify(): ranked candidates, best first.

    Accepted shapes, per the docstring: a list of (song_id, score) pairs,
    a list of (song_id, artist, score) triples, a bare list of song ids,
    a single id, None, or [].
    """
    if value is None:
        return "ok", "returned None (no match), an accepted shape"
    if isinstance(value, str):
        value = [value]
    items = _as_list(value, "identify")
    if items is None:
        if _np is not None and isinstance(value, _np.ndarray):
            return "invalid", "returned an ndarray; expected a list of (song_id, score) pairs"
        return "invalid", "returned {}; expected a list of (song_id, score) pairs (or one of the accepted shapes)".format(
            type(value).__name__
        )
    if not items:
        return "ok", "returned [] (no match)"
    pairs, bare, triples = 0, 0, 0
    normalized = []
    for index, item in enumerate(items):
        if isinstance(item, str):
            bare += 1
            normalized.append((item, None))
        elif isinstance(item, (list, tuple)) and len(item) == 2 and isinstance(item[0], str) and _is_number(item[1]):
            pairs += 1
            normalized.append((str(item[0]), float(item[1])))
        elif (
            isinstance(item, (list, tuple))
            and len(item) == 3
            and isinstance(item[0], str)
            and isinstance(item[1], str)
            and _is_number(item[2])
        ):
            triples += 1
            normalized.append((str(item[0]), float(item[2])))
        else:
            return "invalid", (
                "identify()[{}]: expected (song_id, score), (song_id, artist, score) or a bare song id, got {}".format(
                    index, type(item).__name__
                )
            )
    if sum([pairs > 0, bare > 0, triples > 0]) > 1:
        return "invalid", "mixed return shapes in one list (pairs/bare ids/triples); pick one shape"
    unknown = [song_id for song_id, _ in normalized if song_id not in enrolled_ids]
    if unknown:
        return "invalid", "returned id(s) not in the enrolled set {}: {}".format(
            sorted(enrolled_ids), ", ".join(sorted(set(unknown)))
        )
    return "ok", "returned {} candidate(s) as {}".format(len(normalized), {0: "(song_id, score) pairs", 1: "bare song ids", 2: "(song_id, artist, score) triples"}[triples > 0 and 2 or (bare > 0 and 1 or 0)])


def validate_recognize(value, n_images):
    """week2 recognize(): one answer per image, same order; str or None."""
    items = _as_list(value, "recognize")
    if items is None:
        if _np is not None and isinstance(value, _np.ndarray):
            return "invalid", "returned an ndarray; expected one answer per input image, as a list"
        return "invalid", "returned {}; expected a list with one answer per input image".format(type(value).__name__)
    if len(items) != n_images:
        return "invalid", "got {} answer(s) for {} image(s); recognize() must return one answer per image, in order".format(
            len(items), n_images
        )
    for index, item in enumerate(items):
        if item is not None and not isinstance(item, str):
            return "invalid", "recognize()[{}]: expected a person id or None, got {}".format(index, type(item).__name__)
    named = sum(1 for item in items if item is not None)
    return "ok", "returned {} answer(s): {} named, {} None".format(len(items), named, len(items) - named)


def _validate_cluster_labels(value, n_images):
    items = value if isinstance(value, (list, tuple)) else None
    if items is None and _np is not None and isinstance(value, _np.ndarray) and value.ndim == 1:
        items = list(value)
    if items is None:
        return "invalid", "returned {}; expected one integer label per image".format(type(value).__name__)
    if len(items) != n_images:
        return "invalid", "got {} label(s) for {} image(s); cluster() must return one label per image, in order".format(
            len(items), n_images
        )
    for index, item in enumerate(items):
        if not _is_int(item):
            return "invalid", "cluster()[{}]: expected an integer label, got {}".format(index, type(item).__name__)
    return "ok", items


def _embedding_checks(value, what, n_rows):
    if _np is None:
        return "invalid", "numpy is not installed in this interpreter, so the output cannot be inspected"
    array = value if isinstance(value, _np.ndarray) else None
    if array is None:
        try:
            array = _np.asarray(value)
        except Exception:  # noqa: BLE001
            return "invalid", "{}: returned {}; expected an (N, D) numeric array".format(what, type(value).__name__)
    if array.ndim != 2:
        return "invalid", "{}: expected a 2-D (N, D) array, got {} dimension(s)".format(what, array.ndim)
    if array.shape[0] != n_rows:
        return "invalid", "{}: expected one row per input ({}), got shape {}".format(what, n_rows, tuple(array.shape))
    if array.shape[1] < 1:
        return "invalid", "{}: expected D >= 1, got shape {}".format(what, tuple(array.shape))
    if array.dtype.kind != "f":
        return "invalid", "{}: expected a float array (the contract says float32), got dtype {}".format(what, array.dtype)
    if not bool(_np.isfinite(array).all()):
        return "invalid", "{}: contains NaN or infinite values".format(what)
    return "ok", array


# ---------------------------------------------------------------------------
# per-benchmark exercise plans: call the real interface, in dependency order


def exercise_audio(submission, manifest):
    steps = []
    enrolled_ids = {song["id"] for song in manifest["enroll"]}
    for song in manifest["enroll"]:
        status, detail, _ = classify_call(
            submission.enroll, args=(song["id"], _np.asarray(song["samples"], dtype=_np.float32), manifest["sample_rate"])
        )
        steps.append(step("enroll", status, detail or "enrolled song '{}'".format(song["id"])))
        if status != "ok":
            return steps
    query = manifest["queries"][0]
    status, detail, value = classify_call(
        submission.identify, args=(_np.asarray(query["samples"], dtype=_np.float32), manifest["sample_rate"])
    )
    if status == "ok":
        status, detail = validate_audio_identify(value, enrolled_ids)
    steps.append(step("identify", status, detail))
    return steps


def exercise_recognition(submission, manifest):
    steps = []
    height, width, channels = manifest["image_shape"]
    for person in manifest["enroll"]:
        images = [_np.asarray(image, dtype=_np.uint8).reshape(height, width, channels) for image in person["images"]]
        status, detail, _ = classify_call(submission.enroll, args=(person["person_id"], images))
        steps.append(step("enroll", status, detail or "enrolled person '{}'".format(person["person_id"])))
        if status != "ok":
            return steps
    images = [_np.asarray(image, dtype=_np.uint8).reshape(height, width, channels) for image in manifest["queries"]]
    status, detail, value = classify_call(submission.recognize, args=(images,))
    if status == "ok":
        status, detail = validate_recognize(value, len(images))
    steps.append(step("recognize", status, detail))
    return steps


def exercise_clustering(submission, manifest):
    steps = []
    height, width, channels = manifest["image_shape"]
    images = [_np.asarray(image, dtype=_np.uint8).reshape(height, width, channels) for image in manifest["images"]]
    status, detail, first = classify_call(submission.cluster, args=(images,), kwargs={"seed": manifest["seed"]})
    if status != "ok":
        steps.append(step("cluster", status, detail))
        return steps
    status, detail = _validate_cluster_labels(first, len(images))
    if status != "ok":
        steps.append(step("cluster", status, detail))
        return steps
    # The benchmark reruns the clusterer under several seeds; the contract is
    # that the same seed reproduces the same partition (week2/README.md,
    # "Whispers and randomness"). Verify exactly that.
    status2, detail2, second = classify_call(submission.cluster, args=(images,), kwargs={"seed": manifest["seed"]})
    if status2 != "ok":
        steps.append(step("cluster", status2, detail2))
        return steps
    validated2 = _validate_cluster_labels(second, len(images))
    if validated2[0] != "ok":
        steps.append(step("cluster", validated2[0], validated2[1]))
        return steps
    if list(first) != list(second):
        steps.append(step("cluster", "invalid", "two runs with the same seed={} gave different labels; use the seed for every random choice".format(manifest["seed"])))
        return steps
    steps.append(step("cluster", "ok", "returned {} integer label(s); same seed={} reproduces them".format(len(first), manifest["seed"])))
    return steps


def exercise_language(submission, manifest):
    steps = []
    captions = manifest["captions"]
    # captions deliberately include tokens the adapter cannot know; the
    # docstring is explicit that unseen words must contribute zero vectors,
    # not raise.
    status, detail, text_vectors = classify_call(submission.embed_text, args=(captions,))
    text_d = None
    if status == "ok":
        status, detail_or_array = _embedding_checks(text_vectors, "embed_text", len(captions))
        if status == "ok":
            text_d = detail_or_array.shape[1]
            norms = _np.linalg.norm(detail_or_array, axis=1)
            detail = "returned shape {} float array; mean row L2 norm {:.4f}".format(
                tuple(detail_or_array.shape), float(_np.mean(norms))
            )
        else:
            detail = detail_or_array
    steps.append(step("embed_text", status, detail))

    descriptors = _np.asarray(manifest["descriptors"], dtype=_np.float32).reshape(manifest["descriptors_shape"])
    status, detail, image_vectors = classify_call(submission.embed_images, args=(descriptors,))
    image_d = None
    if status == "ok":
        status, detail_or_array = _embedding_checks(image_vectors, "embed_images", manifest["descriptors_shape"][0])
        if status == "ok":
            image_d = detail_or_array.shape[1]
            detail = "returned shape {} float array".format(tuple(detail_or_array.shape))
        else:
            detail = detail_or_array
    steps.append(step("embed_images", status, detail))

    d_status, d_detail = "ok", "text and image embeddings share D={}".format(text_d)
    if text_d is not None and image_d is not None and text_d != image_d:
        d_status = "invalid"
        d_detail = (
            "embed_text D={} disagrees with embed_images D={}; the benchmark reports the disagreement "
            "instead of scoring near chance".format(text_d, image_d)
        )
    elif text_d is None or image_d is None:
        d_status, d_detail = "blocked", "one of the two embeddings did not return, so D agreement is unverified"
    steps.append(step("d_consistency", d_status, d_detail))

    status, detail, _ = classify_call(submission.prepare_database, args=(manifest["image_ids"], descriptors))
    steps.append(step("prepare_database", status, detail or "prepared database with {} image ids".format(len(manifest["image_ids"]))))
    if status != "ok":
        steps.append(step("search", "blocked", "prepare_database did not complete ({}), so search() was not exercised".format(status)))
        return steps
    status, detail, value = classify_call(submission.search, args=(manifest["query"], manifest["k"]))
    if status == "ok":
        items = value if isinstance(value, (list, tuple)) else None
        if items is None:
            status, detail = "invalid", "search(): returned {}; expected a list of k image ids, best first".format(type(value).__name__)
        elif len(items) != manifest["k"]:
            status, detail = "invalid", "search(): got {} id(s) for k={}".format(len(items), manifest["k"])
        else:
            bad = [item for item in items if not _is_int(item)]
            if bad:
                status, detail = "invalid", "search(): expected integer image ids, got e.g. {}".format(type(bad[0]).__name__)
            else:
                off_pool = [int(item) for item in items if int(item) not in manifest["image_ids"]]
                if off_pool:
                    status, detail = "invalid", "search(): returned id(s) {} not in the database pool {} - return database ids, not row indices".format(
                        off_pool, manifest["image_ids"]
                    )
                else:
                    status, detail = "ok", "returned {} id(s) from the database pool".format(len(items))
    steps.append(step("search", status, detail))
    return steps


EXERCISERS = {
    "audio-identification": exercise_audio,
    "vision-recognition": exercise_recognition,
    "vision-clustering": exercise_clustering,
    "language-search": exercise_language,
}


# ---------------------------------------------------------------------------
# one modality end to end


def _import_module(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    if spec is None or spec.loader is None:
        return None, "could not build an import spec for this file"
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 - the point is to report it
        return None, _fmt_exc(exc)
    return module, ""


def _dependency_identity(source_paths):
    """Versions of the third-party packages the adapters import (top-level)."""
    roots = set()
    for path in source_paths:
        try:
            tree = ast.parse(Path(path).read_text())
        except (OSError, SyntaxError, ValueError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                roots.add(node.module.split(".")[0])
    roots.discard("submission")  # the adapter module name is never a package
    try:
        module_to_dists = _metadata.packages_distributions() if _metadata is not None else {}
    except Exception:  # pragma: no cover
        module_to_dists = {}
    versions = {}
    for root in sorted(roots):
        dists = module_to_dists.get(root, [root])
        version = "not installed"
        for dist in sorted(dists):
            try:
                version = _metadata.version(dist)
                break
            except Exception:  # noqa: BLE001
                continue
        versions[root] = version
    return versions


def check_modality(spec, repo_root, fixtures_root, module_seq, source_hashes):
    week = spec["week"]
    benchmark = spec["benchmark"]
    rel_source = spec["source"]
    source_path = repo_root / rel_source
    manifest_path = Path(fixtures_root) / spec["fixture"]
    manifest_display = _display(manifest_path, repo_root)
    base = {
        "week": week,
        "benchmark": benchmark,
        "factory": spec["factory"],
        "source": rel_source,
        "fixture": manifest_display,
    }
    if source_path.is_file():
        source_hashes[rel_source] = _sha256_file(source_path)

    def result(verdict, steps):
        base["verdict"] = verdict
        base["refusal"] = verdict in REFUSAL_VERDICTS
        base["steps"] = steps
        base["next_action"] = _next_action(base, verdict, steps, manifest_display)
        return base

    if not source_path.is_file():
        return result(
            "missing",
            [step("module", "missing", "{} not found - the benchmark looks for this exact path".format(rel_source))],
        )

    try:
        manifest = load_manifest(manifest_path, benchmark)
    except MalformedFixture as exc:
        return result(
            "unexercised",
            [step("fixture", "unexercised", "malformed fixture: {}".format(exc))],
        )

    module_seq[0] += 1
    module, import_detail = _import_module(source_path, "_capstone_preflight_{}".format(module_seq[0]))
    if module is None:
        return result("load_error", [step("module", "load_error", import_detail)])

    factory_name = spec["factory"]
    factory = getattr(module, factory_name, None)
    if not callable(factory):
        return result(
            "missing",
            [step("construct", "missing", "no callable {}() in {} - the benchmark calls it to build your adapter".format(factory_name, rel_source))],
        )

    status, detail, submission = classify_call(factory, args=())
    if status != "ok":
        return result("missing" if status == "missing" else "invalid", [step("construct", status, detail or "factory returned nothing usable")])
    if submission is None:
        return result("invalid", [step("construct", "invalid", "{}() returned None; it must return your adapter object".format(factory_name))])

    steps = EXERCISERS[benchmark](submission, manifest)

    statuses = [s["status"] for s in steps]
    if "missing" in statuses:
        verdict = "missing"
    elif "invalid" in statuses:
        verdict = "invalid"
    else:
        verdict = "ok"
    return result(verdict, steps)


def _next_action(entry, verdict, steps, manifest_display):
    week = entry["week"]
    rerun = RERUN_TEMPLATE.format(week=week)
    source = entry["source"]
    if verdict == "load_error":
        return "make {} import cleanly first ({}); nothing can run until the module imports".format(source, steps[0]["detail"])
    if verdict == "missing":
        target = next((s for s in steps if s["status"] == "missing"), steps[0])
        if target["method"] in ("module", "construct"):
            return "replace the NotImplementedError stub in {}: {} must build your adapter (see the file's own docstring); then rerun: {}".format(
                source, entry["factory"], rerun
            )
        return "implement {}() in {} - it still raises NotImplementedError (the starter stub); then rerun: {}".format(
            target["method"], source, rerun
        )
    if verdict == "invalid":
        target = next((s for s in steps if s["status"] == "invalid"), steps[0])
        return "fix {}() in {}: {}; then rerun: {}".format(target["method"], source, target["detail"], rerun)
    if verdict == "unexercised":
        return "the {} modality was not exercised: repair or add the fixture manifest at {} (see tools/submission-preflight/README.md); then rerun: {}".format(
            entry["benchmark"], manifest_display, rerun
        )
    return "the seam checks out on the shipped fixtures - this is not a score; run `cogworks run --benchmark {}` for the offline number".format(
        entry["benchmark"]
    )


# ---------------------------------------------------------------------------
# receipt


def run_preflight(repo_root, fixtures_root, weeks=None):
    """Run the preflight and return the receipt as a dict.

    Deterministic: no timestamps, no absolute paths, sorted keys downstream.
    """
    repo_root = Path(repo_root).resolve()
    fixtures_root = Path(fixtures_root).resolve()
    if weeks is None:
        weeks = ("week1", "week2", "week3")
    selected = [spec for spec in MODALITIES if spec["week"] in tuple(weeks)]

    source_hashes = {}
    module_seq = [0]
    results = [check_modality(spec, repo_root, fixtures_root, module_seq, source_hashes) for spec in selected]

    counts = {verdict: 0 for verdict in VERDICTS}
    for entry in results:
        counts[entry["verdict"]] += 1
    counts = {
        "modalities": len(results),
        "ok": counts["ok"],
        "missing": counts["missing"],
        "invalid": counts["invalid"],
        "unexercised": counts["unexercised"],
        "load_error": counts["load_error"],
        "refusals": sum(counts[v] for v in REFUSAL_VERDICTS),
    }

    probed = {}
    for name in BENCHMARK_MODULE_CANDIDATES:
        try:
            probed[name] = importlib.util.find_spec(name) is not None
        except Exception:  # noqa: BLE001 - probing must never crash the tool
            probed[name] = False
    installed = sorted(name for name, found in probed.items() if found)
    if installed:
        stack_note = "benchmark package importable ({}); the preflight still does not score it".format(", ".join(installed))
    else:
        stack_note = (
            "benchmark package not installed; accuracy is unmeasured here and the preflight never installs it - "
            "scoring happens with `cogworks run` on an approved install"
        )

    return {
        "receipt_version": RECEIPT_VERSION,
        "tool": "tools/submission-preflight/check.py",
        "selection": {"weeks": list(weeks)},
        "source_identity": {"git_commit": git_head(repo_root), "files": dict(sorted(source_hashes.items()))},
        "interpreter_identity": {"implementation": sys.implementation.name, "version": "{}.{}.{}".format(*sys.version_info[:3])},
        "dependency_identity": _dependency_identity(
            [repo_root / spec["source"] for spec in MODALITIES if (repo_root / spec["source"]).is_file()]
        ),
        "fixture_identity": {
            spec["benchmark"]: (
                _sha256_file(Path(fixtures_root) / spec["fixture"])
                if (Path(fixtures_root) / spec["fixture"]).is_file()
                else "absent"
            )
            for spec in selected
        },
        "benchmark_stack": {"status": "installed" if installed else "not-installed", "modules_probed": probed, "note": stack_note},
        "results": results,
        "counts": counts,
    }


# ---------------------------------------------------------------------------
# CLI


def _parse_weeks(value):
    if value.strip().lower() == "all":
        return ("week1", "week2", "week3")
    weeks = tuple(part.strip() for part in value.split(",") if part.strip())
    valid = {spec["week"] for spec in MODALITIES}
    for week in weeks:
        if week not in valid:
            raise argparse.ArgumentTypeError("unknown week '{}' (choose from all, {})".format(week, ", ".join(sorted(valid))))
    if not weeks:
        raise argparse.ArgumentTypeError("no week selected")
    return weeks


def print_report(receipt, stream):
    counts = receipt["counts"]
    stream.write(
        "submission preflight - {} modalit{}, {} refusal{}, {} unexercised\n".format(
            counts["modalities"],
            "y" if counts["modalities"] == 1 else "ies",
            counts["refusals"],
            "" if counts["refusals"] == 1 else "s",
            counts["unexercised"],
        )
    )
    for entry in receipt["results"]:
        stream.write("\n== {} / {} - {} ==\n".format(entry["week"], entry["benchmark"], entry["verdict"].upper()))
        for s in entry["steps"]:
            line = "   {:<18} {}".format(s["method"], s["status"])
            if s["detail"]:
                line += ": " + s["detail"]
            stream.write(line + "\n")
        stream.write("   next: {}\n".format(entry["next_action"]))
    stream.write(
        "\ncounts: ok={ok} missing={missing} invalid={invalid} unexercised={unexercised} load_error={load_error} refusals={refusals}\n".format(
            **counts
        )
    )
    stream.write("receipt: pass --json PATH to write one; this tool never scores\n")


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="python tools/submission-preflight/check.py",
        description="Local preflight of the capstone submission seam (never scores).",
    )
    parser.add_argument("--week", type=_parse_weeks, default=("week1", "week2", "week3"), help="week to check: all, week1, week2, week3 (or a comma list)")
    parser.add_argument("--fixtures", default=None, help="fixture root (default: {} under the repo root)".format(DEFAULT_FIXTURES_REL))
    parser.add_argument("--repo-root", default=None, help="repository root (default: the clone this tool lives in)")
    parser.add_argument("--json", default=None, metavar="PATH", help="write the deterministic receipt here ('-' for stdout)")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve() if args.repo_root else TOOL_DIR.parents[1]
    if not repo_root.is_dir():
        parser.error("repo root not found: {}".format(repo_root))
    fixtures_root = Path(args.fixtures).resolve() if args.fixtures else repo_root / DEFAULT_FIXTURES_REL

    receipt = run_preflight(repo_root, fixtures_root, weeks=args.week)
    print_report(receipt, sys.stdout)

    if args.json:
        payload = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
        if args.json == "-":
            sys.stdout.write(payload)
        else:
            Path(args.json).write_text(payload)
            sys.stdout.write("receipt written: {}\n".format(_display(Path(args.json), repo_root)))

    counts = receipt["counts"]
    if counts["ok"] == counts["modalities"]:
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
