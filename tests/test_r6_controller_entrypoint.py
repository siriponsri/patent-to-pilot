"""Actual controller main with authored Docker/GPU probes and real journal."""
from copy import deepcopy
from pathlib import Path
import json
import sys
from types import SimpleNamespace

import pytest

sys.path.insert(0,str(Path(__file__).parents[1]/'scripts/healthtech'))
import supervise_r6_calibration as controller
import supervise_sacr_r5_engine as prior
from r3_engine_client import EngineError
from test_r6_admission import fixture
from test_r3_engine_packaging import state_for
from patent_to_pilot.research.r6_dispatch_journal import initialize,DispatchJournal


def setup(tmp_path,monkeypatch,fault=None):
    jobs=tmp_path/'jobs';job=jobs/'ptp-r6-calibration-20261111-v1';job.mkdir(parents=True)
    code=job/'code';scripts=code/'scripts/healthtech';scripts.mkdir(parents=True)
    for name in ['r3_engine_client.py','supervise_sacr_r5_engine.py','supervise_r6_calibration.py']:
        (job/name).write_text('authored');(scripts/name).write_text('authored')
    (job/'dispatch').mkdir();base=tmp_path/'base'
    (base/'venv/lib/python3.12/site-packages').mkdir(parents=True)
    (base/'models/qwen3-8b').mkdir(parents=True)
    (base/('models/.'+controller.GPU+'.lock')).write_text('')
    monkeypatch.setattr(prior,'BASE',base)
    monkeypatch.setattr(controller,'__file__',str(job/'supervise_r6_calibration.py'))
    monkeypatch.setattr(controller,'Path',lambda p:jobs if str(p)=='/home/chaw/patent-to-pilot-jobs' else Path(p))
    monkeypatch.setattr(controller,'signal',SimpleNamespace(SIGTERM=1,signal=lambda *a:None))
    monkeypatch.setitem(sys.modules,'resource',SimpleNamespace(RLIMIT_AS=1,RLIMIT_FSIZE=2,RUSAGE_SELF=3,
        setrlimit=lambda *a:None,getrusage=lambda *a:SimpleNamespace(ru_maxrss=1)))
    d,l,s,g=fixture();old=d['attempt_id'];d.update(attempt_id=job.name,ledger_generation=0,files_sha256={})
    s['stage_attempts']['calibration']=[job.name]
    s['reservations']=[{'attempt_id':job.name,'status':'RESERVED','declaration':deepcopy(d)}]
    s['qualified_dispatches']={job.name:deepcopy(d)}
    from patent_to_pilot.research import r6_dispatch_files
    monkeypatch.setattr(r6_dispatch_files,'load_dispatch',lambda *a,**k:{'declaration':d,'ledger':l,'scope':s,'gates':g})
    monkeypatch.setattr(r6_dispatch_files,'validate_worker_package',lambda *a:None)
    control=jobs/'ptp-r6-control';control.mkdir()
    stored=deepcopy(s)
    if fault=='stale':stored['authored_new_generation']='current differs'
    initialize(control/'dispatch.sqlite','a'*64,l,stored)
    if fault=='busy':output=controller.GPU
    else:output=''
    monkeypatch.setattr(controller.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout=output))
    events=[]
    class FakeEngine:
        config=None
        def check_version(self):return {'ApiVersion':'authored'}
        def inspect(self,name):
            if self.config is None:
                if fault=='owned':return {'State':{'Running':False}}
                raise EngineError(404)
            mounts=[(Path(m['Source']),m['Target'],m['ReadOnly']) for m in self.config['HostConfig']['Mounts']]
            state=state_for(self.config,mounts);state['State'].update(Pid=0)
            return state
        def request(self,method,path,payload=None):
            events.append(path)
            if 'create?' in path:
                if fault in ('create_failure','unknown_stop'):raise TimeoutError('authored create transport loss')
                self.config=payload
        def terminate(self,name):
            events.append('terminate')
            if fault=='unknown_stop':raise TimeoutError('authored unknown termination')
            raise EngineError(404)
    monkeypatch.setattr(controller,'Engine',FakeEngine)
    return job,events,(d,l,s,g),control/'dispatch.sqlite'


def test_actual_controller_claims_current_ledger_before_create_and_never_replays(tmp_path,monkeypatch):
    job,events,args,path=setup(tmp_path,monkeypatch)
    controller.main('a'*64)
    assert json.loads((job/'global-dispatch.json').read_bytes())['status']=='CONSUMED_UNRESOLVED'
    assert json.loads((job/'terminal.json').read_bytes())['status']=='TERMINAL'
    assert any('/create?' in event for event in events)
    with pytest.raises(FileExistsError):controller.main('a'*64)
    with pytest.raises(ValueError):DispatchJournal(path,'a'*64).claim(*args,expected_generation=0)


@pytest.mark.parametrize('fault',['stale','busy','owned','create_failure','unknown_stop'])
def test_actual_controller_rejects_stale_or_busy_and_preserves_unknown(tmp_path,monkeypatch,fault):
    job,events,args,path=setup(tmp_path,monkeypatch,fault)
    with pytest.raises((RuntimeError,ValueError,TimeoutError)):controller.main('a'*64)
    terminal=json.loads((job/'terminal.json').read_bytes())
    if fault in ('stale','busy','owned'):assert events==[]
    if fault=='create_failure':assert terminal['container_outcome']=='NO_CONTAINER' and terminal['absence_observation']=='ENGINE_404'
    if fault=='unknown_stop':assert terminal['status']=='TERMINATION_UNKNOWN'
    if fault in ('create_failure','unknown_stop'):
        with pytest.raises(ValueError):DispatchJournal(path,'a'*64).claim(*args,expected_generation=0)
