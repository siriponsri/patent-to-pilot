import hashlib
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_fidelity_screen import DIMENSIONS
from patent_to_pilot.research.sacr_generated_token_profile import CONTRACT
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_outcomes import METRICS
from patent_to_pilot.research.sacr_r2_bundle_runner import run_bundle
from patent_to_pilot.research.sacr_token_profile import source_catalogue
from test_sacr_profile import SOURCE
from test_sacr_prompts import PROMPTS
from test_sacr_token_profile import proposal


def digest(raw): return hashlib.sha256(raw).hexdigest()


def harness(tmp_path, mode=None):
    files = {'profile_tokens':'sacr_profile_tokens_v1.txt', 'generic':'sacr_generic_views_v0.txt',
             'selective':'sacr_selective_v0.txt', 'critic':'sacr_fidelity_screen_v1.txt'}
    hashes = {k:digest((PROMPTS/v).read_bytes()) for k,v in files.items()}
    execution = {'run_id':'authored-r2', 'profile_contract':CONTRACT,
        'identities':{'generator_manifest':'a'*64, 'prompt_manifest':'b'*64},
        'limits':GenerationLimits().__dict__}
    calls = []

    def invoke(stage, path, messages, schema):
        calls.append(stage)
        path.mkdir(exist_ok=False)
        if mode == 'infra' and stage == 'generic': raise RuntimeError('authored interruption')
        reservation = {'status':'RESERVED', 'retry':False, 'limits':GenerationLimits().__dict__,
            'messages_sha256':digest(json.dumps(messages, ensure_ascii=False, sort_keys=True).encode())}
        if mode == 'wrong_request': reservation['messages_sha256'] = '0'*64
        (path/'reservation.json').write_text(json.dumps(reservation))
        if stage == 'profile':
            p = proposal(SOURCE, [(0,len(source_catalogue(SOURCE)['tokens']),SOURCE)])
            p['input_kind'] = 'DAPFAM_TA'
            text = json.dumps(p)
        elif stage == 'generic': text = json.dumps({'views':[SOURCE]})
        elif stage == 'selective': text = json.dumps({'selective_abstract':SOURCE})
        else:
            critic = {'query_id':'q1', 'source_sha256':digest(SOURCE.encode()),
                      'dimensions':{k:'supported' for k in DIMENSIONS}, 'findings':[]}
            if mode == 'surrogate_critic':
                critic['dimensions']['roles_direction'] = 'uncertain'
                critic['findings'] = [{'dimension':'roles_direction', 'artifact':'compact',
                    'source_quote':SOURCE, 'candidate_quote':SOURCE, 'reason':chr(0xd800)}]
            text = json.dumps(critic)
        if mode == 'bad_profile' and stage == 'profile': text = '{invalid'
        if mode == 'bad_generic' and stage == 'generic': text = '{invalid'
        record = {'status':'EOS_COMPLETE', 'text':text, 'model_calls':1, 'input_tokens':10,
                  'output_tokens':5, 'response_sha256':digest(text.encode()), 'retry':False}
        if mode == stage+'_input_limit':
            record = {'status':'INPUT_LIMIT', 'text':None, 'model_calls':0,
                      'input_tokens':8193, 'output_tokens':0, 'retry':False}
        (path/'generation.json').write_text(json.dumps(record))
        metrics = {k:0 for k in METRICS}
        metrics.update({k:record[k] for k in ('model_calls','input_tokens','output_tokens')})
        return metrics

    args = dict(destination=tmp_path/'bundle', query_id='q1', source=SOURCE, execution=execution,
        prompt_root=PROMPTS, expected_prompt_hashes=hashes, invoke=invoke,
        check_admission=lambda stage:None, maximum_characters=65536)
    return args, calls


def test_complete_bundle_binds_four_attempts_but_never_passes_fidelity(tmp_path):
    args,calls = harness(tmp_path)
    result = run_bundle(**args)
    assert calls == ['profile','generic','selective','critic']
    assert result['status'] == 'AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS'
    assert result['semantic_pass'] is False
    assert result['costs']['metrics']['model_calls']['value'] == 4
    with pytest.raises(FileExistsError): run_bundle(**args)
    assert len(calls) == 4


def test_rejected_profile_is_retained_charged_and_never_dispatches_views(tmp_path):
    args,calls = harness(tmp_path,'bad_profile')
    result = run_bundle(**args)
    assert calls == ['profile'] and result['status'] == 'UNASSESSABLE'
    assert result['costs']['metrics']['model_calls']['value'] == 1
    assert (args['destination']/'profile-rejection.json').exists()


def test_rejected_generic_preserves_independent_selective_without_critic(tmp_path):
    args,calls = harness(tmp_path,'bad_generic')
    result = run_bundle(**args)
    assert calls == ['profile','generic','selective']
    assert result['status'] == 'UNASSESSABLE'
    artifacts = json.loads((args['destination']/'artifacts.json').read_bytes())
    assert artifacts['selective'] == SOURCE and 'generic_0' not in artifacts
    assert result['costs']['metrics']['model_calls']['value'] == 3


@pytest.mark.parametrize('mode', ['infra','wrong_request'])
def test_uncertain_or_mismatched_attempt_stops_and_cannot_restart(tmp_path,mode):
    args,calls = harness(tmp_path,mode)
    with pytest.raises((RuntimeError,InputBoundaryError)): run_bundle(**args)
    assert 'critic' not in calls and 'selective' not in calls
    failure = json.loads((args['destination']/'failure.json').read_bytes())
    assert failure['unsettled_attempt_cost'].startswith('UNKNOWN')
    with pytest.raises(FileExistsError): run_bundle(**args)


def test_admission_failure_makes_no_generation_call(tmp_path):
    args,calls = harness(tmp_path)
    def deny(stage): raise TimeoutError('budget unavailable')
    args['check_admission'] = deny
    with pytest.raises(TimeoutError): run_bundle(**args)
    assert calls == []


@pytest.mark.parametrize('change', ['contract','critic_prompt','limit'])
def test_invalid_contract_is_rejected_before_any_call(tmp_path,change):
    args,calls = harness(tmp_path)
    if change == 'contract': args['execution']['profile_contract'] = 'legacy'
    elif change == 'critic_prompt': args['expected_prompt_hashes']['critic'] = '0'*64
    else: args['maximum_characters'] = False
    with pytest.raises(InputBoundaryError): run_bundle(**args)
    assert calls == [] and not args['destination'].exists()


def test_escaped_surrogate_in_completed_critic_is_unassessable_with_all_costs(tmp_path):
    args,calls = harness(tmp_path,'surrogate_critic')
    result = run_bundle(**args)
    assert len(calls) == 4 and result['status'] == 'UNASSESSABLE'
    assert result['screening']['reason'] == 'MALFORMED_OR_AMBIGUOUS_CRITIC'
    assert result['costs']['metrics']['model_calls']['value'] == 4
    assert not (args['destination']/'failure.json').exists()


def test_local_executor_rechecks_admission_after_model_wrapper_setup(tmp_path, monkeypatch):
    from patent_to_pilot.research import sacr_r2_bundle_runner as runner
    calls = []
    def factory(stage,schema):
        calls.append('setup')
        return object()
    def deny(stage):
        calls.append('admission')
        raise TimeoutError('window ended during grammar setup')
    monkeypatch.setattr(runner,'run_reserved_attempt',lambda *a,**k:pytest.fail('late call'))
    invoke = runner.local_executor(tokenizer=None,model_factory=factory,device='cuda:0',
        eos_token_ids=[1],check_admission=deny,peak_memory_bytes=lambda:0)
    with pytest.raises(TimeoutError): invoke('profile',tmp_path/'attempt',[],{})
    assert calls == ['setup','admission'] and not (tmp_path/'attempt').exists()


def test_critic_input_limit_is_flagged_with_known_zero_call_cost(tmp_path):
    args,calls = harness(tmp_path,'critic_input_limit')
    result = run_bundle(**args)
    assert calls == ['profile','generic','selective','critic']
    assert result['status'] == 'UNASSESSABLE'
    assert result['costs']['metrics']['model_calls']['value'] == 3
    assert result['events'][-1]['metrics']['model_calls'] == 0
    assert result['events'][-1]['metrics']['input_tokens'] == 8193
    assert not (args['destination']/'failure.json').exists()


@pytest.mark.parametrize('stage,expected_calls', [('profile',0),('generic',2),('selective',2)])
def test_artifact_input_limit_is_unassessable_without_unknown_cost(tmp_path,stage,expected_calls):
    args,calls = harness(tmp_path,stage+'_input_limit')
    result = run_bundle(**args)
    assert result['status'] == 'UNASSESSABLE'
    assert result['costs']['metrics']['model_calls']['value'] == expected_calls
    assert 'critic' not in calls
    assert not (args['destination']/'failure.json').exists()
