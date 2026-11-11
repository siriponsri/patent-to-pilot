from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/healthtech'))
from supervise_sg_r5_source_attachment import source_configuration


def test_source_join_isolation_and_file_ceiling():
    config,mounts=source_configuration(Path('/fresh-job'),100,'f'*64)
    host=config['HostConfig']
    assert host['NanoCpus']==1_000_000_000 and host['Memory']==1536*1024**2
    assert host['NetworkMode']=='none' and host['ReadonlyRootfs']
    assert not host.get('DeviceRequests')
    assert host['Ulimits']==[{'Name':'fsize','Soft':64*1024**2,'Hard':64*1024**2}]
    assert {target for _,target,_ in mounts}=={'/code','/out','/declaration.json','/input/corpus.jsonl','/input/source-sample.json'}
    assert [target for _,target,readonly in mounts if not readonly]==['/out']
    assert config['Cmd'][1]=='/code/scripts/healthtech/run_sg_r5_source_attachment.py'
