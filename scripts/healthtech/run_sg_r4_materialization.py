from pathlib import Path
import json,hashlib,sys
sys.path.insert(0,'/code/src')
from patent_to_pilot.research.sg_materialization_v1 import materialize
def main():
    raw=Path('/declaration.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=sys.argv[1]:raise RuntimeError('declaration mismatch')
    d=json.loads(raw);sample_raw=Path('/source-sample.json').read_bytes()
    if hashlib.sha256(sample_raw).hexdigest()!=d['sample_sha256']:raise RuntimeError('fixed sample mismatch')
    sample=json.loads(sample_raw)
    if sample['corpus_sha256']!=d['corpus_sha256'] or sample['uses_qrels'] or sample['uses_retrieval_scores']:
        raise RuntimeError('sample source boundary mismatch')
    ids=[row['id'] for row in sample['sample']]
    if len(ids)!=100:raise RuntimeError('source cohort changed')
    materialize('/corpus.jsonl','/out/attempt',expected_sha256=d['corpus_sha256'],
       expected_config_sha256=d['config_sha256'],expected_families=45336,sample_ids=ids,
       expected_counts=d['expected_census_counts'],max_input_bytes=328999080,max_pairs=18326,
       max_seconds=1560,max_output_bytes=128*1024**2)
if __name__=='__main__':main()
