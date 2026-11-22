"""G03 amendment 3 decisions (docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md §3-§4). Evaluator side.

  pilot --evals-root evals-a3-pilot --models m1,m2,.. --apps a3/apps-pilot.json --v0-evals evals --meta meta.pkl
        --costs costs.json --out results-a3-pilot.json
        evals-a3-pilot/<model_dir>/P1-DEV/<arm>.json for each model (routes L, Q, P, H, K)
  full  --evals evals-a3 --v0-evals evals --meta meta.pkl --out results-a3.json

F* (protocol v1) = alloc-L0-Q2-P2-A0 = alloc-L0-Q2-P2-H0-K0 here; its per-query values are checked against the protocol-v1
evaluation before any comparison.
"""
import argparse, json, pickle
from pathlib import Path

import numpy as np

ROUTES = ('L', 'Q', 'P', 'H', 'K')
PRIORITY = ('P', 'Q', 'H', 'K', 'L')
KINDS = ('ALL', 'IN', 'OUT')
DELTA, TIE, SEED, NB = 0.005, 0.0005, 20261119, 10000
FSTAR_A3, FSTAR_V0 = 'alloc-L0-Q2-P2-H0-K0', 'alloc-L0-Q2-P2-A0'


def cluster_bootstrap(values, clusters):
    v = np.asarray(values, dtype=np.float64)
    uniq, inv = np.unique(np.asarray(clusters), return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(uniq)); cnts = np.bincount(inv, minlength=len(uniq)).astype(float)
    w = np.random.default_rng(SEED).multinomial(len(uniq), np.full(len(uniq), 1 / len(uniq)), size=NB).astype(float)
    m = (w @ sums) / (w @ cnts)
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def alloc_of(name):
    return {t[0]: int(t[1:]) for t in name[6:].split('-')}


def uses_llm(name):
    a = alloc_of(name)
    return bool(a.get('H') or a.get('K'))


def per_query(path):
    return json.load(open(path))['per_query']


def mean_over(pq, apps, key):
    xs = [pq[a][key] for a in apps if a in pq and key in pq[a]]
    return float(np.mean(xs)) if xs else float('nan'), len(xs)


def paired(pa, pb, apps, clusters):
    out = {}
    for k in KINDS:
        key = f'{k}_R@200'
        qs = sorted(q for q in apps if key in pa.get(q, {}) and key in pb.get(q, {}))
        d = [pa[q][key] - pb[q][key] for q in qs]
        m, lo, hi = cluster_bootstrap(d, [clusters.get(q, 'q:' + q) for q in qs])
        out[key] = {'delta': m, 'ci95': [lo, hi], 'n': len(qs), 'wins': int(sum(x > 0 for x in d)),
                    'losses': int(sum(x < 0 for x in d))}
    return out


def clusters_of(meta_path):
    meta = pickle.load(open(meta_path, 'rb'))
    return {b: {q['app']: str(q.get('au') or 'q:' + q['app']) for q in meta['queries'][b]} for b in ('P1-DEV', 'VAL')}


def pilot(a):
    apps = sorted(json.load(open(a.apps)))
    cl = clusters_of(a.meta)['P1-DEV']
    costs = json.load(open(a.costs)) if a.costs else {}
    f0 = per_query(Path(a.v0_evals) / 'P1-DEV' / f'{FSTAR_V0}.json')
    fstar_mean = mean_over(f0, apps, 'ALL_R@200')[0]
    models = {}
    for m in a.models.split(','):
        d = Path(a.evals_root) / m.replace('/', '__') / 'P1-DEV'
        fx = per_query(d / f'{FSTAR_A3}.json')
        integrity = all(fx.get(q) == f0.get(q) for q in apps)
        if not integrity:
            raise SystemExit(f'F* mismatch for {m}')
        table = {}
        for p in d.glob('alloc-*.json'):
            pq = per_query(p)
            table[p.stem] = {k: mean_over(pq, apps, f'{k}_R@200')[0] for k in KINDS}
        b4 = [n for n in table if sum(alloc_of(n).values()) == 4 and uses_llm(n)]
        best = max(b4, key=lambda n: (table[n]['ALL'], -len([r for r, c in alloc_of(n).items() if c])))
        cmp_ = paired(per_query(d / f'{best}.json'), f0, apps, cl)
        models[m] = {'G_m': table[best]['ALL'], 'best_llm_alloc': best, 'best_IN': table[best]['IN'],
                     'best_OUT': table[best]['OUT'], 'delta_vs_Fstar': cmp_, 'integrity_Fstar_equal': integrity,
                     'single_route_B1': {n: table[n] for n in table if sum(alloc_of(n).values()) == 1},
                     'H4_K4': {n: table[n] for n in ('alloc-L0-Q0-P0-H4-K0', 'alloc-L0-Q0-P0-H0-K4') if n in table},
                     'pilot_cost_usd': costs.get(m), 'arm_table_B4': {n: table[n] for n in table
                                                                       if sum(alloc_of(n).values()) == 4}}
    top = max(v['G_m'] for v in models.values())
    near = [m for m, v in models.items() if top - v['G_m'] <= TIE]
    mstar = min(near, key=lambda m: (models[m]['pilot_cost_usd'] if models[m]['pilot_cost_usd'] is not None
                                     else float('inf'), -models[m]['G_m']))
    d = models[mstar]['delta_vs_Fstar']['ALL_R@200']
    go = d['delta'] >= DELTA and d['ci95'][0] > 0
    res = {'format': 'ptp-g03-dev-a3-pilot', 'amendment': 'G03-DEV-AMENDMENT-3-20261122.md', 'n_pilot': len(apps),
           'Fstar_pilot_ALL': fstar_mean, 'models': models, 'm_star': mstar,
           'decision': ('GO: Stage B with ' + mstar) if go else
           'STOP: H-M3 not supported on the pilot (Delta < +0.005 or lower CI <= 0); no Stage B spend',
           'note': 'pilot Delta is optimistic (best of ~66 LLM allocations on the same queries); it only gates spending'}
    json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('n_pilot', 'Fstar_pilot_ALL', 'm_star', 'decision')}, indent=1))
    for m, v in models.items():
        print(m, round(v['G_m'], 4), v['best_llm_alloc'], {k: [round(x, 4) for x in [w['delta']] + w['ci95']]
                                                             for k, w in v['delta_vs_Fstar'].items()})


def full(a):
    ev, ev0 = Path(a.evals), Path(a.v0_evals)
    cl = clusters_of(a.meta)
    integrity = {b: per_query(ev / b / f'{FSTAR_A3}.json') == per_query(ev0 / b / f'{FSTAR_V0}.json')
                 for b in ('P1-DEV', 'VAL')}
    if not all(integrity.values()):
        raise SystemExit(f'F* mismatch: {integrity}')
    dev = {p.stem: json.load(open(p))['metrics'] for p in (ev / 'P1-DEV').glob('alloc-*.json')}
    allocs4 = [n for n in dev if sum(alloc_of(n).values()) == 4]
    best = max(dev[n]['ALL_R@200']['mean'] for n in allocs4)
    near = [n for n in allocs4 if best - dev[n]['ALL_R@200']['mean'] <= TIE]
    used = lambda n: [r for r, c in alloc_of(n).items() if c]
    f3 = min(near, key=lambda n: (len(used(n)), sorted(PRIORITY.index(r) for r in used(n)), -dev[n]['ALL_R@200']['mean']))
    pq = lambda b, arm: per_query(ev / b / f'{arm}.json')
    val_apps = sorted(pq('VAL', FSTAR_A3))
    principal = paired(pq('VAL', f3), pq('VAL', FSTAR_A3), val_apps, cl['VAL']) if f3 != FSTAR_A3 else None
    if not uses_llm(f3):
        decision = 'H-M3 NOT SUPPORTED on DEV: the best P1-DEV allocation uses no LLM route (H or K)'
    else:
        lo_all, hi_all = principal['ALL_R@200']['ci95']
        holds = all(principal[f'{k}_R@200']['ci95'][0] > -DELTA for k in ('IN', 'OUT'))
        decision = ('CONTINUE: LLM routes improve ALL R@200 with IN/OUT non-inferior' if lo_all > 0 and holds else
                    'PARK LLM routes' + ('' if holds else ' (IN or OUT inferior)') if hi_all < 0 or not holds else
                    'REVISE: ALL CI includes 0, IN/OUT hold')
    dev_apps = sorted(pq('P1-DEV', FSTAR_A3))
    desc = {'P1-DEV|F3*-F*': paired(pq('P1-DEV', f3), pq('P1-DEV', FSTAR_A3), dev_apps, cl['P1-DEV'])
            if f3 != FSTAR_A3 else None}
    table = {b: {p.stem: {k: json.load(open(p))['metrics'][f'{k}_R@200']['mean'] for k in KINDS}
                 for p in (ev / b).glob('*.json')} for b in ('P1-DEV', 'VAL')}
    res = {'format': 'ptp-g03-dev-a3', 'amendment': 'G03-DEV-AMENDMENT-3-20261122.md', 'integrity_Fstar_equal': integrity,
           'F3_star': f3, 'F3_star_uses_llm_route': uses_llm(f3), 'principal_VAL_F3star_minus_Fstar': principal,
           'decision': decision, 'descriptive': desc, 'arm_table': table,
           'disclosed': 'fourth look at VAL in G03 (v1, A1, A2, A3); DEV phase only'}
    json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('F3_star', 'F3_star_uses_llm_route', 'principal_VAL_F3star_minus_Fstar',
                                          'decision', 'integrity_Fstar_equal')}, indent=1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('mode', choices=('pilot', 'full'))
    for k in ('--evals', '--evals-root', '--models', '--apps', '--costs'):
        ap.add_argument(k)
    for k in ('--v0-evals', '--meta', '--out'):
        ap.add_argument(k, required=True)
    args = ap.parse_args()
    pilot(args) if args.mode == 'pilot' else full(args)
