import copy
import hashlib

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_profile import validate_profile

SOURCE = "Reduce reverse flow of liquid at low pressure without external electrical power."


def span(text, source=SOURCE):
    start = source.index(text)
    return {"field": "allowed_query", "start": start, "end": start + len(text), "text": text}


def fixture(source=SOURCE):
    return {"profile_version": "sacr-profile-v0", "query_id": "q1", "input_kind": "MTM_P",
            "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
            "extraction_status": "valid", "failure_reasons": [], "context_items": [], "unknowns": [],
            "blocks": [{"block_id": "b1", "relation_text": "Reduce reverse flow of liquid",
                        "source_spans": [span(source, source)], "action": "Reduce", "operand": "liquid",
                        "attached_conditions": [
                            {"condition_id": "c1", "raw_text": "low pressure", "normalized_text": "low pressure",
                             "kind": "qualitative", "relation_to_block": "explicit",
                             "source_spans": [span("low pressure", source)]},
                            {"condition_id": "c2", "raw_text": "without external electrical power",
                             "normalized_text": "without external electrical power", "kind": "polarity",
                             "relation_to_block": "explicit", "source_spans": [span("without external electrical power", source)]}]}]}


def check(profile, source=SOURCE):
    return validate_profile(profile, source=source, query_id="q1", input_kind="MTM_P")


def test_exact_spans_are_not_semantic_support():
    result = check(fixture())
    assert result["explicit_conditions"] == 2
    assert result["conjunction_blocks"] == 1
    assert result["semantic_status"] == "unknown"
    assert result["fidelity_review"] == "REQUIRED"
    assert not result["anchor_fallback_required"]


@pytest.mark.parametrize("bad", ["offset", "bool_offset", "slice", "field", "duplicate_span", "source_hash",
                                 "query_id", "extra_label", "role", "condition", "unit", "duplicate_id", "cap"])
def test_invalid_source_or_schema_refused(bad):
    p = fixture()
    b, c = p["blocks"][0], p["blocks"][0]["attached_conditions"][0]
    if bad == "offset":
        c["source_spans"][0]["end"] += 1
    elif bad == "bool_offset":
        b["source_spans"][0]["start"] = False
    elif bad == "slice":
        c["source_spans"][0]["text"] = "different"
    elif bad == "field":
        c["source_spans"][0]["field"] = "hidden_abstract"
    elif bad == "duplicate_span":
        c["source_spans"] *= 2
    elif bad == "source_hash":
        p["source_sha256"] = "0" * 64
    elif bad == "query_id":
        p["query_id"] = "other"
    elif bad == "extra_label":
        p["targets"] = ["hidden"]
    elif bad == "role":
        b["action"] = "install valve"
    elif bad == "condition":
        c["raw_text"] = "5 kPa"
    elif bad == "unit":
        c["unit"] = "kPa"
    elif bad == "duplicate_id":
        c["condition_id"] = "b1"
    else:
        p["blocks"] *= 9
    with pytest.raises(InputBoundaryError):
        check(p)


def test_invented_normalization_is_review_flag_not_auto_acceptance():
    p = fixture()
    p["blocks"][0]["relation_text"] = "Use a check valve"
    c = p["blocks"][0]["attached_conditions"][0]
    c["normalized_text"] = "5 kPa"
    c["numeric_value"] = "5"
    result = check(p)
    assert result["review_flags"] == ["condition_normalization", "numeric_normalization", "relation_normalization"]
    assert result["fidelity_review"] == "REQUIRED"
    assert result["semantic_status"] == "unknown"


def test_uncertain_attachment_not_counted_for_conjunction():
    p = fixture()
    for c in p["blocks"][0]["attached_conditions"]:
        c["relation_to_block"] = "uncertain"
    result = check(p)
    assert result["uncertain_conditions"] == 2
    assert result["conjunction_blocks"] == 0


def test_unicode_codepoint_offsets_and_no_normalization():
    source = "🧪 ลดแรงดัน: " + SOURCE
    p = fixture(source)
    assert check(p, source)["status"] == "STRUCTURE_AND_SPANS_PASS"
    p["blocks"][0]["attached_conditions"][0]["source_spans"][0]["start"] += 1
    with pytest.raises(InputBoundaryError):
        check(p, source)


def test_failed_or_empty_profile_keeps_anchor():
    p = fixture()
    p["blocks"] = []
    assert check(p)["anchor_fallback_required"]
    p["extraction_status"] = "failed"
    with pytest.raises(InputBoundaryError):
        check(p)
    p["failure_reasons"] = ["generation failed"]
    assert check(p)["anchor_fallback_required"]


def test_context_replacement_and_block_order():
    p = fixture()
    p["context_items"] = [{"raw_text": "liquid", "action": "proposed_abstraction", "replacement": "fluid",
                           "reason": "candidate normalization", "source_spans": [span("liquid")]}]
    assert check(p)["review_flags"] == ["context_abstraction"]
    later = copy.deepcopy(p["blocks"][0])
    later.update(block_id="b2", relation_text="low pressure", action=None, operand=None,
                 source_spans=[span("low pressure")], attached_conditions=[])
    p["blocks"].insert(0, later)
    with pytest.raises(InputBoundaryError, match="source order"):
        check(p)
