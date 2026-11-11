import copy
import json

import pytest
from jsonschema import Draft202012Validator, ValidationError

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_generated_token_profile import (
    CONTRACT, generated_token_profile_result, replay_generated_token_profile,
)
from patent_to_pilot.research.sacr_schema import token_profile_schema, quote_profile_schema
from patent_to_pilot.research.sacr_token_profile import source_catalogue
from test_sacr_controller import setup
from test_sacr_generated_view_controller import evidence
from test_sacr_profile import SOURCE
from test_sacr_token_profile import proposal


def inputs(tmp_path, status='EOS_COMPLETE', profile_change=None):
    controller = setup(tmp_path)
    count = len(source_catalogue(SOURCE)['tokens'])
    p = proposal(SOURCE, [(0, count, SOURCE)])
    p['query_id'] = 'q'
    if profile_change == 'empty': p['blocks'] = []
    elif profile_change == 'partial': p['extraction_status'] = 'partial'
    elif profile_change == 'invalid': p['blocks'][0]['source_spans'][0]['end_token'] = count+1
    elif profile_change == 'surrogate': p['blocks'][0]['relation_text'] = chr(0xd800)
    raw, identity, costs = evidence(controller, 'profile', status=status, text=json.dumps(p))
    execution = copy.deepcopy(controller.journal.execution)
    execution['profile_contract'] = CONTRACT
    return raw, identity, dict(execution=execution, attempt_id='profile', query_id='q',
                               source=SOURCE, metrics=costs, input_kind='MTM_P')


def test_generation_cost_binding_and_exact_replay(tmp_path):
    raw, identity, kwargs = inputs(tmp_path)
    result = generated_token_profile_result(raw, identity, **kwargs)
    assert result['format'] == CONTRACT
    assert result['compact']['text'] == SOURCE
    assert result['generation']['record']['model_calls'] == 1
    assert result['semantic_status'] == 'unknown'
    assert replay_generated_token_profile(result, **kwargs) == result
    result['compact']['text'] = 'changed'
    with pytest.raises(InputBoundaryError): replay_generated_token_profile(result, **kwargs)


@pytest.mark.parametrize('change', ['contract', 'artifact', 'source', 'cost', 'prompt', 'attempt'])
def test_wrong_execution_or_cost_cannot_be_rebound(tmp_path, change):
    raw, identity, kwargs = inputs(tmp_path)
    if change == 'contract': del kwargs['execution']['profile_contract']
    elif change == 'artifact': identity['artifact_sha256'] = '0'*64
    elif change == 'source': kwargs['source'] += ' changed'
    elif change == 'cost': kwargs['metrics']['output_tokens'] += 1
    elif change == 'prompt': identity['prompt_manifest_sha256'] = '0'*64
    else: kwargs['attempt_id'] = 'different'
    with pytest.raises(InputBoundaryError): generated_token_profile_result(raw, identity, **kwargs)


def test_non_eos_retains_original_generation_and_cost(tmp_path):
    from patent_to_pilot.research.sacr_generated_view import GenerationEvidenceFailure
    raw, identity, kwargs = inputs(tmp_path, status='NO_EOS')
    with pytest.raises(GenerationEvidenceFailure) as failure:
        generated_token_profile_result(raw, identity, **kwargs)
    assert failure.value.output['reason'] == 'GENERATION_NOT_EOS_COMPLETE'
    assert failure.value.output['generation_artifact_utf8'].encode() == raw
    assert failure.value.metrics == kwargs['metrics']
    assert failure.value.output['retry'] is False


@pytest.mark.parametrize('state', ['empty', 'partial', 'invalid', 'surrogate'])
def test_unusable_profiles_are_not_promoted(tmp_path, state):
    from patent_to_pilot.research.sacr_generated_view import GenerationEvidenceFailure
    raw, identity, kwargs = inputs(tmp_path, profile_change=state)
    if state in ('invalid', 'surrogate'):
        with pytest.raises(GenerationEvidenceFailure) as failure:
            generated_token_profile_result(raw, identity, **kwargs)
        assert failure.value.output['generation_artifact_utf8'].encode() == raw
        assert failure.value.metrics == kwargs['metrics']
    else:
        result = generated_token_profile_result(raw, identity, **kwargs)
        assert result['decision'] != 'PROFILE_STRUCTURALLY_PREPARED_FIDELITY_PENDING'


def test_source_bound_schema_preserves_legacy_and_accepts_token_profile():
    source = 'A works. A works.'
    args = dict(source=source, query_id='q1', input_kind='MTM_P')
    legacy = quote_profile_schema(**args)
    schema = token_profile_schema(**args)
    Draft202012Validator.check_schema(schema)
    v = Draft202012Validator(schema)
    p = proposal(source, [(2, 4, 'A works.')])
    v.validate(p)
    assert quote_profile_schema(**args) == legacy
    for key, value in [('start_token', -1), ('end_token', 5), ('start_token', True)]:
        bad = copy.deepcopy(p)
        bad['blocks'][0]['source_spans'][0][key] = value
        with pytest.raises(ValidationError): v.validate(bad)
    p['blocks'][0]['source_spans'][0]['text'] = 'legacy quote'
    with pytest.raises(ValidationError): v.validate(p)
