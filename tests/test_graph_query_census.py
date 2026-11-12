from patent_to_pilot.research.graph_query_census import census, pilot_ids
from patent_to_pilot.research.sg_relations_v2 import extract_family_v2


def key(text):
    rows = extract_family_v2({'id': 'x', 'title': '', 'abstract': text, 'claims': ''})['records']
    return sorted({r['alias_key'] for r in rows})


def test_census_counts_coverage_without_qrels_and_freezes_pilot():
    texts = ['A pump configured to reduce pressure.', 'A valve configured to control flow.', 'Plain background text.']
    k1, k2 = key(texts[0]), key(texts[1])
    assert k1 and k2 and not key(texts[2])
    queries = [{'id': 'q%02d' % i, 'text': texts[i % 3]} for i in range(30)]
    postings = {k1[0]: {'F1': 'r1', 'F2': 'r2'}, k2[0]: {'F2': 'r3'}, 'other': {'F2': 'r4', 'F9': 'r5'}}
    out = census(queries, postings)
    assert out['all']['queries'] == 30 and out['all']['zero_keys'] == 10 and out['all']['with_structure'] == 20
    assert len(out['pilot_ids']) == 20 and out['pilot_ids'] == sorted(pilot_ids([q['id'] for q in queries]))
    assert out['qrels_used'] is False and out['scores_computed'] is False
    assert out['pilot_screening_scope']['one_hop_bridge_keys'] >= 1   # 'other' reached through F2
