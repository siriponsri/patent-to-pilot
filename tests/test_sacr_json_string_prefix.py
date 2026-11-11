import pytest
from patent_to_pilot.research.sacr_json_string_prefix import possible_string_transition


@pytest.mark.parametrize('text',['a",','a\\','a\\u','a\\u00','a\\u001','a\\u001F','a\\"b','ไทย 🧪','a"\n'])
def test_valid_or_potentially_valid_prefix_is_not_removed(text):
    assert possible_string_transition(text)


@pytest.mark.parametrize('text',['a\n','a\r','a\t','a\\q','a\\uZ','a\\u00Z','a\n"'])
def test_impossible_before_first_string_close_rejected(text):
    assert not possible_string_transition(text)


def test_v3_trie_preserves_partial_unicode_and_fused_boundary():
    from patent_to_pilot.research.sacr_boundary_callback_v3 import boundary_token_records
    values=['a\\u','a\\u0','a\\u001','a\\uZ','a\n','a",','a"\n','a\\q']
    assert set(dict(boundary_token_records([(i,s,False) for i,s in enumerate(values)])))=={0,1,2,5,6}
