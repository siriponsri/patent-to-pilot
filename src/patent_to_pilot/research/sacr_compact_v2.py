"""Prospective v2 compact renderer: union exact source occurrences, not strings.

R1 renderer and artifacts remain unchanged. Deduplicating repeated evidence
references must never erase separate occurrences of identical source text.
"""
from .sacr_profile import validate_profile

VERSION = 'sacr-compact-source-interval-union-v2'


def _occurrence(text, spans, source):
    found = set()
    for span in spans:
        offset = span['start']
        while True:
            start = source.find(text, offset, span['end'])
            if start < 0:
                break
            found.add((start, start + len(text)))
            offset = start + 1
    return next(iter(found)) if len(found) == 1 else None


def compact_view_v2(profile, *, source, query_id, input_kind):
    validation = validate_profile(profile, source=source, query_id=query_id, input_kind=input_kind)
    base = {'version': VERSION, 'semantic_status': 'unknown', 'fidelity_review': 'REQUIRED'}
    if validation['anchor_fallback_required']:
        return {**base, 'status': 'ANCHOR_FALLBACK', 'text': None}
    if (validation['review_flags'] or validation['uncertain_conditions'] or profile['unknowns'] or
            profile['extraction_status'] != 'valid' or
            any(c['action'] != 'retain' for c in profile['context_items'])):
        return {**base, 'status': 'REVIEW_REQUIRED', 'text': None}
    requirements = []
    for block in profile['blocks']:
        requirements.append((block['relation_text'], block['source_spans']))
        requirements.extend((c['raw_text'], c['source_spans']) for c in block['attached_conditions'])
    requirements.extend((c['raw_text'], c['source_spans']) for c in profile['context_items'])
    intervals = [_occurrence(text, spans, source) for text, spans in requirements]
    if any(span is None for span in intervals):
        return {**base, 'status': 'REVIEW_REQUIRED', 'reason': 'AMBIGUOUS_TEXT_OCCURRENCE', 'text': None}
    merged = []
    for start, end in sorted(set(intervals)):
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    spans = [{'field': 'allowed_query', 'start': start, 'end': end, 'text': source[start:end]}
             for start, end in merged]
    return {**base, 'status': 'PROPOSED_COMPACT_V2', 'text': '\n'.join(s['text'] for s in spans),
            'source_spans': spans, 'referenced_occurrences': len(intervals), 'merged_intervals': len(spans)}
