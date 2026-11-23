"""P2-T02 step 2b (CPU): exact inner-product retrieval, max-p aggregation to units, C0 masks, top 1000 (protocol §3).

Copied from bridgeret/code/dense_bridgeret_v3.py: scores = Q(float32 of fp16) @ P(float32 of fp16).T; per query the
RPD mask (unit first_pub >= filing date -> -inf) and the own-unit mask ('A:' + app_id -> -inf) are applied at UNIT
level after aggregation; top 1000 by argpartition, ties by score then unit index (np.lexsort((top, -row[top])));
units in the z-arctic unit order; scores written with 5 decimals; -inf rows skipped.
Max-p: unit score = max over the unit's passages (passages are stored contiguously in unit order). With
--identity (one passage per unit, the C0 index) it is the plain dense_bridgeret_v3 retrieval (reproduction check).
Only P1-DEV is accepted. Output: gzip TSV app_id, rank, unit, score.
Usage: python p2t02_retrieve.py --passages <enc>/passages.f16.npy (--punit <content>/c1.unit.npy | --identity)
         --units <units.json> --queries <qdir> --units-tsv <corpus-units.tsv> --tasks <tasks.tsv> --out run.tsv.gz
         [--chunk 256] [--limit-q N]
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import os
import time
from pathlib import Path

TOPK = 1000


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--passages', required=True)
    ap.add_argument('--punit')
    ap.add_argument('--identity', action='store_true')
    ap.add_argument('--units', required=True)
    ap.add_argument('--queries', required=True)
    ap.add_argument('--units-tsv', required=True)
    ap.add_argument('--tasks', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--chunk', type=int, default=256)
    ap.add_argument('--limit-q', type=int, default=0)
    ap.add_argument('--block', default='P1-DEV')
    a = ap.parse_args()
    if a.block != 'P1-DEV':
        raise SystemExit('P2-T02 retrieval runs on P1-DEV only (never VAL or TEST)')
    import numpy as np
    t0 = time.time()
    units = json.loads(Path(a.units).read_text())
    P = np.load(a.passages, mmap_mode='r')
    if a.identity:
        assert P.shape[0] == len(units)
        starts = None
    else:
        pu = np.load(a.punit)
        assert pu.shape[0] == P.shape[0] and np.all(np.diff(pu) >= 0)
        assert pu[0] == 0 and pu[-1] == len(units) - 1 and np.unique(pu).size == len(units)
        starts = np.searchsorted(pu, np.arange(len(units)), side='left')
    Pf = np.asarray(P, dtype=np.float32)
    print(f'{time.time() - t0:7.1f}s loaded {Pf.shape[0]} passages for {len(units)} units', flush=True)
    pub = {}
    with open(a.units_tsv, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            pub[r['unit_id']] = int(r['first_pub'].replace('-', ''))
    pubs = np.array([pub[u] for u in units]); uidx = {u: i for i, u in enumerate(units)}
    apps = json.loads((Path(a.queries) / 'P1-DEV.apps.json').read_text())
    Q = np.load(Path(a.queries) / 'P1-DEV.f16.npy').astype(np.float32)
    assert Q.shape[0] == len(apps)
    if a.limit_q:
        apps, Q = apps[:a.limit_q], Q[:a.limit_q]
    need = set(apps)
    fd = {}
    with open(a.tasks, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['app_id'] in need:
                fd[r['app_id']] = int(r['filing_date'].replace('-', ''))
    assert len(fd) == len(need)
    tmp = a.out + '.tmp'
    nrows = 0
    with gzip.open(tmp, 'wt', encoding='utf-8', compresslevel=6) as g:
        g.write('app_id\trank\tunit\tscore\n')
        for s in range(0, len(apps), a.chunk):
            S = Q[s:s + a.chunk] @ Pf.T
            U = S if starts is None else np.maximum.reduceat(S, starts, axis=1)
            del S
            for i, app in enumerate(apps[s:s + a.chunk]):
                row = U[i]; row[pubs >= fd[app]] = -np.inf
                own = uidx.get('A:' + app)
                if own is not None: row[own] = -np.inf
                top = np.argpartition(-row, TOPK)[:TOPK]; top = top[np.lexsort((top, -row[top]))]
                lines = ''.join(f"{app}\t{k + 1}\t{units[j]}\t{row[j]:.5f}\n" for k, j in enumerate(top) if np.isfinite(row[j]))
                nrows += lines.count('\n')
                g.write(lines)
            if (s // a.chunk) % 10 == 0:
                print(f'{time.time() - t0:7.1f}s retrieved {s + len(apps[s:s + a.chunk])}/{len(apps)}', flush=True)
    os.replace(tmp, a.out)
    info = {'out': a.out, 'queries': len(apps), 'rows': nrows, 'passages': int(Pf.shape[0]), 'units': len(units),
            'max_p': not a.identity, 'seconds': round(time.time() - t0, 1)}
    Path(a.out + '.json').write_text(json.dumps(info, indent=1))
    print(json.dumps(info), flush=True)
    print('RETRIEVE_DONE', flush=True)


if __name__ == '__main__':
    main()
