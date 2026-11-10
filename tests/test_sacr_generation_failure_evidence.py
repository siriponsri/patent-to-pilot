import json

import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_components import digest
from patent_to_pilot.research.sacr_outcomes import summarize_costs
from patent_to_pilot.research import sacr_journal
from test_sacr_generated_view_controller import evidence, prepared


@pytest.mark.parametrize('kind', ['generic', 'selective'])
@pytest.mark.parametrize('status,text', [('NO_EOS', None), ('EOS_COMPLETE', '{bad')])
def test_failure_retains_bound_artifact_observed_cost_and_unknowns(tmp_path, kind, status, text):
    controller = prepared(tmp_path)
    raw, identity, costs = evidence(controller, kind, status=status, text=text)
    costs.update(gpu_seconds=2.5, peak_memory_bytes=None)
    with pytest.raises(InputBoundaryError):
        controller.generated_views('q', kind, lambda *_: (raw, identity, costs))
    receipt, output = controller.journal.read_terminal_attempt(kind)
    assert receipt['status'] == 'FAILED'
    assert output['generation_artifact_utf8'].encode() == raw
    assert output['generation_identity'] == identity
    path = controller.journal.destination / digest(kind)
    event = json.loads((path / 'event.json').read_bytes())
    summary = summarize_costs([event])['metrics']
    assert summary['model_calls']['value'] == 1
    assert summary['input_tokens']['value'] == 3
    assert summary['output_tokens']['value'] == 2
    assert summary['gpu_seconds']['value'] == 2.5
    assert summary['peak_memory_bytes']['value'] is None
    assert summary['peak_memory_bytes']['unknown_events'] == 1
    assert summary['operation_wall_seconds']['value'] >= 0
    with pytest.raises(InputBoundaryError):
        controller.journal.read_completed_output(kind)
    with pytest.raises(FileExistsError):
        controller.generated_views('q', kind, lambda *_: pytest.fail('retry'))
    (path / 'output.json').write_bytes((path / 'output.json').read_bytes() + b' ')
    with pytest.raises(InputBoundaryError, match='output bytes changed'):
        controller.journal.read_terminal_attempt(kind)


@pytest.mark.parametrize('case', ['identity', 'cost', 'exception', 'interrupt'])
def test_unverified_failure_stays_unknown_without_fabricated_artifact(tmp_path, case):
    controller = prepared(tmp_path)
    raw, identity, costs = evidence(controller, 'generic')
    if case == 'identity':
        identity['artifact_sha256'] = 'a' * 64
    if case == 'cost':
        costs['gpu_seconds'] = -1
    def work(*_):
        if case == 'exception':
            raise RuntimeError('authored infrastructure error')
        if case == 'interrupt':
            raise KeyboardInterrupt()
        return raw, identity, costs
    error = KeyboardInterrupt if case == 'interrupt' else RuntimeError if case == 'exception' else InputBoundaryError
    with pytest.raises(error):
        controller.generated_views('q', 'generic', work)
    receipt, output = controller.journal.read_terminal_attempt('generic')
    assert receipt['status'] == ('INTERRUPTED' if case == 'interrupt' else 'FAILED')
    assert output is None
    event = json.loads((controller.journal.destination / digest('generic') / 'event.json').read_bytes())
    assert event['metrics']['model_calls'] is None
    assert event['metrics']['gpu_seconds'] is None


def test_failure_evidence_write_error_remains_unsealed_without_retry(tmp_path, monkeypatch):
    controller = prepared(tmp_path)
    original_write = sacr_journal._write
    def fail_output(path, value):
        if path.name == 'output.json':
            raise OSError('authored disk error')
        return original_write(path, value)
    monkeypatch.setattr(sacr_journal, '_write', fail_output)
    with pytest.raises(OSError):
        controller.generated_views('q', 'generic', lambda *_: evidence(controller, 'generic', text='{bad'))
    path = controller.journal.destination / digest('generic')
    assert (path / 'reservation.json').exists()
    assert not (path / 'seal.json').exists()
    with pytest.raises(InputBoundaryError, match='unsealed'):
        controller.journal.read_terminal_attempt('generic')
    with pytest.raises(FileExistsError):
        controller.generated_views('q', 'generic', lambda *_: pytest.fail('retry'))
