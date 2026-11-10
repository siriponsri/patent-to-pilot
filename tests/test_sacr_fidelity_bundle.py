import hashlib
import json
import pytest

from patent_to_pilot.research.sacr_fidelity_bundle import screen_bundle, critic_messages, combine_screen as combine_bound
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_fidelity_screen import DIMENSIONS
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

SOURCE = 'Reduce reverse flow without electrical power.'
PROMPT = b'Screen source only.'


def reservation(a, s):
    messages = critic_messages(prompt_raw=PROMPT, expected_prompt_sha256=hashlib.sha256(PROMPT).hexdigest(),
        query_id='q1', source=SOURCE, artifacts=a, screening=s)
    return {'status':'RESERVED', 'retry':False, 'limits':GenerationLimits().__dict__,
            'messages_sha256':hashlib.sha256(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode()).hexdigest()}


def combine_screen(**args):
    if args['screening'].get('status') == 'BUNDLE_READY_FOR_CRITIC' and args['critic_raw'] is not None:
        args.update(critic_reservation=reservation(args['artifacts'],args['screening']),
            prompt_raw=PROMPT,expected_prompt_sha256=hashlib.sha256(PROMPT).hexdigest())
    return combine_bound(**args)


def fixture():
    artifacts = {k: SOURCE for k in ('compact', 'selective', 'generic_0')}
    artifacts['profile'] = json.dumps({'relation': SOURCE})
    return artifacts


def screen(artifacts):
    return screen_bundle(query_id='q1', source=SOURCE, artifacts=artifacts,
        protected_phrases=['without electrical power'], maximum_characters=65536, structurally_valid=True)


def critic():
    return json.dumps({'query_id':'q1','source_sha256':hashlib.sha256(SOURCE.encode()).hexdigest(),
        'dimensions':{d:'supported' for d in DIMENSIONS},'findings':[]}).encode()


def test_complete_bundle_is_never_automatic_semantic_pass():
    a=fixture();s=screen(a)
    result=combine_screen(screening=s,critic_raw=critic(),query_id='q1',source=SOURCE,artifacts=a)
    assert result['status']=='AUTOMATIC_UNFLAGGED_NOT_FIDELITY_PASS'
    assert result['semantic_pass'] is False


def test_omitted_view_blocks_critic_and_cannot_hide_behind_valid_profile():
    a=fixture();del a['selective'];s=screen(a)
    assert s['status']=='UNASSESSABLE_BUNDLE' and not s['critic_call_allowed']
    assert combine_screen(screening=s,critic_raw=critic(),query_id='q1',source=SOURCE,artifacts=a)['status']=='UNASSESSABLE'


def test_supported_critic_cannot_override_lexical_loss():
    a=fixture();a['selective']='Reduce reverse flow.'
    result=combine_screen(screening=screen(a),critic_raw=critic(),query_id='q1',source=SOURCE,artifacts=a)
    assert result['status']=='ESCALATE' and result['semantic_pass'] is False


@pytest.mark.parametrize('raw',[None,b'{bad'])
def test_missing_or_malformed_critic_escalates(raw):
    a=fixture()
    assert combine_screen(screening=screen(a),critic_raw=raw,query_id='q1',source=SOURCE,artifacts=a)['status']=='UNASSESSABLE'


def test_prompt_and_artifact_hashes_bound_before_call():
    a=fixture();s=screen(a);prompt=b'Screen only source.'
    args=dict(prompt_raw=prompt,expected_prompt_sha256=hashlib.sha256(prompt).hexdigest(),query_id='q1',source=SOURCE,artifacts=a,screening=s)
    assert len(critic_messages(**args))==2
    a['generic_0']='Change polarity.'
    with pytest.raises(InputBoundaryError):critic_messages(**args)
    with pytest.raises(InputBoundaryError):combine_screen(screening=s,critic_raw=critic(),query_id='q1',source=SOURCE,artifacts=a)


def test_missing_lexical_receipt_cannot_be_unflagged():
    a=fixture();a['selective']='Reduce reverse flow.';s=screen(a)
    del s['lexical']['selective']
    with pytest.raises(InputBoundaryError,match='lexical evidence'):
        combine_screen(screening=s,critic_raw=critic(),query_id='q1',source=SOURCE,artifacts=a)


def test_critic_from_different_bundle_is_rejected_even_same_source():
    a=fixture();old=reservation(a,screen(a))
    a['generic_0']=SOURCE+' Reduce reverse flow.';s=screen(a)
    with pytest.raises(InputBoundaryError,match='request does not match'):
        combine_bound(screening=s,critic_raw=critic(),query_id='q1',source=SOURCE,artifacts=a,
            critic_reservation=old,prompt_raw=PROMPT,expected_prompt_sha256=hashlib.sha256(PROMPT).hexdigest())
