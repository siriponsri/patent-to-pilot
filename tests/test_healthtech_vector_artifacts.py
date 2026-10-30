import json
from pathlib import Path

import numpy as np
import pytest

from patent_to_pilot.evaluation.healthtech.local_retrieval import PatentRecord, SharedRetriever
from patent_to_pilot.evaluation.healthtech.vector_artifacts import (
    VectorArtifactError,
    encode_vector_shards,
    export_runtime_text,
    load_vector_bundle,
)
from patent_to_pilot.healthtech.engine import DossierInput, run_dossier


class FakeEncoder:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def encode(self, texts):
        self.calls.append(list(texts))
        return np.asarray([self.values[text] for text in texts], dtype="<f4"), sum(len(text.split()) for text in texts)


class BadDtypeEncoder(FakeEncoder):
    def encode(self, texts):
        self.calls.append(list(texts))
        return np.asarray([self.values[text] for text in texts], dtype="<f8"), 0


class NonfiniteEncoder(FakeEncoder):
    def encode(self, texts):
        self.calls.append(list(texts))
        return np.asarray([[np.nan, 0.0] for _ in texts], dtype="<f4"), 0


class FakeReranker:
    def score(self, query, documents):
        return [0.0 for _ in documents], len(query.split()) * len(documents)


class FakeVectorSearch:
    def search(self, query, *, limit):
        return [{"patent_id_canonical": "US000002A1", "score": 0.99, "rank": 1}], 3


def _rows():
    return [
        {"item_id": "p2", "document_id": "US000002A1", "text": "second valve", "source_id": "src", "source_revision": "r1"},
        {"item_id": "p1", "document_id": "US000001A1", "text": "first valve", "source_id": "src", "source_revision": "r1"},
        {"item_id": "p3", "document_id": "US000003A1", "text": "third pump", "source_id": "src", "source_revision": "r1"},
    ]


def test_runtime_export_is_ordered_and_rejects_evaluator_fields(tmp_path: Path):
    output = tmp_path / "runtime.jsonl"
    manifest = export_runtime_text(
        _rows(), output, dataset_id="fixture", source_revision="r1", representation="text-v1"
    )
    parsed = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [row["item_id"] for row in parsed] == ["fixture:p1", "fixture:p2", "fixture:p3"]
    assert manifest["row_count"] == 3
    with pytest.raises(VectorArtifactError, match="evaluator fields"):
        export_runtime_text(
            [{**_rows()[0], "qrels": ["gold"]}],
            tmp_path / "poisoned.jsonl",
            dataset_id="fixture",
            source_revision="r1",
            representation="text-v1",
        )


def test_vector_shards_resume_and_exact_tie_break(tmp_path: Path):
    runtime = tmp_path / "runtime.jsonl"
    export_runtime_text(_rows(), runtime, dataset_id="fixture", source_revision="r1", representation="text-v1")
    vectors = {
        "first valve": [1.0, 0.0],
        "second valve": [1.0, 0.0],
        "third pump": [0.0, 1.0],
    }
    output = tmp_path / "bundle"
    with pytest.raises(RuntimeError, match="injected interruption"):
        encode_vector_shards(
            runtime,
            output,
            FakeEncoder(vectors),
            model={"id": "fixture-model", "revision": "r1"},
            config={"norm_policy": "none"},
            batch_size=1,
            shard_size=2,
            stop_after_shards=1,
        )
    assert (output / "manifest.partial.json").exists()
    resumed_encoder = FakeEncoder(vectors)
    manifest = encode_vector_shards(
        runtime,
        output,
        resumed_encoder,
        model={"id": "fixture-model", "revision": "r1"},
        config={"norm_policy": "none"},
        batch_size=1,
        shard_size=2,
    )
    assert manifest["status"] == "complete"
    assert len(resumed_encoder.calls) == 1
    bundle = load_vector_bundle(output)
    ranked = bundle.search(np.asarray([1.0, 0.0], dtype="<f4"), limit=3)
    assert [row["document_id"] for row in ranked] == ["US000001A1", "US000002A1", "US000003A1"]


def test_import_rejects_partial_and_path_traversal(tmp_path: Path):
    runtime = tmp_path / "runtime.jsonl"
    export_runtime_text(_rows(), runtime, dataset_id="fixture", source_revision="r1", representation="text-v1")
    output = tmp_path / "bundle"
    encode_vector_shards(
        runtime,
        output,
        FakeEncoder({"first valve": [1.0, 0.0], "second valve": [0.0, 1.0], "third pump": [1.0, 1.0]}),
        model={"id": "fixture-model", "revision": "r1"},
        config={"norm_policy": "none"},
        shard_size=3,
    )
    (output / "leftover.partial").write_text("partial", encoding="utf-8")
    with pytest.raises(VectorArtifactError, match="partial bundle"):
        load_vector_bundle(output)
    (output / "leftover.partial").unlink()
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["shards"][0]["vectors_file"] = "../escape.npy"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(VectorArtifactError, match="unsafe bundle path|escapes root"):
        load_vector_bundle(output)


def test_encoder_rejects_wrong_dtype_and_nonfinite_vectors(tmp_path: Path):
    runtime = tmp_path / "runtime.jsonl"
    export_runtime_text(_rows(), runtime, dataset_id="fixture", source_revision="r1", representation="text-v1")
    with pytest.raises(VectorArtifactError, match="little-endian float32"):
        encode_vector_shards(
            runtime,
            tmp_path / "bad-dtype",
            BadDtypeEncoder({row["text"]: [1.0, 0.0] for row in _rows()}),
            model={"id": "fixture-model", "revision": "r1"},
            config={"norm_policy": "none"},
        )
    with pytest.raises(VectorArtifactError, match="non-finite"):
        encode_vector_shards(
            runtime,
            tmp_path / "bad-finite",
            NonfiniteEncoder({row["text"]: [1.0, 0.0] for row in _rows()}),
            model={"id": "fixture-model", "revision": "r1"},
            config={"norm_policy": "none"},
        )


def test_shared_retriever_accepts_precomputed_vectors_without_reencoding_documents(tmp_path: Path):
    runtime = tmp_path / "runtime.jsonl"
    export_runtime_text(
        [
            {"item_id": "p1", "document_id": "US000001A1", "text": "first valve", "source_id": "src", "source_revision": "r1"},
            {"item_id": "p2", "document_id": "US000002A1", "text": "second valve", "source_id": "src", "source_revision": "r1"},
        ],
        runtime,
        dataset_id="fixture",
        source_revision="r1",
        representation="text-v1",
    )
    bundle_dir = tmp_path / "bundle"
    encode_vector_shards(
        runtime,
        bundle_dir,
        FakeEncoder({"first valve": [1.0, 0.0], "second valve": [0.0, 1.0]}),
        model={"id": "fixture-model", "revision": "r1"},
        config={"norm_policy": "none"},
        shard_size=2,
    )
    bundle = load_vector_bundle(bundle_dir)
    patents = [
        PatentRecord("1", "US000001A1", "US-grant", "US", "First", "", "", "first valve", "src", "r1", "u", "a" * 64, "b" * 64, "2026-01-01", "", ""),
        PatentRecord("2", "US000002A1", "US-grant", "US", "Second", "", "", "second valve", "src", "r1", "u", "c" * 64, "d" * 64, "2026-01-01", "", ""),
    ]
    query_encoder = FakeEncoder({"first": [1.0, 0.0]})
    retriever = SharedRetriever(
        patents,
        encoder=query_encoder,
        reranker=FakeReranker(),
        precomputed_vectors=bundle,
    )
    results, _ = retriever.dense_search("first", limit=2)
    assert results[0]["patent_id_canonical"] == "US000001A1"
    assert retriever.index_tokens == 0
    assert query_encoder.calls == [["first"]]


def test_dossier_engine_can_augment_lexical_candidates_with_returned_vectors():
    root = Path(__file__).resolve().parents[1]
    payload = json.loads((root / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    data = DossierInput.model_validate(payload)
    dossier, events, manifest = run_dossier(
        data,
        run_id="vector-backed",
        code_commit="test",
        vector_search=FakeVectorSearch(),
    )
    candidate = next(item for item in dossier.candidates if item.patent_id_canonical == "US000002A1")
    assert candidate.scores["dense_cosine"] == pytest.approx(0.99)
    assert events[0].returned_candidates >= 1
    assert manifest.stop_reason == "fixed_schedule_complete"
