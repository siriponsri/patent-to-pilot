"""Dry-run and explicitly gated pilot CLI for the two owner-selected models.

Dry-run is the default and never constructs a live dispatch. A live run still
requires an explicit flag, environment key, pinned config, and the existing
ledger budget guards; no live run is authorized by this script.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.providers import (  # noqa: E402
    AttemptLedger,
    OpenRouterAdapter,
    OpenRouterHTTPTransport,
    ProviderCapabilities,
    ProviderConfig,
    ProviderRequest,
)


PRICE_SOURCE = "docs/research/pilot-next/MODEL_SELECTION_AND_COST.md"
PRICE_DATE = "2026-10-25"
MATRIX = [
    {"model": "google/gemini-2.5-flash-lite", "routing_only": ["google-ai-studio"], "input_usd_per_million": 0.10, "output_usd_per_million": 0.40},
    {"model": "openai/gpt-4.1-mini", "routing_only": ["openai"], "input_usd_per_million": 0.40, "output_usd_per_million": 1.60},
]


def build_plan(*, attempts: int, spend_cap: float, input_tokens: int, schema_framing_tokens: int, output_tokens: int) -> dict:
    if attempts < 1 or attempts > 10:
        raise ValueError("pilot attempts must be between 1 and 10")
    if spend_cap < 0 or spend_cap > 1.0:
        raise ValueError("pilot spend cap must be between 0 and 1 USD")
    rows = []
    for index, item in enumerate(MATRIX):
        effective_input = input_tokens + schema_framing_tokens
        upper_bound = (effective_input * item["input_usd_per_million"] + output_tokens * item["output_usd_per_million"]) / 1_000_000
        rows.append({**item, "attempts_max": (attempts + 1) // 2 if index == 0 else attempts // 2, "max_price": {"prompt": item["input_usd_per_million"], "completion": item["output_usd_per_million"]}, "input_allowance_tokens": effective_input, "per_attempt_cost_upper_bound_usd": upper_bound, "cost_estimate_status": "provisional_price_snapshot_not_measured"})
    return {
        "status": "DRY_RUN_NOT_EXECUTABLE" if spend_cap == 0 else "LIVE_REQUIRES_SEPARATE_OWNER_AUTHORIZATION",
        "provider": "openrouter",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "routing": {"allow_fallbacks": False, "automatic_routing": False, "exact_model_pin": True, "require_parameters": True},
        "run_matrix": rows,
        "max_attempts_total": attempts,
        "token_limits": {"input_tokens_per_attempt": input_tokens, "schema_framing_tokens_per_attempt": schema_framing_tokens, "input_allowance_tokens_per_attempt": input_tokens + schema_framing_tokens, "output_tokens_per_attempt": output_tokens, "total_tokens_per_attempt": input_tokens + schema_framing_tokens + output_tokens},
        "cost_upper_bound": {"per_request_must_be_explicit": True, "run_spend_cap_usd": spend_cap, "missing_estimate_is_not_zero": True},
        "price_source": PRICE_SOURCE,
        "price_snapshot_date": PRICE_DATE,
        "actual_cost": None,
        "notes": ["Pricing is provisional catalog information from the project contract.", "No key is read during dry-run.", "Every live attempt must reserve through AttemptLedger before dispatch."],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Patent-to-Pilot OpenRouter pilot preflight")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--live", action="store_true", help="explicit live mode; still requires key and owner authorization")
    parser.add_argument("--attempts", type=int, default=10)
    parser.add_argument("--spend-cap", type=float, default=1.0)
    parser.add_argument("--input-tokens", type=int, default=4000)
    parser.add_argument("--output-tokens", type=int, default=1500)
    parser.add_argument("--schema-framing-tokens", type=int, default=128)
    args = parser.parse_args()
    plan = build_plan(attempts=args.attempts, spend_cap=args.spend_cap, input_tokens=args.input_tokens, schema_framing_tokens=args.schema_framing_tokens, output_tokens=args.output_tokens)
    if not args.live:
        plan["status"] = "DRY_RUN_NOT_EXECUTABLE"
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 0
    # Live mode is deliberately a preflight only in this bounded package. It
    # validates construction and key presence but never auto-starts a batch.
    if os.environ.get("OPENROUTER_API_KEY") is None:
        plan["status"] = "LIVE_BLOCKED_MISSING_KEY"
        print(json.dumps(plan, indent=2, ensure_ascii=False))
        return 2
    plan["status"] = "LIVE_NOT_RUN_OWNER_AUTHORIZATION_REQUIRED"
    plan["live_transport"] = "OpenRouterHTTPTransport available; dispatch not started"
    print(json.dumps(plan, indent=2, ensure_ascii=False))
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
