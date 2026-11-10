"""Structural/source checks, never semantic certification of an LLM profile."""
from __future__ import annotations

import hashlib

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, exact_fields, identifier


def _text(value):
    if type(value) is not str or not value.strip():
        raise InputBoundaryError("invalid profile text")


def _fields(value, required, optional=()):
    if type(value) is not dict or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        raise InputBoundaryError("profile schema mismatch")


def _spans(spans, source, *, required=True):
    if type(spans) is not list or (required and not spans):
        raise InputBoundaryError("invalid source span list")
    seen = set()
    for span in spans:
        exact_fields(span, {"field", "start", "end", "text"})
        start, end = span["start"], span["end"]
        if (span["field"] != "allowed_query" or type(start) is not int or type(end) is not int or
                not 0 <= start < end <= len(source) or span["text"] != source[start:end] or
                (start, end) in seen):
            raise InputBoundaryError("invalid or duplicate source span")
        seen.add((start, end))
    return [span["text"] for span in spans]


def validate_profile(profile, *, source: str, query_id: str, input_kind: str) -> dict:
    """Validate v0 structure and exact code-point offsets. No hidden inputs.

    Proposed caps: eight blocks, eight conditions per block. Uncertain condition
    attachment is never counted as conjunction-ready. Changed normalization and
    abstraction are explicitly flagged for review, even with valid source spans.
    """
    _text(source)
    identifier(query_id)
    if input_kind not in ("MTM_P", "DAPFAM_TA"):
        raise InputBoundaryError("unsupported declared query view")
    exact_fields(profile, {"profile_version", "query_id", "source_sha256", "input_kind", "blocks",
                           "context_items", "unknowns", "extraction_status", "failure_reasons"})
    if (profile["profile_version"] != "sacr-profile-v0" or profile["query_id"] != query_id or
            profile["input_kind"] != input_kind or
            profile["source_sha256"] != hashlib.sha256(source.encode("utf-8")).hexdigest()):
        raise InputBoundaryError("profile source identity mismatch")
    status = profile["extraction_status"]
    if status not in ("valid", "partial", "failed"):
        raise InputBoundaryError("invalid extraction status")
    for key in ("blocks", "context_items", "unknowns", "failure_reasons"):
        if type(profile[key]) is not list:
            raise InputBoundaryError("invalid profile list")
    for reason in profile["failure_reasons"]:
        _text(reason)
    if (status == "valid" and profile["failure_reasons"]) or (status == "failed" and not profile["failure_reasons"]):
        raise InputBoundaryError("inconsistent extraction status")
    if len(profile["blocks"]) > 8:
        raise InputBoundaryError("relation block cap exceeded")
    ids, reviews, last_start = set(), [], -1
    explicit, uncertain, active = 0, 0, 0
    def unique(value):
        identifier(value)
        if value in ids:
            raise InputBoundaryError("duplicate profile item identifier")
        ids.add(value)
    for block in profile["blocks"]:
        _fields(block, {"block_id", "relation_text", "source_spans", "attached_conditions"},
                {"action", "operand", "effect"})
        unique(block["block_id"])
        _text(block["relation_text"])
        evidence = _spans(block["source_spans"], source)
        start = min(span["start"] for span in block["source_spans"])
        if start < last_start:
            raise InputBoundaryError("blocks not in source order")
        last_start = start
        if not any(block["relation_text"] in text for text in evidence):
            reviews.append("relation_normalization")
        for role in ("action", "operand", "effect"):
            if block.get(role) is not None:
                _text(block[role])
                if not any(block[role] in text for text in evidence):
                    raise InputBoundaryError("role is not source backed")
        conditions = block["attached_conditions"]
        if type(conditions) is not list or len(conditions) > 8:
            raise InputBoundaryError("condition cap exceeded")
        block_active = False
        for condition in conditions:
            _fields(condition, {"condition_id", "raw_text", "normalized_text", "kind", "relation_to_block", "source_spans"},
                    {"numeric_value", "unit"})
            unique(condition["condition_id"])
            raw, normalized = condition["raw_text"], condition["normalized_text"]
            _text(raw)
            _text(normalized)
            snippets = _spans(condition["source_spans"], source)
            if not any(raw in text for text in snippets):
                raise InputBoundaryError("condition raw text is not source backed")
            if condition["kind"] not in ("numeric", "qualitative", "polarity", "direction", "material", "other"):
                raise InputBoundaryError("unknown condition kind")
            if condition["relation_to_block"] not in ("explicit", "uncertain"):
                raise InputBoundaryError("invalid condition attachment")
            if raw != normalized:
                reviews.append("condition_normalization")
            if condition.get("numeric_value") is not None:
                _text(condition["numeric_value"])  # exact decimal text, never float coercion
                reviews.append("numeric_normalization")
            if condition.get("unit") is not None:
                _text(condition["unit"])
                if not any(condition["unit"] in text for text in snippets):
                    raise InputBoundaryError("unit is not source backed")
            if condition["relation_to_block"] == "uncertain":
                uncertain += 1
            else:
                explicit += 1
                block_active = True
        active += int(block_active)
    for item in profile["context_items"]:
        _fields(item, {"raw_text", "action", "reason", "source_spans"}, {"replacement"})
        _text(item["raw_text"])
        _text(item["reason"])
        snippets = _spans(item["source_spans"], source)
        if not any(item["raw_text"] in text for text in snippets):
            raise InputBoundaryError("context is not source backed")
        if item["action"] not in ("retain", "proposed_abstraction", "unresolved"):
            raise InputBoundaryError("invalid context action")
        replacement = item.get("replacement")
        if replacement is not None:
            _text(replacement)
        if item["action"] == "proposed_abstraction":
            _text(replacement)
            reviews.append("context_abstraction")
        elif replacement is not None:
            raise InputBoundaryError("replacement without proposed abstraction")
    for item in profile["unknowns"]:
        _fields(item, {"description", "reason"}, {"source_spans"})
        _text(item["description"])
        if item["reason"] not in ("ambiguity", "insufficient_text", "unsupported_normalization", "other"):
            raise InputBoundaryError("invalid uncertainty reason")
        _spans(item.get("source_spans", []), source, required=False)
    return {"status": "STRUCTURE_AND_SPANS_PASS", "blocks": len(profile["blocks"]),
            "explicit_conditions": explicit, "uncertain_conditions": uncertain,
            "conjunction_blocks": active, "review_flags": sorted(set(reviews)),
            "anchor_fallback_required": status == "failed" or not profile["blocks"],
            "semantic_status": "unknown", "fidelity_review": "REQUIRED"}
