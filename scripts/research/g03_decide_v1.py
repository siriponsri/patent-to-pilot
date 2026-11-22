"""G03 amendment 1 decision (docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-1-20261122.md).

Routes L, Q, P, T (PatEmbed title+abstract), C (PatEmbed first independent claim). Evaluator side.
F* (protocol v1) = Q2 + P2, which in the amendment namespace is alloc-L0-Q2-P2-T0-C0 (identical windows and scorer);
its per-query values are checked against the protocol-v1 evaluation before use.
Usage: python g03_decide_v1.py --evals evals-a1 --v0-evals evals --meta meta.pkl --out results-a1.json
"""
import argparse, json, pickle
from pathlib import Path

import numpy as np

ROUTES = ('L', 'Q', 'P', 'T', 'C')
PRIORITY = ('P', 'Q', 'T', 'C', 'L')
KINDS = ('ALL', 'IN', 'OUT')
DELTA, TIE, SEED, B = 0.005, 0.0005, 20261119, 10000
FSTAR_A1, FSTAR_V0 = 'alloc-L0-Q2-P2-T0-C0', 'alloc-L0-Q2-P2-A0'


def cluster_bootstrap(values, clusters):
    v = np.asarray(values, dtype=np.float64)
    uniq, inv = np.unique(np.asarray(clusters), return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(uniq)); cnts = np.bincount(inv, minlength=len(uniq)).astype(float)
    w = np.random.default_rng(SEED).multinomial(len(uniq), np.full(len(uniq), 1 / len(uniq)), size=B).astype(float)
    m = (w @ sums) / (w @ cnts)
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def alloc_of(name):
    return {t[0]: int(t[1:]) for t in name[6:].split('-')}


def main():
    ap = argparse.ArgumentParser()
    for k in ('--evals', '--v0-evals', '--meta', '--out'):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    ev, ev0 = Path(a.evals), Path(a.v0_evals)
    load = lambda d, b, arm: json.load(open(d / b / f'{arm}.json'))
    meta = pickle.load(open(a.meta, 'rb'))
    clusters = {b: {q['app']: str(q.get('au') or 'q:' + q['app']) for q in meta['queries'][b]} for b in ('P1-DEV', 'VAL')}
    # integrity: F* in both namespaces must give identical per-query values
    integrity = {}
    for b in ('P1-DEV', 'VAL'):
        x, y = load(ev, b, FSTAR_A1)['per_query'], load(ev0, b, FSTAR_V0)['per_query']
        integrity[b] = x == y
    if not all(integrity.values()):
        raise SystemExit(f'F* mismatch between namespaces: {integrity}')
    dev = {p.stem: json.load(open(p))['metrics'] for p in (ev / 'P1-DEV').glob('alloc-*.json')}
    allocs4 = [n for n in dev if sum(alloc_of(n).values()) == 4]
    best = max(dev[n]['ALL_R@200']['mean'] for n in allocs4)
    near = [n for n in allocs4 if best - dev[n]['ALL_R@200']['mean'] <= TIE]
    used = lambda n: [r for r, c in alloc_of(n).items() if c]
    f1 = min(near, key=lambda n: (len(used(n)), sorted(PRIORITY.index(r) for r in used(n)), -dev[n]['ALL_R@200']['mean']))
    uses_obligation = any(alloc_of(f1)[r] for r in ('T', 'C'))

    def paired(block, arm_a, arm_b):
        pa, pb = load(ev, block, arm_a)['per_query'], load(ev, block, arm_b)['per_query']
        out = {}
        for k in KINDS:
            key = f'{k}_R@200'
            qs = sorted(q for q in pa if key in pa[q] and key in pb.get(q, {}))
            d = [pa[q][key] - pb[q][key] for q in qs]
            m, lo, hi = cluster_bootstrap(d, [clusters[block].get(q, 'q:' + q) for q in qs])
            out[key] = {'delta': m, 'ci95': [lo, hi], 'n': len(qs), 'wins': int(sum(x > 0 for x in d)),
                        'losses': int(sum(x < 0 for x in d))}
        return out
    principal = paired('VAL', f1, FSTAR_A1) if f1 != FSTAR_A1 else None
    if not uses_obligation:
        decision = 'H-M1 NOT SUPPORTED on DEV: the best P1-DEV allocation uses no obligation route (T or C)'
    else:
        lo_all = principal['ALL_R@200']['ci95'][0]; hi_all = principal['ALL_R@200']['ci95'][1]
        holds = all(principal[f'{k}_R@200']['ci95'][0] > -DELTA for k in ('IN', 'OUT'))
        decision = ('CONTINUE: obligation routes improve ALL R@200 with IN/OUT non-inferior' if lo_all > 0 and holds else
                    'PARK obligation routes' + ('' if holds else ' (IN or OUT inferior)') if hi_all < 0 or not holds else
                    'REVISE: ALL CI includes 0, IN/OUT hold')
    desc = {f'{b}|SF-v1c-F1*': paired(b, 'sf-v1c-B4', f1) for b in ('P1-DEV', 'VAL')}
    desc.update({f'{b}|F1*-F*': paired(b, f1, FSTAR_A1) for b in ('P1-DEV',) if f1 != FSTAR_A1})
    table = {b: {p.stem: {k: json.load(open(p))['metrics'][f'{k}_R@200']['mean'] for k in KINDS}
                 for p in (ev / b).glob('*.json')} for b in ('P1-DEV', 'VAL')}
    res = {'format': 'ptp-g03-dev-a1', 'amendment': 'G03-DEV-AMENDMENT-1-20261122.md', 'integrity_Fstar_equal': integrity,
           'F1_star': f1, 'F1_star_uses_obligation_route': uses_obligation, 'principal_VAL_F1star_minus_Fstar': principal,
           'decision': decision, 'descriptive': desc, 'arm_table': table}
    json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('F1_star', 'F1_star_uses_obligation_route', 'principal_VAL_F1star_minus_Fstar',
                                          'decision', 'integrity_Fstar_equal')}, indent=1))


if __name__ == '__main__':
    main()
