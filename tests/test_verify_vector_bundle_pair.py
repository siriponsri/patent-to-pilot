import json
from pathlib import Path

import numpy as np
import pytest

from scripts.healthtech.verify_vector_bundle_pair import verify
from patent_to_pilot.evaluation.healthtech.vector_artifacts import (
    VectorArtifactError,
    encode_vector_shards,
    export_runtime_text,
    sha256_file,
)


class FixtureEncoder:
    def encode(self, texts):
        values = {
            "first valve": [1.0, 0.0],
            "second valve": [0.0, 1.0],
            "device query": [1.0, 1.0],
        }
        return np.asarray([values[text] for text in texts], dtype="<f4"), 0


def _runtime(root: Path, name: str, rows: list[dict[str, str]]) -> Path:
    path = root / "inputs" / name / "runtime.jsonl"
    export_runtime_text(rows, path, dataset_id=name, source_revision="fixture-r1", representation="text-v1")
    return path


def _bundle(root: Path, relative: str, runtime: Path) -> None:
    encode_vector_shards(
        runtime,
        root / relative,
        FixtureEncoder(),
        model={"model_id": relative.split("/")[-1], "revision": "fixture-r1"},
        config={"norm_policy": "none"},
        shard_size=2,
    )


def test_verifier_accepts_bound_bundle_pair(tmp_path: Path):
    root = tmp_path / "artifacts"
    corpus = _runtime(
        root,
        "corpus",
        [
            {"item_id": "p1", "document_id": "US000001A1", "text": "first valve", "source_id": "src", "source_revision": "r1"},
            {"item_id": "p2", "document_id": "US000002A1", "text": "second valve", "source_id": "src", "source_revision": "r1"},
        ],
    )
    queries = _runtime(
        root,
        "queries",
        [{"item_id": "q1", "document_id": "Q1", "text": "device query", "source_id": "src", "source_revision": "r1"}],
    )
    runtime_manifest = root / "inputs" / "device-runtime" / "manifest.json"
    runtime_manifest.parent.mkdir(parents=True)
    runtime_manifest.write_text(
        json.dumps(
            {
                "cases": ["fixture-case"],
                "corpus_sha256": sha256_file(corpus),
                "queries_sha256": sha256_file(queries),
                "corpus": {"row_count": 2},
                "queries": {"row_count": 1},
            }
        ),
        encoding="utf-8",
    )
    for relative in (
        "outputs/device-patembed-corpus",
        "outputs/device-e5-corpus",
    ):
        _bundle(root, relative, corpus)
    for relative in (
        "outputs/device-patembed-queries",
        "outputs/device-e5-queries",
    ):
        _bundle(root, relative, queries)

    receipt = verify(root)

    assert receipt["status"] == "PASS_VECTOR_BUNDLE_INTEGRITY_PRIOR_ARTIFACT"
    assert receipt["runtime"]["corpus_rows"] == 2
    assert receipt["runtime"]["query_rows"] == 1
    assert all(receipt["checks"].values())


def test_verifier_rejects_runtime_input_binding_mismatch(tmp_path: Path):
    root = tmp_path / "artifacts"
    runtime = _runtime(
        root,
        "corpus",
        [{"item_id": "p1", "document_id": "US000001A1", "text": "first valve", "source_id": "src", "source_revision": "r1"}],
    )
    manifest = root / "inputs" / "device-runtime" / "manifest.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({"corpus_sha256": "0" * 64, "queries_sha256": "1" * 64}),
        encoding="utf-8",
    )
    for relative in (
        "outputs/device-patembed-corpus",
        "outputs/device-e5-corpus",
    ):
        _bundle(root, relative, runtime)
    with pytest.raises(VectorArtifactError, match="input binding mismatch"):
        verify(root)
