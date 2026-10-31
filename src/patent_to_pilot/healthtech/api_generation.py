"""Fail-closed OpenRouter Qwen3-32B generation runner for O3."""
from __future__ import annotations

import json
from datetime import datetime
import math
from pathlib import Path
import re
import time
from typing import Any, Callable

from patent_to_pilot.healthtech.b4_live import B4Pricing, conservative_request_bound_usd
from patent_to_pilot.healthtech.generation_payload import (
    build_rights_cleared_paired_payload,
    canonical_json,
    sha256_json,
    strip_fence,
    validate_generation_output,
)
from patent_to_pilot.providers import (
    BudgetExceededError,
    MockHTTPTransport,
    OpenRouterHTTPTransport,
    ProviderCapabilities,
    ProviderRequest,
    ProviderResponse,
)
from patent_to_pilot.providers.round1 import (
    R1_AUTHORIZATION_ID,
    Round1ProjectBudget,
    Round1Runner,
    build_round1_config,
    build_round1_policy,
)


MODEL_ID = "qwen/qwen3-32b"
CREDIT_SNAPSHOT_FORMAT = "ptp-openrouter-credit-snapshot-v1"


class APIGenerationError(RuntimeError):
    """Raised when an API generation precondition or result fails."""


def _safe_token(value: str) -> str:
    token = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_") or "item"
    return token[:48]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise APIGenerationError("API generation input is unreadable") from exc
    if not isinstance(value, dict):
        raise APIGenerationError("API generation input must be a JSON object")
    return value


def normalize_account_credit_snapshot(raw: dict[str, Any]) -> dict[str, Any]:
    """Validate the sanitized account-credit fact used by live preflight."""
    if not isinstance(raw, dict):
        raise APIGenerationError("account credit snapshot must be a JSON object")
    if raw.get("format") != CREDIT_SNAPSHOT_FORMAT:
        raise APIGenerationError("account credit snapshot format is unsupported")
    if raw.get("provider") != "openrouter":
        raise APIGenerationError("account credit snapshot provider must be openrouter")
    source = raw.get("source")
    if source not in {"approved_integration", "owner_sanitized_snapshot"}:
        raise APIGenerationError("account credit snapshot source is not approved")
    as_of_utc = raw.get("as_of_utc")
    if not isinstance(as_of_utc, str) or not as_of_utc.strip():
        raise APIGenerationError("account credit snapshot timestamp is required")
    try:
        parsed_time = datetime.fromisoformat(as_of_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise APIGenerationError("account credit snapshot timestamp is invalid") from exc
    if parsed_time.tzinfo is None:
        raise APIGenerationError("account credit snapshot timestamp must include timezone")
    remaining = raw.get("remaining_credits_usd")
    if isinstance(remaining, bool) or not isinstance(remaining, (int, float)) or not math.isfinite(float(remaining)):
        raise APIGenerationError("remaining_credits_usd must be a finite number")
    if float(remaining) < 0:
        raise APIGenerationError("remaining_credits_usd cannot be negative")
    unsigned = {
        "format": CREDIT_SNAPSHOT_FORMAT,
        "provider": "openrouter",
        "source": source,
        "as_of_utc": as_of_utc,
        "remaining_credits_usd": float(remaining),
    }
    declared_hash = raw.get("snapshot_sha256")
    expected_hash = sha256_json(unsigned)
    if declared_hash is not None and declared_hash != expected_hash:
        raise APIGenerationError("account credit snapshot hash mismatch")
    return unsigned | {"snapshot_sha256": expected_hash}


class OpenRouterQwenGenerationRunner:
    """Run one sequential, exact-route generation attempt per frozen case."""

    def __init__(
        self,
        *,
        budget: Round1ProjectBudget,
        pricing: B4Pricing,
        transport_factory: Callable[[], Any] | None = None,
        live_enabled: bool = False,
        account_credit_snapshot: dict[str, Any] | None = None,
        run_id: str,
        max_output_tokens: int = 512,
        max_findings: int = 6,
        non_thinking_parameters: dict[str, Any] | None = None,
        max_input_tokens: int = 6144,
        timeout_seconds: float = 45.0,
    ) -> None:
        if pricing.model != MODEL_ID:
            raise APIGenerationError("API generation requires exact qwen/qwen3-32b")
        if max_output_tokens < 1 or max_output_tokens > 4096:
            raise APIGenerationError("max_output_tokens is outside the bounded range")
        if max_findings < 1 or max_findings > 6:
            raise APIGenerationError("max_findings is outside the frozen schema range")
        if max_input_tokens < 1:
            raise APIGenerationError("max_input_tokens must be positive")
        if live_enabled and budget.namespace != "canonical":
            raise BudgetExceededError("paid generation requires the canonical authorization ledger")
        if live_enabled and account_credit_snapshot is None:
            raise APIGenerationError("live generation requires a sanitized account credit snapshot")
        self.budget = budget
        self.pricing = pricing
        self.live_enabled = live_enabled
        self.account_credit_snapshot = (
            normalize_account_credit_snapshot(account_credit_snapshot)
            if account_credit_snapshot is not None
            else None
        )
        self.run_id = run_id
        self.max_output_tokens = max_output_tokens
        self.max_findings = max_findings
        self.max_input_tokens = max_input_tokens
        self.timeout_seconds = timeout_seconds
        self.non_thinking_parameters = dict(non_thinking_parameters or {})
        self.transport_factory = transport_factory or (lambda: OpenRouterHTTPTransport())
        self.policy = build_round1_policy(
            {pricing.model: pricing.upstream_provider},
            pricing_snapshot_sha256=pricing.snapshot_sha256,
            pricing_snapshot_utc=pricing.snapshot_utc,
        )
        self.config = build_round1_config(
            self.policy,
            phase="paired_pilot",
            model=MODEL_ID,
            max_price={
                "prompt": pricing.max_price_prompt,
                "completion": pricing.max_price_completion,
            },
            live_enabled=live_enabled,
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
            max_total_tokens=max_input_tokens + max_output_tokens + 1024,
            prompt_version="ptp-ht-o3-qwen3-32b-v1",
        )
        self.config.timeout_seconds = timeout_seconds
        self.capabilities = ProviderCapabilities(
            provider="openrouter",
            model=MODEL_ID,
            structured_outputs=True,
            tools=False,
            parameter_names=set(self.non_thinking_parameters),
            exact_model_pin=True,
            auto_routing=False,
        )

    def _request_for_case(self, payload_case: dict[str, Any]) -> tuple[ProviderRequest, int, int, float]:
        messages = payload_case["messages"]
        serialized = canonical_json(messages)
        input_tokens = max(1, (len(serialized) + 3) // 4)
        schema_tokens = max(1, (len(canonical_json(payload_case["response_schema"])) + 3) // 4)
        if input_tokens + schema_tokens > self.max_input_tokens:
            raise APIGenerationError("frozen paired message exceeds configured input bound")
        upper_bound = conservative_request_bound_usd(
            input_tokens=input_tokens + schema_tokens,
            output_tokens=self.max_output_tokens,
            pricing=self.pricing,
        )
        request_id = f"{_safe_token(self.run_id)}-{_safe_token(payload_case['case_id'])}"
        request = ProviderRequest(
            prompt=messages[-1]["content"],
            messages=messages,
            response_schema=payload_case["response_schema"],
            parameters=dict(self.non_thinking_parameters),
            input_tokens_estimate=input_tokens,
            schema_framing_tokens=schema_tokens,
            max_output_tokens=self.max_output_tokens,
            cost_upper_bound_usd=upper_bound,
            request_id=request_id,
        )
        return request, input_tokens, schema_tokens, upper_bound

    def run(self, pack: dict[str, Any]) -> dict[str, Any]:
        if self.live_enabled and not self.non_thinking_parameters:
            raise APIGenerationError(
                "current route snapshot lacks an explicit non-thinking parameter binding"
            )
        payload = build_rights_cleared_paired_payload(
            pack,
            provider="openrouter",
            model=MODEL_ID,
            route=self.pricing.upstream_provider,
            max_output_tokens=self.max_output_tokens,
        )
        prepared_cases = []
        for payload_case, source_case in zip(payload["cases"], pack["cases"]):
            request, input_tokens, schema_tokens, upper_bound = self._request_for_case(payload_case)
            prepared_cases.append((payload_case, source_case, request, input_tokens, schema_tokens, upper_bound))
        total_bound = sum(item[5] for item in prepared_cases)
        if self.live_enabled:
            assert self.account_credit_snapshot is not None
            if self.account_credit_snapshot["remaining_credits_usd"] < total_bound:
                raise BudgetExceededError("account credit snapshot is below the conservative run bound")
        result_cases: list[dict[str, Any]] = []
        for payload_case, source_case, request, input_tokens, schema_tokens, upper_bound in prepared_cases:
            attempt_id = request.request_id
            started = time.perf_counter()
            case_result: dict[str, Any] = {
                "case_id": payload_case["case_id"],
                "attempt_id": attempt_id,
                "message_sha256": payload_case["message_sha256"],
                "payload_sha256": payload_case["payload_sha256"],
                "input_token_bound": input_tokens,
                "schema_framing_token_bound": schema_tokens,
                "output_token_bound": self.max_output_tokens,
                "cost_upper_bound_usd": upper_bound,
                "status": "NOT_RUN",
            }
            try:
                data_class = "synthetic" if all(
                    item["decision"] == "SYNTHETIC" for item in payload_case["source_bindings"]
                ) else "public"
                response: ProviderResponse = Round1Runner(
                    self.budget,
                    self.transport_factory,
                ).complete(
                    attempt_id=attempt_id,
                    phase="paired_pilot",
                    config=self.config,
                    request=request,
                    capabilities=self.capabilities,
                    upper_bound_usd=upper_bound,
                    data_class=data_class,
                )
                output_text = response.text
                output_hash = sha256_json(output_text)
                parsed = json.loads(strip_fence(output_text))
                validate_generation_output(parsed, source_case, max_findings=self.max_findings)
                case_result.update({
                    "status": "SUCCESS",
                    "output_sha256": output_hash,
                    "schema_valid": True,
                    "usage": response.usage,
                    "latency_seconds": response.latency_seconds,
                    "cost_usd": response.cost_usd,
                    "actual_debit_usd": response.actual_debit_usd,
                    "reported_model": response.reported_model,
                    "reported_upstream_provider": response.reported_upstream_provider,
                    "parsed_output": parsed,
                })
            except Exception as exc:
                case_result.update({
                    "status": "FAILED",
                    "error_class": type(exc).__name__,
                    "schema_valid": False,
                    "elapsed_seconds": time.perf_counter() - started,
                })
                result_cases.append(case_result)
                snapshot = self.budget.snapshot()
                if snapshot["dispatch_blocked"]:
                    break
                continue
            result_cases.append(case_result)
        snapshot = self.budget.snapshot()
        status = "PASS_API_QWEN3_32B_FROZEN_PACK_GENERATION" if result_cases and all(
            case["status"] == "SUCCESS" for case in result_cases
        ) and len(result_cases) == len(pack["cases"]) else "PARTIAL_API_QWEN3_32B_FROZEN_PACK_GENERATION"
        return {
            "format": "ht-o3-api-generation-receipt-v1",
            "status": status,
            "authorization_id": R1_AUTHORIZATION_ID,
            "model_id": MODEL_ID,
            "route": self.pricing.upstream_provider,
            "pricing_snapshot_sha256": self.pricing.snapshot_sha256,
            "pricing_snapshot_utc": self.pricing.snapshot_utc,
            "pack_sha256": payload["pack_sha256"],
            "manifest": payload["manifest"],
            "thinking": False,
            "account_credit_snapshot": self.account_credit_snapshot,
            "conservative_run_bound_usd": total_bound,
            "provider_calls": sum(case["status"] in {"SUCCESS", "FAILED"} for case in result_cases),
            "paid_cost_usd": sum(float(case.get("actual_debit_usd") or 0.0) for case in result_cases),
            "ledger_snapshot": snapshot,
            "cases": result_cases,
        }

    @staticmethod
    def sanitized_receipt(result: dict[str, Any]) -> dict[str, Any]:
        """Drop messages and generated text before persisting a receipt."""
        safe = dict(result)
        safe["cases"] = []
        for case in result.get("cases", []):
            safe["cases"].append({
                key: value
                for key, value in case.items()
                if key not in {"parsed_output", "output_text", "messages"}
            })
        return safe

    @classmethod
    def from_snapshot(
        cls,
        *,
        budget: Round1ProjectBudget,
        snapshot_path: Path,
        transport_factory: Callable[[], Any] | None,
        live_enabled: bool,
        account_credit_snapshot: dict[str, Any] | None = None,
        run_id: str,
        max_output_tokens: int = 512,
        max_findings: int = 6,
    ) -> "OpenRouterQwenGenerationRunner":
        raw = _load_json(snapshot_path)
        try:
            pricing = B4Pricing.model_validate(raw)
        except Exception as exc:
            raise APIGenerationError("model snapshot does not contain exact pricing fields") from exc
        parameters = raw.get("non_thinking_parameters")
        if parameters is not None and not isinstance(parameters, dict):
            raise APIGenerationError("non_thinking_parameters must be an object")
        return cls(
            budget=budget,
            pricing=pricing,
            transport_factory=transport_factory,
            live_enabled=live_enabled,
            account_credit_snapshot=account_credit_snapshot,
            run_id=run_id,
            max_output_tokens=max_output_tokens,
            max_findings=max_findings,
            non_thinking_parameters=parameters,
            max_input_tokens=int(raw.get("max_input_tokens", min(int(raw.get("context_length", 6144)), 6144))),
            timeout_seconds=float(raw.get("timeout_seconds", 45.0)),
        )


def write_sanitized_receipt(result: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe = OpenRouterQwenGenerationRunner.sanitized_receipt(result)
    output_path.write_text(json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
