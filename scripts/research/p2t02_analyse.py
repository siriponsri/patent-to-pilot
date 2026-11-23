"""P2-T02 evaluator-side analysis (protocol §5, frozen bd30d3f7). P1-DEV only; never reads VAL labels or TEST.

Subcommands
  gate     : C0 reproduction gate. The unchanged evaluator (eval_bridgeret_dev.py), fed the EXISTING runs/z-arctic and
             runs/bm25 run-P1-DEV.tsv.gz through this pipeline's evaluator path, must reproduce summary-P1-DEV.json
             exactly (every metric mean and n; ALL R@200 is the required one). Exit 1 on failure.
  samerun  : compare a re-generated C0 run (p2t02_retrieve.py --identity) with the existing z-arctic run, row by row,
             for the queries present in the new run (retrieval-path reproduction check).
  decide   : frozen contrasts with the G03 cluster bootstrap (examiner art unit, B = 10,000, seed 20261119), decision
             rule, and the always-reported descriptives (R@200/R@1000 per arm, new candidates vs C0, new judged-positive
             recovery |G n (P1 minus P0)|, displaced positives, per-query wins/losses, deeper-original-query control,
             index build cost).
  fusion   : descriptive F*-style fusion check over the G03 action model (B = 4 windows) with the qualifying arm(s)
             substituted; run only when decide reports a qualifying arm.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import pickle
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

KINDS = ('ALL', 'IN', 'OUT')
DELTA, TIE, SEED, B = 0.005, 0.0005, 20261119, 10000
BLOCK = 'P1-DEV'
G03_ROUTES = ('L', 'Q', 'P', 'A')
PRIORITY = ('Q', 'P', 'A', 'L')     # G03 protocol §4 tie order for F*


# ------------------------------------------------------------------ copied verbatim from g03_decide.py
def cluster_bootstrap(values, clusters, b=B, seed=SEED):
    v = np.asarray(values, dtype=np.float64)
    uniq, inv = np.unique(np.asarray(clusters), return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(uniq))
    cnts = np.bincount(inv, minlength=len(uniq)).astype(np.float64)
    rng = np.random.default_rng(seed)
    w = rng.multinomial(len(uniq), np.full(len(uniq), 1.0 / len(uniq)), size=b).astype(np.float64)
    means = (w @ sums) / (w @ cnts)
    return float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def paired_pq(pa, pb, clusters, cut=200):
    """g03_decide.paired() on per-query dicts (evaluator per_query rows)."""
    res = {}
    for k in KINDS:
        key = f'{k}_R@{cut}'
        apps = sorted(q for q in pa if key in pa[q] and key in pb.get(q, {}))
        d = [pa[q][key] - pb[q][key] for q in apps]
        cl = [clusters.get(q, 'q:' + q) for q in apps]
        m, lo, hi = cluster_bootstrap(d, cl)
        res[key] = {'delta': m, 'ci95': [lo, hi], 'n': len(apps), 'wins': int(sum(x > 0 for x in d)),
                    'losses': int(sum(x < 0 for x in d))}
    return res
# ------------------------------------------------------------------


def qualifies(c):
    return (c['ALL_R@200']['ci95'][0] > 0 and c['IN_R@200']['ci95'][0] > -DELTA
            and c['OUT_R@200']['ci95'][0] > -DELTA)


def load_eval(p, per_query=True):
    d = json.load(open(p))
    assert d['block'] == BLOCK
    return d if per_query else d['metrics']


def clusters_from_meta(meta_p):
    meta = pickle.load(open(meta_p, 'rb'))
    return {q['app']: str(q.get('au') or 'q:' + q['app']) for q in meta['queries'][BLOCK]}


def read_run(p, depth=1000):
    intern, out = {}, defaultdict(list)
    op = gzip.open if str(p).endswith('.gz') else open
    with op(p, 'rt', encoding='utf-8') as f:
        assert f.readline().rstrip('\n').split('\t')[:3] == ['app_id', 'rank', 'unit']
        for line in f:
            a, r, u, _ = line.rstrip('\n').split('\t')
            r = int(r)
            if r <= depth:
                out[a].append((r, intern.setdefault(u, u)))
    return {a: [u for _, u in sorted(v)] for a, v in out.items()}


def positives(pairs_p, units_p, tasks_p):
    """Evaluator logic of eval_bridgeret_dev.py (conditional sets) for P1-DEV: app -> kind -> set(units)."""
    corpus = set()
    with open(units_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            corpus.add(r['unit_id'])
    rows = []
    with open(pairs_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['block'] == BLOCK and r['unit'] and r['unit_first_pub']:
                rows.append(r)
    need = {r['app_id'] for r in rows}
    fd = {}
    with open(tasks_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['app_id'] in need:
                fd[r['app_id']] = r['filing_date']
    rel = defaultdict(lambda: defaultdict(set))
    for r in rows:
        a, u = r['app_id'], r['unit']
        if r['unit_first_pub'] >= fd[a] or u == 'A:' + a:
            continue
        kinds = ['ALL'] + (['OUT'] if r['dom_ipc3'] == 'OUT3' else ['IN'] if r['dom_ipc3'] == 'IN3' else [])
        for k in kinds:
            if u in corpus:
                rel[a][k].add(u)
    return rel


def cmd_gate(a):
    out, ok = {'checks': []}, True
    for name, ev, summ in (('arctic-c0', a.eval_arctic, a.summary_arctic), ('bm25-c0', a.eval_bm25, a.summary_bm25)):
        mine = load_eval(ev, False)
        ref = json.load(open(summ))['metrics']
        same_all = set(mine) == set(ref) and all(mine[k] == ref[k] for k in ref)
        key = 'ALL_R@200'
        same_key = mine[key] == ref[key]
        ok &= bool(same_all and same_key)
        out['checks'].append({'route': name, 'eval': ev, 'summary': summ, 'ALL_R@200_mine': mine[key],
                              'ALL_R@200_summary': ref[key], 'ALL_R@200_equal': same_key,
                              'all_metrics_equal': same_all})
    out['gate_passed'] = bool(ok)
    Path(a.out).write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print('GATE_PASSED' if ok else 'GATE_FAILED', flush=True)
    if not ok:
        sys.exit(1)


def cmd_samerun(a):
    new = defaultdict(list)
    with gzip.open(a.new, 'rt', encoding='utf-8') as f:
        f.readline()
        for line in f:
            new[line.split('\t', 1)[0]].append(line)
    ref = defaultdict(list)
    with gzip.open(a.ref, 'rt', encoding='utf-8') as f:
        f.readline()
        for line in f:
            q = line.split('\t', 1)[0]
            if q in new:
                ref[q].append(line)
    same_lines = sum(1 for q in new for x, y in zip(new[q], ref[q]) if x == y)
    tot = sum(len(v) for v in new.values())
    same_units = sum(1 for q in new for x, y in zip(new[q], ref[q]) if x.split('\t')[:3] == y.split('\t')[:3])
    same_q = sum(1 for q in new if new[q] == ref[q])
    res = {'new': a.new, 'ref': a.ref, 'queries': len(new), 'rows_new': tot,
           'rows_ref': sum(len(v) for v in ref.values()), 'identical_rows': same_lines,
           'identical_rank_unit_rows': same_units, 'identical_queries': same_q,
           'exact_reproduction': same_q == len(new) and tot == sum(len(v) for v in ref.values())}
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))
    print('SAMERUN_EXACT' if res['exact_reproduction'] else 'SAMERUN_NOT_EXACT', flush=True)


def overlap_stats(arm_run, ref_run, rel):
    """New candidates and judged-positive recovery/displacement of arm vs ref, evaluator side."""
    res = {}
    apps = sorted(set(arm_run) | set(ref_run))
    for cut in (200, 1000):
        new_c, rec, disp, qrec, qdisp = [], {k: 0 for k in KINDS}, {k: 0 for k in KINDS}, 0, 0
        for q in apps:
            p1, p0 = set(arm_run.get(q, [])[:cut]), set(ref_run.get(q, [])[:cut])
            new_c.append(len(p1 - p0))
            g = rel.get(q, {})
            r_any = d_any = 0
            for k in KINDS:
                gs = g.get(k, set())
                r, d = len(gs & (p1 - p0)), len(gs & (p0 - p1))
                rec[k] += r; disp[k] += d
                if k == 'ALL':
                    r_any, d_any = r, d
            qrec += r_any > 0; qdisp += d_any > 0
        nc = np.asarray(new_c, dtype=np.float64)
        res[f'@{cut}'] = {'queries': len(apps), 'new_candidates_per_query_mean': round(float(nc.mean()), 3),
                          'new_candidates_per_query_p50': float(np.percentile(nc, 50)),
                          'new_candidates_total': int(nc.sum()),
                          'new_judged_positive_recovery': rec, 'displaced_positives': disp,
                          'net_positive_change': {k: rec[k] - disp[k] for k in KINDS},
                          'queries_with_recovery': int(qrec), 'queries_with_displacement': int(qdisp)}
    return res


def parse_time(p):
    out = {}
    try:
        txt = Path(p).read_text(errors='replace')
    except FileNotFoundError:
        return None
    m = re.search(r'Elapsed \(wall clock\) time \(h:mm:ss or m:ss\): (\S+)', txt)
    if m:
        parts = [float(x) for x in m.group(1).split(':')]
        sec = 0.0
        for x in parts:
            sec = sec * 60 + x
        out['wall_seconds'] = round(sec, 1)
    m = re.search(r'Maximum resident set size \(kbytes\): (\d+)', txt)
    if m:
        out['max_rss_gib'] = round(int(m.group(1)) / 2 ** 20, 2)
    m = re.search(r'Exit status: (\d+)', txt)
    if m:
        out['exit_status'] = int(m.group(1))
    return out


def du(p):
    p = Path(p)
    if not p.exists():
        return None
    if p.is_file():
        return p.stat().st_size
    return sum(x.stat().st_size for x in p.rglob('*') if x.is_file())


def cmd_decide(a):
    root = Path(a.root)
    ev = root / 'evals'
    gate = json.load(open(root / 'gate.json'))
    if not gate['gate_passed']:
        sys.exit('C0 reproduction gate not passed: no contrast is computed')
    clusters = clusters_from_meta(a.meta)
    names = ('arctic-c0', 'arctic-c1', 'arctic-c2', 'bm25-c0', 'bm25-full')
    E = {n: load_eval(ev / f'{n}.json') for n in names}
    for n in names:
        assert E[n]['metrics']['ALL_R@200']['n'] == E['arctic-c0']['metrics']['ALL_R@200']['n']
    pq = {n: E[n]['per_query'] for n in names}
    table = {n: {k: E[n]['metrics'][k]['mean'] for k in
                 ('ALL_R@200', 'IN_R@200', 'OUT_R@200', 'ALL_R@1000', 'IN_R@1000', 'OUT_R@1000', 'OUT_MRR',
                  'OUT_nDCG@10')} | {'n_queries_run': E[n]['n_queries_run']} for n in names}
    contrasts = {
        'coverage_arctic_C1_minus_C0': paired_pq(pq['arctic-c1'], pq['arctic-c0'], clusters),
        'coverage_bm25_full_minus_C0': paired_pq(pq['bm25-full'], pq['bm25-c0'], clusters),
        'structure_arctic_C2_minus_C1': paired_pq(pq['arctic-c2'], pq['arctic-c1'], clusters),
        'arctic_C2_minus_C0': paired_pq(pq['arctic-c2'], pq['arctic-c0'], clusters),
    }
    q_c1 = qualifies(contrasts['coverage_arctic_C1_minus_C0'])
    q_c2 = qualifies(contrasts['arctic_C2_minus_C0'])
    q_bm = qualifies(contrasts['coverage_bm25_full_minus_C0'])
    struct = qualifies(contrasts['structure_arctic_C2_minus_C1'])
    if q_c2 and struct:
        arctic = ('arctic-c2', 'Arctic-C2 becomes the representation baseline; structure is credited '
                               '(C2 - C0 and C2 - C1 both meet the rule)')
    elif q_c1:
        arctic = ('arctic-c1', 'Arctic-C1 (flat complete content) becomes the representation baseline; structure gets '
                               'no credit' + (' (C2 - C1 does not meet the rule)' if not struct else
                                              ' (C2 - C1 meets the rule but C2 - C0 does not)'))
    elif q_c2:
        arctic = (None, 'UNSETTLED: Arctic-C2 meets the rule against C0, C1 does not, and C2 - C1 does not credit '
                        'structure; the frozen protocol does not say which index becomes the baseline (owner decision)')
    else:
        arctic = (None, 'NO_GAIN for Arctic coverage: keep Arctic-C0')
    bm = ('bm25-full', 'BM25-full becomes the BM25 representation baseline') if q_bm else \
        (None, 'NO_GAIN for BM25 coverage: keep BM25-C0')
    overall = 'NO_GAIN: keep C0; P2-T04 proceeds on the existing routes' if arctic[0] is None and bm[0] is None \
        and not arctic[1].startswith('UNSETTLED') else 'see per-route decisions'
    decision = {'rule': 'baseline if vs C0 of the same route ALL lo > 0 and IN, OUT lo > -0.005; structure credited only '
                        'if C2 - C1 ALL lo > 0 and IN, OUT lo > -0.005',
                'qualifies': {'arctic-c1_vs_c0': q_c1, 'arctic-c2_vs_c0': q_c2, 'bm25-full_vs_c0': q_bm,
                              'structure_c2_vs_c1': struct},
                'arctic': {'baseline': arctic[0], 'text': arctic[1]}, 'bm25': {'baseline': bm[0], 'text': bm[1]},
                'overall': overall,
                'substitute_for_fusion': {k: v for k, v in (('A', arctic[0]), ('L', bm[0])) if v}}
    # deeper original-query control: the same original route at windows 1-2 (depth 400) under the G03 action model
    deeper = {}
    g03 = Path(a.g03_evals) if a.g03_evals else None
    if g03 is None:
        deeper = {'deferred': 'G03 evals are not on this host (amendment A1); computed later on dr-train'}
    for r, c0, arms, d1, d2 in (('A', 'arctic-c0', ('arctic-c1', 'arctic-c2'), 'alloc-L0-Q0-P0-A1', 'alloc-L0-Q0-P0-A2'),
                                ('L', 'bm25-c0', ('bm25-full',), 'alloc-L1-Q0-P0-A0', 'alloc-L2-Q0-P0-A0')) if g03 else ():
        w1 = load_eval(g03 / f'{d1}.json')['per_query']
        w2 = load_eval(g03 / f'{d2}.json')['per_query']
        row = {'g03_arms': [d1, d2],
               'window1_equals_route_C0_R@200': all(abs(w1[q].get('ALL_R@200', 0) - pq[c0][q].get('ALL_R@200', 0)) < 1e-12
                                                    for q in pq[c0]),
               'depth400_minus_depth200': paired_pq(w2, w1, clusters)}
        for arm in arms:
            row[f'{arm}_minus_original_depth400'] = paired_pq(pq[arm], w2, clusters)
        deeper[r] = row
    # new candidates / recovery (evaluator side)
    rel = positives(a.pairs, a.units_tsv, a.tasks)
    runs = {'arctic-c0': a.run_arctic_c0, 'bm25-c0': a.run_bm25_c0,
            'arctic-c1': root / 'runs/arctic-c1/run-P1-DEV.tsv.gz', 'arctic-c2': root / 'runs/arctic-c2/run-P1-DEV.tsv.gz',
            'bm25-full': root / 'runs/bm25-full/run-P1-DEV.tsv.gz'}
    cand = {}
    R = {'arctic-c0': read_run(runs['arctic-c0'])}
    for arm in ('arctic-c1', 'arctic-c2'):
        R[arm] = read_run(runs[arm])
        cand[f'{arm}_vs_arctic-c0'] = overlap_stats(R[arm], R['arctic-c0'], rel)
    cand['arctic-c2_vs_arctic-c1'] = overlap_stats(R['arctic-c2'], R['arctic-c1'], rel)
    R = {'bm25-c0': read_run(runs['bm25-c0']), 'bm25-full': read_run(runs['bm25-full'])}
    cand['bm25-full_vs_bm25-c0'] = overlap_stats(R['bm25-full'], R['bm25-c0'], rel)
    del R
    # cost
    cost = {'content_build': parse_time(root / 'logs/build.time'),
            'encode_queries': parse_time(root / 'logs/encode-queries.time'),
            'encode_c1': parse_time(root / 'logs/encode-c1.time'), 'encode_c2': parse_time(root / 'logs/encode-c2.time'),
            'retrieve_c1': parse_time(root / 'logs/retrieve-c1.time'),
            'retrieve_c2': parse_time(root / 'logs/retrieve-c2.time'),
            'bm25_full': parse_time(root / 'logs/bm25-full.time'),
            'encode_json': {n: json.load(open(root / f'enc/{n}/encode.json')) for n in ('c1', 'c2')
                            if (root / f'enc/{n}/encode.json').exists()},
            'disk_bytes': {'content_dir': du(root / 'content'), 'c1_ids': du(root / 'content/c1.ids.u32'),
                           'c2_ids': du(root / 'content/c2.ids.u32'), 'c1_vectors': du(root / 'enc/c1/passages.f16.npy'),
                           'c2_vectors': du(root / 'enc/c2/passages.f16.npy'),
                           'full_text_jsonl': du(root / 'content/ser-full/passages.jsonl'),
                           'c0_vectors_reference': du(Path(a.run_arctic_c0).parent / 'passages.f16.npy')},
            'content_stats': json.load(open(root / 'content/stats.json'))}
    res = {'format': 'ptp-p2t02-v1',
           'protocol': 'docs/healthtech/research/p2-coverage/P2-T02-COVERAGE-CONTROL-PROTOCOL.md@bd30d3f7',
           'block': BLOCK, 'gate': gate, 'arm_table': table, 'contrasts': contrasts, 'decision': decision,
           'deeper_original_query_control': deeper, 'candidates_and_recovery': cand, 'cost': cost,
           'bootstrap': {'B': B, 'seed': SEED, 'cluster': 'examiner art unit (am7/prep-v1/meta.pkl)'}}
    for extra in ('samerun.json', 'validate-c0.json'):
        if (root / extra).exists():
            res[extra[:-5]] = json.load(open(root / extra))
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps({'arm_table': table, 'decision': decision,
                      'contrasts': {k: {m: {'delta': round(v[m]['delta'], 5), 'ci95': [round(x, 5) for x in v[m]['ci95']]}
                                        for m in v} for k, v in contrasts.items()}}, indent=1))
    print('DECIDE_DONE', flush=True)


def alloc_name(alloc):
    return 'alloc-' + '-'.join(f'{r}{n}' for r, n in zip(G03_ROUTES, alloc))


def routes_used(name):
    return [t[0] for t in name[6:].split('-') if int(t[1:])]


def f_star_rule(metrics):
    """g03_decide.decide() F* selection over the B = 4 allocations: best P1-DEV ALL R@200, ties within 0.0005 by fewest
    routes, then route priority Q, P, A, L, then score."""
    allocs4 = [x for x in metrics if x.startswith('alloc-') and sum(int(t[1:]) for t in x[6:].split('-')) == 4]
    best = max(metrics[x]['ALL_R@200']['mean'] for x in allocs4)
    near = [x for x in allocs4 if best - metrics[x]['ALL_R@200']['mean'] <= TIE]
    return min(near, key=lambda x: (len(routes_used(x)), sorted(PRIORITY.index(r) for r in routes_used(x)),
                                    -metrics[x]['ALL_R@200']['mean']))


def cmd_fusion(a):
    sub_ev, g03 = Path(a.sub_evals), Path(a.g03_evals)
    clusters = clusters_from_meta(a.meta)
    sub = {p.stem: load_eval(p) for p in sub_ev.glob('alloc-*.json')}
    orig_names = [p.stem for p in g03.glob('alloc-*.json')]
    orig_m = {n: load_eval(g03 / f'{n}.json', False) for n in orig_names}
    sub_m = {n: d['metrics'] for n, d in sub.items()}
    f_orig = f_star_rule(orig_m)
    f_sub = f_star_rule(sub_m)
    rr = alloc_name((1, 1, 1, 1))
    po = lambda n: load_eval(g03 / f'{n}.json')['per_query']
    row = lambda m: {k: m[f'{k}_R@200']['mean'] for k in KINDS}
    res = {'substituted': json.loads(a.substituted), 'budget': 4,
           'original_F_star': f_orig, 'original_F_star_R@200': row(orig_m[f_orig]),
           'substituted_F_star_rule_pick': f_sub, 'substituted_F_star_R@200': row(sub_m[f_sub]),
           'substituted_minus_original_F_star': paired_pq(sub[f_sub]['per_query'], po(f_orig), clusters),
           'RR_substituted_minus_original': paired_pq(sub[rr]['per_query'], po(rr), clusters),
           'grid_R@200': {n: {'substituted': row(sub_m[n]), 'original': row(orig_m[n]) if n in orig_m else None}
                          for n in sorted(sub_m)},
           'note': 'descriptive only (protocol §5); selection and contrast on the same P1-DEV data'}
    Path(a.out).write_text(json.dumps(res, indent=1))
    print(json.dumps({k: res[k] for k in ('substituted', 'original_F_star', 'substituted_F_star_rule_pick',
                                          'original_F_star_R@200', 'substituted_F_star_R@200')}, indent=1))
    print('FUSION_DONE', flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('gate', 'samerun', 'decide', 'fusion'))
    for x in ('eval-arctic', 'eval-bm25', 'summary-arctic', 'summary-bm25', 'new', 'ref', 'root', 'meta', 'g03-evals',
              'pairs', 'units-tsv', 'tasks', 'run-arctic-c0', 'run-bm25-c0', 'sub-evals', 'substituted', 'out'):
        ap.add_argument('--' + x)
    a = ap.parse_args()
    {'gate': cmd_gate, 'samerun': cmd_samerun, 'decide': cmd_decide, 'fusion': cmd_fusion}[a.cmd](a)


if __name__ == '__main__':
    main()
