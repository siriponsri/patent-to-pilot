from patent_to_pilot.research.sg_relations import extract_family


def row(text):
    return {'id': 'F', 'title': 'device', 'abstract': text, 'claims': ''}


def test_exact_clause_preserves_negation_number_and_no_inferred_roles():
    source = 'A pump is configured to reduce flow at 3.2 kPa without electrical power.'
    out = extract_family(row(source))
    r = out['records'][0]
    assert r['source_span']['text'] == source
    assert r['roles']['action']['text'] == 'reduce flow at 3.2 kPa without electrical power.'
    for span in [r['source_span'], *r['roles'].values()]:
        assert source[span['start']:span['end']] == span['text']
    assert r['operand'] is None and r['effect'] is None
    assert r['semantic_status'] == 'UNSCREENED_NO_EDGES_ALLOWED'


def test_no_cue_abstains_and_repeated_occurrences_are_not_merged():
    assert extract_family(row('A pump reduces flow.'))['empty']
    sentence = 'A pump is configured to reduce flow.'
    records = extract_family(row(sentence + '\n' + sentence))['records']
    assert len(records) == 2
    assert records[0]['relation_id'] != records[1]['relation_id']
    assert records[0]['alias_key'] == records[1]['alias_key']


def test_cap_and_long_sources_count_abstentions_without_repair():
    s = 'A pump is configured to reduce flow.'
    out = extract_family(row('\n'.join([s] * 10)))
    assert len(out['records']) == 8 and out['counts']['cap_omitted'] == 2
    out = extract_family(row('A pump is configured to ' + 'x' * 4000))
    assert out['empty'] and out['counts']['over_length'] == 1


def test_alias_is_exact_and_case_sensitive_no_synonym_inference():
    a = extract_family(row('A pump is configured to reduce flow.'))['records'][0]
    b = extract_family(row('A valve is configured to reduce flow.'))['records'][0]
    c = extract_family(row('A pump is configured to Reduce flow.'))['records'][0]
    assert a['alias_key'] == b['alias_key']
    assert a['alias_key'] != c['alias_key']
    assert a['semantic_status'] == b['semantic_status'] == 'UNSCREENED_NO_EDGES_ALLOWED'
