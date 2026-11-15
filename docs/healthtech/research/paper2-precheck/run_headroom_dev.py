"""Paper 2 pre-check: BM25 exposure headroom on DAPFAM dev, run ONCE (CPU, local).
Spec: HEADROOM-PREDECLARATION.md (committed before this script ran). Dev only; test untouched.
Public aggregates -> headroom-dev-result.json; per-query values -> private folder only."""
import hashlib, json, re, sys, time
from array import array
from collections import Counter
from pathlib import Path
import numpy as np
from scipy import sparse

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'src'))
from patent_to_pilot.evaluation.dapfam_native import native_dev_task, evaluate_paper1_dev, evaluate_native_dev
from patent_to_pilot.research.paper1_analysis import rrf_fuse, exposure_strata

P = REPO.parent / '_private_artifacts/healthtech'
S = P / 'ptp-dapfam-native-dev-20261110-v3'
CORPUS, QUERIES, QRELS = S / 'runtime-dev/corpus.jsonl', S / 'runtime-dev/queries-ta.jsonl', S / 'dev-evaluation/qrels-dev.jsonl'
B0F = P / 'ptp-paper1-a2-dev-20261115-v1/reference-top200-private.jsonl'
OUT_PRIVATE = P / 'ptp-paper2-headroom-dev-20261116-v1'
PUBLIC = HERE / 'headroom-dev-result.json'
PINS = {CORPUS: '42f895cd411b344f7be4de4c77bfab66797aa2a1d92353dbee82669fc569af0d',
        QUERIES: '6fa09d71c96b0e18f5b7986add7011d17ba6826bad753d7a0cc52a2ce5859d2a',
        QRELS: 'ca693dc8a1d5c5bf10249c8e9438be5198346349dcd1b6a6194e0eeb96923473',
        B0F: '1f0f738ff649a111f16292edb5c63bd27cb6b204f6bc6205dbef6e89323c61c9'}
S5_B0 = {'ALL': 0.34262, 'IN': 0.51370, 'OUT': 0.14772}
STOP = set('a an and are as at be by for from has have in into is it its of on or that the this to was were which with '
           'wherein said such being comprising thereof'.split())
K1, B, DEPTH = 0.9, 0.4, 200
METRICS = ('Recall@200', 'Recall@100', 'NDCG@10')
TOK = re.compile(r'[a-z0-9]+')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def tokens(text):
    return [t for t in TOK.findall(text.lower()) if t not in STOP]


def main():
    assert not PUBLIC.exists() and not OUT_PRIVATE.exists(), 'already run once'
    for p, h in PINS.items():
        assert sha(p) == h, p.name
    t0 = time.process_time()
    load = lambda p: [json.loads(l) for l in p.read_text(encoding='utf-8').splitlines() if l.strip()]
    # --- BM25 index
    vocab, ids, dls = {}, [], []
    rows, cols, vals = array('i'), array('i'), array('i')
    with open(CORPUS, encoding='utf-8') as fh:
        for i, line in enumerate(fh):
            r = json.loads(line)
            ids.append(r['id'])
            tf = Counter(tokens(' '.join((r['title'] or '', r['abstract'] or '', r['claims'] or ''))))
            dls.append(sum(tf.values()))
            for t, c in tf.items():
                rows.append(i); cols.append(vocab.setdefault(t, len(vocab))); vals.append(c)
    N = len(ids)
    tfm = sparse.csc_matrix((np.frombuffer(vals, dtype=np.int32).astype(np.float64), (np.frombuffer(rows, dtype=np.int32), np.frombuffer(cols, dtype=np.int32))), shape=(N, len(vocab)))
    del rows, cols, vals
    dl = np.array(dls, dtype=np.float64); avgdl = dl.mean()
    df = np.diff(tfm.indptr)
    idf = np.log(1.0 + (N - df + 0.5) / (df + 0.5))
    W = tfm.tocoo()
    norm = K1 * (1 - B + B * dl[W.row] / avgdl)
    W = sparse.csc_matrix((idf[W.col] * W.data * (K1 + 1) / (W.data + norm), (W.row, W.col)), shape=W.shape)
    id_arr = np.array(ids)
    order_ids = np.argsort(id_arr, kind='stable')
    id_rank = np.empty(N, dtype=np.int64); id_rank[order_ids] = np.arange(N)  # rank of id in ascending id order
    pos = {f: i for i, f in enumerate(ids)}
    queries = load(QUERIES)
    bm25 = {}
    for q in queries:
        terms = sorted({vocab[t] for t in tokens(q['text']) if t in vocab})
        score = np.asarray(W[:, terms].sum(axis=1)).ravel() if terms else np.zeros(N)
        if q['id'] in pos:
            score[pos[q['id']]] = 0.0  # self-exclusion (BM25 only)
        cand = np.nonzero(score > 0)[0]
        cand = cand[np.lexsort((id_rank[cand], -score[cand]))][:DEPTH]
        bm25[q['id']] = [ids[i] for i in cand]
    index_stats = {'documents': N, 'vocabulary': len(vocab), 'avgdl': round(float(avgdl), 3),
                   'queries_with_fewer_than_200_bm25_results': sum(len(v) < DEPTH for v in bm25.values())}
    # --- systems
    b0 = {r['query_id']: r['families'] for r in load(B0F)}
    assert set(b0) == set(bm25)
    rrf = {q: rrf_fuse(b0[q], bm25[q]) for q in b0}
    u400 = {q: b0[q] + [f for f in bm25[q] if f not in set(b0[q])] for q in b0}
    systems = {'B0': b0, 'BM25': bm25, 'RRF': rrf}
    corpus_rows = [{'relevant_id': f, 'title_en': '', 'abstract_en': '', 'claims_text': ''} for f in ids]
    query_rows = [{'query_id': q['id'], 'title_en': '', 'abstract_en': ''} for q in queries]
    relations = load(QRELS)
    public, private = {}, {}
    for part in ('ALL', 'IN', 'OUT'):
        task = native_dev_task(corpus_rows, query_rows, relations, partition=part)
        elig = sorted(task['qrels'])
        res = {n: evaluate_paper1_dev(task, {q: t[q] for q in elig}) for n, t in systems.items()}
        per = {n: r.pop('per_query') for n, r in res.items()}
        u = evaluate_native_dev(task, {q: u400[q] for q in elig}, cutoffs=(400,), include_per_query=True)
        per['U400'] = u.pop('per_query')
        metrics = {n: r['metrics'] for n, r in res.items()}
        metrics['U400'] = {'Recall@400': u['metrics']['Recall@400']}
        paired = {}
        for n in ('BM25', 'RRF'):
            paired[n] = {}
            for m in METRICS:
                d = [per[n][q][m] - per['B0'][q][m] for q in elig]
                paired[n][m] = {'mean_delta': round(sum(d) / len(d), 5), 'wins': sum(x > 1e-12 for x in d),
                                'losses': sum(x < -1e-12 for x in d), 'ties': sum(abs(x) <= 1e-12 for x in d)}
        d = [per['U400'][q]['Recall@400'] - per['B0'][q]['Recall@200'] for q in elig]
        paired['U400_R400_vs_B0_R200'] = {'mean_delta': round(sum(d) / len(d), 5), 'wins': sum(x > 1e-12 for x in d),
                                          'losses': sum(x < -1e-12 for x in d), 'ties': sum(abs(x) <= 1e-12 for x in d)}
        public[part] = {'eligible_queries': len(elig), 'metrics': metrics, 'paired_vs_B0': paired}
        b0x = {q: per['B0'][q]['Recall@200'] > 0 for q in elig}
        public[part]['exposure_strata_vs_B0'] = {
            'BM25@200': exposure_strata({q: per['BM25'][q]['Recall@200'] > 0 for q in elig}, b0x),
            'RRF@200': exposure_strata({q: per['RRF'][q]['Recall@200'] > 0 for q in elig}, b0x),
            'U400@400': exposure_strata({q: per['U400'][q]['Recall@400'] > 0 for q in elig}, b0x)}
        private[part] = per
    for part in S5_B0:
        assert abs(public[part]['metrics']['B0']['Recall@200'] - S5_B0[part]) < 1e-9, 'B0 does not reproduce S5'
    d_out = public['OUT']['metrics']['RRF']['Recall@200'] - public['OUT']['metrics']['B0']['Recall@200']
    d_in = public['IN']['metrics']['RRF']['Recall@200'] - public['IN']['metrics']['B0']['Recall@200']
    verdict = 'GO' if d_out >= 0.010 and d_in >= -0.020 else 'NO_GO'
    OUT_PRIVATE.mkdir(parents=True)
    (OUT_PRIVATE / 'per-query.json').write_text(json.dumps(private) + '\n', encoding='utf-8')
    (OUT_PRIVATE / 'bm25-top200-private.jsonl').write_text(
        ''.join(json.dumps({'query_id': q, 'families': v}) + '\n' for q, v in sorted(bm25.items())), encoding='utf-8')
    result = {'status': 'PAPER2_HEADROOM_DEV_DESCRIPTIVE', 'verdict': verdict,
              'rule': 'GO iff RRF-B0 OUT Recall@200 >= 0.010 and RRF-B0 IN Recall@200 >= -0.020',
              'rrf_minus_b0': {'OUT_Recall@200': round(d_out, 5), 'IN_Recall@200': round(d_in, 5)},
              'predeclaration_sha256': sha(HERE / 'HEADROOM-PREDECLARATION.md'), 'inputs_sha256_verified': True,
              'b0_reproduces_s5': True, 'protected_test_access': False, 'model_calls': 0, 'significance_claim': False,
              'bm25': {'k1': K1, 'b': B, 'depth': DEPTH, 'stopwords': len(STOP), **index_stats},
              'process_cpu_seconds_in_script': round(time.process_time() - t0, 3), 'results': public}
    PUBLIC.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'verdict': verdict, **result['rrf_minus_b0']}))


if __name__ == '__main__':
    main()
