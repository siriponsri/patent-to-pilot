"""Exact complete Graph114 input admission; no model, truncation or resampling."""
from pathlib import Path
import hashlib,json,sys,time
sys.path.insert(0,'/code/src')


def main():
    import resource
    start=time.monotonic();cpu=time.process_time()
    receipt={'status':'INCOMPLETE','model_calls':0,'gpu_seconds':0,'units':[],'retry':False}
    try:
        raw=Path('/declaration.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise RuntimeError('declaration mismatch')
        d=json.loads(raw)
        if d['kind']!='graph-input' or d['wall_seconds']!=600:raise RuntimeError('Graph input scope')
        inputs={}
        for name,expected in d['input_sha256'].items():
            if name not in ('sources-private.jsonl','source-sample.json','alias-sample.json'):raise RuntimeError('unexpected input')
            raw=(Path('/input')/name).read_bytes()
            if len(raw)>64*1024**2 or hashlib.sha256(raw).hexdigest()!=expected:raise RuntimeError('fixed Graph input differs')
            inputs[name]=raw
        if len(inputs)!=3:raise RuntimeError('missing fixed Graph input')
        from patent_to_pilot.research.sg_r6_manifest import build_manifest,preflight_graph
        from patent_to_pilot.research.mtm_runtime import InputBoundaryError
        from patent_to_pilot.research.r6_backend import R6Backend
        from transformers import AutoTokenizer
        identity_raw=Path('/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json').read_bytes()
        if hashlib.sha256(identity_raw).hexdigest()!=d['identity_sha256']:raise RuntimeError('identity receipt changed')
        identity=json.loads(identity_raw)
        for name in ['tokenizer.json','tokenizer_config.json','config.json']:
            if hashlib.sha256((Path('/models/qwen3-8b')/name).read_bytes()).hexdigest()!=identity['files'][name]['sha256']:
                raise RuntimeError('tokenizer changed')
        manifest=build_manifest([json.loads(line) for line in inputs['sources-private.jsonl'].splitlines()],
            json.loads(inputs['source-sample.json']),json.loads(inputs['alias-sample.json']))
        tokenizer=AutoTokenizer.from_pretrained('/models/qwen3-8b',local_files_only=True)
        backend=R6Backend(tokenizer=tokenizer,output_root=Path('/out'),lmfe_source_sha256=d['lmfe_source_sha256'])
        with Path('/out/coverage-private.json').open('x') as f:json.dump(manifest['coverage'],f)
        total_bytes=0
        def admission(index):
            if time.monotonic()-start>500:raise TimeoutError('Graph input preflight shutdown margin')
        def persist(index,prepared):
            nonlocal total_bytes
            raw=json.dumps(prepared,ensure_ascii=False,sort_keys=True).encode();total_bytes+=len(raw)
            if total_bytes>60*1024**2:raise RuntimeError('private prepared request size ceiling')
            with (Path('/out')/f'request-{index:03}-private.json').open('xb') as f:f.write(raw)
        receipt.update(preflight_graph(manifest,count_tokens=backend.count_tokens,write_request=persist,check_admission=admission))
        receipt['prepared_request_bytes']=total_bytes
    except BaseException as error:
        receipt.update(status='FAILED_INPUT_PREFLIGHT',exception_type=type(error).__name__,reason=str(error)[:200]);raise
    finally:
        receipt.update(wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
            worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with Path('/out/receipt.json').open('x') as f:json.dump(receipt,f,indent=2)


if __name__=='__main__':main()
