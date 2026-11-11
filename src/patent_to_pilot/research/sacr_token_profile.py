"""Prospective source-token references; no model calls or legacy output repair.

Tokens are maximal non-whitespace source runs, not model tokenizer IDs. Their
zero-based half-open ranges select exact source code-point spans. This preserves
all internal whitespace and punctuation, and disambiguates repeated occurrences.
"""
from copy import deepcopy
import hashlib
import json
import re

from .mtm_runtime import InputBoundaryError, exact_fields
from .sacr_profile import validate_profile

VERSION = 'sacr-profile-token-spans-v1'


def _utf8(text):
    try:
        return text.encode('utf-8')
    except UnicodeError:
        raise InputBoundaryError('invalid Unicode scalar text; no repair') from None


def source_catalogue(source):
    if type(source) is not str or not source.strip():
        raise InputBoundaryError('invalid token-reference source')
    return {'format': 'sacr-source-tokens-v1',
            'source_sha256': hashlib.sha256(_utf8(source)).hexdigest(),
            'tokens': [{'id': i, 'start': m.start(), 'end': m.end(), 'text': m.group()}
                       for i, m in enumerate(re.finditer(r'\S+', source))]}


def _resolve(reference, source, tokens):
    exact_fields(reference, {'field', 'start_token', 'end_token'})
    start, end = reference['start_token'], reference['end_token']
    if (reference['field'] != 'allowed_query' or type(start) is not int or
            type(end) is not int or not 0 <= start < end <= len(tokens)):
        raise InputBoundaryError('invalid token reference range')
    a, b = tokens[start]['start'], tokens[end - 1]['end']
    return {'field': 'allowed_query', 'start': a, 'end': b, 'text': source[a:b]}


def align_token_profile(proposal, *, source, query_id, input_kind):
    if type(proposal) is not dict or proposal.get('profile_version') != VERSION:
        raise InputBoundaryError('only explicitly versioned token profiles may be aligned')
    catalogue = source_catalogue(source)
    original = _utf8(json.dumps(proposal, ensure_ascii=False, sort_keys=True,
                               separators=(',', ':')))
    canonical = deepcopy(proposal)
    canonical['profile_version'] = 'sacr-profile-v0'
    count = 0

    def walk(value):
        nonlocal count
        if type(value) is dict:
            for key, child in value.items():
                if key == 'source_spans':
                    if type(child) is not list:
                        raise InputBoundaryError('invalid token reference list')
                    value[key] = [_resolve(ref, source, catalogue['tokens']) for ref in child]
                    count += len(child)
                else:
                    walk(child)
        elif type(value) is list:
            for child in value:
                walk(child)

    walk(canonical)
    validation = validate_profile(canonical, source=source, query_id=query_id,
                                  input_kind=input_kind)
    raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True,
                     separators=(',', ':')).encode('utf-8')
    return {'profile': canonical, 'validation': validation, 'alignment': {
        'format': VERSION, 'proposal_sha256': hashlib.sha256(original).hexdigest(),
        'canonical_profile_sha256': hashlib.sha256(raw).hexdigest(),
        'catalogue_sha256': hashlib.sha256(json.dumps(catalogue, ensure_ascii=False,
            sort_keys=True, separators=(',', ':')).encode('utf-8')).hexdigest(),
        'resolved_references': count, 'semantic_status': 'unknown',
        'policy': 'EXACT_SOURCE_TOKEN_RANGE_NO_NORMALIZATION_NO_REORDERING'}}
