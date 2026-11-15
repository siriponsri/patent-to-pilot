"""Aggregate US-linkability profile of DAPFAM dev (dev split only; metadata columns only).

Reads the staged dev query ids and dev qrels, plus jurisdiction/IPC/date columns of the
pinned HF parquet files (revision 780f4011...). Writes aggregates only.
Usage: python -I dapfam_dev_us_profile.py <dev_dir> <hf_meta_dir> <out.json>
"""
import collections, json, sys
from pathlib import Path
import pyarrow.parquet as pq

dev, meta, out = map(Path, sys.argv[1:4])
qids = [json.loads(l)['id'] for l in open(dev / 'runtime-dev/queries-ta.jsonl', encoding='utf-8')]
qset = set(qids)
qrels = [json.loads(l) for l in open(dev / 'dev-evaluation/qrels-dev.jsonl', encoding='utf-8')]
cols = ['earliest_claim_jusrisdiction', 'jurisdiction', 'classifications_ipcr_list_first_three_chars_list', 'earliest_claim_year']
q = pq.read_table(meta / 'queries.parquet', columns=['query_id'] + cols).to_pylist()
qmeta = {r['query_id']: r for r in q if r['query_id'] in qset}
need = {r['relevant_id'] for r in qrels}
c = pq.read_table(meta / 'corpus.parquet', columns=['relevant_id'] + cols).to_pylist()
cmeta = {r['relevant_id']: r for r in c if r['relevant_id'] in need}

def us(r): return {'earliest_US': r['earliest_claim_jusrisdiction'] == 'US', 'any_US': 'US' in (r['jurisdiction'] or [])}
def sections(r): return {x[0] for x in (r['classifications_ipcr_list_first_three_chars_list'] or []) if x}
def yr(r):
    try: return int(r['earliest_claim_year'])
    except Exception: return None

res = {'dev_queries': len(qids), 'dev_queries_with_metadata': len(qmeta)}
res['queries_earliest_US'] = sum(us(r)['earliest_US'] for r in qmeta.values())
res['queries_any_US_member'] = sum(us(r)['any_US'] for r in qmeta.values())
res['queries_any_US_and_year_2006_2017'] = sum(us(r)['any_US'] and (yr(r) or 0) in range(2006, 2018) for r in qmeta.values())
res['query_year_histogram'] = dict(sorted(collections.Counter(str(yr(r)) for r in qmeta.values()).items()))
pos = [r for r in qrels if r['relevance_score'] > 0 and r['query_id'] in qset]
res['dev_positive_pairs'] = len(pos)
tab = collections.Counter()
for r in pos:
    qm, cm = qmeta.get(r['query_id']), cmeta.get(r['relevant_id'])
    if not qm or not cm: tab[(r['domain_rel'], 'missing_meta')] += 1; continue
    both_us = us(qm)['any_US'] and us(cm)['any_US']
    sec = 'same_section_overlap' if sections(qm) & sections(cm) else 'section_mismatch'
    tab[(r['domain_rel'], 'both_any_US' if both_us else 'not_both_US')] += 1
    tab[(r['domain_rel'], sec)] += 1
res['positive_pairs_by_domain'] = {f'{a}|{b}': n for (a, b), n in sorted(tab.items())}
out.write_text(json.dumps(res, indent=1), encoding='utf-8')
print(json.dumps(res, indent=1))
