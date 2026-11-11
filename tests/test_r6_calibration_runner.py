import json

import pytest

from test_r6_reference_runner import setup
from patent_to_pilot.research.r6_calibration_runner import frozen_tasks,run_calibration
from patent_to_pilot.research.r6_reference_runner import encoded,sha
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def arguments(tmp_path):
    _,invoke,calls=setup('calibration')
    def all_supported(stage,path,messages,schema):
        metrics=invoke(stage,path,messages,schema)
        record=json.loads((path/'generation.json').read_bytes())
        body=json.loads(messages[1]['content'])
        text=json.dumps({'binding_sha256':body['binding_sha256'],
            'dimensions':{key:'supported' for key in schema['properties']['dimensions']['properties']},'findings':[]})
        record.update(text=text,response_sha256=sha(text.encode()))
        (path/'generation.json').write_text(json.dumps(record))
        return metrics
    return dict(destination=tmp_path/'out',tasks_sha256=sha(encoded(frozen_tasks())),run_id='authored',
        invoke=all_supported,count_tokens=lambda messages:10,check_admission=lambda index:None),calls


def test_valid_json_all_supported_is_not_semantic_calibration_pass(tmp_path):
    args,calls=arguments(tmp_path)
    result=run_calibration(**args)
    assert len(calls)==24 and result['costs']['metrics']['model_calls']['value']==24
    assert result['status']=='CALIBRATION_FAILED'
    assert result['assessment']['required_verdict_misses']==14
    assert result['assessment']['execution_rejected_cases']==0
    assert not result['native_fidelity_proven']


def test_complete_input_gate_before_generation(tmp_path):
    args,calls=arguments(tmp_path);args['count_tokens']=lambda messages:8193
    result=run_calibration(**args)
    assert result['status']=='CALIBRATION_NOT_ASSESSABLE' and calls==[]


def test_changed_frozen_requests_never_call_backend(tmp_path):
    args,calls=arguments(tmp_path);args['tasks_sha256']='0'*64
    with pytest.raises(InputBoundaryError):run_calibration(**args)
    assert calls==[] and not args['destination'].exists()


def test_unknown_backend_does_not_emit_assessment(tmp_path):
    args,calls=arguments(tmp_path);original=args['invoke']
    def broken(stage,*rest):
        if stage=='reference-003':raise RuntimeError('unknown backend')
        return original(stage,*rest)
    args['invoke']=broken
    with pytest.raises(RuntimeError):run_calibration(**args)
    assert len(calls)==3 and not (args['destination']/'calibration-assessment.json').exists()
    assert (args['destination']/'failure.json').exists()
