"""Run provider-shaped HT-B4 control selection over a frozen local cohort.

The mock mode exercises the full structured-provider path without network or
cost. Live mode requires a current endpoint snapshot, an exact R1 ledger, an
explicit provider-transfer manifest, and an approved existing credential.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from contextlib import nullcontext
from pathlib import Path
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.healthtech.retrieval import evaluate_known_links
from patent_to_pilot.healthtech.b4_live import B4Pricing, B4ProviderSelector
from patent_to_pilot.healthtech.controller import ControllerObservation, deterministic_controller_action
from patent_to_pilot.healthtech.provider_transfer import (
    ProviderTransferManifest,
    ProviderVisibleSource,
)
from patent_to_pilot.providers import MockHTTPResponse, MockHTTPTransport, OpenRouterHTTPTransport
from patent_to_pilot.providers.env_file import scoped_env_file_key
from patent_to_pilot.providers.round1 import Round1ProjectBudget, build_round1_policy


def _load_offline_module():
    path = ROOT / "scripts" / "healthtech" / "run_bounded_controller.py"
    spec = importlib.util.spec_from_file_location("healthtech_bounded_controller", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load bounded controller runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OFFLINE = _load_offline_module()
BASELINES = OFFLINE.BASELINES


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _pricing(path: Path) -> B4Pricing:
    payload = _read_json(path)
    return B4Pricing.model_validate(payload)


def _sources(runtime: dict, registry: dict) -> list[ProviderVisibleSource]:
    rows = registry.get("sources")
    if not isinstance(rows, list):
        raise ValueError("source registry lacks sources")
    by_id = {row.get("source_id"): row for row in rows if isinstance(row, dict) and row.get("source_id")}
    source_ids = sorted({row["source_id"] for row in runtime.get("devices", []) + runtime.get("patents", [])})
    result = []
    for source_id in source_ids:
        row = by_id.get(source_id)
        if row is None:
            raise ValueError(f"runtime source is absent from registry: {source_id}")
        source_hash = (
            row.get("payload_sha256")
            or row.get("raw_json_sha256")
            or row.get("normalized_sha256")
            or row.get("raw_html_sha256")
        )
        if not isinstance(source_hash, str) or len(source_hash) != 64:
            raise ValueError(f"runtime source lacks a usable hash: {source_id}")
        result.append(ProviderVisibleSource(
            source_id=source_id,
            source_revision=str(row.get("revision", "")),
            source_sha256=source_hash,
            source_type=str(row.get("source_type", "unknown")),
            synthetic=False,
        ))
    return result


class MockControllerTransport:
    is_mock = True

    def send(self, *, config, request):
        payload = json.loads(request.prompt)
        observation = ControllerObservation.model_validate(payload["observation"])
        action = deterministic_controller_action(observation)
        return MockHTTPResponse(200, {
            "model": config.model,
            "provider": "OpenAI" if config.routing_only == ["openai"] else config.routing_only[0],
            "choices": [{"message": {"content": action.model_dump_json()}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120, "cost": 0.0001},
        })


def _selector_factory(*, args, budget, policy, pricing, runtime_sources, transfer_manifest):
    def make(device):
        transport_factory = (
            (lambda: OpenRouterHTTPTransport())
            if args.mode == "live"
            else (lambda: MockControllerTransport())
        )
        return B4ProviderSelector(
            budget=budget,
            policy=policy,
            pricing=pricing,
            run_id=args.run_id,
            query_id=device.query_id,
            phase=args.phase,
            transport_factory=transport_factory,
            live_enabled=args.mode == "live",
            visible_sources=runtime_sources,
            transfer_manifest=transfer_manifest,
            max_output_tokens=args.max_output_tokens,
        )
    return make


def _run(args: argparse.Namespace, parser: argparse.ArgumentParser) -> int:
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    if not 1 <= args.max_steps <= 4:
        parser.error("max-steps must be between 1 and 4")
    if args.mode == "live" and args.transfer_manifest is None:
        parser.error("live mode requires --transfer-manifest")
    if args.mode == "live" and args.env_file is None and not __import__("os").environ.get("OPENROUTER_API_KEY"):
        parser.error("live mode requires the inherited key or an explicit --env-file")
    args.output.mkdir(parents=True)

    runtime = _read_json(args.runtime)
    registry = _read_json(args.source_registry)
    pricing = _pricing(args.model_snapshot)
    model = args.model or pricing.model
    if model != pricing.model:
        parser.error("--model must match the endpoint snapshot model")
    policy = build_round1_policy(
        {pricing.model: pricing.upstream_provider},
        pricing_snapshot_sha256=pricing.snapshot_sha256,
        pricing_snapshot_utc=pricing.snapshot_utc,
    )
    if args.mode == "mock":
        mock_path = args.budget_path or (args.output / "mock-round1.sqlite3")
        budget = Round1ProjectBudget(
            mock_path,
            model_provider_map={pricing.model: pricing.upstream_provider},
            pricing_snapshot_sha256=pricing.snapshot_sha256,
            pricing_snapshot_utc=pricing.snapshot_utc,
            namespace="mock",
        )
    else:
        budget = Round1ProjectBudget(
            args.budget_path,
            model_provider_map={pricing.model: pricing.upstream_provider},
            pricing_snapshot_sha256=pricing.snapshot_sha256,
            pricing_snapshot_utc=pricing.snapshot_utc,
            namespace="canonical",
        )
    transfer_manifest = None if args.transfer_manifest is None else ProviderTransferManifest.model_validate(_read_json(args.transfer_manifest))
    runtime_sources = _sources(runtime, registry)
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
    selectors = {device.query_id: _selector_factory(
        args=args,
        budget=budget,
        policy=policy,
        pricing=pricing,
        runtime_sources=runtime_sources,
        transfer_manifest=transfer_manifest,
    )(device) for device in devices}
    method = "HT-B4-LIVE" if args.mode == "live" else "HT-B4-MOCK"
    rows = [OFFLINE._run_controller_device(
        device,
        retriever,
        candidate_depth=candidate_depth,
        rerank_depth=rerank_depth,
        max_steps=args.max_steps,
        action_selector=selectors[device.query_id],
        method_name=method,
    ) for device in devices]
    predictions = {row["query_id"]: [item["patent_id_canonical"] for item in row["final_ranking"]] for row in rows}
    statuses = {row["query_id"]: row["status"] for row in rows}
    _write_json(args.output / "runtime_predictions.json", {
        "status": "PREDICTIONS_WRITTEN_BEFORE_REFERENCE_LOAD",
        "method": method,
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
    provider_calls = sum(len(selector.receipts) for selector in selectors.values())
    actual_cost = sum(float(receipt.get("cost_usd") or 0.0) for selector in selectors.values() for receipt in selector.receipts)
    _write_json(args.output / "controller_policy.json", {
        "name": "provider_shaped_observation_bounded_controller",
        "version": "ht-b4-r1-controller-v1",
        "actions": ["technical_search", "feature_search", "stop"],
        "max_steps": args.max_steps,
        "model": pricing.model,
        "upstream_provider": pricing.upstream_provider,
        "phase": args.phase,
        "mode": args.mode,
        "evaluator_visibility": "none",
        "provider_transfer_summary": sorted({item.source_id for item in runtime_sources}),
    })
    _write_json(args.output / "evaluator_validation.json", {
        "method": method,
        "primary_k": 20,
        "metric": metric,
        "group_results": group_results,
        "references_loaded_after_runtime_outputs": True,
    })
    _write_json(args.output / "controller_frontier.json", {
        "status": "DESCRIPTIVE_DEVELOPMENT_PROVIDER_SHAPED_RUN" if args.mode == "mock" else "LIVE_PROVIDER_CONTROLLER_RUN",
        "method": method,
        "device_count": len(devices),
        "macro_known_link_recall_at_20": metric["macro_known_link_recall"],
        "micro_known_link_recall_at_20": metric["micro_known_link_recall"],
        "failed_device_count": sum(row["status"] == "failed" for row in rows),
        "provider_calls": provider_calls,
        "paid_cost_usd": actual_cost if args.mode == "live" else 0.0,
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
    snapshot = budget.snapshot()
    _write_json(args.output / "receipt.json", {
        "status": "REAL_PUBLIC_PROVIDER_SHAPED_MOCK_RUN" if args.mode == "mock" else "REAL_PUBLIC_LIVE_PROVIDER_RUN",
        "method": method,
        "mode": args.mode,
        "code_commit": args.code_commit,
        "protocol_hash": args.protocol_hash,
        "cohort_manifest_hash": args.cohort_manifest_hash,
        "runtime_sha256": _sha256(args.runtime),
        "references_sha256": _sha256(args.references),
        "groups_sha256": _sha256(args.groups),
        "source_registry_sha256": _sha256(args.source_registry),
        "model_snapshot_sha256": _sha256(args.model_snapshot),
        "policy": policy,
        "devices": len(devices),
        "patents": len(patents),
        "provider_calls": provider_calls,
        "paid_cost_usd": actual_cost if args.mode == "live" else 0.0,
        "simulated_cost_usd": actual_cost if args.mode == "mock" else 0.0,
        "ledger_snapshot": snapshot,
        "index_prep_seconds": index_elapsed,
        "artifacts": {
            "controller_policy": "controller_policy.json",
            "controller_frontier": "controller_frontier.json",
            "evaluator_validation": "evaluator_validation.json",
            "raw_rankings": "raw_rankings.jsonl",
            "runtime_predictions": "runtime_predictions.json",
        },
        "limitations": [
            "Mock mode is provider-shaped engineering evidence and incurs no paid cost.",
            "Live mode requires separately reviewed provider-transfer rights for every non-synthetic source.",
            "Development-only public disclosure cohort; no semantic relevance gold or generalization claim.",
            "Product-level disclosed links are not claim-level semantic gold.",
        ],
    })
    print(json.dumps({"status": "PASS", "mode": args.mode, "output": str(args.output), "macro_known_link_recall_at_20": metric["macro_known_link_recall"], "provider_calls": provider_calls, "paid_cost_usd": actual_cost if args.mode == "live" else 0.0}))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--source-registry", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--protocol-hash", required=True)
    parser.add_argument("--cohort-manifest-hash", required=True)
    parser.add_argument("--model-snapshot", type=Path, required=True)
    parser.add_argument(
        "--budget-path",
        type=Path,
        default=None,
        help="isolated mock journal path; live mode accepts only the registered canonical path",
    )
    parser.add_argument("--transfer-manifest", type=Path)
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", choices=["mock", "live"], default="mock")
    parser.add_argument("--phase", choices=["canary", "paired_pilot", "robustness"], default="paired_pilot")
    parser.add_argument("--model", default=None)
    parser.add_argument("--candidate-depth", type=int, default=50)
    parser.add_argument("--rerank-depth", type=int, default=50)
    parser.add_argument("--max-steps", type=int, default=3)
    parser.add_argument("--max-output-tokens", type=int, default=256)
    args = parser.parse_args()
    if args.mode == "live" and args.transfer_manifest is None:
        parser.error("live mode requires --transfer-manifest")
    if args.mode == "live" and args.env_file is None and not __import__("os").environ.get("OPENROUTER_API_KEY"):
        parser.error("live mode requires the inherited key or an explicit --env-file")
    credential_context = (
        scoped_env_file_key(args.env_file)
        if args.mode == "live" and args.env_file is not None
        else nullcontext()
    )
    with credential_context:
        return _run(args, parser)


if __name__ == "__main__":
    raise SystemExit(main())
