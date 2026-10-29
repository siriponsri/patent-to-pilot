"""Reproject frozen offline baseline outputs onto sourced family groups."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from statistics import mean
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.retrieval import shared_reference_groups


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _family_map(payload: dict[str, Any]) -> dict[str, str]:
    rows = payload.get("mappings")
    if not isinstance(rows, list) or not rows:
        raise ValueError("family mapping must contain a nonempty mappings list")
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("family mapping contains a non-object row")
        patent_id = str(row.get("patent_id_canonical") or "").strip()
        family_id = str(row.get("family_id") or "").strip()
        if not patent_id or not family_id:
            raise ValueError("family mapping row lacks patent_id_canonical or family_id")
        prior = result.get(patent_id)
        if prior is not None and prior != family_id:
            raise ValueError(f"family mapping conflicts for {patent_id}")
        result[patent_id] = family_id
    return result


def _family_merge_groups(exact_groups: list[list[str]], family_groups: list[list[str]]) -> list[list[str]]:
    exact_sets = [frozenset(group) for group in exact_groups]
    return sorted(
        [sorted(group) for group in (frozenset(item) for item in family_groups)
         if sum(bool(group & exact) for exact in exact_sets) > 1]
    )


def _metric_group_rows(metric: dict[str, Any], groups: list[list[str]]) -> list[dict[str, Any]]:
    per_query = metric.get("per_query")
    if not isinstance(per_query, list):
        raise ValueError("baseline metric lacks per_query rows")
    by_query = {str(row.get("query_id")): row for row in per_query if isinstance(row, dict)}
    rows: list[dict[str, Any]] = []
    for index, group in enumerate(groups):
        values = [float(by_query[query_id]["known_recall"]) for query_id in group if query_id in by_query]
        rows.append({
            "group_id": str(index),
            "query_ids": group,
            "query_count": len(values),
            "macro_known_link_recall": mean(values) if values else None,
            "k": metric.get("k"),
        })
    return rows


def _frontier_group_rows(row: dict[str, Any], groups: list[list[str]], primary_k: int) -> list[dict[str, Any]]:
    per_query = row.get("per_query")
    if not isinstance(per_query, list):
        raise ValueError("frontier row lacks per_query rows")
    by_query = {str(item.get("query_id")): item for item in per_query if isinstance(item, dict)}
    rows: list[dict[str, Any]] = []
    for index, group in enumerate(groups):
        items = [by_query[query_id] for query_id in group if query_id in by_query]
        reached = [item for item in items if item.get("status") == "completed"]
        values = [float(item.get("known_recall_at_k", 0.0)) for item in items]
        reached_values = [float(item.get("known_recall_at_k", 0.0)) for item in reached]
        rows.append({
            "group_id": str(index),
            "query_ids": group,
            "query_count": len(items),
            "reached_query_count": len(reached),
            "failed_query_count": sum(item.get("status") == "failed" for item in items),
            "not_realized_query_count": sum(item.get("status") == "not_realized" for item in items),
            "macro_known_link_recall_at_k_all_devices": mean(values) if values else None,
            "macro_known_link_recall_at_k_reached_devices": mean(reached_values) if reached_values else None,
            "k": primary_k,
        })
    return rows


def analyze_family_frontier(
    *,
    baseline_dir: str | Path,
    references_path: str | Path,
    family_mapping_path: str | Path,
    split: str,
) -> dict[str, Any]:
    baseline = Path(baseline_dir).resolve()
    references_payload = _read_json(Path(references_path))
    mapping_payload = _read_json(Path(family_mapping_path))
    group_results = _read_json(baseline / "per_device_group_results.json")
    frontier = _read_json(baseline / "frontier_diagnostics.json")
    receipt = _read_json(baseline / "receipt.json")
    references = references_payload.get("references")
    if not isinstance(references, dict) or not references:
        raise ValueError("references payload must contain a nonempty references object")
    family_map = _family_map(mapping_payload)
    family_groups = shared_reference_groups(references, families=family_map)

    methods = sorted(group_results)
    if not methods:
        raise ValueError("baseline group results are empty")
    first_method = group_results[methods[0]]
    first_by_k = first_method.get("by_k") if isinstance(first_method, dict) else None
    if not isinstance(first_by_k, dict) or not first_by_k:
        raise ValueError("baseline group results lack by_k metrics")
    primary_k = int(frontier.get("primary_k", 20))
    exact_metric = first_by_k.get(str(primary_k))
    if not isinstance(exact_metric, dict):
        exact_metric = first_by_k[sorted(first_by_k)[0]]
    exact_rows = exact_metric.get("group_results")
    if not isinstance(exact_rows, list):
        raise ValueError("baseline metric lacks exact group_results")
    exact_groups = [list(row.get("query_ids", [])) for row in exact_rows if isinstance(row, dict)]
    merged_groups = _family_merge_groups(exact_groups, family_groups)

    by_method_and_k: dict[str, dict[str, Any]] = {}
    for method in methods:
        method_payload = group_results.get(method)
        if not isinstance(method_payload, dict) or not isinstance(method_payload.get("by_k"), dict):
            raise ValueError(f"baseline method lacks by_k metrics: {method}")
        by_method_and_k[method] = {}
        for k, metric in sorted(method_payload["by_k"].items(), key=lambda item: int(item[0])):
            if not isinstance(metric, dict):
                raise ValueError(f"invalid metric for {method} k={k}")
            by_method_and_k[method][str(k)] = {
                "exact_group_results": metric.get("group_results", []),
                "family_group_results": _metric_group_rows(metric, family_groups),
                "macro_known_link_recall": metric.get("macro_known_link_recall"),
                "micro_known_link_recall": metric.get("micro_known_link_recall"),
            }

    frontier_rows = frontier.get("quality_resource_frontier", {}).get("rows", [])
    if not isinstance(frontier_rows, list):
        raise ValueError("frontier quality_resource_frontier.rows must be a list")
    family_frontier_rows: list[dict[str, Any]] = []
    for row in frontier_rows:
        if not isinstance(row, dict):
            raise ValueError("frontier rows must be objects")
        family_frontier_rows.append({
            "method": row.get("method"),
            "prefix": row.get("prefix"),
            "scheduled_query_count": row.get("scheduled_query_count"),
            "reached_query_count": row.get("reached_query_count"),
            "failed_query_count": row.get("failed_query_count"),
            "not_realized_query_count": row.get("not_realized_query_count"),
            "macro_known_link_recall_at_20_all_devices": row.get("macro_known_link_recall_at_20_all_devices"),
            "micro_known_link_recall_at_20": row.get("micro_known_link_recall_at_20"),
            "family_group_results": _frontier_group_rows(row, family_groups, primary_k),
        })

    return {
        "format": "ht-family-aware-frontier-analysis-v1",
        "status": "PASS_OFFLINE_FAMILY_FRONTIER_ANALYSIS",
        "split": split,
        "baseline_status": receipt.get("status"),
        "baseline_receipt_sha256": _sha256(baseline / "receipt.json"),
        "family_mapping_status": mapping_payload.get("status"),
        "family_mapping_sha256": mapping_payload.get("mapping_sha256"),
        "counts": {
            "reference_queries": len(references),
            "exact_group_count": len(exact_groups),
            "family_aware_group_count": len(family_groups),
            "family_mapped_patents": len(family_map),
            "families_observed": len(set(family_map.values())),
            "family_merged_exact_group_count": len(merged_groups),
        },
        "exact_groups": sorted(exact_groups),
        "family_aware_groups": family_groups,
        "family_merged_exact_groups": merged_groups,
        "primary_k": primary_k,
        "by_method_and_k": by_method_and_k,
        "frontier_rows": family_frontier_rows,
        "uncertainty": {
            "status": "NOT_ESTIMABLE",
            "confidence_intervals": "NOT_ESTIMABLE",
            "reason": [
                f"The {split} slice has {len(references)} eligible queries and {len(family_groups)} sourced family-aware groups.",
                "Family-aware rows are a sensitivity/provenance view, not independent semantic relevance gold.",
                "No confidence interval or pooled generalization claim is produced by this analysis.",
            ],
        },
        "limitations": [
            "Exact baseline rankings and metrics are preserved; this script only reprojects evaluator rows onto sourced family groups.",
            "Unlisted device-patent pairs remain unjudged and are never recoded as negatives.",
            "Family IDs are sourced Google Patents metadata, not legal family or claim-level relevance adjudication.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--family-mapping", type=Path, required=True)
    parser.add_argument("--split", required=True, choices=("development", "final_holdout"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh path")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = analyze_family_frontier(
        baseline_dir=args.baseline,
        references_path=args.references,
        family_mapping_path=args.family_mapping,
        split=args.split,
    )
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "split": args.split, "counts": payload["counts"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
