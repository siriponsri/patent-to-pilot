import importlib.util
from pathlib import Path, PurePosixPath
import pytest
import subprocess
from types import SimpleNamespace


def load():
    p=Path(__file__).resolve().parents[1]/'scripts/healthtech/supervise_sg_r3_census.py'
    spec=importlib.util.spec_from_file_location('sg_r3_supervisor',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


@pytest.mark.parametrize('fault',[None,'network','gpu','extra_mount','write_input','memory','logs'])
def test_isolation_requires_exact_allowlist(fault):
    m=load();mounts=[(PurePosixPath('/job/corpus.jsonl'),'/input/corpus.jsonl',True)]
    h={'NetworkMode':'none','ReadonlyRootfs':True,'Privileged':False,'DeviceRequests':[],
       'Memory':1536*1024**2,'MemorySwap':1536*1024**2,'NanoCpus':1_000_000_000,
       'CapDrop':['ALL'],'SecurityOpt':['no-new-privileges'],'LogConfig':{'Type':'none'},
       'PidsLimit':64,'Ulimits':[{'Name':'fsize','Soft':8*1024**2,'Hard':8*1024**2}]}
    s={'HostConfig':h,'Image':m.IMAGE,'Config':{'User':'1000:1000'},
       'Mounts':[{'Source':'/job/corpus.jsonl','Destination':'/input/corpus.jsonl','RW':False}]}
    if fault=='network':h['NetworkMode']='host'
    if fault=='gpu':h['DeviceRequests']=[{'Count':1}]
    if fault=='memory':h['Memory']*=2
    if fault=='logs':h['LogConfig']['Type']='json-file'
    if fault=='write_input':s['Mounts'][0]['RW']=True
    if fault=='extra_mount':s['Mounts'].append({'Source':'/private','Destination':'/hidden','RW':False})
    if fault:
        with pytest.raises(RuntimeError):m.validate_isolation(s,mounts)
    else:m.validate_isolation(s,mounts)


@pytest.mark.parametrize('first_state',['running','unknown'])
def test_stop_response_loss_still_kills_then_reobserves(monkeypatch,first_state):
    m=load();calls=[];observations=0
    def run(cmd,**kwargs):
        calls.append(cmd[1])
        if cmd[1]=='stop':raise subprocess.TimeoutExpired(cmd,15)
        return SimpleNamespace(returncode=0)
    def inspect():
        nonlocal observations
        observations+=1
        if observations==1:
            if first_state=='unknown':raise ValueError('bad observation')
            return {'State':{'Running':True}}
        return {'State':{'Running':False,'ExitCode':137}}
    monkeypatch.setattr(m.subprocess,'run',run);monkeypatch.setattr(m,'inspect',inspect)
    assert not m.stop_owned()['State']['Running']
    assert calls==['stop','kill'] and observations==2


def test_unverified_kill_never_reports_terminal(monkeypatch):
    m=load()
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0))
    monkeypatch.setattr(m,'inspect',lambda:{'State':{'Running':True}})
    with pytest.raises(RuntimeError):m.stop_owned()
