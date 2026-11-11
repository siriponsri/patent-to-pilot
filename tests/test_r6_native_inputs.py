import pytest

from patent_to_pilot.research.r6_native_inputs import preflight_native
from patent_to_pilot.research.r6_cohort import digest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def test_all100_full_inputs_retained_and_generated_critic_not_claimed(tmp_path):
    from test_sacr_r6_bundle_runner import setup
    args,_,_=setup(tmp_path)
    rows=[{'query_id':f'q{i:03}','source':args['source']} for i in range(100)]
    calls=[]
    def count(messages):
        calls.append(messages)
        return 8193 if len(calls)<=42 else 10
    receipt=preflight_native(rows,manifest_sha256=digest(rows),prompt_root=args['prompt_root'],
        generic_prompt_sha256=args['generic_prompt_sha256'],count_tokens=count,check_admission=lambda i:None)
    assert len(calls)==200 and len(receipt['units'])==100
    assert receipt['risk_units']==21 and receipt['status']=='STOPPED_INPUT_RISK_CAP'
    assert receipt['model_calls']==0 and not receipt['semantic_pass']
    assert receipt['critic_input_admission'].startswith('REQUIRES_ACTUAL')


def test_changed_manifest_stops_before_tokenizer(tmp_path):
    with pytest.raises(InputBoundaryError):
        preflight_native([],manifest_sha256='a'*64,prompt_root=tmp_path,
            generic_prompt_sha256='b'*64,count_tokens=lambda _:pytest.fail('unexpected tokenizer'),
            check_admission=lambda i:None)
