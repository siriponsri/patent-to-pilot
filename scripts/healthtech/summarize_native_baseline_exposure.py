"""Descriptive exposure bins from sealed existing dev metrics; no new retrieval."""
import hashlib
import json
import math
from pathlib import Path
import time

PIN='a1ea06dbb68d9d413c272525a43c596c821475f48479b68fe5fd240dc38fbcf2'


def summarize(data, expected_counts):
    if set(data)!=set(expected_counts): raise ValueError('partition mismatch')
    result={}
    for partition,count in expected_counts.items():
        rows=data[partition]
        if type(rows) is not dict or len(rows)!=count or count<1:
            raise ValueError('eligible denominator changed')
        bins={'1-10':0,'11-100':0,'101-200':0,'not_exposed_at_200':0}
        totals={k:0.0 for k in (10,100,200)}
        for values in rows.values():
            recalls=[values[f'Recall@{k}'] for k in (10,100,200)]
            if any(type(v) not in (int,float) or not math.isfinite(v) or not 0<=v<=1 for v in recalls):
                raise ValueError('invalid recall value')
            if recalls!=sorted(recalls): raise ValueError('recall must be monotonic')
            key='1-10' if recalls[0]>0 else '11-100' if recalls[1]>0 else '101-200' if recalls[2]>0 else 'not_exposed_at_200'
            bins[key]+=1
            for k,v in zip((10,100,200),recalls): totals[k]+=v
        result[partition]={'eligible_queries':count,'first_known_positive_rank_bin':bins,
            'exposed_queries_at_10':bins['1-10'],
            'exposed_queries_at_100':bins['1-10']+bins['11-100'],
            'exposed_queries_at_200':count-bins['not_exposed_at_200'],
            'mean_recall_check':{str(k):round(v/count,5) for k,v in totals.items()}}
    return result


def main():
    started=time.monotonic(); raw=Path('/input/private-per-query.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PIN: raise ValueError('sealed per-query artifact changed')
    result={'status':'DESCRIPTIVE_EXISTING_DEV_METRICS_ONLY',
        'partitions':summarize(json.loads(raw),{'ALL':474,'IN':450,'OUT':349}),
        'input_sha256':PIN,'cutoffs':[10,100,200],
        'limitations':['coarse rank bins inferred from positive recall, not exact ranks',
                       'unexposed means no known positive at cutoff, not semantic irrelevance',
                       'no comparator: paired effects and exposure-rescue comparisons unavailable'],
        'model_calls':0,'gpu_seconds':0,'protected_test_access':False,
        'wall_seconds':time.monotonic()-started}
    with Path('/out/aggregate.json').open('x') as f: json.dump(result,f,indent=2)
    print(json.dumps(result))


if __name__=='__main__': main()
