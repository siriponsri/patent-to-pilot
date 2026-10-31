"""Bind the existing OpenRouter R1 journal without creating or resetting it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.providers.ledger_registry import register_canonical_ledger  # noqa: E402
from patent_to_pilot.providers.round1 import build_round1_policy, round1_policy_hash  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-path", type=Path, required=True)
    parser.add_argument("--registry-path", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--pricing-snapshot-sha256", required=True)
    parser.add_argument("--pricing-snapshot-utc", required=True)
    parser.add_argument("--ledger-id")
    args = parser.parse_args()
    policy = build_round1_policy(
        {args.model: args.route},
        pricing_snapshot_sha256=args.pricing_snapshot_sha256,
        pricing_snapshot_utc=args.pricing_snapshot_utc,
    )
    binding = register_canonical_ledger(
        args.ledger_path,
        authorization_id=policy["authorization_id"],
        policy_hash=round1_policy_hash(policy),
        pricing_snapshot_sha256=args.pricing_snapshot_sha256,
        pricing_snapshot_utc=args.pricing_snapshot_utc,
        registry_path=args.registry_path,
        ledger_id=args.ledger_id,
    )
    print(json.dumps(binding.as_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
