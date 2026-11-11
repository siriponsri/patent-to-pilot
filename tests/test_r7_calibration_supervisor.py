import copy
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).parents[1]/'scripts/healthtech'))
from supervise_r7_calibration import configuration,supervise,GPU
from supervise_sacr_r5_engine import validate_isolation
from test_r3_engine_packaging import state_for


def test_exact_calibration_mounts_keep_data_and_socket_out(tmp_path):
    config,mounts=configuration(tmp_path,100,'a'*64)
    validate_isolation(state_for(config,mounts),config,mounts)
    targets={target for _,target,_ in mounts}
    assert targets=={'/code','/out','/dispatch','/deps','/models/qwen3-8b','/models/.'+GPU+'.lock'}
    assert dict((target,readonly) for _,target,readonly in mounts)['/dispatch']
    assert config['Cmd']==['-s','/code/scripts/healthtech/run_r7_calibration.py','100','a'*64]
    assert config['HostConfig']['NanoCpus']==8_000_000_000
    assert config['HostConfig']['Memory']==31*1024**3
    assert config['HostConfig']['DeviceRequests'][0]['DeviceIDs']==[GPU]


@pytest.mark.parametrize('fault',['network','mount','command','device','memory'])
def test_actual_supervision_never_starts_invalid_calibration_isolation(tmp_path,fault):
    config,mounts=configuration(tmp_path,100,'a'*64)
    class Engine:
        calls=[]
        def request(self,method,path,payload=None):self.calls.append(path)
        def inspect(self,name):
            state=state_for(config,mounts)
            if fault=='network':state['HostConfig']['NetworkMode']='host'
            if fault=='mount':state['Mounts'].append({'Type':'bind','Source':'/','Destination':'/host','RW':False})
            if fault=='command':state['Config']['Cmd']=['wrong']
            if fault=='device':state['HostConfig']['DeviceRequests']=[]
            if fault=='memory':state['HostConfig']['Memory']=32*1024**3
            return state
    engine=Engine();out=tmp_path/'out';out.mkdir()
    with pytest.raises(RuntimeError):supervise(engine,'authored',config,mounts,100,out)
    assert not any(path.endswith('/start') for path in engine.calls)


def test_calibration_timeout_returns_authoritative_terminal_state(tmp_path):
    config,mounts=configuration(tmp_path,100,'a'*64)
    class Engine:
        stopped=False
        def request(self,*args):pass
        def inspect(self,name):return state_for(config,mounts,True)
        def terminate(self,name):
            self.stopped=True
            return state_for(config,mounts,False)
    engine=Engine();out=tmp_path/'out';out.mkdir()
    reason,state=supervise(engine,'authored',config,mounts,100,out,clock=lambda:101)
    assert reason=='TIMEOUT' and engine.stopped and not state['State']['Running']
