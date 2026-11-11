from patent_to_pilot.research.sg_relations_v2 import extract_family_v2


def row(text,id='f1'): return {'id':id,'title':'','abstract':'','claims':text}


def test_semicolon_units_preserve_conditions_and_exact_role_locations():
    source='A housing; a sensor configured to detect a signal at 5 kPa without power; a unit adapted to store the data.'
    out=extract_family_v2(row(source))
    assert len(out['records'])==2
    r=out['records'][0]
    assert r['alias_descriptor']=='detect|signal'
    assert '5 kPa without power' in r['trailing_context_span']['text']
    for key in ('source_span','cue_span','action_span','operand_span','trailing_context_span'):
        s=r[key]; assert source[s['start']:s['end']]==s['text']
    assert r['semantic_status']=='UNSCREENED_NO_EDGES_ALLOWED'


def test_alias_key_does_not_assert_condition_compatibility():
    a=extract_family_v2(row('A sensor configured to detect a signal at 5 kPa.'))['records'][0]
    b=extract_family_v2(row('A sensor configured to detect the signal at 10 kPa.','f2'))['records'][0]
    assert a['alias_key']==b['alias_key']
    assert a['trailing_context_span']!=b['trailing_context_span']
    assert 'cross_record_compatibility' in a['unresolved_roles']


def test_no_synonyms_stemming_or_subject_invention():
    a=extract_family_v2(row('A device configured to receive signals.'))['records'][0]
    b=extract_family_v2(row('A device configured to receive a signal.'))['records'][0]
    assert a['alias_key']!=b['alias_key']
    assert not extract_family_v2(row('A device configured to understand signals.'))['records']
    assert 'subject_attachment' in a['unresolved_roles']


def test_no_operand_no_record_and_long_unit_abstains():
    assert not extract_family_v2(row('A unit configured to detect the.'))['records']
    out=extract_family_v2(row('x'*4100+' configured to detect a signal.'))
    assert out['counts']['over_length']==1 and not out['records']


def test_distinct_occurrences_and_cap_preserve_accounting():
    text='; '.join(['A unit configured to receive data']*10)
    out=extract_family_v2(row(text))
    assert len(out['records'])==8 and out['counts']['cap_omitted']==2
    assert len({r['relation_id'] for r in out['records']})==8


def test_decimal_quantity_in_operand_is_never_shortened():
    r=extract_family_v2(row('A filter configured to remove 0.5 micrometre particles from fluid.'))['records'][0]
    assert r['operand_span']['text']=='0.5 micrometre particles'
    assert r['alias_descriptor']=='remove|0.5 micrometre particles'
