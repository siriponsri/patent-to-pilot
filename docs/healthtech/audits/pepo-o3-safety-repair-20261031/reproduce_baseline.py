"""Offline counterexamples on the owned pre-repair snapshot, synthetic files only."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import tempfile
import argparse

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--baseline-root", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = args.baseline_root.resolve()
sys.path.insert(0, str(root / "src"))
from patent_to_pilot.providers import ledger_registry as registry
from patent_to_pilot.providers.round1 import Round1ProjectBudget, build_round1_policy, round1_policy_hash
from patent_to_pilot.providers.openrouter import OpenRouterHTTPTransport, ProviderConfig, ProviderRequest
from patent_to_pilot.healthtech.api_generation import normalize_account_credit_snapshot

with tempfile.TemporaryDirectory(prefix="ptp-baseline-synthetic-") as temporary:
    work = Path(temporary)
    policy = build_round1_policy({"qwen/qwen3-32b": "DeepInfra"}, pricing_snapshot_sha256="a" * 64, pricing_snapshot_utc="2026-10-31T00:00:00Z")
    ledger = work / "fresh.sqlite3"
    ledger.write_bytes(b"")
    reg = work / "binding.json"
    registry.default_registry_path = lambda _: reg
    registry.register_canonical_ledger(ledger, authorization_id=policy["authorization_id"],
        policy_hash=round1_policy_hash(policy), pricing_snapshot_sha256="a" * 64,
        pricing_snapshot_utc="2026-10-31T00:00:00Z")
    # The registered zero-byte file has no historical attempts or SQLite schema.
    budget = Round1ProjectBudget(ledger, model_provider_map=policy["models"],
        pricing_snapshot_sha256="a" * 64, pricing_snapshot_utc="2026-10-31T00:00:00Z")
    budget.reserve(attempt_id="synthetic-only", phase="paired_pilot", model="qwen/qwen3-32b",
        provider="DeepInfra", payload_sha256="b" * 64, upper_bound_usd=.01, bound_verified=True, data_class="synthetic")
    output = {"baseline_source": "8b64ca09 source snapshot", "all_fixtures_synthetic": True,
        "non_sqlite_registration_accepted": True,
        "empty_canonical_without_history_reserved_nano_usd": budget.snapshot()["committed_nano_usd"],
        "registry_policy_hash_matches_sqlite_policy_hash": round1_policy_hash(policy) == budget.policy_hash}
    budget.close()
    output["stale_credit_accepted"] = bool(normalize_account_credit_snapshot({
        "format": "ptp-openrouter-credit-snapshot-v1", "provider": "openrouter", "source": "approved_integration",
        "as_of_utc": "2000-01-01T00:00:00Z", "remaining_credits_usd": 100}))
    output["future_credit_accepted"] = bool(normalize_account_credit_snapshot({
        "format": "ptp-openrouter-credit-snapshot-v1", "provider": "openrouter", "source": "owner_sanitized_snapshot",
        "as_of_utc": "2999-01-01T00:00:00Z", "remaining_credits_usd": 100}))
    payload = OpenRouterHTTPTransport._request_payload(ProviderConfig(model="qwen/qwen3-32b"),
        ProviderRequest(prompt="ORIGINAL SYNTHETIC", messages=[{"role": "user", "content": "ORIGINAL SYNTHETIC"}],
            parameters={"messages": [{"role": "user", "content": "OVERRIDDEN SYNTHETIC"}]}))
    output["parameters_replaced_frozen_messages"] = payload["messages"][0]["content"] == "OVERRIDDEN SYNTHETIC"
    output["external_provider_calls"] = 0
    output["actual_paid_cost_usd"] = 0
with args.output.open("x", encoding="utf-8") as handle:
    handle.write(json.dumps(output, indent=2) + "\n")
print(json.dumps(output, indent=2))
