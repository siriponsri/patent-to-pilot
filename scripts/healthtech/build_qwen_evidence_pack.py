"""Build a hash-bound, local-research-only Qwen evidence pack."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


CASE_ORDER = ["HT-DEV-MITRACLIP", "HT-DEV-TENDYNE", "HT-DEV-TRICLIP"]
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"
MODEL_ID = "Qwen/Qwen3-8B"


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _source_descriptor(source: dict[str, Any]) -> dict[str, Any]:
    registry = source.get("source")
    if not isinstance(registry, dict):
        raise ValueError("dossier source lacks source registry object")
    rights = source.get("rights")
    rights = rights if isinstance(rights, dict) else {}
    return {
        "source_id": registry.get("source_id"),
        "source_type": registry.get("source_type"),
        "version_label": registry.get("version_label"),
        "sha256": registry.get("sha256"),
        "uri": registry.get("uri"),
        "locator": registry.get("locator"),
        "record_id": registry.get("record_id"),
        "retrieved_at": registry.get("retrieved_at"),
        "limits": registry.get("limits", []),
        "rights_id": rights.get("rights_id"),
        "basis_url": rights.get("basis_url"),
        "clause_locator": rights.get("clause_locator"),
        "local_evaluation": rights.get("local_evaluation"),
        "product_display": rights.get("product_display"),
        "redistribution": rights.get("redistribution"),
        "displayable_fields": rights.get("displayable_fields", []),
        "synthetic": bool(source.get("synthetic", False)),
    }


def _evidence_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "evidence_id": row.get("evidence_id"),
        "evidence_kind": row.get("evidence_kind"),
        "jurisdiction": row.get("jurisdiction"),
        "locator": row.get("locator"),
        "payload_hash": row.get("payload_hash"),
        "source_date": row.get("source_date"),
        "source_id": row.get("source_id"),
        "source_version": row.get("source_version"),
        "statement": row.get("statement"),
        "structured_field": row.get("structured_field"),
        "structured_value": row.get("structured_value"),
        "support_basis": row.get("support_basis"),
        "verification_status": row.get("verification_status"),
    }


def _candidate_row(index: int, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": index + 1,
        "association_status": row.get("association_status"),
        "disclosure_evidence_id": row.get("disclosure_evidence_id"),
        "family_id": row.get("family_id"),
        "family_source_id": row.get("family_source_id"),
        "patent_id_canonical": row.get("patent_id_canonical"),
        "patent_id_raw": row.get("patent_id_raw"),
        "retrieval_action_ids": row.get("retrieval_action_ids", []),
        "scores": row.get("scores", {}),
        "source_id": row.get("source_id"),
        "source_revision": row.get("source_revision"),
        "locator": f"candidate:{row.get('patent_id_canonical')}",
    }


def _query_view(query: dict[str, Any]) -> dict[str, Any]:
    allowed = (
        "query_id",
        "device_id_canonical",
        "device_id_raw",
        "jurisdiction",
        "brief",
        "technical_description",
        "features_of_interest",
        "user_questions",
        "evidence_cutoff",
        "permitted_inputs",
        "selected_comparator_source_id",
    )
    return {key: query.get(key) for key in allowed}


def _case_view(case_id: str, dossier_path: Path) -> dict[str, Any]:
    dossier = _read_object(dossier_path)
    query = dossier.get("query")
    evidence = dossier.get("evidence")
    candidates = dossier.get("candidates")
    sources = dossier.get("sources")
    if not isinstance(query, dict) or not isinstance(evidence, list) or not isinstance(candidates, list) or not isinstance(sources, list):
        raise ValueError(f"invalid dossier shape: {dossier_path}")
    if query.get("query_id") != case_id:
        raise ValueError(f"case id mismatch in {dossier_path}")
    if any(not isinstance(item, dict) for item in evidence + candidates + sources):
        raise ValueError(f"non-object row in {dossier_path}")
    return {
        "case_id": case_id,
        "input_dossier_sha256": _sha256_file(dossier_path),
        "query": _query_view(query),
        "evidence_order": "preserved_from_dossier_json",
        "evidence": [_evidence_row(item) for item in evidence],
        "candidates": [_candidate_row(index, item) for index, item in enumerate(candidates)],
        "sources": [_source_descriptor(item) for item in sources],
        "unresolved_items": dossier.get("unresolved_items", []),
    }


def _prompt_contract() -> dict[str, Any]:
    return {
        "condition": {
            "thinking": False,
            "do_sample": False,
            "max_new_tokens": 512,
            "output_language": "English JSON",
        },
        "system_instructions": [
            "Use only the supplied local-research evidence pack.",
            "Return exactly one JSON object and no markdown or explanation.",
            "Preserve evidence_id, source_id, and locator values exactly.",
            "Use record_type=evidence for evidence rows and record_type=candidate for patent candidates.",
            "Return at most 4 findings; keep summary and support_basis concise.",
            "Return unresolved as an array with zero or one concise string.",
            "Do not infer clinical suitability, FTO, patent validity, approval probability, or investment merit.",
            "Treat product-level disclosed_link evidence as product-level disclosure only, not semantic claim proof.",
            "Treat retrieved_candidate rows as candidates only; do not upgrade them to disclosed links.",
            "If the pack does not support a conclusion, put the limitation in unresolved.",
        ],
        "output_schema": {
            "type": "object",
            "additionalProperties": False,
            "required": ["device_id", "device_name", "findings", "unresolved"],
            "properties": {
                "device_id": {"type": "string"},
                "device_name": {"type": "string"},
                "findings": {
                    "type": "array",
                    "maxItems": 6,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": [
                            "record_type",
                            "record_id",
                            "source_id",
                            "locator",
                            "classification",
                            "summary",
                            "support_basis",
                        ],
                        "properties": {
                            "record_type": {"enum": ["evidence", "candidate"]},
                            "record_id": {"type": "string"},
                            "source_id": {"type": "string"},
                            "locator": {"type": "string"},
                            "classification": {
                                "enum": ["source_fact", "disclosed_link", "retrieved_candidate", "unresolved"]
                            },
                            "summary": {"type": "string"},
                            "support_basis": {"type": "string"},
                        },
                    },
                },
                "unresolved": {"type": "array", "items": {"type": "string"}},
            },
        },
    }


def _write_pack(cases: list[dict[str, Any]], output_path: Path, captured_at_utc: str | None = None) -> dict[str, Any]:
    if not cases:
        raise ValueError("at least one dossier case is required")
    pack: dict[str, Any] = {
        "format": "ht-o3-qwen3-frozen-evidence-pack-v1",
        "status": "PASS_FROZEN_LOCAL_RESEARCH_PACK",
        "captured_at_utc": captured_at_utc or datetime.now(timezone.utc).isoformat(),
        "purpose": "local_research_only",
        "model_condition": {
            "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "license": "apache-2.0",
            "dtype": "float16",
            "attention": "eager",
            "thinking": False,
            "provider_calls": 0,
            "paid_cost_usd": 0.0,
        },
        "runtime_exclusions": [
            "evaluator labels",
            "qrels and gold-derived queries",
            "hidden oracles",
            "raw HTML/source payloads",
            "provider credentials",
        ],
        "evidence_policy": {
            "case_order": [case["case_id"] for case in cases],
            "evidence_order": "preserve dossier JSON order",
            "candidate_order": "preserve dossier JSON order and assign one-based rank",
            "source_payloads": "excluded; source IDs, hashes, locators, and rights metadata retained",
            "unlisted_pairs": "remain unjudged and are not recoded as negatives",
        },
        "prompt_contract": _prompt_contract(),
        "cases": cases,
    }
    pack["pack_sha256"] = _sha256_bytes(_canonical_json(pack))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(pack, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return pack


def build_pack(dossier_root: Path, output_path: Path, captured_at_utc: str | None = None) -> dict[str, Any]:
    cases = []
    for case_id in CASE_ORDER:
        dossier_path = dossier_root / case_id / "dossier.json"
        if not dossier_path.is_file():
            raise FileNotFoundError(dossier_path)
        cases.append(_case_view(case_id, dossier_path))
    return _write_pack(cases, output_path, captured_at_utc=captured_at_utc)


def build_single_pack(dossier_path: Path, case_id: str, output_path: Path, captured_at_utc: str | None = None) -> dict[str, Any]:
    if not dossier_path.is_file():
        raise FileNotFoundError(dossier_path)
    return _write_pack([_case_view(case_id, dossier_path)], output_path, captured_at_utc=captured_at_utc)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--dossier-root", type=Path)
    source.add_argument("--dossier", type=Path)
    parser.add_argument("--case-id")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--captured-at-utc")
    args = parser.parse_args()
    if args.dossier is not None:
        if not args.case_id:
            parser.error("--case-id is required with --dossier")
        pack = build_single_pack(args.dossier, args.case_id, args.output, captured_at_utc=args.captured_at_utc)
    else:
        pack = build_pack(args.dossier_root, args.output, captured_at_utc=args.captured_at_utc)
    print(json.dumps({
        "status": pack["status"],
        "pack_sha256": pack["pack_sha256"],
        "case_order": pack["evidence_policy"]["case_order"],
        "case_count": len(pack["cases"]),
        "evidence_counts": {case["case_id"]: len(case["evidence"]) for case in pack["cases"]},
        "candidate_counts": {case["case_id"]: len(case["candidates"]) for case in pack["cases"]},
        "source_counts": {case["case_id"]: len(case["sources"]) for case in pack["cases"]},
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
