from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import json

import pytest

from patent_to_pilot.evaluation.healthtech.local_retrieval import (
    PatentRecord,
    _OnnxTokenizer,
)
from patent_to_pilot.healthtech.engine import DossierInput, export_markdown, run_dossier
from patent_to_pilot.healthtech.history import (
    DossierHistoryError,
    append_user_edits,
    save_version,
)
from scripts.healthtech import run_real_baselines as baselines


ROOT = Path(__file__).resolve().parents[1]
TOKENIZER = ROOT / "data/raw/healthtech/models/sentence-transformers-all-MiniLM-L6-v2/tokenizer.json"


@pytest.mark.skipif(not TOKENIZER.exists(), reason="pinned local tokenizer artifact is unavailable")
def test_onnx_tokenizer_uses_native_masks_types_and_deterministic_padding():
    tokenizer = _OnnxTokenizer(str(TOKENIZER), max_length=256)
    short = "mitral valve"
    long = " ".join(["valve"] * 400)

    first = tokenizer.encode_texts([short, long])
    second = tokenizer.encode_texts([short, long])
    ids, masks, types, token_count = first

    assert ids.shape == (2, 256)
    assert masks.shape == types.shape == ids.shape
    assert int(masks[0].sum()) == 5
    assert int(masks[1].sum()) == 256
    assert token_count == int(masks.sum())
    assert int(masks[0][ids[0] == tokenizer.pad_id].sum()) == 0
    assert (ids == second[0]).all()
    assert (masks == second[1]).all()
    assert (types == second[2]).all()

    pair_ids, pair_masks, pair_types, pair_tokens = tokenizer.encode_pairs([("query", "document")])
    assert pair_ids.shape == pair_masks.shape == pair_types.shape == (1, 256)
    assert pair_tokens == int(pair_masks.sum())
    assert int(pair_masks[0].sum()) == 5
    assert 1 in set(pair_types[0].tolist())
    assert int(pair_masks[0][pair_ids[0] == tokenizer.pad_id].sum()) == 0


def _device():
    return SimpleNamespace(
        query_id="q1",
        company="Example Co",
        technical_description="first fixed query",
        features_of_interest=["second fixed query"],
    )


def _patents():
    return [
        PatentRecord(
            "US000001A1", "US000001A1", "US-grant", "US", "One", "One", "claim", "one",
            "source", "v1", "urn:one", "a" * 64, "b" * 64, "2026-01-01", "Example Co", "source",
        ),
        PatentRecord(
            "US000002A1", "US000002A1", "US-grant", "US", "Two", "Two", "claim", "two",
            "source", "v1", "urn:two", "c" * 64, "d" * 64, "2026-01-01", "Example Co", "source",
        ),
    ]


class _FakeRetriever:
    def __init__(self, fail_on: int | None = None):
        self.calls: list[str] = []
        self.fail_on = fail_on

    def fixed_bundle(self, query: str, *, candidate_depth: int, rerank_depth: int):
        self.calls.append(query)
        if self.fail_on == len(self.calls):
            raise RuntimeError(f"failure on action {len(self.calls)}")
        return {
            "query": query,
            "query_hash": baselines.stable_json_hash(query),
            "reranked": [{"patent_id_canonical": "US000001A1", "score": 1.0, "rank": 1}],
            "resources": {
                "query_calls": 1,
                "rerank_pairs": 1,
                "returned_candidates": 1,
                "embedding_query_tokens": 5,
                "rerank_tokens": 7,
            },
            "observables": {"lexical_dense_disagreement": 0.0},
        }


def test_baseline_preserves_completed_attempt_before_later_failure():
    result = baselines._run_method(
        _device(), _patents(), method="HT-B2", lexical=None, retriever=_FakeRetriever(fail_on=2),
        candidate_depth=2, rerank_depth=2,
    )

    assert result["status"] == "failed"
    assert [attempt["status"] for attempt in result["attempts"]] == ["completed", "failed"]
    assert [attempt["query"] for attempt in result["attempts"]] == ["first fixed query", "second fixed query"]
    assert result["resources"]["query_calls"] == 2
    assert result["resources"]["rerank_pairs"] == 1
    assert result["final_ranking"][0]["patent_id_canonical"] == "US000001A1"


def test_baseline_records_failure_before_dispatch_with_zero_query_calls(monkeypatch):
    def fail_before_schedule(_device):
        raise RuntimeError("pre-dispatch failure")

    monkeypatch.setattr(baselines, "_fixed_queries", fail_before_schedule)
    result = baselines._run_method(
        _device(), _patents(), method="HT-B2", lexical=None, retriever=_FakeRetriever(),
        candidate_depth=2, rerank_depth=2,
    )

    assert result["status"] == "failed"
    assert len(result["attempts"]) == 1
    assert result["attempts"][0]["status"] == "failed"
    assert result["attempts"][0]["query"] == "first fixed query"
    assert result["attempts"][0]["resources"]["query_calls"] == 0


def test_b1_and_fixed_multiquery_methods_share_first_query_text():
    b1_retriever = _FakeRetriever()
    b2_retriever = _FakeRetriever()
    b1 = baselines._run_method(_device(), _patents(), method="HT-B1", lexical=None, retriever=b1_retriever, candidate_depth=2, rerank_depth=2)
    baselines._run_method(_device(), _patents(), method="HT-B2", lexical=None, retriever=b2_retriever, candidate_depth=2, rerank_depth=2)
    assert b1["prefix_diagnostics"]["first_query"] == b2_retriever.calls[0]
    assert b1_retriever.calls[0] == b2_retriever.calls[0] == "first fixed query"


def test_history_rejects_stale_parent_and_export_includes_user_edits(tmp_path):
    example = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    dossier, _, _ = run_dossier(DossierInput.model_validate(example), run_id="repair-history", code_commit="test")
    history = tmp_path / "history"
    save_version(history, dossier)
    edited = append_user_edits(history, {"audit-note": "keep this in export"}, expected_parent_version=1)

    with pytest.raises(DossierHistoryError, match="expected parent version"):
        append_user_edits(history, {"stale": "writer"}, expected_parent_version=1)
    with pytest.raises(DossierHistoryError, match="version already exists"):
        save_version(history, dossier)

    markdown = export_markdown(edited, language="en")
    assert "## User edits" in markdown
    assert "keep this in export" in markdown
