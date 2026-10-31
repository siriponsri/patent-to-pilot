from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "healthtech" / "build_qwen_evidence_pack.py"
RUNNER = Path(__file__).resolve().parents[1] / "scripts" / "healthtech" / "run_qwen_generation_evidence_pack.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_dossier(root: Path, case_id: str, index: int) -> None:
    source_id = f"source-{index}"
    dossier = {
        "query": {
            "query_id": case_id,
            "device_id_canonical": case_id,
            "device_id_raw": case_id,
            "jurisdiction": "US",
            "brief": "Bounded local test case",
            "technical_description": "Synthetic device description",
            "features_of_interest": ["feature"],
            "user_questions": ["What is supported?"],
            "evidence_cutoff": "2026-10-27",
            "permitted_inputs": [source_id],
            "selected_comparator_source_id": source_id,
        },
        "evidence": [{
            "evidence_id": f"evidence-{index}",
            "evidence_kind": "regulatory_record",
            "jurisdiction": "US",
            "locator": "field:trade_name",
            "payload_hash": "a" * 64,
            "source_date": "2026-10-27",
            "source_id": source_id,
            "source_version": "test",
            "statement": "trade_name: Synthetic",
            "structured_field": "trade_name",
            "structured_value": "Synthetic",
            "support_basis": "Supplied source field",
            "verification_status": "field_value_checked",
        }],
        "candidates": [{
            "association_status": "retrieved_candidate",
            "disclosure_evidence_id": None,
            "family_id": None,
            "family_source_id": None,
            "patent_id_canonical": f"US{index}B2",
            "patent_id_raw": f"US{index}B2",
            "retrieval_action_ids": ["step-1"],
            "scores": {"score": 1.0},
            "source_id": source_id,
            "source_revision": "test",
        }],
        "sources": [{
            "jurisdiction": "US",
            "payload": {"secret_payload": "must not be copied"},
            "rights": {
                "rights_id": "test-rights",
                "local_evaluation": "ALLOWED_LOCAL_RESEARCH",
                "product_display": "BLOCKED_LOCAL",
                "redistribution": "BLOCKED_LOCAL",
                "displayable_fields": [],
            },
            "source": {
                "source_id": source_id,
                "source_type": "regulatory_record",
                "version_label": "test",
                "sha256": "b" * 64,
                "uri": "https://example.invalid/source",
                "locator": "field:trade_name",
                "record_id": source_id,
                "retrieved_at": "2026-10-27T00:00:00",
                "limits": ["synthetic"],
            },
            "source_date": "2026-10-27",
            "synthetic": True,
        }],
        "unresolved_items": ["Synthetic fixture only"],
    }
    case_dir = root / case_id
    case_dir.mkdir(parents=True)
    (case_dir / "dossier.json").write_text(json.dumps(dossier), encoding="utf-8")


def test_build_pack_preserves_order_and_excludes_payloads(tmp_path: Path) -> None:
    builder = _load(SCRIPT, "qwen_pack_builder")
    for index, case_id in enumerate(builder.CASE_ORDER, start=1):
        _write_dossier(tmp_path / "dossiers", case_id, index)
    output = tmp_path / "pack.json"
    pack = builder.build_pack(tmp_path / "dossiers", output, captured_at_utc="2026-10-31T00:00:00Z")
    assert pack["pack_sha256"]
    assert [case["case_id"] for case in pack["cases"]] == builder.CASE_ORDER
    assert all(len(case["evidence"]) == 1 for case in pack["cases"])
    assert all("payload" not in source for case in pack["cases"] for source in case["sources"])
    assert "qrels and gold-derived queries" in pack["runtime_exclusions"]


def test_runner_rejects_unknown_source_locator(tmp_path: Path) -> None:
    builder = _load(SCRIPT, "qwen_pack_builder_for_runner")
    try:
        runner = _load(RUNNER, "qwen_pack_runner")
    except ModuleNotFoundError as exc:
        pytest.skip(f"runtime dependency unavailable: {exc}")
    for index, case_id in enumerate(builder.CASE_ORDER, start=1):
        _write_dossier(tmp_path / "dossiers", case_id, index)
    pack = builder.build_pack(tmp_path / "dossiers", tmp_path / "pack.json", captured_at_utc="2026-10-31T00:00:00Z")
    case = pack["cases"][0]
    valid = {
        "device_id": case["query"]["device_id_canonical"],
        "device_name": case["query"]["device_id_raw"],
        "findings": [{
            "record_type": "evidence",
            "record_id": case["evidence"][0]["evidence_id"],
            "source_id": case["evidence"][0]["source_id"],
            "locator": case["evidence"][0]["locator"],
            "classification": "source_fact",
            "summary": "Source-backed fact",
            "support_basis": "Supplied source field",
        }],
        "unresolved": [],
    }
    runner._validate_output(valid, case, max_findings=6)
    invalid = json.loads(json.dumps(valid))
    invalid["findings"][0]["locator"] = "field:wrong"
    with pytest.raises(ValueError, match="source_id/locator mismatch"):
        runner._validate_output(invalid, case, max_findings=6)
