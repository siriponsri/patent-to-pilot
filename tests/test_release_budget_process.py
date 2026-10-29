"""Offline process-level regression controls for the shared project envelope."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

import pytest
from patent_to_pilot.providers.project_budget import ProjectBudget
from patent_to_pilot.providers.openrouter import BudgetExceededError

WORKER = r'''
from pathlib import Path
import json,os,socket,sys,time
def denied(*a,**kw): raise RuntimeError('network forbidden in budget worker')
socket.socket.connect=denied; socket.socket.connect_ex=denied
socket.socket.bind=denied; socket.create_connection=denied; socket.getaddrinfo=denied
from patent_to_pilot.providers.project_budget import ProjectBudget
from patent_to_pilot.providers.openrouter import BudgetExceededError
db,aid,gate,ready,action=sys.argv[1:]
b=ProjectBudget(Path(db))
Path(ready).write_text('ready')
deadline=time.monotonic()+10
while not Path(gate).exists():
 if time.monotonic()>deadline: raise RuntimeError('test start gate timeout')
 time.sleep(.01)
try:
 b.reserve(attempt_id=aid,phase='calibration',model='openai/gpt-4.1-mini',provider='openai',payload_sha256='a'*64,upper_bound_usd='.75',bound_verified=True,data_class='synthetic')
 if action=='crash': os._exit(7)
 print(json.dumps({'result':'reserved'}))
except BudgetExceededError:
 print(json.dumps({'result':'blocked'}))
finally: b.close()
'''


def reserve(b, aid, amount='.5'):
    return b.reserve(attempt_id=aid,phase='calibration',model='openai/gpt-4.1-mini',provider='openai',payload_sha256='a'*64,upper_bound_usd=amount,bound_verified=True,data_class='synthetic')


def start(tmp_path, aid, action='normal'):
    script=tmp_path/'budget-worker.py'
    if not script.exists():script.write_text(WORKER,encoding='utf-8')
    ready=tmp_path/(aid+'.ready')
    project_src = str(Path(__file__).resolve().parents[1] / 'src')
    child_env = os.environ.copy()
    child_env['PYTHONPATH'] = os.pathsep.join(filter(None, [project_src, child_env.get('PYTHONPATH')]))
    p=subprocess.Popen([sys.executable,'-B',str(script),str(tmp_path/'budget.sqlite'),aid,str(tmp_path/'go'),str(ready),action],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,env=child_env)
    return p,ready


def await_ready(rows):
    deadline=time.monotonic()+15
    while not all(ready.exists() for _,ready in rows):
        for p,ready in rows:
            if p.poll() is not None:pytest.fail('budget child exited before test gate')
        if time.monotonic()>deadline:pytest.fail('budget child readiness timeout')
        time.sleep(.02)


def cleanup(rows):
    for p,_ in rows:
        if p.poll() is None:
            p.terminate();p.wait(timeout=10)


def test_cross_process_atomic_reservation(tmp_path):
    ProjectBudget(tmp_path/'budget.sqlite').close()
    rows=[start(tmp_path,'a'),start(tmp_path,'b')]
    try:
        await_ready(rows);(tmp_path/'go').write_text('go')
        results=[]
        for p,_ in rows:
            out,err=p.communicate(timeout=20)
            assert p.returncode==0,err
            results.append(json.loads(out)['result'])
        assert sorted(results)==['blocked','reserved']
        b=ProjectBudget(tmp_path/'budget.sqlite')
        assert b.snapshot()['attempts']==1 and b.snapshot()['committed_nano_usd']==750_000_000
        b.close()
    finally:cleanup(rows)


def test_crash_reservation_survives_restart_and_never_expires_implicitly(tmp_path):
    rows=[start(tmp_path,'crashed',action='crash')]
    try:
        await_ready(rows);(tmp_path/'go').write_text('go')
        p,_=rows[0];p.communicate(timeout=20);assert p.returncode==7
        b=ProjectBudget(tmp_path/'budget.sqlite')
        before=b.snapshot()
        assert before['unknown_or_pending']==['crashed']
        with pytest.raises(BudgetExceededError):reserve(b,'retry')
        b.settle('crashed',None);b.close()
        b=ProjectBudget(tmp_path/'budget.sqlite')
        assert b.snapshot()['committed_nano_usd']==750_000_000
        with pytest.raises(BudgetExceededError):reserve(b,'retry')
        b.close()
    finally:cleanup(rows)


def test_failed_attempt_charge_and_new_retry_are_both_durable(tmp_path):
    path=tmp_path/'budget.sqlite';b=ProjectBudget(path)
    reserve(b,'failed-schema');b.settle('failed-schema','.2');b.close()
    b=ProjectBudget(path)
    with pytest.raises(BudgetExceededError):reserve(b,'failed-schema')
    reserve(b,'retry-1');b.settle('retry-1','.1');b.settle('retry-1','.1');b.close()
    b=ProjectBudget(path)
    assert b.snapshot()['attempts']==2 and b.snapshot()['actual_nano_usd']==300_000_000
    with pytest.raises(BudgetExceededError):reserve(b,'too-large','.8')
    b.close()


@pytest.mark.parametrize('claim_ready',[False,True])
def test_offline_preflight_cannot_be_activated_by_config_claims(tmp_path,monkeypatch,claim_ready):
    import runpy
    import patent_to_pilot
    root=Path(patent_to_pilot.__file__).resolve().parents[2]
    plan=json.loads((root/'configs/long-run-offline-v2.json').read_text())
    plan['technical_gates']={k:True for k in plan['technical_gates']}
    plan['live_enabled']=claim_ready
    path=tmp_path/'plan.json';path.write_text(json.dumps(plan))
    out=tmp_path/'output';corpus=tmp_path/'corpus'
    monkeypatch.setattr(sys,'argv',['prepare_long_run_offline.py','--plan',str(path),'--output-dir',str(out),'--corpus-dir',str(corpus)])
    if claim_ready:
        with pytest.raises(ValueError,match='disable live'):
            runpy.run_path(str(root/'scripts/prepare_long_run_offline.py'),run_name='__main__')
        assert not out.exists() and not corpus.exists()
    else:
        runpy.run_path(str(root/'scripts/prepare_long_run_offline.py'),run_name='__main__')
        result=json.loads((out/'preflight.json').read_text())
        assert result['scientific_live_ready'] is False
        assert result['provider_calls']==0 and result['api_cost_usd']==0
        assert result['worker_isolation'].startswith('NOT_IMPLEMENTED')
