"""Read-only aggregate DAPFAM audit. No model/provider/network or repo writes."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
import time

sys.dont_write_bytecode = True
repo=Path(r'C:\Users\User\Desktop\myProject\patent-to-pilot')
out=Path(__file__).resolve().parent
duckdb=Path(r'C:\Users\User\AppData\Local\duckdb\cli\2.0.0\duckdb.exe')
data=repo/'methodology/datasets/research-only-nc'
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path)
 obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
coverage=module('coverage_probe',repo/'scripts/healthtech/analyze_dapfam_coverage.py')
bm25=module('bm25_probe',repo/'scripts/healthtech/run_dapfam_bm25.py')
prefix="SET autoinstall_known_extensions=false; SET autoload_known_extensions=false; SET threads=2; SET memory_limit='512MB'; SET temp_directory='"+str(out/'duckdb-temp').replace('\\','/')+"'; SET max_temp_directory_size='256MB'; "
def query(sql):
 r=subprocess.run([str(duckdb),'-no-agent','-json','-c',prefix+sql],capture_output=True,text=True,check=True,timeout=120,cwd=out)
 return json.loads(r.stdout)
c=data/'corpus.parquet';q=data/'queries.parquet';rels=data/'qrels_all.parquet'
started=time.time()
result={'snapshot':'db0798276e3158b04131b4e910abc0a11511e94c','started_unix':started,
 'duckdb_sha256':sha(duckdb),'input_files':{},'counts':query(coverage.build_counts_sql(c,q,rels)),
 'screening':query(coverage.build_screening_sql(c,'c','corpus')+' UNION ALL '+coverage.build_screening_sql(q,'q','queries')),
 'positive_qrels':query(coverage.build_qrel_sql(c,q,rels)),
 'schema':{name:query("DESCRIBE SELECT * FROM read_parquet('"+str(path).replace('\\','/')+"')") for name,path in [('corpus',c),('queries',q),('qrels',rels)]},
 'label_histogram':query("SELECT domain_rel,relevance_score,count(*) n FROM read_parquet('"+str(rels).replace('\\','/')+"') GROUP BY domain_rel,relevance_score ORDER BY domain_rel,relevance_score")}
for name,path in [('corpus',c),('queries',q),('qrels',rels)]:
 result['input_files'][name]={'path':path.relative_to(repo).as_posix(),'bytes':path.stat().st_size,'sha256':sha(path)}
sql="""WITH c AS (SELECT relevant_id FROM read_parquet('{c}')), q AS (SELECT query_id FROM read_parquet('{q}')), r AS (SELECT * FROM read_parquet('{r}')) SELECT (SELECT count(*) FROM r LEFT JOIN c USING (relevant_id) WHERE c.relevant_id IS NULL) missing_targets,(SELECT count(*) FROM r LEFT JOIN q USING (query_id) WHERE q.query_id IS NULL) missing_queries,(SELECT count(*) FROM c JOIN q ON relevant_id=query_id) query_target_id_overlap,(SELECT count(*) FROM r WHERE query_id IS NULL OR relevant_id IS NULL OR relevance_score IS NULL) null_keys_or_labels""".format(c=str(c).replace('\\','/'),q=str(q).replace('\\','/'),r=str(rels).replace('\\','/'))
result['joins']=query(sql)
rankings=repo/'results/healthtech/ht-dapfam-bm25-20261030-r3/rankings.jsonl'
if rankings.is_file():
 rows=[json.loads(x) for x in rankings.read_text(encoding='utf-8').splitlines()]
 result['saved_rankings']={'path':rankings.relative_to(repo).as_posix(),'sha256':sha(rankings),'rows':len(rows),
  'unique_queries':len({x['query_id'] for x in rows}),'widths':sorted({len(x['ranked_ids']) for x in rows}),
  'duplicate_ids_rows':sum(len(x['ranked_ids'])!=len(set(x['ranked_ids'])) for x in rows),
  'nonfinite_score_rows':sum(any(not math.isfinite(y) for y in x['scores']) for x in rows)}
result['authored_evaluator_probe']={
 'duplicate_rank':bm25.evaluate({'Q':['P','P']},{'Q':{'P':1.0}},k=2),
 'unknown_prediction_query_accepted':bm25.evaluate({'Q':['P'],'UNKNOWN':['P']},{'Q':{'P':1.0}},k=2),
 'missing_prediction_scores_zero':bm25.evaluate({},{'Q':{'P':1.0}},k=2),
 'note':'Helper accepts invalid external rankings; current saved runner-generated rankings checked separately. No claim current reported metrics are inflated.'}
owner=json.loads((repo/'results/healthtech/ht-dapfam-coverage-20261030-r1/summary.json').read_text())
result['owner_coverage_matches']={key:result[key]==owner[key] for key in ['screening','positive_qrels']}
result['input_owner_hashes_match']={name:result['input_files'][name]['sha256']==owner['input_files'][name]['sha256'] for name in result['input_files']}
result['elapsed_seconds']=time.time()-started
result['resources']={'provider_calls':0,'model_inference_calls':0,'network_calls':0,'paid_cost_usd':0,'repo_writes':0}
(out/'data-probe-result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['schema','input_files']},indent=2))
