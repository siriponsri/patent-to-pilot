"""Hard-negative mining pools for P1-BridgeRet TRAIN tasks (pre-declaration section 4). CPU only; TRAIN only.

For every TRAIN task with a query: positives = units of K(q) (pairs-dev, block TRAIN). Candidate pools from the
RPD-masked TRAIN runs: BM25 top-100 and Z-Arctic dense ranks 20-200. Multi-positive guards remove: any unit in K(q),
the task's own unit, and any unit whose serialised passage text is byte-identical to a positive's text.
(Other citations from later office actions of the same application are not available in pairs-dev; this guard is NOT
applied here and is reported as a limitation.) Each candidate is tagged OUT/IN/NOIPC against the query's IPC3 set
(query = earliest pre-grant publication) for recipe S3. The best positive's dense score is kept for the rule-only margin
denoise (drop negatives scoring > 0.95 x positive score).
Output mined-TRAIN.jsonl: {app_id, pos:[units], pos_dense:max score|null, bm25:[[unit,dom]], dense:[[unit,rank,score,dom]]}
Usage: python3 -I mine_negatives_bridgeret.py <pv_dir> <ser_dir> <texts_dir> <pairs-dev.tsv> <corpus-units.tsv>
       <bm25 run-TRAIN.tsv> <dense run-TRAIN.tsv> <out_dir>
"""
import csv, hashlib, io, json, sys, zipfile
from collections import defaultdict
from pathlib import Path

csv.field_size_limit(1 << 30)


def zrows(path):
    z = zipfile.ZipFile(path)
    return csv.DictReader(io.TextIOWrapper(z.open(z.namelist()[0]), encoding='utf-8', newline=''), delimiter='\t')


def pat_key(pid):
    import re
    m = re.fullmatch(r'(RE|D|PP|H|T)?0*(\d{1,8})', (pid or '').strip().upper())
    return 'P' + (m.group(1) or '') + m.group(2) if m else 'P' + pid


def main(argv):
    pv, ser, texts, pairs_p, units_p, bm_p, de_p, out = [Path(a) for a in argv[:8]]
    out.mkdir(parents=True, exist_ok=True)
    pos = defaultdict(set)
    with open(pairs_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['block'] == 'TRAIN' and r['unit']:
                pos[r['app_id']].add(r['unit'])
    qdoc = {}
    for l in open(texts / 'queries.jsonl', encoding='utf-8'):
        r = json.loads(l)
        if r['block'] == 'TRAIN' and r.get('doc'):
            qdoc[r['app_id']] = r['doc']
    rep = {}
    with open(units_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            rep[r['unit_id']] = r['rep_doc']
    thash = {}
    for l in open(ser / 'passages.jsonl', encoding='utf-8'):
        r = json.loads(l)
        thash[r['unit']] = hashlib.sha1(r['text'].encode()).digest()
    need = set(rep.values()) | set(qdoc.values())
    ipc3 = defaultdict(set)
    for r in zrows(pv / 'g_ipc_at_issue.tsv.zip'):
        d = pat_key(r['patent_id'])
        if d in need:
            ipc3[d].add(r['section'] + r['ipc_class'])
    for r in zrows(pv / 'pg_ipc_at_issue.tsv.zip'):
        d = 'PG' + r['pgpub_id']
        if d in need:
            ipc3[d].add(r['section'] + r['ipc_class'])

    def dom(app, unit):
        a, c = ipc3.get(qdoc[app], set()), ipc3.get(rep.get(unit, ''), set())
        return 'NOIPC' if not a or not c else ('IN' if a & c else 'OUT')

    def load(p, hi, keep_pos):
        res = defaultdict(list)
        with open(p, encoding='utf-8') as f:
            for r in csv.DictReader(f, delimiter='\t'):
                k = int(r['rank'])
                if r['app_id'] in qdoc and (k <= hi or (keep_pos and r['unit'] in pos.get(r['app_id'], ()))):
                    res[r['app_id']].append((r['unit'], k, float(r['score'])))
        return res
    bm = load(bm_p, 100, False)
    de_all = load(de_p, 200, True)          # ranks <= 200 plus positives at any rank (for pos_dense)
    stats = defaultdict(int)
    with open(out / 'mined-TRAIN.jsonl', 'w', encoding='utf-8') as g:
        for a in sorted(qdoc):
            P = pos.get(a, set())
            if not P:
                stats['no_positive_in_corpus'] += 1
                continue
            ph = {thash[u] for u in P if u in thash}
            bad = lambda u: u in P or u == 'A:' + a or thash.get(u) in ph
            pd = [s for u, k, s in de_all.get(a, ()) if u in P]
            bml = [[u, dom(a, u)] for u, k, s in bm.get(a, ()) if not bad(u)]
            dl = [[u, k, round(s, 5), dom(a, u)] for u, k, s in de_all.get(a, ()) if 20 <= k <= 200 and not bad(u)]
            stats['tasks'] += 1; stats['bm25_negs'] += len(bml); stats['dense_negs'] += len(dl)
            stats['dense_OUT'] += sum(x[3] == 'OUT' for x in dl); stats['dense_IN'] += sum(x[3] == 'IN' for x in dl)
            stats['guard_removed'] += sum(1 for u, k, s in de_all.get(a, ()) if 20 <= k <= 200 and bad(u))
            g.write(json.dumps({'app_id': a, 'pos': sorted(P), 'pos_dense': max(pd) if pd else None, 'bm25': bml, 'dense': dl}) + '\n')
    (out / 'mined-report.json').write_text(json.dumps(dict(stats), indent=1))
    print(json.dumps(dict(stats), indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
