"""SACR pilot retrieval panel (NATIVE-STAGES-20261112 addendum, frozen before any SACR score).

Texts are encoded exactly like B0 (DENSE_QUERY_PREFIX + text). Anchors (original TA) are
re-encoded in the same job; if they do not reproduce the pinned B0 rankings, the anchors
become the reference and the drift is reported. Fallback queries keep the reference ranking.
"""
from .mtm_runtime import InputBoundaryError

ACTION = 'USE_SCREENED_CANDIDATE'


def encode_plan(pilot, decisions, candidates, prefix):
    """pilot: [{'id','text'}]; decisions: {id: {'action',...}}; candidates: {id: selective text}."""
    ids = [p['id'] for p in pilot]
    if len(ids) != len(set(ids)) or set(decisions) != set(ids):
        raise InputBoundaryError('decisions must cover exactly the frozen pilot')
    if any(d.get('action') not in (ACTION, 'ORIGINAL_QUERY_FALLBACK') for d in decisions.values()):
        raise InputBoundaryError('unresolved (HOLD) query in pilot panel')
    screened = [i for i in ids if decisions[i]['action'] == ACTION]
    if any(type(candidates.get(i)) is not str or not candidates[i].strip() for i in screened):
        raise InputBoundaryError('screened query without candidate text')
    rows = [('anchor', p['id'], prefix + p['text']) for p in pilot]
    rows += [('sacr', i, prefix + candidates[i]) for i in screened]
    return rows


def anchor_check(anchor_rankings, b0_rankings):
    same = [q for q, r in anchor_rankings.items() if b0_rankings.get(q, {}).get('families') == r['families']]
    return {'queries': len(anchor_rankings), 'identical_family_lists': len(same),
            'reference': 'B0_PINNED' if len(same) == len(anchor_rankings) else 'REENCODED_ANCHORS'}


def assemble(pilot, decisions, sacr_rankings, reference_rankings):
    panel, counts = {}, {'screened': 0, 'fallback': 0}
    for p in pilot:
        q = p['id']
        if decisions[q]['action'] == ACTION:
            panel[q] = sacr_rankings[q]; counts['screened'] += 1
        else:
            panel[q] = reference_rankings[q]; counts['fallback'] += 1
    return panel, counts
