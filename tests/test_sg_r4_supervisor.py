from pathlib import Path
import sys,copy
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'scripts/healthtech'))
from supervise_sg_r4_materialization import job_configuration
from supervise_r3_engine_v2 import validate_isolation
from test_r3_engine_packaging import state_for
def test_cpu_corpus_sample_boundary(tmp_path):
    config,mounts=job_configuration(tmp_path,'a'*64)
    targets={t for _,t,_ in mounts}
    assert targets=={'/code','/out','/declaration.json','/corpus.jsonl','/source-sample.json'}
    assert config['HostConfig']['NanoCpus']==1_000_000_000
    assert config['HostConfig']['Memory']==1536*1024**2
    assert not config['HostConfig'].get('DeviceRequests')
    assert config['HostConfig']['Ulimits'][0]['Hard']==128*1024**2
    validate_isolation(state_for(config,mounts),config,mounts)
def test_extra_mount_or_gpu_rejected(tmp_path):
    config,mounts=job_configuration(tmp_path,'a'*64)
    state=state_for(config,mounts)
    state['Mounts'].append({'Type':'bind','Source':'/private','Destination':'/extra','RW':False})
    with pytest.raises(RuntimeError):validate_isolation(state,config,mounts)
    state=state_for(config,mounts);state['HostConfig']['DeviceRequests']=[{'Count':-1}]
    with pytest.raises(RuntimeError):validate_isolation(state,config,mounts)
