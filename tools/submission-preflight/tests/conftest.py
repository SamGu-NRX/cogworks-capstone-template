"""Shared test scaffolding: synthetic adapters and tiny fixture manifests.

The synthetic adapters are deliberately NOT the repo's starter code: each one
exercises one class of preflight verdict (stub, working, wrong-shape output,
crash, partial implementation, absent factory, unimportable module). They are
written into throwaway repository trees so the contracts hold without
touching any week directory in the real repo.
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

TOOL_DIR = Path(__file__).resolve().parents[1]
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))

import check  # noqa: E402 - path set up above on purpose

REPO_ROOT = Path(__file__).resolve().parents[3]


# ---------------------------------------------------------------------------
# synthetic adapter sources, keyed by (week, behaviour)


AUDIO_STUB = '''
import numpy as np

class Submission:
    def __init__(self):
        raise NotImplementedError("build your database here")

    def enroll(self, song_id, samples, sample_rate):
        raise NotImplementedError("call your fingerprint-and-store code")

    def identify(self, samples, sample_rate):
        raise NotImplementedError("call your matcher")

def create_submission(resources=None):
    return Submission()
'''

AUDIO_VALID = '''
import numpy as np

class Submission:
    """Cosine similarity against raw enrolled clips; contract-true, not good."""

    def __init__(self):
        self._db = {}

    def enroll(self, song_id, samples, sample_rate):
        self._db[song_id] = np.asarray(samples, dtype=np.float32)

    def identify(self, samples, sample_rate):
        query = np.asarray(samples, dtype=np.float32)
        best, best_score = None, -1.0
        for song_id, ref in self._db.items():
            n = min(len(ref), len(query))
            if n == 0:
                continue
            denom = np.linalg.norm(ref[:n]) * np.linalg.norm(query[:n]) + 1e-9
            score = float(np.dot(ref[:n], query[:n]) / denom)
            if best is None or score > best_score:
                best, best_score = song_id, score
        if best is None:
            return []
        return [(best, best_score)]

def create_submission(resources=None):
    return Submission()
'''

AUDIO_BARE_ID = AUDIO_VALID.replace(
    "return [(best, best_score)]",
    "return best  # bare song id, an accepted shape",
)

AUDIO_TRIPLES = AUDIO_VALID.replace(
    "return [(best, best_score)]",
    "return [(best, 'unknown artist', best_score)]  # triples, an accepted shape",
)

AUDIO_INVALID = '''
import numpy as np

class Submission:
    def __init__(self):
        self._db = {}

    def enroll(self, song_id, samples, sample_rate):
        self._db[song_id] = np.asarray(samples, dtype=np.float32)

    def identify(self, samples, sample_rate):
        return 3  # not one of the accepted shapes

def create_submission(resources=None):
    return Submission()
'''

AUDIO_NO_FACTORY = '''
import numpy as np

class Submission:
    def __init__(self):
        self._db = {}

    def enroll(self, song_id, samples, sample_rate):
        self._db[song_id] = np.asarray(samples, dtype=np.float32)

    def identify(self, samples, sample_rate):
        return []
# no create_submission factory: the benchmark has nothing to call
'''

AUDIO_UNIMPORTABLE = "this file does not parse (((\n"

RECOG_STUB = '''
class RecognitionSubmission:
    def __init__(self):
        raise NotImplementedError("set up your database and model here")

    def enroll(self, person_id, images):
        raise NotImplementedError("call your descriptor and profile code")

    def recognize(self, images):
        raise NotImplementedError("call your matcher")
'''

RECOG_VALID = '''
import numpy as np

class RecognitionSubmission:
    def __init__(self):
        self._db = {}

    def enroll(self, person_id, images):
        self._db[person_id] = [np.asarray(image, dtype=np.float64) for image in images]

    def recognize(self, images):
        answers = []
        for image in images:
            arr = np.asarray(image, dtype=np.float64).ravel()
            best, best_d = None, None
            for person_id, refs in self._db.items():
                for ref in refs:
                    r = ref.ravel()
                    n = min(r.size, arr.size)
                    d = float(np.mean(np.abs(r[:n] - arr[:n])))
                    if best_d is None or d < best_d:
                        best, best_d = person_id, d
            answers.append(best if best is not None else None)
        return answers

def create_recognition_submission(resources=None):
    return RecognitionSubmission()
'''

RECOG_INVALID = '''
import numpy as np

class RecognitionSubmission:
    def __init__(self):
        self._db = {}

    def enroll(self, person_id, images):
        self._db[person_id] = True

    def recognize(self, images):
        return ["someone"] * (len(images) + 1)  # one answer too many

def create_recognition_submission(resources=None):
    return RecognitionSubmission()
'''

CLUSTER_STUB = '''
class ClusteringSubmission:
    def __init__(self):
        raise NotImplementedError("set up your model here")

    def cluster(self, images, *, seed):
        raise NotImplementedError("call your whispers implementation")
'''

CLUSTER_VALID = '''
import numpy as np

class ClusteringSubmission:
    """Groups identical arrays; deterministic for any seed."""

    def __init__(self):
        pass

    def cluster(self, images, *, seed):
        seen = {}
        labels = []
        for image in images:
            key = np.asarray(image).tobytes()
            if key not in seen:
                seen[key] = len(seen)
            labels.append(seen[key])
        return labels

def create_clustering_submission(resources=None):
    return ClusteringSubmission()
'''

CLUSTER_UNSTABLE = (
    CLUSTER_VALID.replace(
        "import numpy as np\n",
        "import numpy as np\n_state = {\"calls\": 0}\n",
        1,
    )
    .replace(
        "        return labels",
        "        _state[\"calls\"] += 1\n"
        "        if _state[\"calls\"] % 2 == 0:\n"
        "            labels = [label + 10 for label in labels]  # leaked state: same seed, different labels\n"
        "        return labels",
        1,
    )
)

WEEK2_FILES = {
    "stub": RECOG_STUB + "\n\n" + CLUSTER_STUB + "\n\ndef create_recognition_submission(resources=None):\n    return RecognitionSubmission()\n\ndef create_clustering_submission(resources=None):\n    return ClusteringSubmission()\n",
    "valid": RECOG_VALID + "\n\n" + CLUSTER_VALID,
    "recog_invalid": RECOG_INVALID + "\n\n" + CLUSTER_VALID,
    "cluster_unstable": RECOG_VALID + "\n\n" + CLUSTER_UNSTABLE,
}

LANG_STUB = '''
import numpy as np

class Submission:
    def __init__(self):
        raise NotImplementedError("load your weights, GloVe, and IDF table")

    def embed_text(self, captions):
        raise NotImplementedError("call your caption embedding code")

    def embed_images(self, descriptors):
        raise NotImplementedError("apply your trained W_embed")

    def prepare_database(self, image_ids, descriptors):
        raise NotImplementedError("build your searchable database")

    def search(self, query, k):
        raise NotImplementedError("call your query path")

def create_submission(resources=None):
    return Submission()
'''

LANG_VALID = '''
import numpy as np

D = 8

class Submission:
    """Hash-bucket embeddings; contract-true, not meaningful."""

    def __init__(self):
        self._ids = []
        self._matrix = None

    def embed_text(self, captions):
        rows = []
        for caption in captions:
            vec = np.zeros(D, dtype=np.float32)
            for word in caption.split():
                vec[sum(ord(ch) for ch in word) % D] += 1.0
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec = vec / norm
            rows.append(vec)
        return np.vstack(rows) if rows else np.zeros((0, D), dtype=np.float32)

    def embed_images(self, descriptors):
        arr = np.asarray(descriptors, dtype=np.float32)
        return arr[:, :D] / (np.linalg.norm(arr[:, :D], axis=1, keepdims=True) + 1e-9)

    def prepare_database(self, image_ids, descriptors):
        self._ids = list(image_ids)
        self._matrix = self.embed_images(descriptors)

    def search(self, query, k):
        q = self.embed_text([query])[0]
        scores = self._matrix @ q
        order = np.argsort(-scores)[:k]
        return [self._ids[int(i)] for i in order]

def create_submission(resources=None):
    return Submission()
'''

LANG_KEYERROR = LANG_VALID.replace(
    "            for word in caption.split():\n                vec[sum(ord(ch) for ch in word) % D] += 1.0",
    "            for word in caption.split():\n                if word not in _VOCAB:\n                    raise KeyError(word)  # the exact failure week3 warns about\n                vec[_VOCAB[word] % D] += 1.0",
).replace(
    "D = 8",
    "D = 8\n_VOCAB = {'a': 0, 'red': 1, 'ball': 2, 'on': 3, 'grass': 4, 'dog': 5, 'runs': 6}",
)

LANG_PARTIAL = LANG_VALID.replace(
    "    def embed_images(self, descriptors):\n        arr = np.asarray(descriptors, dtype=np.float32)\n        return arr[:, :D] / (np.linalg.norm(arr[:, :D], axis=1, keepdims=True) + 1e-9)",
    "    def embed_images(self, descriptors):\n        raise NotImplementedError('apply your trained W_embed')",
)

WEEK3_FILES = {
    "stub": LANG_STUB,
    "valid": LANG_VALID,
    "keyerror": LANG_KEYERROR,
    "partial": LANG_PARTIAL,
}


# ---------------------------------------------------------------------------
# valid fixture manifests (tiny; pure formulas, no randomness)


def sine(freq, count, amp, offset=0, rate=44100):
    return [
        round(amp * math.sin(2 * math.pi * freq * (offset + i) / rate), 6)
        for i in range(count)
    ]


def image_values(base, spread):
    flat = []
    for row in range(4):
        for col in range(4):
            for channel in range(3):
                if channel == 0:
                    flat.append(min(255, base + spread * ((row + col) % 2)))
                elif channel == 1:
                    flat.append(min(255, base // 2))
                else:
                    flat.append(min(255, max(0, base - 60)))
    return flat


def build_manifests(fixtures_root):
    """Write one valid manifest per benchmark; returns the root path."""
    root = Path(fixtures_root)
    audio = root / "audio-identification"
    audio.mkdir(parents=True, exist_ok=True)
    (audio / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "sample_rate": 44100,
                "enroll": [
                    {"id": "songA", "samples": sine(440, 32, 0.5)},
                    {"id": "songB", "samples": sine(660, 32, 0.5)},
                ],
                "queries": [{"samples": sine(440, 24, 0.25, offset=4)}],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    recog = root / "vision-recognition"
    recog.mkdir(parents=True, exist_ok=True)
    (recog / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "image_shape": [4, 4, 3],
                "enroll": [
                    {"person_id": "alice", "images": [{"data": image_values(200, 30)}]},
                    {"person_id": "bob", "images": [{"data": image_values(60, 30)}]},
                ],
                "queries": [{"data": image_values(200, 10)}, {"data": image_values(60, 10)}],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    clus = root / "vision-clustering"
    clus.mkdir(parents=True, exist_ok=True)
    (clus / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "image_shape": [4, 4, 3],
                "images": [
                    {"data": image_values(200, 0)},
                    {"data": image_values(200, 0)},
                    {"data": image_values(60, 0)},
                    {"data": image_values(60, 0)},
                ],
                "seed": 7,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    lang = root / "language-search"
    lang.mkdir(parents=True, exist_ok=True)
    descriptors = [
        round(((i * 37 + j * 11) % 97) / 97 - 0.5, 4)
        for i in range(4)
        for j in range(512)
    ]
    (lang / "manifest.json").write_text(
        json.dumps(
            {
                "version": 1,
                "captions": [
                    "a red ball on grass",
                    "a dog runs",
                    "zzq xkcd unseen words",
                ],
                "descriptors": {"shape": [4, 512], "data": descriptors},
                "image_ids": [101, 102, 103, 104],
                "query": "a red ball",
                "k": 2,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    return root


# ---------------------------------------------------------------------------
# pytest fixtures


@pytest.fixture(scope="session")
def real_repo_root():
    return REPO_ROOT


@pytest.fixture
def manifests(tmp_path):
    return build_manifests(tmp_path / "fixtures")


@pytest.fixture
def synthetic_repo(tmp_path):
    def _make(weeks):
        root = tmp_path / "repo"
        for week, behaviour in weeks.items():
            target = root / week
            target.mkdir(parents=True, exist_ok=True)
            if week == "week1":
                sources = {
                    "stub": AUDIO_STUB,
                    "valid": AUDIO_VALID,
                    "bare_id": AUDIO_BARE_ID,
                    "triples": AUDIO_TRIPLES,
                    "invalid": AUDIO_INVALID,
                    "no_factory": AUDIO_NO_FACTORY,
                    "unimportable": AUDIO_UNIMPORTABLE,
                }
            elif week == "week2":
                sources = WEEK2_FILES
            elif week == "week3":
                sources = WEEK3_FILES
            else:  # pragma: no cover - test authoring error
                raise ValueError(week)
            (target / "submission.py").write_text(sources[behaviour])
        return root

    return _make


def only(receipt, benchmark):
    matches = [entry for entry in receipt["results"] if entry["benchmark"] == benchmark]
    assert len(matches) == 1, "expected exactly one result for " + benchmark
    return matches[0]
