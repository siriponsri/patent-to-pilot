import copy
import hashlib
import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_token_profile import (
    VERSION, align_token_profile, source_catalogue,
)
from test_sacr_profile import fixture


def proposal(source, ranges):
    p = fixture()
    p['source_sha256'] = hashlib.sha256(source.encode('utf-8')).hexdigest()
    p['profile_version'] = VERSION
    p['blocks'] = [{'block_id': 'b'+str(i), 'relation_text': text,
                    'attached_conditions': [], 'source_spans': [
                        {'field': 'allowed_query', 'start_token': a, 'end_token': b}]}
                   for i, (a, b, text) in enumerate(ranges)]
    return p


def align(p, source):
    return align_token_profile(p, source=source, query_id='q1', input_kind='MTM_P')


def test_repeated_occurrences_have_distinct_exact_offsets_and_no_mutation():
    source = 'A works. A works.'
    p = proposal(source, [(0, 2, 'A works.'), (2, 4, 'A works.')])
    before = copy.deepcopy(p)
    result = align(p, source)
    assert p == before
    assert [b['source_spans'][0]['start'] for b in result['profile']['blocks']] == [0, 9]
    assert result['alignment']['semantic_status'] == 'unknown'
    assert result == align(p, source)


def test_unicode_internal_whitespace_and_punctuation_are_unchanged():
    source = ' 🧪\tแรงดันต่ำ  (5 kPa).\n'
    tokens = source_catalogue(source)['tokens']
    assert [t['text'] for t in tokens] == ['🧪', 'แรงดันต่ำ', '(5', 'kPa).']
    text = source[1:-1]
    result = align(proposal(source, [(0, 4, text)]), source)
    assert result['profile']['blocks'][0]['source_spans'][0] == {
        'field': 'allowed_query', 'start': 1, 'end': len(source)-1, 'text': text}


@pytest.mark.parametrize('bounds', [(-1, 1), (0, 0), (2, 1), (0, 3), (False, 1), (0, True), ('0', 1)])
def test_invalid_ranges_fail(bounds):
    with pytest.raises(InputBoundaryError):
        align(proposal('A works.', [(*bounds, 'A works.')]), 'A works.')


@pytest.mark.parametrize('change', ['source', 'query', 'field', 'legacy', 'extra', 'order', 'condition'])
def test_existing_source_schema_order_and_condition_rules_remain(change):
    source = 'A works. B stops.'
    p = proposal(source, [(0, 2, 'A works.'), (2, 4, 'B stops.')])
    if change == 'source': p['source_sha256'] = '0'*64
    elif change == 'query': p['query_id'] = 'other'
    elif change == 'field': p['blocks'][0]['source_spans'][0]['field'] = 'hidden'
    elif change == 'legacy': p['profile_version'] = 'sacr-profile-quotes-v1'
    elif change == 'extra': p['targets'] = ['hidden']
    elif change == 'order': p['blocks'].reverse()
    else:
        p['blocks'][0]['attached_conditions'] = [{
            'condition_id': 'c1', 'raw_text': 'invented', 'normalized_text': 'invented',
            'kind': 'qualitative', 'relation_to_block': 'explicit',
            'source_spans': [{'field': 'allowed_query', 'start_token': 0, 'end_token': 2}]}]
    with pytest.raises(InputBoundaryError): align(p, source)


def test_normalized_relation_is_flagged_not_semantically_accepted():
    result = align(proposal('A works.', [(0, 2, 'A improves performance')]), 'A works.')
    assert 'relation_normalization' in result['validation']['review_flags']
    assert result['validation']['semantic_status'] == 'unknown'


def test_prompt_and_generation_dispatch_are_explicit_and_bound():
    from test_sacr_prompts import build
    from patent_to_pilot.research.sacr_generation import GenerationLimits, validate_generation
    source = 'A works. A works.'
    messages = build('profile_tokens', source=source)
    payload = json.loads(messages['messages'][1]['content'])
    assert payload['allowed_query'] == source
    assert payload['source_tokens'] == [[0, 'A'], [1, 'works.'], [2, 'A'], [3, 'works.']]
    assert payload['identity']['profile_version'] == VERSION
    assert messages['prompt_sha256'] != build('profile_quotes')['prompt_sha256']
    raw = json.dumps(proposal(source, [(2, 4, 'A works.')]))
    record = {'status': 'EOS_COMPLETE', 'text': raw,
              'response_sha256': hashlib.sha256(raw.encode()).hexdigest()}
    args = dict(kind='profile_tokens', source=source, query_id='q1', input_kind='MTM_P', limits=GenerationLimits())
    result = validate_generation(record, **args)
    assert result['profile']['blocks'][0]['source_spans'][0]['start'] == 9
    record['status'] = 'OUTPUT_LIMIT'
    assert validate_generation(record, **args)['anchor_fallback_required']
