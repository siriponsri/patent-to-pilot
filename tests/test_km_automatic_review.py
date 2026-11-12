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
    result['checks']['negation_modality'] = {'status': 'flagged', 'source_quote': 'The valve must not leak.',
        'candidate_quote': 'The valve leaks.', 'reason': 'Negation reversed.'}
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
    result['checks']['roles_direction'].update(status='uncertain', source_quote='The valve must not leak.')
    assert interpret_review(result, req)['screening'] == 'uncertain'


def test_review_quotes_are_enumerated_literal_spans():
    # v2: synthetic v4 review paraphrased quotes; the grammar now only offers literal spans.
    req = prepare_review(item_id='q2', source='A pump, wherein it stops above 4 kPa. It is not refilled.',
                         candidate='It stops above 4 kPa.', track='SACR', km_text='k', km_sha256=sha('k'))
    spans = req['schema']['properties']['checks']['properties']['roles_direction']['properties']['source_quote']['enum']
    assert spans[0] == '' and 'It is not refilled.' in spans and 'wherein it stops above 4 kPa.' in spans
    assert all(x in req['payload']['source'] for x in spans)


def test_spans_never_need_json_escaping():
    # v3: LMFE emits enum strings literally; a newline/quote/backslash span produced invalid JSON.
    from patent_to_pilot.research.km_automatic_review import literal_spans
    spans = literal_spans('Pump title\nA pump, wherein it stops. It says "x" ok. Path a' + chr(92) + 'b.')
    assert 'Pump title' in spans and 'A pump,' in spans
    assert all('\n' not in s and '"' not in s and chr(92) not in s for s in spans)
