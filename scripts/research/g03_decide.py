"""G03 DEV selection and decision (protocol docs/healthtech/research/g03-dev/G03-DEV-PROTOCOL.md §7, frozen ec720914).

Evaluator side: reads the unchanged evaluator's outputs (evals/<block>/<arm>.json, with per-query rows) and, for clusters only,
the examiner art unit from the AM-7 prep metadata. Never reads TEST.

  gate:   E01 reproduction gate (B = 1 arms equal the existing single-route summaries to 4 decimals) + anchor dense / best route
  decide: F*, SF*, D, RR, anchor-only; principal VAL contrast SF* - F* with cluster bootstrap; decision rule; descriptive tables
"""
from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
import sys

import numpy as np

ROUTES = ('L', 'Q', 'P', 'A')
RDIR = {'L': 'bm25', 'Q': 'z-qwen3', 'P': 'z-patembed', 'A': 'z-arctic'}
KINDS = ('ALL', 'IN', 'OUT')
DELTA, TIE, SEED, B = 0.005, 0.0005, 20261119, 10000
PRIORITY = ('Q', 'P', 'A', 'L')   # protocol §4 tie order for F*


def alloc_name(alloc):
    return 'alloc-' + '-'.join(f'{r}{n}' for r, n in zip(ROUTES, alloc))


def single(r, n=1):
    return alloc_name(tuple(n if x == r else 0 for x in ROUTES))


def load(evals: Path, block: str, arm: str, per_query=False):
    d = json.load(open(evals / block / f'{arm}.json'))
    return d if per_query else d['metrics']


def mean(m, key):
    return m[key]['mean']


def cluster_bootstrap(values, clusters, b=B, seed=SEED):
    v = np.asarray(values, dtype=np.float64)
    uniq, inv = np.unique(np.asarray(clusters), return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(uniq))
    cnts = np.bincount(inv, minlength=len(uniq)).astype(np.float64)
    rng = np.random.default_rng(seed)
    w = rng.multinomial(len(uniq), np.full(len(uniq), 1.0 / len(uniq)), size=b).astype(np.float64)
    means = (w @ sums) / (w @ cnts)
    return float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def gate(a):
    ev, out, ok = Path(a.evals), {'checks': []}, True
    for block in ('P1-DEV', 'VAL'):
        for r in ROUTES:
            mine = load(ev, block, single(r))
            ref = json.load(open(Path(a.summaries) / RDIR[r] / f'summary-{block}.json'))['metrics']
            for k in KINDS:
                key = f'{k}_R@200'
                same = round(mine[key]['mean'], 4) == round(ref[key]['mean'], 4) and mine[key]['n'] == ref[key]['n']
                ok &= same
                out['checks'].append({'block': block, 'route': r, 'metric': key, 'g03': mine[key]['mean'],
                                      'summary': ref[key]['mean'], 'n': mine[key]['n'], 'equal_4dp': same})
    dev = {r: mean(load(ev, 'P1-DEV', single(r)), 'ALL_R@200') for r in ROUTES}
    out['p1dev_ALL_R@200_single'] = dev
    out['anchor_dense'] = max(('Q', 'P', 'A'), key=lambda r: (dev[r], -ROUTES.index(r)))
    out['best_single'] = max(ROUTES, key=lambda r: (dev[r], -ROUTES.index(r)))
    out['gate_passed'] = bool(ok)
    print(json.dumps(out, indent=1))
    if not ok:
        sys.exit('E01 reproduction gate FAILED: stop before reading any other arm')


def paired(ev, block, arm_a, arm_b, clusters):
    pa = load(ev, block, arm_a, True)['per_query']
    pb = load(ev, block, arm_b, True)['per_query']
    res = {}
    for k in KINDS:
        key = f'{k}_R@200'
        apps = sorted(q for q in pa if key in pa[q] and key in pb.get(q, {}))
        d = [pa[q][key] - pb[q][key] for q in apps]
        cl = [clusters.get(q, 'q:' + q) for q in apps]
        m, lo, hi = cluster_bootstrap(d, cl)
        res[key] = {'delta': m, 'ci95': [lo, hi], 'n': len(apps), 'wins': int(sum(x > 0 for x in d)),
                    'losses': int(sum(x < 0 for x in d))}
    return res


def decide(a):
    ev = Path(a.evals)
    g = json.load(open(ev.parent / 'gate.json'))
    if not g['gate_passed']:
        sys.exit('gate not passed')
    meta = pickle.load(open(a.meta, 'rb'))
    clusters = {b: {q['app']: str(q.get('au') or 'q:' + q['app']) for q in meta['queries'][b]} for b in ('P1-DEV', 'VAL')}
    arms = {b: sorted(p.stem for p in (ev / b).glob('*.json')) for b in ('P1-DEV', 'VAL')}
    metrics = {b: {arm: load(ev, b, arm) for arm in arms[b]} for b in arms}
    allocs4 = [x for x in arms['P1-DEV'] if x.startswith('alloc-') and sum(int(t[1:]) for t in x[6:].split('-')) == 4]

    def routes_used(name):
        return [t[0] for t in name[6:].split('-') if int(t[1:])]

    dev = metrics['P1-DEV']
    best = max(mean(dev[x], 'ALL_R@200') for x in allocs4)
    near = [x for x in allocs4 if best - mean(dev[x], 'ALL_R@200') <= TIE]
    f_star = min(near, key=lambda x: (len(routes_used(x)), sorted(PRIORITY.index(r) for r in routes_used(x)),
                                      -mean(dev[x], 'ALL_R@200')))
    sfn, sfc = mean(dev['sf-v0n-B4'], 'ALL_R@200'), mean(dev['sf-v0c-B4'], 'ALL_R@200')
    sf_star = 'sf-v0c-B4' if sfc - sfn > TIE else 'sf-v0n-B4'
    d_arm = single(g['best_single'], 4)
    rr = alloc_name((1, 1, 1, 1))
    anchor = alloc_name(tuple(1 if r in ('L', g['anchor_dense']) else 0 for r in ROUTES))
    sel = {'F_star': f_star, 'SF_star': sf_star, 'D': d_arm, 'RR': rr, 'anchor_only_B2': anchor,
           'p1dev_ALL_R@200': {'F_star': mean(dev[f_star], 'ALL_R@200'), 'sf-v0n-B4': sfn, 'sf-v0c-B4': sfc}}
    principal = paired(ev, 'VAL', sf_star, f_star, clusters['VAL'])
    all_, in_, out_ = (principal[f'{k}_R@200']['ci95'] for k in KINDS)
    holds = in_[0] > -DELTA and out_[0] > -DELTA
    if all_[0] > 0 and holds:
        decision = 'CONTINUE: adaptive allocation beats the best fixed allocation with IN and OUT non-inferior'
    elif all_[1] < 0 or not holds:
        decision = 'PARK adaptive allocation: F* stays the static default' + ('' if holds else ' (IN or OUT inferior)')
    else:
        decision = 'REVISE: ALL CI includes 0 and IN/OUT hold; record a mechanism-level hypothesis before v1'
    mech = {}
    for block in ('P1-DEV', 'VAL'):
        for lab, other in (('SF*-RR', rr), ('SF*-D', d_arm), ('SF*-anchor_only', anchor)):
            mech[f'{block}|{lab}'] = paired(ev, block, sf_star, other, clusters[block])
        mech[f'{block}|SF*-F*'] = paired(ev, block, sf_star, f_star, clusters[block])
    sweep = {}
    for block in ('P1-DEV', 'VAL'):
        for b in (2, 3, 4):
            ab = [x for x in arms['P1-DEV'] if x.startswith('alloc-') and sum(int(t[1:]) for t in x[6:].split('-')) == b]
            fb = max(ab, key=lambda x: mean(dev[x], 'ALL_R@200'))   # best fixed per budget, chosen on P1-DEV
            row = {'F_best_on_dev': fb}
            for lab, arm in (('F', fb), ('SF-v0n', f'sf-v0n-B{b}'), ('SF-v0c', f'sf-v0c-B{b}')):
                m = metrics[block][arm]
                row[lab] = {k: mean(m, f'{k}_R@200') for k in KINDS}
            sweep[f'{block}|B{b}'] = row
    table = {block: {arm: {k: mean(metrics[block][arm], f'{k}_R@200') for k in KINDS}
                     | {'OUT_MRR': mean(metrics[block][arm], 'OUT_MRR')} for arm in arms[block]} for block in arms}
    res = {'format': 'ptp-g03-dev-v1', 'protocol': 'docs/healthtech/research/g03-dev/G03-DEV-PROTOCOL.md@ec720914',
           'gate': g, 'selection_on_P1-DEV': sel, 'principal_VAL_SFstar_minus_Fstar': principal, 'delta_margin': DELTA,
           'decision': decision, 'mechanism_descriptive': mech, 'budget_sweep': sweep, 'arm_table': table}
    json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps({'selection': sel, 'principal': principal, 'decision': decision}, indent=1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=('gate', 'decide'))
    ap.add_argument('--evals', required=True)
    ap.add_argument('--summaries')
    ap.add_argument('--meta')
    ap.add_argument('--out')
    args = ap.parse_args()
    gate(args) if args.cmd == 'gate' else decide(args)
