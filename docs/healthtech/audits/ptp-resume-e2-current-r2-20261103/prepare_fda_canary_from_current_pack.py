"""Prepare a rights-cleared FDA factual canary from the current private pack.

The input and outputs are private Windows artifacts. This script never reads
credentials, contacts a provider, opens the budget journal, or copies raw
source payloads into the repository.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.healthtech.generation_payload import (  # noqa: E402
    build_generation_messages,
    build_rights_cleared_paired_payload,
    sha256_json,
)

FIELDS = ["pma_number", "trade_name", "applicant"]
BASIS_URL = "https://open.fda.gov/terms/"


def prepare(input_path: Path, captured_at_utc: str) -> tuple[dict, dict, dict]:
    raw_bytes = input_path.read_bytes()
    input_file_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    original = json.loads(raw_bytes)
    parent_pack_sha256 = original.get("pack_sha256")
    unsigned = dict(original)
    unsigned.pop("pack_sha256", None)
    if not isinstance(parent_pack_sha256, str) or sha256_json(unsigned) != parent_pack_sha256:
        raise ValueError("input pack hash mismatch")

    pack = copy.deepcopy(original)
    pack["purpose"] = "FDA factual canary only; no device-patent comparison"
    pack["status"] = "PREPARED_OFFLINE_NOT_EXECUTED"
    pack["captured_at_utc"] = captured_at_utc
    pack["parent_pack_sha256"] = parent_pack_sha256
    pack["evidence_policy"] = {
        "fields": FIELDS,
        "source_basis": BASIS_URL,
        "excluded": "all patents, disclosures, generic/GMDN terms, raw text and evaluator material",
    }
    pack["prompt_contract"]["system_instructions"] = [
        "Extract only the supplied FDA structured facts. Data provided by the U.S. Food and Drug Administration (https://open.fda.gov).",
        "Keep exact record IDs and source locators. Do not infer clinical suitability, approval status, FTO, patent associations or investment value.",
        "Return JSON only. Omitted evidence is unresolved, never a negative finding.",
    ]

    for case in pack["cases"]:
        source = next(
            source
            for source in case["sources"]
            if source.get("source_type") == "regulatory_record"
            and source.get("redistribution") == "ALLOWED_WITH_ATTRIBUTION"
            and set(FIELDS).issubset(set(source.get("displayable_fields", [])))
        )
        source = copy.deepcopy(source)
        source["basis_url"] = BASIS_URL
        source["clause_locator"] = "Data Rights and Usage; Attribution"
        source["displayable_fields"] = FIELDS
        case["sources"] = [source]
        case["evidence"] = [
            row
            for row in case["evidence"]
            if row.get("source_id") == source["source_id"]
            and row.get("structured_field") in set(FIELDS)
        ]
        if len(case["evidence"]) != len(FIELDS):
            raise ValueError(f"unexpected FDA evidence count: {case['case_id']}")
        case["evidence_order"] = [row["evidence_id"] for row in case["evidence"]]
        case["candidates"] = []
        old_query = case["query"]
        case["query"] = {
            key: old_query.get(key)
            for key in ("query_id", "device_id_canonical", "device_id_raw", "jurisdiction", "evidence_cutoff")
        }
        case["query"].update(
            selected_comparator_source_id=source["source_id"],
            brief="Summarize the reviewed FDA facts.",
            technical_description="",
            features_of_interest=[],
            user_questions=[],
        )
        case["unresolved_items"] = []
        case["remote_transfer_review"] = {
            "purpose": "ht-o3-generation",
            "provider": "openrouter",
            "route": "deepinfra",
            "basis_reference": "openFDA-CC0-structured-PMA-facts-20261031-no-GMDN-no-third-party-documents",
        }

    for case in pack["cases"]:
        case["remote_transfer_review"]["message_sha256"] = sha256_json(
            build_generation_messages(pack, case)
        )

    pack.pop("pack_sha256", None)
    pack["pack_sha256"] = sha256_json(pack)
    payload = build_rights_cleared_paired_payload(
        pack,
        provider="openrouter",
        model="qwen/qwen3-32b",
        route="deepinfra",
        max_output_tokens=512,
    )
    receipt = {
        "format": "ptp-e2-rights-cleared-fda-pack-preparation-v1",
        "status": "PASS_RIGHTS_PROJECTION_OFFLINE_ONLY",
        "prepared_at_utc": captured_at_utc,
        "input_file_sha256": input_file_sha256,
        "parent_pack_sha256": parent_pack_sha256,
        "prepared_pack_sha256": pack["pack_sha256"],
        "cases": len(pack["cases"]),
        "evidence_rows": sum(len(case["evidence"]) for case in pack["cases"]),
        "fields": FIELDS,
        "basis_url": BASIS_URL,
        "source_rights": "ALLOWED_WITH_ATTRIBUTION; FDA structured facts only",
        "source_backed_transfer_review": "PASS",
        "manifest_sha256": payload["manifest"]["manifest_sha256"],
        "message_sha256": {
            case["case_id"]: case["message_sha256"] for case in payload["cases"]
        },
        "payload_sha256": {
            case["case_id"]: case["payload_sha256"] for case in payload["cases"]
        },
        "provider_calls": 0,
        "paid_cost_usd": 0.0,
    }
    return pack, payload, receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--captured-at-utc", default=None)
    args = parser.parse_args()
    if args.output_dir.exists():
        raise SystemExit("OUTPUT_EXISTS")
    captured_at_utc = args.captured_at_utc or datetime.now(timezone.utc).isoformat()
    pack, payload, receipt = prepare(args.input, captured_at_utc)
    args.output_dir.mkdir(parents=True)
    (args.output_dir / "evidence-pack.json").write_text(
        json.dumps(pack, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "exact-messages.json").write_text(
        json.dumps(payload["cases"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (args.output_dir / "preparation-receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": receipt["status"], **{key: receipt[key] for key in (
        "prepared_pack_sha256", "manifest_sha256", "cases", "evidence_rows"
    )}}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
