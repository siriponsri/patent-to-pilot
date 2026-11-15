"""Paper 1 retrieval panel (frozen protocol 2026-11-13 + amendment A1): which texts are encoded per query.

Every text is encoded exactly like B0 (query prefix + text). Per query: the original TA anchor, the A1
F-shuffle control (deterministic word shuffle, no LLM) and, for each arm, the arm text when the arm
decision is a use action. Fallback queries keep the reference (B0) ranking. No labels are used here.
"""
from .mtm_runtime import InputBoundaryError
from .paper1_controls import shuffled_query

USE_ACTIONS = {'rewrite': 'USE_REWRITE', 'sacr': 'USE_SCREENED_CANDIDATE'}
FALLBACK = 'ORIGINAL_QUERY_FALLBACK'


def merge_sources(queries, sources, kind):
    """sources: [(job_queries, decisions, texts)] in batch order -> (decisions, texts) covering exactly `queries`."""
    if kind not in USE_ACTIONS:
        raise InputBoundaryError('unknown arm kind')
    ids = [q['id'] for q in queries]; source = {q['id']: q['text'] for q in queries}
    if len(ids) != len(set(ids)):
        raise InputBoundaryError('duplicate query')
    decisions, texts = {}, {}
    for job_queries, job_decisions, job_texts in sources:
        job_ids = [q['id'] for q in job_queries]
        if set(job_decisions) != set(job_ids) or set(job_ids) & set(decisions):
            raise InputBoundaryError('arm job decisions must cover its own queries exactly once')
        for q in job_queries:
            if source.get(q['id']) != q['text']:
                raise InputBoundaryError('arm job query differs from the retrieval query set')
            action = job_decisions[q['id']].get('action')
            if action not in (USE_ACTIONS[kind], FALLBACK):
                raise InputBoundaryError('unresolved (HOLD) query in arm job')
            decisions[q['id']] = action
            if action != FALLBACK:
                text = job_texts.get(q['id'])
                if type(text) is not str or not text.strip():
                    raise InputBoundaryError('used query without arm text')
                texts[q['id']] = text
    if set(decisions) != set(ids):
        raise InputBoundaryError('arm jobs must cover exactly the retrieval query set')
    return decisions, texts


def encode_plan(queries, arms, prefix, shuffle=True):
    """arms: {name: (decisions, texts)} -> [(kind, query_id, text_to_encode)]; anchors first."""
    rows = [('anchor', q['id'], prefix + q['text']) for q in queries]
    if shuffle:
        rows += [('shuffle', q['id'], prefix + shuffled_query(q['id'], q['text'])) for q in queries]
    for name in sorted(arms):
        if name in ('anchor', 'shuffle'):
            raise InputBoundaryError('reserved arm name')
        _, texts = arms[name]
        rows += [(name, q['id'], prefix + texts[q['id']]) for q in queries if q['id'] in texts]
    return rows


def anchor_check(anchor_rankings, b0_rankings):
    same = [q for q, r in anchor_rankings.items() if b0_rankings.get(q, {}).get('families') == r['families']]
    return {'queries': len(anchor_rankings), 'identical_family_lists': len(same),
            'reference': 'B0_PINNED' if len(same) == len(anchor_rankings) else 'REENCODED_ANCHORS'}


def assemble(queries, texts, arm_rankings, reference_rankings):
    """Standalone arm panel: arm ranking where the arm text was used, the reference ranking on fallback."""
    panel, counts = {}, {'used': 0, 'fallback': 0}
    for q in queries:
        i = q['id']
        if i in texts:
            panel[i] = arm_rankings[i]; counts['used'] += 1
        else:
            panel[i] = reference_rankings[i]; counts['fallback'] += 1
    return panel, counts


def partial_job_decisions(kind, job_queries, results, hold_index):
    """Decisions for an arm job that stopped on one query (no decisions-private.json was written).

    results: parsed result.json for job queries 0..hold_index-1 (all must exist). The query at hold_index
    raised the HOLD; under the owner decisions of 2026-11-14/15 it is an ORIGINAL_QUERY_FALLBACK and is not
    regenerated. Queries after hold_index never started and must be covered by a continuation job.
    Returns (covered_queries, decisions).
    """
    if kind not in USE_ACTIONS:
        raise InputBoundaryError('unknown arm kind')
    if type(hold_index) is not int or not 0 <= hold_index < len(job_queries) or len(results) != hold_index:
        raise InputBoundaryError('partial job needs exactly one result per query before the hold')
    decisions = {}
    for q, r in zip(job_queries[:hold_index], results):
        action = r.get('action') if kind == 'rewrite' else (r.get('decision') or {}).get('action')
        if r.get('query_id') != q['id'] or action not in (USE_ACTIONS[kind], FALLBACK):
            raise InputBoundaryError('partial job result identity or action invalid')
        decisions[q['id']] = {'action': action, 'reason': r.get('reason')}
    decisions[job_queries[hold_index]['id']] = {'action': FALLBACK, 'reason': 'HOLD_ENGINEERING_FAILURE_OWNER_FALLBACK'}
    return job_queries[:hold_index + 1], decisions
