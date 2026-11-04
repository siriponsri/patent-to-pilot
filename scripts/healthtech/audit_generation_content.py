"""Audit saved generation outputs against the frozen evidence pack (offline, no model calls).

Writes a sanitized summary: labels, issue codes and hashes only, no generated text.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.healthtech.content_audit import RUBRIC_VERSION, audit_case  # noqa: E402
from patent_to_pilot.healthtech.generation_payload import sha256_json  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--journal", type=Path, required=True, help="private case journal JSONL")
    parser.add_argument("--pack", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True, help="sanitized runner receipt")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists")
    pack = json.loads(args.pack.read_text(encoding="utf-8"))
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    cases = {c["case_id"]: c for c in pack["cases"]}
    receipt_cases = {c["case_id"]: c for c in receipt["cases"]}
    rows = [json.loads(line) for line in args.journal.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    for row in rows:
        if "case" not in row:
            continue
        out = row["case"]
        rec = receipt_cases[out["case_id"]]
        integrity = {
            "output_sha256_recomputed_matches": sha256_json(out["output_text"]) == out["output_sha256"] == rec["output_sha256"],
            "message_sha256_matches_receipt": out["message_sha256"] == rec["message_sha256"],
            "payload_sha256_matches_receipt": out["payload_sha256"] == rec["payload_sha256"],
            "generation_id_matches_receipt": out["provider_generation_id"] == rec["provider_generation_id"],
        }
        audit = audit_case(cases[out["case_id"]], out["parsed_output"])
        results.append({"case_id": out["case_id"], "integrity": integrity, **audit})
    summary = {
        "format": "ptp-generation-content-audit-summary-v1",
        "rubric_version": RUBRIC_VERSION,
        "pack_sha256": pack["pack_sha256"],
        "cases": len(results),
        "findings": sum(r["findings"] for r in results),
        "correct": sum(r["correct"] for r in results),
        "incorrect_or_unsupported": sum(r["incorrect_or_unsupported"] for r in results),
        "flagged_other": sum(r["flagged_other"] for r in results),
        "missing_evidence_rows": sum(len(r["missing_evidence_ids"]) for r in results),
        "all_integrity_checks_pass": all(all(r["integrity"].values()) for r in results),
        "results": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("cases", "findings", "correct", "incorrect_or_unsupported",
                                               "flagged_other", "missing_evidence_rows", "all_integrity_checks_pass")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
