from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "healthtech" / "run_real_baselines.py"
SPEC = importlib.util.spec_from_file_location("run_real_baselines", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _device() -> SimpleNamespace:
    return SimpleNamespace(
        query_id="device-1",
        company="Acme Medical",
        technical_description="implantable catheter",
        features_of_interest=["radiopaque marker"],
    )


def test_failed_attempt_keeps_elapsed_resources_and_marks_unknown_fields(monkeypatch):
    wall_ticks = iter([10.0, 10.25])
    cpu_ticks = iter([20.0, 20.125])
    monkeypatch.setattr(MODULE, "perf_counter", lambda: next(wall_ticks))
    monkeypatch.setattr(MODULE, "process_time", lambda: next(cpu_ticks))
    attempts: list[dict] = []

    assert MODULE._run_control_attempt(attempts, 1, "query", lambda: (_ for _ in ()).throw(RuntimeError("boom"))) is None

    attempt = attempts[0]
    assert attempt["status"] == "failed"
    assert attempt["resources"]["query_calls"] == 1
    assert attempt["resources"]["wall_seconds"] == 0.25
    assert attempt["resources"]["cpu_seconds"] == 0.125
    assert attempt["resource_accounting"] == {
        "status": "PARTIAL_UNKNOWN",
        "unknown_fields": [
            "embedding_query_tokens",
            "rerank_pairs",
            "rerank_tokens",
            "returned_candidates",
        ],
    }


def test_unexpected_method_failure_preserves_partial_attempt_history():
    attempts = [{
        "attempt_id": 1,
        "query": "query",
        "status": "completed",
        "resources": {"query_calls": 1, "wall_seconds": 2.0, "cpu_seconds": 1.0},
    }]
    state = {
        "attempts": attempts,
        "method_started": MODULE.perf_counter() - 0.01,
        "method_cpu_started": MODULE.process_time(),
        "scheduled_queries": ["query", "query-2"],
    }

    result = MODULE._failed_method_result(_device(), "HT-B2", state, RuntimeError("late failure"))

    assert result["attempts"] is attempts
    assert result["resources"]["attempt_count"] == 1
    assert result["resources"]["query_calls"] == 1
    assert result["resources"]["method_wall_seconds"] > 0
    assert result["resources"]["method_cpu_seconds"] >= 0
    assert result["prefix_diagnostics"]["realized_attempt_count"] == 1
    assert result["method_error"]["error_type"] == "RuntimeError"


def test_run_method_failure_does_not_append_synthetic_attempt():
    result = MODULE._run_method(
        _device(),
        [],
        method="unsupported-method",
        lexical=None,
        retriever=None,
        candidate_depth=1,
        rerank_depth=1,
    )

    assert result["status"] == "failed"
    assert result["attempts"] == []
    assert result["resources"]["attempt_count"] == 0
    assert result["resources"]["method_wall_seconds"] >= 0
    assert result["method_error"]["error_type"] == "ValueError"
