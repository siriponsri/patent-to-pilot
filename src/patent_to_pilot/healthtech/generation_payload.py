"""Shared frozen-message and rights-cleared payload contract for O3.

Both the local Qwen3-8B runner and the OpenRouter Qwen3-32B runner call these
helpers. The remote branch receives only the reviewed model-visible projection;
raw source payloads, evaluator material, and credentials are excluded.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any


PACK_FORMAT = "ht-o3-qwen3-frozen-evidence-pack-v1"
PAYLOAD_FORMAT = "ht-o3-rights-cleared-paired-payload-v1"
REMOTE_ALLOWED_RIGHTS = {"ALLOWED", "ALLOWED_WITH_ATTRIBUTION"}


class GenerationPayloadError(ValueError):
    """Raised when a frozen pack cannot be transferred safely."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def strip_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def _model_visible_case(pack: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    if pack.get("format") != PACK_FORMAT:
        raise GenerationPayloadError("unexpected evidence pack format")
    sources = case.get("sources")
    if not isinstance(sources, list) or any(not isinstance(row, dict) for row in sources):
        raise GenerationPayloadError("case source descriptors are invalid")
    if any("payload" in row or "raw_html" in row or "raw_text" in row for row in sources):
        raise GenerationPayloadError("raw source payload is not allowed in the model projection")
    query = case.get("query")
    if not isinstance(query, dict):
        raise GenerationPayloadError("case query is invalid")
    compact_evidence = []
    for row in case.get("evidence", []):
        if not isinstance(row, dict):
            raise GenerationPayloadError("case evidence row is invalid")
        compact_row = dict(row)
        value = compact_row.get("structured_value")
        if isinstance(value, list) and len(value) > 8:
            compact_row["structured_value"] = {
                "count": len(value),
                "values_omitted_from_model_view": True,
            }
        compact_evidence.append(compact_row)
    candidates = case.get("candidates", [])
    if not isinstance(candidates, list):
        raise GenerationPayloadError("case candidates are invalid")
    compact_case = {
        "case_id": case.get("case_id"),
        "query": {
            key: query.get(key)
            for key in (
                "query_id",
                "device_id_canonical",
                "device_id_raw",
                "jurisdiction",
                "brief",
                "technical_description",
                "features_of_interest",
                "user_questions",
                "evidence_cutoff",
            )
        },
        "evidence": compact_evidence,
        "candidates": [
            {
                key: candidate.get(key)
                for key in (
                    "rank",
                    "association_status",
                    "disclosure_evidence_id",
                    "patent_id_canonical",
                    "patent_id_raw",
                    "source_id",
                    "source_revision",
                    "locator",
                )
            }
            for candidate in candidates[:6]
            if isinstance(candidate, dict)
        ],
        "candidate_preview": "first six candidates only; complete ordered candidate list remains in the frozen pack",
        "unresolved_items": case.get("unresolved_items", [])[:1],
    }
    return compact_case


def build_generation_messages(pack: dict[str, Any], case: dict[str, Any]) -> list[dict[str, str]]:
    """Build the exact message list shared by local and API branches."""
    contract = pack.get("prompt_contract")
    if not isinstance(contract, dict) or not isinstance(contract.get("system_instructions"), list):
        raise GenerationPayloadError("pack prompt contract is missing")
    system_text = "\n".join(str(item) for item in contract["system_instructions"])
    compact_case = _model_visible_case(pack, case)
    compact_schema = (
        "Return one JSON object with exactly these top-level keys: device_id, device_name, findings, unresolved. "
        "Each finding must have exactly: record_type, record_id, source_id, locator, classification, summary, support_basis. "
        "record_type is evidence or candidate; classification is source_fact, disclosed_link, retrieved_candidate, or unresolved. "
        "Use exact IDs and locators from the case. unresolved must contain zero or one concise string."
    )
    user_payload = {
        "task": "Extract an auditable evidence summary for one named device.",
        "output_schema": compact_schema,
        "case": compact_case,
    }
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True)},
    ]


def validate_generation_output(parsed: Any, case: dict[str, Any], max_findings: int) -> None:
    """Validate output IDs, locators, and candidate association semantics."""
    if not isinstance(parsed, dict) or set(parsed) != {"device_id", "device_name", "findings", "unresolved"}:
        raise ValueError("output keys do not match frozen schema")
    if parsed["device_id"] != case["query"]["device_id_canonical"]:
        raise ValueError("device_id does not match case")
    if not isinstance(parsed["device_name"], str):
        raise ValueError("device_name is not a string")
    findings = parsed["findings"]
    if not isinstance(findings, list) or len(findings) > max_findings:
        raise ValueError("findings violates maxItems")
    evidence_by_id = {row["evidence_id"]: row for row in case["evidence"]}
    all_candidates = case["candidates"]
    visible_candidates = all_candidates[:6]
    candidate_by_id = {row["patent_id_canonical"]: row for row in visible_candidates}
    for row in all_candidates:
        if row.get("association_status") == "disclosed_link":
            disclosure_id = row.get("disclosure_evidence_id")
            disclosure = evidence_by_id.get(disclosure_id)
            if disclosure is None or disclosure.get("evidence_kind") != "patent_disclosure":
                raise ValueError("candidate disclosed_link lacks source-backed disclosure evidence")
    allowed_types = {"source_fact", "disclosed_link", "retrieved_candidate", "unresolved"}
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("finding is not an object")
        required = {"record_type", "record_id", "source_id", "locator", "classification", "summary", "support_basis"}
        if set(finding) != required:
            raise ValueError("finding keys do not match frozen schema")
        if finding["record_type"] not in {"evidence", "candidate"}:
            raise ValueError("unknown record_type")
        classification = finding["classification"]
        if classification not in allowed_types:
            raise ValueError("unknown classification")
        if finding["record_type"] == "evidence":
            row = evidence_by_id.get(finding["record_id"])
            if row is None:
                raise ValueError("finding references unknown evidence_id")
            if finding["source_id"] != row["source_id"] or finding["locator"] != row["locator"]:
                raise ValueError("evidence source_id/locator mismatch")
            if classification not in {"source_fact", "disclosed_link", "unresolved"}:
                raise ValueError("evidence classification is not supported")
            if classification == "disclosed_link" and row.get("evidence_kind") != "patent_disclosure":
                raise ValueError("disclosed_link classification requires patent disclosure evidence")
        elif finding["record_type"] == "candidate":
            row = candidate_by_id.get(finding["record_id"])
            if row is None:
                raise ValueError("finding references candidate outside model-visible preview")
            if finding["source_id"] != row["source_id"] or finding["locator"] != row["locator"]:
                raise ValueError("candidate source_id/locator mismatch")
            if classification not in {"disclosed_link", "retrieved_candidate"}:
                raise ValueError("candidate classification is not supported")
            if classification != row.get("association_status"):
                raise ValueError("candidate classification does not match association_status")
        if not isinstance(finding["summary"], str) or not isinstance(finding["support_basis"], str):
            raise ValueError("finding text fields are not strings")
    if not isinstance(parsed["unresolved"], list) or any(not isinstance(item, str) for item in parsed["unresolved"]):
        raise ValueError("unresolved must be a string array")


def _source_decision(source: dict[str, Any]) -> str:
    if source.get("synthetic") is True:
        return "SYNTHETIC"
    decision = source.get("redistribution")
    if decision not in REMOTE_ALLOWED_RIGHTS:
        raise GenerationPayloadError(
            f"source {source.get('source_id')} is not rights-cleared for remote generation"
        )
    return str(decision)


def _case_source_ids(case: dict[str, Any]) -> list[str]:
    ids = []
    query = case.get("query") or {}
    if query.get("selected_comparator_source_id"):
        ids.append(query["selected_comparator_source_id"])
    for group in (case.get("evidence", []), case.get("candidates", [])):
        for row in group:
            if isinstance(row, dict) and row.get("source_id"):
                ids.append(row["source_id"])
    return sorted(set(ids))


def build_rights_cleared_paired_payload(
    pack: dict[str, Any],
    *,
    provider: str,
    model: str,
    route: str,
    max_output_tokens: int = 512,
) -> dict[str, Any]:
    """Return runtime payloads plus a sanitized manifest view.

    The returned ``cases[*].messages`` are kept for the immediate runner only;
    callers writing artifacts should persist ``manifest`` and its hashes, not
    the raw messages or generated output.
    """
    if pack.get("format") != PACK_FORMAT:
        raise GenerationPayloadError("unexpected frozen pack format")
    if provider != "openrouter" or not model or not route:
        raise GenerationPayloadError("exact provider, model, and route are required")
    if max_output_tokens < 1:
        raise GenerationPayloadError("max_output_tokens must be positive")
    cases = pack.get("cases")
    if not isinstance(cases, list) or not cases:
        raise GenerationPayloadError("frozen pack has no cases")
    output_schema = pack.get("prompt_contract", {}).get("output_schema")
    if not isinstance(output_schema, dict):
        raise GenerationPayloadError("frozen output schema is missing")
    runtime_cases = []
    manifest_cases = []
    all_decisions = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("case_id"), str):
            raise GenerationPayloadError("frozen case is invalid")
        source_by_id = {
            row.get("source_id"): row
            for row in case.get("sources", [])
            if isinstance(row, dict) and row.get("source_id")
        }
        source_bindings = []
        for source_id in _case_source_ids(case):
            source = source_by_id.get(source_id)
            if source is None:
                raise GenerationPayloadError(f"case source descriptor is missing: {source_id}")
            decision = _source_decision(source)
            all_decisions.append(decision)
            source_bindings.append({
                "source_id": source_id,
                "source_revision": source.get("version_label"),
                "source_sha256": source.get("sha256"),
                "decision": decision,
                "rights_id": source.get("rights_id"),
                "basis_url": source.get("basis_url"),
                "basis_locator": source.get("clause_locator") or source.get("locator"),
                "displayable_fields": source.get("displayable_fields", []),
            })
        messages = build_generation_messages(pack, case)
        request_shape = {
            "model": model,
            "route": route,
            "messages": messages,
            "response_schema": output_schema,
            "max_output_tokens": max_output_tokens,
            "thinking": False,
        }
        message_hash = sha256_json(messages)
        payload_hash = sha256_json(request_shape)
        runtime_cases.append({
            "case_id": case["case_id"],
            "messages": messages,
            "response_schema": output_schema,
            "message_sha256": message_hash,
            "payload_sha256": payload_hash,
            "source_bindings": source_bindings,
        })
        manifest_cases.append({
            "case_id": case["case_id"],
            "source_bindings": source_bindings,
            "message_sha256": message_hash,
            "payload_sha256": payload_hash,
        })
    decision = "ALLOWED_WITH_ATTRIBUTION" if "ALLOWED_WITH_ATTRIBUTION" in all_decisions else "ALLOWED"
    unsigned_manifest = {
        "format": PAYLOAD_FORMAT,
        "purpose": "ht-o3-generation",
        "provider": provider,
        "model": model,
        "route": route,
        "thinking": False,
        "max_output_tokens": max_output_tokens,
        "pack_sha256": pack["pack_sha256"],
        "decision": decision,
        "excluded_fields": [
            "raw source payloads",
            "raw HTML/source pages",
            "evaluator labels and qrels",
            "gold-derived queries",
            "provider credentials",
            "generated output text",
        ],
        "model_visible_fields": {
            "query": ["query_id", "device_id_canonical", "device_id_raw", "jurisdiction", "brief", "technical_description", "features_of_interest", "user_questions", "evidence_cutoff"],
            "evidence": "frozen evidence rows without source payloads",
            "candidates": "first six ordered candidates with exact IDs, statuses, revisions, and locators",
            "sources": "rights-cleared metadata and hashes only",
        },
        "cases": manifest_cases,
    }
    manifest = unsigned_manifest | {"manifest_sha256": sha256_json(unsigned_manifest)}
    return {
        "format": PAYLOAD_FORMAT,
        "manifest": manifest,
        "cases": runtime_cases,
        "pack_sha256": pack["pack_sha256"],
        "decision": decision,
    }
