"""A small provider-neutral request seam with a mockable OpenRouter transport.

The adapter follows the OpenRouter chat-completions shape but never creates a
credential or performs a live call unless the caller explicitly enables it.
Native adapters for other vendors are intentionally future registry entries,
not claims of compatibility.
"""

from __future__ import annotations

import json
import hashlib
import math
import os
import socket
import time
import builtins
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from jsonschema import Draft202012Validator, SchemaError, ValidationError
from pydantic import BaseModel, ConfigDict, Field


class AdapterError(RuntimeError):
    """Base error for explicit adapter failures."""


class LiveCallsDisabledError(AdapterError):
    pass


class CapabilityError(AdapterError):
    pass


class ResponseValidationError(AdapterError):
    pass


class BudgetExceededError(AdapterError):
    pass


class RateLimitError(AdapterError):
    pass


class TimeoutError(AdapterError):
    pass


class ModelDriftError(AdapterError):
    pass


class HTTPTransportError(AdapterError):
    pass


class ProviderCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    structured_outputs: bool = False
    tools: bool = False
    parameter_names: set[str] = Field(default_factory=set)
    exact_model_pin: bool = True
    auto_routing: bool = False


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str = "openrouter"
    model: str = Field(min_length=1)
    base_url: str = "https://openrouter.ai/api/v1"
    endpoint_path: str = "/chat/completions"
    routing_only: list[str] = Field(default_factory=list)
    allow_fallbacks: bool = False
    require_parameters: bool = True
    max_price: dict[str, float] = Field(default_factory=dict)
    api_key_env: str = "OPENROUTER_API_KEY"
    live_enabled: bool = False
    research_mode: bool = True
    allow_auto_routing: bool = False
    timeout_seconds: float = Field(default=30.0, gt=0)
    max_input_tokens: int = Field(default=4000, ge=1)
    max_output_tokens: int = Field(default=1500, ge=1)
    max_total_tokens: int = Field(default=5500, ge=1)
    max_spend_usd: float = Field(default=0.0, ge=0)
    retries: int = Field(default=0, ge=0)
    prompt_version: str = "unversioned"
    config_version: str = "g11-provider-config-1"


class ProviderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1)
    # When present, this exact message list is sent to the provider. The
    # legacy single-prompt path remains available for existing controllers.
    messages: list[dict[str, str]] | None = None
    response_schema: dict[str, Any] | None = None
    tools: list[dict[str, Any]] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    input_tokens_estimate: int | None = Field(default=None, ge=0)
    schema_framing_tokens: int = Field(default=0, ge=0)
    max_output_tokens: int | None = Field(default=None, ge=1)
    estimated_cost_usd: float | None = Field(default=None, ge=0)
    cost_upper_bound_usd: float | None = Field(default=None, ge=0)
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex}")


class ProviderAttempt(BaseModel):
    model_config = ConfigDict(extra="forbid")
    attempt: int = Field(ge=1)
    status: str
    request_id: str
    error: str | None = None
    error_code: str | None = None
    error_class: str | None = None
    latency_seconds: float | None = None
    reservation_id: str | None = None
    reservation_status: str = "unknown"
    reserved_input_tokens: int = 0
    reserved_output_tokens: int = 0
    reserved_total_tokens: int = 0
    reserved_cost_usd: float | None = None
    observed_input_tokens: int | None = None
    observed_output_tokens: int | None = None
    observed_total_tokens: int | None = None
    observed_cost_usd: float | None = None
    # requested_provider is the broker; reported_provider is an upstream label.
    # Defaults preserve compatibility with pre-repair attempt records.
    requested_provider: str | None = None
    requested_model: str | None = None
    requested_upstream_providers: list[str] = Field(default_factory=list)
    reported_model: str | None = None
    reported_provider: str | None = None
    reported_upstream_provider: str | None = None
    identity_error: str | None = None


class ProviderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str | None
    model: str | None
    requested_provider: str
    requested_model: str
    reported_provider: str | None = None
    reported_model: str | None = None
    requested_upstream_providers: list[str] = Field(default_factory=list)
    reported_upstream_provider: str | None = None
    model_drift: bool = False
    provider_drift: bool = False
    request_id: str
    text: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    cost_usd: float | None = None
    latency_seconds: float
    retry_count: int = Field(ge=0)
    response_schema_valid: bool | None = None
    actual_debit_usd: float = 0.0
    budget_breach: bool = False
    dispatch_blocked: bool = False
    budget_breach_reasons: list[str] = Field(default_factory=list)
    attempts: list[ProviderAttempt] = Field(default_factory=list)


@dataclass(frozen=True)
class MockHTTPResponse:
    status_code: int
    payload: dict[str, Any] | None = None
    headers: dict[str, str] | None = None


class HTTPTransport(Protocol):
    is_mock: bool

    def send(self, *, config: ProviderConfig, request: ProviderRequest) -> MockHTTPResponse:
        ...

    def preflight(self, *, config: ProviderConfig, request: ProviderRequest) -> None:
        ...


class MockHTTPTransport:
    """Injectable HTTP stand-in; it never opens a socket."""

    is_mock = True

    def __init__(self, response: MockHTTPResponse | Exception | list[MockHTTPResponse | Exception]) -> None:
        self.response = response
        self.calls: list[tuple[ProviderConfig, ProviderRequest]] = []
        self._index = 0

    def send(self, *, config: ProviderConfig, request: ProviderRequest) -> MockHTTPResponse:
        self.calls.append((config, request))
        response = self.response
        if isinstance(response, list):
            if not response:
                raise AdapterError("mock transport response sequence exhausted")
            response = response[min(self._index, len(response) - 1)]
            self._index += 1
        if isinstance(response, Exception):
            raise response
        return response


class OpenRouterHTTPTransport:
    """Single-attempt OpenRouter HTTP transport.

    The adapter/ledger owns retries and budget reservation. This transport does
    not retry, does not log headers, and reads the API key only at dispatch.
    """

    is_mock = False

    def __init__(self, opener: Any | None = None) -> None:
        self._opener = opener or urllib.request.build_opener(_NoRedirect())

    @property
    def opener(self) -> Any:
        return self._opener

    @staticmethod
    def _url(config: ProviderConfig) -> str:
        from urllib.parse import urlsplit
        base = urlsplit(config.base_url)
        if base.scheme != "https" or base.hostname != "openrouter.ai" or base.port is not None or base.username or base.password or base.query or base.fragment or base.path.rstrip("/") != "/api/v1":
            raise CapabilityError("OpenRouter base URL must be the exact HTTPS origin/path https://openrouter.ai/api/v1")
        if config.endpoint_path != "/chat/completions":
            raise CapabilityError("OpenRouter endpoint path must be /chat/completions")
        return "https://openrouter.ai/api/v1/chat/completions"

    def preflight(self, *, config: ProviderConfig, request: ProviderRequest) -> None:
        if not config.live_enabled:
            raise LiveCallsDisabledError("live provider calls are disabled")
        if config.allow_auto_routing or not config.research_mode:
            raise CapabilityError("live pilot requires pinned research mode without automatic routing")
        if not config.base_url.startswith("https://"):
            raise CapabilityError("live OpenRouter endpoint must use HTTPS")
        OpenRouterHTTPTransport._url(config)
        if not config.routing_only:
            raise CapabilityError("live pilot requires an exact provider routing allowlist")
        if config.allow_fallbacks or not config.require_parameters:
            raise CapabilityError("live pilot requires allow_fallbacks=false and require_parameters=true")
        if not config.max_price:
            raise CapabilityError("live pilot requires a max_price guard")
        if not os.environ.get(config.api_key_env):
            raise CapabilityError("live provider key is not available in the configured environment")

    @staticmethod
    def _request_payload(config: ProviderConfig, request: ProviderRequest) -> dict[str, Any]:
        output_limit = request.max_output_tokens or config.max_output_tokens
        payload: dict[str, Any] = {
            "model": config.model,
            "messages": request.messages or [{"role": "user", "content": request.prompt}],
            "stream": False,
            "max_tokens": output_limit,
        }
        if config.routing_only:
            payload["provider"] = {
                "only": config.routing_only,
                "allow_fallbacks": config.allow_fallbacks,
                "require_parameters": config.require_parameters,
                "max_price": config.max_price,
            }
        if request.response_schema is not None:
            payload["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "patent_to_pilot_output", "strict": True, "schema": request.response_schema},
            }
        if request.tools:
            payload["tools"] = request.tools
        payload.update(request.parameters)
        return payload

    @staticmethod
    def _decode_body(raw: bytes) -> dict[str, Any] | None:
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return None
        return decoded if isinstance(decoded, dict) else None

    def send(self, *, config: ProviderConfig, request: ProviderRequest) -> MockHTTPResponse:
        self.preflight(config=config, request=request)
        key = os.environ.get(config.api_key_env)
        # Keep the secret in the request object only; never include it in an
        # exception, return payload, or attempt log.
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        url = self._url(config)
        body = json.dumps(self._request_payload(config, request), separators=(",", ":")).encode("utf-8")
        http_request = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            # urllib has no automatic retry policy here; retries are ledger-owned.
            opened_response = self._opener.open(http_request, timeout=config.timeout_seconds) if hasattr(self._opener, "open") else self._opener(http_request, timeout=config.timeout_seconds)
            response = opened_response
            with response as opened:
                status = int(getattr(opened, "status", getattr(opened, "code", 200)))
                raw = opened.read()
            return MockHTTPResponse(status_code=status, payload=self._decode_body(raw))
        except urllib.error.HTTPError as exc:
            try:
                raw = exc.read()
            except Exception:
                raw = b""
            return MockHTTPResponse(status_code=int(exc.code), payload=self._decode_body(raw))
        except (socket.timeout, builtins.TimeoutError, TimeoutError) as exc:
            raise TimeoutError("HTTP request timed out") from None
        except urllib.error.URLError as exc:
            raise HTTPTransportError("HTTP transport failed") from None
        except OSError as exc:
            raise HTTPTransportError("HTTP transport failed") from None
        except Exception as exc:
            raise HTTPTransportError("HTTP transport failed") from None


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class AttemptLedger:
    """Shared reservation ledger for all attempts dispatched by an adapter."""

    def __init__(self) -> None:
        self.attempts: list[ProviderAttempt] = []
        self._reserved_input = 0
        self._reserved_output = 0
        self._reserved_total = 0
        self._actual_total = 0
        self._reserved_cost = 0.0
        self.actual_debit_usd = 0.0
        self.budget_breach = False
        self.budget_breach_reasons: list[str] = []
        self.dispatch_blocked = False
        self._spend_cap = 0.0

    @property
    def cumulative(self) -> dict[str, float | int]:
        return {
            "reserved_input_tokens": self._reserved_input,
            "reserved_output_tokens": self._reserved_output,
            "reserved_total_tokens": self._reserved_total,
            "actual_total_tokens": self._actual_total,
            "reserved_cost_usd": self._reserved_cost,
            "actual_debit_usd": self.actual_debit_usd,
            "budget_breach": self.budget_breach,
            "dispatch_blocked": self.dispatch_blocked,
            "budget_breach_reasons": list(self.budget_breach_reasons),
        }

    def reserve(self, *, config: ProviderConfig, request: ProviderRequest, attempt: int) -> ProviderAttempt:
        if self.dispatch_blocked:
            raise BudgetExceededError("dispatch blocked after budget breach")
        if config.live_enabled and request.cost_upper_bound_usd is None:
            raise BudgetExceededError("live dispatch requires an explicit conservative cost upper bound")
        input_bound = (request.input_tokens_estimate if request.input_tokens_estimate is not None else config.max_input_tokens) + request.schema_framing_tokens
        output_bound = request.max_output_tokens or config.max_output_tokens
        total_bound = input_bound + output_bound
        if input_bound > config.max_input_tokens:
            raise BudgetExceededError("request input token bound exceeds configured limit")
        if output_bound > config.max_output_tokens or total_bound > config.max_total_tokens:
            raise BudgetExceededError("request token bound exceeds configured limit")
        if request.cost_upper_bound_usd is not None:
            cost_bound = request.cost_upper_bound_usd
        elif request.estimated_cost_usd is not None:
            cost_bound = request.estimated_cost_usd
        else:
            # An unknown cost is conservatively held pending for the full
            # remaining spend ceiling; it is never treated as zero.
            remaining = config.max_spend_usd - self._reserved_cost - self.actual_debit_usd
            if remaining <= 0:
                raise BudgetExceededError("unknown cost cannot be reserved within the remaining spend cap")
            cost_bound = remaining
        if self._actual_total + self._reserved_total + total_bound > config.max_total_tokens:
            raise BudgetExceededError("cumulative reserved token bound exceeds configured limit")
        if self.actual_debit_usd + self._reserved_cost + cost_bound > config.max_spend_usd + 1e-12:
            raise BudgetExceededError("cumulative reserved spend bound exceeds configured limit")
        reservation_id = f"res_{uuid.uuid4().hex}"
        self._reserved_input += input_bound
        self._reserved_output += output_bound
        self._reserved_total += total_bound
        self._reserved_cost += cost_bound
        return ProviderAttempt(
            attempt=attempt, status="reserved", request_id=request.request_id,
            requested_provider=config.provider, requested_model=config.model,
            requested_upstream_providers=list(config.routing_only),
            reservation_id=reservation_id, reservation_status="pending",
            reserved_input_tokens=input_bound, reserved_output_tokens=output_bound,
            reserved_total_tokens=total_bound, reserved_cost_usd=cost_bound,
        )

    def record_rejection(self, *, request: ProviderRequest, attempt: int, exc: Exception) -> ProviderAttempt:
        code, error_class, safe_message = OpenRouterAdapter._safe_error(exc)
        entry = ProviderAttempt(
            attempt=attempt,
            status="budget_exhausted",
            request_id=request.request_id,
            error=safe_message,
            error_code=code,
            error_class=error_class,
            reservation_status="rejected",
        )
        self.attempts.append(entry)
        return entry

    def settle(self, reservation: ProviderAttempt, *, usage: dict[str, int] | None, cost: float | None, outcome_known: bool) -> ProviderAttempt:
        normalized = normalize_usage(usage)
        reservation.observed_input_tokens = normalized["input_tokens"]
        reservation.observed_output_tokens = normalized["output_tokens"]
        reservation.observed_total_tokens = normalized["total_tokens"]
        reservation.observed_cost_usd = cost
        reservation.reservation_status = "settled" if outcome_known and cost is not None else "unknown_pending"
        if cost is not None:
            reserved = reservation.reserved_cost_usd or 0.0
            self._reserved_cost = max(self._reserved_cost - reserved, 0.0)
            self.actual_debit_usd += cost
            if cost > reserved + 1e-12:
                self._mark_breach(f"observed cost {cost:.8f} exceeded reservation {reserved:.8f}")
            if self.actual_debit_usd > 0 and self.actual_debit_usd > self._spend_cap:
                self._mark_breach(f"cumulative actual debit {self.actual_debit_usd:.8f} exceeded cap {self._spend_cap:.8f}")
        if outcome_known and normalized["total_tokens"] is not None:
            self._reserved_total -= reservation.reserved_total_tokens
            self._actual_total += normalized["total_tokens"]
        if not any(item is reservation for item in self.attempts):
            self.attempts.append(reservation)
        return reservation

    def configure_cap(self, spend_cap: float) -> None:
        self._spend_cap = spend_cap

    def _mark_breach(self, reason: str) -> None:
        self.budget_breach = True
        self.dispatch_blocked = True
        if reason not in self.budget_breach_reasons:
            self.budget_breach_reasons.append(reason)

    def mark_token_breach(self, reason: str) -> None:
        self._mark_breach(reason)


def normalize_usage(usage: dict[str, Any] | None) -> dict[str, int | None]:
    """Normalize prompt/completion/total without double-counting total."""
    if not isinstance(usage, dict):
        return {"input_tokens": None, "output_tokens": None, "total_tokens": None}
    input_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    output_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    total_tokens = usage.get("total_tokens")
    def scalar(value: Any) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else None
    input_tokens = scalar(input_tokens)
    output_tokens = scalar(output_tokens)
    total_tokens = scalar(total_tokens)
    if total_tokens is None and input_tokens is not None and output_tokens is not None:
        total_tokens = input_tokens + output_tokens
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens}


class OpenRouterAdapter:
    """OpenRouter-shaped adapter with provider-neutral contract checks."""

    def __init__(self, config: ProviderConfig, transport: HTTPTransport, capabilities: ProviderCapabilities, ledger: AttemptLedger | None = None) -> None:
        self.config = config
        self.transport = transport
        self.capabilities = capabilities
        self.ledger = ledger or AttemptLedger()
        self.ledger.configure_cap(config.max_spend_usd)
        self.attempts = self.ledger.attempts
        if config.provider != "openrouter":
            raise ValueError("OpenRouterAdapter requires provider='openrouter'")
        if capabilities.provider != config.provider or capabilities.model != config.model:
            raise CapabilityError("provider config and capability metadata do not match")
        if config.research_mode and config.allow_auto_routing:
            raise CapabilityError("research_mode requires auto routing to be disabled")
        if config.research_mode and not capabilities.exact_model_pin:
            raise CapabilityError("research_mode requires an exact model pin")
        if config.research_mode and capabilities.auto_routing:
            raise CapabilityError("capability metadata reports auto routing")

    def _validate_request(self, request: ProviderRequest) -> None:
        if request.response_schema is not None and not self.capabilities.structured_outputs:
            raise CapabilityError("requested structured outputs but model capability is unsupported")
        if request.response_schema is not None:
            try:
                Draft202012Validator.check_schema(request.response_schema)
            except SchemaError as exc:
                raise CapabilityError(f"unsupported or invalid JSON Schema: {exc.validator}") from exc
        if request.tools and not self.capabilities.tools:
            raise CapabilityError("requested tools but model capability is unsupported")
        unknown = set(request.parameters) - self.capabilities.parameter_names
        if unknown:
            raise CapabilityError(f"unsupported provider parameters: {', '.join(sorted(unknown))}")
        output_limit = request.max_output_tokens or self.config.max_output_tokens
        if output_limit > self.config.max_output_tokens:
            raise BudgetExceededError("requested output tokens exceed configured limit")
        if "max_tokens" in request.parameters:
            raise CapabilityError("max_tokens must use max_output_tokens so the ledger and HTTP payload cannot diverge")
        effective_input = (request.input_tokens_estimate or 0) + request.schema_framing_tokens
        if effective_input > self.config.max_input_tokens:
            raise BudgetExceededError("input estimate plus schema/framing exceeds configured limit")
        if request.input_tokens_estimate is not None and request.input_tokens_estimate + request.schema_framing_tokens > self.config.max_input_tokens:
            raise BudgetExceededError("input estimate plus schema/framing exceeds configured limit")

    @staticmethod
    def _validate_schema(text: str, schema: dict[str, Any] | None) -> bool | None:
        if schema is None:
            return None
        try:
            validator = Draft202012Validator(schema)
            validator.check_schema(schema)
        except SchemaError as exc:
            raise CapabilityError(f"unsupported or invalid JSON Schema: {exc.validator}") from exc
        try:
            value = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ResponseValidationError("response is not valid JSON") from exc
        errors = sorted(validator.iter_errors(value), key=lambda error: list(error.path))
        if errors:
            raise ResponseValidationError(f"response schema validation failed at {list(errors[0].path)}: {errors[0].validator}")
        return True

    @staticmethod
    def _extract_billing(response: MockHTTPResponse) -> tuple[dict[str, Any] | None, float | None, str | None, str | None]:
        """Read billing/identity metadata without validating content."""
        payload = response.payload
        if not isinstance(payload, dict):
            return None, None, None, None
        usage_raw = payload.get("usage")
        usage = usage_raw if isinstance(usage_raw, dict) else None
        cost_raw = payload.get("cost")
        if cost_raw is None and isinstance(usage, dict):
            cost_raw = usage.get("cost")
        cost = float(cost_raw) if isinstance(cost_raw, (int, float)) and not isinstance(cost_raw, bool) and math.isfinite(float(cost_raw)) and float(cost_raw) >= 0 else None
        reported_model = payload.get("model") if isinstance(payload.get("model"), str) else None
        reported_provider = payload.get("provider") if isinstance(payload.get("provider"), str) else None
        return usage, cost, reported_model, reported_provider

    # Exact supported response labels only. No case folding, prefix matching,
    # priority/region collapsing, or model-version aliases are inferred.
    _UPSTREAM_LABELS = {
        "google-ai-studio": "google-ai-studio",
        "Google AI Studio": "google-ai-studio",
        "openai": "openai",
        "OpenAI": "openai",
    }

    @staticmethod
    def _safe_identity(value: str | None, public_values: set[str]) -> str | None:
        if value is None or value in public_values:
            return value
        # Untrusted identity fields must never become a credential/error echo.
        # Retain an attributable digest, not arbitrary response text.
        digest = hashlib.sha256(value.encode("utf-8", errors="replace")).hexdigest()
        return "redacted-sha256:" + digest

    def _capture_identity(self, entry: ProviderAttempt, model: str | None, provider: str | None) -> None:
        labels = self._UPSTREAM_LABELS
        upstream = labels.get(provider) if provider is not None else None
        if provider in self.config.routing_only:
            upstream = provider
        entry.requested_provider = self.config.provider
        entry.requested_model = self.config.model
        entry.requested_upstream_providers = list(self.config.routing_only)
        entry.reported_model = self._safe_identity(model, {self.config.model})
        entry.reported_provider = self._safe_identity(provider, set(labels) | set(self.config.routing_only) | {self.config.provider})
        entry.reported_upstream_provider = upstream
        if not self.config.research_mode:
            return
        require_identity = self.config.live_enabled or bool(self.config.routing_only)
        if model is None and require_identity:
            entry.identity_error = "missing_model"
        elif model is not None and model != self.config.model:
            entry.identity_error = "model_mismatch"
        elif self.config.routing_only and provider is None:
            entry.identity_error = "missing_upstream_provider"
        elif self.config.routing_only and upstream not in self.config.routing_only:
            entry.identity_error = "upstream_provider_mismatch"

    @staticmethod
    def _extract_content(response: MockHTTPResponse) -> tuple[str, str | None]:
        """Read content separately from billing settlement."""
        if response.payload is None:
            raise ResponseValidationError("provider returned no JSON payload")
        choices = response.payload.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ResponseValidationError("provider response has no choices")
        message = choices[0].get("message")
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str):
            raise ResponseValidationError("provider response choice has no text content")
        finish_reason = choices[0].get("finish_reason")
        return text, finish_reason if isinstance(finish_reason, str) else None

    @staticmethod
    def _safe_error(exc: Exception) -> tuple[str, str, str]:
        mapping = {
            CapabilityError: ("capability_error", "capability"),
            ResponseValidationError: ("response_validation_error", "response_validation"),
            BudgetExceededError: ("budget_exceeded", "budget"),
            RateLimitError: ("rate_limit", "rate_limit"),
            TimeoutError: ("timeout", "timeout"),
            ModelDriftError: ("model_drift", "model_drift"),
            LiveCallsDisabledError: ("live_calls_disabled", "policy"),
        }
        for error_type, (code, error_class) in mapping.items():
            if isinstance(exc, error_type):
                return code, error_class, "provider attempt failed"
        return "adapter_error", "adapter", "provider attempt failed"

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        self._validate_request(request)
        if not self.config.live_enabled and not getattr(self.transport, "is_mock", False):
            raise LiveCallsDisabledError("live provider calls are disabled by default")
        if not self.config.live_enabled and getattr(self.transport, "is_mock", False) is False:
            raise LiveCallsDisabledError("live provider calls are disabled by default")
        preflight = getattr(self.transport, "preflight", None)
        if self.config.live_enabled and callable(preflight):
            # Configuration/key checks happen before any attempt reservation or
            # network dispatch. The ledger still guards every actual attempt.
            preflight(config=self.config, request=request)
        attempts: list[ProviderAttempt] = []
        max_attempts = self.config.retries + 1
        started = time.perf_counter()
        for attempt_number in range(1, max_attempts + 1):
            attempt_started = time.perf_counter()
            reservation: ProviderAttempt | None = None
            settled = False
            try:
                reservation = self.ledger.reserve(config=self.config, request=request, attempt=attempt_number)
                attempts.append(reservation)
                response = self.transport.send(config=self.config, request=request)
                latency = time.perf_counter() - attempt_started
                if response.status_code == 429:
                    raise RateLimitError("provider returned HTTP 429")
                if response.status_code >= 500:
                    raise AdapterError(f"provider returned HTTP {response.status_code}")
                if response.status_code >= 400:
                    raise AdapterError(f"provider returned HTTP {response.status_code}")
                usage, cost, reported_model, reported_provider = self._extract_billing(response)
                normalized = normalize_usage(usage)
                # DurableLedger persists these sanitized identities together with
                # billing before any identity/content/schema rejection.
                self._capture_identity(reservation, reported_model, reported_provider)
                self.ledger.settle(reservation, usage=usage, cost=cost, outcome_known=usage is not None and cost is not None)
                settled = True
                if normalized["total_tokens"] is not None and normalized["total_tokens"] > self.config.max_total_tokens:
                    self.ledger.mark_token_breach("observed usage exceeded configured token cap")
                if self.ledger.budget_breach:
                    raise BudgetExceededError("observed provider debit breached the configured spend cap")
                if reservation.identity_error:
                    messages = {
                        "missing_model": "reported model is missing",
                        "model_mismatch": "reported model differs from requested model",
                        "missing_upstream_provider": "reported upstream provider is missing",
                        "upstream_provider_mismatch": "reported upstream provider is outside the approved route",
                    }
                    raise ModelDriftError(messages[reservation.identity_error])
                text, finish_reason = self._extract_content(response)
                schema_valid = self._validate_schema(text, request.response_schema)
                reservation.status = "success"
                reservation.latency_seconds = latency
                normalized_usage = {key: value for key, value in normalized.items() if value is not None} or None
                result = ProviderResponse(provider=reservation.reported_provider, model=reservation.reported_model, requested_provider=self.config.provider, requested_model=self.config.model, reported_provider=reservation.reported_provider, reported_model=reservation.reported_model, requested_upstream_providers=list(self.config.routing_only), reported_upstream_provider=reservation.reported_upstream_provider, model_drift=False, provider_drift=False, request_id=request.request_id, text=text, usage=normalized_usage, finish_reason=finish_reason, cost_usd=cost, latency_seconds=time.perf_counter() - started, retry_count=attempt_number - 1, response_schema_valid=schema_valid, actual_debit_usd=self.ledger.actual_debit_usd, budget_breach=self.ledger.budget_breach, dispatch_blocked=self.ledger.dispatch_blocked, budget_breach_reasons=list(self.ledger.budget_breach_reasons), attempts=attempts)
                return result
            except Exception as exc:
                code, error_class, safe_message = self._safe_error(exc)
                status = "timeout" if isinstance(exc, TimeoutError) else "rate_limit" if isinstance(exc, RateLimitError) else "budget_exhausted" if isinstance(exc, BudgetExceededError) else "model_drift" if isinstance(exc, ModelDriftError) else "error"
                if reservation is None:
                    reservation = self.ledger.record_rejection(request=request, attempt=attempt_number, exc=exc)
                    attempts.append(reservation)
                else:
                    reservation.status = status
                    reservation.error = safe_message
                    reservation.error_code = code
                    reservation.error_class = error_class
                    reservation.latency_seconds = time.perf_counter() - attempt_started
                    if not settled:
                        self.ledger.settle(reservation, usage=None, cost=None, outcome_known=False)
                if isinstance(exc, BudgetExceededError) or attempt_number >= max_attempts:
                    raise
        raise AdapterError("provider attempt loop ended unexpectedly")
