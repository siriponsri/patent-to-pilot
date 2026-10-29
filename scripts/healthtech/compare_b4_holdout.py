"""Compare the HT-B4 provider-shaped mock with frozen holdout controls."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any


METHODS = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _b4_row(frontier: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    per_device = frontier.get("per_device", [])
    return {
        "method": "HT-B4-MOCK",
        "macro_known_link_recall_at_20": frontier.get("macro_known_link_recall_at_20"),
        "micro_known_link_recall_at_20": frontier.get("micro_known_link_recall_at_20"),
        "device_count": frontier.get("device_count"),
        "failed_device_count": frontier.get("failed_device_count"),
        "provider_shaped_calls": frontier.get("provider_calls", 0),
        "query_calls": frontier.get("resources", {}).get("query_calls", 0),
        "rerank_pairs": frontier.get("resources", {}).get("rerank_pairs", 0),
        "wall_seconds": sum(row.get("resources", {}).get("method_wall_seconds", 0) for row in per_device),
        "cpu_seconds": sum(row.get("resources", {}).get("method_cpu_seconds", 0) for row in per_device),
        "paid_cost_usd": receipt.get("paid_cost_usd", 0.0),
        "simulated_cost_usd": receipt.get("simulated_cost_usd", 0.0),
        "unknown_billing": len(receipt.get("ledger_snapshot", {}).get("unknown_or_pending", [])),
        "ledger_breach": receipt.get("ledger_snapshot", {}).get("breach"),
        "model": receipt.get("policy", {}).get("models"),
        "pricing_snapshot_sha256": receipt.get("policy", {}).get("pricing_snapshot_sha256"),
        "pricing_snapshot_utc": receipt.get("policy", {}).get("pricing_snapshot_utc"),
        "status": "MOCK_ONLY_NOT_PROVIDER_EVIDENCE",
    }


def build_comparison(
    *,
    offline_frontier: dict[str, Any],
    b4_frontier: dict[str, Any],
    b4_receipt: dict[str, Any],
    code_commit: str,
    protocol_hash: str,
    cohort_manifest_hash: str,
    input_hashes: dict[str, str] | None = None,
) -> dict[str, Any]:
    offline_rows = []
    for method in METHODS:
        metrics = offline_frontier.get("by_method", {}).get(method)
        if not isinstance(metrics, dict):
            raise ValueError(f"offline frontier lacks {method}")
        offline_rows.append(
            {
                "method": method,
                "macro_known_link_recall_at_20": metrics.get("macro_known_link_recall_at_20"),
                "device_count": metrics.get("device_count"),
                "failed_device_count": metrics.get("failed_device_count", 0),
                "query_calls": metrics.get("query_calls", 0),
                "rerank_pairs": metrics.get("rerank_pairs", 0),
                "wall_seconds": None,
                "paid_cost_usd": 0.0,
                "status": "OFFLINE_CONTROL",
            }
        )
    b4_row = _b4_row(b4_frontier, b4_receipt)
    by_method = {row["method"]: row for row in offline_rows}
    b4_recall = b4_row["macro_known_link_recall_at_20"]
    deltas = []
    for method in METHODS:
        deltas.append(
            {
                "method": method,
                "b4_minus_control_macro_recall": b4_recall - by_method[method]["macro_known_link_recall_at_20"],
                "status": "DESCRIPTIVE_NOT_ESTIMABLE",
            }
        )
    return {
        "format": "ht-b4-holdout-comparison-v1",
        "status": "PASS_B4_PROVIDER_SHAPED_HOLDOUT_DESCRIPTIVE",
        "code_commit": code_commit,
        "protocol_hash": protocol_hash,
        "cohort_manifest_hash": cohort_manifest_hash,
        "split": "final_holdout",
        "offline_controls": offline_rows,
        "b4_provider_shaped_mock": b4_row,
        "deltas_vs_controls": deltas,
        "interpretation": [
            "The fixed-policy HT-B4 mock matches HT-B3 on holdout macro known-link recall in this run.",
            "The HT-B4 mock is below HT-B0b, HT-B1, and HT-B2 on holdout macro known-link recall in this run.",
            "Mock provider-shaped calls exercise the action schema and accounting path but are not live-provider evidence.",
            "The holdout remains a small company-level transfer check with product-level disclosures, unjudged pairs, and NOT_ESTIMABLE generalization.",
        ],
        "input_hashes": input_hashes or {},
    }


def render_report(comparison: dict[str, Any]) -> str:
    lines = [
        "# HT-B4 provider-shaped holdout comparison",
        "",
        f"- Status: `{comparison['status']}`",
        f"- Code tested: `{comparison['code_commit']}`",
        f"- Protocol hash: `{comparison['protocol_hash']}`",
        f"- Cohort manifest hash: `{comparison['cohort_manifest_hash']}`",
        "- Split: `final_holdout`; endpoint: macro known-link recall at K=20.",
        "",
        "| Method | Macro known-link R@20 | Calls | Rerank pairs | Paid cost | Status |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in comparison["offline_controls"] + [comparison["b4_provider_shaped_mock"]]:
        calls = row.get("provider_shaped_calls", row.get("query_calls", 0))
        paid = row.get("paid_cost_usd", 0.0)
        lines.append(
            f"| {row['method']} | {row['macro_known_link_recall_at_20']:.4f} | {calls} | {row.get('rerank_pairs', 0)} | ${paid:.4f} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            f"HT-B4 mock simulated debit: `${comparison['b4_provider_shaped_mock']['simulated_cost_usd']:.4f}`; unknown/pending billing items: `{comparison['b4_provider_shaped_mock']['unknown_billing']}`; ledger breach: `{comparison['b4_provider_shaped_mock']['ledger_breach']}`.",
            "",
            "## B4 minus fixed controls",
            "",
            "| Control | Macro recall delta | Status |",
            "|---|---:|---|",
        ]
    )
    for row in comparison["deltas_vs_controls"]:
        lines.append(f"| {row['method']} | {row['b4_minus_control_macro_recall']:.4f} | {row['status']} |")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {statement}" for statement in comparison["interpretation"])
    return "\n".join(lines) + "\n"


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(output: Path, comparison: dict[str, Any]) -> None:
    output.mkdir(parents=True)
    (output / "comparison.json").write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output / "COMPARISON.md").write_text(render_report(comparison), encoding="utf-8")
    _write_csv(output / "comparison.csv", comparison["offline_controls"] + [comparison["b4_provider_shaped_mock"]])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline-frontier", type=Path, required=True)
    parser.add_argument("--b4-frontier", type=Path, required=True)
    parser.add_argument("--b4-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--protocol-hash", required=True)
    parser.add_argument("--cohort-manifest-hash", required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    input_hashes = {str(path): _sha256(path) for path in (args.offline_frontier, args.b4_frontier, args.b4_receipt)}
    comparison = build_comparison(
        offline_frontier=_read_json(args.offline_frontier),
        b4_frontier=_read_json(args.b4_frontier),
        b4_receipt=_read_json(args.b4_receipt),
        code_commit=args.code_commit,
        protocol_hash=args.protocol_hash,
        cohort_manifest_hash=args.cohort_manifest_hash,
        input_hashes=input_hashes,
    )
    write_outputs(args.output, comparison)
    print(json.dumps({"status": comparison["status"], "output": str(args.output), "b4_recall": comparison["b4_provider_shaped_mock"]["macro_known_link_recall_at_20"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
