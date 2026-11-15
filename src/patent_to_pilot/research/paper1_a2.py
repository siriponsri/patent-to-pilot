"""Paper 1 amendment A2 (owner approval to prepare 2026-11-15; pre-declaration paper1-a2/A2-PREDECLARATION.md).

Tail fusion T-X(k): B0's top-k kept unchanged; ranks k+1..200 filled from arm X in its own order (families already
placed are skipped); if the arm runs out, B0's remaining families continue. CPU only; pure functions, no I/O.
The candidate family and the dev selection rule below were fixed before any A2 computation.
"""
from ..evaluation.dapfam_native import native_dev_task, evaluate_paper1_dev
from .mtm_runtime import InputBoundaryError
from .paper1_analysis import DEPTH, exposure_strata

K_GRID = (50, 100, 150)
A2_ARMS = ('FA', 'GR', 'SACR', 'shuffle')
IN_HARM_ADMISSIBLE = -0.010   # half the frozen 0.020 harm margin (selection on dev only)
PRIMARY = 'Recall@200'


def tail_fuse(b0, arm, k, depth=DEPTH):
    for ranking in (b0, arm):
        if type(ranking) is not list or len(ranking) != len(set(ranking)):
            raise InputBoundaryError('rankings must be duplicate-free lists')
    if type(k) is not int or not 0 <= k <= depth:
        raise InputBoundaryError('invalid head size')
    out = list(b0[:k]); seen = set(out)
    for source in (arm, b0[k:]):
        for family in source:
            if len(out) == depth:
                return out
            if family not in seen:
                out.append(family); seen.add(family)
    return out


def a2_systems(reference, tables, ks=K_GRID):
    """tables: {'FA'|'GR'|'SACR'|'shuffle': {qid: [families]}} -> {'B0', 'T-X(k)'}."""
    if set(tables) != set(A2_ARMS):
        raise InputBoundaryError('A2 needs FA, GR, SACR and shuffle tables')
    for t in tables.values():
        if set(t) != set(reference):
            raise InputBoundaryError('every table must rank exactly the reference queries')
    systems = {'B0': reference}
    for arm in A2_ARMS:
        for k in ks:
            systems['T-%s(%d)' % (arm, k)] = {q: tail_fuse(reference[q], tables[arm][q], k) for q in reference}
    return systems


def select_k(metrics, ks=K_GRID):
    """metrics: {partition: {system: {metric: value}}}. Pre-declared rule (A2-PREDECLARATION.md)."""
    b0_in = metrics['IN']['B0'][PRIMARY]
    rows = [(k, metrics['IN']['T-FA(%d)' % k][PRIMARY] - b0_in, metrics['OUT']['T-FA(%d)' % k][PRIMARY]) for k in ks]
    admissible = [(k, d, out) for k, d, out in rows if d >= IN_HARM_ADMISSIBLE]
    if not admissible:
        return {'k_star': None, 'status': 'NO_ADMISSIBLE_TAIL_FUSION_ON_DEV', 'rows': rows}
    best = max(round(out, 5) for _, _, out in admissible)
    k_star = max(k for k, _, out in admissible if round(out, 5) == best)
    return {'k_star': k_star, 'status': 'SELECTED', 'rows': rows}


def a2_dev_design(corpus, queries, relations, systems):
    """-> (public aggregates, private per-query). Descriptive dev design; no bootstrap, no significance."""
    public, private, metrics = {}, {}, {}
    for partition in ('ALL', 'IN', 'OUT'):
        task = native_dev_task(corpus, queries, relations, partition=partition)
        eligible = sorted(task['qrels'])
        results = {n: evaluate_paper1_dev(task, {q: t[q] for q in eligible}) for n, t in systems.items()}
        per = {n: r.pop('per_query') for n, r in results.items()}
        metrics[partition] = {n: r['metrics'] for n, r in results.items()}
        paired = {}
        for n in systems:
            if n == 'B0':
                continue
            d = [per[n][q][PRIMARY] - per['B0'][q][PRIMARY] for q in eligible]
            paired[n] = {'mean_delta': sum(d) / len(d), 'wins': sum(x > 1e-12 for x in d),
                         'losses': sum(x < -1e-12 for x in d), 'ties': sum(abs(x) <= 1e-12 for x in d)}
        public[partition] = {'eligible_queries': len(eligible), 'metrics': metrics[partition], 'paired_vs_B0': paired}
        if partition == 'OUT':
            public[partition]['exposure_strata_vs_B0'] = {
                n: exposure_strata({q: per[n][q][PRIMARY] > 0 for q in eligible}, {q: per['B0'][q][PRIMARY] > 0 for q in eligible})
                for n in systems if n != 'B0'}
        private[partition] = per
    public['selection'] = select_k(metrics)
    return public, private
