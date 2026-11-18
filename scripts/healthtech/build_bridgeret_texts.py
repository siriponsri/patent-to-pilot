"""BridgeRet text tables: query texts (non-TEST tasks only) and Challenge-1M corpus passages. Stdlib only.

Query side: tasks in TRAIN, VAL, P1-DEV, P2-DEV of the FROZEN manifest. TEST task texts are NOT built here
(spec 01 section 1.4: no TEST query text is read before the owner approves the TEST dispatch).
Query document = the earliest pre-grant publication of the task application (types utility/new/new-utility):
the application as filed and first published. Tasks without one get variant 'no_pgpub' and are counted.
Corpus side: rep_doc of every unit in corpus-units.tsv (grant 'P...' or pre-grant 'PG...').
Components per document: title, abstract, first independent claim (bridgeret_query rules, reduced
incrementally so that only one candidate claim per document is held in memory).
Outputs: queries.jsonl, corpus.jsonl, report.json (counts + sha256). Serialisation and token truncation are
applied later with the model tokenizer (bridgeret_query.serialise).
Usage: python3 -I build_bridgeret_texts.py <pv_dir> <frozen_manifest.json> <corpus-units.tsv> <out_dir> [workers]
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import multiprocessing as mp
import re
import sys
import time
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from patent_to_pilot.research import bridgeret_query as q
except ImportError:
    import bridgeret_query as q  # flat copy on the remote

csv.field_size_limit(1 << 30)
QUERY_BLOCKS = ('TRAIN', 'VAL', 'P1-DEV', 'P2-DEV')
PG_TYPES = {'utility', 'new', 'new-utility'}
NEED: set = set()


def zrows(path: Path):
    z = zipfile.ZipFile(path)
    name = z.namelist()[0]
    return csv.DictReader(io.TextIOWrapper(z.open(name), encoding='utf-8', newline=''), delimiter='\t')


def pat_key(pid):
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', (pid or '').strip().upper())
    return 'P' + (m.group(1) or '') + m.group(2) if m else 'P' + pid


def claim_file(path: str):
    """Reduce one claims file to {doc: (indep_num, indep_text, any_num, any_text)} for needed docs."""
    p = Path(path)
    pg = p.name.startswith('pg_')
    best: dict[str, list] = {}
    for r in zrows(p):
        doc = ('PG' + r['pgpub_id']) if pg else pat_key(r['patent_id'])
        if doc not in NEED:
            continue
        text = r.get('claim_text') or ''
        if q.is_cancelled(text):
            continue
        num_s = (r.get('claim_number') or '').strip() or (r.get('claim_sequence') or '')
        try:
            num = int(num_s)
        except ValueError:
            num = 10 ** 6
        cur = best.setdefault(doc, [None, None, None, None])
        if cur[2] is None or num < cur[2]:
            cur[2], cur[3] = num, text
        indep = not (r.get('dependent') or '').strip() and not q.DEPENDENCY.search(text)
        if indep and (cur[0] is None or num < cur[0]):
            cur[0], cur[1] = num, text
    return best


def init(need):
    global NEED
    NEED = need


def fsha(p):
    x = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''):
            x.update(b)
    return x.hexdigest()


def main(argv):
    pv, man_p, units_p, out = Path(argv[0]), Path(argv[1]), Path(argv[2]), Path(argv[3])
    workers = int(argv[4]) if len(argv) > 4 else 8
    out.mkdir(parents=True, exist_ok=False)
    t0 = time.time()
    man = json.loads(man_p.read_text())
    if not man.get('frozen'):
        raise SystemExit('manifest is not frozen')
    task_block = {a: b for b in QUERY_BLOCKS for a in man['blocks'][b]}
    # earliest pgpub per task application + titles
    pg_title, qdoc = {}, {}
    for r in zrows(pv / 'pg_published_application.tsv.zip'):
        if r['patent_type'] not in PG_TYPES:
            continue
        a = re.sub(r'[\s/,]', '', r['application_id'] or '')
        doc = 'PG' + r['pgpub_id']
        if a in task_block:
            cur = qdoc.get(a)
            if cur is None or (r['published_date'], doc) < cur:
                qdoc[a] = (r['published_date'], doc)
        pg_title[doc] = r['application_title']
    with open(units_p, encoding='utf-8') as f:
        units = [(r['unit_id'], r['rep_doc']) for r in csv.DictReader(f, delimiter='\t')]
    need = {d for _, d in units} | {d for _, d in qdoc.values()}
    title = {d: pg_title[d] for d in need if d in pg_title}
    del pg_title
    for r in zrows(pv / 'g_patent.tsv.zip'):
        d = pat_key(r['patent_id'])
        if d in need:
            title[d] = r['patent_title']
    abstract = {}
    for r in zrows(pv / 'g_patent_abstract.tsv.zip'):
        d = pat_key(r['patent_id'])
        if d in need:
            abstract[d] = r.get('patent_abstract') or ''
    for r in zrows(pv / 'pg_published_application_abstract.tsv.zip'):
        d = 'PG' + r['pgpub_id']
        if d in need:
            abstract[d] = r.get('application_abstract') or ''
    files = sorted(str(p) for p in (pv / 'claims').glob('*_claims_*.tsv.zip'))
    claims: dict[str, list] = {}
    if workers > 1 and 'fork' in mp.get_all_start_methods():
        pool = mp.get_context('fork').Pool(workers, initializer=init, initargs=(need,))
        parts = pool.imap_unordered(claim_file, files)
    else:
        init(need)
        pool, parts = None, map(claim_file, files)
    try:
        for part in parts:
            for d, v in part.items():
                cur = claims.setdefault(d, [None, None, None, None])
                if v[2] is not None and (cur[2] is None or v[2] < cur[2]):
                    cur[2], cur[3] = v[2], v[3]
                if v[0] is not None and (cur[0] is None or v[0] < cur[0]):
                    cur[0], cur[1] = v[0], v[1]
    finally:
        if pool is not None:
            pool.close()
            pool.join()

    def comp(d):
        c = claims.get(d)
        if c and c[1] is not None:
            claim, var = q._clean(c[1]), 'first_independent'
        elif c and c[3] is not None:
            claim, var = q._clean(c[3]), 'claim_fallback_claim1'
        else:
            claim, var = '', 'no_claims'
        return {'title': q._clean(title.get(d, '')), 'abstract': q._clean(abstract.get(d, '')), 'claim': claim,
                'claim_variant': var}

    stats = {'queries_by_block': {}, 'queries_no_pgpub': 0, 'query_variants': {}, 'corpus_variants': {},
             'corpus_no_abstract': 0, 'corpus_no_title': 0, 'query_no_abstract': 0}
    with open(out / 'queries.jsonl', 'w', encoding='utf-8') as f:
        for a, b in sorted(task_block.items()):
            stats['queries_by_block'][b] = stats['queries_by_block'].get(b, 0) + 1
            if a not in qdoc:
                stats['queries_no_pgpub'] += 1
                f.write(json.dumps({'app_id': a, 'block': b, 'doc': None, 'variant': 'no_pgpub'}) + '\n')
                continue
            c = comp(qdoc[a][1])
            stats['query_variants'][c['claim_variant']] = stats['query_variants'].get(c['claim_variant'], 0) + 1
            stats['query_no_abstract'] += not c['abstract']
            f.write(json.dumps({'app_id': a, 'block': b, 'doc': qdoc[a][1], 'pub': qdoc[a][0], **c}, ensure_ascii=False) + '\n')
    with open(out / 'corpus.jsonl', 'w', encoding='utf-8') as f:
        for u, d in units:
            c = comp(d)
            stats['corpus_variants'][c['claim_variant']] = stats['corpus_variants'].get(c['claim_variant'], 0) + 1
            stats['corpus_no_abstract'] += not c['abstract']
            stats['corpus_no_title'] += not c['title']
            f.write(json.dumps({'unit': u, 'doc': d, **c}, ensure_ascii=False) + '\n')
    stats.update({'n_corpus': len(units), 'claim_files': len(files), 'seconds': round(time.time() - t0, 1),
                  'manifest_sha256': man['manifest_sha256'], 'corpus_units_sha256': fsha(units_p),
                  'outputs_sha256': {p: fsha(out / p) for p in ('queries.jsonl', 'corpus.jsonl')}})
    (out / 'report.json').write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
