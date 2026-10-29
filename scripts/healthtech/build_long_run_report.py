"""Build a reproducible HealthTech long-run report from frozen outputs."""
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


def _method_rows(frontier: dict[str, Any], method_summary: dict[str, Any], split: str) -> list[dict[str, Any]]:
    by_method = frontier.get("by_method")
    if not isinstance(by_method, dict):
        raise ValueError("frontier lacks by_method")
    rows: list[dict[str, Any]] = []
    for method in METHODS:
        metrics = by_method.get(method)
        resources = method_summary.get(method)
        if not isinstance(metrics, dict) or not isinstance(resources, dict):
            raise ValueError(f"frontier or method summary lacks {method}")
        groups = {
            str(row.get("group_id"))
            for row in frontier.get("groups", [])
            if isinstance(row, dict) and row.get("method") == method
        }
        rows.append({
            "split": split,
            "method": method,
            "query_count": int(metrics.get("realized_query_count", 0)),
            "group_count": len(groups),
            "macro_known_link_recall_at_20": metrics.get("macro_known_link_recall_at_20"),
            "query_calls": metrics.get("query_calls", 0),
            "rerank_pairs": metrics.get("rerank_pairs", 0),
            "embedding_query_tokens": metrics.get("embedding_query_tokens", 0),
            "rerank_tokens": metrics.get("rerank_tokens", 0),
            "returned_candidates": metrics.get("returned_candidates", 0),
            "wall_seconds": resources.get("resources", {}).get("method_wall_seconds", 0),
            "cpu_seconds": resources.get("resources", {}).get("method_cpu_seconds", 0),
            "failed_query_count": metrics.get("failed_device_count", 0),
            "paid_cost_usd": 0.0,
            "unknown_billing": 0,
        })
    return rows


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"expected JSON object in {path}")
            rows.append(value)
    return rows


def _b4_row(frontier: dict[str, Any], receipt: dict[str, Any], raw_rankings: list[dict[str, Any]]) -> dict[str, Any]:
    calls = [
        action["controller_call"]
        for row in raw_rankings
        for action in row.get("actions", [])
        if isinstance(action, dict) and isinstance(action.get("controller_call"), dict)
    ]
    return {
        "split": "development",
        "method": "HT-B4-MOCK",
        "query_count": frontier.get("device_count", 0),
        "group_count": None,
        "macro_known_link_recall_at_20": frontier.get("macro_known_link_recall_at_20"),
        "query_calls": sum(row.get("resources", {}).get("query_calls", 0) for row in frontier.get("per_device", [])),
        "rerank_pairs": sum(row.get("resources", {}).get("rerank_pairs", 0) for row in frontier.get("per_device", [])),
        "embedding_query_tokens": sum(row.get("resources", {}).get("embedding_query_tokens", 0) for row in frontier.get("per_device", [])),
        "rerank_tokens": sum(row.get("resources", {}).get("rerank_tokens", 0) for row in frontier.get("per_device", [])),
        "returned_candidates": sum(row.get("resources", {}).get("returned_candidates", 0) for row in frontier.get("per_device", [])),
        "wall_seconds": sum(row.get("resources", {}).get("method_wall_seconds", 0) for row in frontier.get("per_device", [])),
        "cpu_seconds": sum(row.get("resources", {}).get("method_cpu_seconds", 0) for row in frontier.get("per_device", [])),
        "failed_query_count": frontier.get("failed_device_count", 0),
        "provider_shaped_calls": len(calls),
        "input_token_bound": sum(call.get("input_token_bound", 0) for call in calls),
        "output_token_bound": sum(call.get("output_token_bound", 0) for call in calls),
        "latency_seconds": sum(call.get("latency_seconds", 0) for call in calls),
        "schema_valid_calls": sum(bool(call.get("response_schema_valid")) for call in calls),
        "paid_cost_usd": receipt.get("paid_cost_usd", 0.0),
        "simulated_cost_usd": receipt.get("simulated_cost_usd", 0.0),
        "unknown_billing": len(receipt.get("ledger_snapshot", {}).get("unknown_or_pending", [])),
        "ledger_actual_nano_usd": receipt.get("ledger_snapshot", {}).get("actual_nano_usd"),
        "model": receipt.get("policy", {}).get("models"),
        "pricing_snapshot_sha256": receipt.get("policy", {}).get("pricing_snapshot_sha256"),
        "pricing_snapshot_utc": receipt.get("policy", {}).get("pricing_snapshot_utc"),
    }


def build_summary(
    *,
    dev_frontier: Path,
    dev_summary: Path,
    dev_receipt: Path,
    holdout_frontier: Path,
    holdout_summary: Path,
    holdout_receipt: Path,
    b4_frontier: Path,
    b4_receipt: Path,
    b4_raw_rankings: Path,
    b4_verification: Path,
    code_commit: str,
    protocol_hash: str,
    cohort_manifest_hash: str,
) -> dict[str, Any]:
    dev_frontier_payload = _read_json(dev_frontier)
    dev_summary_payload = _read_json(dev_summary)
    dev_receipt_payload = _read_json(dev_receipt)
    holdout_frontier_payload = _read_json(holdout_frontier)
    holdout_summary_payload = _read_json(holdout_summary)
    holdout_receipt_payload = _read_json(holdout_receipt)
    b4_frontier_payload = _read_json(b4_frontier)
    b4_receipt_payload = _read_json(b4_receipt)
    b4_verification_payload = _read_json(b4_verification)
    return {
        "format": "ht-long-run-summary-v1",
        "code_commit": code_commit,
        "protocol_hash": protocol_hash,
        "cohort_manifest_hash": cohort_manifest_hash,
        "development": {
            "receipt": dev_receipt_payload,
            "rows": _method_rows(dev_frontier_payload, dev_summary_payload, "development"),
        },
        "final_holdout": {
            "receipt": holdout_receipt_payload,
            "rows": _method_rows(holdout_frontier_payload, holdout_summary_payload, "final_holdout"),
        },
        "b4_provider_shaped_mock": {
            "receipt": b4_receipt_payload,
            "verification": b4_verification_payload,
            "row": _b4_row(b4_frontier_payload, b4_receipt_payload, _read_jsonl(b4_raw_rankings)),
        },
        "input_hashes": {
            str(path): _sha256(path)
            for path in (
                dev_frontier,
                dev_summary,
                dev_receipt,
                holdout_frontier,
                holdout_summary,
                holdout_receipt,
                b4_frontier,
                b4_receipt,
                b4_raw_rankings,
                b4_verification,
            )
        },
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "NOT_REPORTED"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def render_report(summary: dict[str, Any]) -> str:
    lines = [
        "# HealthTech long-run report",
        "",
        f"- Code tested: `{summary['code_commit']}`",
        f"- Protocol hash: `{summary['protocol_hash']}`",
        f"- Cohort manifest hash: `{summary['cohort_manifest_hash']}`",
        "- Verdict: `PARTIAL; named offline and provider-shaped packages pass, live/provider and semantic-gold branches remain blocked or NOT_RUN`",
        "",
        "## 1. Scope and status",
        "",
        "This report is generated from frozen local artifacts. It separates offline retrieval baselines, provider-shaped mock execution, live-provider execution, semantic judgment intake, backend dossiers, and user/commercial validation.",
        "",
        "| Area | Status | Evidence boundary |",
        "|---|---|---|",
        "| M1 integrity | PASS in current-head audit | Adversarial source/export, frozen-identity, and typed-policy probes are recorded separately; this report does not re-run them. |",
        "| M2 data/cohort | PASS development package | Boston/Stryker/Cook public disclosure cohort is typed and frozen; Bridge remains BLOCKED_LOCAL. |",
        "| M3 methods/evaluator | PASS descriptive development | HT-B0a/B0b/B1/B2/B3 have fresh development and company holdout outputs; group uncertainty remains NOT_ESTIMABLE. |",
        "| M4 provider seam | PASS engineering | Versioned R1 policy, durable ledger, structured B4 seam, and mock fault tests pass. |",
        "| M5 paid provider | NOT_RUN / BLOCKED_LOCAL | No live request, paid canary, or paired pilot was dispatched. |",
        "| M6 backend/research | PARTIAL | Real dossiers/exports and integration contracts exist; manuscript and user evidence remain preparatory. |",
        "| M7 handoff | PASS for this package | Report, expansion request, audit, checkpoint, and pushed commits are present. |",
        "",
        "## 2. Frozen cohort and rights",
        "",
        "The main development view contains 5 queries/devices and 24 patents; the final holdout view contains 3 queries and the same 24-patent universe. The composite contains product-level disclosed relationships plus unjudged distractors. Unlisted pairs remain unjudged and are not treated as negatives. Product-level disclosure is not claim-level semantic relevance gold.",
        "",
        "No new raw-source acquisition or provider transfer occurred in this report package. Existing source registries, revisions, hashes, rights policies, split manifests, and family sensitivity artifacts remain the source of truth.",
        "",
        "## 3. Offline baseline results",
        "",
        "| Split | Method | Queries | Groups | Macro known-link R@20 | Query calls | Rerank pairs | Wall seconds | Errors |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for split in ("development", "final_holdout"):
        for row in summary[split]["rows"]:
            lines.append(
                f"| {split} | {row['method']} | {row['query_count']} | {row['group_count']} | {_fmt(row['macro_known_link_recall_at_20'])} | {_fmt(row['query_calls'])} | {_fmt(row['rerank_pairs'])} | {_fmt(row['wall_seconds'])} | {row['failed_query_count']} |"
            )
    lines.extend([
        "",
        "These are descriptive known-link recovery results. They do not establish exhaustive recall, semantic relevance, clinical suitability, FTO, patent validity, investment merit, or generalization beyond the frozen groups.",
        "",
        "## 4. HT-B4 provider-shaped mock",
        "",
        "| Metric | Actual value |",
        "|---|---:|",
        f"| Development devices | {summary['b4_provider_shaped_mock']['row']['query_count']} |",
        f"| Patents | {summary['b4_provider_shaped_mock']['receipt'].get('patents')} |",
        f"| Provider-shaped calls | {summary['b4_provider_shaped_mock']['row']['provider_shaped_calls']} |",
        f"| Macro known-link R@20 | {_fmt(summary['b4_provider_shaped_mock']['row']['macro_known_link_recall_at_20'])} |",
        f"| Total latency seconds | {_fmt(summary['b4_provider_shaped_mock']['row']['latency_seconds'])} |",
        f"| Schema-valid calls | {summary['b4_provider_shaped_mock']['row']['schema_valid_calls']} |",
        f"| Paid cost | ${summary['b4_provider_shaped_mock']['row']['paid_cost_usd']:.4f} |",
        f"| Simulated mock debit | ${summary['b4_provider_shaped_mock']['row']['simulated_cost_usd']:.4f} |",
        f"| Unknown/pending ledger items | {summary['b4_provider_shaped_mock']['row']['unknown_billing']} |",
        "",
        "The mock transport exercised the exact action schema and R1 reservation/settlement path but did not create provider evidence. Live mode remains blocked without an explicit source-transfer manifest and approved current paid readiness.",
        "",
        "## 5. Accounting and stopping",
        "",
        "R1 authorization remains USD 8.00 total with a USD 7.00 admission threshold and USD 1.00 internal reserve. The mock run paid USD 0.00; its simulated ledger debit is recorded separately. Canary and paired pilot remain NOT_RUN. Paid dispatch stops on unknown billing, identity/pricing drift, missing transfer rights, insufficient bound, schema/action failure, or loss of information value.",
        "",
        "## 6. Backend and research handoff",
        "",
        "Real public-case dossier runs exist for Abbott/Boston/Cook slices with source/history/version/export artifacts. The paused Claude UI receives schemas/contracts only; no UI takeover or deployment occurred. G5 task materials remain prepared templates with no participants, timings, offers, purchases, or customer validation. G6 manuscript methods/tables are descriptive and development-only; publication readiness and acceptance are NOT_RUN.",
        "",
        "## 7. Next information-gaining work",
        "",
        "1. Obtain or authorize a rights-cleared semantic judgment source with explicit labels, source revision/hash, adjudicator role, locators, independent company/family groups, and an untouched holdout.",
        "2. Keep paid HT-B4 blocked until transfer rights, credential/credit state, current pricing/identity, full-request bounds, and reconciliation gates are all evidenced.",
        "3. Use the existing frozen methods and report builder for the next cohort; do not tune on the holdout or convert unjudged pairs into negatives.",
        "",
    ])
    return "\n".join(lines)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--protocol-hash", required=True)
    parser.add_argument("--cohort-manifest-hash", required=True)
    parser.add_argument("--dev-frontier", type=Path, required=True)
    parser.add_argument("--dev-summary", type=Path, required=True)
    parser.add_argument("--dev-receipt", type=Path, required=True)
    parser.add_argument("--holdout-frontier", type=Path, required=True)
    parser.add_argument("--holdout-summary", type=Path, required=True)
    parser.add_argument("--holdout-receipt", type=Path, required=True)
    parser.add_argument("--b4-frontier", type=Path, required=True)
    parser.add_argument("--b4-receipt", type=Path, required=True)
    parser.add_argument("--b4-raw-rankings", type=Path, required=True)
    parser.add_argument("--b4-verification", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    args.output.mkdir(parents=True)
    summary = build_summary(
        dev_frontier=args.dev_frontier,
        dev_summary=args.dev_summary,
        dev_receipt=args.dev_receipt,
        holdout_frontier=args.holdout_frontier,
        holdout_summary=args.holdout_summary,
        holdout_receipt=args.holdout_receipt,
        b4_frontier=args.b4_frontier,
        b4_receipt=args.b4_receipt,
        b4_raw_rankings=args.b4_raw_rankings,
        b4_verification=args.b4_verification,
        code_commit=args.code_commit,
        protocol_hash=args.protocol_hash,
        cohort_manifest_hash=args.cohort_manifest_hash,
    )
    (args.output / "summary_tables.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = summary["development"]["rows"] + summary["final_holdout"]["rows"] + [summary["b4_provider_shaped_mock"]["row"]]
    _write_csv(args.output / "frontier_table.csv", rows)
    (args.output / "REPORT.md").write_text(render_report(summary), encoding="utf-8")
    receipt = {
        "format": "ht-long-run-report-receipt-v1",
        "status": "PASS_REPORT_GENERATED_FROM_FROZEN_ARTIFACTS",
        "code_commit": args.code_commit,
        "protocol_hash": args.protocol_hash,
        "cohort_manifest_hash": args.cohort_manifest_hash,
        "input_hashes": summary["input_hashes"],
        "outputs": {
            "report": "REPORT.md",
            "summary_tables": "summary_tables.json",
            "frontier_table": "frontier_table.csv",
        },
        "limitations": [
            "No live provider request or paid canary was run.",
            "Known-link metrics are descriptive product-disclosure recovery, not semantic gold.",
            "G5 user/commercial validation and G6 publication readiness remain NOT_VALIDATED or NOT_RUN.",
        ],
    }
    (args.output / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(args.output), "rows": len(rows), "b4_calls": summary["b4_provider_shaped_mock"]["row"]["provider_shaped_calls"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
