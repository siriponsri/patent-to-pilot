import json

import pytest

from patent_to_pilot.providers import (
    AttemptLedger,
    BudgetExceededError,
    CapabilityError,
    LiveCallsDisabledError,
    ModelDriftError,
    MockHTTPResponse,
    MockHTTPTransport,
    OpenRouterHTTPTransport,
    OpenRouterAdapter,
    HTTPTransportError,
    ProviderCapabilities,
    ProviderConfig,
    ProviderRequest,
    RateLimitError,
    ResponseValidationError,
    TimeoutError,
    normalize_usage,
)


def _adapter(response, *, structured=True, tools=False, live=False, retries=0, spend=1.0):
    config = ProviderConfig(model="openai/gpt-4o-mini", live_enabled=live, retries=retries, max_spend_usd=spend)
    caps = ProviderCapabilities(provider="openrouter", model=config.model, structured_outputs=structured, tools=tools, parameter_names={"temperature"})
    return OpenRouterAdapter(config, MockHTTPTransport(response), caps)


def test_mock_success_records_exact_model_usage_and_schema():
    response = MockHTTPResponse(200, {"model": "openai/gpt-4o-mini", "provider": "openrouter", "choices": [{"message": {"content": '{"answer":"ok"}'}, "finish_reason": "stop"}], "usage": {"prompt_tokens": 2, "completion_tokens": 3}})
    adapter = _adapter(response)
    result = adapter.complete(ProviderRequest(prompt="hello", response_schema={"type": "object", "required": ["answer"], "properties": {"answer": {"type": "string"}}}))
    assert result.provider == "openrouter" and result.model == "openai/gpt-4o-mini"
    assert result.usage == {"input_tokens": 2, "output_tokens": 3, "total_tokens": 5}
    assert result.response_schema_valid is True and result.retry_count == 0


def test_invalid_schema_and_unsupported_capability_are_explicit():
    bad = _adapter(MockHTTPResponse(200, {"model": "openai/gpt-4o-mini", "provider": "openrouter", "choices": [{"message": {"content": '{"wrong":1}'}}]}))
    with pytest.raises(ResponseValidationError):
        bad.complete(ProviderRequest(prompt="hello", response_schema={"type": "object", "required": ["answer"]}))
    no_structured = _adapter(MockHTTPResponse(200, {"choices": []}), structured=False)
    with pytest.raises(CapabilityError, match="structured outputs"):
        no_structured.complete(ProviderRequest(prompt="hello", response_schema={"type": "object"}))


def test_timeout_rate_limit_and_budget_are_recorded_without_retry_by_default():
    timeout = _adapter(TimeoutError("timeout"))
    with pytest.raises(TimeoutError):
        timeout.complete(ProviderRequest(prompt="hello"))
    assert timeout.attempts[0].status == "timeout"
    limited = _adapter(MockHTTPResponse(429, {}), retries=0)
    with pytest.raises(RateLimitError):
        limited.complete(ProviderRequest(prompt="hello"))
    assert limited.attempts[0].status == "rate_limit"
    budget = _adapter(MockHTTPResponse(200, {"choices": [{"message": {"content": "ok"}}], "usage": {"total_tokens": 99}}), spend=1.0)
    budget.config.max_total_tokens = 10
    with pytest.raises(BudgetExceededError):
        budget.complete(ProviderRequest(prompt="hello"))
    assert budget.attempts[0].status == "budget_exhausted"


def test_missing_usage_is_unknown_not_invented_and_live_transport_is_disabled():
    missing = _adapter(MockHTTPResponse(200, {"choices": [{"message": {"content": "ok"}}]}))
    assert missing.complete(ProviderRequest(prompt="hello")).usage is None
    class NonMock:
        is_mock = False
        def send(self, **kwargs):
            raise AssertionError("must not be called")
    adapter = OpenRouterAdapter(ProviderConfig(model="x"), NonMock(), ProviderCapabilities(provider="openrouter", model="x"))
    with pytest.raises(LiveCallsDisabledError):
        adapter.complete(ProviderRequest(prompt="hello"))


def test_usage_normalization_does_not_double_count_total():
    assert normalize_usage({"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8})["total_tokens"] == 8


def test_shared_ledger_rejects_single_request_token_bound_and_cumulative_spend():
    config = ProviderConfig(model="google/gemini-2.5-flash-lite", max_input_tokens=5, max_output_tokens=3, max_total_tokens=8, max_spend_usd=0.01)
    caps = ProviderCapabilities(provider="openrouter", model=config.model)
    transport = MockHTTPTransport([
        MockHTTPResponse(200, {"model": config.model, "provider": "openrouter", "choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}, "cost": 0.006}),
        MockHTTPResponse(200, {"model": config.model, "provider": "openrouter", "choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8}, "cost": 0.006}),
    ])
    ledger = AttemptLedger()
    adapter = OpenRouterAdapter(config, transport, caps, ledger)
    adapter.complete(ProviderRequest(prompt="one", input_tokens_estimate=5, max_output_tokens=3, cost_upper_bound_usd=0.006))
    with pytest.raises(BudgetExceededError):
        adapter.complete(ProviderRequest(prompt="two", input_tokens_estimate=5, max_output_tokens=3, cost_upper_bound_usd=0.006))
    assert ledger.attempts[-1].reservation_status == "rejected"
    assert ledger.actual_debit_usd == pytest.approx(0.006)
    assert ledger.dispatch_blocked is False
    assert len(transport.calls) == 1
    too_big = OpenRouterAdapter(config, MockHTTPTransport(MockHTTPResponse(200, {})), caps)
    with pytest.raises(BudgetExceededError):
        too_big.complete(ProviderRequest(prompt="too big", input_tokens_estimate=6, max_output_tokens=3))


def test_missing_usage_and_cost_remain_unknown_pending_and_retry_reservations_are_logged():
    config = ProviderConfig(model="openai/gpt-4.1-mini", max_input_tokens=5, max_output_tokens=3, max_total_tokens=16, max_spend_usd=0.01, retries=1)
    caps = ProviderCapabilities(provider="openrouter", model=config.model)
    transport = MockHTTPTransport([TimeoutError("Authorization: fake-secret"), MockHTTPResponse(200, {"model": config.model, "provider": "openrouter", "choices": [{"message": {"content": "ok"}}]})])
    ledger = AttemptLedger()
    adapter = OpenRouterAdapter(config, transport, caps, ledger)
    result = adapter.complete(ProviderRequest(prompt="retry", input_tokens_estimate=5, max_output_tokens=3, cost_upper_bound_usd=0.005))
    assert result.retry_count == 1
    assert ledger.attempts[0].reservation_status == "unknown_pending"
    assert ledger.attempts[0].error == "provider attempt failed"
    assert "fake-secret" not in json.dumps([attempt.model_dump() for attempt in ledger.attempts])
    assert ledger.attempts[1].reservation_status == "unknown_pending"


def test_json_schema_enforces_integer_minimum_and_additional_properties():
    response = MockHTTPResponse(200, {"model": "openai/gpt-4o-mini", "provider": "openrouter", "choices": [{"message": {"content": '{"count": 1.5, "extra": true}'}}]})
    adapter = _adapter(response)
    schema = {"type": "object", "additionalProperties": False, "required": ["count"], "properties": {"count": {"type": "integer", "minimum": 2}}}
    with pytest.raises(ResponseValidationError):
        adapter.complete(ProviderRequest(prompt="schema", response_schema=schema))


def test_invalid_schema_is_rejected_before_transport_dispatch():
    transport = MockHTTPTransport(MockHTTPResponse(200, {}))
    adapter = _adapter(MockHTTPResponse(200, {}))
    adapter.transport = transport
    with pytest.raises(CapabilityError):
        adapter.complete(ProviderRequest(prompt="invalid schema", response_schema={"type": "not-a-json-schema-type"}))
    assert transport.calls == []


def test_research_mode_rejects_reported_model_drift_and_does_not_guess_missing_provider():
    drift = MockHTTPResponse(200, {"model": "openai/gpt-4.1-mini", "provider": "openrouter", "choices": [{"message": {"content": "ok"}}]})
    config = ProviderConfig(model="google/gemini-2.5-flash-lite")
    caps = ProviderCapabilities(provider="openrouter", model=config.model)
    config.max_spend_usd = 1.0
    adapter = OpenRouterAdapter(config, MockHTTPTransport(drift), caps)
    with pytest.raises(Exception, match="reported model"):
        adapter.complete(ProviderRequest(prompt="drift"))
    missing = _adapter(MockHTTPResponse(200, {"model": "openai/gpt-4o-mini", "choices": [{"message": {"content": "ok"}}]}))
    result = missing.complete(ProviderRequest(prompt="missing provider"))
    assert result.provider is None and result.reported_provider is None


def test_observed_cost_over_reservation_breaches_budget_and_blocks_future_dispatch():
    config = ProviderConfig(model="openai/gpt-4.1-mini", max_input_tokens=5, max_output_tokens=3, max_total_tokens=8, max_spend_usd=0.01)
    caps = ProviderCapabilities(provider="openrouter", model=config.model)
    transport = MockHTTPTransport(MockHTTPResponse(200, {"model": config.model, "provider": "openrouter", "choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}, "cost": 0.006}))
    ledger = AttemptLedger()
    adapter = OpenRouterAdapter(config, transport, caps, ledger)
    with pytest.raises(BudgetExceededError):
        adapter.complete(ProviderRequest(prompt="over reservation", input_tokens_estimate=5, max_output_tokens=3, cost_upper_bound_usd=0.005))
    assert ledger.actual_debit_usd == pytest.approx(0.006)
    assert ledger.budget_breach is True and ledger.dispatch_blocked is True
    assert ledger.budget_breach_reasons
    before = len(transport.calls)
    with pytest.raises(BudgetExceededError):
        adapter.complete(ProviderRequest(prompt="blocked", input_tokens_estimate=5, max_output_tokens=3, cost_upper_bound_usd=0.001))
    assert len(transport.calls) == before


def test_schema_invalid_attempt_settles_billing_then_retry_debit_is_cumulative():
    config = ProviderConfig(model="openai/gpt-4.1-mini", max_input_tokens=5, max_output_tokens=3, max_total_tokens=16, max_spend_usd=0.02, retries=1)
    caps = ProviderCapabilities(provider="openrouter", model=config.model, structured_outputs=True)
    invalid = MockHTTPResponse(200, {"model": config.model, "provider": "openrouter", "choices": [{"message": {"content": '{"count": 1}'}}], "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3}, "cost": 0.006})
    valid = MockHTTPResponse(200, {"model": config.model, "provider": "openrouter", "choices": [{"message": {"content": '{"count": 2}'}}], "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3}, "cost": 0.006})
    ledger = AttemptLedger()
    adapter = OpenRouterAdapter(config, MockHTTPTransport([invalid, valid]), caps, ledger)
    result = adapter.complete(ProviderRequest(prompt="schema retry", input_tokens_estimate=5, max_output_tokens=3, cost_upper_bound_usd=0.006, response_schema={"type": "object", "required": ["count"], "properties": {"count": {"type": "integer", "minimum": 2}}}))
    assert result.retry_count == 1
    assert result.actual_debit_usd == pytest.approx(0.012)
    assert len(ledger.attempts) == 2
    assert ledger.attempts[0].reservation_status == "settled"
    assert ledger.attempts[0].status == "error"
    assert ledger.attempts[0].observed_cost_usd == pytest.approx(0.006)
    assert ledger.attempts[1].status == "success"


def test_live_mode_requires_explicit_positive_cost_upper_bound_before_dispatch():
    config = ProviderConfig(model="openai/gpt-4.1-mini", live_enabled=True, max_spend_usd=0.01, routing_only=["openai"], max_price={"prompt": 0.4, "completion": 1.6})
    caps = ProviderCapabilities(provider="openrouter", model=config.model)
    transport = MockHTTPTransport(MockHTTPResponse(200, {}))
    adapter = OpenRouterAdapter(config, transport, caps)
    with pytest.raises(BudgetExceededError, match="cost upper bound"):
        adapter.complete(ProviderRequest(prompt="live guard"))
    assert transport.calls == []


class _FakeHTTPResponse:
    def __init__(self, status, body):
        self.status = status
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


def _http_adapter(fake_opener, *, retries=0, spend=1.0):
    config = ProviderConfig(model="openai/gpt-4.1-mini", live_enabled=True, retries=retries, max_spend_usd=spend, routing_only=["openai"], max_price={"prompt": 0.40, "completion": 1.60})
    caps = ProviderCapabilities(provider="openrouter", model=config.model)
    transport = OpenRouterHTTPTransport(opener=fake_opener)
    adapter = OpenRouterAdapter(config, transport, caps)
    return adapter, transport


def test_openrouter_http_transport_mock_success_and_billing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-only-key")
    body = json.dumps({"model": "openai/gpt-4.1-mini", "provider": "OpenAI", "choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 2, "completion_tokens": 1}, "cost": 0.002}).encode()
    adapter, transport = _http_adapter(lambda request, timeout: _FakeHTTPResponse(200, body))
    result = adapter.complete(ProviderRequest(prompt="hello", input_tokens_estimate=2, max_output_tokens=1, cost_upper_bound_usd=0.002))
    assert result.actual_debit_usd == pytest.approx(0.002)
    assert result.text == "ok"
    assert transport.is_mock is False


def test_http_payload_pins_routing_and_output_limit_and_rejects_input_framing_over_cap(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-only-key")
    body = json.dumps({"model": "openai/gpt-4.1-mini", "provider": "OpenAI", "choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 2, "completion_tokens": 1}, "cost": 0.002}).encode()
    captured = {}
    def opener(request, timeout):
        captured["payload"] = json.loads(request.data.decode())
        captured["url"] = request.full_url
        return _FakeHTTPResponse(200, body)
    adapter, _ = _http_adapter(opener)
    adapter.complete(ProviderRequest(prompt="hello", input_tokens_estimate=2, schema_framing_tokens=1, max_output_tokens=7, cost_upper_bound_usd=0.002))
    assert captured["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert captured["payload"]["max_tokens"] == 7
    assert captured["payload"]["provider"] == {"only": ["openai"], "allow_fallbacks": False, "require_parameters": True, "max_price": {"prompt": 0.4, "completion": 1.6}}
    with pytest.raises(BudgetExceededError):
        adapter.complete(ProviderRequest(prompt="too much framing", input_tokens_estimate=3999, schema_framing_tokens=2, max_output_tokens=1, cost_upper_bound_usd=0.001))


@pytest.mark.parametrize("base_url", ["https://evil.example/api/v1", "https://openrouter.ai/api/v1/../other", "https://openrouter.ai/api/v1?redirect=https://evil.example"])
def test_http_transport_allowlists_origin_and_path_before_key_or_network(monkeypatch, base_url):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-only-key")
    calls = []
    adapter, transport = _http_adapter(lambda request, timeout: calls.append(request) or _FakeHTTPResponse(200, b"{}"))
    adapter.config.base_url = base_url
    with pytest.raises(CapabilityError):
        adapter.complete(ProviderRequest(prompt="url", input_tokens_estimate=1, max_output_tokens=1, cost_upper_bound_usd=0.001))
    assert calls == [] and transport.is_mock is False


def test_http_transport_disables_redirects_and_traceback_has_no_secret(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-only-key")
    transport = OpenRouterHTTPTransport(opener=lambda request, timeout: _FakeHTTPResponse(301, b"{}"))
    assert isinstance(transport.opener, object)
    config = ProviderConfig(model="openai/gpt-4.1-mini", live_enabled=True, routing_only=["openai"], max_price={"prompt": 0.4, "completion": 1.6})
    with pytest.raises(HTTPTransportError):
        # The fake opener raises an opaque error; formatted exception text
        # must not contain the Authorization value.
        def bad_opener(request, timeout):
            raise OSError("Authorization: fake-only-key")
        OpenRouterHTTPTransport(opener=bad_opener).send(config=config, request=ProviderRequest(prompt="trace", max_output_tokens=1, cost_upper_bound_usd=0.001))
    import traceback
    secret = "fake-only-key"
    def secret_opener(request, timeout):
        raise OSError("Authorization: " + secret)
    try:
        OpenRouterHTTPTransport(opener=secret_opener).send(config=config, request=ProviderRequest(prompt="trace", max_output_tokens=1, cost_upper_bound_usd=0.001))
    except HTTPTransportError:
        assert "fake-only-key" not in traceback.format_exc()


@pytest.mark.parametrize("status", [429, 500])
def test_openrouter_http_transport_returns_retryable_status_without_internal_retry(monkeypatch, status):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-only-key")
    body = b'{"error":"rate or server"}'
    calls = []
    def opener(request, timeout):
        calls.append(timeout)
        return _FakeHTTPResponse(status, body)
    adapter, _ = _http_adapter(opener, retries=0)
    with pytest.raises((RateLimitError, Exception)):
        adapter.complete(ProviderRequest(prompt="hello", input_tokens_estimate=2, max_output_tokens=1, cost_upper_bound_usd=0.002))
    assert len(calls) == 1
    assert calls[0] == 30.0


def test_openrouter_http_transport_timeout_is_sanitized_and_reservation_unknown(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-only-key")
    def opener(request, timeout):
        raise TimeoutError("Authorization: fake-only-key")
    adapter, _ = _http_adapter(opener)
    with pytest.raises(TimeoutError):
        adapter.complete(ProviderRequest(prompt="timeout", input_tokens_estimate=2, max_output_tokens=1, cost_upper_bound_usd=0.002))
    assert adapter.attempts[0].reservation_status == "unknown_pending"
    assert adapter.attempts[0].error == "provider attempt failed"


def test_openrouter_http_transport_malformed_and_missing_billing_are_not_fabricated(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-only-key")
    adapter, _ = _http_adapter(lambda request, timeout: _FakeHTTPResponse(200, b"not-json"))
    with pytest.raises(ModelDriftError):
        adapter.complete(ProviderRequest(prompt="malformed", input_tokens_estimate=2, max_output_tokens=1, cost_upper_bound_usd=0.002))
    assert adapter.attempts[0].reservation_status == "unknown_pending"

    body = json.dumps({"model": "openai/gpt-4.1-mini", "provider": "OpenAI", "choices": [{"message": {"content": "ok"}}]}).encode()
    adapter, _ = _http_adapter(lambda request, timeout: _FakeHTTPResponse(200, body))
    result = adapter.complete(ProviderRequest(prompt="missing billing", input_tokens_estimate=2, max_output_tokens=1, cost_upper_bound_usd=0.002))
    assert result.cost_usd is None
    assert result.actual_debit_usd == 0.0
    assert result.attempts[0].reservation_status == "unknown_pending"


def test_nested_usage_cost_is_normalized_without_dropping_scalar_billing(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "fake-only-key")
    body = json.dumps({"model": "openai/gpt-4.1-mini", "provider": "OpenAI", "choices": [{"message": {"content": "ok"}}], "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3, "cost": 0.003, "details": {"reasoning_tokens": 99}}}).encode()
    adapter, _ = _http_adapter(lambda request, timeout: _FakeHTTPResponse(200, body))
    result = adapter.complete(ProviderRequest(prompt="nested billing", input_tokens_estimate=2, max_output_tokens=1, cost_upper_bound_usd=0.003))
    assert result.cost_usd == pytest.approx(0.003)
    assert result.usage == {"input_tokens": 2, "output_tokens": 1, "total_tokens": 3}
