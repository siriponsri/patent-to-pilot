"""P1 BridgeRet amendment AM-6: forgetting / domain trade-off report (descriptive only; never used to choose S*).

Compares each fine-tuned run with the zero-shot base model on the SAME block, using the per-query rows written by
eval_bridgeret_dev.py. For OUT, IN and ALL Recall@200 (conditional) it reports the paired mean delta over queries
present in both files, a paired bootstrap 95% CI (B = 10,000, seed 20261119, resampling queries) and wins/losses/ties.
Descriptive flag (fixed before any fine-tuned number): IN_TRADEOFF when the IN point delta is below -0.020 (the margin
used in P1-DAPFAM). The flag is a label for the report, not a test and not a selection rule.
Usage: python3 bridgeret_forgetting_report.py <base-eval.json> <out.json> <name>=<ft-eval.json> [...]
"""
import json, sys

import numpy as np

METRICS = ('OUT_R@200', 'IN_R@200', 'ALL_R@200')
SEED, B, IN_MARGIN = 20261119, 10000, 0.020
TEST_BLOCKS = ('P1-TEST', 'P2-TEST', 'P3-TEST')


def load(p):
    d = json.load(open(p, encoding='utf-8'))
    if d.get('block') in TEST_BLOCKS:
        raise SystemExit(f'refusing TEST block in {p}')
    return d


def paired(base_pq, ft_pq, metric, rng):
    qs = sorted(q for q in base_pq if metric in base_pq[q] and q in ft_pq and metric in ft_pq[q])
    if not qs:
        return None
    d = np.array([ft_pq[q][metric] - base_pq[q][metric] for q in qs])
    n = len(d)
    means = np.empty(B)
    for s in range(0, B, 500):                       # chunks keep memory small for ~26k queries
        k = min(500, B - s)
        means[s:s + k] = d[rng.integers(0, n, size=(k, n))].mean(axis=1)
    lo, hi = np.quantile(means, [0.025, 0.975])
    return {'n': n, 'delta': round(float(d.mean()), 5), 'ci95': [round(float(lo), 5), round(float(hi), 5)],
            'wins': int((d > 0).sum()), 'losses': int((d < 0).sum()), 'ties': int((d == 0).sum())}


def main(argv):
    base_p, out_p, pairs = argv[0], argv[1], argv[2:]
    base = load(base_p)
    res = {'format': 'ptp-bridgeret-forgetting-v1', 'amendment': 'AM-6', 'descriptive_only': True,
           'block': base['block'], 'base': base_p, 'seed': SEED, 'B': B, 'in_margin': IN_MARGIN, 'configs': {}}
    for item in pairs:
        name, path = item.split('=', 1)
        ft = load(path)
        if ft['block'] != base['block']:
            raise SystemExit(f'block mismatch: {name} {ft["block"]} vs {base["block"]}')
        rng = np.random.default_rng(SEED)            # same resampling stream for every config
        row = {m: paired(base['per_query'], ft['per_query'], m, rng) for m in METRICS}
        row['IN_TRADEOFF'] = bool(row['IN_R@200'] and row['IN_R@200']['delta'] < -IN_MARGIN)
        row['means'] = {m: ft['metrics'].get(m, {}).get('mean') for m in METRICS}
        res['configs'][name] = row
    res['base_means'] = {m: base['metrics'].get(m, {}).get('mean') for m in METRICS}
    json.dump(res, open(out_p, 'w', encoding='utf-8'), indent=1)
    for name, row in res['configs'].items():
        print(name, {m: row[m]['delta'] if row[m] else None for m in METRICS}, 'IN_TRADEOFF' if row['IN_TRADEOFF'] else '')


if __name__ == '__main__':
    main(sys.argv[1:])
