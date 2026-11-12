"""Pilot-20 evaluation of B0 vs SACR panel (NATIVE-STAGES-20261112 addendum; no significance claims).

Uses the native evaluator unchanged, restricting eligible qrels to the frozen pilot IDs. Per-query
rows are private; only macro metrics and paired win/loss/tie counts are published.
"""
from ..evaluation.dapfam_native import native_dev_task, evaluate_paper1_dev
from .mtm_runtime import InputBoundaryError

PARTITIONS = ('ALL', 'IN', 'OUT')


def evaluate_arms(corpus, queries, relations, pilot_ids, arms):
    pilot = set(pilot_ids)
    if len(pilot) != len(pilot_ids) or set(arms) != {'B0', 'SACR'}:
        raise InputBoundaryError('frozen pilot and both arms required')
    for name, table in arms.items():
        if set(table) != pilot:
            raise InputBoundaryError('every arm must rank exactly the pilot queries: ' + name)
    public, private = {}, {}
    for partition in PARTITIONS:
        task = native_dev_task(corpus, queries, relations, partition=partition)
        task['qrels'] = {q: g for q, g in task['qrels'].items() if q in pilot}
        if not task['qrels']:
            public[partition] = {'eligible_queries': 0}; continue
        results = {name: evaluate_paper1_dev(task, {q: table[q] for q in pilot}) for name, table in arms.items()}
        per = {name: r.pop('per_query') for name, r in results.items()}
        paired = {}
        for metric in results['B0']['metrics']:
            deltas = [per['SACR'][q][metric] - per['B0'][q][metric] for q in task['qrels']]
            paired[metric] = {'sacr_better': sum(d > 1e-12 for d in deltas), 'b0_better': sum(d < -1e-12 for d in deltas),
                              'ties': sum(abs(d) <= 1e-12 for d in deltas), 'mean_delta': round(sum(deltas) / len(deltas), 5)}
        public[partition] = {'eligible_queries': len(task['qrels']), 'B0': results['B0']['metrics'],
                             'SACR': results['SACR']['metrics'], 'paired': paired}
        private[partition] = per
    return public, private
