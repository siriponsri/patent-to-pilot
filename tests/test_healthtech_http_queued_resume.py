"""Regression for stale executor callbacks after queued cancellation/resume."""
import json
from pathlib import Path
from threading import Event

from patent_to_pilot.healthtech.engine import run_dossier
from patent_to_pilot.healthtech.http import HealthTechJobService

ROOT = Path(__file__).resolve().parents[1]


def test_cancel_queued_then_resume_executes_once(tmp_path):
    """Hold the worker so both original and resumed callbacks are queued."""
    release = Event()
    entered = Event()
    calls = []

    def occupy_worker():
        entered.set()
        assert release.wait(10)

    def runner(*args, **kwargs):
        calls.append(kwargs["run_id"])
        return run_dossier(*args, **kwargs)

    service = HealthTechJobService(tmp_path / "jobs", runner=runner, code_commit="fixture")
    try:
        service.executor.submit(occupy_worker)
        assert entered.wait(5)
        data = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))
        job = service.submit({"input": data, "idempotency_key": "queued-cancel-resume"})
        assert service.cancel(job["job_id"])["state"] == "cancelled"
        assert service.resume(job["job_id"])["state"] == "queued"
        release.set()
        service.executor.submit(lambda: None).result(timeout=10)
        current = service.status(job["job_id"])
        assert len(calls) == 1
        assert current["state"] == "succeeded"
        assert current["attempt"] == 1
        assert len(service.history(job["job_id"])["history"]["versions"]) == 1
    finally:
        release.set()
        service.close()
