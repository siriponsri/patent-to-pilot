"""Summarize a post-hoc equalized prefix from a frozen frontier receipt."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_METHODS = ("HT-B1", "HT-B2", "HT-B3")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    frontier = payload.get("quality_resource_frontier")
    if not isinstance(frontier, dict) or not isinstance(frontier.get("rows"), list):
        raise ValueError("frontier receipt lacks quality_resource_frontier.rows")
    rows = [row for row in frontier["rows"] if isinstance(row, dict)]
    if not rows:
        raise ValueError("frontier receipt has no quality-resource rows")
    return rows


def analyze(
    frontier_path: Path,
    *,
    query_calls: int,
    rerank_pairs: int,
    source_candidate: str | None = None,
) -> dict[str, Any]:
    payload = json.loads(frontier_path.read_text(encoding="utf-8"))
    selected = [
        row
        for row in _rows(payload)
        if row.get("query_calls") == query_calls
        and row.get("rerank_pairs") == rerank_pairs
        and row.get("method") in REQUIRED_METHODS
    ]
    by_method = {str(row["method"]): row for row in selected}
    missing = [method for method in REQUIRED_METHODS if method not in by_method]
    if missing:
        raise ValueError(f"budget slice missing methods: {', '.join(missing)}")
    if len(selected) != len(REQUIRED_METHODS):
        raise ValueError("budget slice contains duplicate or unexpected required rows")

    result_rows = []
    for method in REQUIRED_METHODS:
        row = by_method[method]
        result_rows.append(
            {
                "method": method,
                "prefix": row.get("prefix"),
                "scheduled_query_count": row.get("scheduled_query_count"),
                "query_calls": row.get("query_calls"),
                "rerank_pairs": row.get("rerank_pairs"),
                "macro_known_link_recall_at_20": row.get("macro_known_link_recall_at_20_all_devices"),
                "failed_query_count": row.get("failed_query_count", 0),
                "not_realized_query_count": row.get("not_realized_query_count", 0),
            }
        )

    values = [row["macro_known_link_recall_at_20"] for row in result_rows]
    return {
        "format": "ht-matched-budget-prefix-diagnostic-v1",
        "status": "PASS_POSTHOC_DESCRIPTIVE_FIRST_ACTION_SLICE",
        "source": {
            "path": str(frontier_path),
            "sha256": _sha256(frontier_path),
            "receipt_candidate": source_candidate or payload.get("candidate") or payload.get("code_commit"),
        },
        "budget": {
            "query_calls": query_calls,
            "rerank_pairs": rerank_pairs,
            "selection_status": "POSTHOC_DESCRIPTIVE_NOT_PREREGISTERED_FINAL_ENDPOINT",
        },
        "methods": result_rows,
        "summary": {
            "macro_recall_min": min(values),
            "macro_recall_max": max(values),
            "macro_recall_range": max(values) - min(values),
            "all_failures_zero": all(row["failed_query_count"] == 0 for row in result_rows),
            "all_queries_realized": all(row["not_realized_query_count"] == 0 for row in result_rows),
        },
        "interpretation": {
            "claim": "B1, B2 prefix-1, and B3 prefix-1 share the same first-action budget and observed endpoint on this receipt.",
            "adaptive_test": "NOT_ESTABLISHED",
            "b4_status": "EXCLUDED_CONTROLLER_STEPS_NOT_DIRECTLY_COMPARABLE_TO_QUERY_RERANK_BUDGET",
            "final_holdout": "ABSENT_FROM_SOURCE_RECEIPT",
            "semantic_gold": "NOT_AVAILABLE_PRODUCT_DISCLOSED_LINKS_ONLY",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontier-diagnostics", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--query-calls", type=int, required=True)
    parser.add_argument("--rerank-pairs", type=int, required=True)
    parser.add_argument("--source-candidate")
    args = parser.parse_args()

    result = analyze(
        args.frontier_diagnostics,
        query_calls=args.query_calls,
        rerank_pairs=args.rerank_pairs,
        source_candidate=args.source_candidate,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
