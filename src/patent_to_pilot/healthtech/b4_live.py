"""Structured HT-B4 controller selection over the versioned R1 provider seam."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from decimal import Decimal, ROUND_CEILING
import hashlib
import json
import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from patent_to_pilot.healthtech.controller import (
    CONTROLLER_RESPONSE_SCHEMA,
    ControllerAction,
    ControllerObservation,
    validate_controller_action,
)
from patent_to_pilot.healthtech.provider_transfer import (
    ProviderTransferManifest,
    ProviderVisibleSource,
    validate_provider_transfer,
)
from patent_to_pilot.providers.openrouter import (
    ProviderCapabilities,
    ProviderConfig,
    ProviderRequest,
    ProviderResponse,
)
from patent_to_pilot.providers.round1 import (
    Round1ProjectBudget,
    Round1Runner,
    build_round1_config,
)


class B4Pricing(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    model: str = Field(min_length=1)
    upstream_provider: str = Field(min_length=1)
    snapshot_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    snapshot_utc: str = Field(min_length=1)
    prompt_usd_per_million: Decimal = Field(gt=0)
    completion_usd_per_million: Decimal = Field(gt=0)
    max_price_prompt: float = Field(gt=0)
    max_price_completion: float = Field(gt=0)
    unsupported_billable_components: list[str] = Field(default_factory=list)


def _canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def build_b4_prompt(observation: ControllerObservation) -> str:
    """Serialize only structured observations and the fixed action contract."""
    envelope = {
        "schema_version": "ht-b4-controller-v1",
        "task": "Select exactly one bounded retrieval action from the allowed enum.",
        "observation": observation.model_dump(mode="json"),
        "allowed_actions": CONTROLLER_RESPONSE_SCHEMA,
        "constraints": [
            "Return JSON only.",
            "Do not emit URLs, source text, patent text, evaluator fields, or tools.",
            "Stop when the observation requires stopping.",
        ],
    }
    return _canonical(envelope)


def conservative_request_bound_usd(
    *,
    input_tokens: int,
    output_tokens: int,
    pricing: B4Pricing,
    margin_bps: int = 1500,
) -> float:
    """Return a nanodollar-ceiling bound for text-only structured output."""
    if input_tokens < 1 or output_tokens < 1 or margin_bps < 0:
        raise ValueError("token bounds and margin must be positive")
    if pricing.unsupported_billable_components:
        raise ValueError("unsupported billable components prevent a verified bound")
    base = (
        Decimal(input_tokens) * pricing.prompt_usd_per_million / Decimal(1_000_000)
        + Decimal(output_tokens) * pricing.completion_usd_per_million / Decimal(1_000_000)
    )
    gross = base * (Decimal(10_000 + margin_bps) / Decimal(10_000))
    return float(gross.quantize(Decimal("0.000000001"), rounding=ROUND_CEILING))


def _safe_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_") or "item"
    return token[:48]


def _response_receipt(
    *,
    attempt_id: str,
    prompt: str,
    request: ProviderRequest,
    response: ProviderResponse,
    action: ControllerAction | None,
) -> dict[str, Any]:
    return {
        "attempt_id": attempt_id,
        "request_id": request.request_id,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        "input_token_bound": request.input_tokens_estimate,
        "schema_framing_token_bound": request.schema_framing_tokens,
        "output_token_bound": request.max_output_tokens,
        "cost_upper_bound_usd": request.cost_upper_bound_usd,
        "response_sha256": hashlib.sha256(response.text.encode("utf-8")).hexdigest(),
        "reported_model": response.reported_model,
        "reported_upstream_provider": response.reported_upstream_provider,
        "usage": response.usage,
        "cost_usd": response.cost_usd,
        "actual_debit_usd": response.actual_debit_usd,
        "latency_seconds": response.latency_seconds,
        "response_schema_valid": response.response_schema_valid,
        "action": None if action is None else action.model_dump(mode="json"),
    }


class B4ProviderSelector:
    """Select bounded controller actions with a shared R1 budget."""

    def __init__(
        self,
        *,
        budget: Round1ProjectBudget,
        policy: Mapping[str, Any],
        pricing: B4Pricing,
        run_id: str,
        query_id: str,
        phase: str,
        transport_factory: Callable[[], Any],
        live_enabled: bool,
        visible_sources: list[ProviderVisibleSource],
        transfer_manifest: ProviderTransferManifest | None,
        max_output_tokens: int = 256,
    ) -> None:
        if pricing.model not in policy.get("models", {}):
            raise ValueError("pricing model is not bound to the R1 policy")
        if policy.get("models", {}).get(pricing.model) != pricing.upstream_provider:
            raise ValueError("pricing upstream provider is not bound to the R1 policy")
        if policy.get("pricing_snapshot_sha256") != pricing.snapshot_sha256 or policy.get("pricing_snapshot_utc") != pricing.snapshot_utc:
            raise ValueError("pricing snapshot is not bound to the R1 policy")
        self.run_id = run_id
        self.query_id = query_id
        self.phase = phase
        self.pricing = pricing
        self.visible_sources = list(visible_sources)
        self.transfer_summary = validate_provider_transfer(self.visible_sources, transfer_manifest) if live_enabled else []
        self.data_class = "synthetic" if self.visible_sources and all(item.synthetic for item in self.visible_sources) else "public"
        max_input_tokens = 6144
        schema_bound = len(_canonical(CONTROLLER_RESPONSE_SCHEMA).encode("utf-8"))
        self.config: ProviderConfig = build_round1_config(
            policy,
            phase=phase,
            model=pricing.model,
            max_price={"prompt": pricing.max_price_prompt, "completion": pricing.max_price_completion},
            live_enabled=live_enabled,
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
            max_total_tokens=max_input_tokens + max_output_tokens + schema_bound,
            prompt_version="ptp-ht-b4-r1-controller-v1",
        )
        self.capabilities = ProviderCapabilities(
            provider="openrouter",
            model=pricing.model,
            structured_outputs=True,
            tools=False,
            parameter_names=set(),
            exact_model_pin=True,
            auto_routing=False,
        )
        self.runner = Round1Runner(budget, transport_factory)
        self._last_receipt: dict[str, Any] | None = None
        self.receipts: list[dict[str, Any]] = []
        self._schema_bound = schema_bound

    def select(self, observation: ControllerObservation) -> ControllerAction:
        prompt = build_b4_prompt(observation)
        input_bound = len(prompt.encode("utf-8"))
        if input_bound + self._schema_bound > self.config.max_input_tokens:
            raise ValueError("structured controller prompt exceeds the configured input bound")
        output_bound = self.config.max_output_tokens
        upper_bound = conservative_request_bound_usd(
            input_tokens=input_bound + self._schema_bound,
            output_tokens=output_bound,
            pricing=self.pricing,
        )
        attempt_id = f"{_safe_token(self.run_id)}-{_safe_token(self.query_id)}-s{observation.step_index}"
        request = ProviderRequest(
            prompt=prompt,
            response_schema=CONTROLLER_RESPONSE_SCHEMA,
            input_tokens_estimate=input_bound,
            schema_framing_tokens=self._schema_bound,
            max_output_tokens=output_bound,
            cost_upper_bound_usd=upper_bound,
            request_id=attempt_id,
        )
        try:
            response = self.runner.complete(
                attempt_id=attempt_id,
                phase=self.phase,
                config=self.config,
                request=request,
                capabilities=self.capabilities,
                upper_bound_usd=upper_bound,
                data_class=self.data_class,
            )
            payload = json.loads(response.text)
            action = validate_controller_action(payload, observation)
            self._last_receipt = _response_receipt(
                attempt_id=attempt_id, prompt=prompt, request=request, response=response, action=action
            )
            self._last_receipt["status"] = "SUCCESS"
            self._last_receipt["transfer_summary"] = self.transfer_summary
            self.receipts.append(self._last_receipt)
            return action
        except Exception as exc:
            self._last_receipt = {
                "attempt_id": attempt_id,
                "request_id": attempt_id,
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "input_token_bound": input_bound,
                "schema_framing_token_bound": self._schema_bound,
                "output_token_bound": output_bound,
                "cost_upper_bound_usd": upper_bound,
                "status": "FAILED",
                "error_class": type(exc).__name__,
            }
            self._last_receipt["transfer_summary"] = self.transfer_summary
            self.receipts.append(self._last_receipt)
            raise

    def take_last_receipt(self) -> dict[str, Any] | None:
        receipt = self._last_receipt
        self._last_receipt = None
        return receipt
