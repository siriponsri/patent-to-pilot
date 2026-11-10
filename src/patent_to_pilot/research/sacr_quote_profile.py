"""Prospective quote-profile v1 adapter. Never repairs offset-profile v0 output."""
from copy import deepcopy
import hashlib
import json

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields
from patent_to_pilot.research.sacr_profile import validate_profile


def resolve_quote(quote: dict, source: str) -> dict:
    exact_fields(quote, {"field", "text"})
    text = quote["text"]
    if quote["field"] != "allowed_query" or type(text) is not str or not text.strip():
        raise InputBoundaryError("invalid source quotation")
    start = source.find(text)
    # Search overlaps too: "aa" in "aaa" is ambiguous, unlike str.count().
    if start < 0 or source.find(text, start + 1) >= 0:
        raise InputBoundaryError("source quotation absent or ambiguous")
    return {"field": "allowed_query", "start": start, "end": start + len(text), "text": text}


def align_quote_profile(proposal: dict, *, source: str, query_id: str, input_kind: str) -> dict:
    if type(source) is not str or not source.strip() or type(proposal) is not dict:
        raise InputBoundaryError("invalid quote-profile input")
    if proposal.get("profile_version") != "sacr-profile-quotes-v1":
        raise InputBoundaryError("only explicitly versioned quote profiles may be aligned")
    original = json.dumps(proposal, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    canonical = deepcopy(proposal)
    canonical["profile_version"] = "sacr-profile-v0"
    count = 0
    def walk(value):
        nonlocal count
        if type(value) is dict:
            for key, child in value.items():
                if key == "source_spans":
                    if type(child) is not list:
                        raise InputBoundaryError("invalid quote-reference list")
                    value[key] = [resolve_quote(quote, source) for quote in child]
                    count += len(child)
                else:
                    walk(child)
        elif type(value) is list:
            for child in value:
                walk(child)
    walk(canonical)
    validation = validate_profile(canonical, source=source, query_id=query_id, input_kind=input_kind)
    raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {"profile": canonical, "validation": validation, "alignment": {
        "format": "sacr-quote-alignment-v1", "proposal_sha256": hashlib.sha256(original).hexdigest(),
        "canonical_profile_sha256": hashlib.sha256(raw).hexdigest(), "resolved_references": count,
        "policy": "UNIQUE_EXACT_CODEPOINT_MATCH_NO_NORMALIZATION", "semantic_status": "unknown"}}
