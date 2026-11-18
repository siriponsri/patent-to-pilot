"""Reciprocal-rank fusion of BridgeRet run files (pre-declaration: E0 = RRF(BM25, best zero-shot dense), k = 60,
depth 1000 per list). Ties: higher fused score, then better best-rank, then unit id. Output top 1000.
Usage: python3 -I rrf_bridgeret.py <out.tsv> <run1.tsv> <run2.tsv> [...]
"""
import csv, sys
from collections import defaultdict

K, DEPTH, TOP = 60, 1000, 1000


def main(argv):
    out, runs = argv[0], argv[1:]
    fused = defaultdict(lambda: defaultdict(float))
    best = defaultdict(dict)
    for p in runs:
        with open(p, encoding='utf-8') as f:
            for r in csv.DictReader(f, delimiter='\t'):
                k = int(r['rank'])
                if k > DEPTH:
                    continue
                a, u = r['app_id'], r['unit']
                fused[a][u] += 1.0 / (K + k)
                best[a][u] = min(best[a].get(u, 10 ** 9), k)
    with open(out, 'w', encoding='utf-8') as g:
        g.write('app_id\trank\tunit\tscore\n')
        for a in sorted(fused):
            items = sorted(fused[a].items(), key=lambda x: (-x[1], best[a][x[0]], x[0]))[:TOP]
            g.write(''.join(f'{a}\t{i + 1}\t{u}\t{s:.6f}\n' for i, (u, s) in enumerate(items)))


if __name__ == '__main__':
    main(sys.argv[1:])
