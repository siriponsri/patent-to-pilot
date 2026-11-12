from copy import deepcopy
import pytest
from patent_to_pilot.research.km_automatic_review import prepare_review, interpret_review, CHECKS
from patent_to_pilot.research.patent_structure_marking import sha, RequestIntegrityError
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def example():
    req = prepare_review(item_id='q1', source='The valve must not leak.', candidate='The valve leaks.',
                         track='SACR', km_text='Preserve negation.', km_sha256=sha('Preserve negation.'))
    result = {'binding_sha256': req['binding_sha256'], 'checks': {
        k: {'status': 'screened', 'source_quote': '', 'candidate_quote': '', 'reason': 'No problem detected.'}
        for k in CHECKS}}
    return req, result


def test_flag_preserved_without_semantic_certification():
    req, result = example()
    result['checks']['negation_modality'] = {'status': 'flagged', 'source_quote': 'must not leak',
        'candidate_quote': 'leaks', 'reason': 'Negation reversed.'}
    out = interpret_review(result, req)
    assert out['screening'] == 'flagged' and not out['semantic_certified']
    assert not out['reviewer_validated']


@pytest.mark.parametrize('problem', ['missing_check', 'wrong_binding', 'invented_quote', 'unsupported_flag', 'changed_request'])
def test_invalid_review_cannot_pass(problem):
    req, result = example()
    if problem == 'missing_check': del result['checks']['roles_direction']
    if problem == 'wrong_binding': result['binding_sha256'] = 'f' * 64
    if problem == 'invented_quote': result['checks']['roles_direction']['source_quote'] = 'not in source'
    if problem == 'unsupported_flag': result['checks']['roles_direction']['status'] = 'flagged'
    if problem == 'changed_request': req['payload']['candidate'] = 'changed'
    with pytest.raises(RequestIntegrityError if problem == 'changed_request' else InputBoundaryError):
        interpret_review(result, req)


def test_uncertainty_is_not_a_pass_and_screened_is_not_certified():
    req, result = example()
    assert not interpret_review(result, req)['semantic_certified']
    result['checks']['roles_direction'].update(status='uncertain', source_quote='valve')
    assert interpret_review(result, req)['screening'] == 'uncertain'
