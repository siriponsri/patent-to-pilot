import copy
import hashlib
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_generation import GenerationLimits, validate_generation
from patent_to_pilot.research.sacr_quote_profile import align_quote_profile, resolve_quote
from test_sacr_profile import SOURCE, fixture
from test_sacr_prompts import build


def proposal():
    p = fixture()
    p["profile_version"] = "sacr-profile-quotes-v1"
    for block in p["blocks"]:
        for span in block["source_spans"]:
            del span["start"], span["end"]
        for condition in block["attached_conditions"]:
            for span in condition["source_spans"]:
                del span["start"], span["end"]
    return p


def test_exact_alignment_is_deterministic_and_does_not_mutate_proposal():
    p = proposal()
    original = copy.deepcopy(p)
    result = align_quote_profile(p, source=SOURCE, query_id="q1", input_kind="MTM_P")
    assert p == original
    assert result["profile"] == fixture()
    assert result["alignment"]["resolved_references"] == 3
    assert result["alignment"]["semantic_status"] == "unknown"
    assert result == align_quote_profile(p, source=SOURCE, query_id="q1", input_kind="MTM_P")


@pytest.mark.parametrize("source,text", [("aaa", "aa"), ("low pressure then low pressure", "low pressure"),
                                        ("low pressure", "Low pressure"), ("a  b", "a b"), ("abc", "missing")])
def test_absent_ambiguous_and_normalized_quotes_refused(source, text):
    with pytest.raises(InputBoundaryError, match="absent or ambiguous"):
        resolve_quote({"field": "allowed_query", "text": text}, source)


def test_unique_unicode_context_and_literal_punctuation():
    result = resolve_quote({"field": "allowed_query", "text": "แรงดันต่ำ (5 kPa)"}, "🧪 แรงดันต่ำ (5 kPa)")
    assert result["start"] == 2
    assert result["end"] == len("🧪 แรงดันต่ำ (5 kPa)")


def test_v0_cannot_be_repaired_or_relabelled_with_old_offsets():
    old = fixture()
    old["blocks"][0]["source_spans"][0]["end"] -= 1
    with pytest.raises(InputBoundaryError, match="explicitly versioned"):
        align_quote_profile(old, source=SOURCE, query_id="q1", input_kind="MTM_P")
    old["profile_version"] = "sacr-profile-quotes-v1"
    with pytest.raises(InputBoundaryError):
        align_quote_profile(old, source=SOURCE, query_id="q1", input_kind="MTM_P")


def test_unknown_fields_and_wrong_source_identity_still_fail():
    for change in ("labels", "hash", "quote"):
        p = proposal()
        if change == "labels":
            p["targets"] = ["hidden"]
        elif change == "hash":
            p["source_sha256"] = "0" * 64
        else:
            p["blocks"][0]["source_spans"][0]["text"] = "invented quote"
        before = copy.deepcopy(p)
        with pytest.raises(InputBoundaryError):
            align_quote_profile(p, source=SOURCE, query_id="q1", input_kind="MTM_P")
        assert p == before


def test_generation_dispatch_and_new_prompt_identity():
    messages = build("profile_quotes")
    identity = json.loads(messages["messages"][1]["content"])["identity"]
    assert identity["profile_version"] == "sacr-profile-quotes-v1"
    assert messages["prompt_sha256"] != build("profile")["prompt_sha256"]
    text = json.dumps(proposal())
    record = {"status": "EOS_COMPLETE", "text": text, "response_sha256": hashlib.sha256(text.encode()).hexdigest()}
    result = validate_generation(record, kind="profile_quotes", source=SOURCE, query_id="q1",
                                 input_kind="MTM_P", limits=GenerationLimits())
    assert result["status"] == "QUOTE_PROFILE_STRUCTURALLY_VALID"
    assert result["profile"]["profile_version"] == "sacr-profile-v0"
    record["status"] = "OUTPUT_LIMIT"
    assert validate_generation(record, kind="profile_quotes", source=SOURCE, query_id="q1",
                               input_kind="MTM_P", limits=GenerationLimits())["anchor_fallback_required"]
