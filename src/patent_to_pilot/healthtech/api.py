"""Fail-closed HealthTech request seam for dry-run and mock-only pre-live work."""
from __future__ import annotations

import json
from typing import Any, Literal

from jsonschema import Draft202012Validator, SchemaError
from pydantic import BaseModel, ConfigDict, Field, model_validator

from patent_to_pilot.healthtech.contracts import content_hash
from patent_to_pilot.providers import (
    AttemptLedger,
    LiveCallsDisabledError,
    MockHTTPTransport,
    OpenRouterAdapter,
    ProviderCapabilities,
    ProviderConfig,
    ProviderRequest,
)


class HealthTechVisibleSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_id: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    visibility: Literal["runtime"] = "runtime"

    @model_validator(mode="after")
    def reject_evaluator_names(self):
        lowered = self.source_id.lower()
        if "evaluator" in lowered or "gold" in lowered:
            raise ValueError("evaluator/gold sources are not visible to HealthTech requests")
        return self


class HealthTechAPIConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    mode: Literal["dry_run", "mock", "live"] = "dry_run"
    provider: Literal["openrouter"] = "openrouter"
    model: str = Field(default="healthtech-not-used", min_length=1)
    max_input_tokens: int = Field(default=2048, ge=1)
    max_output_tokens: int = Field(default=256, ge=1)
    max_total_tokens: int = Field(default=2304, ge=1)
    max_spend_usd: float = Field(default=0.0, ge=0)
    allow_evaluator_sources: Literal[False] = False

    @model_validator(mode="after")
    def bounds(self):
        if self.max_total_tokens < self.max_input_tokens + self.max_output_tokens:
            raise ValueError("max_total_tokens must cover input and output bounds")
        if self.mode == "live":
            raise ValueError("HealthTech live mode is disabled in the pre-live package")
        return self


class HealthTechRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    request_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    query_id: str = Field(min_length=1)
    action_type: Literal["bounded_controller", "evidence_summary", "source_selection"]
    prompt: str = Field(min_length=1)
    response_schema: dict[str, Any]
    visible_sources: list[HealthTechVisibleSource] = Field(min_length=1)
    estimated_input_tokens: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_request(self):
        ids = [source.source_id for source in self.visible_sources]
        if len(ids) != len(set(ids)):
            raise ValueError("visible source IDs must be unique")
        try:
            Draft202012Validator.check_schema(self.response_schema)
        except SchemaError as exc:
            raise ValueError("response_schema is not valid JSON Schema") from exc
        return self


class HealthTechDispatchReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    status: Literal["DRY_RUN_NOT_EXECUTED", "MOCK_COMPLETE"]
    mode: Literal["dry_run", "mock"]
    request_id: str
    request_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    visible_source_ids: list[str]
    visible_source_hashes: dict[str, str]
    network_attempts: int = Field(ge=0)
    provider_calls: int = Field(ge=0)
    paid_cost_usd: float = Field(default=0.0, ge=0)
    response_schema_valid: bool | None = None
    response: dict[str, Any] | None = None


def _request_hash(request: HealthTechRequest) -> str:
    return content_hash(request.model_dump(mode="json"))


def dispatch_healthtech_request(
    config: HealthTechAPIConfig,
    request: HealthTechRequest,
    *,
    transport: MockHTTPTransport | None = None,
) -> HealthTechDispatchReceipt:
    """Validate visibility/config and execute only dry-run or injected mock paths."""
    if request.estimated_input_tokens > config.max_input_tokens:
        raise ValueError("request input estimate exceeds configured bound")
    if len(request.prompt.encode("utf-8")) > config.max_input_tokens * 4:
        raise ValueError("request prompt exceeds configured byte bound")
    request_hash = _request_hash(request)
    visible_ids = [source.source_id for source in request.visible_sources]
    visible_hashes = {source.source_id: source.payload_hash for source in request.visible_sources}
    if config.mode == "dry_run":
        return HealthTechDispatchReceipt(
            status="DRY_RUN_NOT_EXECUTED", mode="dry_run", request_id=request.request_id,
            request_hash=request_hash, visible_source_ids=visible_ids,
            visible_source_hashes=visible_hashes, network_attempts=0,
            provider_calls=0, paid_cost_usd=0.0,
        )
    if config.mode == "live":  # defensive branch; config validation already rejects it
        raise LiveCallsDisabledError("HealthTech live provider calls are disabled")
    if transport is None or not getattr(transport, "is_mock", False):
        raise LiveCallsDisabledError("mock mode requires an injected fake transport")
    provider_config = ProviderConfig(
        provider=config.provider, model=config.model, live_enabled=False,
        research_mode=True, max_input_tokens=config.max_input_tokens,
        max_output_tokens=config.max_output_tokens, max_total_tokens=config.max_total_tokens,
        max_spend_usd=config.max_spend_usd, retries=0,
    )
    capabilities = ProviderCapabilities(
        provider=config.provider, model=config.model, structured_outputs=True,
        tools=False, parameter_names=set(), exact_model_pin=True, auto_routing=False,
    )
    adapter = OpenRouterAdapter(provider_config, transport, capabilities, AttemptLedger())
    response = adapter.complete(ProviderRequest(
        prompt=request.prompt, response_schema=request.response_schema,
        input_tokens_estimate=request.estimated_input_tokens,
        max_output_tokens=config.max_output_tokens, estimated_cost_usd=0.0,
        cost_upper_bound_usd=0.0, request_id=request.request_id,
    ))
    try:
        response_payload = json.loads(response.text)
    except json.JSONDecodeError:
        response_payload = {"text": response.text}
    if not isinstance(response_payload, dict):
        response_payload = {"value": response_payload}
    return HealthTechDispatchReceipt(
        status="MOCK_COMPLETE", mode="mock", request_id=request.request_id,
        request_hash=request_hash, visible_source_ids=visible_ids,
        visible_source_hashes=visible_hashes, network_attempts=0,
        provider_calls=len(response.attempts), paid_cost_usd=0.0,
        response_schema_valid=response.response_schema_valid, response=response_payload,
    )
