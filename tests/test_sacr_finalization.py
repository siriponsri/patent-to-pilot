import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_selection_result import selection_outcome
from test_sacr_retrieval_controller import ready


def completed(tmp_path):
    controller, index, p = ready(tmp_path)
    controller.acquire('q', index, p['eligible'])
    selected = controller.select('q', index, p['eligible'])
    return controller, index, p, selected


def test_controller_derives_complete_outcomes_without_rerun(tmp_path, monkeypatch):
    controller, index, p, selected = completed(tmp_path)
    def forbidden(*args, **kwargs):
        pytest.fail('finalization must not rerun search/selection')
    monkeypatch.setattr('patent_to_pilot.research.sacr_controller.acquire_union', forbidden)
    monkeypatch.setattr('patent_to_pilot.research.sacr_controller.compare_factorial', forbidden)
    report = controller.finalize_ready(index, {'q': p['eligible']})
    assert report['cohort']['queries'] == 1
    outcomes = json.loads((controller.journal.destination / 'outcomes.json').read_text())
    assert outcomes == [selection_outcome(selected)]
    assert not report['protected_evaluation_authorized']


@pytest.mark.parametrize('change', ['reverse', 'drop', 'add', 'state'])
def test_low_level_journal_rejects_different_outcome_from_typed_selection(tmp_path, change):
    controller, _, _, selected = completed(tmp_path)
    outcome = selection_outcome(selected)
    if change == 'reverse':
        outcome['rankings']['I/L'].reverse()
    elif change == 'drop':
        outcome['rankings']['I/L'].pop()
    elif change == 'add':
        outcome['rankings']['I/L'].append('invented-family')
    else:
        from patent_to_pilot.research.sacr_outcomes import finalize_query
        outcome = finalize_query(query_id='q', state='REVIEW_REQUIRED')
    with pytest.raises(InputBoundaryError, match='differs from sealed selection'):
        controller.journal.finalize([outcome])
    assert not (controller.journal.destination / 'completion.json').exists()


def test_incomplete_query_not_silently_dropped(tmp_path):
    controller, index, p = ready(tmp_path)
    with pytest.raises(InputBoundaryError, match='unsealed'):
        controller.finalize_ready(index, {'q': p['eligible']})
    assert not (controller.journal.destination / 'outcomes.json').exists()


def test_foreign_or_missing_masks_do_not_shrink_cohort(tmp_path):
    controller, index, p, _ = completed(tmp_path)
    for masks in ({}, {'other': p['eligible']}):
        with pytest.raises(InputBoundaryError, match='exact declared mask cohort'):
            controller.finalize_ready(index, masks)


def test_changed_selection_refused_before_final_artifacts(tmp_path):
    controller, index, p, _ = completed(tmp_path)
    path = controller.journal.destination / digest('selection') / 'output.json'
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(InputBoundaryError, match='bytes changed'):
        controller.finalize_ready(index, {'q': p['eligible']})
    assert not (controller.journal.destination / 'outcomes.json').exists()
