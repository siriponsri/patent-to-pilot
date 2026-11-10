import copy

import pytest
from jsonschema import Draft202012Validator

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_quote_profile import align_quote_profile
from patent_to_pilot.research.sacr_schema import quote_profile_schema
from test_sacr_quote_profile import SOURCE, proposal


def validator():
    schema = quote_profile_schema(source=SOURCE, query_id='q1', input_kind='MTM_P')
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_existing_fixture_and_optional_nullable_roles():
    p = proposal()
    validator().validate(p)
    p['blocks'][0].update(action=None, operand=None, effect=None)
    validator().validate(p)
    align_quote_profile(p, source=SOURCE, query_id='q1', input_kind='MTM_P')


@pytest.mark.parametrize('case', ['identity', 'extra', 'missing', 'block_cap', 'condition_cap',
                                  'kind', 'offset', 'empty_quote', 'numeric_type', 'role_type'])
def test_schema_rejects_structural_defects(case):
    p = proposal()
    b = p['blocks'][0]
    c = b['attached_conditions'][0]
    if case == 'identity':
        p['query_id'] = 'q2'
    elif case == 'extra':
        p['hidden_labels'] = []
    elif case == 'missing':
        del b['attached_conditions']
    elif case == 'block_cap':
        p['blocks'] = [copy.deepcopy(b) for _ in range(9)]
    elif case == 'condition_cap':
        b['attached_conditions'] = [copy.deepcopy(c) for _ in range(9)]
    elif case == 'kind':
        c['kind'] = 'invented'
    elif case == 'offset':
        b['source_spans'][0]['start'] = 0
    elif case == 'empty_quote':
        b['source_spans'] = []
    elif case == 'numeric_type':
        c['numeric_value'] = 5
    elif case == 'role_type':
        b['action'] = 3
    assert not validator().is_valid(p)


@pytest.mark.parametrize('case', ['invented_quote', 'duplicate_id', 'failed_without_reason', 'whitespace'])
def test_post_generation_validation_remains_necessary(case):
    p = proposal()
    if case == 'invented_quote':
        p['blocks'][0]['source_spans'][0]['text'] = 'not in the source'
    elif case == 'duplicate_id':
        p['blocks'][0]['attached_conditions'][0]['condition_id'] = p['blocks'][0]['block_id']
    elif case == 'failed_without_reason':
        p['extraction_status'] = 'failed'
        p['failure_reasons'] = []
    else:
        p['blocks'][0]['relation_text'] = ' '
    validator().validate(p)
    with pytest.raises(InputBoundaryError):
        align_quote_profile(p, source=SOURCE, query_id='q1', input_kind='MTM_P')


def test_empty_failed_profile_and_unicode_context():
    p = proposal()
    p.update(blocks=[], extraction_status='failed', failure_reasons=['insufficient text'])
    validator().validate(p)
    assert align_quote_profile(p, source=SOURCE, query_id='q1', input_kind='MTM_P')['validation']['anchor_fallback_required']
    p['unknowns'] = [{'description': 'ไทย "quoted"\n🧪', 'reason': 'ambiguity', 'source_spans': []}]
    validator().validate(p)


def test_schema_identity_does_not_share_mutable_state():
    first = quote_profile_schema(source=SOURCE, query_id='q1', input_kind='MTM_P')
    first['properties']['query_id']['enum'][0] = 'changed'
    assert validator().is_valid(proposal())
