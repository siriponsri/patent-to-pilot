"""Synthetic tests for BridgeRet query serialisation (authored text only)."""
from patent_to_pilot.research import bridgeret_query as q

W = lambda s: len(s.split())          # whitespace tokenizer double


def C(n, t, d=''):
    return q.ClaimRow(n, t, d)


def test_first_independent_skips_cancelled_and_dependent():
    claims = [C(1, '1 . (canceled)'), C(2, '2 . The pump of claim 9 wherein x.', 'claim 9'),
              C(3, '3 . A pump comprising a valve.'), C(4, '4. A method of making a pump.')]
    assert q.first_independent_claim(claims) == ('A pump comprising a valve.', 'first_independent')


def test_dependency_detected_from_text_when_field_empty():
    claims = [C(1, '1. The device according to claim 5, further comprising a lid.'),
              C(2, '2. A device comprising a housing.')]
    assert q.first_independent_claim(claims)[0] == 'A device comprising a housing.'


def test_fallback_and_no_claims():
    assert q.first_independent_claim([C(2, '2. The x of claim 1.', 'claim 1')]) == ('The x of claim 1.', 'claim_fallback_claim1')
    assert q.first_independent_claim([C(1, '1. (Cancelled)')]) == (None, 'no_claims')


def test_order_and_separators():
    s = q.serialise('Pump', 'An abstract.', [C(1, '1. A pump.')], W)
    assert s.text == 'Pump\nAn abstract.\nA pump.' and s.variant == [] and s.truncated == {}


def test_no_abstract_variant():
    s = q.serialise('Pump', '', [C(1, '1. A pump.')], W)
    assert s.text == 'Pump\nA pump.' and s.variant == ['no_abstract']


def test_truncates_claim_tail_first_never_title():
    title = 'T ' * 5
    s = q.serialise(title, 'a ' * 10, [C(1, '1. ' + 'c ' * 50)], W, cap=30)
    t, a, c = s.text.split('\n')
    assert t == title.strip() and a == ('a ' * 10).strip()
    assert s.tokens <= 30 and 'claim' in s.truncated and 'abstract' not in s.truncated


def test_abstract_cut_when_claim_exhausted():
    s = q.serialise('T', 'a ' * 40, [C(1, '1. ' + 'c ' * 40)], W, cap=20)
    assert s.tokens <= 20 and s.truncated['claim'] == 40 and s.truncated['abstract'] > 0
    assert s.text.startswith('T\n')


def test_title_over_cap_reported_not_cut():
    s = q.serialise('t ' * 10, 'a b', [C(1, '1. c d')], W, cap=5)
    assert s.text.split('\n')[0] == ('t ' * 10).strip() and 'title_over_cap' in s.variant


def test_claims_by_document_groups_patentsview_rows():
    rows = [{'pgpub_id': 'P1', 'claim_number': '00002', 'claim_text': '2 . A b.', 'dependent': ''},
            {'pgpub_id': 'P1', 'claim_number': '00001', 'claim_text': '1 . (canceled)', 'dependent': ''}]
    g = q.claims_by_document(rows, 'pgpub_id')
    assert q.first_independent_claim(g['P1']) == ('A b.', 'first_independent')
