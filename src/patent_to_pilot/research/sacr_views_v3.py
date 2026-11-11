"""Prospective R3 views. Rendering is not fidelity admission or retrieval dispatch."""
from .sacr_evidence_v3 import compile_evidence


def _union(intervals):
    merged = []
    for start, end in sorted(set(intervals)):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return merged


def render_views(proposal, *, source, query_id):
    compiled = compile_evidence(proposal, source=source, query_id=query_id)
    base = {'source_anchor': source, 'retrieval_ready': False,
            'semantic_status': 'UNKNOWN_REQUIRES_REVIEW', 'omission_review_required': True}
    if compiled['anchor_fallback_required']:
        return {**base, 'status': 'ABSTAINED', 'compact': None, 'selective': None,
                'source_intervals': [], 'proposed_abstractions': 0}
    intervals = []
    for block in compiled['blocks']:
        evidence = list(block['literal_evidence'])
        for condition in block['conditions']:
            evidence.extend(condition['literal_evidence'])
            evidence.extend(condition['attachment_evidence'])
        intervals.extend((span['start'], span['end']) for span in evidence)
    merged = _union(intervals)
    compact = '\n'.join(source[a:b] for a, b in merged)
    # Selective proposals are reviewed as a distinct query, not substituted into
    # literal evidence. Condition and attachment context remain exact source.
    selective_parts = []
    selective_intervals = []
    count = 0
    for block in compiled['blocks']:
        if block['abstraction_proposal'] is not None:
            selective_parts.append(block['abstraction_proposal']); count += 1
        else:
            selective_intervals.extend((s['start'], s['end']) for s in block['literal_evidence'])
        for condition in block['conditions']:
            selective_intervals.extend((s['start'], s['end']) for s in
                                       condition['attachment_evidence'] + condition['literal_evidence'])
    selective_merged = _union(selective_intervals)
    selective_parts.extend(source[a:b] for a,b in selective_merged)
    # Deduplicate source occurrences only, never equal strings or generated text.
    # Proposal-versus-source repetition remains visible for lexical screening.
    return {**base, 'status': 'PROPOSED_VIEWS_FIDELITY_PENDING',
            'compact': compact, 'selective': '\n'.join(selective_parts),
            'source_intervals': merged, 'selective_source_intervals': selective_merged,
            'proposed_abstractions': count}
