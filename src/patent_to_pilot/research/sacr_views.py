"""Deterministic compact text and conservative proposal screening, not entailment.

REVIEW_REQUIRED proposals are retained as evidence but not returned as usable
views. No retrieval outcome may be used to repair or approve a proposal.
"""
from collections import Counter
import hashlib
import re

from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json, exact_fields
from patent_to_pilot.research.sacr_profile import validate_profile

NUMBERS = re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)*(?:%|\b)")
WORDS = re.compile(r"[^\W\d_]+", re.UNICODE)
POLARITY = re.compile(r"\b(?:no|not|without|except|never|neither|nor)\b", re.IGNORECASE)


def parse_view_response(raw: bytes, *, kind: str, maximum_bytes: int) -> list[str]:
    if type(maximum_bytes) is not int or maximum_bytes <= 0 or len(raw) > maximum_bytes:
        raise InputBoundaryError("generated response exceeds declared byte cap")
    value = decode_json(raw)
    if kind == "selective":
        exact_fields(value, {"selective_abstract"})
        views = [] if value["selective_abstract"] is None else [value["selective_abstract"]]
    elif kind == "generic":
        exact_fields(value, {"views"})
        views = value["views"]
        if type(views) is not list or len(views) > 2:
            raise InputBoundaryError("generic view cap exceeded")
    else:
        raise InputBoundaryError("unknown generation response kind")
    if any(type(text) is not str or not text.strip() for text in views):
        raise InputBoundaryError("invalid generated view text")
    return views


def compact_view(profile, *, source: str, query_id: str, input_kind: str) -> dict:
    report = validate_profile(profile, source=source, query_id=query_id, input_kind=input_kind)
    if report["anchor_fallback_required"]:
        return {"status": "ANCHOR_FALLBACK", "text": None, "semantic_status": "unknown"}
    # Never serialize unreviewed normalization or silently drop uncertain conditions.
    if report["review_flags"] or report["uncertain_conditions"] or profile["unknowns"]:
        return {"status": "REVIEW_REQUIRED", "text": None, "semantic_status": "unknown"}
    clauses = []
    for block in profile["blocks"]:
        conditions = sorted(block["attached_conditions"], key=lambda c: min(s["start"] for s in c["source_spans"]))
        clauses.append(" ; ".join([block["relation_text"]] + [c["raw_text"] for c in conditions]))
    return {"status": "PROPOSED_COMPACT", "text": "\n".join(clauses), "semantic_status": "unknown"}


def screen_view(source: str, proposed: str, *, protected_phrases: list[str], maximum_characters: int) -> dict:
    """Conservative lexical checks. The protected list must come from validation.

    Numeric/polarity inventories and literal protected phrases catch specific
    defects, not role reversal or semantic inventions using existing vocabulary.
    New words require review; this rule must not be sold as complete SACR.
    """
    if (type(source) is not str or not source.strip() or type(proposed) is not str or not proposed.strip() or
            type(maximum_characters) is not int or maximum_characters <= 0 or
            type(protected_phrases) is not list):
        raise InputBoundaryError("invalid view screening input")
    if any(type(text) is not str or not text or text not in source for text in protected_phrases):
        raise InputBoundaryError("protected phrase lacks source backing")
    reasons, review = [], []
    if len(proposed) > maximum_characters:
        reasons.append("view_length_exceeded")
    if any(text not in proposed for text in protected_phrases):
        reasons.append("protected_phrase_lost")
    if Counter(NUMBERS.findall(source)) != Counter(NUMBERS.findall(proposed)):
        reasons.append("numeric_literal_inventory_changed")
    if Counter(m.lower() for m in POLARITY.findall(source)) != Counter(m.lower() for m in POLARITY.findall(proposed)):
        reasons.append("polarity_inventory_changed")
    novel = set(WORDS.findall(proposed.casefold())) - set(WORDS.findall(source.casefold()))
    if novel:
        review.append("new_vocabulary")
    return {"status": "REJECTED" if reasons else "REVIEW_REQUIRED" if review else "LEXICAL_SCREEN_PASS",
            "rejection_reasons": reasons, "review_flags": review, "new_vocabulary_count": len(novel),
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "view_sha256": hashlib.sha256(proposed.encode()).hexdigest(), "semantic_status": "unknown"}


def collect_screened_views(source: str, proposals: list[str], *, protected_phrases: list[str], maximum_characters: int) -> dict:
    """Keep immutable anchor and at most two passing proposals; retain outcomes."""
    if type(source) is not str or not source.strip() or type(proposals) is not list or len(proposals) > 2:
        raise InputBoundaryError("invalid anchor or proposal cap")
    views, records, seen = [source], [], {source}
    for text in proposals:
        screen = screen_view(source, text, protected_phrases=protected_phrases, maximum_characters=maximum_characters)
        status = screen["status"]
        duplicate = text in seen
        accepted = status == "LEXICAL_SCREEN_PASS" and not duplicate
        if accepted:
            views.append(text)
            seen.add(text)
        records.append({**screen, "duplicate": duplicate, "included": accepted})
    return {"views": views, "proposals": records, "semantic_status": "unknown",
            "method_status": "SCREENING_COMPONENT_ONLY_NOT_FULL_SACR"}
