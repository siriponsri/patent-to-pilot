"""Run the rights-cleared Qwen3-32B API branch over a frozen evidence pack."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.healthtech.api_generation import (  # noqa: E402
    MODEL_ID,
    APIGenerationError,
    OpenRouterQwenGenerationRunner,
    normalize_account_credit_snapshot,
    write_sanitized_receipt,
)
from patent_to_pilot.healthtech.b4_live import B4Pricing  # noqa: E402
from patent_to_pilot.healthtech.generation_payload import (  # noqa: E402
    build_rights_cleared_paired_payload,
    canonical_json,
    sha256_json,
)
from patent_to_pilot.providers import MockHTTPResponse, OpenRouterHTTPTransport  # noqa: E402
from patent_to_pilot.providers.round1 import Round1ProjectBudget  # noqa: E402


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _load_pack(path: Path) -> dict[str, Any]:
    pack = _read_json(path)
    claimed = pack.get("pack_sha256")
    unsigned = dict(pack)
    unsigned.pop("pack_sha256", None)
    if not isinstance(claimed, str) or sha256_json(unsigned) != claimed:
        raise ValueError("pack_sha256 mismatch")
    return pack


def _pricing(path: Path) -> B4Pricing:
    return B4Pricing.model_validate(_read_json(path))


class MockGenerationTransport:
    is_mock = True

    def send(self, *, config, request):
        messages = request.messages or [{"role": "user", "content": request.prompt}]
        payload = json.loads(messages[-1]["content"])
        case = payload["case"]
        content = json.dumps({
            "device_id": case["query"]["device_id_canonical"],
            "device_name": case["query"]["device_id_raw"],
            "findings": [],
            "unresolved": ["Mock transport only; no provider result."],
        }, ensure_ascii=False, sort_keys=True)
        return MockHTTPResponse(200, {
            "model": config.model,
            "provider": config.routing_only[0],
            "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": request.input_tokens_estimate or 0,
                "completion_tokens": 32,
                "total_tokens": (request.input_tokens_estimate or 0) + 32,
                "cost": 0.0,
            },
        })


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--model-snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", choices=["dry-run", "mock", "live"], default="dry-run")
    parser.add_argument("--budget-path", type=Path, default=None, help="mock-only isolated journal; live accepts only canonical path")
    parser.add_argument("--credit-snapshot", type=Path, default=None, help="sanitized current OpenRouter credit snapshot; required for live mode")
    parser.add_argument("--max-output-tokens", type=int, default=512)
    parser.add_argument("--max-findings", type=int, default=6)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh path")
    pack = _load_pack(args.pack)
    pricing = _pricing(args.model_snapshot)
    if pricing.model != MODEL_ID:
        parser.error("model snapshot must pin qwen/qwen3-32b")
    if args.mode == "live" and args.budget_path is None:
        parser.error("--budget-path is required for live mode")
    if args.mode == "live" and args.credit_snapshot is None:
        parser.error("--credit-snapshot is required for live mode")
    account_credit_snapshot = (
        normalize_account_credit_snapshot(_read_json(args.credit_snapshot))
        if args.credit_snapshot is not None
        else None
    )
    if args.mode == "dry-run":
        payload = build_rights_cleared_paired_payload(
            pack,
            provider="openrouter",
            model=MODEL_ID,
            route=pricing.upstream_provider,
            max_output_tokens=args.max_output_tokens,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({
            "format": "ht-o3-api-generation-preflight-v1",
            "status": "DRY_RUN_NOT_EXECUTED",
            "model_id": MODEL_ID,
            "route": pricing.upstream_provider,
            "pack_sha256": payload["pack_sha256"],
            "manifest": payload["manifest"],
            "provider_calls": 0,
            "paid_cost_usd": 0.0,
        }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": "DRY_RUN_NOT_EXECUTED", "manifest_sha256": payload["manifest"]["manifest_sha256"]}))
        return 0
    if args.mode == "mock":
        budget = Round1ProjectBudget(
            args.budget_path or (args.output.parent / "mock-round1.sqlite3"),
            model_provider_map={MODEL_ID: pricing.upstream_provider},
            pricing_snapshot_sha256=pricing.snapshot_sha256,
            pricing_snapshot_utc=pricing.snapshot_utc,
            namespace="mock",
        )
        transport_factory = lambda: MockGenerationTransport()
        live_enabled = False
    else:
        budget = Round1ProjectBudget(
            args.budget_path,
            model_provider_map={MODEL_ID: pricing.upstream_provider},
            pricing_snapshot_sha256=pricing.snapshot_sha256,
            pricing_snapshot_utc=pricing.snapshot_utc,
            namespace="canonical",
        )
        transport_factory = lambda: OpenRouterHTTPTransport()
        live_enabled = True
    try:
        runner = OpenRouterQwenGenerationRunner.from_snapshot(
            budget=budget,
            snapshot_path=args.model_snapshot,
            transport_factory=transport_factory,
            live_enabled=live_enabled,
            account_credit_snapshot=account_credit_snapshot,
            run_id=args.run_id,
            max_output_tokens=args.max_output_tokens,
            max_findings=args.max_findings,
        )
        result = runner.run(pack)
        write_sanitized_receipt(result, args.output)
    finally:
        budget.close()
    print(json.dumps({
        "status": result["status"],
        "model_id": result["model_id"],
        "route": result["route"],
        "manifest_sha256": result["manifest"]["manifest_sha256"],
        "provider_calls": result["provider_calls"],
        "paid_cost_usd": result["paid_cost_usd"],
    }, ensure_ascii=False))
    return 0 if result["status"] == "PASS_API_QWEN3_32B_FROZEN_PACK_GENERATION" else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (APIGenerationError, ValueError) as exc:
        raise SystemExit(f"ERROR: {exc}") from None
