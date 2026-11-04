"""Compute source-binding and operational metrics for a frozen local Qwen receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def evaluate_operational(receipt: dict[str, Any], pack: dict[str, Any]) -> dict[str, Any]:
    """Evaluate deterministic contract/coverage properties, never semantic truth."""
    if receipt.get("pack_sha256") != pack.get("pack_sha256"):
        raise ValueError("receipt/pack hash binding mismatch")

    pack_cases = {case.get("case_id"): case for case in pack.get("cases", [])}
    receipt_cases = receipt.get("cases", [])
    if not isinstance(receipt_cases, list) or not receipt_cases:
        raise ValueError("receipt has no cases")

    case_results: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    total_findings = 0
    exact_bindings = 0
    classification_matches = 0
    emitted_evidence_ids: set[str] = set()
    total_evidence_rows = 0
    unresolved_cases = 0
    unresolved_items = 0
    classification_counts: dict[str, int] = {}

    for receipt_case in receipt_cases:
        case_id = receipt_case.get("case_id")
        pack_case = pack_cases.get(case_id)
        if not isinstance(pack_case, dict):
            raise ValueError(f"receipt case missing from pack: {case_id}")

        evidence_rows = pack_case.get("evidence", [])
        candidate_rows = pack_case.get("candidates", [])
        evidence_by_id = {
            row.get("evidence_id"): row for row in evidence_rows if row.get("evidence_id")
        }
        candidate_by_id = {
            row.get("patent_id_canonical"): row
            for row in candidate_rows
            if row.get("patent_id_canonical")
        }
        total_evidence_rows += len(evidence_by_id)
        parsed = receipt_case.get("parsed_output") or {}
        findings = parsed.get("findings") or []
        unresolved = parsed.get("unresolved") or []
        if unresolved:
            unresolved_cases += 1
            unresolved_items += len(unresolved)

        case_exact = 0
        case_classification = 0
        case_evidence_ids: set[str] = set()
        for index, finding in enumerate(findings):
            total_findings += 1
            classification = finding.get("classification")
            classification_counts[classification] = classification_counts.get(classification, 0) + 1
            record_id = finding.get("record_id")
            expected = evidence_by_id.get(record_id) or candidate_by_id.get(record_id)
            if not isinstance(expected, dict):
                errors.append({
                    "case_id": case_id,
                    "finding_index": index,
                    "error": "unknown_record_id",
                    "record_id": record_id,
                })
                continue

            exact = (
                finding.get("source_id") == expected.get("source_id")
                and finding.get("locator") == expected.get("locator")
            )
            if exact:
                exact_bindings += 1
                case_exact += 1
            else:
                errors.append({
                    "case_id": case_id,
                    "finding_index": index,
                    "error": "source_locator_mismatch",
                    "record_id": record_id,
                })

            if record_id in evidence_by_id:
                case_evidence_ids.add(record_id)
                evidence_kind = expected.get("evidence_kind")
                expected_classification = (
                    "disclosed_link" if evidence_kind == "patent_disclosure" else "source_fact"
                )
            else:
                expected_classification = expected.get("association_status")
            if classification == expected_classification:
                classification_matches += 1
                case_classification += 1
            else:
                errors.append({
                    "case_id": case_id,
                    "finding_index": index,
                    "error": "classification_contract_mismatch",
                    "record_id": record_id,
                    "expected": expected_classification,
                    "observed": classification,
                })
            emitted_evidence_ids.update(case_evidence_ids)

        case_results.append({
            "case_id": case_id,
            "schema_valid": bool(receipt_case.get("schema_valid")),
            "output_sha256": receipt_case.get("output_sha256"),
            "finding_count": len(findings),
            "unresolved_count": len(unresolved),
            "input_evidence_rows": len(evidence_by_id),
            "emitted_evidence_rows": len(case_evidence_ids),
            "exact_source_locator_bindings": case_exact,
            "classification_contract_matches": case_classification,
        })

    schema_valid_cases = sum(1 for case in receipt_cases if case.get("schema_valid") is True)
    total_cases = len(receipt_cases)
    exact_rate = exact_bindings / total_findings if total_findings else None
    classification_rate = classification_matches / total_findings if total_findings else None
    evidence_rate = len(emitted_evidence_ids) / total_evidence_rows if total_evidence_rows else None
    unresolved_rate = unresolved_cases / total_cases if total_cases else None
    latencies = [
        case.get("generation_latency_seconds")
        for case in receipt_cases
        if isinstance(case.get("generation_latency_seconds"), (int, float))
    ]
    mean_latency = receipt.get("mean_generation_latency_seconds")
    if mean_latency is None and latencies:
        mean_latency = sum(latencies) / len(latencies)

    return {
        "format": "ptp-local-qwen-operational-evaluation-v1",
        "status": "PASS_OPERATIONAL_SOURCE_BOUNDING" if not errors else "FAIL_OPERATIONAL_SOURCE_BOUNDING",
        "interpretation": (
            "Deterministic source/locator and workflow-coverage metrics only; "
            "not semantic relevance, retrieval accuracy, or adaptive superiority."
        ),
        "summary": {
            "case_count": total_cases,
            "schema_valid_cases": schema_valid_cases,
            "finding_count": total_findings,
            "exact_source_locator_bindings": exact_bindings,
            "exact_source_locator_rate": exact_rate,
            "classification_contract_matches": classification_matches,
            "classification_contract_rate": classification_rate,
            "input_evidence_rows": total_evidence_rows,
            "emitted_unique_evidence_rows": len(emitted_evidence_ids),
            "evidence_coverage_rate": evidence_rate,
            "cases_with_unresolved_items": unresolved_cases,
            "unresolved_visibility_rate": unresolved_rate,
            "unresolved_item_count": unresolved_items,
            "classification_counts": classification_counts,
        },
        "resource_summary": {
            "model_id": receipt.get("model_id"),
            "model_revision": receipt.get("model_revision"),
            "total_prompt_tokens": sum(case.get("prompt_tokens", 0) for case in receipt_cases),
            "total_output_tokens": sum(case.get("output_tokens", 0) for case in receipt_cases),
            "mean_generation_latency_seconds": mean_latency,
            "provider_calls": receipt.get("provider_calls"),
            "paid_cost_usd": receipt.get("paid_cost_usd"),
            "pack_sha256": receipt.get("pack_sha256"),
        },
        "cases": case_results,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    result = evaluate_operational(_load(args.receipt), _load(args.pack))
    result["inputs"] = {
        "receipt_sha256": _sha256(args.receipt),
        "pack_file_sha256": _sha256(args.pack),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, sort_keys=True))
    return 0 if result["status"].startswith("PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
