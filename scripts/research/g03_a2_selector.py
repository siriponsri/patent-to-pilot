"""G03 amendment 2: learned per-query allocation selector (docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-2-20261122.md).

Features: runtime-observable route statistics only (scores at ranks 1/10/50/200, s1 - s200, presence; pairwise top-200
overlap). Targets: TRAIN-sample per-query ALL R@200 of each B = 4 allocation (unchanged evaluator). Realised P1-DEV/VAL
values are read from the protocol-v1 per-query evaluations of the selected allocation.
Usage: python g03_a2_selector.py --g03 /data/ptp-paper2/g03-dev --bridgeret /data/ptp-paper2/bridgeret --out results-a2.json
"""
import argparse, gzip, itertools, json, pickle
from pathlib import Path

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROUTES = ('L', 'Q', 'P', 'A')
FSTAR = 'alloc-L0-Q2-P2-A0'
PRIORITY = ('Q', 'P', 'A', 'L')
KINDS = ('ALL', 'IN', 'OUT')
DELTA, TIE, SEED, B = 0.005, 0.0005, 20261119, 10000


def allocs():
    return ['alloc-' + '-'.join(f'{r}{n}' for r, n in zip(ROUTES, c))
            for c in itertools.product(range(5), repeat=4) if sum(c) == 4]


def read_top(path, only=None, k=200):
    out = {}
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        next(f)
        for line in f:
            a, r, u, s = line.rstrip('\n').split('\t')
            if int(r) > k or (only is not None and a not in only):
                continue
            out.setdefault(a, []).append((int(r), u, float(s)))
    return {a: ([u for _, u, _ in sorted(v)], [s for _, _, s in sorted(v)]) for a, v in out.items()}


def features(apps, tops):
    X = np.zeros((len(apps), len(ROUTES) * 6 + 6), dtype=np.float64)
    for i, a in enumerate(apps):
        sets = {}
        for j, r in enumerate(ROUTES):
            units, sc = tops[r].get(a, ([], []))
            sets[r] = set(units)
            if sc:
                at = lambda n: sc[min(n, len(sc)) - 1]
                X[i, j * 6:(j + 1) * 6] = [at(1), at(10), at(50), at(200), at(1) - at(200), 1.0]
        for p, (r1, r2) in enumerate(itertools.combinations(ROUTES, 2)):
            X[i, len(ROUTES) * 6 + p] = len(sets[r1] & sets[r2]) / 200.0
    return X


def cluster_bootstrap(values, clusters):
    v = np.asarray(values, dtype=np.float64)
    uniq, inv = np.unique(np.asarray(clusters), return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(uniq)); cnts = np.bincount(inv, minlength=len(uniq)).astype(float)
    w = np.random.default_rng(SEED).multinomial(len(uniq), np.full(len(uniq), 1 / len(uniq)), size=B).astype(float)
    m = (w @ sums) / (w @ cnts)
    return float(v.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--g03', required=True); ap.add_argument('--bridgeret', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    g, br = Path(a.g03), Path(a.bridgeret)
    arms = allocs()
    sample = set(json.loads((g / 'a2/train-sample.json').read_text()))
    rdir = {'L': 'bm25', 'Q': 'z-qwen3', 'P': 'z-patembed', 'A': 'z-arctic'}
    train_paths = {'L': br / 'runs/bm25-train/run-TRAIN.tsv.gz', 'Q': br / 'runs/z-qwen3/run-TRAIN.tsv.gz',
                   'P': g / 'a2/z-patembed-train/run-TRAIN.tsv.gz', 'A': br / 'runs/z-arctic/run-TRAIN.tsv.gz'}
    # ---- TRAIN
    tops = {r: read_top(p, sample) for r, p in train_paths.items()}
    ytr = {arm: json.load(open(g / f'evals-a2/TRAIN/{arm}.json'))['per_query'] for arm in arms}
    tr_apps = sorted(q for q in ytr[FSTAR] if 'ALL_R@200' in ytr[FSTAR][q] and q in sample)
    Xtr = features(tr_apps, tops)
    Y = {arm: np.array([ytr[arm][q]['ALL_R@200'] for q in tr_apps]) for arm in arms}
    models = {'LS-ridge': lambda: make_pipeline(StandardScaler(), Ridge(alpha=1.0)),
              'LS-hgb': lambda: HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=31,
                                                              random_state=0)}
    fitted = {name: {arm: mk().fit(Xtr, Y[arm]) for arm in arms} for name, mk in models.items()}
    order = sorted(arms, key=lambda x: (x != FSTAR,))   # F* first on ties
    meta = pickle.load(open(br / 'am7/prep-v1/meta.pkl', 'rb'))
    res = {'format': 'ptp-g03-dev-a2', 'amendment': 'G03-DEV-AMENDMENT-2-20261122.md', 'n_train': len(tr_apps),
           'train_mean_ALL_R@200': {arm: float(Y[arm].mean()) for arm in (FSTAR,)}, 'blocks': {}}
    realised = {}
    for block in ('P1-DEV', 'VAL'):
        pq = {arm: json.load(open(g / f'evals/{block}/{arm}.json'))['per_query'] for arm in arms}
        apps = sorted(q for q in pq[FSTAR] if 'ALL_R@200' in pq[FSTAR][q])
        btops = {r: read_top(br / 'runs' / rdir[r] / f'run-{block}.tsv.gz', set(apps)) for r in ROUTES}
        X = features(apps, btops)
        clusters = {q['app']: str(q.get('au') or 'q:' + q['app']) for q in meta['queries'][block]}
        oracle = float(np.mean([max(pq[arm][q]['ALL_R@200'] for arm in arms) for q in apps]))
        fs = float(np.mean([pq[FSTAR][q]['ALL_R@200'] for q in apps]))
        res['blocks'][block] = {'F_star_ALL': fs, 'oracle_ALL': oracle, 'selectors': {}}
        for name in models:
            P = np.column_stack([fitted[name][arm].predict(X) for arm in order])
            choice = [order[int(np.argmax(row))] for row in P]
            realised[(block, name)] = dict(zip(apps, choice))
            vals = {k: float(np.mean([pq[c][q][f'{k}_R@200'] for q, c in zip(apps, choice) if f'{k}_R@200' in pq[c][q]]))
                    for k in KINDS}
            dist = {}
            for c in choice:
                dist[c] = dist.get(c, 0) + 1
            res['blocks'][block]['selectors'][name] = {
                'R@200': vals, 'headroom_captured': (vals['ALL'] - fs) / (oracle - fs) if oracle > fs else None,
                'chosen_top': sorted(dist.items(), key=lambda kv: -kv[1])[:8]}
        res['blocks'][block]['_pq'] = None
        realised[(block, 'pq')] = pq
        realised[(block, 'clusters')] = clusters
    dev = res['blocks']['P1-DEV']['selectors']
    ls = 'LS-hgb' if dev['LS-hgb']['R@200']['ALL'] - dev['LS-ridge']['R@200']['ALL'] > TIE else 'LS-ridge'

    def paired(block, name):
        pq, ch, cl = realised[(block, 'pq')], realised[(block, name)], realised[(block, 'clusters')]
        out = {}
        for k in KINDS:
            key = f'{k}_R@200'
            qs = [q for q in ch if key in pq[ch[q]][q] and key in pq[FSTAR][q]]
            d = [pq[ch[q]][q][key] - pq[FSTAR][q][key] for q in qs]
            m, lo, hi = cluster_bootstrap(d, [cl.get(q, 'q:' + q) for q in qs])
            out[key] = {'delta': m, 'ci95': [lo, hi], 'n': len(qs), 'wins': int(sum(x > 0 for x in d)),
                        'losses': int(sum(x < 0 for x in d))}
        return out
    principal = paired('VAL', ls)
    lo, hi = principal['ALL_R@200']['ci95']
    holds = all(principal[f'{k}_R@200']['ci95'][0] > -DELTA for k in ('IN', 'OUT'))
    decision = ('CONTINUE: learned selector beats F* with IN/OUT non-inferior' if lo > 0 and holds else
                'PARK learned selector' + ('' if holds else ' (IN or OUT inferior)') if hi < 0 or not holds else
                'REVISE: ALL CI includes 0, IN/OUT hold')
    for b in res['blocks']:
        res['blocks'][b].pop('_pq', None)
    res.update({'LS_star': ls, 'principal_VAL_LSstar_minus_Fstar': principal, 'decision': decision,
                'descriptive_P1DEV_LSstar_minus_Fstar': paired('P1-DEV', ls)})
    json.dump(res, open(a.out, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('n_train', 'LS_star', 'principal_VAL_LSstar_minus_Fstar', 'decision')}, indent=1))
    print(json.dumps(res['blocks'], indent=1)[:3000])


if __name__ == '__main__':
    main()
