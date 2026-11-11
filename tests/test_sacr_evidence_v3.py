import copy
import hashlib
import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_evidence_v3 import VERSION, compile_evidence

SOURCE = 'Valve must not reverse flow at 5 kPa. Valve must not reverse flow at 7 kPa.'


def ref(a, b):
    return {'field': 'allowed_query', 'start_token': a, 'end_token': b}


def proposal():
    return {'version': VERSION, 'query_id': 'synthetic-v3',
        'source_sha256': hashlib.sha256(SOURCE.encode()).hexdigest(), 'blocks': [{
        'id': 'b0', 'evidence': [ref(0, 8), ref(2, 5)],
        'roles': {'negation': [ref(2, 3)], 'quantity': [ref(6, 7)], 'unit': [ref(7, 8)]},
        'conditions': [{'id': 'c0', 'kind': 'numeric', 'attachment': 'explicit',
                        'evidence': [ref(5, 8)], 'attachment_evidence': [ref(0, 8)]},
                       {'id': 'c1', 'kind': 'polarity', 'attachment': 'uncertain',
                        'evidence': [ref(2, 5)], 'attachment_evidence': [ref(0, 8)]}],
        'abstraction': 'Prevent reverse movement under the stated constraints.'}]}


def run(p):
    return compile_evidence(p, source=SOURCE, query_id='synthetic-v3')


def test_literals_overlap_multiple_conditions_and_full_source_preserved():
    p = proposal(); before = copy.deepcopy(p); r = run(p)
    assert p == before
    assert r['retained_source'] == SOURCE
    b = r['blocks'][0]
    assert b['literal_evidence'][1]['text'] == 'not reverse flow'
    assert b['role_evidence']['quantity'][0]['text'] == '5'
    assert b['conditions'][0]['literal_evidence'][0]['text'] == 'at 5 kPa.'
    assert len(b['conditions']) == 2
    assert not r['retrieval_ready'] and not r['automatic_fidelity_pass']


def test_repeated_occurrences_distinct_and_wrong_semantics_not_autoaccepted():
    p = proposal(); p['blocks'][0]['conditions'][0]['evidence'] = [ref(13, 16)]
    r = run(p)
    assert r['blocks'][0]['conditions'][0]['literal_evidence'][0]['text'] == 'at 7 kPa.'
    assert r['semantic_status'] == 'UNKNOWN_REQUIRES_REVIEW'
    assert 'condition_attachment' in r['required_reviews']
    assert not r['retrieval_ready']


@pytest.mark.parametrize('change', ['missing', 'raw', 'identity', 'range', 'bool', 'duplicate', 'role_outside'])
def test_invalid_or_missing_evidence_rejected(change):
    p = proposal(); b = p['blocks'][0]
    if change == 'missing': del b['conditions']
    if change == 'raw': b['conditions'][0]['raw_text'] = 'invented'
    if change == 'identity': p['source_sha256'] = 'wrong'
    if change == 'range': b['evidence'][0] = ref(0, 999)
    if change == 'bool': b['evidence'][0] = ref(False, 9)
    if change == 'duplicate': b['evidence'] = [ref(0, 8), ref(0, 8)]
    if change == 'role_outside': b['roles']['quantity'] = [ref(14, 15)]
    with pytest.raises(InputBoundaryError): run(p)


def test_abstraction_cannot_replace_literal_evidence_or_omit_original():
    p = proposal(); p['blocks'][0]['abstraction'] = 'reverse flow at 100 psi'
    r = run(p)
    assert r['retained_source'] == SOURCE
    assert '100' not in r['blocks'][0]['literal_evidence'][0]['text']
    assert not r['automatic_fidelity_pass']
