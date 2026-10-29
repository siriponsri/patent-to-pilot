from __future__ import annotations

import json
from pathlib import Path

from patent_to_pilot.evaluation.healthtech.scifact import (
    SciFactDocument,
    SciFactRuntimeClaim,
)
from scripts.healthtech.run_scifact_lexical_baseline import _resolve_data_root, generate_predictions


def test_lexical_baseline_is_deterministic_and_runtime_only():
    corpus = {
        "10": SciFactDocument("10", "Valve repair", ("The valve repair improved outcomes.",), False),
        "11": SciFactDocument("11", "Drug therapy", ("The drug therapy reduced symptoms.",), False),
    }
    claims = [SciFactRuntimeClaim(2, "Valve repair improved outcomes")]
    first = generate_predictions(claims, corpus, top_k=1)
    second = generate_predictions(claims, corpus, top_k=1)
    assert first == second
    assert first == [{"id": 2, "evidence": {"10": {"label": "SUPPORT", "sentences": [0]}}}]
    assert "cited_doc_ids" not in first[0]
    assert "evidence" in first[0]


def test_lexical_baseline_can_emit_empty_evidence_without_missing_rows():
    corpus = {"10": SciFactDocument("10", "Valve repair", ("The valve repair improved outcomes.",), False)}
    claims = [SciFactRuntimeClaim(2, "Completely unrelated astronomy claim")]
    predictions = generate_predictions(claims, corpus, top_k=1)
    assert predictions == [{"id": 2, "evidence": {}}]


def test_resolve_data_root_accepts_extracted_release_root(tmp_path):
    data_root = tmp_path / "release" / "data"
    data_root.mkdir(parents=True)
    (data_root / "corpus.jsonl").write_text("{}\n", encoding="utf-8")
    (data_root / "claims_dev.jsonl").write_text("{}\n", encoding="utf-8")
    assert _resolve_data_root(tmp_path / "release") == data_root
