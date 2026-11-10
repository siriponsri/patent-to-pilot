import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_views import compact_view, collect_screened_views, parse_view_response, screen_view
from test_sacr_profile import SOURCE, fixture


def test_compact_is_source_ordered_and_uncertain_attachment_abstains():
    p = fixture()
    p["blocks"][0]["attached_conditions"].reverse()
    result = compact_view(p, source=SOURCE, query_id="q1", input_kind="MTM_P")
    assert result["text"] == "Reduce reverse flow of liquid ; low pressure ; without external electrical power"
    assert result["semantic_status"] == "unknown"
    p["blocks"][0]["attached_conditions"][0]["relation_to_block"] = "uncertain"
    assert compact_view(p, source=SOURCE, query_id="q1", input_kind="MTM_P")["status"] == "REVIEW_REQUIRED"


def test_failed_empty_or_normalized_profile_does_not_silently_serialize():
    p = fixture()
    p["blocks"] = []
    assert compact_view(p, source=SOURCE, query_id="q1", input_kind="MTM_P")["status"] == "ANCHOR_FALLBACK"
    p = fixture()
    p["blocks"][0]["relation_text"] = "Use a valve"
    assert compact_view(p, source=SOURCE, query_id="q1", input_kind="MTM_P")["text"] is None


@pytest.mark.parametrize("raw,kind", [(b'{"views": ["a", "b", "c"]}', "generic"),
    (b'{"views": [""]}', "generic"), (b'{"selective_abstract": "a", "targets": []}', "selective"),
    (b'{"views": [], "views": []}', "generic"), (b'```json\n{}\n```', "generic"),
    (b'{"views": ["partial"', "generic")])
def test_invalid_complete_response_rejected(raw, kind):
    with pytest.raises(InputBoundaryError):
        parse_view_response(raw, kind=kind, maximum_bytes=1000)


def test_null_and_partial_output_count_are_not_retried():
    assert parse_view_response(b'{"selective_abstract": null}', kind="selective", maximum_bytes=100) == []
    assert parse_view_response(b'{"views": ["a"]}', kind="generic", maximum_bytes=100) == ["a"]
    with pytest.raises(InputBoundaryError):
        parse_view_response(b'{"views": []}', kind="generic", maximum_bytes=1)


@pytest.mark.parametrize("proposed,reason", [
    ("Reduce reverse flow of liquid at low pressure with electrical power.", "protected_phrase_lost"),
    (SOURCE + " at 5 kPa", "numeric_literal_inventory_changed"),
    (SOURCE.replace("without", "with"), "polarity_inventory_changed")])
def test_specific_invariant_losses_are_rejected(proposed, reason):
    result = screen_view(SOURCE, proposed, protected_phrases=["without external electrical power"], maximum_characters=1000)
    assert result["status"] == "REJECTED" and reason in result["rejection_reasons"]


def test_new_mechanism_and_ordinary_synonym_both_need_review():
    for proposed in (SOURCE + " using a valve", SOURCE.replace("Reduce", "Decrease")):
        result = screen_view(SOURCE, proposed, protected_phrases=["low pressure"], maximum_characters=1000)
        assert result["status"] == "REVIEW_REQUIRED"
        assert result["semantic_status"] == "unknown"


def test_anchor_preserved_duplicate_logged_and_no_forced_replacement():
    out = collect_screened_views(SOURCE, [SOURCE, SOURCE + " with a valve"],
                                 protected_phrases=["low pressure"], maximum_characters=1000)
    assert out["views"] == [SOURCE]
    assert out["proposals"][0]["duplicate"]
    assert out["proposals"][1]["status"] == "REVIEW_REQUIRED"
    assert out["method_status"] == "SCREENING_COMPONENT_ONLY_NOT_FULL_SACR"


def test_known_limitation_existing_words_can_reverse_roles():
    # Preserve this falsification fixture: lexical pass cannot establish meaning.
    result = screen_view("A pushes B", "B pushes A", protected_phrases=[], maximum_characters=100)
    assert result["status"] == "LEXICAL_SCREEN_PASS"
    assert result["semantic_status"] == "unknown"
