"""Build a deterministic engineering analysis from G5 task receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from statistics import median
from typing import Any


REPO = Path(__file__).resolve().parents[2]
PASS_STATUS = "PASS_OFFLINE_ENGINEERING_TASK"
FAIL_STATUS = "FAILED_OFFLINE_ENGINEERING_TASK"
SUPPORTED_STATUSES = {PASS_STATUS, FAIL_STATUS}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _artifact_path(receipt_path: Path, relative: str) -> Path:
    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValueError(f"receipt contains unsafe artifact path: {relative}")
    resolved = (receipt_path.parent / candidate).resolve()
    root = receipt_path.parent.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"artifact escapes receipt directory: {relative}")
    return resolved


def _validate_receipt(path: Path) -> tuple[dict[str, Any], dict[str, bool]]:
    receipt = _read_json(path)
    if receipt.get("format") != "ht-g5-pilot-task-receipt-v1":
        raise ValueError(f"unsupported G5 receipt format: {path}")
    status = receipt.get("status")
    if status not in SUPPORTED_STATUSES:
        raise ValueError(f"unsupported G5 receipt status {status!r}: {path}")
    case = receipt.get("case")
    if not isinstance(case, dict) or not isinstance(case.get("query_id"), str):
        raise ValueError(f"receipt lacks case.query_id: {path}")
    elapsed = receipt.get("engineering_execution_seconds")
    if not isinstance(elapsed, (int, float)) or isinstance(elapsed, bool) or elapsed < 0:
        raise ValueError(f"receipt has invalid engineering execution time: {path}")
    for key in ("provider_calls", "network_calls"):
        value = receipt.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError(f"receipt has invalid {key}: {path}")
    paid = receipt.get("paid_cost_usd")
    if not isinstance(paid, (int, float)) or isinstance(paid, bool) or paid < 0:
        raise ValueError(f"receipt has invalid paid_cost_usd: {path}")

    artifacts: dict[str, bool] = {}
    if status == PASS_STATUS:
        declared = receipt.get("artifact_sha256")
        if not isinstance(declared, dict) or not declared:
            raise ValueError(f"successful receipt lacks artifact hashes: {path}")
        for relative, expected in sorted(declared.items()):
            if not isinstance(relative, str) or not isinstance(expected, str) or len(expected) != 64:
                raise ValueError(f"malformed artifact hash in receipt: {path}")
            artifact = _artifact_path(path, relative)
            if not artifact.is_file():
                raise FileNotFoundError(f"receipt artifact missing: {artifact}")
            actual = _sha256(artifact)
            artifacts[relative] = actual == expected
            if actual != expected:
                raise ValueError(f"receipt artifact hash mismatch: {artifact}")
    return receipt, artifacts


def build_analysis(receipt_paths: list[Path]) -> dict[str, Any]:
    if not receipt_paths:
        raise ValueError("at least one G5 receipt is required")
    rows: list[dict[str, Any]] = []
    receipt_hashes: dict[str, str] = {}
    query_ids: set[str] = set()
    artifact_checks: Counter[str] = Counter()
    failure_types: Counter[str] = Counter()
    failure_stages: Counter[str] = Counter()
    external_statuses: Counter[str] = Counter()
    total_provider_calls = 0
    total_network_calls = 0
    total_paid = 0.0
    durations: list[float] = []
    candidate_totals = Counter()

    for raw_path in receipt_paths:
        path = raw_path.resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        receipt, artifacts = _validate_receipt(path)
        query_id = receipt["case"]["query_id"]
        if query_id in query_ids:
            raise ValueError(f"duplicate G5 query_id: {query_id}")
        query_ids.add(query_id)
        status = receipt["status"]
        elapsed = float(receipt["engineering_execution_seconds"])
        durations.append(elapsed)
        total_provider_calls += receipt["provider_calls"]
        total_network_calls += receipt["network_calls"]
        total_paid += float(receipt["paid_cost_usd"])
        receipt_hashes[_display_path(path)] = _sha256(path)
        artifact_checks.update({"checked": len(artifacts), "passed": sum(artifacts.values())})
        if status == FAIL_STATUS:
            failure_types[str(receipt.get("failure_type", "UNKNOWN"))] += 1
            failure_stages[str(receipt.get("failure_stage", "UNKNOWN"))] += 1
        external_projection = receipt.get("external_projection")
        if isinstance(external_projection, dict):
            external_statuses[str(external_projection.get("status", "UNKNOWN"))] += 1
        candidate_counts = receipt.get("candidate_counts")
        if isinstance(candidate_counts, dict):
            for key in ("disclosed_link", "retrieved_candidate", "total"):
                value = candidate_counts.get(key)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    candidate_totals[key] += value
        source_inspection = receipt.get("source_inspection")
        rows.append(
            {
                "query_id": query_id,
                "device_id_canonical": receipt["case"].get("device_id_canonical"),
                "company": receipt["case"].get("company"),
                "status": status,
                "purpose": receipt.get("purpose"),
                "source_id": source_inspection.get("source_id") if isinstance(source_inspection, dict) else None,
                "field": source_inspection.get("field") if isinstance(source_inspection, dict) else None,
                "engineering_execution_seconds": elapsed,
                "provider_calls": receipt["provider_calls"],
                "network_calls": receipt["network_calls"],
                "paid_cost_usd": float(receipt["paid_cost_usd"]),
                "external_projection_status": external_projection.get("status") if isinstance(external_projection, dict) else None,
                "artifact_hashes_checked": len(artifacts),
                "artifact_hashes_passed": sum(artifacts.values()),
            }
        )

    passed = sum(row["status"] == PASS_STATUS for row in rows)
    failed = len(rows) - passed
    analysis = {
        "format": "ht-g5-pilot-task-analysis-v1",
        "status": "PASS_G5_PILOT_ANALYSIS_ENGINEERING_ONLY",
        "receipt_count": len(rows),
        "pass_count": passed,
        "failure_count": failed,
        "success_rate": passed / len(rows),
        "engineering_execution_seconds": {
            "total": sum(durations),
            "min": min(durations),
            "median": median(durations),
            "max": max(durations),
        },
        "candidate_counts": dict(sorted(candidate_totals.items())),
        "external_projection_status_counts": dict(sorted(external_statuses.items())),
        "failure_type_counts": dict(sorted(failure_types.items())),
        "failure_stage_counts": dict(sorted(failure_stages.items())),
        "provider_calls": total_provider_calls,
        "network_calls": total_network_calls,
        "paid_cost_usd": total_paid,
        "artifact_hashes": {
            "checked": artifact_checks["checked"],
            "passed": artifact_checks["passed"],
        },
        "receipt_hashes": receipt_hashes,
        "cases": sorted(rows, key=lambda row: row["query_id"]),
        "limitations": [
            "This is an engineering dry-run analysis, not participant task time or a service-level claim.",
            "No participant, usability, willingness-to-pay, repeat-use, or commercial validation is inferred.",
            "Product-level disclosed links are not semantic relevance gold; unlisted pairs remain UNJUDGED.",
            "No provider request, restricted payload transfer, or paid inference is represented by this analysis.",
        ],
    }
    return analysis


def render_report(analysis: dict[str, Any]) -> str:
    timing = analysis["engineering_execution_seconds"]
    lines = [
        "# HT-G5 pilot-task engineering analysis",
        "",
        f"- Status: `{analysis['status']}`",
        f"- Receipts: `{analysis['receipt_count']}` ({analysis['pass_count']} pass, {analysis['failure_count']} failure)",
        f"- Success rate: `{analysis['success_rate']:.4f}`",
        f"- Engineering time total / median / min / max: `{timing['total']:.4f}s` / `{timing['median']:.4f}s` / `{timing['min']:.4f}s` / `{timing['max']:.4f}s`",
        f"- Provider calls / network calls / paid cost: `{analysis['provider_calls']}` / `{analysis['network_calls']}` / `USD {analysis['paid_cost_usd']:.2f}`",
        f"- Artifact hashes: `{analysis['artifact_hashes']['passed']}/{analysis['artifact_hashes']['checked']}` passed",
        "",
        "| Case | Status | Engineering seconds | Source field | External projection |",
        "|---|---|---:|---|---|",
    ]
    for row in analysis["cases"]:
        lines.append(
            f"| {row['query_id']} | {row['status']} | {row['engineering_execution_seconds']:.4f} | "
            f"{row['source_id']}:{row['field']} | {row['external_projection_status'] or 'NOT_REPORTED'} |"
        )
    lines.extend(
        [
            "",
            "This analysis summarizes local engineering receipts only. Engineering seconds are not participant task time and do not measure human task burden, commercial demand, semantic patent relevance, clinical suitability, FTO, patent validity, investment merit, or publication readiness.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(output: Path, analysis: dict[str, Any]) -> None:
    if output.exists():
        raise ValueError(f"output already exists: {output}")
    output.mkdir(parents=True, exist_ok=False)
    (output / "analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "ANALYSIS.md").write_text(render_report(analysis), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("receipts", type=Path, nargs="+")
    args = parser.parse_args()
    analysis = build_analysis(args.receipts)
    write_outputs(args.output, analysis)
    print(json.dumps({"status": analysis["status"], "output": str(args.output), "receipt_count": analysis["receipt_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
