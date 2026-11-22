"""D3 partial audit: DAPFAM (queries + corpus) Lens IDs vs the PatenTEB test splits already on disk. Aggregates only.
Run with a Python that has pyarrow, from ../_private_artifacts:  python <this file>
"""
import pyarrow.parquet as pq, glob, json, os
D='healthtech/ptp-paper2-oa-dapfam-meta/'
cor=set(map(str,pq.read_table(D+'corpus.parquet',columns=['relevant_id']).column(0).to_pylist()))
qry=set(map(str,pq.read_table(D+'queries.parquet',columns=['query_id']).column(0).to_pylist()))
print('DAPFAM corpus',len(cor),'queries',len(qry),'q in corpus',len(qry&cor))
res={}; allq=set(); allany=set()
for f in sorted(glob.glob('healthtech/patenteb-gated/*/test/data.parquet')):
    task=os.path.normpath(f).split(os.sep)[-3]
    s=pq.read_schema(f).names
    cols=[c for c in ('q','pos','neg') if c in s]
    t=pq.read_table(f,columns=cols)
    ids={c:set(map(str,t.column(c).to_pylist())) for c in cols}
    allq|=ids['q']
    for v in ids.values(): allany|=v
    res[task]={c:{'n_ids':len(v),'dapfam_queries':len(v&qry),'dapfam_corpus':len(v&cor)} for c,v in ids.items()}
res['UNION_q']={'n_ids':len(allq),'dapfam_queries':len(allq&qry),'dapfam_corpus':len(allq&cor)}
res['UNION_any']={'n_ids':len(allany),'dapfam_queries':len(allany&qry),'dapfam_corpus':len(allany&cor)}
print(json.dumps(res,indent=1))
