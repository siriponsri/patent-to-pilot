"""Fixture and single-exchange Chat Completions transport."""

import json
import math
import os
import re
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Protocol

import httpx
from patent_to_pilot.budget.ledger import estimate_chat_max_usd

from .contract import Draft, Proposition, TaskRequest
from .evidence import Evidence, relevant_checks, relevant_claims


@dataclass(frozen=True)
class Preset:
    base_url: str
    model: str
    key_env: str | None
    max_output: int = 800
    max_input_bytes: int = 24_000
    output_field: str = "max_tokens"
    capabilities: tuple[str, ...] = ("nonstream_text",)


PRESETS = {
    "fixture": Preset("", "mwd-fixture-v1", None),
    "typhoon": Preset("https://api.opentyphoon.ai/v1", "typhoon-v2.1-12b-instruct", "TYPHOON_API_KEY"),
    "openrouter": Preset("https://openrouter.ai/api/v1", "openai/gpt-4o-mini", "OPENROUTER_API_KEY"),
    "openai": Preset("https://api.openai.com/v1", "gpt-4o-mini-2024-07-18", "OPENAI_API_KEY",
                     output_field="max_completion_tokens"),
    "anthropic": Preset("https://api.anthropic.com/v1", "claude-sonnet-4-5-20250929", "ANTHROPIC_API_KEY"),
    "gemini": Preset("https://generativelanguage.googleapis.com/v1beta/openai", "gemini-2.5-flash", "GEMINI_API_KEY"),
    "dashscope": Preset("https://{workspace}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1",
                        "qwen-plus", "DASHSCOPE_API_KEY"),
    "deepseek": Preset("https://api.deepseek.com", "deepseek-chat", "DEEPSEEK_API_KEY"),
    "vllm": Preset("http://localhost:8000/v1", "configure-local-model", "VLLM_API_KEY"),
    "ollama": Preset("http://localhost:11434/v1", "configure-local-model", None),
}


@dataclass(frozen=True)
class Tariff:
    input_per_million: float
    output_per_million: float
    gross_multiplier: float
    evidence_ref: str

    def __post_init__(self):
        rates = (self.input_per_million, self.output_per_million, self.gross_multiplier)
        if not all(math.isfinite(rate) and rate >= 0 for rate in rates):
            raise ValueError("invalid tariff")
        if self.gross_multiplier < 1 or not self.evidence_ref.strip():
            raise ValueError("gross multiplier and tariff evidence are required")

    def cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (prompt_tokens * self.input_per_million + completion_tokens * self.output_per_million) / 1_000_000


@dataclass(frozen=True)
class Route:
    provider: str
    preset: Preset
    tariff: Tariff
    upstream_slug: str | None = None
    upstream_response: str | None = None

    @property
    def label(self) -> str:
        return self.upstream_slug or self.preset.base_url or "offline"

    def estimate(self, messages: list[dict[str, str]]) -> float | None:
        size = len(json.dumps(messages, ensure_ascii=False).encode("utf-8"))
        if size > self.preset.max_input_bytes:
            return None
        return estimate_chat_max_usd(
            {"input": self.tariff.input_per_million, "output": self.tariff.output_per_million},
            size, self.preset.max_output, margin=self.tariff.gross_multiplier,
        )


FIXTURE_ROUTE = Route("fixture", PRESETS["fixture"], Tariff(0, 0, 1, "B1 offline fixture"))


@dataclass(frozen=True)
class Completion:
    text: str | None
    input_tokens: int | None
    output_tokens: int | None
    cost_usd: float
    cost_basis: str
    generation_id: str | None = None


class UncertainDispatch(Exception):
    def __init__(self, reason: str, detail: dict | None = None):
        self.reason = reason
        self.detail = detail or {}


class Provider(Protocol):
    route: Route

    def complete(self, request: TaskRequest, evidence: Evidence, messages: list[dict[str, str]]) -> Completion:
        ...


class FixtureProvider:
    route = FIXTURE_ROUTE

    def complete(self, request: TaskRequest, evidence: Evidence, messages: list[dict[str, str]]) -> Completion:
        items = []
        if request.task == "A2":
            for row in relevant_checks(request, evidence):
                text = f"{row.owner} · {row.text}" if row.agency is None else f"{row.owner} · {row.agency} · {row.text}"
                items.append(Proposition(text=text, claim_ids=[row.claim_ids[0]]))
        else:
            for c in relevant_claims(request, evidence):
                if c.state == "known" and c.id not in {"entry", "queue"}:
                    items.append(Proposition(text=c.text, claim_ids=[c.id]))
                    break
            if request.task == "A3" and request.question_id == "market_window" and evidence.forecast and not items:
                text = (
                    "ค่าประมาณนี้ใช้กับการอนุมัติ ANDA ขั้นสุดท้ายครั้งแรกในสหรัฐฯ"
                    if request.language == "th" else "The estimate covers first final ANDA approval in the US."
                )
                items.append(Proposition(text=text, claim_ids=[evidence.forecast.claim_id]))
        return Completion(Draft(items=items).model_dump_json(), 0, 0, 0.0, "offline fixture; no network")


class ChatCompletionsProvider:
    def __init__(self, route: Route, api_key: str | None, client: httpx.Client):
        self.route = route
        self._key = api_key
        self._client = client
        if route.preset.capabilities != ("nonstream_text",):
            raise ValueError("unsupported capability set")
        if route.preset.key_env and not api_key:
            raise ValueError("required provider key missing")
        url = httpx.URL(route.preset.base_url)
        if (
            url.scheme not in {"http", "https"} or not url.host or url.userinfo or url.query or url.fragment
            or "{" in route.preset.base_url or "}" in route.preset.base_url
        ):
            raise ValueError("provider requires a fixed endpoint without credentials")
        if url.scheme != "https" and route.provider not in {"vllm", "ollama"}:
            raise ValueError("hosted providers require HTTPS")
        if route.provider == "openrouter" and not (route.upstream_slug and route.upstream_response):
            raise ValueError("OpenRouter requires a pinned upstream and response identity")

    def complete(self, request: TaskRequest, evidence: Evidence, messages: list[dict[str, str]]) -> Completion:
        route = self.route
        preset = route.preset
        payload = {"model": preset.model, "messages": messages, "stream": False, preset.output_field: preset.max_output}
        if route.provider == "openrouter":
            payload["provider"] = {
                "only": [route.upstream_slug], "order": [route.upstream_slug], "allow_fallbacks": False,
                "max_price": {"prompt": route.tariff.input_per_million, "completion": route.tariff.output_per_million},
            }
            payload["usage"] = {"include": True}
        headers = {"Authorization": f"Bearer {self._key}"} if self._key else {}
        try:
            response = self._client.post(
                f"{preset.base_url.rstrip('/')}/chat/completions", headers=headers, json=payload,
                follow_redirects=False, timeout=20.0,
            )
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException:
            raise UncertainDispatch("timeout") from None
        except (httpx.HTTPError, ValueError):
            raise UncertainDispatch("upstream_error") from None
        return self._decode(data)

    def _decode(self, data: object) -> Completion:
        route = self.route
        if not isinstance(data, dict):
            raise UncertainDispatch("billing_missing")
        if data.get("model") != route.preset.model or (
            route.provider == "openrouter" and data.get("provider") != route.upstream_response
        ):
            raise UncertainDispatch("route_or_price_changed")
        usage = data.get("usage")
        if not isinstance(usage, dict):
            raise UncertainDispatch("billing_missing")
        in_tokens, out_tokens = usage.get("prompt_tokens"), usage.get("completion_tokens")
        if any(type(n) is not int or n < 0 for n in (in_tokens, out_tokens)):
            raise UncertainDispatch("billing_missing")
        details = {"input_tokens": in_tokens, "output_tokens": out_tokens}
        locked_cost = route.tariff.cost(in_tokens, out_tokens)
        basis = "reported tokens at locked tariff, gross multiplier applied"
        if route.provider == "openrouter":
            reported = usage.get("cost")
            if type(reported) not in (int, float) or not math.isfinite(reported) or reported < 0:
                raise UncertainDispatch("billing_missing", details)
            if not math.isclose(reported, locked_cost, rel_tol=0, abs_tol=1e-8):
                raise UncertainDispatch("route_or_price_changed", {**details, "reported_cost_usd": reported})
            locked_cost = reported
            basis = "reported OpenRouter credits, gross multiplier applied"
        if out_tokens > route.preset.max_output:
            raise UncertainDispatch("route_or_price_changed", details)
        text = None
        choices = data.get("choices")
        if isinstance(choices, list) and len(choices) == 1 and isinstance(choices[0], dict):
            choice = choices[0]
            msg = choice.get("message")
            if (
                choice.get("finish_reason") == "stop" and isinstance(msg, dict)
                and isinstance(msg.get("content"), str) and not msg.get("tool_calls")
                and not msg.get("function_call")
            ):
                text = msg["content"]
        generation_id = data.get("id")
        if not isinstance(generation_id, str) or not re.fullmatch(r"[a-zA-Z0-9_.:-]{1,128}", generation_id):
            generation_id = None
        return Completion(text, in_tokens, out_tokens, locked_cost * route.tariff.gross_multiplier, basis, generation_id)


@contextmanager
def live_provider(route: Route):
    """Construct the server-only transport after a route has qualified."""
    key_env = route.preset.key_env
    with httpx.Client(transport=httpx.HTTPTransport(retries=0), trust_env=False) as client:
        yield ChatCompletionsProvider(route, os.environ.get(key_env) if key_env else None, client)
