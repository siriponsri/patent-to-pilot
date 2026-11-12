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


def test_v3_evaluation_builds_postings_and_applies_frozen_gate():
    import json
    from patent_to_pilot.research.graph_extractor_v3_census import evaluate, GATE
    corpus = [json.dumps({'id': 'F%d' % i, 'title': '', 'abstract': 'A pump configured to reduce flow.',
                          'claims': 'The valve stops delivery.'}) for i in range(3)]
    queries = [{'id': 'q%02d' % i, 'text': 'A device to reduce flow.' if i % 2 else 'Plain text.'} for i in range(30)]
    result, postings = evaluate(corpus, queries)
    assert result['corpus']['families'] == 3 and result['corpus']['shared_keys'] == 2
    assert result['all']['with_structure'] == 15 and result['query_share_with_usable_key'] == 0.5
    assert result['gate_results']['G1'] and not result['gate_results']['G3'] and result['gate_status'] == 'FAIL'
    assert GATE['G3_min_shared_keys'] == 1000
