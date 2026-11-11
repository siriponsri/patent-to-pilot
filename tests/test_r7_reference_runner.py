import copy,json
import pytest
from test_r6_reference_runner import setup as prior_setup
from patent_to_pilot.research.r7_reference_runner import task,preflight_requests,run_reference_cohort
from patent_to_pilot.research.r6_critic_tasks import RECORD_CRITERIA
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def setup(mode='graph',bad=False):
    count=114 if mode=='graph' else 24
    tasks=[task(dict(query_id=f'q{i:03}',source='A pump moves water.',artifacts={'candidate':'Water is moved.'},
                     criteria=RECORD_CRITERIA,scope={'authored':True})) for i in range(count)]
    _,base,calls=prior_setup(mode,bad)
    def invoke(stage,path,messages,schema):
        index=int(stage.split('-')[-1]);prepared=tasks[index]['prepared']
        assert messages==prepared['messages']
        assert messages!=prepared['original']['messages']
        assert schema==prepared['original']['schema']
        return base(stage,path,messages,schema)
    return tasks,invoke,calls


def run(tmp_path,tasks,invoke,preflight,mode='graph'):
    return run_reference_cohort(destination=tmp_path/'out',tasks=tasks,preflight=preflight,mode=mode,
                                run_id='authored',invoke=invoke,check_admission=lambda i:None)


def test_graph_fourteen_initial_risks_seventh_new_flag_stops(tmp_path):
    tasks,invoke,calls=setup(bad=True)
    # Put the risks last: they must count before the first backend call.
    huge=copy.deepcopy(tasks[-1]['unit']);huge['source']='word '*(64*256+1)
    tasks[-1]=task(huge)
    positions=iter(range(113))
    p=preflight_requests(tasks,mode='graph',count_tokens=lambda m:8193 if next(positions)>=100 else 10)
    assert p['input_limit_units']==14 and p['rows'][-1]['status']=='CATALOGUE_LIMIT'
    r=run(tmp_path,tasks,invoke,p)
    assert len(calls)==7 and r['risk_units']==21 and r['status']=='STOP_RISK_CAP'
    assert r['fixed_denominator']==114 and len(r['unstarted_parent_ids'])==107
    assert r['initial_risk_parent_ids']==[f'q{i:03}' for i in range(100,114)]
    assert r['costs']['metrics']['model_calls']['value']==7


def test_complete_graph_skips_all_fourteen_limits_without_dropping_parents(tmp_path):
    tasks,invoke,calls=setup()
    huge=copy.deepcopy(tasks[-1]['unit']);huge['source']='word '*(64*256+1);tasks[-1]=task(huge)
    positions=iter(range(113))
    p=preflight_requests(tasks,mode='graph',count_tokens=lambda m:8193 if next(positions)>=100 else 10)
    r=run(tmp_path,tasks,invoke,p)
    assert len(calls)==100 and len(r['results'])==114 and r['risk_units']==14
    assert r['status']=='SCREENING_COMPLETE_NOT_FIDELITY' and not r['semantic_pass']
    assert not r['unstarted_parent_ids']


@pytest.mark.parametrize('fault',['old_messages','schema','version','preflight_hash','duplicate','missing'])
def test_mutations_reject_before_backend(tmp_path,fault):
    tasks,invoke,calls=setup('calibration')
    p=preflight_requests(tasks,mode='calibration',count_tokens=lambda m:10)
    prepared=tasks[0]['prepared']
    if fault=='old_messages':prepared['messages']=prepared['original']['messages']
    elif fault=='schema':prepared['original']['schema']['additionalProperties']=True
    elif fault=='version':prepared['version']='wrong'
    elif fault=='preflight_hash':p['rows'][0]['messages_sha256']='0'*64
    elif fault=='duplicate':tasks[-1]=tasks[0]
    else:tasks.pop()
    with pytest.raises(InputBoundaryError):run(tmp_path,tasks,invoke,p,'calibration')
    assert calls==[] and not (tmp_path/'out').exists()


def test_unknown_backend_preserves_completed_costs_and_blocks_replay(tmp_path):
    tasks,invoke,calls=setup('calibration');p=preflight_requests(tasks,mode='calibration',count_tokens=lambda m:10)
    def broken(stage,*args):
        if stage=='reference-002':raise RuntimeError('authored unknown execution')
        return invoke(stage,*args)
    with pytest.raises(RuntimeError):run(tmp_path,tasks,broken,p,'calibration')
    failure=json.loads((tmp_path/'out/failure.json').read_bytes())
    assert len(calls)==len(failure['known_events'])==2 and failure['unknown_attempt']
    with pytest.raises(FileExistsError):run(tmp_path,tasks,invoke,p,'calibration')
