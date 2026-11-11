import json,hashlib
import pytest
from patent_to_pilot.research.r6_reference_runner import preflight_requests,run_reference_cohort
from patent_to_pilot.research.reference_critic_v1 import prepare
from patent_to_pilot.research.r6_critic_tasks import RECORD_CRITERIA
from patent_to_pilot.research.sacr_generation import GenerationLimits
from patent_to_pilot.research.sacr_outcomes import METRICS
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def setup(mode='graph',bad=False):
    count=114 if mode=='graph' else 24
    tasks=[{'prepared':prepare(query_id=f'q{i:03}',source='A pump moves water.',artifacts={'candidate':'Water is moved.'},
        criteria=RECORD_CRITERIA,scope={'authored':True})} for i in range(count)]
    calls=[]
    def invoke(stage,path,messages,schema):
        calls.append(stage);path.mkdir()
        reservation={'status':'RESERVED','retry':False,'limits':GenerationLimits().__dict__,
            'messages_sha256':hashlib.sha256(json.dumps(messages,ensure_ascii=False,sort_keys=True).encode()).hexdigest()}
        (path/'reservation.json').write_text(json.dumps(reservation))
        body=json.loads(messages[1]['content'])
        text='{invalid' if bad else json.dumps({'binding_sha256':body['binding_sha256'],
            'dimensions':{k:'supported' for k in RECORD_CRITERIA},'findings':[]})
        record={'status':'EOS_COMPLETE','model_calls':1,'input_tokens':10,'output_tokens':5,'retry':False,
            'text':text,'response_sha256':hashlib.sha256(text.encode()).hexdigest()}
        (path/'generation.json').write_text(json.dumps(record))
        metrics={k:0 for k in METRICS};metrics.update(model_calls=1,input_tokens=10,output_tokens=5)
        return metrics
    return tasks,invoke,calls


def test_all114_requests_admitted_before_any_reference_call(tmp_path):
    tasks,invoke,calls=setup();seen=[]
    def count(messages):seen.append(1);return 10
    p=preflight_requests(tasks,mode='graph',count_tokens=count)
    assert len(seen)==114 and calls==[]
    r=run_reference_cohort(destination=tmp_path/'out',tasks=tasks,preflight=p,mode='graph',run_id='authored',invoke=invoke,check_admission=lambda i:None)
    assert len(calls)==114 and r['risk_units']==0 and not r['semantic_pass']
    with pytest.raises(FileExistsError):run_reference_cohort(destination=tmp_path/'out',tasks=tasks,preflight=p,mode='graph',run_id='authored',invoke=invoke,check_admission=lambda i:None)


def test_input21_stops_graph_before_any_inference(tmp_path):
    tasks,invoke,calls=setup();n=iter(range(114))
    p=preflight_requests(tasks,mode='graph',count_tokens=lambda m:8193 if next(n)<21 else 10)
    r=run_reference_cohort(destination=tmp_path/'out',tasks=tasks,preflight=p,mode='graph',run_id='authored',invoke=invoke,check_admission=lambda i:None)
    assert r['status']=='STOP_INPUT_GATE' and r['fixed_denominator']==114 and calls==[]


def test_invalid_evaluator_risk21_retains_completed_call_costs(tmp_path):
    tasks,invoke,calls=setup(bad=True);p=preflight_requests(tasks,mode='graph',count_tokens=lambda m:10)
    r=run_reference_cohort(destination=tmp_path/'out',tasks=tasks,preflight=p,mode='graph',run_id='authored',invoke=invoke,check_admission=lambda i:None)
    assert len(calls)==r['risk_units']==21 and r['status']=='STOP_RISK_CAP'
    assert r['costs']['metrics']['model_calls']['value']==21
    assert {row['reason'] for row in r['results']}=={'INVALID_EVALUATOR'}


def test_calibration_keeps_raw24_results_separate_from_semantic_grading(tmp_path):
    tasks,invoke,calls=setup('calibration');p=preflight_requests(tasks,mode='calibration',count_tokens=lambda m:10)
    r=run_reference_cohort(destination=tmp_path/'out',tasks=tasks,preflight=p,mode='calibration',run_id='authored',invoke=invoke,check_admission=lambda i:None)
    assert len(calls)==24 and all(row['critic_text'] for row in r['results'])
    assert r['status']=='SCREENING_COMPLETE_NOT_FIDELITY'


def test_changed_preflight_never_dispatches(tmp_path):
    tasks,invoke,calls=setup();p=preflight_requests(tasks,mode='graph',count_tokens=lambda m:10)
    p['rows'][0]['messages_sha256']='0'*64
    with pytest.raises(InputBoundaryError):run_reference_cohort(destination=tmp_path/'out',tasks=tasks,preflight=p,mode='graph',run_id='authored',invoke=invoke,check_admission=lambda i:None)
    assert calls==[]
