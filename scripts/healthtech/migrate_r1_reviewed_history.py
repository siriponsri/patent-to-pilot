"""Install a reviewed R1 history anchor and pre-R1 carryover in place."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.providers.history_migration import migrate_reviewed_r1_history  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-path", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--carryover", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--route", required=True)
    parser.add_argument("--pricing-snapshot-sha256", required=True)
    parser.add_argument("--pricing-snapshot-utc", required=True)
    parser.add_argument("--registry-path", type=Path)
    args = parser.parse_args()
    review = json.loads(args.review.read_text(encoding="utf-8"))
    carryover = json.loads(args.carryover.read_text(encoding="utf-8"))
    binding = migrate_reviewed_r1_history(
        args.ledger_path,
        model_provider_map={args.model: args.route},
        pricing_snapshot_sha256=args.pricing_snapshot_sha256,
        pricing_snapshot_utc=args.pricing_snapshot_utc,
        review=review,
        carryover=carryover,
        registry_path=args.registry_path,
    )
    print(json.dumps(binding.as_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
