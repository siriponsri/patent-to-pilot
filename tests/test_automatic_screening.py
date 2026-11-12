import pytest
from patent_to_pilot.research.automatic_screening import route_result, complete_query_panel
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


@pytest.mark.parametrize('track', ['SACR', 'GRAPH'])
@pytest.mark.parametrize('terminal', ['failed', 'unknown'])
def test_uncertain_execution_never_falls_back(track, terminal):
    assert route_result(track, terminal, True, 'flagged')['action'] == 'HOLD'


def test_integrity_failure_cannot_be_screened_away():
    assert route_result('SACR', 'completed', False, 'screened')['action'] == 'HOLD'


def test_semantic_risk_has_explicit_track_specific_outcome():
    assert route_result('SACR', 'completed', True, 'uncertain')['action'] == 'ORIGINAL_QUERY_FALLBACK'
    assert route_result('GRAPH', 'completed', True, 'flagged')['action'] == 'ABSTAIN_RELATION'
    assert not route_result('GRAPH', 'completed', True, 'screened')['semantic_certified']


def test_fallback_keeps_query_and_exact_baseline_order():
    rows = {'q1': {'decision': route_result('SACR', 'completed', True, 'invalid_output')},
            'q2': {'decision': route_result('SACR', 'completed', True, 'screened'), 'ranking': ['c', 'a']}}
    out = complete_query_panel(['q1', 'q2'], rows, {'q1': ['b', 'a'], 'q2': ['a', 'b']}, ['a', 'b', 'c'])
    assert out['rankings'] == {'q1': ['b', 'a'], 'q2': ['c', 'a']}
    assert out['queries'] == 2 and out['coverage_counts'] == {'candidate': 1, 'fallback': 1}


def test_missing_query_cannot_improve_denominator():
    with pytest.raises(InputBoundaryError):
        complete_query_panel(['q1'], {}, {'q1': ['a']}, ['a'])


def test_hold_cannot_be_silently_dropped():
    with pytest.raises(InputBoundaryError):
        complete_query_panel(['q1'], {'q1': {'decision': route_result('SACR', 'unknown', True, 'not_run')}}, {'q1': ['a']}, ['a'])
