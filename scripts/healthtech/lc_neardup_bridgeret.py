"""L-C near-duplicate audit (spec 01 section 6), DEV/VAL vs TRAIN, first independent claim only. Never TEST.

Shingles: 5-word shingles of the lowercased claim (\\w+ tokens), hashed once with blake2b-64; MinHash with 64 universal
hash functions (a*x+b mod 2^31-1, fixed seed 20261119); LSH 16 bands x 4 rows for candidates; a pair is a near-duplicate
if the estimated Jaccard (signature agreement) >= 0.8. Reports the share of queries per block with >= 1 TRAIN near-dup;
writes the per-query flag (dup=TRUE/FALSE) for stratified reporting.
Usage: python3 lc_neardup_bridgeret.py <texts_dir> <out_dir>
"""
import hashlib, json, re, sys
from collections import defaultdict
from pathlib import Path

import numpy as np

NP, BANDS, ROWS, K, THR = 64, 16, 4, 5, 0.8
P31 = (1 << 31) - 1
rng = np.random.default_rng(20261119)
A = rng.integers(1, P31, NP, dtype=np.uint64); B = rng.integers(0, P31, NP, dtype=np.uint64)


def sig(text):
    toks = re.findall(r'\w+', text.lower())
    sh = {' '.join(toks[i:i + K]) for i in range(max(1, len(toks) - K + 1))} if toks else set()
    if not sh:
        return None
    x = np.array([int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), 'big') % P31 for s in sh], dtype=np.uint64)
    v = (np.multiply.outer(A, x) + B[:, None]) % P31          # all operands < 2^31, products < 2^62: no overflow
    return v.min(axis=1)


def main(argv):
    d, out = Path(argv[0]), Path(argv[1]); out.mkdir(parents=True, exist_ok=True)
    qs = [json.loads(l) for l in open(d / 'queries.jsonl', encoding='utf-8')]
    qs = [r for r in qs if r.get('doc') and r.get('claim') and r['block'] in ('TRAIN', 'VAL', 'P1-DEV', 'P2-DEV')]
    sigs = {r['app_id']: sig(r['claim']) for r in qs}
    block = {r['app_id']: r['block'] for r in qs}
    buckets = defaultdict(list)
    for a, s in sigs.items():
        if s is not None and block[a] == 'TRAIN':
            for b in range(BANDS):
                buckets[(b, s[b * ROWS:(b + 1) * ROWS].tobytes())].append(a)
    flag, res = {}, {}
    for a, s in sigs.items():
        if block[a] == 'TRAIN':
            continue
        dup = False
        if s is not None:
            cand = {t for b in range(BANDS) for t in buckets.get((b, s[b * ROWS:(b + 1) * ROWS].tobytes()), ())}
            dup = any((sigs[t] == s).mean() >= THR for t in cand)
        flag[a] = dup
    for blk in ('VAL', 'P1-DEV', 'P2-DEV'):
        v = [flag[a] for a in flag if block[a] == blk]
        res[blk] = {'n': len(v), 'near_dup_in_TRAIN': sum(v), 'share': round(sum(v) / max(1, len(v)), 4)}
    (out / 'lc-flags.json').write_text(json.dumps(flag))
    (out / 'lc-summary.json').write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == '__main__':
    main(sys.argv[1:])
