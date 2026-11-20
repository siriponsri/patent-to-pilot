"""AM-7 / AM-7.1 stage-2a library (pure functions; numpy only). Frozen rules: paper1-bridgeret/am7/AM-7-MISSING-REFERENCE.md
and AM-7.1.md. Every rule below cites the section it implements.
"""
import hashlib
import math
from collections import defaultdict

import numpy as np

ANCHOR_SALT = 'p1-am7-anchor-v1'          # AM-7 §3
SHUFFLE_SALT = 'p1-am7-shuffle-v1'        # AM-7 §4.7
DEV_SAMPLE_SALT = 'p1-am7-dev-sample-v1'  # AM-7 §4.3
RRF_K, DEPTH = 60, 1000
PROTECTED = ('P1-TEST', 'P2-TEST', 'P3-TEST')
SEED, B = 20261119, 10000


def sha(s):
    return hashlib.sha256(s.encode()).hexdigest()


# ------------------------------------------------------------------ cohort (AM-7 §3)
def c103_set(rows, filing_date, app_id, corpus):
    """rows: dicts with unit, basis, dom_ipc3, unit_first_pub. Returns {'IN3': set, 'OUT3': set, 'NOIPC': set}."""
    s = {'IN3': set(), 'OUT3': set(), 'NOIPC': set()}
    for r in rows:
        u = r['unit']
        if r['basis'] not in ('103', 'both') or not u or not r['unit_first_pub'] or u not in corpus:
            continue
        if r['unit_first_pub'] >= filing_date or u == 'A:' + app_id:
            continue
        s.setdefault(r['dom_ipc3'], set()).add(u)
    return s


def anchor_of(app_id, in_units):
    return min(in_units, key=lambda u: sha(f'{ANCHOR_SALT}|{app_id}|{u}'))


def strict_out103(rows, filing_date, app_id):
    """103 OUT3 cited units, RPD-visible with a known date, in or out of the corpus (AM-7 §3 strict MR)."""
    return {r['unit'] for r in rows if r['basis'] in ('103', 'both') and r['unit'] and r['unit_first_pub']
            and r['unit_first_pub'] < filing_date and r['unit'] != 'A:' + app_id and r['dom_ipc3'] == 'OUT3'}


# ------------------------------------------------------------------ ranking helpers
def rank_from_scores(scores, unit_rank, depth=DEPTH):
    """Top-depth indices of a 1-D score array (-inf = excluded); ties by unit id (AM-7 §4: ties broken by unit id)."""
    finite = np.isfinite(scores)
    n = int(finite.sum())
    k = min(depth, n)
    if k == 0:
        return np.empty(0, dtype=np.int64)
    part = np.argpartition(-scores, k - 1)[:k] if k < len(scores) else np.arange(len(scores))
    part = part[np.isfinite(scores[part])]
    # boundary ties: include every index whose score equals the k-th score, then cut after the tie-break
    kth = np.min(scores[part])
    extra = np.nonzero(scores == kth)[0]
    cand = np.union1d(part, extra)
    order = np.lexsort((unit_rank[cand], -scores[cand]))
    return cand[order][:k]


def rrf(lists, k=RRF_K, depth=DEPTH, unit_rank=None):
    """Reciprocal rank fusion of index lists (each already cut to its depth). Ties by unit id rank."""
    sc = defaultdict(float)
    for lst in lists:
        for r, i in enumerate(lst):
            sc[int(i)] += 1.0 / (k + r + 1)
    key = (lambda i: (-sc[i], unit_rank[i])) if unit_rank is not None else (lambda i: (-sc[i], i))
    return np.array(sorted(sc, key=key)[:depth], dtype=np.int64)


def n5_ranking(counts, base_scores, unit_rank, depth=DEPTH):
    """AM-7.1 §3: positive-count units first by count, ties by U0 score (then unit id); then the rest in U0 order.
    counts: {unit_index: count>0}; units excluded by the mask must already be absent; base_scores = U0 scores (-inf
    for excluded)."""
    pos = [i for i, c in counts.items() if c > 0 and np.isfinite(base_scores[i])]
    pos.sort(key=lambda i: (-counts[i], -base_scores[i], unit_rank[i]))
    head = pos[:depth]
    if len(head) >= depth:
        return np.array(head, dtype=np.int64)
    rest = rank_from_scores(base_scores, unit_rank, depth + len(head))
    seen = set(head)
    tail = [int(i) for i in rest if int(i) not in seen][:depth - len(head)]
    return np.array(head + tail, dtype=np.int64)


def mmr(cand, vecs, qsims, lam, depth=DEPTH):
    """AM-7.1 §2 greedy MMR over a candidate list. vecs: (n, d) L2-normalised rows of cand; qsims: cos(q, cand)."""
    n = len(cand)
    sim = vecs @ vecs.T
    chosen, maxsim = [], np.full(n, -np.inf)
    avail = np.ones(n, dtype=bool)
    for _ in range(min(depth, n)):
        red = np.where(np.isfinite(maxsim), maxsim, 0.0)
        val = lam * qsims - (1 - lam) * red
        val[~avail] = -np.inf
        j = int(np.argmax(val))
        chosen.append(j); avail[j] = False
        maxsim = np.maximum(np.where(np.isfinite(maxsim), maxsim, -np.inf), sim[j])
    return cand[np.array(chosen, dtype=np.int64)]


def mmr_batch(cands, vecs, qsims, lam, depth=DEPTH, sim=None):
    """Batched greedy MMR: cands (b, n), vecs (b, n, d), qsims (b, n). Same rule as mmr(); argmax ties -> lowest position
    (positions follow U0 order, so ties go to the better U0 rank)."""
    b, n = cands.shape
    if sim is None:
        sim = np.matmul(vecs, np.swapaxes(vecs, 1, 2))      # batched BLAS (einsum here was ~100x slower)
    maxsim = np.zeros((b, n), dtype=np.float32)
    first = np.ones(b, dtype=bool)
    avail = np.ones((b, n), dtype=bool)
    out = np.empty((b, min(depth, n)), dtype=np.int64)
    rows = np.arange(b)
    for t in range(min(depth, n)):
        val = lam * qsims - (1 - lam) * np.where(first[:, None], 0.0, maxsim)
        val = np.where(avail, val, -np.inf)
        j = np.argmax(val, axis=1)
        out[:, t] = cands[rows, j]
        avail[rows, j] = False
        newsim = sim[rows, j]
        maxsim = np.where(first[:, None], newsim, np.maximum(maxsim, newsim))
        first[:] = False
    return out


# ------------------------------------------------------------------ metrics
def recall_at(ranked, targets, k):
    if not targets:
        return None
    top = set(int(i) for i in ranked[:k])
    return sum(1 for t in targets if t in top) / len(targets)


def mrr_first(ranked, targets):
    for r, i in enumerate(ranked):
        if int(i) in targets:
            return 1.0 / (r + 1)
    return 0.0


# ------------------------------------------------------------------ inference (AM-7 §5: art-unit cluster bootstrap)
def cluster_bootstrap(values, clusters, b=B, seed=SEED):
    """values: per-query numbers (e.g. paired differences); clusters: per-query cluster ids. Returns mean, 2.5/97.5 %."""
    v = np.asarray(values, dtype=np.float64)
    cl = np.asarray(clusters)
    uniq, inv = np.unique(cl, return_inverse=True)
    sums = np.bincount(inv, weights=v, minlength=len(uniq))
    cnts = np.bincount(inv, minlength=len(uniq)).astype(np.float64)
    rng = np.random.default_rng(seed)
    w = rng.multinomial(len(uniq), np.full(len(uniq), 1.0 / len(uniq)), size=b).astype(np.float64)
    means = (w @ sums) / (w @ cnts)
    return float(v.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def design_effect(values, clusters, b=2000, seed=SEED):
    v = np.asarray(values, dtype=np.float64)
    _, lo, hi = cluster_bootstrap(v, clusters, b=b, seed=seed)
    se_cl = (hi - lo) / (2 * 1.959964)
    se_iid = v.std() / math.sqrt(len(v))
    return (se_cl / se_iid) ** 2 if se_iid > 0 else float('nan')


def mde(sd, n, deff=1.0, z_a=2.241403, z_b=0.841621):
    """80 % power, two-sided alpha 0.025 (AM-7 §5 family alpha)."""
    return (z_a + z_b) * sd * math.sqrt(deff) / math.sqrt(n)


# ------------------------------------------------------------------ selection (AM-7.1 §1, §2, §4, §6)
def pick_param(scores, tie=0.001, prefer='small'):
    """scores: {param: value}. Highest value; values within `tie` of the best -> smallest (or largest) param."""
    best = max(scores.values())
    tied = [p for p, v in scores.items() if round(best - v, 9) <= tie]
    key = (lambda p: (p if p != 'inf' else math.inf))
    return (min if prefer == 'small' else max)(tied, key=key)


def pick_first_best(order, scores, tie=0.001):
    """Strongest of an ordered list; ties within `tie` -> the earlier entry."""
    best = max(scores[k] for k in order)
    return next(k for k in order if round(best - scores[k], 9) <= tie)


def select_across(order, per_query, clusters, margin=0.010):
    """AM-7.1 §6 step 2. order: candidate names, simplest first; per_query: {name: np.array of per-query values on the
    same queries}. Returns (A*, log)."""
    inc = order[0]
    log = []
    for cand in order[1:]:
        d = per_query[cand] - per_query[inc]
        m, lo, hi = cluster_bootstrap(d, clusters)
        ok = m >= margin and lo > 0
        log.append({'incumbent': inc, 'challenger': cand, 'delta': round(m, 5), 'ci95': [round(lo, 5), round(hi, 5)],
                    'replaced': bool(ok)})
        if ok:
            inc = cand
    return inc, log


# ------------------------------------------------------------------ N5 co-citation index (AM-7.1 §3)
class CoCitation:
    """actions: list of (mail_int, app_id, group_root, unit_index_tuple). Build once; query per (anchor, q)."""

    def __init__(self, actions):
        self.actions = actions
        self.by_unit = defaultdict(list)
        for k, (_, _, _, units) in enumerate(actions):
            for u in set(units):
                self.by_unit[u].append(k)

    def counts(self, anchor, q_mail, q_app, q_group, protected_apps=frozenset()):
        c = defaultdict(int)
        n_src = 0
        for k in self.by_unit.get(anchor, ()):
            mail, app, grp, units = self.actions[k]
            if mail >= q_mail or app == q_app or (q_group is not None and grp == q_group):
                continue
            if app in protected_apps:
                raise RuntimeError('protected application found among source actions')
            n_src += 1
            for u in set(units):
                if u != anchor:
                    c[u] += 1
        return c, n_src


# ------------------------------------------------------------------ decoy (AM-7.1 §5)
def matched_decoy(u0_top, qsims_top, shared_top, k_units, anchor, anchor_qsim, unit_rank):
    """u0_top: U0 top-1000 indices; qsims_top: their cos(q,.); shared_top: bool per entry; k_units: all K(q) units.
    Ties -> unit id (AM-7.1 §5)."""
    best = None
    for i, s, sh in zip(u0_top, qsims_top, shared_top):
        i = int(i)
        if not sh or i in k_units or i == anchor:
            continue
        key = (abs(float(s) - anchor_qsim), int(unit_rank[i]))
        if best is None or key < best[0]:
            best = (key, i)
    return None if best is None else best[1]


def topk_rows(S, unit_rank, depth=DEPTH, slack=64):
    """Row-wise top-depth with unit-id tie-break for a 2-D score array (-inf = excluded). Uses torch.topk when available
    (exact: falls back to rank_from_scores for a row whose tie spans the slack boundary)."""
    n_rows, n = S.shape
    k = min(depth + slack, n)
    try:
        import torch
        v, idx = torch.topk(torch.from_numpy(S), k, dim=1)
        v, idx = v.numpy(), idx.numpy()
    except ImportError:
        idx = np.argpartition(-S, k - 1, axis=1)[:, :k] if k < n else np.tile(np.arange(n), (n_rows, 1))
        v = np.take_along_axis(S, idx, axis=1)
        o = np.argsort(-v, axis=1, kind='stable')
        idx, v = np.take_along_axis(idx, o, axis=1), np.take_along_axis(v, o, axis=1)
    out = []
    for r in range(n_rows):
        vr, ir = v[r], idx[r]
        fin = np.isfinite(vr)
        if fin.sum() < min(depth, k) and fin.sum() < np.isfinite(S[r]).sum():
            out.append(rank_from_scores(S[r], unit_rank, depth)); continue
        vr, ir = vr[fin], ir[fin]
        if len(vr) > depth and k < n and vr[-1] == vr[min(depth, len(vr)) - 1]:
            out.append(rank_from_scores(S[r], unit_rank, depth)); continue
        order = np.lexsort((unit_rank[ir], -vr))
        out.append(ir[order][:depth])
    return out
