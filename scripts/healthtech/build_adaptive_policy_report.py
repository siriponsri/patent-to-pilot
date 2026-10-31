"""Build the goal-specific adaptive acquisition report from audited receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.healthtech.adaptive_report import build_adaptive_policy_report, write_adaptive_policy_report


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--holdout-comparison", type=Path, required=True)
    parser.add_argument("--offline-verification", type=Path, required=True)
    parser.add_argument("--cross-cohort-comparison", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--code-commit", required=True)
    parser.add_argument("--parent-audit", required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    paths = [args.holdout_comparison, args.offline_verification]
    if args.cross_cohort_comparison is not None:
        paths.append(args.cross_cohort_comparison)
    report = build_adaptive_policy_report(
        holdout_comparison=_read_json(args.holdout_comparison),
        offline_verification=_read_json(args.offline_verification),
        cross_cohort_comparison=(
            None if args.cross_cohort_comparison is None else _read_json(args.cross_cohort_comparison)
        ),
        code_commit=args.code_commit,
        parent_audit=args.parent_audit,
        input_hashes={str(path): _sha256(path) for path in paths},
    )
    write_adaptive_policy_report(args.output, report)
    print(json.dumps({"status": report["status"], "output": str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
