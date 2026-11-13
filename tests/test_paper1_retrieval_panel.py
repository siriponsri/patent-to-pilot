import pytest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.paper1_controls import shuffled_query
from patent_to_pilot.research.paper1_retrieval_panel import merge_sources, encode_plan, anchor_check, assemble

Q = [{'id': 'a', 'text': 'alpha beta gamma'}, {'id': 'b', 'text': 'delta epsilon'}, {'id': 'c', 'text': 'zeta eta theta'}]
USE, FB = {'action': 'USE_REWRITE'}, {'action': 'ORIGINAL_QUERY_FALLBACK'}


def test_merge_batches_and_plan():
    decisions, texts = merge_sources(Q, [(Q[:2], {'a': USE, 'b': FB}, {'a': 'A rewrite'}), (Q[2:], {'c': USE}, {'c': 'C rewrite'})], 'rewrite')
    assert decisions == {'a': 'USE_REWRITE', 'b': 'ORIGINAL_QUERY_FALLBACK', 'c': 'USE_REWRITE'} and set(texts) == {'a', 'c'}
    rows = encode_plan(Q, {'FA': (decisions, texts)}, 'P: ')
    assert [r[:2] for r in rows] == [('anchor', 'a'), ('anchor', 'b'), ('anchor', 'c'), ('shuffle', 'a'), ('shuffle', 'b'),
                                     ('shuffle', 'c'), ('FA', 'a'), ('FA', 'c')]
    assert rows[0][2] == 'P: alpha beta gamma' and rows[6][2] == 'P: A rewrite'
    assert rows[3][2] == 'P: ' + shuffled_query('a', 'alpha beta gamma')
    assert sorted(rows[3][2][3:].split()) == ['alpha', 'beta', 'gamma']


@pytest.mark.parametrize('sources', [
    [(Q[:2], {'a': USE, 'b': FB}, {'a': 'x'})],                                    # c not covered
    [(Q, {'a': USE, 'b': FB, 'c': {'action': 'HOLD'}}, {'a': 'x'})],               # unresolved
    [(Q, {'a': USE, 'b': FB, 'c': USE}, {'a': 'x', 'c': ' '})],                    # blank used text
    [(Q, {'a': USE, 'b': FB, 'c': FB}, {'a': 'x'}), (Q[:1], {'a': USE}, {'a': 'x'})],  # query in two jobs
    [([dict(Q[0], text='changed')] + Q[1:], {'a': FB, 'b': FB, 'c': FB}, {})],     # different source text
])
def test_merge_rejects(sources):
    with pytest.raises(InputBoundaryError):
        merge_sources(Q, sources, 'rewrite')


def test_sacr_kind_and_assemble():
    decisions, texts = merge_sources(Q, [(Q, {'a': {'action': 'USE_SCREENED_CANDIDATE'}, 'b': FB, 'c': FB}, {'a': 'cand'})], 'sacr')
    ref = {i: {'families': [i + '0']} for i in 'abc'}
    panel, counts = assemble(Q, texts, {'a': {'families': ['z']}}, ref)
    assert counts == {'used': 1, 'fallback': 2} and panel['a'] == {'families': ['z']} and panel['b'] == ref['b']
    assert anchor_check(ref, ref)['reference'] == 'B0_PINNED'
    assert anchor_check(ref, dict(ref, a={'families': []}))['reference'] == 'REENCODED_ANCHORS'
