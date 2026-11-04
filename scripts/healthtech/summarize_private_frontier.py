"""Summarize a private frontier receipt without exporting source payloads.

The input directory is intentionally outside Git. The emitted JSON contains
file hashes, aggregate metrics, and resource vectors only; it omits raw query,
patent, and source identifiers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


METHODS = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3")
REQUIRED_FILES = (
    "receipt.json",
    "method_summary.json",
    "frontier_diagnostics.json",
    "per_device_group_results.json",
    "evaluator_validation.json",
    "raw_rankings.jsonl",
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path.name}")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _numeric_fields(value: dict[str, Any]) -> dict[str, int | float]:
    return {
        key: item
        for key, item in value.items()
        if isinstance(item, (int, float)) and not isinstance(item, bool)
    }


def _resource_vector(resources: dict[str, Any]) -> dict[str, int | float | str | list[Any]]:
    fields = (
        "attempt_count",
        "query_calls",
        "rerank_pairs",
        "rerank_tokens",
        "embedding_query_tokens",
        "returned_candidates",
        "method_cpu_seconds",
        "method_wall_seconds",
        "resource_accounting_status",
        "unknown_resource_fields",
    )
    return {key: resources.get(key) for key in fields if key in resources}


def _compact_prefix(row: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "method",
        "prefix",
        "scheduled_query_count",
        "reached_query_count",
        "failed_query_count",
        "not_realized_query_count",
        "query_calls",
        "rerank_pairs",
        "rerank_tokens",
        "embedding_query_tokens",
        "returned_candidates",
        "cpu_seconds",
        "wall_seconds",
        "macro_known_link_recall_at_20_all_devices",
        "micro_known_link_recall_at_20_all_devices",
    )
    return {key: row[key] for key in fields if key in row}


def _budget_ceiling_slices(prefix_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    methods = ("HT-B1", "HT-B2", "HT-B3")
    observed = [
        row
        for row in prefix_rows
        if row.get("method") in methods
        and isinstance(row.get("query_calls"), (int, float))
        and isinstance(row.get("rerank_pairs"), (int, float))
    ]
    ceilings = sorted(
        {
            (int(row["query_calls"]), int(row["rerank_pairs"]))
            for row in observed
        }
    )
    slices: list[dict[str, Any]] = []
    for query_calls, rerank_pairs in ceilings:
        selected: dict[str, dict[str, Any]] = {}
        for method in methods:
            eligible = [
                row
                for row in observed
                if row["method"] == method
                and int(row["query_calls"]) <= query_calls
                and int(row["rerank_pairs"]) <= rerank_pairs
            ]
            if not eligible:
                continue
            eligible.sort(
                key=lambda row: (
                    int(row.get("prefix", 0)),
                    int(row["query_calls"]),
                    int(row["rerank_pairs"]),
                ),
                reverse=True,
            )
            row = eligible[0]
            selected[method] = {
                "prefix": row.get("prefix"),
                "query_calls": row.get("query_calls"),
                "rerank_pairs": row.get("rerank_pairs"),
                "failed_query_count": row.get("failed_query_count", 0),
                "not_realized_query_count": row.get("not_realized_query_count", 0),
                "macro_known_link_recall_at_20_all_devices": row.get(
                    "macro_known_link_recall_at_20_all_devices"
                ),
            }
        vectors = {
            (int(row["query_calls"]), int(row["rerank_pairs"]))
            for row in selected.values()
        }
        slices.append(
            {
                "ceiling": {
                    "query_calls": query_calls,
                    "rerank_pairs": rerank_pairs,
                },
                "selected_by_method": selected,
                "methods_present": sorted(selected),
                "all_required_methods_present": len(selected) == len(methods),
                "equal_realized_budget": len(vectors) == 1 and len(selected) == len(methods),
                "selection_rule": (
                    "maximum observed prefix within the resource ceiling; "
                    "no endpoint-based selection and no rerun"
                ),
                "claim_boundary": (
                    "posthoc descriptive ceiling sensitivity; "
                    "only equal_realized_budget slices are matched-budget diagnostics"
                ),
            }
        )
    return slices


def summarize(baseline: Path) -> dict[str, Any]:
    baseline = baseline.resolve()
    missing = [name for name in REQUIRED_FILES if not (baseline / name).is_file()]
    if missing:
        raise FileNotFoundError("missing private frontier files: " + ", ".join(missing))

    receipt = _read_json(baseline / "receipt.json")
    method_summary = _read_json(baseline / "method_summary.json")
    frontier = _read_json(baseline / "frontier_diagnostics.json")
    group_results = _read_json(baseline / "per_device_group_results.json")
    evaluator = _read_json(baseline / "evaluator_validation.json")
    raw_rows = [
        json.loads(line)
        for line in (baseline / "raw_rankings.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    methods = list(receipt.get("methods", []))
    if tuple(methods) != METHODS:
        raise ValueError(f"unexpected method set: {methods!r}")

    by_method = frontier.get("by_method", {})
    method_rows: list[dict[str, Any]] = []
    for method in METHODS:
        summary = method_summary.get(method, {})
        metrics = by_method.get(method, {})
        method_rows.append(
            {
                "method": method,
                "completed_query_count": summary.get("completed_query_count"),
                "failed_query_count": summary.get("failed_query_count"),
                "macro_known_link_recall_at_20": metrics.get("macro_known_link_recall_at_20"),
                "micro_known_link_recall_at_20": metrics.get("micro_known_link_recall_at_20"),
                "resource": _resource_vector(summary.get("resources", {})),
            }
        )

    prefix_rows = [
        _compact_prefix(row)
        for row in frontier.get("quality_resource_frontier", {}).get("rows", [])
        if isinstance(row, dict)
    ]
    matched = [
        row
        for row in prefix_rows
        if row.get("prefix") == 1
        and row.get("method") in {"HT-B1", "HT-B2", "HT-B3"}
        and row.get("query_calls") == 3
        and row.get("rerank_pairs") == 123
    ]
    matched_values = {
        row["method"]: row.get("macro_known_link_recall_at_20_all_devices")
        for row in matched
    }
    matched_first_action = {
        "status": "PASS_OBSERVED" if len(matched) == 3 else "NOT_AVAILABLE",
        "methods": matched_values,
        "equal_metric": len(set(matched_values.values())) == 1 if matched_values else False,
        "all_failures_zero": all(row.get("failed_query_count") == 0 for row in matched),
        "all_not_realized_zero": all(row.get("not_realized_query_count") == 0 for row in matched),
        "claim_boundary": "first-action diagnostic only; not a completed adaptive-policy comparison",
    }
    budget_ceiling_slices = _budget_ceiling_slices(prefix_rows)

    vectors = {
        row["method"]: {
            key: row["resource"].get(key)
            for key in ("query_calls", "rerank_pairs", "embedding_query_tokens")
        }
        for row in method_rows
    }
    equal_total_budget = len({json.dumps(value, sort_keys=True) for value in vectors.values()}) == 1
    uncertainty = frontier.get("quality_resource_frontier", {}).get("uncertainty", {})
    shared_groups = evaluator.get("shared_reference_groups", [])

    return {
        "format": "ptp-private-frontier-reconciliation-v1",
        "source_files": {
            name: {
                "bytes": (baseline / name).stat().st_size,
                "sha256": _sha256(baseline / name),
            }
            for name in REQUIRED_FILES
        },
        "receipt": {
            "status": receipt.get("status"),
            "code_commit": receipt.get("code_commit"),
            "protocol_hash": receipt.get("protocol_hash"),
            "cohort_manifest_hash": receipt.get("cohort_manifest_hash"),
            "methods": methods,
            "devices": receipt.get("devices"),
            "patents": receipt.get("patents"),
            "reference_pairs": receipt.get("reference_pairs"),
            "candidate_depth": receipt.get("candidate_depth"),
            "rerank_depth": receipt.get("rerank_depth"),
            "provider_calls": receipt.get("provider_calls"),
            "paid_cost_usd": receipt.get("paid_cost_usd"),
        },
        "evaluation_scope": {
            "reference_query_count": evaluator.get("reference_query_count"),
            "reference_pair_count": evaluator.get("reference_pair_count"),
            "shared_reference_group_count": len(shared_groups),
            "shared_reference_group_sizes": [len(group) for group in shared_groups],
            "final_holdout": "NOT_PRESENT_IN_PRIVATE_DEVELOPMENT_RECEIPT",
            "runtime_reference_separation": evaluator.get("runtime_reference_separation"),
            "uncertainty": uncertainty,
        },
        "methods": method_rows,
        "budget_comparability": {
            "resource_vectors": vectors,
            "equal_total_budget_across_methods": equal_total_budget,
            "matched_first_action": matched_first_action,
            "budget_ceiling_slices": budget_ceiling_slices,
            "claim_boundary": "full-method quality differences are descriptive because realized budgets differ",
        },
        "frontier_prefixes": prefix_rows,
        "raw_ranking_rows": len(raw_rows),
        "raw_ranking_statuses": sorted({str(row.get("status")) for row in raw_rows}),
        "privacy": {
            "raw_query_or_patent_text_exported": False,
            "raw_source_identifiers_exported": False,
            "absolute_private_path_exported": False,
            "source_file_names_and_hashes_only": True,
        },
        "limitations": [
            "The private receipt covers a three-query development slice with two shared exact-patent groups.",
            "No final holdout or semantic relevance gold is established by this reconciliation.",
            "Only slices marked equal_realized_budget are matched-budget diagnostics; other ceilings are at-most-budget sensitivity views.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = summarize(args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
