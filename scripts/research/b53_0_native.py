"""B53.0 native DAPFAM metrics (plans/B53-0-AMENDMENT-20261122.md): nDCG@100 and Recall@100, ALL/IN/OUT, TAC->TAC,
from the frozen B53 runs. Evaluator side (reads qrels-pos.jsonl). Writes aggregates only.

Usage: python3 b53_0_native.py <inputs_dir> <runs_dir> <out_json>
"""
import gzip, json, math, sys
from pathlib import Path

PAPER = {'F3': {'nDCG@100': {'ALL': 0.3055, 'IN': 0.3477, 'OUT': 0.0482}, 'R@100': {'ALL': 0.3627, 'IN': 0.4437, 'OUT': 0.1311}},
         'F1': {'nDCG@100': {'ALL': 0.2451, 'IN': 0.2759, 'OUT': 0.0418}, 'R@100': {'ALL': 0.2820, 'IN': 0.3463, 'OUT': 0.1117}}}
TOL = 0.010


def read_run(p):
    op = gzip.open if str(p).endswith('.gz') else open
    out = {}
    with op(p, 'rt', encoding='utf-8') as f:
        for line in f:
            q, r, fam, _ = line.rstrip('\n').split('\t')
            if r == 'rank':
                continue
            out.setdefault(q, []).append((int(r), fam))
    return {q: [f for _, f in sorted(v)] for q, v in out.items()}


def metrics(ranked, pos, graded):
    top = ranked[:100]
    rel = {f: (s if graded else 1.0) for f, s in pos.items()}
    dcg = sum(rel[f] / math.log2(i + 2) for i, f in enumerate(top) if f in rel)
    ideal = sorted(rel.values(), reverse=True)[:100]
    idcg = sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
    return dcg / idcg, sum(1 for f in top if f in rel) / len(rel)


def main(in_dir, runs_dir, out_json):
    pos = {}
    for line in open(Path(in_dir) / 'qrels-pos.jsonl', encoding='utf-8'):
        r = json.loads(line)
        for view in ('ALL', r['domain']):
            pos.setdefault(view, {}).setdefault(r['query_id'], {})[r['family']] = float(r['score'])
    scores = sorted({s for v in pos['ALL'].values() for s in v.values()})
    res = {'format': 'ptp-b53-0-v1', 'amendment': 'plans/B53-0-AMENDMENT-20261122.md', 'task': 'TAC->TAC',
           'n_queries_with_positives': {v: len(pos[v]) for v in pos}, 'distinct_relevance_scores': scores[:20],
           'tolerance': TOL, 'systems': {}}
    for arm in ('F0', 'F1', 'F2', 'F3', 'F4'):
        p = Path(runs_dir) / f'{arm}.tsv.gz'
        if not p.exists():
            p = Path(runs_dir) / f'{arm}.tsv'
        run = read_run(p)
        row = {}
        for graded in (False, True):
            tag = 'graded' if graded else 'binary'
            for view in ('ALL', 'IN', 'OUT'):
                vals = [metrics(run.get(q, []), P, graded) for q, P in pos[view].items()]
                row.setdefault(f'nDCG@100_{tag}', {})[view] = sum(v[0] for v in vals) / len(vals)
                row.setdefault('R@100', {})[view] = sum(v[1] for v in vals) / len(vals)
        if arm in PAPER:
            cmp = {}
            for m, key in (('nDCG@100', 'nDCG@100_binary'), ('R@100', 'R@100')):
                for view, pv in PAPER[arm][m].items():
                    d = row[key][view] - pv
                    cmp[f'{m}|{view}'] = {'ours': round(row[key][view], 4), 'paper': pv, 'delta': round(d, 4),
                                          'verdict': 'consistent' if abs(d) <= TOL else 'differs'}
            row['vs_paper'] = cmp
        res['systems'][arm] = row
    json.dump(res, open(out_json, 'w'), indent=1)
    print(json.dumps({a: r.get('vs_paper', {k: {v: round(x, 4) for v, x in r['nDCG@100_binary'].items()} for k in ['x']})
                      for a, r in res['systems'].items()}, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])
