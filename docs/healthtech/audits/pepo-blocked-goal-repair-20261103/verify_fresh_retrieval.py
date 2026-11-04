"""Offline independent verification of saved vectors/rankings; no model or API."""
from pathlib import Path
import argparse,hashlib,json,math
import numpy as np

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--references',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    reported=json.loads((args.run/'fresh-retrieval-evaluation.json').read_text())
    rankings=json.loads((args.run/'rankings.json').read_text())
    receipt=json.loads((args.run/'gpu-compute-receipt.json').read_text())
    assert hashlib.sha256(args.references.read_bytes()).hexdigest()==reported['evaluator_sha256']
    gold=json.loads(args.references.read_text())['references']
    rows=[]
    for item in reported['method_rows']:
        method=item['method'];per=[];hits=0;denom=0
        for query,ranking in rankings[method].items():
            assert len(ranking)==len(set(ranking))==20
            rel=set(gold[query]);found=len(rel.intersection(ranking));hits+=found;denom+=len(rel)
            dcg=sum(1/math.log2(rank+2) for rank,doc in enumerate(ranking) if doc in rel)
            ideal=sum(1/math.log2(rank+2) for rank in range(min(len(rel),20)))
            per.append((found/len(rel),dcg/ideal))
        values={'macro_recall_at_20':sum(x[0] for x in per)/len(per),'micro_recall_at_20':hits/denom,
                'macro_ndcg_at_20':sum(x[1] for x in per)/len(per)}
        delta=max(abs(values[k]-item[k]) for k in values)
        assert hits==item['hits_total'] and denom==item['positive_denominator']==61 and delta<1e-12
        rows.append({'method':method,'hits':hits,'denominator':denom,'values':values,'max_abs_delta':delta})
    dense=[]
    for model in receipt['models']:
        kind=model['kind'];roles={row['role']:row for row in model['roles']}
        corpus=np.load(args.run/(kind+'-passage.npy'),allow_pickle=False)
        queries=np.load(args.run/(kind+'-query.npy'),allow_pickle=False)
        assert corpus.shape==(41,768) and queries.shape==(3,768)
        assert np.isfinite(corpus).all() and np.isfinite(queries).all()
        assert np.allclose(np.linalg.norm(corpus,axis=1),1,atol=1e-5)
        assert np.allclose(np.linalg.norm(queries,axis=1),1,atol=1e-5)
        for query_id,scores in zip(roles['query']['document_ids'],queries@corpus.T):
            ids=roles['passage']['document_ids']
            order=sorted(range(len(ids)),key=lambda i:(-float(scores[i]),ids[i]))[:20]
            assert [ids[i] for i in order]==rankings[kind+'-dense'][query_id]
        dense.append({'model':kind,'rankings_match_saved_vectors':True,'queries':len(queries)})
    output={'status':'VERIFIED_SAVED_VECTORS_RANKINGS_AND_METRICS','tolerance':1e-12,
            'metrics':rows,'dense_recomputation':dense,'provider_calls':0,'gpu_jobs':0,
            'scope':'Three-case development diagnostic; unlisted patents remain unjudged; no final-holdout or causal improvement claim'}
    args.output.write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'status':output['status'],'methods':len(rows),'dense_queries':6,'max_abs_delta':max(r['max_abs_delta'] for r in rows)}))

if __name__=='__main__':main()
