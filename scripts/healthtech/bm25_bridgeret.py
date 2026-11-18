"""B-BM25 over Challenge-1M (pre-declaration section 4): k1=1.5, b=0.75, lowercase [a-z0-9]+ tokens,
no stemming/stop list, over the serialised passage text. RPD mask (first_pub < filing date) and self-unit
exclusion applied before top-k. Blocks run: those named on the command line (never TEST).
Output: run-<block>.tsv  app_id, rank, unit, score  (top 1000)
Usage: python3 -I bm25_bridgeret.py <serialised_dir> <corpus-units.tsv> <tasks.tsv> <out_dir> BLOCK [BLOCK...]
"""
import csv, json, sys, time
from pathlib import Path


K1, B, TOPK, QB = 1.5, 0.75, 1000, 64
PROTECTED = {'P1-TEST', 'P2-TEST', 'P3-TEST'}


def dint(s):  # YYYY-MM-DD -> int
    return int(s.replace('-', '')[:8]) if s else 0


def main(argv):
    d, units_p, tasks_p, out = Path(argv[0]), argv[1], argv[2], Path(argv[3])
    blocks = set(argv[4:])
    if blocks & PROTECTED:
        raise SystemExit('BM25 dev script refuses TEST blocks')
    import numpy as np
    from sklearn.feature_extraction.text import CountVectorizer
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    pub = {}
    with open(units_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            pub[r['unit_id']] = dint(r['first_pub'])
    units, texts = [], []
    for l in open(d / 'passages.jsonl', encoding='utf-8'):
        r = json.loads(l)
        units.append(r['unit']); texts.append(r['text'])
    uidx = {u: i for i, u in enumerate(units)}
    pubs = np.array([pub[u] for u in units], dtype=np.int64)
    cv = CountVectorizer(token_pattern=r'[a-z0-9]+', lowercase=True, dtype=np.float32)
    tf = cv.fit_transform(texts).tocsr()
    del texts
    n = tf.shape[0]
    dl = np.asarray(tf.sum(axis=1)).ravel()
    df = np.bincount(tf.indices, minlength=tf.shape[1])
    idf = np.log1p((n - df + 0.5) / (df + 0.5)).astype(np.float32)
    norm = K1 * (1 - B + B * dl / dl.mean())
    rows = np.repeat(np.arange(n), np.diff(tf.indptr))
    tf.data = (tf.data * (K1 + 1) / (tf.data + norm[rows]) * idf[tf.indices]).astype(np.float32)
    W = tf.T.tocsr()          # vocab x docs
    print('index built', n, tf.shape[1], round(time.time() - t0, 1), flush=True)
    fd = {}
    with open(tasks_p, encoding='utf-8') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            fd[r['app_id']] = dint(r['filing_date'])
    qs = [json.loads(l) for l in open(d / 'queries.jsonl', encoding='utf-8')]
    for blk in sorted(blocks):
        sel = [r for r in qs if r['block'] == blk]
        with open(out / f'run-{blk}.tsv', 'w', encoding='utf-8') as g:
            g.write('app_id\trank\tunit\tscore\n')
            for s in range(0, len(sel), QB):
                chunk = sel[s:s + QB]
                Q = cv.transform([r['text'] for r in chunk]).astype(np.float32)
                S = (Q @ W).toarray()
                for i, r in enumerate(chunk):
                    row = S[i]
                    row[pubs >= fd[r['app_id']]] = -np.inf
                    own = uidx.get('A:' + r['app_id'])
                    if own is not None:
                        row[own] = -np.inf
                    top = np.argpartition(-row, TOPK)[:TOPK]
                    top = top[np.lexsort((top, -row[top]))]
                    for k, j in enumerate(top):
                        if np.isfinite(row[j]) and row[j] > 0:   # only documents matching >= 1 query term
                            g.write(f"{r['app_id']}\t{k + 1}\t{units[j]}\t{row[j]:.4f}\n")
                if s % (QB * 20) == 0:
                    print(blk, s, round(time.time() - t0, 1), flush=True)
    print('done', round(time.time() - t0, 1))


if __name__ == '__main__':
    main(sys.argv[1:])
