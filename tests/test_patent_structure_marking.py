from copy import deepcopy
import pytest
from patent_to_pilot.research.patent_structure_marking import prepare, validate_and_render, sha, VERSION, RequestIntegrityError
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def example():
    text = 'The pump reduces pressure except during cleaning.'
    request = prepare(text, 'q1', 'Keep exceptions.', sha('Keep exceptions.'))
    result = {'version': VERSION, 'query_id': 'q1', 'source_sha256': sha(text),
              'labels': ['none'] * 4 + ['exception'] * 3, 'uncertain_roles': [],
              'abstraction': text}
    return request, result


def test_mark_preserves_complete_anchor_and_exact_exception():
    request, output = example()
    result = validate_and_render(output, request)
    assert result['marks'][0]['text'] == 'except during cleaning.'
    assert result['anchor'] == request['payload']['source']
    assert result['candidate_available'] and not result['semantic_certified']
    assert result['screening_required']


@pytest.mark.parametrize('failure', ['wrong_source', 'short', 'long', 'unknown_label'])
def test_invalid_mark_is_rejected(failure):
    request, output = example()
    if failure == 'wrong_source': output['source_sha256'] = 'f' * 64
    if failure == 'short': output['labels'] = output['labels'][:-1]
    if failure == 'long': output['labels'] = output['labels'] + ['none']
    if failure == 'unknown_label': output['labels'][0] = 'claim'
    with pytest.raises(InputBoundaryError): validate_and_render(output, request)


def test_uncertainty_and_null_do_not_become_candidates():
    request, output = example()
    output['uncertain_roles'] = ['exception']
    assert not validate_and_render(output, request)['candidate_available']
    output['uncertain_roles'] = []; output['abstraction'] = None
    assert not validate_and_render(output, request)['candidate_available']


def test_changed_km_rejected_before_generation():
    with pytest.raises(InputBoundaryError): prepare('source text', 'q1', 'changed', sha('original'))


def test_blank_abstraction_is_rejected_as_model_output():
    request, output = example()
    output['abstraction'] = '   '
    with pytest.raises(InputBoundaryError): validate_and_render(output, request)


@pytest.mark.parametrize('field', ['source', 'schema'])
def test_request_corruption_is_not_output_rejection(field):
    request, output = example()
    if field == 'source': request['payload']['source'] = 'changed'
    else: request['schema']['properties']['query_id']['const'] = 'changed'
    with pytest.raises(RequestIntegrityError): validate_and_render(output, request)


def test_labels_are_fixed_length_and_runs_become_marks():
    # v2 smoke repeated one interval up to the item cap; v3 fixes output length to the source.
    km = 'Preserve conditions and exceptions.'
    text = 'The pump stops below 5 kPa except during cleaning.'
    request = prepare(text, 'q-bounds', km, sha(km))
    labels = request['schema']['properties']['labels']; count = len(request['payload']['tokens'])
    assert labels['minItems'] == labels['maxItems'] == count and VERSION == 'patent-structure-marking-v5'
    output = {'version': VERSION, 'query_id': 'q-bounds', 'source_sha256': sha(text),
              'labels': ['entity', 'entity', 'action', 'condition', 'condition', 'condition',
                         'exception', 'exception', 'exception'], 'uncertain_roles': [], 'abstraction': text}
    marks = validate_and_render(output, request)['marks']
    assert [(m['role'], m['text']) for m in marks] == [('entity', 'The pump'), ('action', 'stops'),
        ('condition', 'below 5 kPa'), ('exception', 'except during cleaning.')]


def test_worked_examples_are_valid_marking_outputs_and_not_the_synthetic_source():
    from patent_to_pilot.research.patent_structure_marking import EXAMPLES
    km = 'Preserve conditions and exceptions.'
    for i, example in enumerate(EXAMPLES):
        request = prepare(example['source'], 'example-%d' % i, km, sha(km))
        output = {'version': VERSION, 'query_id': 'example-%d' % i, 'source_sha256': sha(example['source']),
                  'labels': example['labels'], 'uncertain_roles': example['uncertain_roles'],
                  'abstraction': example['abstraction']}
        result = validate_and_render(output, request)
        assert result['candidate_available'] and result['marks']
        assert 'infusion pump' not in example['source']   # never the GPU synthetic test sentence
    assert 'Worked examples' in request['messages'][0]['content']


def test_model_sees_token_texts_only_but_validation_keeps_offsets():
    km = 'Preserve conditions and exceptions.'
    text = 'The pump stops below 5 kPa except during cleaning.'
    request = prepare(text, 'q-compact', km, sha(km))
    import json
    shown = json.loads(request['messages'][1]['content'])
    assert shown['tokens'] == text.split() and all('start' in t for t in request['payload']['tokens'])
