"""Paper 1 S5 dev evaluation (frozen protocol 2026-11-13 sections 5-6 + amendment A1). Pure functions, no I/O.

Systems: B0 (pinned reference), standalone FA/GR/SACR panels, fused F-FA/F-GR/F-SACR (RRF k=60 depth 200 with B0)
and the A1 C2 control F-shuffle. Metrics come from the pinned native evaluator unchanged.

Dev is DESCRIPTIVE (protocol section 6): bootstrap intervals and paired SDs are reported for engineering readiness,
the owner checkpoint and the power statement only. No gatekeeping verdicts or significance labels are produced here.
C1: an arm flagged ENGINEERING_FAULT by the retrieval job is refused before any of its systems are evaluated.
C3: every endpoint again on the queries outside the family-overlap set.
"""
import math
from ..evaluation.dapfam_native import native_dev_task, evaluate_paper1_dev
from .mtm_runtime import InputBoundaryError
from .paper1_analysis import rrf_fuse, components, cluster_bootstrap_ci, query_bootstrap_ci, sign_flip_p, exposure_strata, DEPTH
from .paper1_controls import family_overlap

PARTITIONS = ('ALL', 'IN', 'OUT')
ARMS = ('FA', 'GR', 'SACR')
PRIMARY = 'Recall@200'
# (label, system, reference); comparisons are paired on identical eligible queries.
COMPARISONS = (('H1', 'F-FA', 'B0'), ('H2', 'F-FA', 'F-GR'), ('H3', 'F-FA', 'F-SACR'), ('C2', 'F-FA', 'F-shuffle'),
               ('FA_standalone', 'FA', 'B0'), ('GR_standalone', 'GR', 'B0'), ('SACR_standalone', 'SACR', 'B0'),
               ('F-GR_vs_B0', 'F-GR', 'B0'), ('F-SACR_vs_B0', 'F-SACR', 'B0'), ('F-shuffle_vs_B0', 'F-shuffle', 'B0'))
RANK_BINS = ((1, 10), (11, 50), (51, 100), (101, 200))
PLANNING_N = 556          # protocol section 6 power statement
Z_TWO_SIDED_05, Z_POWER_80 = 1.959964, 0.841621
EPS = 1e-12


def build_systems(reference, shuffle, panels, c1):
    """reference/shuffle/panels[arm]: {qid: [families]}; c1: {arm: verdict}. Returns {system: rankings}."""
    if set(panels) != set(ARMS):
        raise InputBoundaryError('FA, GR and SACR panels required')
    for arm in ARMS:
        if c1.get(arm) != 'MOVEMENT_PRESENT':
            raise InputBoundaryError('C1 did not pass for ' + arm + ': stop before evaluating it')
    ids = set(reference)
    for table in [shuffle, *panels.values()]:
        if set(table) != ids:
            raise InputBoundaryError('every system must rank exactly the reference queries')
    systems = {'B0': reference, **panels}
    for name, table in [('shuffle', shuffle), *panels.items()]:
        systems['F-' + name] = {q: rrf_fuse(reference[q], table[q]) for q in reference}
    return systems


def first_positive_bin(ranking, gold):
    for rank, family in enumerate(ranking[:DEPTH], start=1):
        if family in gold:
            return next('%d-%d' % b for b in RANK_BINS if b[0] <= rank <= b[1])
    return 'none'


def _paired(per, system, reference, queries, groups):
    deltas = {q: per[system][q][PRIMARY] - per[reference][q][PRIMARY] for q in queries}
    values = list(deltas.values()); n = len(values); mean = sum(values) / n
    sd = math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1)) if n > 1 else 0.0
    out = {'queries': n, 'mean_delta': mean, 'paired_sd': sd,
           'wins': sum(v > EPS for v in values), 'losses': sum(v < -EPS for v in values), 'ties': sum(abs(v) <= EPS for v in values),
           'cluster_bootstrap_descriptive': cluster_bootstrap_ci(deltas, [[q for q in g if q in deltas] for g in groups if any(q in deltas for q in g)]),
           'mde_80_power_planning_n': PLANNING_N, 'mde_80_power': (Z_TWO_SIDED_05 + Z_POWER_80) * sd / math.sqrt(PLANNING_N)}
    if out['cluster_bootstrap_descriptive']['largest_component_share'] > 0.5:
        out['query_bootstrap_sensitivity'] = query_bootstrap_ci(deltas)
        out['sign_flip_p_sensitivity'] = sign_flip_p(deltas)
    return out


def evaluate_partition(corpus, queries, relations, systems, partition, exclude=frozenset()):
    task = native_dev_task(corpus, queries, relations, partition=partition)
    task['qrels'] = {q: g for q, g in task['qrels'].items() if q not in exclude}
    eligible = sorted(task['qrels'])
    if not eligible:
        return {'eligible_queries': 0}, {}
    results = {name: evaluate_paper1_dev(task, {q: table[q] for q in eligible}) for name, table in systems.items()}
    per = {name: r.pop('per_query') for name, r in results.items()}
    groups = components({q: list(task['qrels'][q]) for q in eligible})
    judged = {}
    for r in relations:
        judged.setdefault(r['query_id'], set()).add(r['relevant_id'])
    public = {'eligible_queries': len(eligible), 'components': len(groups),
              'largest_component_share': max(len(g) for g in groups) / len(eligible),
              'metrics': {name: r['metrics'] for name, r in results.items()},
              'paired_primary': {label: dict(_paired(per, s, ref, eligible, groups), system=s, reference=ref)
                                 for label, s, ref in COMPARISONS},
              'exposure_at_200': {name: sum(per[name][q][PRIMARY] > 0 for q in eligible) for name in systems},
              'exposure_strata_vs_B0': {name: exposure_strata({q: per[name][q][PRIMARY] > 0 for q in eligible},
                                                              {q: per['B0'][q][PRIMARY] > 0 for q in eligible})
                                        for name in systems if name != 'B0'},
              'first_positive_rank_bins': {name: _count(first_positive_bin(systems[name][q], task['qrels'][q]) for q in eligible)
                                           for name in systems},
              'unjudged_share_top10': {name: _unjudged(systems[name], judged, eligible) for name in systems}}
    return public, per


def _count(values):
    out = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return out


def _unjudged(table, judged, eligible):
    top = [(q, f) for q in eligible for f in table[q][:10]]
    return sum(f not in judged.get(q, ()) for q, f in top) / len(top) if top else None


def evaluate_dev(corpus, queries, relations, systems):
    """-> (public, private). public has aggregates only; private holds per-query values keyed by dev query IDs."""
    public, private = {'main': {}, 'c3_family_overlap_sensitivity': {}}, {'main': {}, 'c3': {}}
    positives = {}
    for r in relations:
        if float(r['relevance_score']) > 0:
            positives.setdefault(r['query_id'], set()).add(r['relevant_id'])
    overlap = family_overlap([q['query_id'] for q in queries], [c['relevant_id'] for c in corpus], positives)
    excluded = frozenset(overlap['excluded_for_sensitivity'])
    for partition in PARTITIONS:
        public['main'][partition], private['main'][partition] = evaluate_partition(corpus, queries, relations, systems, partition)
        public['c3_family_overlap_sensitivity'][partition], private['c3'][partition] = evaluate_partition(
            corpus, queries, relations, systems, partition, excluded)
    public['c3_audit'] = {k: v for k, v in overlap.items() if k != 'excluded_for_sensitivity'}
    public['c3_audit']['excluded_queries'] = len(excluded)
    return public, private
