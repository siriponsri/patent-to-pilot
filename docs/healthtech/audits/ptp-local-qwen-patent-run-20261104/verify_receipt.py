"""Verify a private local Qwen receipt without printing model outputs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "src"))

from patent_to_pilot.healthtech.generation_payload import (  # noqa: E402
    build_generation_messages,
    validate_generation_output,
)


def canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--max-findings", type=int, default=4)
    args = parser.parse_args()

    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    unsigned = dict(pack)
    claimed_pack_hash = unsigned.pop("pack_sha256")
    if hashlib.sha256(canonical(unsigned)).hexdigest() != claimed_pack_hash:
        raise SystemExit("pack hash mismatch")
    if receipt.get("pack_sha256") != claimed_pack_hash:
        raise SystemExit("receipt is bound to a different pack")
    if receipt.get("provider_calls") != 0 or receipt.get("paid_cost_usd") != 0.0:
        raise SystemExit("paid boundary is not zero")

    cases = pack.get("cases", [])
    rows = receipt.get("cases", [])
    if len(cases) != len(rows):
        raise SystemExit("case count mismatch")
    result_rows = []
    for case, row in zip(cases, rows):
        if row.get("case_id") != case.get("case_id"):
            raise SystemExit("case ID mismatch")
        messages = build_generation_messages(pack, case)
        expected_messages_hash = hashlib.sha256(canonical(messages)).hexdigest()
        if row.get("messages_sha256") != expected_messages_hash:
            raise SystemExit(f"message hash mismatch: {case.get('case_id')}")
        parsed = row.get("parsed_output")
        validate_generation_output(parsed, case, args.max_findings)
        if row.get("schema_valid") is not True or row.get("parse_error") is not None:
            raise SystemExit(f"schema receipt mismatch: {case.get('case_id')}")
        result_rows.append(
            {
                "case_id": case["case_id"],
                "schema_valid": True,
                "prompt_tokens": row.get("prompt_tokens"),
                "output_tokens": row.get("output_tokens"),
                "generation_latency_seconds": row.get("generation_latency_seconds"),
                "output_sha256": row.get("output_sha256"),
            }
        )

    print(
        json.dumps(
            {
                "verified_at_utc": datetime.now(timezone.utc).isoformat(),
                "pack_sha256": claimed_pack_hash,
                "receipt_sha256": sha256_file(args.receipt),
                "status": receipt.get("status"),
                "provider_calls": receipt.get("provider_calls"),
                "paid_cost_usd": receipt.get("paid_cost_usd"),
                "cases": result_rows,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
