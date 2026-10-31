from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

from patent_to_pilot.healthtech.api_generation import OpenRouterQwenGenerationRunner
from patent_to_pilot.healthtech.b4_live import B4Pricing
from patent_to_pilot.providers import BudgetExceededError, MockHTTPResponse
from patent_to_pilot.providers.round1 import Round1ProjectBudget


def _load_fixture_builder():
    path = Path(__file__).with_name("test_healthtech_generation_payload.py")
    spec = importlib.util.spec_from_file_location("generation_payload_fixture", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_api_script():
    path = Path(__file__).resolve().parents[1] / "scripts" / "healthtech" / "run_openrouter_generation_evidence_pack.py"
    spec = importlib.util.spec_from_file_location("api_generation_cli", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MockGenerationTransport:
    is_mock = True

    def send(self, *, config, request):
        messages = request.messages or [{"role": "user", "content": request.prompt}]
        payload = json.loads(messages[-1]["content"])
        case = payload["case"]
        output = {
            "device_id": case["query"]["device_id_canonical"],
            "device_name": case["query"]["device_id_raw"],
            "findings": [],
            "unresolved": ["mock"],
        }
        return MockHTTPResponse(200, {
            "model": config.model,
            "provider": config.routing_only[0],
            "choices": [{"message": {"content": json.dumps(output)}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 10, "total_tokens": 110, "cost": 0.0},
        })


def test_api_runner_uses_exact_messages_and_mock_namespace_without_paid_dispatch(tmp_path):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    pricing = B4Pricing(
        model="qwen/qwen3-32b",
        upstream_provider="DeepInfra",
        snapshot_sha256="a" * 64,
        snapshot_utc="2026-10-31T00:00:00Z",
        prompt_usd_per_million="0.08",
        completion_usd_per_million="0.28",
        max_price_prompt=0.08,
        max_price_completion=0.28,
    )
    budget = Round1ProjectBudget(
        tmp_path / "mock-ledger.sqlite3",
        model_provider_map={pricing.model: pricing.upstream_provider},
        pricing_snapshot_sha256=pricing.snapshot_sha256,
        pricing_snapshot_utc=pricing.snapshot_utc,
        namespace="mock",
    )
    try:
        runner = OpenRouterQwenGenerationRunner(
            budget=budget,
            pricing=pricing,
            transport_factory=lambda: MockGenerationTransport(),
            live_enabled=False,
            run_id="api-generation-test",
            max_output_tokens=64,
            max_findings=6,
        )
        result = runner.run(pack)
        assert result["status"] == "PASS_API_QWEN3_32B_FROZEN_PACK_GENERATION"
        assert result["provider_calls"] == 3
        assert result["paid_cost_usd"] == 0.0
        assert all(case["schema_valid"] is True for case in result["cases"])
        safe = runner.sanitized_receipt(result)
        assert all("parsed_output" not in case for case in safe["cases"])
        assert budget.snapshot()["ledger_namespace"] == "mock"
    finally:
        budget.close()

def test_api_generation_cli_dry_run_writes_sanitized_manifest(tmp_path, monkeypatch):
    pack = _load_fixture_builder()._synthetic_pack(tmp_path)
    pack_path = tmp_path / "pack.json"
    pack_path.write_text(json.dumps(pack), encoding="utf-8")
    pricing = B4Pricing(
        model="qwen/qwen3-32b",
        upstream_provider="DeepInfra",
        snapshot_sha256="a" * 64,
        snapshot_utc="2026-10-31T00:00:00Z",
        prompt_usd_per_million="0.08",
        completion_usd_per_million="0.28",
        max_price_prompt=0.08,
        max_price_completion=0.28,
    )
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps(pricing.model_dump(mode="json")), encoding="utf-8")
    output = tmp_path / "dry-run.json"
    monkeypatch.setattr(sys, "argv", [
        "run_openrouter_generation_evidence_pack.py",
        "--pack", str(pack_path),
        "--model-snapshot", str(snapshot_path),
        "--output", str(output),
        "--run-id", "dry-run-test",
        "--mode", "dry-run",
    ])
    assert _load_api_script().main() == 0
    receipt = json.loads(output.read_text(encoding="utf-8"))
    assert receipt["status"] == "DRY_RUN_NOT_EXECUTED"
    assert all("messages" not in case for case in receipt["manifest"]["cases"])


def test_live_api_runner_rejects_mock_namespace_before_dispatch(tmp_path):
    pricing = B4Pricing(
        model="qwen/qwen3-32b",
        upstream_provider="DeepInfra",
        snapshot_sha256="a" * 64,
        snapshot_utc="2026-10-31T00:00:00Z",
        prompt_usd_per_million="0.08",
        completion_usd_per_million="0.28",
        max_price_prompt=0.08,
        max_price_completion=0.28,
    )
    budget = Round1ProjectBudget(
        tmp_path / "mock-ledger.sqlite3",
        model_provider_map={pricing.model: pricing.upstream_provider},
        pricing_snapshot_sha256=pricing.snapshot_sha256,
        pricing_snapshot_utc=pricing.snapshot_utc,
        namespace="mock",
    )
    try:
        with pytest.raises(BudgetExceededError, match="canonical authorization ledger"):
            OpenRouterQwenGenerationRunner(
                budget=budget,
                pricing=pricing,
                transport_factory=lambda: (_ for _ in ()).throw(AssertionError("transport must not run")),
                live_enabled=True,
                run_id="live-gate-test",
            )
    finally:
        budget.close()
