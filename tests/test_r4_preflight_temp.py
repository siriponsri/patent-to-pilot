from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts/healthtech'))
from supervise_r4_preflight_v2 import add_temporary_workspace
from supervise_r3_engine_v2 import configuration,validate_isolation
from test_r3_engine_packaging import state_for
def test_temp_is_memory_bounded_without_writable_host_mount(tmp_path):
    config,mounts=configuration('census',tmp_path,0,'a'*64)
    result=add_temporary_workspace(config)
    assert 'Tmpfs' not in config['HostConfig']
    assert result['HostConfig']['Memory']==config['HostConfig']['Memory']
    assert result['HostConfig']['Mounts']==config['HostConfig']['Mounts']
    assert result['HostConfig']['Tmpfs']=={'/tmp':'rw,nosuid,size=67108864'}
    state=state_for(result,mounts);validate_isolation(state,result,mounts)
    state['HostConfig']['Tmpfs']={}
    with pytest.raises(RuntimeError):validate_isolation(state,result,mounts)
def test_temp_does_not_silently_relax_other_boundaries(tmp_path):
    config,_=configuration('census',tmp_path,0,'a'*64);config['HostConfig']['NetworkMode']='host'
    with pytest.raises(RuntimeError):add_temporary_workspace(config)
