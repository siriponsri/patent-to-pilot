import importlib.util
from pathlib import Path
from types import SimpleNamespace
import json
import subprocess
import pytest


def load():
    path=Path(__file__).resolve().parents[1]/'scripts/healthtech/supervise_sacr_r2_synthetic_smoke.py'
    spec=importlib.util.spec_from_file_location('r2_supervisor',path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def test_deadline_stops_owned_container_and_reads_terminal(monkeypatch):
    m=load(); calls=[]
    monkeypatch.setattr(m.time,'monotonic',lambda:1560)
    monkeypatch.setattr(m,'stop_owned',lambda:calls.append('stop') or {'State':{'Running':False}})
    monkeypatch.setattr(m,'inspect',lambda:{'State':{'Running':False,'ExitCode':137}})
    child=SimpleNamespace(poll=lambda:None,wait=lambda timeout:137)
    reason,rc,state=m.monitor(child,1560)
    assert calls==['stop'] and reason=='TIMEOUT' and rc==137
    assert not state['State']['Running']


def test_attached_client_exit_never_proves_container_terminal(monkeypatch):
    m=load(); calls=[]
    monkeypatch.setattr(m,'inspect',lambda:{'State':{'Running':True}})
    monkeypatch.setattr(m,'stop_owned',lambda:calls.append('stop') or {'State':{'Running':False}})
    result=m.monitor(SimpleNamespace(poll=lambda:0,wait=lambda timeout:0),1560)
    assert result[0]=='CLIENT_EXITED_CONTAINER_RUNNING' and calls==['stop']


def test_normal_terminal_does_not_stop_or_restart(monkeypatch):
    m=load()
    monkeypatch.setattr(m,'inspect',lambda:{'State':{'Running':False,'ExitCode':0}})
    monkeypatch.setattr(m,'stop_owned',lambda:(_ for _ in ()).throw(AssertionError('unexpected stop')))
    assert m.monitor(SimpleNamespace(poll=lambda:0,wait=lambda timeout:0),1560)[0]=='EXITED'


def test_stop_timeout_still_kills_and_reobserves(monkeypatch):
    m=load(); calls=[]; states=iter([{'State':{'Running':True}},{'State':{'Running':False}}])
    def run(cmd,**kwargs):
        calls.append(cmd[1])
        if cmd[1]=='stop': raise subprocess.TimeoutExpired(cmd,15)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(m.subprocess,'run',run)
    monkeypatch.setattr(m,'inspect',lambda:next(states))
    assert not m.stop_owned()['State']['Running']
    assert calls==['stop','kill']


@pytest.mark.parametrize('change', ['nan','inflated','erased','insufficient'])
def test_budget_cannot_use_nonfinite_inflated_or_erased_cost(change):
    from patent_to_pilot.research.sacr_r2_runtime_guards import validate_budget
    from patent_to_pilot.research.mtm_runtime import InputBoundaryError
    root=Path(__file__).resolve().parents[1]
    ledger=json.loads((root/'docs/healthtech/audits/ptp-mtm-dapfam-resume-20261110/resource-ledger.json').read_bytes())
    validate_budget(ledger,1800)
    if change=='nan': ledger['gpu_remaining_seconds']=float('nan')
    elif change=='inflated': ledger['gpu_remaining_seconds']+=1800
    elif change=='erased':
        ledger['gpu_conservative_charged_seconds']=0; ledger['gpu_remaining_seconds']=259200
    else:
        ledger['fidelity_generation_remaining_seconds']=1000; ledger['fidelity_generation_charged_seconds']=27800
    with pytest.raises(InputBoundaryError): validate_budget(ledger,1800)


def test_empty_source_pin_set_is_never_accepted(tmp_path):
    from patent_to_pilot.research.sacr_r2_runtime_guards import validate_sources
    from patent_to_pilot.research.mtm_runtime import InputBoundaryError
    with pytest.raises(InputBoundaryError): validate_sources(tmp_path,{})
