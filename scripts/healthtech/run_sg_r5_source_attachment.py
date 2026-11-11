"""Approved fixed-source join, no extraction/model/evaluator/database."""
from pathlib import Path
import hashlib,json,sys,resource,time
sys.path.insert(0,'/code/src')
from patent_to_pilot.research.sg_fixed_source_attachment import attach_fixed_sources


def main():
    start=time.monotonic();receipt={'status':'INCOMPLETE','model_calls':0,'gpu_seconds':0,'retry':False}
    try:
        raw=Path('/declaration.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise RuntimeError('declaration hash mismatch')
        d=json.loads(raw)
        if d['run_id']!='ptp-sg-r5-source-attachment-20261111-v1':raise RuntimeError('wrong job')
        raw=Path('/input/source-sample.json').read_bytes()
        if hashlib.sha256(raw).hexdigest()!=d['source_sample_sha256']:raise RuntimeError('fixed sample identity mismatch')
        sample=json.loads(raw);ids=sorted(sample['records_by_family'])
        if len(ids)!=100 or sample['no_substitution'] is not True:raise RuntimeError('fixed sample contract')
        with Path('/out/data-operation-dispatch.json').open('x') as f:json.dump({'status':'SOURCE_JOIN_DISPATCH_INTENT','retry':False},f)
        result=attach_fixed_sources('/input/corpus.jsonl','/out/private-source-attachment',
            expected_sha256=d['corpus_sha256'],fixed_ids=ids,max_seconds=1500)
        receipt.update(status=result['status'],source_units=result['source_units'],
            private_output_bytes=result['private_output_bytes'],private_output_sha256=result['private_output_sha256'],
            corpus_sha256=result['corpus_sha256'],extraction='NOT_RUN',semantic_fidelity='NOT_ASSESSED')
    except BaseException as error:
        receipt.update(status='FAILED_NO_RETRY',exception_type=type(error).__name__)
        raise
    finally:
        receipt.update(wall_seconds=time.monotonic()-start,worker_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
        with Path('/out/receipt.json').open('x') as f:json.dump(receipt,f,indent=2)

if __name__=='__main__':main()
