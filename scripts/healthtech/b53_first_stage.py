"""B53 Stage 1: first-stage substitution on DAPFAM (plans/B53-PREDECLARATION.md, frozen 274af5de).

Subcommands (exploratory, evaluation-only; DAPFAM stays on this PC / dr-train):
  build <parquet_dir> <out_dir>                 (local, needs pyarrow) TAC texts for corpus + all queries, positive qrels
  bm25  <in_dir> <runs_dir>                     F1: BM25 k1 1.5, b 0.75, [a-z0-9]+, top 1000
  dense <in_dir> <runs_dir> <arm> <model_dir> <kind> [mem_frac]
        kind: st-mixed | st-out (sentence-transformers PatEmbed prompts), arctic, qwen3
  rrf   <runs_dir> <arm> <armA> <armB>           RRF k 60 over depth 1000
  eval  <in_dir> <runs_dir> <out_json>           endpoints of section 3 and B53.1 contrasts of section 4
Runs: <runs_dir>/<arm>.tsv with lines query_id \\t rank \\t family \\t score (rank 1..1000).
"""
import json, math, os, random, re, sys, time
from pathlib import Path

TOPK = 1000
RRF_K = 60
SEED = 20261119
PROMPTS = {
    'st-mixed': ('encode query for mixed document retrieval: ', 'encode document for mixed retrieval: '),
    'st-out': ('encode query for different document retrieval: ', 'encode document for different retrieval: '),
    'arctic': ('query: ', ''),
    'qwen3': ('Instruct: Given a patent, retrieve prior art patents\nQuery: ', ''),
}
TOKEN = re.compile(r'[a-z0-9]+')
LOCK = '/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/models/.GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089.lock'


def tac(title, abstract, claims):
    return '\n'.join(v for v in (title or '', abstract or '', claims or '') if v)


def read_jsonl(p):
    with open(p, encoding='utf-8') as f:
        return [json.loads(l) for l in f]


def write_run(path, ranked):
    """ranked: {query_id: [(family, score), ...]} already ordered."""
    tmp = str(path) + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as g:
        for q in sorted(ranked):
            for i, (fam, s) in enumerate(ranked[q][:TOPK]):
                g.write(f'{q}\t{i + 1}\t{fam}\t{s:.6f}\n')
    os.replace(tmp, path)


def read_run(path):
    run = {}
    with open(path, encoding='utf-8') as f:
        for l in f:
            q, r, fam, s = l.rstrip('\n').split('\t')
            run.setdefault(q, []).append(fam)
    return run


def top_sorted(scores, ids):
    """Top-1000 by score desc, ties by family id asc."""
    import numpy as np
    k = min(TOPK, len(ids))
    part = np.argpartition(-scores, k - 1)[:k]
    order = sorted(part, key=lambda j: (-float(scores[j]), ids[j]))
    return [(ids[j], float(scores[j])) for j in order]


# ---------------------------------------------------------------- build (local)
def cmd_build(parquet_dir, out_dir):
    import hashlib, pyarrow.parquet as pq
    pd_, out = Path(parquet_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=False)
    src = {f: hashlib.sha256((pd_ / f).read_bytes()).hexdigest() for f in ('corpus.parquet', 'queries.parquet', 'qrels_all.parquet')}
    corpus = pq.read_table(pd_ / 'corpus.parquet', columns=['relevant_id', 'title_en', 'abstract_en', 'claims_text']).to_pylist()
    queries = pq.read_table(pd_ / 'queries.parquet', columns=['query_id', 'title_en', 'abstract_en', 'claims_text']).to_pylist()
    rel = pq.read_table(pd_ / 'qrels_all.parquet').to_pylist()
    cids = {str(r['relevant_id']) for r in corpus}
    qids = {str(r['query_id']) for r in queries}
    assert len(cids) == len(corpus) == 45336 and len(qids) == len(queries) == 1247
    with open(out / 'corpus.jsonl', 'w', encoding='utf-8') as g:
        for r in sorted(corpus, key=lambda r: str(r['relevant_id'])):
            g.write(json.dumps({'id': str(r['relevant_id']), 'text': tac(r['title_en'], r['abstract_en'], r['claims_text'])}, ensure_ascii=False) + '\n')
    with open(out / 'queries.jsonl', 'w', encoding='utf-8') as g:
        for r in sorted(queries, key=lambda r: str(r['query_id'])):
            g.write(json.dumps({'id': str(r['query_id']), 'text': tac(r['title_en'], r['abstract_en'], r['claims_text'])}, ensure_ascii=False) + '\n')
    pos = []
    for r in rel:
        q, fam = str(r['query_id']), str(r['relevant_id'])
        assert q in qids and fam in cids
        s = float(r['relevance_score'])
        if s > 0:
            assert r['domain_rel'] in ('IN', 'OUT')
            pos.append({'query_id': q, 'family': fam, 'score': s, 'domain': r['domain_rel']})
    pos.sort(key=lambda r: (r['query_id'], r['family']))
    with open(out / 'qrels-pos.jsonl', 'w', encoding='utf-8') as g:
        for r in pos:
            g.write(json.dumps(r) + '\n')
    elig = {d: len({r['query_id'] for r in pos if d == 'ALL' or r['domain'] == d}) for d in ('ALL', 'IN', 'OUT')}
    files = {f: hashlib.sha256((out / f).read_bytes()).hexdigest() for f in ('corpus.jsonl', 'queries.jsonl', 'qrels-pos.jsonl')}
    man = {'format': 'ptp-b53-inputs-v1', 'source_sha256': src, 'files': files, 'corpus': len(corpus), 'queries': len(queries),
           'positive_pairs': len(pos), 'positive_pairs_by_domain': {d: sum(r['domain'] == d for r in pos) for d in ('IN', 'OUT')},
           'eligible_queries': elig, 'view': 'TAC (title\\nabstract\\nclaims), queries and corpus'}
    (out / 'manifest.json').write_text(json.dumps(man, indent=2))
    print(json.dumps({k: man[k] for k in ('corpus', 'queries', 'positive_pairs', 'positive_pairs_by_domain', 'eligible_queries')}))


# ---------------------------------------------------------------- BM25
def cmd_bm25(in_dir, runs_dir):
    import numpy as np
    from scipy.sparse import csr_matrix
    t0 = time.time()
    docs = read_jsonl(Path(in_dir) / 'corpus.jsonl')
    qs = read_jsonl(Path(in_dir) / 'queries.jsonl')
    ids = [d['id'] for d in docs]
    vocab, rows, cols, vals, dl = {}, [], [], [], []
    for i, d in enumerate(docs):
        tf = {}
        for t in TOKEN.findall(d['text'].lower()):
            tf[t] = tf.get(t, 0) + 1
        dl.append(sum(tf.values()))
        for t, c in tf.items():
            rows.append(i); cols.append(vocab.setdefault(t, len(vocab))); vals.append(c)
    N, dl = len(docs), np.array(dl, dtype=np.float64)
    tfm = csr_matrix((np.array(vals, dtype=np.float64), (rows, cols)), shape=(N, len(vocab)))
    df = np.bincount(tfm.indices, minlength=len(vocab))
    idf = np.log(1 + (N - df + 0.5) / (df + 0.5))
    k1, b = 1.5, 0.75
    norm = k1 * (1 - b + b * dl / dl.mean())
    tfm = tfm.tocoo()
    w = tfm.data * (k1 + 1) / (tfm.data + norm[tfm.row]) * idf[tfm.col]
    W = csr_matrix((w, (tfm.row, tfm.col)), shape=tfm.shape).tocsc()
    ranked = {}
    for q in qs:
        cnt = {}
        for t in TOKEN.findall(q['text'].lower()):
            if t in vocab:
                cnt[vocab[t]] = cnt.get(vocab[t], 0) + 1
        s = np.zeros(N)
        for t, c in cnt.items():
            s += c * W[:, t].toarray().ravel()
        pos = np.nonzero(s > 0)[0]
        ranked[q['id']] = sorted(((ids[j], float(s[j])) for j in pos), key=lambda x: (-x[1], x[0]))[:TOPK]
    Path(runs_dir).mkdir(parents=True, exist_ok=True)
    write_run(Path(runs_dir) / 'F1.tsv', ranked)
    print('bm25 done', len(ranked), round(time.time() - t0, 1))


# ---------------------------------------------------------------- dense
def cmd_dense(in_dir, runs_dir, arm, model_dir, kind, frac='0.15'):
    import fcntl, numpy as np, torch, torch.nn.functional as F
    t0 = time.time()
    docs = read_jsonl(Path(in_dir) / 'corpus.jsonl'); qs = read_jsonl(Path(in_dir) / 'queries.jsonl')
    ids = [d['id'] for d in docs]
    qp, dp = PROMPTS[kind]
    lockf = open(LOCK, 'a'); fcntl.flock(lockf, fcntl.LOCK_EX)
    torch.cuda.set_per_process_memory_fraction(float(frac), 0)
    bs = int(os.environ.get('BS', '16'))
    trunc = {'q': 0, 'd': 0}
    if kind.startswith('st'):
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer(model_dir, device='cuda'); m.half(); m.max_seq_length = 512
        tok = m.tokenizer

        def enc(texts, side):
            n = tok(texts, truncation=False)['input_ids']; trunc[side] += sum(len(x) > 512 for x in n)
            return m.encode(texts, batch_size=bs, normalize_embeddings=True, convert_to_numpy=True).astype(np.float32)
    else:
        from transformers import AutoModel, AutoTokenizer
        last = kind == 'qwen3'
        tok = AutoTokenizer.from_pretrained(model_dir, padding_side='left' if last else 'right')
        kw = dict(trust_remote_code=True, torch_dtype=torch.float16)
        if not last:
            kw.update(use_memory_efficient_attention=False, unpad_inputs=False)
        model = AutoModel.from_pretrained(model_dir, **kw).cuda().eval()

        def enc(texts, side):
            out = []
            for s in range(0, len(texts), bs):
                chunk = texts[s:s + bs]
                trunc[side] += sum(len(x) > 512 for x in tok(chunk, truncation=False)['input_ids'])
                bt = tok(chunk, padding=True, truncation=True, max_length=512, return_tensors='pt').to('cuda')
                with torch.inference_mode():
                    h = model(**bt).last_hidden_state
                    v = h[:, -1] if last else h[:, 0]
                    out.append(F.normalize(v.float(), dim=-1).cpu().numpy())
            return np.concatenate(out)
    order = sorted(range(len(docs)), key=lambda i: len(docs[i]['text']))
    parts = []
    for s in range(0, len(order), 2048):
        idx = order[s:s + 2048]
        parts.append((idx, enc([dp + docs[i]['text'] for i in idx], 'd')))
        print(arm, 'docs', s + len(idx), round(time.time() - t0, 1), flush=True)
    dim = parts[0][1].shape[1]; D = np.zeros((len(docs), dim), dtype=np.float32)
    for idx, v in parts:
        D[idx] = v
    Q = enc([qp + q['text'] for q in qs], 'q')
    fcntl.flock(lockf, fcntl.LOCK_UN)
    S = Q @ D.T
    ranked = {q['id']: top_sorted(S[i], ids) for i, q in enumerate(qs)}
    Path(runs_dir).mkdir(parents=True, exist_ok=True)
    write_run(Path(runs_dir) / f'{arm}.tsv', ranked)
    meta = {'arm': arm, 'kind': kind, 'model_dir': model_dir, 'query_prompt': qp, 'doc_prompt': dp,
            'truncated_queries': trunc['q'], 'truncated_docs': trunc['d'], 'seconds': round(time.time() - t0, 1)}
    (Path(runs_dir) / f'{arm}.meta.json').write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta))


# ---------------------------------------------------------------- RRF
def cmd_rrf(runs_dir, arm, a, b):
    ra, rb = read_run(Path(runs_dir) / f'{a}.tsv'), read_run(Path(runs_dir) / f'{b}.tsv')
    ranked = {}
    for q in set(ra) | set(rb):
        s = {}
        for run in (ra.get(q, []), rb.get(q, [])):
            for i, fam in enumerate(run[:TOPK]):
                s[fam] = s.get(fam, 0.0) + 1.0 / (RRF_K + i + 1)
        ranked[q] = sorted(s.items(), key=lambda x: (-x[1], x[0]))[:TOPK]
    write_run(Path(runs_dir) / f'{arm}.tsv', ranked)
    print('rrf', arm, len(ranked))


# ---------------------------------------------------------------- evaluation
def per_query(run, pos, qids_order):
    """pos: {q: {'OUT': {fam: score}, 'IN': {...}}}. Returns per-query dict for OUT-eligible etc."""
    res = {}
    for q in qids_order:
        r = run.get(q, [])
        rank = {f: i + 1 for i, f in enumerate(r)}
        out = pos.get(q, {}).get('OUT', {}); inn = pos.get(q, {}).get('IN', {})
        allp = {**inn, **out}
        hits = sorted(rank[f] for f in out if f in rank)
        r1 = hits[0] if hits else None
        def rec(P, k):
            return sum(1 for f in P if rank.get(f, 10**9) <= k) / len(P) if P else None
        def ndcg(P, k):
            if not P:
                return None
            dcg = sum(P[f] / math.log2(rank[f] + 1) for f in P if rank.get(f, 10**9) <= k)
            ideal = sorted(P.values(), reverse=True)[:k]
            return dcg / sum(g / math.log2(i + 2) for i, g in enumerate(ideal))
        oracle = None
        if out:
            inpool = sum(1 for f in out if rank.get(f, 10**9) <= 200)   # ideal reorder of the top-200 pool into the top 100
            oracle = min(inpool, 100) / len(out)
        res[q] = {'r1': r1, 'x100': int(r1 is not None and r1 <= 100), 'x200': int(r1 is not None and r1 <= 200),
                  'x1000': int(r1 is not None), 'out_r100': rec(out, 100), 'out_r200': rec(out, 200),
                  'in_r100': rec(inn, 100), 'in_r200': rec(inn, 200), 'all_r100': rec(allp, 100), 'all_r200': rec(allp, 200),
                  'out_ndcg100': ndcg(out, 100), 'oracle_out_r100': oracle, 'self_top1': int(bool(r) and r[0] == q)}
    return res


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def boot_diff(a, b, B=10000, seed=SEED):
    rng = random.Random(seed); n = len(a)
    d = [x - y for x, y in zip(a, b)]
    m = sum(d) / n
    reps = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return m, reps[int(0.025 * B)], reps[int(0.975 * B) - 1]


def mcnemar(a, b):
    g = sum(1 for x, y in zip(a, b) if x == 1 and y == 0); l = sum(1 for x, y in zip(a, b) if x == 0 and y == 1)
    n = g + l
    if n == 0:
        return g, l, 1.0
    k = min(g, l)
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return g, l, min(1.0, 2 * p)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0.0] * len(ps); run = 0.0
    for r, i in enumerate(order):
        run = max(run, (len(ps) - r) * ps[i]); adj[i] = min(1.0, run)
    return adj


def cmd_eval(in_dir, runs_dir, out_json):
    pos = {}
    for r in read_jsonl(Path(in_dir) / 'qrels-pos.jsonl'):
        pos.setdefault(r['query_id'], {}).setdefault(r['domain'], {})[r['family']] = r['score']
    qids = sorted(q['id'] for q in read_jsonl(Path(in_dir) / 'queries.jsonl'))
    out_q = [q for q in qids if pos.get(q, {}).get('OUT')]
    in_q = [q for q in qids if pos.get(q, {}).get('IN')]
    all_q = [q for q in qids if pos.get(q)]
    arms = sorted(p.stem for p in Path(runs_dir).glob('*.tsv'))
    pq_ = {a: per_query(read_run(Path(runs_dir) / f'{a}.tsv'), pos, qids) for a in arms}
    summ = {}
    for a in arms:
        P = pq_[a]
        exp_r1 = sorted(P[q]['r1'] for q in out_q if P[q]['r1'] is not None and P[q]['r1'] <= 100)
        summ[a] = {
            'pi100': mean([P[q]['x100'] for q in out_q]), 'pi200': mean([P[q]['x200'] for q in out_q]),
            'pi1000': mean([P[q]['x1000'] for q in out_q]),
            'median_r1_exposed100': exp_r1[len(exp_r1) // 2] if exp_r1 else None,
            'share_r1_le10_exposed100': (sum(r <= 10 for r in exp_r1) / len(exp_r1)) if exp_r1 else None,
            'out_recall100': mean([P[q]['out_r100'] for q in out_q]), 'out_recall200': mean([P[q]['out_r200'] for q in out_q]),
            'out_ndcg100': mean([P[q]['out_ndcg100'] for q in out_q]),
            'in_recall100': mean([P[q]['in_r100'] for q in in_q]), 'in_recall200': mean([P[q]['in_r200'] for q in in_q]),
            'all_recall100': mean([P[q]['all_r100'] for q in all_q]), 'all_recall200': mean([P[q]['all_r200'] for q in all_q]),
            'oracle_out_recall100': mean([P[q]['oracle_out_r100'] for q in out_q]),
            'self_top1_queries': sum(P[q]['self_top1'] for q in qids)}
        if (Path(runs_dir) / f'{a}.meta.json').exists():
            summ[a]['meta'] = json.loads((Path(runs_dir) / f'{a}.meta.json').read_text())
    core = [a for a in ('F1', 'F2', 'F3', 'F4') if a in pq_]
    contrasts = {}
    if 'F0' in pq_:
        ps = []
        for a in core + [a for a in arms if a not in core + ['F0']]:
            xa = [pq_[a][q]['x100'] for q in out_q]; x0 = [pq_['F0'][q]['x100'] for q in out_q]
            m, lo, hi = boot_diff(xa, x0)
            g, l, p = mcnemar(xa, x0)
            contrasts[a] = {'delta_pi100_vs_F0': m, 'ci95': [lo, hi], 'gained': g, 'lost': l, 'mcnemar_p': p,
                            'family': 'B53.1 core (Holm)' if a in core else 'descriptive'}
            if a in core:
                ps.append((a, p))
        for (a, _), adj in zip(ps, holm([p for _, p in ps])):
            contrasts[a]['holm_p'] = adj
    common = [q for q in out_q if all(pq_[a][q]['x100'] for a in ['F0'] + core if a in pq_)]
    res = {'format': 'ptp-b53-stage1-v1', 'predeclaration': 'plans/B53-PREDECLARATION.md (274af5de)',
           'cohorts': {'OUT': len(out_q), 'IN': len(in_q), 'ALL': len(all_q), 'queries': len(qids)},
           'arms': summ, 'b53_1_contrasts': contrasts, 'common_exposed_k100_core': len(common),
           'bootstrap': {'B': 10000, 'seed': SEED}}
    Path(out_json).write_text(json.dumps(res, indent=2))
    pq_out = Path(out_json).with_suffix('.perquery.jsonl')
    with open(pq_out, 'w') as g:
        for q in qids:
            g.write(json.dumps({'q': q, **{a: pq_[a][q] for a in arms}}) + '\n')
    print(json.dumps({a: {k: summ[a][k] for k in ('pi100', 'pi200', 'out_recall100', 'out_ndcg100')} for a in arms}, indent=1))


if __name__ == '__main__':
    c, a = sys.argv[1], sys.argv[2:]
    {'build': cmd_build, 'bm25': cmd_bm25, 'dense': cmd_dense, 'rrf': cmd_rrf, 'eval': cmd_eval}[c](*a)
