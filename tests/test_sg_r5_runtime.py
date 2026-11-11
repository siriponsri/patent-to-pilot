from pathlib import Path
import sys
from copy import deepcopy
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/healthtech'))
from supervise_sg_r5_screening import configuration
from patent_to_pilot.research.sg_r5_runtime_guards import validate_budget
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def ledger():
    return {'gpu_conservative_charged_seconds':9700,'gpu_remaining_seconds':681500,'gpu_limit_seconds':691200,
        'fidelity_generation_charged_seconds':9400,'fidelity_generation_remaining_seconds':221000,'fidelity_limit_seconds':230400,
        'r5_long_run':{'owner_reply':'call_172d9619b8e64a6781a0ff36fb183240','status':'GRAPH_SCREEN_RESERVED',
            'reserved_gpu_seconds':57600,'reserved_fidelity_seconds':57600,
            'initial_gpu_charged_seconds':9525,'initial_fidelity_charged_seconds':9246}}


def test_graph_gpu_mounts_are_fixed_inputs_without_test_or_socket():
    c,mounts=configuration('smoke',Path('/job'),100,'a'*64);host=c['HostConfig']
    assert host['NanoCpus']==8_000_000_000 and host['Memory']==31*1024**3
    assert host['NetworkMode']=='none' and host['ReadonlyRootfs']
    assert {t for _,t,_ in mounts if t.startswith('/input')}=={'/input/sources-private.jsonl','/input/source-sample.json','/input/alias-sample.json'}
    assert all(ro for _,t,ro in mounts if t.startswith('/input'))
    assert not any('socket' in t or 'qrels' in t or 'test' in t for _,t,_ in mounts)
    assert c['Cmd'][1]=='/code/scripts/healthtech/run_sg_r5_screening.py'


@pytest.mark.parametrize('fault',[None,'authority','reset','reservation','cap','overspend'])
def test_graph_budget_requires_owner_scope_and_preserves_old_charges(fault):
    d=ledger()
    if fault=='authority':d['r5_long_run']['owner_reply']='wrong'
    elif fault=='reset':d['gpu_conservative_charged_seconds']=9000;d['gpu_remaining_seconds']=682200
    elif fault=='reservation':d['r5_long_run']['reserved_gpu_seconds']=0
    elif fault=='cap':d['gpu_limit_seconds']=700000
    elif fault=='overspend':d['fidelity_generation_charged_seconds']=200000;d['fidelity_generation_remaining_seconds']=30400
    if fault:
        with pytest.raises(InputBoundaryError):validate_budget(d,57600)
    else:validate_budget(d,57600)
