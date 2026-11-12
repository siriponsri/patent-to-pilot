from patent_to_pilot.research.sg_relations_v3 import extract_family_v3, LEMMAS, VERSION


def keys(text, field='abstract'):
    row = {'id': 'fam-1', 'title': '', 'abstract': '', 'claims': ''}; row[field] = text
    return [r['alias_descriptor'] for r in extract_family_v3(row)['records']]


def test_four_patterns_and_operand_heads():
    assert len(LEMMAS) == 120 and VERSION == 'sg-action-operand-v3'
    assert keys('A valve configured to reduce flow.') == ['reduce|flow']
    assert keys('A method for producing fermented yogurts.') == ['produce|yogurt']
    assert keys('The controller stops delivery when pressure rises.') == ['stop|delivery']
    assert keys('The unit is used to measure the blood pressures of a patient.') == ['measure|pressure']
    assert keys('A sensor capable of detecting each gas leak.') == ['detect|leak']


def test_no_match_without_operand_and_record_format():
    assert keys('It is designed to rotate.') == []
    row = {'id': 'fam-2', 'title': 'Pump', 'abstract': 'A pump to transfer liquid.', 'claims': 'The pump heats water.'}
    out = extract_family_v3(row)
    assert [r['alias_descriptor'] for r in out['records']] == ['transfer|liquid', 'heat|water']
    r = out['records'][0]
    assert r['semantic_status'] == 'UNSCREENED_NO_EDGES_ALLOWED'
    assert row[r['source_field']][r['action_span']['start']:r['action_span']['end']] == r['action_span']['text'] == 'transfer'
