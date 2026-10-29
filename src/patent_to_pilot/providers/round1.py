"""Versioned HealthTech OpenRouter R1 policy and runner seam.

This module owns the new USD 8 round policy without mutating the historical
USD 5 policy or its journals. It reuses the existing adapter, HTTP transport,
and durable SQLite reservation boundary; it never reads credentials itself.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
import hashlib
import json
from pathlib import Path
from typing import Any

from .openrouter import (
    AttemptLedger,
    BudgetExceededError,
    OpenRouterAdapter,
    OpenRouterHTTPTransport,
    ProviderCapabilities,
    ProviderConfig,
    ProviderRequest,
    ProviderResponse,
)
from .project_budget import BudgetedTransport, NANO, ProjectBudget


R1_POLICY_VERSION = "ptp-ht-openrouter-r1-20261028-usd8-v1"
R1_AUTHORIZATION_ID = "PTP-HT-OR-R1-20261028-USD8"
R1_TOTAL_CAP_NANO_USD = 8_000_000_000
R1_ADMISSION_THRESHOLD_NANO_USD = 7_000_000_000
R1_PHASE_CAPS_NANO_USD = {
    "canary": 400_000_000,
    "paired_pilot": 5_400_000_000,
    "robustness": 1_200_000_000,
}


def _sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _require_sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        raise ValueError(f"{label} must be a lowercase SHA-256 hex digest")
    return value


def build_round1_policy(
    model_provider_map: Mapping[str, str],
    *,
    pricing_snapshot_sha256: str,
    pricing_snapshot_utc: str,
) -> dict[str, Any]:
    """Build an immutable admission policy from a verified current snapshot.

    The caller must provide the exact current model/provider map and a hash of
    the official pricing/availability snapshot. No historical model alias is
    treated as current by this helper.
    """
    if not isinstance(model_provider_map, Mapping) or not model_provider_map:
        raise ValueError("a non-empty exact model/provider map is required")
    models = {}
    for model, provider in sorted(model_provider_map.items()):
        if not isinstance(model, str) or not model or not isinstance(provider, str) or not provider:
            raise ValueError("model/provider map entries must be non-empty strings")
        models[model] = provider
    pricing_snapshot_sha256 = _require_sha256(pricing_snapshot_sha256, "pricing snapshot")
    if not isinstance(pricing_snapshot_utc, str) or not pricing_snapshot_utc.strip():
        raise ValueError("pricing snapshot timestamp is required")
    if sum(R1_PHASE_CAPS_NANO_USD.values()) != R1_ADMISSION_THRESHOLD_NANO_USD:
        raise ValueError("R1 phase caps must sum to the admission threshold")
    return {
        "version": R1_POLICY_VERSION,
        "authorization_id": R1_AUTHORIZATION_ID,
        "incremental_cap_nano_usd": R1_TOTAL_CAP_NANO_USD,
        "admission_threshold_nano_usd": R1_ADMISSION_THRESHOLD_NANO_USD,
        "phase_caps_nano_usd": dict(R1_PHASE_CAPS_NANO_USD),
        "models": models,
        "provider": "openrouter",
        "endpoint": "https://openrouter.ai/api/v1/chat/completions",
        "allow_fallbacks": False,
        "require_parameters": True,
        "max_concurrency": 1,
        "retries": 0,
        "unknown_billing": "block",
        "private_data": False,
        "pricing_snapshot_sha256": pricing_snapshot_sha256,
        "pricing_snapshot_utc": pricing_snapshot_utc,
    }


def round1_policy_hash(policy: Mapping[str, Any]) -> str:
    return _sha256(policy)


def build_round1_config(
    policy: Mapping[str, Any],
    *,
    phase: str,
    model: str,
    max_price: Mapping[str, float],
    live_enabled: bool = False,
    max_input_tokens: int = 6144,
    max_output_tokens: int = 512,
    max_total_tokens: int = 6656,
    prompt_version: str = "ptp-ht-b4-r1-v1",
) -> ProviderConfig:
    """Create an exact-route config bound to one R1 phase and model."""
    models = policy.get("models")
    if not isinstance(models, Mapping) or models.get(model) is None:
        raise ValueError("model is not present in the verified R1 policy")
    if phase not in policy.get("phase_caps_nano_usd", {}):
        raise ValueError("phase is not present in the verified R1 policy")
    if not isinstance(max_price, Mapping) or not max_price:
        raise ValueError("current provider price guard is required")
    phase_cap = int(policy["phase_caps_nano_usd"][phase]) / float(NANO)
    return ProviderConfig(
        provider="openrouter",
        model=model,
        routing_only=[models[model]],
        allow_fallbacks=False,
        require_parameters=True,
        max_price=dict(max_price),
        live_enabled=live_enabled,
        research_mode=True,
        allow_auto_routing=False,
        max_input_tokens=max_input_tokens,
        max_output_tokens=max_output_tokens,
        max_total_tokens=max_total_tokens,
        max_spend_usd=phase_cap,
        retries=0,
        prompt_version=prompt_version,
        config_version=round1_policy_hash(policy),
    )


class Round1ProjectBudget(ProjectBudget):
    """Durable R1 budget; opening an older policy DB fails closed."""

    def __init__(
        self,
        path: Path,
        *,
        model_provider_map: Mapping[str, str],
        pricing_snapshot_sha256: str,
        pricing_snapshot_utc: str,
    ) -> None:
        policy = build_round1_policy(
            model_provider_map,
            pricing_snapshot_sha256=pricing_snapshot_sha256,
            pricing_snapshot_utc=pricing_snapshot_utc,
        )
        super().__init__(path, policy=policy)


def request_payload_hash(config: ProviderConfig, request: ProviderRequest) -> str:
    payload = OpenRouterHTTPTransport._request_payload(config, request)
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()


class Round1Runner:
    """One explicit R1 request through the shared adapter/ledger seam."""

    def __init__(self, budget: Round1ProjectBudget, transport_factory: Callable[[], Any]) -> None:
        self.budget = budget
        self.transport_factory = transport_factory

    def complete(
        self,
        *,
        attempt_id: str,
        phase: str,
        config: ProviderConfig,
        request: ProviderRequest,
        capabilities: ProviderCapabilities,
        upper_bound_usd: float,
        data_class: str,
        bound_verified: bool = True,
    ) -> ProviderResponse:
        expected_provider = self.budget.models.get(config.model)
        if (
            config.provider != "openrouter"
            or config.retries != 0
            or config.routing_only != [expected_provider]
            or config.allow_fallbacks
            or not config.require_parameters
            or config.config_version != round1_policy_hash(self.budget.policy)
        ):
            raise BudgetExceededError("R1 config is not bound to the verified policy")
        if request.cost_upper_bound_usd is None:
            raise BudgetExceededError("R1 requires an explicit conservative request bound")
        binding = {
            "attempt_id": attempt_id,
            "phase": phase,
            "payload_sha256": request_payload_hash(config, request),
            "upper_bound_usd": upper_bound_usd,
            "bound_verified": bound_verified,
            "data_class": data_class,
        }
        wrapped = BudgetedTransport(self.transport_factory(), self.budget, binding)
        adapter = OpenRouterAdapter(config, wrapped, capabilities, AttemptLedger())
        return adapter.complete(request)
