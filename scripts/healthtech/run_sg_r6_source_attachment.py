"""One approved fixed282 join; no extraction, query, labels or model loading."""
from pathlib import Path
import hashlib,json,sys,time
sys.path.insert(0,'/code/src')
from patent_to_pilot.research.sg_r6_source_attachment import attach_fixed282_sources
from patent_to_pilot.research.sg_r6_manifest import fixed_union


def execute(declaration,*,input_root,output_root):
    d=declaration;start=time.monotonic();cpu=time.process_time()
    fixture=d['run_id']=='ptp-sg-r6-source-fixture-20261111-v1'
    if (d['run_id'] not in ('ptp-sg-r6-source-attachment-20261111-v1','ptp-sg-r6-source-fixture-20261111-v1')
            or d['wall_seconds']!=(120 if fixture else 1800) or d['model_calls']!=0
            or d.get('input_kind')!=('AUTHORED_FIXTURE' if fixture else 'NATIVE_FIXED282')):
        raise RuntimeError('R6 source join declaration mismatch')
    inputs={}
    for name,key in [('source-sample.json','source_sample_sha256'),('alias-sample.json','alias_sample_sha256')]:
        raw=(input_root/name).read_bytes()
        if len(raw)>16*1024**2 or hashlib.sha256(raw).hexdigest()!=d[key]:raise RuntimeError('fixed sample hash/size mismatch')
        inputs[name]=json.loads(raw)
    ids=fixed_union(inputs['source-sample.json'],inputs['alias-sample.json'])
    id_hash=hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()
    if id_hash!=d['fixed_ids_sha256']:raise RuntimeError('fixed282 identity mismatch')
    with (output_root/'data-operation-dispatch.json').open('x') as f:
        json.dump({'status':'SOURCE_JOIN_DISPATCH_INTENT','retry':False,'fixed_ids_sha256':id_hash},f)
    result=attach_fixed282_sources(input_root/'corpus.jsonl',output_root/'private-source-attachment',
        expected_sha256=d['corpus_sha256'],fixed_ids=ids,max_seconds=60 if fixture else 1500)
    return {**result,'worker_wall_seconds':time.monotonic()-start,'worker_cpu_seconds':time.process_time()-cpu,
        'semantic_fidelity':'NOT_ASSESSED','model_calls':0,'gpu_seconds':0}


def main():
    import resource
    start=time.monotonic();cpu=time.process_time();receipt={'status':'INCOMPLETE','retry':False}
    try:
        raw=Path('/declaration.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise RuntimeError('declaration hash mismatch')
        receipt=execute(json.loads(raw),input_root=Path('/input'),output_root=Path('/out'))
    except BaseException as error:
        receipt.update(status='FAILED_NO_RETRY',exception_type=type(error).__name__);raise
    finally:
        receipt.update(whole_worker_wall_seconds=time.monotonic()-start,whole_worker_cpu_seconds=time.process_time()-cpu,
            worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with Path('/out/receipt.json').open('x') as f:json.dump(receipt,f,indent=2)


if __name__=='__main__':main()
