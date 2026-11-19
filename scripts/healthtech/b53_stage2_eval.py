"""B53 Stage 2 evaluation (plans/B53-PREDECLARATION.md, Stage 2 section; CPU, labels read only here).

Reranks the top 100 of each core arm F0–F4 with each scored instruction (raw score desc, ties by first-stage rank) and
computes strict OUT nDCG@100 per OUT-eligible query (unexposed = 0). Then reports:
- B53.3: the 10 contrasts {Patent-aware, Claim-focused} − Generic for each F, on the common-exposed set C (Holm over 10);
- descriptive: Δ_all, Δ on each arm's own exposed subset, the π·Δ_exp identity check, Scrambled / no-rerank / BGE vs Generic,
  and the response rate.
Usage: python3 b53_stage2_eval.py <in_dir> <runs_dir> <scores_dir> <out_json>
"""
import json, math, random, sys
from pathlib import Path

ARMS_F = ('F0', 'F1', 'F2', 'F3', 'F4')
INSTR = ('generic', 'patent_aware', 'claim_focused', 'scrambled')
SEED = 20261119


def read_jsonl(p):
    return [json.loads(l) for l in open(p, encoding='utf-8')]


def load_pools(runs_dir, k=100):
    pools = {}
    for a in ARMS_F:
        for l in open(Path(runs_dir) / f'{a}.tsv', encoding='utf-8'):
            q, r, fam, s = l.rstrip('\n').split('\t')
            if int(r) <= k:
                pools.setdefault(a, {}).setdefault(q, []).append(fam)
    return pools


def load_scores(path):
    sc = {}
    for l in open(path, encoding='utf-8'):
        q, f, s = l.rstrip('\n').split('\t')
        sc[(q, f)] = float(s)
    return sc


def ndcg100(ranked, out):
    if not out:
        return None
    dcg = sum(out[f] / math.log2(i + 2) for i, f in enumerate(ranked[:100]) if f in out)
    ideal = sorted(out.values(), reverse=True)[:100]
    return dcg / sum(g / math.log2(i + 2) for i, g in enumerate(ideal))


def rerank(pool, scores, q):
    return [f for _, _, f in sorted((-scores[(q, f)], i, f) for i, f in enumerate(pool))]


def boot(d, B=10000, seed=SEED):
    rng = random.Random(seed); n = len(d)
    if n == 0:
        return None, None, None
    m = sum(d) / n
    reps = sorted(sum(d[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return m, reps[int(0.025 * B)], reps[int(0.975 * B) - 1]


def boot_p(d, B=10000, seed=SEED):
    """two-sided bootstrap p for mean 0 (shift method)."""
    n = len(d)
    if n == 0:
        return 1.0
    m = sum(d) / n; c = [x - m for x in d]; rng = random.Random(seed + 1)
    ext = sum(1 for _ in range(B) if abs(sum(c[rng.randrange(n)] for _ in range(n)) / n) >= abs(m))
    return (ext + 1) / (B + 1)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i]); adj = [0.0] * len(ps); run = 0.0
    for r, i in enumerate(order):
        run = max(run, (len(ps) - r) * ps[i]); adj[i] = min(1.0, run)
    return adj


def main(in_dir, runs_dir, scores_dir, out_json):
    out_pos = {}
    for r in read_jsonl(Path(in_dir) / 'qrels-pos.jsonl'):
        if r['domain'] == 'OUT':
            out_pos.setdefault(r['query_id'], {})[r['family']] = r['score']
    qs = sorted(out_pos)
    pools = load_pools(runs_dir)
    scores = {i: load_scores(Path(scores_dir) / f'scores-{i}.tsv') for i in INSTR}
    bge = Path(scores_dir) / 'scores-bge.tsv'
    if bge.exists():
        scores['bge'] = load_scores(bge)
    nd = {}   # (F, system) -> {q: ndcg}
    for F in ARMS_F:
        for q in qs:
            pool = pools[F].get(q, [])
            nd.setdefault((F, 'norerank'), {})[q] = ndcg100(pool, out_pos[q])
            for s in scores:
                nd.setdefault((F, s), {})[q] = ndcg100(rerank(pool, scores[s], q), out_pos[q])
    exposed = {F: {q for q in qs if set(pools[F].get(q, [])) & set(out_pos[q])} for F in ARMS_F}
    C = sorted(set.intersection(*exposed.values()))
    res = {'format': 'ptp-b53-stage2-v1', 'n_out': len(qs), 'C': len(C), 'pi100': {F: len(exposed[F]) / len(qs) for F in ARMS_F},
           'mean_ndcg100': {f'{F}|{s}': sum(v.values()) / len(qs) for (F, s), v in nd.items()}}
    prim, ps = {}, []
    for F in ARMS_F:
        for a in ('patent_aware', 'claim_focused'):
            d = [nd[(F, a)][q] - nd[(F, 'generic')][q] for q in C]
            m, lo, hi = boot(d); p = boot_p(d)
            prim[f'{F}|{a}-generic'] = {'delta_C': m, 'ci95': [lo, hi], 'p': p, 'wins': sum(x > 0 for x in d),
                                        'losses': sum(x < 0 for x in d), 'ties': sum(x == 0 for x in d)}
            ps.append(p)
    for k, adj in zip(prim, holm(ps)):
        prim[k]['holm_p'] = adj
    res['B53_3_primary_on_C'] = prim
    desc = {}
    for F in ARMS_F:
        E = sorted(exposed[F]); pi = len(E) / len(qs)
        for a in [s for s in scores if s != 'generic'] + ['norerank']:
            d_all = [nd[(F, a)][q] - nd[(F, 'generic')][q] for q in qs]
            d_exp = [nd[(F, a)][q] - nd[(F, 'generic')][q] for q in E]
            m_all, lo, hi = boot(d_all); m_exp, lo2, hi2 = boot(d_exp)
            desc[f'{F}|{a}-generic'] = {'delta_all': m_all, 'ci95_all': [lo, hi], 'delta_exposed': m_exp, 'ci95_exposed': [lo2, hi2],
                                        'identity_pi_times_delta_exp': pi * m_exp if m_exp is not None else None,
                                        'response_rate_exposed': sum(x != 0 for x in d_exp) / len(E) if E else None}
    res['descriptive'] = desc
    Path(out_json).write_text(json.dumps(res, indent=2))
    print(json.dumps({k: {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk in ('delta_C', 'holm_p')} for k, v in prim.items()}, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])
