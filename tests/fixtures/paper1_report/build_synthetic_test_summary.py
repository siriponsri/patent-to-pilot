"""Build tests/fixtures/paper1_report/synthetic-test-summary.json: a FAKE Paper 1 test summary for renderer tests.

Every number here is invented (round, patterned values). None comes from DAPFAM, the test split or any run.
The shape follows scripts/healthtech/run_paper1_dev_eval.py (kind paper1-test-eval) and
paper1_dev_eval.evaluate_dev / confirmatory. Designed outcome: H1 SUPERIOR, H2 INCONCLUSIVE, H3 gate closed;
harm check IN non-inferior, ALL not shown.
"""
import json
from pathlib import Path

SYSTEMS = ('B0', 'FA', 'GR', 'SACR', 'F-FA', 'F-GR', 'F-SACR', 'F-shuffle')
COMPARISONS = (('H1', 'F-FA', 'B0'), ('H2', 'F-FA', 'F-GR'), ('H3', 'F-FA', 'F-SACR'), ('C2', 'F-FA', 'F-shuffle'),
               ('FA_standalone', 'FA', 'B0'), ('GR_standalone', 'GR', 'B0'), ('SACR_standalone', 'SACR', 'B0'),
               ('F-GR_vs_B0', 'F-GR', 'B0'), ('F-SACR_vs_B0', 'F-SACR', 'B0'), ('F-shuffle_vs_B0', 'F-shuffle', 'B0'))
N = {'OUT': 556, 'IN': 700, 'ALL': 773}
BASE = {'OUT': 0.1000, 'IN': 0.5000, 'ALL': 0.3000}
OFFSET = {'B0': 0.0, 'FA': -0.0100, 'GR': 0.0100, 'SACR': 0.0050, 'F-FA': 0.0300, 'F-GR': 0.0200, 'F-SACR': 0.0100,
          'F-shuffle': 0.0000}
# designed fake CIs: (mean, low, high) per partition and label
CI = {
    'OUT': {'H1': (0.0300, 0.0100, 0.0500), 'H2': (0.0100, -0.0050, 0.0250), 'H3': (0.0200, -0.0010, 0.0410)},
    'IN': {'H1': (-0.0100, -0.0150, -0.0050)},
    'ALL': {'H1': (-0.0200, -0.0300, -0.0100)},
}


def ci(mean, low, high, n):
    return {'mean': mean, 'ci_low': low, 'ci_high': high, 'resamples': 10000, 'seed': 20261113,
            'components': n // 4, 'largest_component_share': 0.25}


def partition(p):
    n = N[p]
    metrics = {s: {'Recall@10': 0.0111, 'Recall@100': 0.0777, 'Recall@200': round(BASE[p] + OFFSET[s], 4),
                   'NDCG@10': 0.0222, 'NDCG@100': 0.0444, 'NDCG@200': 0.0555} for s in SYSTEMS}
    paired = {}
    for label, s, r in COMPARISONS:
        mean, low, high = CI[p].get(label, (OFFSET[s] - OFFSET[r], OFFSET[s] - OFFSET[r] - 0.0200,
                                             OFFSET[s] - OFFSET[r] + 0.0200))
        paired[label] = {'queries': n, 'mean_delta': mean, 'paired_sd': 0.1000, 'wins': 100, 'losses': 50,
                         'ties': n - 150, 'cluster_bootstrap_descriptive': ci(mean, low, high, n),
                         'mde_80_power_planning_n': 556, 'mde_80_power': 0.0119, 'system': s, 'reference': r}
    exposure = {s: n // 2 for s in SYSTEMS}
    return {'eligible_queries': n, 'components': n // 4, 'largest_component_share': 0.25, 'metrics': metrics,
            'paired_primary': paired, 'exposure_at_200': exposure,
            'exposure_strata_vs_B0': {s: {'both': n // 2 - 10, 'arm_only': 10, 'reference_only': 10,
                                          'neither': n - n // 2 - 10} for s in SYSTEMS if s != 'B0'},
            'first_positive_rank_bins': {s: {'1-10': 10, '11-50': 20, '51-100': 30, '101-200': 40, 'none': n - 100}
                                         for s in SYSTEMS},
            'unjudged_share_top10': {s: 0.5 for s in SYSTEMS}}


def build():
    main = {p: partition(p) for p in ('ALL', 'IN', 'OUT')}
    c3 = {p: partition(p) for p in ('ALL', 'IN', 'OUT')}
    for p in c3:
        c3[p]['eligible_queries'] -= 11
    cis = {s: main['OUT']['paired_primary'][s]['cluster_bootstrap_descriptive'] for s in ('H1', 'H2', 'H3')}
    confirmatory = {
        'gatekeeping': {'H1': 'SUPERIOR', 'H2': 'INCONCLUSIVE', 'H3': 'NOT_TESTED_GATE_CLOSED'},
        'per_step_interpretation_if_tested': {'H1': 'SUPERIOR', 'H2': 'INCONCLUSIVE', 'H3': 'INCONCLUSIVE'},
        'cis': cis, 'equivalence_margin': 0.01, 'harm_noninferiority_margin': 0.02,
        'harm_check_F-FA_vs_B0': {
            'IN': {'ci': main['IN']['paired_primary']['H1']['cluster_bootstrap_descriptive'], 'noninferior': True},
            'ALL': {'ci': main['ALL']['paired_primary']['H1']['cluster_bootstrap_descriptive'], 'noninferior': False}},
        'c2_descriptive': main['OUT']['paired_primary']['C2']['cluster_bootstrap_descriptive']}
    c1 = {arm: {'used_queries': 770, 'identical_top_k_share': 0.01, 'mean_top_k_jaccard': 0.5, 'depth': 200,
                'verdict': 'MOVEMENT_PRESENT', 'truncation': {'texts': 770, 'truncated': 1, 'share': 0.0013,
                                                              'max_length': 512}}
          for arm in ('FA', 'GR', 'SACR', 'shuffle')}
    c1['anchor_truncation'] = {'texts': 773, 'truncated': 1, 'share': 0.0013, 'max_length': 512}
    return {'_synthetic': 'FAKE VALUES FOR RENDERER TESTS ONLY - not a real test result',
            'status': 'PAPER1_TEST_EVALUATED_ONCE', 'split': 'test', 'queries': 773,
            'results': {'main': main, 'c3_family_overlap_sensitivity': c3,
                        'c3_audit': {'queries': 773, 'query_families_in_corpus': 11, 'self_positive_queries': 3,
                                     'excluded_queries': 11},
                        'confirmatory': confirmatory},
            'retrieval_reference': 'REENCODED_ANCHORS',
            'panel_counts': {'FA': {'used': 770, 'fallback': 3}, 'GR': {'used': 770, 'fallback': 3},
                             'SACR': {'used': 760, 'fallback': 13}},
            'c1': c1, 'protected_test_access': True, 'significance_claim': True, 'gatekeeping_applied': True,
            'process_cpu_seconds': 111.1, 'wall_seconds': 111.1}


if __name__ == '__main__':
    out = Path(__file__).with_name('synthetic-test-summary.json')
    out.write_text(json.dumps(build(), indent=2) + '\n', encoding='utf-8')
    print(out)
