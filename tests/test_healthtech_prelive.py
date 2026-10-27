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
    evaluate_predictions,
    load_gold_claims,
    load_runtime_claims,
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
