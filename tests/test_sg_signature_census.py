import pytest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sg_signature_census import SignatureCensus, posting_join, bipartite_one_hop


def record(family, key, rid):
    return {'family_id': family, 'alias_key': key, 'relation_id': rid}


def test_duplicate_occurrences_do_not_inflate_family_pairs():
    c = SignatureCensus(hub_threshold=2)
    c.add_family('A', [record('A', 'k', 'r1'), record('A', 'k', 'r2'), record('A', 'j', 'r3')])
    c.add_family('B', [record('B', 'k', 'r4'), record('B', 'j', 'r5')])
    c.add_family('C', [record('C', 'k', 'r6')])
    c.add_family('D', [])
    s = c.summary()
    assert s['cross_family_pair_key_incidences'] == 4  # AB twice, AC and BC
    assert s['family_frequency_histogram'] == {2: 1, 3: 1}
    assert s['hub_keys'] == 1 and s['max_records_per_key'] == 4
    assert s['families_seen'] == 4 and s['accepted_edges'] == 0


def test_failed_family_is_atomic_and_caps_are_hard():
    c = SignatureCensus(max_families=1, max_records=1)
    before = c.summary()
    with pytest.raises(InputBoundaryError):
        c.add_family('A', [record('B', 'k', 'r')])
    assert c.summary() == before
    c.add_family('A', [record('A', 'k', 'r')])
    for family in ('A', 'B'):
        with pytest.raises(InputBoundaryError): c.add_family(family, [])


@pytest.mark.parametrize('seeds', [[], ['A'], ['B'], ['A', 'D'], ['missing']])
def test_single_key_graph_equals_posting_join(seeds):
    p = {'k': {'A', 'B'}, 'j': {'B', 'C'}, 'isolated': {'D'}}
    assert bipartite_one_hop(p, seeds) == posting_join(p, seeds)
    if seeds == ['A']:
        assert posting_join(p, seeds) == {'B'}  # C requires a separate second hop


def test_empty_census_and_no_pair_expansion_for_hub():
    c = SignatureCensus(max_families=200, max_records=200, hub_threshold=100)
    assert c.summary()['cross_family_pair_key_incidences'] == 0
    for i in range(200): c.add_family('f'+str(i), [record('f'+str(i), 'hub', 'r'+str(i))])
    assert c.summary()['cross_family_pair_key_incidences'] == 19900
    assert c.summary()['hub_keys'] == 1
