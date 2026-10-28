"""Offline pre-live HealthTech adapter, history and API seam checks."""
from __future__ import annotations

from datetime import date
from copy import deepcopy
import json
from pathlib import Path
import socket

import pytest
from pydantic import ValidationError

from patent_to_pilot.evaluation.healthtech.scifact import (
    SciFactGoldClaim,
    SciFactEvidence,
    SciFactFormatError,
    SciFactDocument,
    evaluate_predictions,
    load_gold_claims,
    load_runtime_claims,
    validate_against_corpus,
)
from patent_to_pilot.evaluation.healthtech.local_retrieval import (
    BM25Index,
    PatentRecord,
    reciprocal_rank_fusion,
    validate_runtime_payload,
)
from patent_to_pilot.healthtech.api import (
    HealthTechAPIConfig,
    HealthTechRequest,
    HealthTechVisibleSource,
    dispatch_healthtech_request,
)
from patent_to_pilot.healthtech.engine import DossierInput, run_dossier
from patent_to_pilot.healthtech.history import append_user_edits, load_versions, save_version, source_view
from patent_to_pilot.providers import MockHTTPResponse, MockHTTPTransport
from scripts.healthtech.fetch_public_510k import AcquisitionAccounting

ROOT = Path(__file__).resolve().parents[1]


def _source_hash() -> str:
    return "a" * 64


def _api_request() -> HealthTechRequest:
    return HealthTechRequest(
        request_id="ht-test-001",
        project_id="project-1",
        query_id="query-1",
        action_type="evidence_summary",
        prompt="Return a ready acknowledgement.",
        response_schema={
            "type": "object",
            "additionalProperties": False,
            "properties": {"status": {"type": "string", "enum": ["ready"]}, "request_id": {"type": "string"}},
            "required": ["status", "request_id"],
        },
        visible_sources=[HealthTechVisibleSource(source_id="source-1", source_version="v1", payload_hash=_source_hash())],
        estimated_input_tokens=8,
    )


def test_runtime_scifact_reader_drops_gold_fields_and_gold_loader_preserves_them(tmp_path):
    path = tmp_path / "claims.jsonl"
    path.write_text(json.dumps({"id": 1, "claim": "A claim", "cited_doc_ids": [10], "evidence": {"10": [{"label": "SUPPORT", "sentences": [0]}]}}) + "\n", encoding="utf-8")
    runtime = load_runtime_claims(path)
    gold = load_gold_claims(path)
    assert runtime[0].claim_id == 1 and not hasattr(runtime[0], "evidence")
    assert not hasattr(runtime[0], "cited_doc_ids")
    assert gold[0].evidence["10"].label == "SUPPORT"


def test_scifact_metrics_match_official_abstract_and_sentence_example():
    gold = [SciFactGoldClaim(
        claim_id=52,
        claim="ALDH1 expression is associated with poorer prognosis for breast cancer primary tumors.",
        evidence={
            "11": SciFactEvidence("SUPPORT", ((0, 1), (11,))),
            "15": SciFactEvidence("SUPPORT", ((4,),)),
        },
        cited_doc_ids=("11", "15"),
    )]
    metrics = evaluate_predictions(gold, [{"id": 52, "evidence": {
        "11": {"label": "SUPPORT", "sentences": [1, 11, 13]},
        "16": {"label": "SUPPORT", "sentences": [18, 20]},
    }}])
    assert metrics["abstract_label_only"]["f1"] == pytest.approx(0.5)
    assert metrics["abstract_rationalized"]["f1"] == pytest.approx(0.5)
    assert metrics["sentence_selection"]["precision"] == pytest.approx(0.2)
    assert metrics["sentence_selection"]["recall"] == pytest.approx(0.25)
    assert metrics["sentence_label"]["f1"] == pytest.approx(2 / 9)


def test_scifact_prediction_rejects_nei_and_runtime_loader_does_not_promote_labels(tmp_path):
    path = tmp_path / "claims.jsonl"
    path.write_text(json.dumps({"id": 1, "claim": "A claim", "cited_doc_ids": []}) + "\n", encoding="utf-8")
    assert load_runtime_claims(path)[0].claim == "A claim"
    with pytest.raises(SciFactFormatError):
        evaluate_predictions([SciFactGoldClaim(1, "A claim", {}, ())], [{"id": 1, "evidence": {"1": {"label": "NEI", "sentences": []}}}])


def test_scifact_strict_contract_rejects_duplicate_sentences_and_unexpected_claims():
    gold = [SciFactGoldClaim(1, "A claim", {"10": SciFactEvidence("SUPPORT", ((0,),))}, ("10",))]
    with pytest.raises(SciFactFormatError, match="repeats a sentence ID"):
        evaluate_predictions(gold, [{"id": 1, "evidence": {"10": {"label": "SUPPORT", "sentences": [0, 0]}}}])
    with pytest.raises(SciFactFormatError, match="unexpected prediction claim IDs"):
        evaluate_predictions(gold, [
            {"id": 1, "evidence": {}},
            {"id": 999, "evidence": {}},
        ])


def test_scifact_missing_rows_are_explicit_empty_failures_and_bounds_are_checked():
    gold = [
        SciFactGoldClaim(1, "A claim", {"10": SciFactEvidence("SUPPORT", ((0,),))}, ("10",)),
        SciFactGoldClaim(2, "Another claim", {}, ()),
    ]
    corpus = {"10": SciFactDocument("10", "Title", ("Sentence",), False), "11": SciFactDocument("11", "Other", ("Other",), False)}
    metrics = evaluate_predictions(gold, [{"id": 1, "evidence": {"11": {"label": "SUPPORT", "sentences": [0]}}}], corpus=corpus)
    assert metrics["missing_prediction_claim_ids"] == [2]
    assert metrics["sentence_selection"]["recall"] == 0.0
    with pytest.raises(SciFactFormatError, match="out-of-range"):
        evaluate_predictions(gold, [{"id": 1, "evidence": {"10": {"label": "SUPPORT", "sentences": [1]}}}], corpus=corpus)


def test_scifact_gold_overlapping_rationales_are_rejected():
    corpus = {"10": SciFactDocument("10", "Title", ("Sentence", "Other"), False)}
    gold = [SciFactGoldClaim(1, "A claim", {"10": SciFactEvidence("SUPPORT", ((0,), (0, 1)))}, ("10",))]
    with pytest.raises(SciFactFormatError, match="overlapping rationales"):
        validate_against_corpus(gold, corpus)


def test_public_acquisition_accounting_enforces_cumulative_transfer_and_storage_caps():
    accounting = AcquisitionAccounting(transfer_cap_bytes=5, storage_cap_bytes=7)
    accounting.record_transfer(5)
    with pytest.raises(ValueError, match="cumulative transfer cap"):
        accounting.record_transfer(1)
    accounting.record_storage(7)
    with pytest.raises(ValueError, match="cumulative storage cap"):
        accounting.record_storage(1)


def test_public_acquisition_manifest_accounting_is_self_consistent(tmp_path, monkeypatch):
    from scripts.healthtech import fetch_public_510k as fetcher

    payload = {
        "results": [{
            "k_number": "K123456",
            "device_name": "Example Device",
            "applicant": "Example Co",
            "product_code": "ABC",
            "decision_code": "SESE",
            "decision_date": "2026-01-01",
            "date_received": "2025-12-01",
        }],
        "meta": {"last_updated": "2026-01-01"},
    }

    class Response:
        headers = {"Content-Length": str(len(json.dumps(payload).encode("utf-8")))}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, size=-1):
            data = json.dumps(payload).encode("utf-8")
            if not hasattr(self, "sent"):
                self.sent = True
                return data
            return b""

    monkeypatch.setattr(fetcher, "urlopen", lambda *args, **kwargs: Response())
    output = tmp_path / "snapshot"
    monkeypatch.setattr(
        "sys.argv",
        [
            "fetch_public_510k.py",
            "--k-number",
            "K123456",
            "--output",
            str(output),
            "--max-transfer-bytes",
            "10000",
            "--max-storage-bytes",
            "100000",
        ],
    )
    fetcher.main()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    actual_file_bytes = sum(p.stat().st_size for p in output.rglob("*") if p.is_file())
    assert manifest["accounting"]["manifest_bytes"] == (output / "manifest.json").stat().st_size
    assert manifest["accounting"]["actual_stored_bytes"] == actual_file_bytes


def test_local_retrieval_contract_rejects_evaluator_shortcuts_and_has_stable_fusion():
    base = {
        "format": "ht-runtime-public-device-cohort-v1",
        "status": "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS",
        "devices": [{
            "query_id": "q1", "device_id_raw": "Device", "device_id_canonical": "P1:BASE",
            "company": "Example", "trade_name": "Device", "generic_name": "Valve",
            "product_code": "ABC", "technical_description": "mitral valve delivery",
            "features_of_interest": ["valve"], "source_id": "s1", "evidence_cutoff": "2026-01-01",
        }],
        "patents": [],
    }
    poisoned = json.loads(json.dumps(base))
    poisoned["devices"][0]["references"] = ["US000001A1"]
    with pytest.raises(ValueError, match="evaluator fields"):
        validate_runtime_payload(poisoned)
    patents = [
        PatentRecord("1", "US000001A1", "US-grant", "US", "Valve", "mitral valve", "claim", "mitral valve", "s1", "v1", "u", "a" * 64, "b" * 64, "2026-01-01", "Example", "source"),
        PatentRecord("2", "US000002A1", "US-grant", "US", "Pump", "pump", "claim", "pump", "s2", "v1", "u", "c" * 64, "d" * 64, "2026-01-01", "Example", "source"),
    ]
    ranked = BM25Index(patents).search("mitral valve", limit=2)
    assert ranked[0]["patent_id_canonical"] == "US000001A1"
    fused = reciprocal_rank_fusion([["US000001A1", "US000002A1"], ["US000002A1", "US000001A1"]])
    assert fused["US000001A1"] == pytest.approx(fused["US000002A1"])


def test_dossier_history_and_source_view_are_local_and_editable(tmp_path):
    example = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    dossier, _, _ = run_dossier(DossierInput.model_validate(example), run_id="history", code_commit="test")
    history = tmp_path / "history"
    save_version(history, dossier)
    edited = append_user_edits(history, {"e-device_name": "Review source name in both languages."})
    assert [item.version for item in load_versions(history)] == [1, 2]
    assert edited.parent_version == 1 and edited.user_edits["e-device_name"]
    view = source_view(edited, "synthetic-device-record", "device_name")
    assert view["payload"]["device_name"].startswith("SYNTHETIC")


def test_healthtech_dry_run_never_opens_network(monkeypatch):
    request = _api_request()
    monkeypatch.setattr(socket.socket, "connect", lambda *args, **kwargs: pytest.fail("dry-run opened a socket"))
    receipt = dispatch_healthtech_request(HealthTechAPIConfig(mode="dry_run"), request)
    assert receipt.status == "DRY_RUN_NOT_EXECUTED"
    assert receipt.network_attempts == receipt.provider_calls == 0
    assert receipt.paid_cost_usd == 0


def test_healthtech_api_rejects_evaluator_visibility_and_executes_only_fake_transport():
    with pytest.raises(ValidationError):
        HealthTechVisibleSource(source_id="evaluator-gold", source_version="v1", payload_hash=_source_hash())
    request = _api_request()
    response = MockHTTPResponse(200, {"choices": [{"message": {"content": json.dumps({"status": "ready", "request_id": request.request_id})}}]})
    receipt = dispatch_healthtech_request(HealthTechAPIConfig(mode="mock", model="healthtech-mock-v1"), request, transport=MockHTTPTransport(response))
    assert receipt.status == "MOCK_COMPLETE"
    assert receipt.provider_calls == 1 and receipt.network_attempts == 0 and receipt.paid_cost_usd == 0
    assert receipt.response_schema_valid is True and receipt.response["status"] == "ready"


def test_offline_baseline_controls_and_heuristic_are_explicitly_labeled():
    example = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
    company = deepcopy(example)
    company["query"]["company_metadata"] = {"applicant": "Fictional Demo Co"}
    company["query"]["company_source_id"] = "synthetic-device-record"
    company["query"]["acquisition_budget"]["max_search_calls"] = 1
    company["policy_id"] = "HT-B0a"
    _, company_events, company_manifest = run_dossier(DossierInput.model_validate(company), run_id="b0a", code_commit="test")
    assert company_events[0].action_type == "company_search"
    assert company_manifest.policy_id == "HT-B0a"

    hybrid = deepcopy(example)
    hybrid["policy_id"] = "HT-B1"
    dossier, hybrid_events, hybrid_manifest = run_dossier(DossierInput.model_validate(hybrid), run_id="b1", code_commit="test")
    assert hybrid_manifest.policy_id == "HT-B1"
    assert "hybrid_fixed" in dossier.candidates[0].scores
    assert "hybrid approximation" in hybrid_events[0].decision_summary

    adaptive = deepcopy(example)
    adaptive["policy_id"] = "HT-B3"
    adaptive["query"]["acquisition_budget"]["max_search_calls"] = 3
    _, adaptive_events, adaptive_manifest = run_dossier(DossierInput.model_validate(adaptive), run_id="b3", code_commit="test")
    assert adaptive_manifest.policy_id == "HT-B3"
    assert adaptive_events[-1].stop_reason == "policy_stop"
    assert adaptive_manifest.actual_search_calls == 1
