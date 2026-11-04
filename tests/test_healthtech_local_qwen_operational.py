from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "healthtech" / "evaluate_local_qwen_operational.py"


def _load():
    spec = importlib.util.spec_from_file_location("local_qwen_operational", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fixtures():
    pack = {
        "pack_sha256": "p" * 64,
        "cases": [{
            "case_id": "CASE-1",
            "evidence": [
                {
                    "evidence_id": "FACT-1",
                    "evidence_kind": "regulatory_record",
                    "source_id": "source-1",
                    "locator": "field:name",
                },
                {
                    "evidence_id": "DISC-1",
                    "evidence_kind": "patent_disclosure",
                    "source_id": "source-2",
                    "locator": "field:patents",
                },
            ],
            "candidates": [{
                "patent_id_canonical": "US1B2",
                "association_status": "retrieved_candidate",
                "source_id": "source-3",
                "locator": "candidate:US1B2",
            }],
        }],
    }
    receipt = {
        "pack_sha256": "p" * 64,
        "model_id": "Qwen/Qwen3-8B",
        "model_revision": "test",
        "cases": [{
            "case_id": "CASE-1",
            "schema_valid": True,
            "output_sha256": "o" * 64,
            "prompt_tokens": 10,
            "output_tokens": 5,
            "generation_latency_seconds": 2.0,
            "parsed_output": {
                "findings": [
                    {
                        "record_id": "FACT-1",
                        "source_id": "source-1",
                        "locator": "field:name",
                        "classification": "source_fact",
                    },
                    {
                        "record_id": "DISC-1",
                        "source_id": "source-2",
                        "locator": "field:patents",
                        "classification": "disclosed_link",
                    },
                ],
                "unresolved": ["candidate not independently checked"],
            },
        }],
    }
    return receipt, pack


def test_operational_evaluation_counts_binding_coverage_and_unknowns():
    module = _load()
    receipt, pack = _fixtures()
    result = module.evaluate_operational(receipt, pack)
    assert result["status"] == "PASS_OPERATIONAL_SOURCE_BOUNDING"
    assert result["summary"]["exact_source_locator_rate"] == 1.0
    assert result["summary"]["classification_contract_rate"] == 1.0
    assert result["summary"]["evidence_coverage_rate"] == 1.0
    assert result["summary"]["unresolved_visibility_rate"] == 1.0
    assert result["resource_summary"]["mean_generation_latency_seconds"] == 2.0


def test_operational_evaluation_fails_closed_on_locator_drift():
    module = _load()
    receipt, pack = _fixtures()
    receipt["cases"][0]["parsed_output"]["findings"][0]["locator"] = "field:wrong"
    result = module.evaluate_operational(receipt, pack)
    assert result["status"] == "FAIL_OPERATIONAL_SOURCE_BOUNDING"
    assert any(error["error"] == "source_locator_mismatch" for error in result["errors"])


def test_operational_evaluation_rejects_pack_hash_drift():
    module = _load()
    receipt, pack = _fixtures()
    receipt["pack_sha256"] = "x" * 64
    with pytest.raises(ValueError, match="hash binding mismatch"):
        module.evaluate_operational(receipt, pack)
