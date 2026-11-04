"""Posthoc diagnostic on existing DAPFAM rankings; no model/network execution."""
from pathlib import Path
import importlib.util,json,math,hashlib,time,datetime,collections
import pyarrow.parquet as pq
import pyarrow as pa
pa.set_cpu_count(4)
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('--repo',type=Path,required=True)
parser.add_argument('--historical-worktree',type=Path,required=True)
parser.add_argument('--data-root',type=Path,required=True)
parser.add_argument('--duckdb',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
root=args.output.resolve();root.mkdir(parents=True,exist_ok=False)
repo=args.repo.resolve();old=args.historical_worktree.resolve();data=args.data_root.resolve()
spec=importlib.util.spec_from_file_location('coverage',repo/'scripts/healthtech/analyze_dapfam_coverage.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
db=args.duckdb.resolve()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
started=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.perf_counter()
ids={str(r['query_id']) for r in mod.duckdb_json(db,f"SELECT query_id FROM read_parquet('{mod.sql_literal(data/'queries.parquet')}') AS q WHERE {mod.screening_expression('q',mod.LEXICON['medical_device'])}")}
assert len(ids)==96
qrels=collections.defaultdict(dict)
for row in pq.read_table(data/'qrels_all.parquet').to_pylist():
 if str(row['query_id']) in ids:qrels[str(row['query_id'])][str(row['relevant_id'])]=float(row['relevance_score'])
assert set(qrels)==ids
results=[];sources=[]
for model in ['patembed','e5']:
 d=old/'results/healthtech'/('ht-transformer-eval-20261031-'+model)
 summary=json.loads((d/'summary.json').read_text());rankings=collections.defaultdict(dict)
 for line in (d/'rankings.jsonl').read_text().splitlines():
  row=json.loads(line)
  if row['query_id'] in ids:rankings[row['method']][row['query_id']]=row['ranked_ids']
 sources.append({'model':summary['model'],'code_revision':summary['code_revision'],'created_at_utc':summary['created_at_utc'],'rankings_sha256':sha(d/'rankings.jsonl'),'summary_sha256':sha(d/'summary.json')})
 for method,pred in rankings.items():
  recalls=[];ndcgs=[];hit=positive=missing=dup=0
  for q in sorted(ids):
   ranked=pred.get(q,[]);dup+=len(ranked)-len(set(ranked));missing+=q not in pred
   rank=list(dict.fromkeys(ranked))[:100];pos={d for d,v in qrels[q].items() if v>0}
   h=len(pos&set(rank));hit+=h;positive+=len(pos);recalls.append(h/len(pos) if pos else 0)
   dcg=sum((2**qrels[q].get(d,0)-1)/math.log2(i+2) for i,d in enumerate(rank))
   ideal=sum(1/math.log2(i+2) for i in range(min(100,len(pos))))
   ndcgs.append(dcg/ideal if ideal else 0)
  results.append({'model':model,'method':method,'queries':len(ids),'positive_pairs':positive,'hits_at_100':hit,'macro_recall_at_100':sum(recalls)/len(ids),'micro_recall_at_100':hit/positive,'macro_ndcg_at_100':sum(ndcgs)/len(ids),'missing_queries':missing,'duplicate_rank_ids':dup})
out={'status':'PASS_POSTHOC_CORRECTED_QUERY_SCREEN_DIAGNOSTIC','started_utc':started,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'wall_seconds':time.perf_counter()-tick,'definition':'96 query-side lexical medical screen only; full 45336 candidate universe and ALL supplied positives for selected queries; saved top100 unchanged; self matches retained per historical protocol','selection':'POSTHOC_NOT_FINAL_HOLDOUT_OR_SEMANTIC_DEVICE_GOLD','model_inference':'NOT_RUN_EXISTING_RANKINGS_REEVALUATED','qrels_sha256':sha(data/'qrels_all.parquet'),'query_membership_sha256':hashlib.sha256('\n'.join(sorted(ids)).encode()).hexdigest(),'source_rankings':sources,'results':results,'provider_calls':0,'paid_cost_usd':0,'gpu_jobs':0}
(root/'medical-subset-results.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out))
