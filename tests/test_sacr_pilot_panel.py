import pytest
from patent_to_pilot.research.sacr_pilot_panel import encode_plan, anchor_check, assemble
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

PILOT = [{'id': 'a', 'text': 'pump'}, {'id': 'b', 'text': 'valve'}]


def test_plan_encodes_all_anchors_and_screened_candidates_with_b0_prefix():
    d = {'a': {'action': 'USE_SCREENED_CANDIDATE'}, 'b': {'action': 'ORIGINAL_QUERY_FALLBACK'}}
    rows = encode_plan(PILOT, d, {'a': 'pump below 5 kPa'}, 'P: ')
    assert rows == [('anchor', 'a', 'P: pump'), ('anchor', 'b', 'P: valve'), ('sacr', 'a', 'P: pump below 5 kPa')]
    with pytest.raises(InputBoundaryError):
        encode_plan(PILOT, dict(d, b={'action': 'HOLD'}), {'a': 'x'}, 'P: ')
    with pytest.raises(InputBoundaryError):
        encode_plan(PILOT, d, {}, 'P: ')


def test_anchor_reference_and_panel_fallback():
    anchors = {'a': {'families': ['1', '2']}, 'b': {'families': ['3']}}
    assert anchor_check(anchors, {'a': {'families': ['1', '2']}, 'b': {'families': ['3']}})['reference'] == 'B0_PINNED'
    assert anchor_check(anchors, {'a': {'families': ['2', '1']}, 'b': {'families': ['3']}})['reference'] == 'REENCODED_ANCHORS'
    d = {'a': {'action': 'USE_SCREENED_CANDIDATE'}, 'b': {'action': 'ORIGINAL_QUERY_FALLBACK'}}
    panel, counts = assemble(PILOT, d, {'a': {'families': ['9']}}, anchors)
    assert panel == {'a': {'families': ['9']}, 'b': {'families': ['3']}} and counts == {'screened': 1, 'fallback': 1}
