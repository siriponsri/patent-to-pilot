import pytest
from patent_to_pilot.research.sg_bounded_traversal import rank_structured_and_graph
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_second_hop_adds_family_outside_direct_pool():
    result = rank_structured_and_graph(['pump'], {'pump': ['a'], 'filter': ['a', 'b']}, ['a', 'b'])
    assert result['S']['ranking'] == ['a']
    assert result['G']['ranking'] == ['a', 'b']
    assert result['G']['path_summary']['b']['hops'] == 2
    assert result['G']['scores']['b'] == .5


def test_one_hop_reproduces_direct_control():
    result = rank_structured_and_graph(['x'], {'x': ['a'], 'y': ['a', 'b']}, ['a', 'b'], max_hops=1)
    assert result['S'] == result['G']


def test_cycles_and_insertion_order_do_not_change_result():
    first = rank_structured_and_graph(['x'], {'x': ['a', 'b'], 'y': ['a', 'b']}, ['a', 'b'], max_hops=10)
    second = rank_structured_and_graph(['x'], {'y': ['b', 'a'], 'x': ['b', 'a']}, ['a', 'b'], max_hops=10)
    assert first == second
    assert first['G']['examined_membership_edges'] == 4


def test_hard_budget_and_hub_exclusion():
    result = rank_structured_and_graph(['x'], {'x': ['a', 'b']}, ['a', 'b'], edge_budget=1)
    assert result['G']['examined_membership_edges'] == 1
    assert result['G']['ranking'] == ['a']
    hub = rank_structured_and_graph(['x'], {'x': ['a', 'b']}, ['a', 'b'], max_key_degree=1)
    assert hub['G']['ranking'] == [] and hub['G']['skipped_hub_keys'] == ['x']


def test_foreign_family_is_integrity_failure():
    with pytest.raises(InputBoundaryError):
        rank_structured_and_graph(['x'], {'x': ['foreign']}, ['a'])


def test_reverse_fanout_is_bounded_and_path_is_reconstructible():
    postings = {'x': ['a'], **{f'z{i}': ['a', 'b'] for i in range(100)}}
    result = rank_structured_and_graph(['x'], postings, ['a', 'b'],
                                       reverse_edge_budget=2, frontier_budget=2)
    assert result['G']['examined_reverse_edges'] <= 2
    assert result['G']['path_summary']['b']['path'] == [
        ('key', 'x'), ('family', 'a'), ('key', 'z0'), ('family', 'b')]


def test_exact_budget_completion_is_not_truncation():
    result = rank_structured_and_graph(['x'], {'x': ['a']}, ['a'], max_hops=1, edge_budget=1)
    assert result['G']['budget_reached']
    assert not result['G']['forward_truncated']


@pytest.mark.parametrize('keys,postings,universe', [
    (['x', 1], {'x': ['a']}, ['a']), ([''], {'x': ['a']}, ['a']),
    (['x'], {'x': ['a', 1]}, ['a']), (['x'], {'x': ['a']}, ['a', 'a'])])
def test_malformed_ids_are_boundary_errors(keys, postings, universe):
    with pytest.raises(InputBoundaryError):
        rank_structured_and_graph(keys, postings, universe)
