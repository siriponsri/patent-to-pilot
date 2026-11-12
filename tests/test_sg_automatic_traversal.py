from patent_to_pilot.research.sg_automatic_traversal import rank_graph_arms, _tie
import pytest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

POSTINGS = {'q1': ['A', 'B'], 'q2': ['B', 'C'], 'bridge': ['B', 'D'], 'hub': [f'H{i}' for i in range(5)]}


def test_s_counts_matched_keys_and_g_adds_hop2_only_through_bridges():
    r = rank_graph_arms(['q1', 'q2'], POSTINGS, max_key_degree=4)
    assert r['S']['scores'] == {'A': 1, 'B': 2, 'C': 1}
    assert r['S']['ranking'][0] == 'B'
    assert r['G']['scores']['D'] == 0.5 and r['G']['hop2_families'] == ['D']
    assert all(r['G']['scores'][f] == r['S']['scores'][f] for f in 'AC')


def test_ties_use_salted_hash_not_alphabet():
    r = rank_graph_arms(['q1'], {'q1': ['A', 'B', 'C', 'D']})
    assert r['S']['ranking'] == sorted('ABCD', key=_tie)


def test_s_deep_spends_g_work_on_skipped_hub_without_traversal():
    r = rank_graph_arms(['q1', 'q2', 'hub'], POSTINGS, max_key_degree=4)
    assert r['skipped_hub_keys_in_S_and_G'] == ['hub'] and 'D' not in r['S_deep']['scores']
    assert r['S_deep']['edges'] == min(r['G']['work'], 4 + 5) and r['S_deep']['work_shortfall'] == max(0, r['G']['work'] - 9)
    assert any(f.startswith('H') for f in r['S_deep']['scores'])


def test_budget_truncation_is_reported_and_inputs_validated():
    r = rank_graph_arms(['q1', 'q2'], POSTINGS, edge_budget=3)
    assert r['S']['truncated'] and r['S']['edges'] == 3
    with pytest.raises(InputBoundaryError):
        rank_graph_arms(['q1'], {'q1': ['A', 'A']})
