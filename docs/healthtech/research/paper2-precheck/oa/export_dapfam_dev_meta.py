"""Export DAPFAM dev metadata (dev split only) to one private JSONL for the remote census.
Fields: role (query|target), id, jurisdiction, earliest_claim_date, title_en; plus positive qrels pairs.
Output stays in private storage (never the repo).
Usage: python -I export_dapfam_dev_meta.py <dev_dir> <meta_dir> <out.jsonl>
"""
import json, sys
from pathlib import Path
import pyarrow.parquet as pq
dev, meta, out = map(Path, sys.argv[1:4])
qids = [json.loads(l)['id'] for l in open(dev / 'runtime-dev/queries-ta.jsonl', encoding='utf-8')]
qset = set(qids)
pos = [r for r in map(json.loads, open(dev / 'dev-evaluation/qrels-dev.jsonl', encoding='utf-8')) if r['relevance_score'] > 0 and r['query_id'] in qset]
tgt = {r['relevant_id'] for r in pos}
cols = ['jurisdiction', 'earliest_claim_date', 'title_en']
with open(out, 'w', encoding='utf-8') as f:
    for role, path, key, keep in [('query', 'queries.parquet', 'query_id', qset), ('target', 'corpus.parquet', 'relevant_id', tgt)]:
        for r in pq.read_table(meta / path, columns=[key] + cols).to_pylist():
            if r[key] in keep:
                f.write(json.dumps({'role': role, 'id': r[key], 'jurisdiction': r['jurisdiction'], 'date': str(r['earliest_claim_date'])[:10] if r['earliest_claim_date'] else None, 'title': r['title_en']}) + '\n')
    for r in pos:
        f.write(json.dumps({'role': 'pair', 'q': r['query_id'], 't': r['relevant_id'], 'domain': r['domain_rel']}) + '\n')
print(len(qids), len(tgt), len(pos))
