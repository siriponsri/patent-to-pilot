import json
from pathlib import Path

import pytest

from scripts.healthtech.analyze_pilot_tasks import build_analysis, write_outputs


def _write_receipt(root: Path, query_id: str, *, status: str = "PASS_OFFLINE_ENGINEERING_TASK", bad_hash: bool = False) -> Path:
    case = root / query_id
    case.mkdir(parents=True)
    artifact = case / "source_inspection.json"
    artifact.write_text('{"source_id":"fixture"}\n', encoding="utf-8")
    import hashlib

    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    receipt = {
        "format": "ht-g5-pilot-task-receipt-v1",
        "status": status,
        "case": {"query_id": query_id, "device_id_canonical": query_id, "company": "Fixture"},
        "purpose": "local_research",
        "engineering_execution_seconds": 0.25,
        "provider_calls": 0,
        "network_calls": 0,
        "paid_cost_usd": 0.0,
        "candidate_counts": {"disclosed_link": 1, "retrieved_candidate": 2, "total": 3},
        "source_inspection": {"source_id": "fixture-source", "field": "pma_number"},
        "external_projection": {"status": "BLOCKED_LOCAL", "payload_written": False},
    }
    if status == "PASS_OFFLINE_ENGINEERING_TASK":
        receipt["artifact_sha256"] = {"source_inspection.json": "0" * 64 if bad_hash else digest}
    else:
        receipt["failure_type"] = "RightsBoundaryError"
        receipt["failure_stage"] = "build_rights_aware_json_export"
    path = case / "task_receipt.json"
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return path


def test_builds_deterministic_summary_and_report(tmp_path):
    pass_receipt = _write_receipt(tmp_path, "case-pass")
    fail_receipt = _write_receipt(tmp_path, "case-fail", status="FAILED_OFFLINE_ENGINEERING_TASK")

    analysis = build_analysis([pass_receipt, fail_receipt])
    assert analysis["receipt_count"] == 2
    assert analysis["pass_count"] == 1
    assert analysis["failure_count"] == 1
    assert analysis["failure_type_counts"] == {"RightsBoundaryError": 1}
    assert analysis["artifact_hashes"] == {"checked": 1, "passed": 1}
    assert analysis["paid_cost_usd"] == 0.0

    output = tmp_path / "analysis"
    write_outputs(output, analysis)
    assert json.loads((output / "analysis.json").read_text(encoding="utf-8"))["status"] == analysis["status"]
    assert "participant task time" in (output / "ANALYSIS.md").read_text(encoding="utf-8")


def test_rejects_artifact_hash_mismatch(tmp_path):
    receipt = _write_receipt(tmp_path, "case-bad", bad_hash=True)
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        build_analysis([receipt])


def test_rejects_duplicate_query_ids(tmp_path):
    first = _write_receipt(tmp_path / "a", "same-case")
    second = _write_receipt(tmp_path / "b", "same-case")
    with pytest.raises(ValueError, match="duplicate G5 query_id"):
        build_analysis([first, second])
