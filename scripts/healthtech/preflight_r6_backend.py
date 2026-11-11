"""Approved CPU-only qualification of the actual R6 factory; no model loading."""
from pathlib import Path
import hashlib,json,sys,time
sys.path.insert(0,'/code/src')


def main():
    import resource
    start=time.monotonic();cpu=time.process_time();receipt={'status':'INCOMPLETE','model_calls':0,'gpu_seconds':0,'cases':[],'retry':False}
    try:
        raw=Path('/declaration.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise RuntimeError('declaration mismatch')
        d=json.loads(raw)
        if d['kind'] not in ('profile','critic') or d['wall_seconds']!=600:raise RuntimeError('qualification scope')
        identity_raw=Path('/code/docs/healthtech/audits/ptp-method-first-r2-weights-20261110/identity.json').read_bytes()
        if hashlib.sha256(identity_raw).hexdigest()!=d['identity_sha256']:raise RuntimeError('identity receipt changed')
        identity=json.loads(identity_raw)
        for name in ['tokenizer.json','tokenizer_config.json','config.json']:
            if hashlib.sha256((Path('/models/qwen3-8b')/name).read_bytes()).hexdigest()!=identity['files'][name]['sha256']:
                raise RuntimeError('tokenizer identity changed')
        from transformers import AutoTokenizer
        from jsonschema.exceptions import ValidationError
        from patent_to_pilot.research.r6_backend import R6Backend
        from patent_to_pilot.research.r6_qualification import matrix,validate_contract
        from patent_to_pilot.research.mtm_runtime import InputBoundaryError
        cases=matrix(d['kind'])
        digest=hashlib.sha256(json.dumps(cases,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if digest!=d['fixture_sha256']:raise RuntimeError('authored qualification matrix changed')
        tokenizer=AutoTokenizer.from_pretrained('/models/qwen3-8b',local_files_only=True)
        if type(tokenizer).__name__!='Qwen2TokenizerFast':raise RuntimeError('tokenizer class changed')
        backend=R6Backend(tokenizer=tokenizer,output_root=Path('/out'),lmfe_source_sha256=d['lmfe_source_sha256'])
        for index,case in enumerate(cases):
            if time.monotonic()-start>500:raise TimeoutError('qualification shutdown margin')
            case_start=time.monotonic()
            result=backend.qualify(case['name'],case['prepared']['schema'],case['prepared']['messages'],case['text'])
            try:validate_contract(case);contract=True
            except (InputBoundaryError,ValidationError,UnicodeError,json.JSONDecodeError):contract=False
            row={'case':case['name'],**result,'contract_valid':contract,
                'expected_schema':case['expected_schema'],'expected_contract':case['expected_contract'],
                'case_wall_seconds':time.monotonic()-case_start,
                'matches':result['input_tokens']<=8192 and result['accepted']==case['expected_schema']
                    and contract==case['expected_contract'] and (case['expected_schema'] or
                    result['reason'] in ('TOKEN_NOT_ALLOWED','EOS_NOT_ALLOWED','SCHEMA_EOS_REJECTED'))}
            receipt['cases'].append(row)
            with (Path('/out')/f'case-{index:03}.json').open('x') as f:json.dump(row,f,indent=2)
        receipt['status']='PASS_SHARED_R6_GRAMMAR_CPU' if all(r['matches'] for r in receipt['cases']) else 'FAIL_SHARED_R6_GRAMMAR_CPU'
    except BaseException as error:
        receipt.update(status='FAILED_PREFLIGHT_NO_MODEL',exception_type=type(error).__name__,reason=str(error)[:250]);raise
    finally:
        receipt.update(wall_seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu,
            worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with Path('/out/receipt.json').open('x') as f:json.dump(receipt,f,indent=2)


if __name__=='__main__':main()
