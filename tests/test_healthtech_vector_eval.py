import hashlib

import numpy as np
import pytest

from patent_to_pilot.evaluation.healthtech.vector_artifacts import RuntimeTextRow
from scripts.healthtech.run_vector_retrieval_eval import _rrf_rankings, _validate_model_artifacts, run_evaluation


def _row(document_id: str, text: str) -> RuntimeTextRow:
    return RuntimeTextRow(
        item_id=f"dapfam-corpus:{document_id}",
        document_id=document_id,
        text=text,
        text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        source_id="fixture",
        source_revision="r1",
    )


class FakeBundle:
    document_ids = ("p1", "p2")

    def search(self, query_vector, *, limit):
        document_id = "p1" if float(query_vector[0]) > 0.5 else "p2"
        return [{"document_id": document_id, "item_id": f"dapfam-corpus:{document_id}", "score": 1.0, "rank": 1}]


class FakeEncoder:
    def encode(self, texts):
        if "fail" in texts:
            raise RuntimeError("fixture failure")
        return np.asarray([[1.0, 0.0] for _ in texts], dtype="<f4"), len(texts)


def test_rrf_is_deterministic_and_rejects_duplicates():
    assert _rrf_rankings([["p2", "p1"], ["p1", "p2"]], rrf_k=60) == ["p1", "p2"]
    with pytest.raises(ValueError, match="duplicate"):
        _rrf_rankings([["p1", "p1"]], rrf_k=60)


def test_vector_evaluation_keeps_dense_failure_in_denominator():
    corpus = [_row("p1", "alpha device"), _row("p2", "beta device")]
    queries = [_row("q1", "alpha"), _row("q2", "fail")]
    qrels = {"q1": {"p1": 1.0}, "q2": {"p2": 1.0}}

    summary, rankings, statuses = run_evaluation(
        corpus,
        queries,
        qrels,
        FakeBundle(),
        FakeEncoder(),
        batch_size=1,
        k=1,
        rrf_k=60,
    )

    assert summary["dense_failed_query_count"] == 1
    assert summary["metrics"]["dense"]["failed_query_count"] == 1
    assert summary["metrics"]["dense"]["missing_query_count"] == 0
    assert statuses["dense"]["q2"] == "failed"
    assert rankings["dense"]["q2"] == []


def test_model_artifact_binding_rejects_mismatch(tmp_path):
    model = tmp_path / "model.onnx"
    tokenizer = tmp_path / "tokenizer.json"
    model.write_bytes(b"model")
    tokenizer.write_bytes(b"tokenizer")
    bundle = type("Bundle", (), {
        "manifest": {
            "model": {
                "model_artifact": {"sha256": "0" * 64},
                "tokenizer_artifact": {"sha256": "1" * 64},
            }
        }
    })()

    with pytest.raises(ValueError, match="model artifact"):
        _validate_model_artifacts(bundle, model, tokenizer)
