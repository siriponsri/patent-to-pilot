import importlib.util
from pathlib import Path

import pytest


@pytest.fixture
def supervisor(monkeypatch, tmp_path):
    path = Path(__file__).resolve().parents[1] / 'docs/healthtech/audits/ptp-native-dense-preparation-20261110/supervise_native.py'
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
