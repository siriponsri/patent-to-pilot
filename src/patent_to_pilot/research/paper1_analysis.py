"""Paper 1 frozen analysis (PAPER1-ACQUISITION-PROTOCOL, frozen 13 Nov 2026).

RRF fusion with B0, shared-target component clustering, cluster bootstrap CI, sign-flip randomization,
exposure strata and fixed-sequence gatekeeping. Pure functions on per-query values; no I/O.
"""
import random
from .mtm_runtime import InputBoundaryError

RRF_K = 60
DEPTH = 200
BOOTSTRAP_RESAMPLES = 10_000
RANDOMIZATION_RESAMPLES = 10_000
SEED = 20261113
ALPHA = 0.05
EQUIVALENCE_MARGIN = 0.010      # OUT Recall@200, absolute
NONINFERIORITY_MARGIN = 0.020   # IN / ALL Recall@200 harm check
GATEKEEPING = (('H1', 'F-FA', 'B0'), ('H2', 'F-FA', 'F-GR'), ('H3', 'F-FA', 'F-SACR'))


def rrf_fuse(b0, arm, *, k=RRF_K, depth=DEPTH):
    """Fuse two ranked family lists; ties -> better B0 rank (absent last), then family id."""
    for ranking in (b0, arm):
        if type(ranking) is not list or len(ranking) != len(set(ranking)):
            raise InputBoundaryError('rankings must be duplicate-free lists')
    score = {}
    for ranking in (b0, arm):
        for rank, family in enumerate(ranking[:depth], start=1):
            score[family] = score.get(family, 0.0) + 1.0 / (k + rank)
    b0_rank = {f: r for r, f in enumerate(b0[:depth])}
    order = sorted(score, key=lambda f: (-score[f], b0_rank.get(f, depth), f))
    return order[:depth]


def components(qrels):
    """Connected components of the query-positive-target graph; qrels: {query: iterable of targets}."""
    parent = {}
    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for q, targets in qrels.items():
        find(('q', q))
        for t in targets:
            a, b = find(('q', q)), find(('t', t))
            if a != b: parent[a] = b
    groups = {}
    for q in qrels:
        groups.setdefault(find(('q', q)), []).append(q)
    return sorted((sorted(g) for g in groups.values()), key=lambda g: (-len(g), g[0]))


def _mean(xs):
    return sum(xs) / len(xs)


def cluster_bootstrap_ci(deltas, groups, *, resamples=BOOTSTRAP_RESAMPLES, seed=SEED, alpha=ALPHA):
    """Percentile CI of the macro mean of per-query deltas, resampling whole components."""
    if set(deltas) != {q for g in groups for q in g}:
        raise InputBoundaryError('components must cover exactly the evaluated queries')
    rng = random.Random(seed); sums = [(sum(deltas[q] for q in g), len(g)) for g in groups]
    stats = []
    for _ in range(resamples):
        s = n = 0
        for _ in groups:
            a, b = sums[rng.randrange(len(sums))]; s += a; n += b
        stats.append(s / n)
    stats.sort()
    lo = stats[int((alpha / 2) * resamples)]; hi = stats[int((1 - alpha / 2) * resamples) - 1]
    return {'mean': _mean(list(deltas.values())), 'ci_low': lo, 'ci_high': hi, 'resamples': resamples, 'seed': seed,
            'components': len(groups), 'largest_component_share': max(len(g) for g in groups) / len(deltas)}


def query_bootstrap_ci(deltas, **kw):
    return cluster_bootstrap_ci(deltas, [[q] for q in sorted(deltas)], **kw)


def sign_flip_p(deltas, *, resamples=RANDOMIZATION_RESAMPLES, seed=SEED):
    values = list(deltas.values()); observed = abs(_mean(values)); rng = random.Random(seed)
    hits = sum(abs(_mean([v if rng.random() < 0.5 else -v for v in values])) >= observed - 1e-15 for _ in range(resamples))
    return (hits + 1) / (resamples + 1)


def exposure_strata(a_exposed, b_exposed):
    """a/b_exposed: {query: bool} known positive in top-200. a = arm, b = reference."""
    if set(a_exposed) != set(b_exposed):
        raise InputBoundaryError('same queries required')
    out = {'both': 0, 'arm_only': 0, 'reference_only': 0, 'neither': 0}
    for q in a_exposed:
        a, b = a_exposed[q], b_exposed[q]
        out['both' if a and b else 'arm_only' if a else 'reference_only' if b else 'neither'] += 1
    return out


def interpret(ci, margin=EQUIVALENCE_MARGIN):
    if ci['ci_low'] > 0: return 'SUPERIOR'
    if ci['ci_high'] < 0: return 'INFERIOR'
    if -margin < ci['ci_low'] and ci['ci_high'] < margin: return 'PRACTICALLY_EQUIVALENT'
    return 'INCONCLUSIVE'


def noninferior(ci, margin=NONINFERIORITY_MARGIN):
    return ci['ci_low'] > -margin


def gatekeep(results):
    """results: {step: ci}; fixed sequence, each step tested only if the previous concluded SUPERIOR."""
    out, open_gate = {}, True
    for step, _, _ in GATEKEEPING:
        if not open_gate:
            out[step] = 'NOT_TESTED_GATE_CLOSED'; continue
        out[step] = interpret(results[step])
        open_gate = out[step] == 'SUPERIOR'
    return out
