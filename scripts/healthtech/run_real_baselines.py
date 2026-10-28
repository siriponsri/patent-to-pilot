"""Run HT-B0a/B0b/B1/B2/B3 on a frozen local runtime cohort."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
from time import perf_counter, process_time

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.local_retrieval import (
    BM25Index,
    CrossEncoderReranker,
    DenseEncoder,
    PatentRecord,
    SharedRetriever,
    combine_reranked_bundles,
    explicit_patent_id_tokens,
    final_ranking,
    mask_explicit_patent_ids,
    stable_json_hash,
    validate_runtime_payload,
)
from patent_to_pilot.evaluation.healthtech.retrieval import evaluate_known_links, shared_reference_groups


METHODS = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3")


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _model_paths(model_root: Path, model_dir: str) -> tuple[str, str]:
    root = model_root / model_dir
    return str(root / "onnx" / "model_quint8_avx2.onnx"), str(root / "tokenizer.json")


def _device_text(device) -> str:
    return " ".join(value for value in (device.technical_description, *device.features_of_interest) if value).strip()


def _raw_ranking(rows: list[dict], patents_by_id: dict[str, PatentRecord]) -> list[dict]:
    return [
        {
            "rank": int(row["rank"]),
            "patent_id_raw": patents_by_id[row["patent_id_canonical"]].patent_id_raw,
            "patent_id_canonical": row["patent_id_canonical"],
            "score": float(row["score"]),
        }
        for row in rows
    ]


def _decorate_attempts(result: dict, patents_by_id: dict[str, PatentRecord]) -> None:
    for attempt in result.get("attempts", []):
        if "ranking" in attempt:
            attempt["ranking_raw_ids"] = _raw_ranking(attempt["ranking"], patents_by_id)


def _company_control(device, patents: list[PatentRecord]) -> tuple[list[dict], dict]:
    started = perf_counter()
    cpu_started = process_time()
    scores = {
        patent.patent_id_canonical: 1.0 if device.company and patent.company_metadata == device.company else 0.0
        for patent in patents
    }
    ordered = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    rows = [{"patent_id_canonical": patent_id, "score": score, "rank": rank} for rank, (patent_id, score) in enumerate(ordered, 1)]
    return rows, {
        "company_metadata_matches": sum(score > 0 for score in scores.values()),
        "returned_candidates": len(rows),
        "wall_seconds": perf_counter() - started,
        "cpu_seconds": process_time() - cpu_started,
        "query_calls": 1,
        "controller_tokens": 0,
    }


def _lexical_control(device, index: BM25Index, *, limit: int) -> tuple[list[dict], dict]:
    started = perf_counter()
    cpu_started = process_time()
    rows = index.search(_device_text(device), limit=limit)
    return rows, {
        "returned_candidates": len(rows),
        "wall_seconds": perf_counter() - started,
        "cpu_seconds": process_time() - cpu_started,
        "query_calls": 1,
        "controller_tokens": 0,
    }


def _fixed_queries(device) -> list[str]:
    values = [device.technical_description, *device.features_of_interest]
    queries: list[str] = []
    for value in values:
        text = str(value).strip()
        if text and text not in queries:
            queries.append(text)
    return queries


def _fixed_first_query(device) -> str:
    queries = _fixed_queries(device)
    return queries[0] if queries else _device_text(device)


def _sum_attempt_resources(attempts: list[dict]) -> dict[str, float]:
    totals: dict[str, float] = {}
    for attempt in attempts:
        for key, value in attempt.get("resources", {}).items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                totals[key] = totals.get(key, 0.0) + float(value)
    return totals


def _start_attempt(attempts: list[dict], attempt_id: int, query: str) -> dict:
    attempt = {
        "attempt_id": attempt_id,
        "query": query,
        "query_hash": stable_json_hash(query),
        "status": "started",
        "resources": {"query_calls": 1},
        "observables": {},
    }
    attempts.append(attempt)
    return attempt


def _finish_failed_attempt(attempt: dict, exc: Exception, *, query_calls: int = 1) -> None:
    resources = {"query_calls": query_calls}
    extra = getattr(exc, "resources", None)
    if isinstance(extra, dict):
        resources.update(extra)
    attempt.update({
        "status": "failed",
        "error_type": type(exc).__name__,
        "error": str(exc),
        "resources": resources,
    })


def _run_control_attempt(attempts: list[dict], attempt_id: int, query: str, action) -> list[dict] | None:
    attempt = _start_attempt(attempts, attempt_id, query)
    try:
        ranking, resources = action()
    except Exception as exc:
        _finish_failed_attempt(attempt, exc)
        return None
    attempt.update({"status": "completed", "ranking": ranking, "resources": resources})
    return ranking


def _run_bundle_attempt(attempts: list[dict], attempt_id: int, query: str, retriever: SharedRetriever,
                        *, candidate_depth: int, rerank_depth: int) -> dict | None:
    attempt = _start_attempt(attempts, attempt_id, query)
    try:
        bundle = retriever.fixed_bundle(query, candidate_depth=candidate_depth, rerank_depth=rerank_depth)
        ranking = final_ranking(bundle)
    except Exception as exc:
        _finish_failed_attempt(attempt, exc)
        return None
    attempt.update({
        "status": "completed",
        "query_hash": bundle.get("query_hash", stable_json_hash(query)),
        "ranking": ranking,
        "resources": bundle["resources"],
        "observables": bundle["observables"],
    })
    return bundle


def _run_method(device, patents, *, method: str, lexical: BM25Index, retriever: SharedRetriever,
                candidate_depth: int, rerank_depth: int) -> dict:
    patents_by_id = {patent.patent_id_canonical: patent for patent in patents}
    attempts: list[dict] = []
    bundles: list[dict] = []
    method_started = perf_counter()
    method_cpu_started = process_time()
    final: list[dict] = []
    status = "completed"
    stop_reason = "fixed_schedule_complete"
    scheduled_queries: list[str] = []
    try:
        if method == "HT-B0a":
            scheduled_queries = [str(device.company)]
            ranking = _run_control_attempt(attempts, 1, scheduled_queries[0], lambda: _company_control(device, patents))
            if ranking is None:
                status, stop_reason = "failed", "run_failure"
            else:
                final = ranking
        elif method == "HT-B0b":
            scheduled_queries = [_device_text(device)]
            ranking = _run_control_attempt(attempts, 1, scheduled_queries[0], lambda: _lexical_control(device, lexical, limit=candidate_depth))
            if ranking is None:
                status, stop_reason = "failed", "run_failure"
            else:
                final = ranking
        elif method == "HT-B1":
            scheduled_queries = [_fixed_first_query(device)]
            bundle = _run_bundle_attempt(attempts, 1, scheduled_queries[0], retriever, candidate_depth=candidate_depth, rerank_depth=rerank_depth)
            if bundle is None:
                status, stop_reason = "failed", "run_failure"
            else:
                bundles.append(bundle)
                final = final_ranking(bundle)
        elif method == "HT-B2":
            scheduled_queries = _fixed_queries(device)
            for attempt_id, query in enumerate(scheduled_queries, 1):
                bundle = _run_bundle_attempt(attempts, attempt_id, query, retriever, candidate_depth=candidate_depth, rerank_depth=rerank_depth)
                if bundle is None:
                    status, stop_reason = "failed", "run_failure"
                    break
                bundles.append(bundle)
            final = combine_reranked_bundles(bundles, limit=rerank_depth)
        elif method == "HT-B3":
            scheduled_queries = _fixed_queries(device)
            for attempt_id, query in enumerate(scheduled_queries, 1):
                bundle = _run_bundle_attempt(attempts, attempt_id, query, retriever, candidate_depth=candidate_depth, rerank_depth=rerank_depth)
                if bundle is None:
                    status, stop_reason = "failed", "run_failure"
                    break
                bundles.append(bundle)
                current_ids = {row["patent_id_canonical"] for row in final_ranking(bundle)}
                prior_ids = {row["patent_id_canonical"] for prior in bundles[:-1] for row in final_ranking(prior)}
                new_count = len(current_ids - prior_ids)
                attempts[-1]["observables"] = {**bundle["observables"], "new_candidate_count": new_count}
                if attempt_id == 1 and len(scheduled_queries) > 1:
                    if new_count >= 5 and bundle["observables"]["lexical_dense_disagreement"] < 0.5:
                        stop_reason = "policy_stop"
                        break
                elif new_count == 0:
                    stop_reason = "no_new_candidates_under_policy"
                    break
            else:
                stop_reason = "fixed_schedule_complete"
            final = combine_reranked_bundles(bundles, limit=rerank_depth)
        else:
            raise ValueError(f"unsupported method: {method}")
    except Exception as exc:
        status, stop_reason = "failed", "run_failure"
        if len(attempts) < len(scheduled_queries):
            fallback_query = scheduled_queries[len(attempts)]
        elif method in {"HT-B1", "HT-B2", "HT-B3"}:
            fallback_query = str(getattr(device, "technical_description", "")).strip() or _device_text(device)
        else:
            fallback_query = _device_text(device)
        failed_attempt = _start_attempt(attempts, len(attempts) + 1, fallback_query)
        _finish_failed_attempt(failed_attempt, exc, query_calls=0)
    return {
        "query_id": device.query_id,
        "method": method,
        "status": status,
        "stop_reason": stop_reason,
        "attempts": attempts,
        "final_ranking": _raw_ranking(final, patents_by_id),
        "resources": {
            **_sum_attempt_resources(attempts),
            "method_wall_seconds": perf_counter() - method_started,
            "method_cpu_seconds": process_time() - method_cpu_started,
            "attempt_count": len(attempts),
            "returned_unique_candidates": len({row["patent_id_canonical"] for row in final}),
        },
        "input_diagnostics": {
            "explicit_patent_id_tokens": explicit_patent_id_tokens(_device_text(device)),
            "masked_query": mask_explicit_patent_ids(_device_text(device)),
            "masked_query_equals_original": mask_explicit_patent_ids(_device_text(device)) == _device_text(device),
        },
        "prefix_diagnostics": {
            "schedule_type": "fixed_query_prefix" if method in {"HT-B1", "HT-B2", "HT-B3"} else "single_control_query",
            "scheduled_queries": scheduled_queries,
            "first_query": scheduled_queries[0] if scheduled_queries else None,
            "first_query_hash": stable_json_hash(scheduled_queries[0]) if scheduled_queries else None,
            "realized_attempt_count": len(attempts),
            "completed_attempt_count": sum(attempt["status"] == "completed" for attempt in attempts),
            "failed_attempt_count": sum(attempt["status"] == "failed" for attempt in attempts),
        },
    }


def _group_results(metrics: dict, groups: list[list[str]], *, k: int) -> list[dict]:
    per_query = {row["query_id"]: row for row in metrics["per_query"]}
    rows = []
    for index, group in enumerate(groups):
        values = [per_query[query_id]["known_recall"] for query_id in group if query_id in per_query]
        rows.append({"group_id": str(index), "query_ids": group, "query_count": len(values), "macro_known_link_recall": sum(values) / len(values) if values else None, "k": k})
    return rows


def _prefix_status(row: dict, prefix: int) -> str:
    attempts = {int(attempt.get("attempt_id", 0)): attempt for attempt in row.get("attempts", [])}
    statuses = [attempts.get(index, {}).get("status") for index in range(1, prefix + 1)]
    if any(status == "failed" for status in statuses):
        return "failed"
    if all(status == "completed" for status in statuses):
        return "completed"
    return "not_realized"


def _prefix_ranking(row: dict, prefix: int) -> list[dict]:
    if _prefix_status(row, prefix) != "completed":
        return []
    attempts = [
        attempt for attempt in row.get("attempts", [])
        if int(attempt.get("attempt_id", 0)) <= prefix and attempt.get("status") == "completed"
    ]
    if not attempts:
        return []
    if row["method"] in {"HT-B2", "HT-B3"}:
        bundles = [{"reranked": attempt["ranking"]} for attempt in attempts]
        limit = max(len(bundle["reranked"]) for bundle in bundles)
        return combine_reranked_bundles(bundles, limit=limit)
    return list(attempts[-1]["ranking"])


def _quality_resource_frontier(
    rankings: list[dict],
    references: dict[str, list[str]],
    universe: list[str],
    groups: list[list[str]],
    expected_query_ids: list[str],
    *,
    primary_k: int = 20,
) -> dict:
    rows_by_method_query = {(row["method"], row["query_id"]): row for row in rankings}
    frontier_rows = []
    alignment = {}
    for query_id in expected_query_ids:
        alignment[query_id] = {
            method: rows_by_method_query.get((method, query_id), {}).get("prefix_diagnostics", {}).get("first_query_hash")
            for method in ("HT-B1", "HT-B2", "HT-B3")
        }
    first_query_match = all(
        len(hashes) == 3 and None not in hashes.values() and len(set(hashes.values())) == 1
        for hashes in alignment.values()
    )
    for method in METHODS:
        method_rows = [row for row in rankings if row["method"] == method]
        max_prefix = max((len(row.get("attempts", [])) for row in method_rows), default=0)
        for prefix in range(1, max_prefix + 1):
            predictions: dict[str, list[str]] = {}
            statuses: dict[str, str] = {}
            per_query = []
            resources: dict[str, float] = {}
            for query_id in expected_query_ids:
                row = rows_by_method_query.get((method, query_id), {})
                prefix_status = _prefix_status(row, prefix)
                ranking = _prefix_ranking(row, prefix)
                predictions[query_id] = [item["patent_id_canonical"] for item in ranking]
                statuses[query_id] = "completed" if prefix_status == "completed" else "failed"
                gold = set(references.get(query_id, []))
                hits = len(set(predictions[query_id][:primary_k]) & gold) if prefix_status == "completed" else 0
                attempt_resources = _sum_attempt_resources([
                    attempt for attempt in row.get("attempts", [])
                    if int(attempt.get("attempt_id", 0)) <= prefix
                ])
                for key, value in attempt_resources.items():
                    resources[key] = resources.get(key, 0.0) + float(value)
                per_query.append({
                    "query_id": query_id,
                    "prefix": prefix,
                    "status": prefix_status,
                    "known_links": len(gold),
                    "hits_at_k": hits,
                    "known_recall_at_k": hits / len(gold) if gold else None,
                    "returned_candidates": len(predictions[query_id]),
                })
            metric = evaluate_known_links(
                expected_query_ids=expected_query_ids,
                references=references,
                predictions=predictions,
                universe=universe,
                k=primary_k,
                statuses=statuses,
            )
            reached = [item for item in per_query if item["status"] == "completed"]
            group_rows = []
            per_query_by_id = {item["query_id"]: item for item in per_query}
            for group_index, group in enumerate(groups):
                group_items = [per_query_by_id[query_id] for query_id in group if query_id in per_query_by_id]
                group_reached = [item for item in group_items if item["status"] == "completed"]
                group_rows.append({
                    "group_id": str(group_index),
                    "query_ids": group,
                    "query_count": len(group_items),
                    "reached_query_count": len(group_reached),
                    "failed_query_count": sum(item["status"] == "failed" for item in group_items),
                    "not_realized_query_count": sum(item["status"] == "not_realized" for item in group_items),
                    "macro_known_link_recall_at_k_all_devices": sum(
                        (item["known_recall_at_k"] or 0.0) for item in group_items
                    ) / len(group_items) if group_items else None,
                    "macro_known_link_recall_at_k_reached_devices": sum(
                        (item["known_recall_at_k"] or 0.0) for item in group_reached
                    ) / len(group_reached) if group_reached else None,
                    "k": primary_k,
                })
            frontier_rows.append({
                "method": method,
                "prefix": prefix,
                "scheduled_query_count": max(
                    len(row.get("prefix_diagnostics", {}).get("scheduled_queries", [])) for row in method_rows
                ) if method_rows else 0,
                "expected_query_count": len(expected_query_ids),
                "reached_query_count": len(reached),
                "failed_query_count": sum(item["status"] == "failed" for item in per_query),
                "not_realized_query_count": sum(item["status"] == "not_realized" for item in per_query),
                "macro_known_link_recall_at_20_all_devices": metric["macro_known_link_recall"],
                "macro_known_link_recall_at_20_reached_devices": sum(
                    (item["known_recall_at_k"] or 0.0) for item in reached
                ) / len(reached) if reached else None,
                "micro_known_link_recall_at_20_all_devices": metric["micro_known_link_recall"],
                "query_calls": resources.get("query_calls", 0.0),
                "rerank_pairs": resources.get("rerank_pairs", 0.0),
                "embedding_query_tokens": resources.get("embedding_query_tokens", 0.0),
                "rerank_tokens": resources.get("rerank_tokens", 0.0),
                "returned_candidates": resources.get("returned_candidates", 0.0),
                "cpu_seconds": resources.get("cpu_seconds", 0.0),
                "wall_seconds": resources.get("wall_seconds", 0.0),
                "reached_query_ids": [item["query_id"] for item in reached],
                "failed_query_ids": [item["query_id"] for item in per_query if item["status"] == "failed"],
                "not_realized_query_ids": [item["query_id"] for item in per_query if item["status"] == "not_realized"],
                "per_query": per_query,
                "group_results": group_rows,
            })
    return {
        "status": "DESCRIPTIVE_DEVELOPMENT_FRONTIER",
        "primary_k": primary_k,
        "quality_definition": "Known-link recall at K; failed and not-realized queries score zero in all-device rows.",
        "resource_definition": "Realized local query calls, rerank pairs, embedding/rerank tokens, CPU seconds, wall seconds, and returned candidates.",
        "fixed_prefix_alignment": {
            "methods": ["HT-B1", "HT-B2", "HT-B3"],
            "first_query_hashes_by_query": alignment,
            "first_query_match_across_fixed_methods": first_query_match,
            "shared_action": "SharedRetriever.fixed_bundle with the same candidate and rerank depths.",
        },
        "rows": frontier_rows,
        "uncertainty": {
            "status": "NOT_ESTIMABLE",
            "confidence_intervals": "NOT_ESTIMABLE",
            "reason": [
                "The frozen slice has three eligible queries, two exact-patent groups, and no final holdout.",
                "The company group contains all three Abbott queries, so company-held-out sensitivity is not estimable.",
                "Family mapping is UNKNOWN_NOT_ASSUMED; shared-patent groups are descriptive and not independent family samples.",
            ],
            "reported_instead": [
                "All-device per-prefix quality/resource rows with actual reached and not-realized counts.",
                "Descriptive exact-patent group rows at each observed prefix.",
            ],
        },
    }


def _frontier_diagnostics(
    rankings: list[dict],
    evaluations: dict[str, dict],
    groups: list[list[str]],
    *,
    references: dict[str, list[str]],
    universe: list[str],
    expected_query_ids: list[str],
) -> dict:
    per_device = []
    errors = []
    for row in rankings:
        resource_totals = _sum_attempt_resources(row.get("attempts", []))
        prefix = row.get("prefix_diagnostics", {})
        per_device.append({
            "query_id": row["query_id"],
            "method": row["method"],
            "status": row["status"],
            "scheduled_query_count": len(prefix.get("scheduled_queries", [])),
            "realized_query_count": len(row.get("attempts", [])),
            "completed_attempt_count": prefix.get("completed_attempt_count", 0),
            "failed_attempt_count": prefix.get("failed_attempt_count", 0),
            "first_query": prefix.get("first_query"),
            "first_query_hash": prefix.get("first_query_hash"),
            "query_calls": resource_totals.get("query_calls", 0.0),
            "rerank_pairs": resource_totals.get("rerank_pairs", 0.0),
            "embedding_query_tokens": resource_totals.get("embedding_query_tokens", 0.0),
            "rerank_tokens": resource_totals.get("rerank_tokens", 0.0),
            "returned_candidates": resource_totals.get("returned_candidates", 0.0),
            "method_wall_seconds": row.get("resources", {}).get("method_wall_seconds", 0.0),
            "method_cpu_seconds": row.get("resources", {}).get("method_cpu_seconds", 0.0),
        })
        for attempt in row.get("attempts", []):
            if attempt.get("status") == "failed":
                errors.append({
                    "query_id": row["query_id"],
                    "method": row["method"],
                    "attempt_id": attempt.get("attempt_id"),
                    "query": attempt.get("query"),
                    "query_hash": attempt.get("query_hash"),
                    "error_type": attempt.get("error_type"),
                    "error": attempt.get("error"),
                    "resources": attempt.get("resources", {}),
                })
    by_method = {}
    for method in METHODS:
        rows = [item for item in per_device if item["method"] == method]
        metric = evaluations[method]["by_k"]["20"]
        by_method[method] = {
            "device_count": len(rows),
            "failed_device_count": sum(item["status"] == "failed" for item in rows),
            "realized_query_count": sum(item["realized_query_count"] for item in rows),
            "query_calls": sum(item["query_calls"] for item in rows),
            "rerank_pairs": sum(item["rerank_pairs"] for item in rows),
            "embedding_query_tokens": sum(item["embedding_query_tokens"] for item in rows),
            "rerank_tokens": sum(item["rerank_tokens"] for item in rows),
            "returned_candidates": sum(item["returned_candidates"] for item in rows),
            "macro_known_link_recall_at_20": metric["macro_known_link_recall"],
            "failed_query_ids": metric["failed_query_ids"],
        }
    group_rows = []
    for method in METHODS:
        for group in evaluations[method]["by_k"]["20"]["group_results"]:
            group_rows.append({"method": method, **group})
    headroom = {
        method: {
            "macro_known_link_recall_at_20": by_method[method]["macro_known_link_recall_at_20"],
            "query_calls": by_method[method]["query_calls"],
            "rerank_pairs": by_method[method]["rerank_pairs"],
            "failed_device_count": by_method[method]["failed_device_count"],
        }
        for method in METHODS
    }
    return {
        "status": "DESCRIPTIVE_DEVELOPMENT_FRONTIER",
        "primary_k": 20,
        "fixed_prefix_contract": "HT-B1, HT-B2 and HT-B3 share the same first query text and fixed local bundle action",
        "per_device": per_device,
        "by_method": by_method,
        "groups": group_rows,
        "quality_resource_frontier": _quality_resource_frontier(
            rankings,
            references,
            universe,
            groups,
            expected_query_ids,
        ),
        "headroom": headroom,
        "errors": errors,
        "error_count": len(errors),
        "limitations": [
            "Frontier values are realized local resource units, not dollars.",
            "Group rows are descriptive because the development cohort has two exact-patent components and no final holdout.",
            "Failed devices remain in the evaluator denominator and score zero under the declared failure rule.",
        ],
    }


def _validate_references(runtime_devices, patents, reference_payload: dict) -> tuple[list[str], dict[str, list[str]]]:
    expected = [device.query_id for device in runtime_devices]
    references = reference_payload.get("references")
    if not isinstance(references, dict):
        raise ValueError("evaluator reference payload lacks references")
    if set(references) != set(expected):
        raise ValueError("reference query IDs do not equal runtime eligible query IDs")
    universe = [patent.patent_id_canonical for patent in patents]
    canonical_universe = set(universe)
    for query_id, values in references.items():
        if not isinstance(values, list) or len(values) != len(set(values)):
            raise ValueError(f"reference links must be unique lists: {query_id}")
        canonical = [str(value) for value in values]
        if any(value not in canonical_universe for value in canonical):
            raise ValueError(f"reference link absent from runtime universe: {query_id}")
    return expected, {str(key): [str(value) for value in values] for key, values in references.items()}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True, help="evaluator-only file, loaded after rankings are written")
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--protocol-hash", required=True)
    parser.add_argument("--cohort-manifest-hash", required=True)
    parser.add_argument("--candidate-depth", type=int, default=50)
    parser.add_argument("--rerank-depth", type=int, default=50)
    parser.add_argument("--k", type=int, action="append", default=[20, 10, 50])
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    args.output.mkdir(parents=True)
    runtime = _read_json(args.runtime)
    devices, patents = validate_runtime_payload(runtime)
    if args.candidate_depth < 1 or args.rerank_depth < 1:
        parser.error("candidate and rerank depths must be positive")
    candidate_depth = min(args.candidate_depth, len(patents))
    rerank_depth = min(args.rerank_depth, len(patents))
    encoder_path, encoder_tokenizer = _model_paths(args.model_root, "sentence-transformers-all-MiniLM-L6-v2")
    reranker_path, reranker_tokenizer = _model_paths(args.model_root, "cross-encoder-ms-marco-MiniLM-L-6-v2")
    index_started = perf_counter()
    encoder = DenseEncoder(model_path=encoder_path, tokenizer_path=encoder_tokenizer)
    reranker = CrossEncoderReranker(model_path=reranker_path, tokenizer_path=reranker_tokenizer)
    retriever = SharedRetriever(patents, encoder=encoder, reranker=reranker)
    lexical = BM25Index(patents)
    index_elapsed = perf_counter() - index_started
    rankings: list[dict] = []
    method_summaries: dict[str, dict] = {}
    predictions: dict[str, dict[str, list[str]]] = {method: {} for method in METHODS}
    statuses: dict[str, dict[str, str]] = {method: {} for method in METHODS}
    for method in METHODS:
        method_rows = []
        for device in devices:
            try:
                result = _run_method(device, patents, method=method, lexical=lexical, retriever=retriever,
                                     candidate_depth=candidate_depth, rerank_depth=rerank_depth)
            except Exception as exc:
                result = {
                    "query_id": device.query_id,
                    "method": method,
                    "status": "failed",
                    "stop_reason": "run_failure",
                    "attempts": [{"attempt_id": 1, "query": _device_text(device), "query_hash": stable_json_hash(_device_text(device)), "status": "failed", "error_type": type(exc).__name__, "error": str(exc), "resources": {"query_calls": 1}}],
                    "final_ranking": [],
                    "resources": {"attempt_count": 1, "query_calls": 1, "returned_candidates": 0, "unique_candidates": 0, "method_wall_seconds": 0.0, "method_cpu_seconds": 0.0},
                    "input_diagnostics": {"explicit_patent_id_tokens": explicit_patent_id_tokens(_device_text(device))},
                }
            _decorate_attempts(result, {patent.patent_id_canonical: patent for patent in patents})
            rankings.append(result)
            method_rows.append(result)
            predictions[method][device.query_id] = [row["patent_id_canonical"] for row in result["final_ranking"]]
            statuses[method][device.query_id] = result["status"]
        method_summaries[method] = {
            "method": method,
            "query_count": len(method_rows),
            "completed_query_count": sum(row["status"] == "completed" for row in method_rows),
            "failed_query_count": sum(row["status"] == "failed" for row in method_rows),
            "resources": {
                "method_wall_seconds": sum(float(row["resources"].get("method_wall_seconds", 0.0)) for row in method_rows),
                "method_cpu_seconds": sum(float(row["resources"].get("method_cpu_seconds", 0.0)) for row in method_rows),
                "attempt_count": sum(int(row["resources"].get("attempt_count", 0)) for row in method_rows),
                "query_calls": sum(float(attempt.get("resources", {}).get("query_calls", 0.0)) for row in method_rows for attempt in row.get("attempts", [])),
                "returned_candidates": sum(float(attempt.get("resources", {}).get("returned_candidates", 0.0)) for row in method_rows for attempt in row.get("attempts", [])),
                "rerank_pairs": sum(float(attempt.get("resources", {}).get("rerank_pairs", 0.0)) for row in method_rows for attempt in row.get("attempts", [])),
                "embedding_query_tokens": sum(float(attempt.get("resources", {}).get("embedding_query_tokens", 0.0)) for row in method_rows for attempt in row.get("attempts", [])),
                "rerank_tokens": sum(float(attempt.get("resources", {}).get("rerank_tokens", 0.0)) for row in method_rows for attempt in row.get("attempts", [])),
            },
        }
    _write_jsonl(args.output / "raw_rankings.jsonl", rankings)
    _write_json(args.output / "runtime_predictions.json", {"status": "PREDICTIONS_WRITTEN_BEFORE_REFERENCE_LOAD", "predictions": predictions, "statuses": statuses})
    reference_payload = _read_json(args.references)
    expected, references = _validate_references(devices, patents, reference_payload)
    group_payload = _read_json(args.groups)
    groups = group_payload.get("shared_exact_patent_groups")
    if not isinstance(groups, list) or any(not isinstance(group, list) for group in groups):
        raise ValueError("groups file lacks shared exact patent groups")
    evaluator_validation = {
        "expected_query_ids": expected,
        "expected_query_ids_hash": stable_json_hash(expected),
        "universe": [patent.patent_id_canonical for patent in patents],
        "universe_hash": stable_json_hash([patent.patent_id_canonical for patent in patents]),
        "reference_query_count": len(references),
        "reference_pair_count": sum(len(values) for values in references.values()),
        "shared_reference_groups": shared_reference_groups(references),
        "runtime_reference_separation": "reference file opened only after raw rankings and predictions were written",
    }
    _write_json(args.output / "evaluator_validation.json", evaluator_validation)
    evaluations: dict[str, dict] = {}
    for method in METHODS:
        k_metrics: dict[str, dict] = {}
        for cutoff in sorted(set(args.k)):
            metric = evaluate_known_links(expected_query_ids=expected, references=references, predictions=predictions[method], universe=[patent.patent_id_canonical for patent in patents], k=cutoff, statuses=statuses[method])
            metric["group_results"] = _group_results(metric, groups, k=cutoff)
            k_metrics[str(cutoff)] = metric
        evaluations[method] = {"method": method, "by_k": k_metrics, "status": "PASS" if method_summaries[method]["failed_query_count"] == 0 else "PARTIAL_FAILURE"}
    _write_json(args.output / "per_device_group_results.json", evaluations)
    frontier = _frontier_diagnostics(
        rankings,
        evaluations,
        groups,
        references=references,
        universe=[patent.patent_id_canonical for patent in patents],
        expected_query_ids=expected,
    )
    _write_json(args.output / "frontier_diagnostics.json", frontier)
    primary = {method: evaluations[method]["by_k"]["20"]["macro_known_link_recall"] for method in METHODS}
    headroom = {
        "primary_k": 20,
        "macro_known_link_recall": primary,
        "null_findings": [
            "This is a development-only public disclosure cohort; no held-out generalization claim is made.",
            "The company-only control is not company-held-out because every device is ABBOTT MEDICAL.",
            "Unlisted pairs are unjudged; the metric is known-link recovery only.",
        ],
        "method_order": list(METHODS),
        "simple_heuristic_minus_fixed_hybrid": primary["HT-B3"] - primary["HT-B1"],
    }
    _write_json(args.output / "development_headroom.json", headroom)
    _write_json(args.output / "method_summary.json", method_summaries)
    receipt = {
        "status": "REAL_PUBLIC_DEVELOPMENT_RUN",
        "run_at_utc": datetime.now(timezone.utc).isoformat(),
        "code_commit": args.code_commit,
        "scoring_script_sha256": _file_sha256(Path(__file__)),
        "protocol_hash": args.protocol_hash,
        "cohort_manifest_hash": args.cohort_manifest_hash,
        "runtime_path": str(args.runtime),
        "evaluator_path": str(args.references),
        "model_revisions": {
            "encoder": "sentence-transformers/all-MiniLM-L6-v2@1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
            "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2@233902d25c440f23af6f7d6e94d2946bac0bee0a",
        },
        "devices": len(devices),
        "patents": len(patents),
        "reference_pairs": sum(len(values) for values in references.values()),
        "candidate_depth": candidate_depth,
        "rerank_depth": rerank_depth,
        "index_prep_seconds": index_elapsed,
        "methods": list(METHODS),
        "artifacts": {
            "raw_rankings": "raw_rankings.jsonl",
            "runtime_predictions": "runtime_predictions.json",
            "evaluator_validation": "evaluator_validation.json",
            "per_device_group_results": "per_device_group_results.json",
            "development_headroom": "development_headroom.json",
            "frontier_diagnostics": "frontier_diagnostics.json",
        },
        "provider_calls": 0,
        "paid_cost_usd": 0,
        "limitations": [
            "Development-only public disclosure cohort; no final holdout or publication claim.",
            "Model pretraining contamination cannot be ruled out; short-context quantized ONNX variants are used.",
            "Product disclosure is a source-backed relationship and not claim-level patent validity, FTO, clinical or investment evidence.",
        ],
    }
    _write_json(args.output / "receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "output": str(args.output), "methods": list(METHODS), "devices": len(devices), "patents": len(patents), "pairs": receipt["reference_pairs"], "provider_calls": 0, "paid_cost_usd": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()
