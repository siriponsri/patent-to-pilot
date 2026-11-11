from pathlib import Path
import sys,json,hashlib
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts/healthtech'))
from run_sg_r6_source_attachment import execute
from supervise_sg_r6_source_attachment import source_configuration
from test_sg_r6_manifest import fixture
from patent_to_pilot.research.sg_r6_manifest import fixed_union


def prepare(tmp_path):
    rows,sample,aliases=fixture();inputs=tmp_path/'input';inputs.mkdir();out=tmp_path/'out';out.mkdir()
    for name,value in [('source-sample.json',sample),('alias-sample.json',aliases)]:
        (inputs/name).write_text(json.dumps(value))
    (inputs/'corpus.jsonl').write_bytes(b''.join(json.dumps(r).encode()+b'\n' for r in rows))
    d={'run_id':'ptp-sg-r6-source-attachment-20261111-v1','wall_seconds':1800,'model_calls':0,
        'fixed_ids_sha256':hashlib.sha256(json.dumps(fixed_union(sample,aliases),separators=(',',':')).encode()).hexdigest()}
    for name,key in [('source-sample.json','source_sample_sha256'),('alias-sample.json','alias_sample_sha256'),('corpus.jsonl','corpus_sha256')]:
        d[key]=hashlib.sha256((inputs/name).read_bytes()).hexdigest()
    return d,inputs,out


def test_real_worker_entry_function_joins_authored282_once(tmp_path):
    d,i,o=prepare(tmp_path);r=execute(d,input_root=i,output_root=o)
    assert r['source_units']==282 and r['model_calls']==0 and r['worker_cpu_seconds']>=0
    with pytest.raises(FileExistsError):execute(d,input_root=i,output_root=o)


@pytest.mark.parametrize('key',['source_sample_sha256','alias_sample_sha256','fixed_ids_sha256'])
def test_changed_fixed_inputs_fail_before_corpus_dispatch(tmp_path,key):
    d,i,o=prepare(tmp_path);d[key]='0'*64
    with pytest.raises(RuntimeError):execute(d,input_root=i,output_root=o)
    assert not (o/'data-operation-dispatch.json').exists()


def test_source_container_mounts_only_approved_inputs_and_no_gpu():
    c,mounts=source_configuration(Path('/job'),100,'a'*64);h=c['HostConfig']
    assert h['NanoCpus']==1_000_000_000 and h['Memory']==1536*1024**2
    assert h['NetworkMode']=='none' and h['ReadonlyRootfs'] and not h.get('DeviceRequests')
    assert {t for _,t,_ in mounts if t.startswith('/input/')}=={'/input/corpus.jsonl','/input/source-sample.json','/input/alias-sample.json'}
    assert all(ro for _,t,ro in mounts if t.startswith('/input/'))
    assert c['Cmd'][1].endswith('/run_sg_r6_source_attachment.py')
