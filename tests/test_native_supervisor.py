import importlib.util
from pathlib import Path

import pytest


@pytest.fixture(params=['ptp-native-dense-preparation-20261110/supervise_native.py',
                        'ptp-syn-sacr004-20261110/supervise.py',
                        'ptp-native-sacr-fidelity-20261110/supervise.py'])
def supervisor(monkeypatch, tmp_path, request):
    path = Path(__file__).resolve().parents[1] / 'docs/healthtech/audits' / request.param
    spec = importlib.util.spec_from_file_location('native_supervisor_test', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'JOB', tmp_path)
    monkeypatch.setattr(module.time, 'sleep', lambda _: None)
    return module


class Live:
    def poll(self):
        return None


def test_wall_bound_stops_owned_attempt(supervisor, monkeypatch):
    stopped = []
    monkeypatch.setattr(supervisor.time, 'monotonic', lambda: 14395)
    monkeypatch.setattr(supervisor, 'stop_owned', lambda: stopped.append(True))
    assert supervisor.monitor(Live(), 0) == ('TIMEOUT', 0)
    assert stopped == [True]


def test_transient_observation_failures_reobserve_then_stop(supervisor, monkeypatch):
    calls, stopped = [], []
    def fail():
        calls.append(1)
        raise RuntimeError('inspect unavailable')
    monkeypatch.setattr(supervisor.time, 'monotonic', lambda: 1)
    monkeypatch.setattr(supervisor, 'inspect', fail)
    monkeypatch.setattr(supervisor, 'stop_owned', lambda: stopped.append(True))
    assert supervisor.monitor(Live(), 0) == ('OBSERVATION_FAILED_STOPPED', 0)
    assert len(calls) == 3 and stopped == [True]


def test_unexpected_exception_stops_before_propagation(supervisor, monkeypatch):
    stopped = []
    monkeypatch.setattr(supervisor.time, 'monotonic', lambda: 1)
    monkeypatch.setattr(supervisor, 'inspect', lambda: {})
    monkeypatch.setattr(supervisor, 'stop_owned', lambda: stopped.append(True))
    with pytest.raises(KeyError):
        supervisor.monitor(Live(), 0)
    assert stopped == [True]


def test_fidelity_child_receipt_failure_stops_owned_job(supervisor, monkeypatch):
    if not hasattr(supervisor, 'start_and_monitor'):
        pytest.skip('new lifecycle guard applies to native fidelity supervisor')
    stopped = []
    class Child:
        pid = 123
    monkeypatch.setattr(supervisor.subprocess, 'Popen', lambda *a, **k: Child())
    monkeypatch.setattr(supervisor, 'write', lambda *a: (_ for _ in ()).throw(OSError('disk full')))
    monkeypatch.setattr(supervisor, 'stop_owned', lambda: stopped.append(True))
    with pytest.raises(OSError, match='disk full'):
        supervisor.start_and_monitor(0, None, None)
    assert stopped == [True]


def test_fidelity_reserves_cleanup_margin(supervisor, monkeypatch):
    if not hasattr(supervisor, 'start_and_monitor'):
        pytest.skip('new cleanup margin applies to native fidelity supervisor')
    stopped = []
    monkeypatch.setattr(supervisor.time, 'monotonic', lambda: 6960)
    monkeypatch.setattr(supervisor, 'stop_owned', lambda: stopped.append(True))
    assert supervisor.monitor(Live(), 0) == ('TIMEOUT', 0)
    assert stopped == [True]
