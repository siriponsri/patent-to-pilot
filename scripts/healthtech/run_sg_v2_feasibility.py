"""One declared label-free100-family S/G candidate run; no model/Neo4j calls."""
import hashlib
import itertools
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src'))
from patent_to_pilot.research.sg_relations_v2 import CONFIG,extract_family_v2

PRIVATE=ROOT.parent/'_private_artifacts/healthtech'
CORPUS=PRIVATE/'ptp-dapfam-native-dev-20261110-v3/runtime-dev/corpus.jsonl'
SAMPLE=PRIVATE/'ptp-sg-sample-20261110/sample.json'
OUTPUT=SAMPLE.parent/'feasibility-v2'
AUDIT=ROOT/'docs/healthtech/audits/ptp-sg-feasibility-r2-20261111'


def sha(raw): return hashlib.sha256(raw).hexdigest()


def run(progress):
    start=time.monotonic()
    d=json.loads((AUDIT/'declaration.json').read_bytes())
    if d['config']!=CONFIG or d['code_sha256']!=sha((ROOT/'src/patent_to_pilot/research/sg_relations_v2.py').read_bytes()):
        raise RuntimeError('declared extractor changed')
    if d['runner_sha256']!=sha(Path(__file__).read_bytes()): raise RuntimeError('declared runner changed')
    raw=SAMPLE.read_bytes()
    if sha(raw)!=d['sample_sha256']: raise RuntimeError('sample changed')
    sample=json.loads(raw)
    ids={r['id'] for r in sample['sample']}
    if len(ids)!=100 or sample['corpus_sha256']!=d['corpus_sha256']:
        raise RuntimeError('fixed sample identity mismatch')
    OUTPUT.mkdir(exist_ok=False)
    progress.update(stage='CORPUS_SCAN',output_created=True)
    results=[]; h=hashlib.sha256(); corpus_count=0
    with CORPUS.open('rb') as f:
        for line in f:
            if time.monotonic()-start>120: raise TimeoutError('bounded feasibility expired')
            h.update(line); row=json.loads(line); corpus_count+=1
            if row['id'] in ids: results.append(extract_family_v2(row))
            progress.update(corpus_rows=corpus_count,selected_families=len(results))
    if h.hexdigest()!=d['corpus_sha256'] or corpus_count!=45336 or {r['family_id'] for r in results}!=ids or len(results)!=100:
        raise RuntimeError('corpus/sample membership mismatch; do not accept outputs')
    progress['stage']='CANDIDATE_PAIR_ENUMERATION'
    records=[r for family in results for r in family['records']]
    groups={}
    for r in records: groups.setdefault(r['alias_key'],[]).append(r)
    pairs=[]
    for group in groups.values():
        for a,b in itertools.combinations(group,2):
            if a['family_id']==b['family_id']: continue
            key='|'.join(sorted([a['relation_id'],b['relation_id']]))+'|action_operand'
            pairs.append({'key':key,'sampling_sha256':sha(('ptp-sg-alias-sample-v1-20261110|'+key).encode()),
                          'endpoints':sorted([a['relation_id'],b['relation_id']]),
                          'status':'UNSCREENED_CANDIDATE_NOT_EDGE'})
    pairs.sort(key=lambda x:(x['sampling_sha256'],x['key']))
    progress.update(candidate_records=len(records),candidate_pairs=len(pairs),stage='OUTPUT_SERIALIZATION')
    selected=pairs[:100]
    if time.monotonic()-start>120: raise TimeoutError('bounded feasibility expired')
    payload=(json.dumps({'families':results,'sampled_candidate_pairs':selected},ensure_ascii=False,indent=2)+'\n').encode()
    if len(payload)>128*1024**2: raise RuntimeError('output bound exceeded')
    with (OUTPUT/'candidates.json').open('xb') as f: f.write(payload)
    nonempty=sum(not r['empty'] for r in results)
    aggregate={'status':'FAIL_NO_CROSS_FAMILY_CANDIDATES' if not pairs else
        'FAIL_INSUFFICIENT_SOURCE_COVERAGE' if nonempty<10 else 'CANDIDATES_REQUIRE_FIDELITY_SCREENING',
        'sample_families':100,'nonempty_families':nonempty,'empty_families':100-nonempty,
        'records':len(records),'candidate_pairs':len(pairs),'sampled_candidate_pairs':len(selected),
        'accepted_edges':0,'counts':{key:sum(r['counts'][key] for r in results) for key in results[0]['counts']},
        'output_sha256':sha(payload),'private_output_bytes':len(payload),'wall_seconds':time.monotonic()-start,
        'model_calls':0,'gpu_seconds':0,'human_cards_issued':0,'semantic_fidelity':'NOT_ASSESSED',
        'retrieval':'NOT_RUN','protected_test_access':False,'retry':False}
    with (AUDIT/'aggregate.json').open('x') as f: json.dump(aggregate,f,indent=2)
    print(json.dumps(aggregate))


def main():
    # Existing results or failures cannot become an implicit replay.
    if OUTPUT.exists() or (AUDIT/'failure.json').exists() or (AUDIT/'aggregate.json').exists():
        raise FileExistsError('consumed feasibility destination; no retry')
    started=time.monotonic(); progress={'stage':'IDENTITY_CHECK','output_created':False}
    try:
        run(progress)
    except BaseException as error:
        declaration=(AUDIT/'declaration.json').read_bytes()
        d=json.loads(declaration)
        failure={'status':'FAILED_NOT_RETRYABLE','exception_type':type(error).__name__,
            'wall_seconds':time.monotonic()-started,'progress':progress,
            'declaration_sha256':sha(declaration),'sample_sha256':d['sample_sha256'],
            'corpus_sha256':d['corpus_sha256'],'code_sha256':d['code_sha256'],
            'runner_sha256':sha(Path(__file__).read_bytes()),'model_calls':0,'gpu_seconds':0,
            'partial_output':'MAY_EXIST_INSPECT_RETAINED_FILES','retry':False,'semantic_fidelity':'NOT_ASSESSED'}
        with (AUDIT/'failure.json').open('x') as f: json.dump(failure,f,indent=2)
        raise


if __name__=='__main__': main()
