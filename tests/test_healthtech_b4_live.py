from __future__ import annotations

import json

import pytest

from patent_to_pilot.healthtech.b4_live import (
    B4Pricing,
    B4ProviderSelector,
    build_b4_prompt,
    conservative_request_bound_usd,
)
from patent_to_pilot.healthtech.controller import ControllerObservation, deterministic_controller_action
from patent_to_pilot.healthtech.provider_transfer import (
    ProviderTransferBinding,
    ProviderTransferError,
    ProviderTransferManifest,
    ProviderVisibleSource,
    validate_provider_transfer,
)
from patent_to_pilot.providers import MockHTTPResponse, MockHTTPTransport
from patent_to_pilot.providers.round1 import Round1ProjectBudget, build_round1_policy


MODEL = "openai/gpt-4.1-mini"
UPSTREAM = "openai"
PRICE_HASH = "a" * 64
PRICE_TIME = "2026-10-29T00:00:00Z"


def observation(**overrides):
    data = {
        "query_id": "q1",
        "step_index": 0,
        "max_steps": 2,
        "remaining_query_calls": 2,
        "remaining_candidate_budget": 20,
        "source_available": True,
        "available_feature_indices": [1],
        "used_feature_indices": [],
        "last_new_candidate_count": 0,
        "last_disagreement": 0.0,
        "last_action": None,
    }
    data.update(overrides)
    return ControllerObservation(**data)


def pricing():
    return B4Pricing(
        model=MODEL,
        upstream_provider=UPSTREAM,
        snapshot_sha256=PRICE_HASH,
        snapshot_utc=PRICE_TIME,
        prompt_usd_per_million="0.4",
        completion_usd_per_million="1.6",
        max_price_prompt=0.4,
        max_price_completion=1.6,
    )


def policy():
    return build_round1_policy(
        {MODEL: UPSTREAM},
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
    )


def test_prompt_contains_only_structured_observation_and_schema():
    prompt = build_b4_prompt(observation())
    payload = json.loads(prompt)
    assert payload["observation"]["query_id"] == "q1"
    assert "SECRET-CLAIM-TEXT" not in prompt
    assert "response_schema" not in payload["observation"]


def test_conservative_bound_rejects_unknown_billable_components():
    with pytest.raises(ValueError, match="unsupported billable"):
        conservative_request_bound_usd(
            input_tokens=100,
            output_tokens=20,
            pricing=pricing().model_copy(update={"unsupported_billable_components": ["web_search"]}),
        )


def test_provider_transfer_is_fail_closed_and_exact():
    source = ProviderVisibleSource(
        source_id="synthetic-source",
        source_revision="v1",
        source_sha256="b" * 64,
        source_type="synthetic",
        synthetic=False,
    )
    with pytest.raises(ProviderTransferError, match="no transfer manifest"):
        validate_provider_transfer([source], None)
    manifest = ProviderTransferManifest(
        run_id="test-run",
        sources=[ProviderTransferBinding(
            source_id=source.source_id,
            source_revision=source.source_revision,
            source_sha256=source.source_sha256,
            decision="BLOCKED_LOCAL",
            basis_url="https://example.invalid/terms",
            basis_locator="terms",
            note="test blocked source",
        )],
    )
    with pytest.raises(ProviderTransferError, match="BLOCKED_LOCAL"):
        validate_provider_transfer([source], manifest)


def test_mock_selector_binds_schema_action_and_durable_r1_budget(tmp_path):
    budget = Round1ProjectBudget(
        tmp_path / "round1.sqlite3",
        model_provider_map={MODEL: UPSTREAM},
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
    )

    def transport_factory():
        action = deterministic_controller_action(observation())
        return MockHTTPTransport(MockHTTPResponse(200, {
            "model": MODEL,
            "provider": "OpenAI",
            "choices": [{"message": {"content": action.model_dump_json()}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120, "cost": 0.0001},
        }))

    selector = B4ProviderSelector(
        budget=budget,
        policy=policy(),
        pricing=pricing(),
        run_id="test-run",
        query_id="q1",
        phase="canary",
        transport_factory=transport_factory,
        live_enabled=False,
        visible_sources=[],
        transfer_manifest=None,
        max_output_tokens=64,
    )
    action = selector.select(observation())
    receipt = selector.take_last_receipt()
    assert action.action_type == "technical_search"
    assert receipt["status"] == "SUCCESS"
    assert receipt["response_schema_valid"] is True
    assert budget.snapshot()["actual_nano_usd"] == 100_000


def test_live_selector_requires_transfer_manifest_before_transport(tmp_path):
    budget = Round1ProjectBudget(
        tmp_path / "round1.sqlite3",
        model_provider_map={MODEL: UPSTREAM},
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
    )
    source = ProviderVisibleSource(
        source_id="public-source",
        source_revision="v1",
        source_sha256="c" * 64,
        source_type="regulatory_record",
    )
    with pytest.raises(ProviderTransferError, match="no transfer manifest"):
        B4ProviderSelector(
            budget=budget,
            policy=policy(),
            pricing=pricing(),
            run_id="test-run",
            query_id="q1",
            phase="canary",
            transport_factory=lambda: MockHTTPTransport(MockHTTPResponse(200, {})),
            live_enabled=True,
            visible_sources=[source],
            transfer_manifest=None,
        )
