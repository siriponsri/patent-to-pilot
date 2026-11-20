"""AM-7.1 §7 contamination sensitivity (descriptive; P1-DEV and VAL only).

A* is rebuilt with the same rule and parameters (no new selection) on the Qwen3-Emb zero-shot backbone; the reported
contrast is A*_qwen3 - U0_qwen3 on E2 MR@200 (art-unit bootstrap). If A* contains N5, RRF(BM25, N5) and BM25 alone are
also reported (BM25 top-1000 lists of runs/bm25, anchor removed; N5 ties and fill-up follow BM25 rank).
Usage: python3 am7_sensitivity.py <prep_dir> <stage2a-results.json> <qwen3 passages.f16.npy> <qwen3 serialised dir>
       <qwen3 query dir> <bm25 run dir> <out.json>
"""
import csv, json, sys, time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import am7_lib as L  # noqa: E402
import am7_stage2a as S2  # noqa: E402


def bm25_lists(path, uidx, apps):
    out = defaultdict(list)
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['app_id'] in apps:
                out[r['app_id']].append((int(r['rank']), uidx[r['unit']]))
    return {a: np.array([i for _, i in sorted(v)], dtype=np.int64) for a, v in out.items()}


def n5_on_list(counts, base_list, unit_rank, depth=L.DEPTH):
    pos_in = {int(i): r for r, i in enumerate(base_list)}
    pos = sorted((i for i, c in counts.items() if c > 0), key=lambda i: (-counts[i], pos_in.get(i, 10 ** 9), unit_rank[i]))
    head = pos[:depth]; seen = set(head)
    return np.array(head + [int(i) for i in base_list if int(i) not in seen][:depth - len(head)], dtype=np.int64)


def main(a):
    prep, res_p, qpfile, qser, qdir, bm25dir, out_p = map(Path, a)
    t0 = time.time(); log = lambda *x: print(round(time.time() - t0), 's', *x, flush=True)
    res = json.load(open(res_p)); sel = res['selection']
    astar = sel['A_star']
    ctx = S2.Ctx(prep, str(qpfile), log)
    order = [json.loads(l)['unit'] for l in open(qser / 'passages.jsonl', encoding='utf-8')]
    if sorted(order) != sorted(ctx.units):
        raise SystemExit('qwen3 corpus units differ from the PatEmbed corpus')
    qrow = {u: i for i, u in enumerate(order)}
    ctx.P = ctx.P[np.array([qrow[u] for u in ctx.units])]          # reorder to the meta unit order
    log('reordered')
    if astar in ('A4p', 'A4'):
        kind = (astar, None)
    else:
        kind = (astar.split(':')[0], float(astar.split(':')[1]))
    abar = ('A1', sel['A1_beta']) if sel['Abar'].startswith('A1') else ('A2', sel['A2_gamma'])
    report = {'format': 'ptp-p1-am7-sensitivity-v1', 'descriptive_only': True, 'A_star': astar, 'blocks': {}}
    for b in S2.BLOCKS:
        ids = json.load(open(qdir / f'Q-{b}.ids.json'))
        Qv = np.load(qdir / f'Q-{b}.f16.npy').astype(np.float32)
        qmap = {q['app']: q for q in ctx.Q[b]}
        rows = [(j, qmap[x]) for j, x in enumerate(ids) if 'e2' in qmap[x]]
        m_u0, m_as = {}, {}
        for s0 in range(0, len(rows), 256):
            part = rows[s0:s0 + 256]
            qs = [q for _, q in part]; Qb = Qv[[j for j, _ in part]]
            anc = [q['e2']['anchor'] for q in qs]
            S = ctx.masked(Qb @ ctx.P.T, qs, extra=[[x] for x in anc])
            u0 = L.topk_rows(S, ctx.unit_rank)
            ast = S2.a_star_list(ctx, kind[0], kind[1], qs, Qb, anc, [()] * len(qs), abar)
            for r, q in enumerate(qs):
                m_u0[q['app']] = S2.e2_metrics(u0[r], q); m_as[q['app']] = S2.e2_metrics(ast[r], q)
        apps = [q['app'] for _, q in rows]
        cl = np.array([qmap[x]['au'] for x in apps])
        d = np.array([m_as[x]['MR@200'] - m_u0[x]['MR@200'] for x in apps])
        m, lo, hi = L.cluster_bootstrap(d, cl)
        blk = {'n_cohort': len(apps), 'U0_qwen3_MR@200': S2.mean_of(m_u0, 'MR@200'), 'Astar_qwen3_MR@200': S2.mean_of(m_as, 'MR@200'),
               'D1_qwen3': {'delta': round(m, 5), 'ci95_artunit': [round(lo, 5), round(hi, 5)]}}
        if astar in ('A4p', 'A4'):
            bl = bm25_lists(bm25dir / f'run-{b}.tsv', ctx.uidx, set(apps))
            mb, mbn = {}, {}
            for x in apps:
                q = qmap[x]; a_ = q['e2']['anchor']
                base = np.array([i for i in bl.get(x, np.empty(0, dtype=np.int64)) if i != a_], dtype=np.int64)
                c, _ = ctx.cc.counts(a_, q['mail'], q['app'], q['group'])
                fd_ok = {i: v for i, v in c.items() if ctx.unit_pub[i] < q['fd'] and ctx.units[i] != 'A:' + x}
                mb[x] = S2.e2_metrics(base, q)
                mbn[x] = S2.e2_metrics(L.rrf([base, n5_on_list(fd_ok, base, ctx.unit_rank)], unit_rank=ctx.unit_rank), q)
            db = np.array([mbn[x]['MR@200'] - mb[x]['MR@200'] for x in apps])
            m, lo, hi = L.cluster_bootstrap(db, cl)
            blk.update({'BM25_MR@200': S2.mean_of(mb, 'MR@200'), 'RRF_BM25_N5_MR@200': S2.mean_of(mbn, 'MR@200'),
                        'RRF_BM25_N5_minus_BM25': {'delta': round(m, 5), 'ci95_artunit': [round(lo, 5), round(hi, 5)]}})
        report['blocks'][b] = blk
        log(b, blk)
    report['seconds'] = round(time.time() - t0, 1)
    json.dump(report, open(out_p, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1:])
