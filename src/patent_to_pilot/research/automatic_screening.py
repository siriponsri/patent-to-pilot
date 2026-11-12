"""Prospective automatic policy; no dispatch authority or semantic certification."""
from .mtm_runtime import InputBoundaryError

POLICY_VERSION = 'automatic-screening-v1'


def route_result(track, terminal, integrity_valid, screening):
    """Separate unknown execution, integrity failure and semantic abstention.

    integrity_valid covers source identity/isolation; malformed normally returned
    output is represented by screening='invalid_output', not an integrity waiver.
    """
    if track not in ('SACR', 'GRAPH'):
        raise InputBoundaryError('unknown track')
    if type(integrity_valid) is not bool:
        raise InputBoundaryError('integrity evidence must be explicit')
    if terminal not in ('completed', 'failed', 'unknown'):
        raise InputBoundaryError('unknown terminal classification')
    if screening not in ('screened', 'flagged', 'uncertain', 'invalid_output', 'not_run'):
        raise InputBoundaryError('unknown screening classification')
    if not integrity_valid or terminal != 'completed':
        action = 'HOLD'
    elif screening == 'not_run':
        action = 'HOLD'
    elif screening == 'screened':
        action = 'USE_SCREENED_CANDIDATE'
    else:
        action = 'ORIGINAL_QUERY_FALLBACK' if track == 'SACR' else 'ABSTAIN_RELATION'
    return dict(policy=POLICY_VERSION, action=action, screening=screening,
                semantic_certified=False, human_review_required=False)


def complete_query_panel(expected_ids, results, baseline, universe, cutoff=200):
    """Build full SACR panel without dropping failures or accepting partial data.

    results maps each query to a routing decision and candidate ranking. HOLD
    aborts evaluation; fallback reuses the exact frozen baseline ranking.
    """
    ids = list(expected_ids)
    if len(ids) != len(set(ids)) or set(results) != set(ids) or set(baseline) != set(ids):
        raise InputBoundaryError('query cohort incomplete or duplicated')
    if type(cutoff) is not int or cutoff < 1:
        raise InputBoundaryError('invalid cutoff')
    known = set(universe)
    rankings, counts = {}, {'candidate': 0, 'fallback': 0}
    for qid in ids:
        row = results[qid]
        decision = row['decision']
        if decision.get('policy') != POLICY_VERSION or decision.get('semantic_certified') is not False:
            raise InputBoundaryError('unbound screening policy')
        action = decision['action']
        if action == 'ORIGINAL_QUERY_FALLBACK':
            ranking = baseline[qid]
            counts['fallback'] += 1
        elif action == 'USE_SCREENED_CANDIDATE':
            ranking = row['ranking']
            counts['candidate'] += 1
        else:
            raise InputBoundaryError('unresolved query prevents evaluation')
        if not isinstance(ranking, list) or len(ranking) != len(set(ranking)) or not set(ranking) <= known:
            raise InputBoundaryError('invalid family ranking')
        rankings[qid] = list(ranking[:cutoff])
    return {'rankings': rankings, 'queries': len(ids), 'coverage_counts': counts,
            'semantic_certified': False}
