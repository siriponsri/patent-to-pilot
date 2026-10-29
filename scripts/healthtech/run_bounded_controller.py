"""Run the offline bounded HT-B4 controller on one frozen public cohort.

The controller uses the same local dense/lexical/reranker bundle as HT-B1/B2/B3
and writes runtime outputs before loading evaluator references. No provider or
network call is available in this script.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from time import perf_counter, process_time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.healthtech.retrieval import evaluate_known_links
from patent_to_pilot.healthtech.controller import (
    CONTROLLER_RESPONSE_SCHEMA,
    ControllerObservation,
    deterministic_controller_action,
    validate_controller_action,
)


def _load_baselines():
    path = ROOT / "scripts" / "healthtech" / "run_real_baselines.py"
    spec = importlib.util.spec_from_file_location("healthtech_real_baselines", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load shared baseline runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASELINES = _load_baselines()


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _fixed_queries(device) -> list[str]:
    return BASELINES._fixed_queries(device)


def _run_controller_device(device, retriever, *, candidate_depth: int, rerank_depth: int, max_steps: int,
                           action_selector=None, method_name: str = "HT-B4-OFFLINE") -> dict:
    queries = _fixed_queries(device)
    feature_indices = list(range(1, len(queries)))
    used_features: list[int] = []
    attempts: list[dict] = []
    bundles: list[dict] = []
    actions: list[dict] = []
    remaining_calls = max_steps
    remaining_candidates = candidate_depth * max_steps
    last_new = 0
    last_disagreement = 0.0
    status = "completed"
    stop_reason = "controller_stop"
    started = perf_counter()
    cpu_started = process_time()
    for step_index in range(max_steps + 1):
        observation = ControllerObservation(
            query_id=device.query_id,
            step_index=step_index,
            max_steps=max_steps,
            remaining_query_calls=remaining_calls,
            remaining_candidate_budget=remaining_candidates,
            source_available=bool(queries),
            available_feature_indices=[index for index in feature_indices if index not in used_features],
            used_feature_indices=used_features,
            last_new_candidate_count=last_new,
            last_disagreement=last_disagreement,
            last_action=actions[-1]["action_type"] if actions else None,
        )
        raw_action = (
            deterministic_controller_action(observation)
            if action_selector is None
            else action_selector.select(observation)
        )
        action = validate_controller_action(raw_action, observation)
        action_row = {"step_index": step_index, **action.model_dump(mode="json"), "observation": observation.model_dump(mode="json")}
        if action_selector is not None:
            receipt = action_selector.take_last_receipt()
            if receipt is not None:
                action_row["controller_call"] = receipt
        actions.append(action_row)
        if action.action_type == "stop":
            stop_reason = action.reason_code
            break
        query = queries[0] if action.action_type == "technical_search" else queries[action.feature_index]
        if action.action_type == "feature_search":
            used_features.append(int(action.feature_index))
        bundle = BASELINES._run_bundle_attempt(
            attempts,
            len(attempts) + 1,
            query,
            retriever,
            candidate_depth=candidate_depth,
            rerank_depth=rerank_depth,
        )
        remaining_calls -= 1
        if bundle is None:
            status = "failed"
            stop_reason = "run_failure"
            break
        bundles.append(bundle)
        ranking = BASELINES.final_ranking(bundle)
        current_ids = {row["patent_id_canonical"] for row in ranking}
        prior_ids = {row["patent_id_canonical"] for prior in bundles[:-1] for row in BASELINES.final_ranking(prior)}
        last_new = len(current_ids - prior_ids)
        last_disagreement = float(bundle["observables"]["lexical_dense_disagreement"])
        remaining_candidates = max(0, remaining_candidates - int(bundle["resources"].get("returned_candidates", 0)))
    final = BASELINES.combine_reranked_bundles(bundles, limit=rerank_depth) if bundles else []
    patents_by_id = {patent.patent_id_canonical: patent for patent in retriever.patents}
    return {
        "query_id": device.query_id,
        "method": method_name,
        "status": status,
        "stop_reason": stop_reason,
        "actions": actions,
        "attempts": attempts,
        "final_ranking": BASELINES._raw_ranking(final, patents_by_id),
        "resources": {
            **BASELINES._sum_attempt_resources(attempts),
            "method_wall_seconds": perf_counter() - started,
            "method_cpu_seconds": process_time() - cpu_started,
            "attempt_count": len(attempts),
            "returned_unique_candidates": len({row["patent_id_canonical"] for row in final}),
            "controller_steps": len(actions),
            "controller_tokens": 0,
        },
        "controller_schema_hash": hashlib.sha256(json.dumps(CONTROLLER_RESPONSE_SCHEMA, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--protocol-hash", required=True)
    parser.add_argument("--cohort-manifest-hash", required=True)
    parser.add_argument("--candidate-depth", type=int, default=50)
    parser.add_argument("--rerank-depth", type=int, default=50)
    parser.add_argument("--max-steps", type=int, default=3)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    if args.max_steps < 1 or args.max_steps > 4:
        parser.error("max-steps must be between 1 and 4")
    args.output.mkdir(parents=True)
    runtime = _read_json(args.runtime)
    devices, patents = BASELINES.validate_runtime_payload(runtime)
    candidate_depth = min(args.candidate_depth, len(patents))
    rerank_depth = min(args.rerank_depth, len(patents))
    encoder_path, encoder_tokenizer = BASELINES._model_paths(args.model_root, "sentence-transformers-all-MiniLM-L6-v2")
    reranker_path, reranker_tokenizer = BASELINES._model_paths(args.model_root, "cross-encoder-ms-marco-MiniLM-L-6-v2")
    index_started = perf_counter()
    encoder = BASELINES.DenseEncoder(model_path=encoder_path, tokenizer_path=encoder_tokenizer)
    reranker = BASELINES.CrossEncoderReranker(model_path=reranker_path, tokenizer_path=reranker_tokenizer)
    retriever = BASELINES.SharedRetriever(patents, encoder=encoder, reranker=reranker)
    index_elapsed = perf_counter() - index_started
    rows = [_run_controller_device(device, retriever, candidate_depth=candidate_depth, rerank_depth=rerank_depth, max_steps=args.max_steps) for device in devices]
    predictions = {row["query_id"]: [item["patent_id_canonical"] for item in row["final_ranking"]] for row in rows}
    statuses = {row["query_id"]: row["status"] for row in rows}
    _write_json(args.output / "runtime_predictions.json", {
        "status": "PREDICTIONS_WRITTEN_BEFORE_REFERENCE_LOAD",
        "method": "HT-B4-OFFLINE",
        "predictions": predictions,
        "statuses": statuses,
    })
    (args.output / "raw_rankings.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")
    reference_payload = _read_json(args.references)
    expected, references = BASELINES._validate_references(devices, patents, reference_payload)
    metric = evaluate_known_links(
        expected_query_ids=expected,
        references=references,
        predictions=predictions,
        universe=[patent.patent_id_canonical for patent in patents],
        k=20,
        statuses=statuses,
    )
    group_payload = _read_json(args.groups)
    groups = group_payload.get("shared_exact_patent_groups")
    if not isinstance(groups, list):
        raise ValueError("groups file lacks shared exact patent groups")
    per_query = {row["query_id"]: row for row in metric["per_query"]}
    group_results = []
    for index, group in enumerate(groups):
        values = [per_query[query_id]["known_recall"] for query_id in group if query_id in per_query]
        group_results.append({"group_id": str(index), "query_ids": group, "query_count": len(values), "macro_known_link_recall": sum(values) / len(values) if values else None, "k": 20})
    controller_policy = {
        "name": "deterministic_observation_bounded_controller",
        "version": "ht-b4-offline-v1",
        "actions": ["technical_search", "feature_search", "stop"],
        "max_steps": args.max_steps,
        "stop_rule": "stop on no novelty, or high-yield low-disagreement prefix; otherwise use the next declared feature",
        "source_observations": ["new_candidate_count", "lexical_dense_disagreement", "remaining_query_calls", "remaining_candidate_budget", "source_available"],
        "evaluator_visibility": "none",
        "provider_calls": 0,
        "paid_cost_usd": 0,
    }
    _write_json(args.output / "controller_policy.json", controller_policy)
    _write_json(args.output / "evaluator_validation.json", {
        "method": "HT-B4-OFFLINE",
        "primary_k": 20,
        "metric": metric,
        "group_results": group_results,
        "references_loaded_after_runtime_outputs": True,
    })
    _write_json(args.output / "controller_frontier.json", {
        "status": "DESCRIPTIVE_DEVELOPMENT_CONTROLLER_RUN",
        "method": "HT-B4-OFFLINE",
        "device_count": len(devices),
        "macro_known_link_recall_at_20": metric["macro_known_link_recall"],
        "micro_known_link_recall_at_20": metric["micro_known_link_recall"],
        "failed_device_count": sum(row["status"] == "failed" for row in rows),
        "resources": {
            "query_calls": sum(row["resources"].get("query_calls", 0) for row in rows),
            "rerank_pairs": sum(row["resources"].get("rerank_pairs", 0) for row in rows),
            "embedding_query_tokens": sum(row["resources"].get("embedding_query_tokens", 0) for row in rows),
            "rerank_tokens": sum(row["resources"].get("rerank_tokens", 0) for row in rows),
            "returned_candidates": sum(row["resources"].get("returned_candidates", 0) for row in rows),
            "controller_steps": sum(row["resources"].get("controller_steps", 0) for row in rows),
        },
        "per_device": rows,
        "fixed_prefix_alignment": "first action uses the same technical query as HT-B1/B2/B3; later actions use declared features only",
        "uncertainty": {"status": "NOT_ESTIMABLE", "reason": "development cohorts have no final holdout and insufficient independent groups"},
    })
    _write_json(args.output / "receipt.json", {
        "status": "REAL_PUBLIC_OFFLINE_CONTROLLER_RUN",
        "method": "HT-B4-OFFLINE",
        "code_commit": args.code_commit,
        "protocol_hash": args.protocol_hash,
        "cohort_manifest_hash": args.cohort_manifest_hash,
        "runtime_sha256": _sha256(args.runtime),
        "references_sha256": _sha256(args.references),
        "groups_sha256": _sha256(args.groups),
        "devices": len(devices),
        "patents": len(patents),
        "provider_calls": 0,
        "paid_cost_usd": 0,
        "index_prep_seconds": index_elapsed,
        "artifacts": {
            "controller_policy": "controller_policy.json",
            "controller_frontier": "controller_frontier.json",
            "evaluator_validation": "evaluator_validation.json",
            "raw_rankings": "raw_rankings.jsonl",
            "runtime_predictions": "runtime_predictions.json",
        },
        "limitations": [
            "Offline deterministic controller only; no OpenRouter response or paid inference.",
            "Development-only public disclosure cohort; no final holdout or generalization claim.",
            "Product-level disclosed links are not claim-level semantic gold.",
        ],
    })
    print(json.dumps({"status": "PASS", "output": str(args.output), "macro_known_link_recall_at_20": metric["macro_known_link_recall"]}))


if __name__ == "__main__":
    main()
