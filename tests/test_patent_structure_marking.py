from copy import deepcopy
import pytest
from patent_to_pilot.research.patent_structure_marking import prepare, validate_and_render, sha, VERSION, RequestIntegrityError
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def example():
    text = 'The pump reduces pressure except during cleaning.'
    request = prepare(text, 'q1', 'Keep exceptions.', sha('Keep exceptions.'))
    result = {'version': VERSION, 'query_id': 'q1', 'source_sha256': sha(text),
              'marks': [{'role': 'exception', 'start_token': 4, 'end_token': 7, 'attachment': 'explicit'}],
              'abstraction': text}
    return request, result


def test_mark_preserves_complete_anchor_and_exact_exception():
    request, output = example()
    result = validate_and_render(output, request)
    assert result['marks'][0]['text'] == 'except during cleaning.'
    assert result['anchor'] == request['payload']['source']
    assert result['candidate_available'] and not result['semantic_certified']
    assert result['screening_required']


@pytest.mark.parametrize('failure', ['wrong_source', 'reversed', 'duplicate', 'out_of_range'])
def test_invalid_mark_is_rejected(failure):
    request, output = example()
    if failure == 'wrong_source': output['source_sha256'] = 'f' * 64
    if failure == 'reversed': output['marks'][0]['end_token'] = 3
    if failure == 'duplicate': output['marks'].append(deepcopy(output['marks'][0]))
    if failure == 'out_of_range': output['marks'][0]['end_token'] = 100
    with pytest.raises(InputBoundaryError): validate_and_render(output, request)


def test_uncertainty_and_null_do_not_become_candidates():
    request, output = example()
    output['marks'][0]['attachment'] = 'uncertain'
    assert not validate_and_render(output, request)['candidate_available']
    output['marks'][0]['attachment'] = 'explicit'; output['abstraction'] = None
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
