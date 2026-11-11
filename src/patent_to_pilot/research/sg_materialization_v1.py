"""Bounded deterministic R2 artifacts and prospective pair-key review sample.

No model, evaluator, database, accepted edge or retrieval operation.
"""
import hashlib,itertools,json,time
from pathlib import Path
from .mtm_runtime import InputBoundaryError
from .sg_relations_v2 import extract_family_v2
from .sg_census_runner import config_hash
from .sg_signature_census import SignatureCensus

SALT='ptp-sg-r4-full-alias-v1-20261111|'
def encoded(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def select_pairs(representatives,limit=100,max_pairs=18326):
    ranked=[];count=0
    for key,members in sorted(representatives.items()):
        for left,right in itertools.combinations(sorted(members),2):
            count+=1
            if count>max_pairs:raise InputBoundaryError('pair-key incidence cap exceeded')
            canonical=json.dumps([key,left,right],ensure_ascii=False,separators=(',',':'))
            digest=hashlib.sha256((SALT+canonical).encode()).hexdigest()
            ranked.append((digest,canonical,{'alias_key':key,'families':[left,right],
                'relation_ids':[members[left],members[right]],'sampling_sha256':digest}))
    ranked.sort(key=lambda row:(row[0],row[1]))
    return [row[2] for row in ranked[:limit]],count

def materialize(source,destination,*,expected_sha256,expected_config_sha256,expected_families,
                sample_ids,expected_counts,max_seconds=1560,max_input_bytes=328999080,
                max_output_bytes=128*1024**2,max_pairs=18326,clock=time.monotonic):
    out=Path(destination);out.mkdir(exist_ok=False);start=clock();written=0
    receipt={'status':'INCOMPLETE','model_calls':0,'gpu_seconds':0,'accepted_edges':0,'retry':False,'families_processed':0}
    census=SignatureCensus(max_families=expected_families,max_records=expected_families*8)
    reps={};source_sample={};selected={};seen_sample=set()
    def check():
        if clock()-start>=max_seconds:raise TimeoutError('materialization deadline')
    def save(name,value):
        nonlocal written
        raw=encoded(value)+b'\n'
        if written+len(raw)>max_output_bytes-16384:raise InputBoundaryError('artifact byte cap')
        with (out/name).open('xb') as handle:handle.write(raw)
        written+=len(raw)
    try:
        if config_hash()!=expected_config_sha256:raise InputBoundaryError('extractor config changed')
        if len(set(sample_ids))!=len(sample_ids):raise InputBoundaryError('duplicate fixed source sample ID')
        sample_ids=set(sample_ids);digest=hashlib.sha256();size=0
        with Path(source).open('rb') as stream:
            while chunk:=stream.read(1024**2):
                check();size+=len(chunk)
                if size>max_input_bytes:raise InputBoundaryError('input byte cap')
                digest.update(chunk)
            if digest.hexdigest()!=expected_sha256:raise InputBoundaryError('source identity mismatch')
            stream.seek(0);second=hashlib.sha256()
            with (out/'relations.jsonl').open('xb') as target:
                while raw:=stream.readline(8*1024**2+1):
                    check()
                    if len(raw)>8*1024**2:raise InputBoundaryError('input line cap')
                    second.update(raw);family=extract_family_v2(json.loads(raw));fid=family['family_id'];records=family['records']
                    census.add_family(fid,records);receipt['families_processed']+=1
                    if fid in sample_ids:
                        seen_sample.add(fid);source_sample[fid]=records
                    for record in records:
                        key,rid=record['alias_key'],record['relation_id']
                        members=reps.setdefault(key,{})
                        members[fid]=min(members.get(fid,rid),rid)
                        line=encoded(record)+b'\n'
                        if written+len(line)>max_output_bytes-16384:raise InputBoundaryError('artifact byte cap')
                        target.write(line);written+=len(line)
            if second.hexdigest()!=expected_sha256:raise InputBoundaryError('source changed during extraction')
        counts=census.summary()
        if receipt['families_processed']!=expected_families or seen_sample!=sample_ids:
            raise InputBoundaryError('incomplete corpus or fixed sample')
        for key,value in expected_counts.items():
            actual=counts[key]
            if key=='family_frequency_histogram':actual={str(k):v for k,v in actual.items()}
            if actual!=value:raise InputBoundaryError('census reproduction mismatch: '+key)
        pairs,total=select_pairs(reps,max_pairs=max_pairs);needed={rid for pair in pairs for rid in pair['relation_ids']}
        with (out/'relations.jsonl').open('rb') as stream:
            for raw in stream:
                check();record=json.loads(raw)
                if record['relation_id'] in needed:selected[record['relation_id']]=record
        if set(selected)!=needed:raise InputBoundaryError('missing sampled witness')
        save('postings.json',reps)
        save('source-sample.json',{'records_by_family':source_sample,'no_substitution':True})
        save('alias-sample.json',{'salt':SALT,'population_pair_key_incidences':total,'sample':pairs,
             'witness_records':selected,'representative_policy':'MIN_RELATION_ID_PER_FAMILY_KEY',
             'limitation':'Sample witnesses do not certify other relations of the same family/key or compatibility.',
             'uses_queries_qrels_retrieval_scores':False})
        receipt.update(status='COMPLETE_UNSCREENED_ARTIFACTS_NO_EDGES',counts=counts,
            source_sample_count=len(source_sample),alias_sample_count=len(pairs),config_sha256=expected_config_sha256,
            corpus_sha256=expected_sha256,artifact_bytes=written)
        check()
    except BaseException as e:
        receipt.update(status='FAILED_NO_RETRY',exception_type=type(e).__name__)
        raise
    finally:
        receipt.update(wall_seconds=clock()-start,partial_artifact_bytes=written)
        with (out/'receipt.json').open('x') as f:json.dump(receipt,f,indent=2)
    return receipt
