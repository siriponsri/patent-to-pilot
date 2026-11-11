import copy
import importlib.util
import json
from pathlib import Path
import sys
import pytest

SCRIPTS=Path(__file__).parents[1]/'scripts/healthtech'
sys.path.insert(0,str(SCRIPTS))
from r3_engine_client import Engine, EngineError
from supervise_r3_engine_v2 import configuration, validate_isolation, supervise, GPU


class Connection:
    status=200
    raw=b'{}'
    closed=False
    def __init__(self,*args,**kwargs):pass
    def request(self,*args,**kwargs):pass
    def getresponse(self):return self
    def read(self,limit):return self.raw[:limit]
    def close(self):type(self).closed=True


def test_transport_closes_on_http_failure():
    class Fail(Connection):status=403
    with pytest.raises(EngineError) as error:Engine(Fail).request('GET','/version')
    assert error.value.status==403 and Fail.closed


def test_transport_rejects_oversized_response():
    class Large(Connection):raw=b'x'*(4*1024*1024+1)
    with pytest.raises(RuntimeError,match='cap'):Engine(Large).request('GET','/version')
    assert Large.closed


@pytest.mark.parametrize('minimum,maximum,ok',[('1.40','1.56',True),('1.48','1.56',False),('1.40','1.46',False)])
def test_api_version_gate(minimum,maximum,ok):
    class Version(Connection):
        raw=json.dumps({'Version':'example','MinAPIVersion':minimum,'ApiVersion':maximum}).encode()
    if ok:assert Engine(Version).check_version()['ApiVersion']==maximum
    else:
        with pytest.raises(RuntimeError):Engine(Version).check_version()


def state_for(config,mounts,running=False):
    return {'Image':config['Image'],'Config':copy.deepcopy(config),'HostConfig':copy.deepcopy(config['HostConfig']),
            'Mounts':[{'Type':'bind','Source':str(s),'Destination':t,'RW':not ro} for s,t,ro in mounts],
            'State':{'Running':running,'ExitCode':0}}


@pytest.mark.parametrize('kind',['census','smoke'])
def test_exact_isolation_and_no_socket_mount(kind,tmp_path):
    config,mounts=configuration(kind,tmp_path,10,'a'*64)
    state=state_for(config,mounts)
    validate_isolation(state,config,mounts)
    targets={t for _,t,_ in mounts}
    assert not any(x in target for target in targets for x in ['docker.sock','queries','qrels','test'])
    if kind=='census':
        assert '/input/corpus.jsonl' in targets and not config['HostConfig'].get('DeviceRequests')
    else:assert config['HostConfig']['DeviceRequests'][0]['DeviceIDs']==[GPU]
    for key,value in [('Memory',0),('NetworkMode','host'),('ReadonlyRootfs',False),('NanoCpus',0)]:
        broken=copy.deepcopy(state);broken['HostConfig'][key]=value
        with pytest.raises(RuntimeError):validate_isolation(broken,config,mounts)
    broken=copy.deepcopy(state);broken['Mounts'].append({'Type':'bind','Source':'/','Destination':'/host','RW':False})
    with pytest.raises(RuntimeError):validate_isolation(broken,config,mounts)


def test_terminal_without_attach_client(tmp_path):
    config,mounts=configuration('census',tmp_path,100,'a'*64)
    class Fake:
        calls=[]
        def request(self,method,path,payload=None):self.calls.append((method,path))
        def inspect(self,name):return state_for(config,mounts)
    fake=Fake();out=tmp_path/'out';out.mkdir()
    reason,state=supervise(fake,'owned',config,mounts,100,out,clock=lambda:0)
    assert reason=='TERMINAL' and len(fake.calls)==2
    assert (tmp_path/'isolation.json').exists()


def test_timeout_stops_owned_job(tmp_path):
    config,mounts=configuration('census',tmp_path,100,'a'*64)
    class Fake:
        stopped=False
        def request(self,*args):pass
        def inspect(self,name):return state_for(config,mounts,True)
        def terminate(self,name):self.stopped=True;return state_for(config,mounts)
    fake=Fake();out=tmp_path/'out';out.mkdir()
    reason,_=supervise(fake,'owned',config,mounts,100,out,clock=lambda:101)
    assert reason=='TIMEOUT' and fake.stopped


def test_isolation_failure_never_starts(tmp_path):
    config,mounts=configuration('census',tmp_path,100,'a'*64)
    class Fake:
        calls=[]
        def request(self,method,path,payload=None):self.calls.append(path)
        def inspect(self,name):
            state=state_for(config,mounts);state['HostConfig']['NetworkMode']='host';return state
    fake=Fake();out=tmp_path/'out';out.mkdir()
    with pytest.raises(RuntimeError):supervise(fake,'owned',config,mounts,100,out)
    assert not any(p.endswith('/start') for p in fake.calls)


def test_lost_stop_response_kills_and_reobserves():
    class Fake(Engine):
        killed=False
        checks=0
        def request(self,method,path,payload=None,**kwargs):
            if '/stop?' in path:raise TimeoutError()
            if path.endswith('/kill'):self.killed=True
        def inspect(self,name):
            self.checks+=1
            return {'State':{'Running':not self.killed}}
    e=Fake();assert not e.terminate('owned')['State']['Running']
    assert e.killed and e.checks==2


def test_unknown_termination_never_claims_stopped():
    class Fake(Engine):
        def request(self,*args,**kwargs):raise TimeoutError()
        def inspect(self,name):raise TimeoutError()
    with pytest.raises(TimeoutError):Fake().terminate('owned')
