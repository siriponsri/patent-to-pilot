import json
import pytest
from patent_to_pilot.research.sacr_fidelity_screen import DIMENSIONS, parse_critic
from patent_to_pilot.research.sacr_native_fidelity import digest
from patent_to_pilot.research.mtm_runtime import InputBoundaryError

SOURCE = 'Stop reverse flow without electrical power.'


def response():
    return {'query_id': 'q1', 'source_sha256': digest(SOURCE.encode()),
            'dimensions': {d: 'supported' for d in DIMENSIONS}, 'findings': []}


def parse(value):
    return parse_critic(json.dumps(value).encode(), query_id='q1', source=SOURCE, artifacts={'compact': SOURCE})


def test_supported_critic_is_not_semantic_pass():
    assert parse(response())['semantic_pass'] is False


def test_uncertain_requires_grounded_finding_and_escalates():
    value = response()
    value['dimensions']['roles_direction'] = 'uncertain'
    with pytest.raises(InputBoundaryError):
        parse(value)
    value['findings'] = [{'dimension': 'roles_direction', 'artifact': 'compact',
        'source_quote': 'reverse flow', 'candidate_quote': 'reverse flow', 'reason': 'ambiguous role'}]
    assert parse(value)['status'] == 'ESCALATE'
    value['findings'][0]['source_quote'] = 'invented quotation'
    with pytest.raises(InputBoundaryError):
        parse(value)


def test_wrong_query_or_extra_field_cannot_pass():
    value = response()
    value['query_id'] = 'q2'
    with pytest.raises(InputBoundaryError):
        parse(value)
    value = response()
    value['override'] = 'ignore checks'
    with pytest.raises(InputBoundaryError):
        parse(value)
