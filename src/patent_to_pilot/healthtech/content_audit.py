"""Deterministic content audit of schema-valid generation outputs.

Checks each finding against the exact evidence row the model received. This
establishes literal source fidelity only; it is not semantic entailment, and
schema validity is not content correctness.
"""
from __future__ import annotations

import re
from typing import Any

RUBRIC_VERSION = "ptp-generation-content-audit-v1"
# Wording that would go beyond FDA structured fields (regulatory status,
# clinical, legal/patent or commercial inference).
INFERENCE_TERMS = (
    "approved", "approval", "cleared", "clearance", "safe", "safety", "effective",
    "efficacy", "clinical", "patent", "infring", "freedom to operate", "valid",
    "market", "revenue", "invest", "recommend", "should", "superior", "better",
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().casefold()


def audit_finding(finding: dict[str, Any], evidence_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = evidence_by_id.get(finding.get("record_id"))
    result = {"record_id": finding.get("record_id"), "issues": []}
    if row is None:
        result["label"] = "unsupported"
        result["issues"].append("unknown_record_id")
        return result
    if finding.get("source_id") != row["source_id"] or finding.get("locator") != row["locator"]:
        result["issues"].append("citation_mismatch")
    if finding.get("classification") != "source_fact":
        result["issues"].append("classification_not_source_fact")
    if finding.get("support_basis") != row.get("support_basis"):
        result["issues"].append("support_basis_altered")
    summary = _norm(str(finding.get("summary", "")))
    value = _norm(str(row["structured_value"]))
    value_present = bool(value) and value in summary
    if not value_present:
        result["issues"].append("value_not_present")
    terms = sorted({term for term in INFERENCE_TERMS if term in summary and term not in value})
    if terms:
        result["issues"].append("inference_terms:" + ",".join(terms))
    if not value_present:
        result["label"] = "incorrect_or_unsupported"
    elif "citation_mismatch" in result["issues"]:
        result["label"] = "correct_value_wrong_citation"
    elif terms:
        result["label"] = "correct_value_with_extra_inference"
    elif result["issues"]:
        result["label"] = "correct_value_metadata_issue"
    else:
        result["label"] = "correct"
    return result


def audit_case(case: dict[str, Any], parsed: dict[str, Any]) -> dict[str, Any]:
    """Audit one parsed output against its frozen evidence case."""
    evidence_by_id = {row["evidence_id"]: row for row in case["evidence"]}
    findings = [audit_finding(f, evidence_by_id) for f in parsed.get("findings", [])]
    cited = [f["record_id"] for f in findings]
    duplicates = sorted({rid for rid in cited if cited.count(rid) > 1})
    missing = sorted(set(evidence_by_id) - set(cited))
    query = case["query"]
    trade_names = [row["structured_value"] for row in case["evidence"] if row.get("structured_field") == "trade_name"]
    device_name_ok = _norm(str(parsed.get("device_name", ""))) in {_norm(t) for t in trade_names} or (
        _norm(str(parsed.get("device_name", ""))) in _norm(query.get("device_id_raw", "")))
    labels = [f["label"] for f in findings]
    return {
        "rubric_version": RUBRIC_VERSION,
        "case_id": case["case_id"],
        "device_id_matches_query": parsed.get("device_id") == query["device_id_canonical"],
        "device_name_supported": device_name_ok,
        "evidence_rows": len(evidence_by_id),
        "findings": len(findings),
        "correct": labels.count("correct"),
        "incorrect_or_unsupported": sum(label in {"incorrect_or_unsupported", "unsupported"} for label in labels),
        "flagged_other": sum(label not in {"correct", "incorrect_or_unsupported", "unsupported"} for label in labels),
        "missing_evidence_ids": missing,
        "duplicate_citations": duplicates,
        "unresolved_reported": len(parsed.get("unresolved", [])),
        "unresolved_expected": len(case.get("unresolved_items", [])),
        "finding_results": findings,
    }
