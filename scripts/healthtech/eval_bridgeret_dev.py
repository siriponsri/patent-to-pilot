"""BridgeRet DEV/VAL evaluator (pre-declaration section 2). Developer-visible labels only (pairs-dev.tsv).

Per query q of the block: positives = units of K(q) with first_pub < filing_date(q), excluding q's own unit.
  conditional set = positives present in Challenge-1M; strict set = positives with a known date (absent = miss).
  OUT/IN by dom_ipc3 (NOIPC counts in ALL only).
Metrics (query-macro over queries whose relevant set is non-empty): Recall@200 and @1000 (OUT, IN, ALL; conditional
and strict for OUT), OUT nDCG@10, OUT MRR. A query missing from the run scores 0.
Usage: python3 -I eval_bridgeret_dev.py <run.tsv> <pairs-dev.tsv> <corpus-units.tsv> <tasks.tsv> <BLOCK> <out.json>
"""
import csv, json, math, sys
from collections import defaultdict


def main(argv):
    run_p, pairs_p, units_p, tasks_p, block, out = argv
    if block in ('P1-TEST', 'P2-TEST', 'P3-TEST'):
        raise SystemExit('dev evaluator refuses TEST blocks')
    corpus = {}
    with open(units_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            corpus[r['unit_id']] = r['first_pub']
    fd = {}
    with open(tasks_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            fd[r['app_id']] = r['filing_date']
    rel = defaultdict(lambda: defaultdict(set))   # app -> kind -> units
    with open(pairs_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r['block'] != block or not r['unit'] or not r['unit_first_pub']:
                continue
            a, u = r['app_id'], r['unit']
            if r['unit_first_pub'] >= fd[a] or u == 'A:' + a:
                continue
            kinds = ['ALL'] + (['OUT'] if r['dom_ipc3'] == 'OUT3' else ['IN'] if r['dom_ipc3'] == 'IN3' else [])
            for k in kinds:
                rel[a][k + '_strict'].add(u)
                if u in corpus:
                    rel[a][k].add(u)
    ranked = defaultdict(list)
    with open(run_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            ranked[r['app_id']].append((int(r['rank']), r['unit']))
    ranked = {a: [u for _, u in sorted(v)] for a, v in ranked.items()}
    acc = defaultdict(list)
    per_q = {}
    for a, kinds in rel.items():
        lst = ranked.get(a, [])
        pos = {u: i for i, u in enumerate(lst)}
        row = {}
        for k, units in kinds.items():
            if not units:
                continue
            for cut in (200, 1000):
                v = sum(1 for u in units if pos.get(u, 10 ** 9) < cut) / len(units)
                acc[f'{k}_R@{cut}'].append(v); row[f'{k}_R@{cut}'] = v
            if k == 'OUT':
                dcg = sum(1 / math.log2(pos[u] + 2) for u in units if pos.get(u, 99) < 10)
                idcg = sum(1 / math.log2(i + 2) for i in range(min(10, len(units))))
                first = min((pos[u] for u in units if u in pos), default=None)
                acc['OUT_nDCG@10'].append(dcg / idcg); acc['OUT_MRR'].append(1 / (first + 1) if first is not None else 0.0)
        per_q[a] = row
    res = {'block': block, 'run': run_p, 'n_queries_run': len(ranked),
           'metrics': {k: {'mean': round(sum(v) / len(v), 5), 'n': len(v)} for k, v in sorted(acc.items())}}
    json.dump({**res, 'per_query': per_q}, open(out, 'w'), indent=None)
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
