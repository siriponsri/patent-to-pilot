"""Build a conservative adaptive-acquisition comparison from audited inputs."""

from __future__ import annotations

from collections.abc import Mapping
import json
import math
from pathlib import Path
from typing import Any


FIXED_METHODS = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _number(value: Any, label: str, *, minimum: float = 0.0, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result) or result < minimum or (maximum is not None and result > maximum):
        raise ValueError(f"{label} is outside the allowed range")
    return result


def _control_row(row: Mapping[str, Any], *, adaptive: bool, status: str) -> dict[str, Any]:
    method = row.get("method")
    if not isinstance(method, str) or not method:
        raise ValueError("comparison row lacks method")
    return {
        "method": method,
        "adaptive": adaptive,
        "status": status,
        "macro_known_link_recall_at_20": _number(
            row.get("macro_known_link_recall_at_20"), f"{method}.macro_known_link_recall_at_20", maximum=1.0
        ),
        "micro_known_link_recall_at_20": (
            None
            if row.get("micro_known_link_recall_at_20") is None
            else _number(row.get("micro_known_link_recall_at_20"), f"{method}.micro_known_link_recall_at_20", maximum=1.0)
        ),
        "device_count": int(_number(row.get("device_count"), f"{method}.device_count", minimum=1.0)),
        "failed_device_count": int(_number(row.get("failed_device_count", 0), f"{method}.failed_device_count")),
        "query_calls": _number(row.get("query_calls", 0), f"{method}.query_calls"),
        "rerank_pairs": _number(row.get("rerank_pairs", 0), f"{method}.rerank_pairs"),
        "paid_cost_usd": _number(row.get("paid_cost_usd", 0.0), f"{method}.paid_cost_usd"),
    }


def _cohort_summary(name: str, cohort: Mapping[str, Any]) -> dict[str, Any]:
    metrics = _mapping(cohort.get("metrics"), f"offline cohort {name}.metrics")
    return {
        "cohort": name,
        "devices": int(_number(cohort.get("devices"), f"offline cohort {name}.devices", minimum=1.0)),
        "patents": int(_number(cohort.get("patents"), f"offline cohort {name}.patents", minimum=1.0)),
        "macro_known_link_recall_at_20": _number(
            metrics.get("macro_known_link_recall_at_20"),
            f"offline cohort {name}.metrics.macro_known_link_recall_at_20",
            maximum=1.0,
        ),
        "micro_known_link_recall_at_20": _number(
            metrics.get("micro_known_link_recall_at_20"),
            f"offline cohort {name}.metrics.micro_known_link_recall_at_20",
            maximum=1.0,
        ),
        "query_calls": _number(metrics.get("query_calls"), f"offline cohort {name}.metrics.query_calls"),
        "controller_steps": _number(metrics.get("controller_steps"), f"offline cohort {name}.metrics.controller_steps"),
        "failed_devices": int(_number(metrics.get("failed_devices", 0), f"offline cohort {name}.metrics.failed_devices")),
        "provider_calls": int(_number(metrics.get("provider_calls", 0), f"offline cohort {name}.metrics.provider_calls")),
        "paid_cost_usd": _number(metrics.get("paid_cost_usd", 0.0), f"offline cohort {name}.metrics.paid_cost_usd"),
        "group_macro_known_link_recall_at_20": metrics.get("group_macro_known_link_recall_at_20", {}),
    }


def build_adaptive_policy_report(
    *,
    holdout_comparison: Mapping[str, Any],
    offline_verification: Mapping[str, Any],
    cross_cohort_comparison: Mapping[str, Any] | None,
    code_commit: str,
    parent_audit: str,
    input_hashes: Mapping[str, str],
) -> dict[str, Any]:
    """Validate and summarize the bounded adaptive-policy evidence already on disk."""
    holdout = _mapping(holdout_comparison, "holdout_comparison")
    controls = holdout.get("offline_controls")
    if not isinstance(controls, list):
        raise ValueError("holdout comparison lacks offline_controls")
    by_method = {row.get("method"): row for row in controls if isinstance(row, Mapping)}
    missing = [method for method in FIXED_METHODS if method not in by_method]
    if missing:
        raise ValueError(f"holdout comparison lacks required controls: {', '.join(missing)}")

    fixed_rows = [_control_row(by_method[method], adaptive=False, status="OFFLINE_CONTROL") for method in FIXED_METHODS]
    b4 = _mapping(holdout.get("b4_provider_shaped_mock"), "holdout_comparison.b4_provider_shaped_mock")
    if b4.get("method") != "HT-B4-MOCK":
        raise ValueError("adaptive row must remain explicitly labeled HT-B4-MOCK")
    if b4.get("status") != "MOCK_ONLY_NOT_PROVIDER_EVIDENCE":
        raise ValueError("adaptive provider-shaped evidence must retain its mock-only status")
    b4_row = _control_row(b4, adaptive=True, status="MOCK_ONLY_NOT_PROVIDER_EVIDENCE")
    b4_row.update(
        {
            "provider_shaped_calls": int(_number(b4.get("provider_shaped_calls", 0), "HT-B4-MOCK.provider_shaped_calls")),
            "simulated_cost_usd": _number(b4.get("simulated_cost_usd", 0.0), "HT-B4-MOCK.simulated_cost_usd"),
            "unknown_billing": int(_number(b4.get("unknown_billing", 0), "HT-B4-MOCK.unknown_billing")),
            "ledger_breach": bool(b4.get("ledger_breach", False)),
        }
    )
    if b4_row["paid_cost_usd"] != 0.0 or b4_row["unknown_billing"] != 0 or b4_row["ledger_breach"]:
        raise ValueError("provider-shaped mock evidence has non-zero paid or uncertain billing")

    device_counts = {row["device_count"] for row in fixed_rows + [b4_row]}
    if len(device_counts) != 1:
        raise ValueError("fixed controls and HT-B4-MOCK must use the same device count")

    offline = _mapping(offline_verification, "offline_verification")
    cohorts = _mapping(offline.get("cohorts"), "offline_verification.cohorts")
    offline_cohorts = [_cohort_summary(name, cohorts[name]) for name in ("abbott", "boston") if name in cohorts]
    if len(offline_cohorts) != 2:
        raise ValueError("offline verification must include Abbott and Boston cohorts")

    cross = None
    if cross_cohort_comparison is not None:
        source = _mapping(cross_cohort_comparison, "cross_cohort_comparison")
        comparability = _mapping(source.get("comparability"), "cross_cohort_comparison.comparability")
        cross = {
            "status": source.get("status"),
            "methods": list(source.get("methods", [])),
            "comparability": dict(comparability),
            "cohort_flags": source.get("cohort_flags", {}),
            "limitations": list(source.get("limitations", [])),
        }

    return {
        "format": "ht-research-product-adaptive-policy-report-v1",
        "status": "PARTIAL_OFFLINE_ADAPTIVE_POLICY_REPORT",
        "scope": "Bounded acquisition-policy comparison over previously audited public disclosure cohorts.",
        "primary_endpoint": {
            "metric": "macro known-link recall at K=20",
            "denominator": "declared known-link references with failed/missing queries retained",
            "unjudged_policy": "unlisted links remain unjudged; they are not negatives",
            "scientific_claim": "DESCRIPTIVE_ONLY_NOT_ESTIMABLE",
        },
        "fixed_controls": fixed_rows,
        "adaptive_evidence": {
            "offline_deterministic_controller": {
                "status": "PASS_OFFLINE_DEVELOPMENT",
                "is_llm": False,
                "cohorts": offline_cohorts,
                "provider_calls": 0,
                "paid_cost_usd": 0.0,
                "not_claimed": [
                    "live LLM controller behavior",
                    "scientific superiority",
                    "generalization beyond the audited cohorts",
                ],
            },
            "provider_shaped_mock": b4_row,
        },
        "holdout_comparison": {
            "status": holdout.get("status"),
            "split": holdout.get("split"),
            "b4_minus_controls": list(holdout.get("deltas_vs_controls", [])),
            "interpretation": list(holdout.get("interpretation", [])),
        },
        "cross_cohort": cross,
        "boundaries": {
            "live_qwen3_controller": "NOT_RUN_BLOCKED_LOCAL",
            "semantic_relevance_gold": "NOT_RUN",
            "clinical_f_to_validity_investment": "OUT_OF_SCOPE",
            "exhaustive_recall": "NOT_ESTABLISHED",
            "publication_readiness": "NOT_ESTABLISHED",
        },
        "limitations": [
            "The adaptive provider-shaped row is a mock transport and is not live-provider evidence.",
            "The offline controller is deterministic; it is not a Qwen3 controller.",
            "Product-level disclosed links are not claim-level semantic relevance gold.",
            "The effective independent group count is small and cohort candidate universes differ.",
            "The current O3 Qwen3-8B versus qwen/qwen3-32b generation comparison remains blocked locally.",
        ],
        "next_discriminating_test": "Freeze a rights-cleared cohort and local Qwen3-8B revision, then compare a live or locally executed bounded controller against the same fixed controls under a frozen protocol.",
        "provenance": {
            "code_commit": code_commit,
            "parent_audit": parent_audit,
            "input_hashes": dict(input_hashes),
            "source_status": "AUDITED_INPUTS_REUSED; NO_PROVIDER_CALLS",
        },
    }


def render_adaptive_policy_report(report: Mapping[str, Any]) -> str:
    lines = [
        "# Adaptive acquisition policy report",
        "",
        f"- Status: `{report['status']}`",
        f"- Code commit: `{report['provenance']['code_commit']}`",
        f"- Parent audit: `{report['provenance']['parent_audit']}`",
        "- Endpoint: macro known-link recall at K=20; descriptive only.",
        "",
        "## Fixed controls and provider-shaped adaptive row",
        "",
        "| Method | Adaptive | Macro R@20 | Query calls | Rerank pairs | Paid cost | Status |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    rows = list(report["fixed_controls"]) + [report["adaptive_evidence"]["provider_shaped_mock"]]
    for row in rows:
        lines.append(
            f"| {row['method']} | {'yes' if row['adaptive'] else 'no'} | {row['macro_known_link_recall_at_20']:.4f} | "
            f"{row['query_calls']:.0f} | {row['rerank_pairs']:.0f} | ${row['paid_cost_usd']:.4f} | {row['status']} |"
        )
    lines.extend(["", "## Offline deterministic controller", "", "| Cohort | Devices | Macro R@20 | Micro R@20 | Query calls | Provider calls | Paid cost |", "|---|---:|---:|---:|---:|---:|---:|"])
    for row in report["adaptive_evidence"]["offline_deterministic_controller"]["cohorts"]:
        lines.append(
            f"| {row['cohort']} | {row['devices']} | {row['macro_known_link_recall_at_20']:.4f} | "
            f"{row['micro_known_link_recall_at_20']:.4f} | {row['query_calls']:.0f} | {row['provider_calls']} | ${row['paid_cost_usd']:.4f} |"
        )
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {item}" for item in report["holdout_comparison"]["interpretation"])
    lines.extend(["", "## Boundaries", ""])
    lines.extend(f"- `{key}`: `{value}`" for key, value in report["boundaries"].items())
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in report["limitations"])
    lines.extend(["", f"Next discriminating test: {report['next_discriminating_test']}", ""])
    return "\n".join(lines)


def write_adaptive_policy_report(output: str | Path, report: Mapping[str, Any]) -> None:
    target = Path(output)
    target.mkdir(parents=True, exist_ok=True)
    (target / "adaptive-policy-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (target / "ADAPTIVE_POLICY_REPORT.md").write_text(render_adaptive_policy_report(report), encoding="utf-8")
