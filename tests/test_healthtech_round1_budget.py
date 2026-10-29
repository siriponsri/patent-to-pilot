from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest

from patent_to_pilot.providers import (
    BudgetExceededError,
    ModelDriftError,
    MockHTTPResponse,
    MockHTTPTransport,
    ProviderCapabilities,
    ProviderRequest,
    ResponseValidationError,
    TimeoutError,
)
from patent_to_pilot.providers.project_budget import ProjectBudget
from patent_to_pilot.providers.round1 import (
    R1_ADMISSION_THRESHOLD_NANO_USD,
    R1_AUTHORIZATION_ID,
    R1_PHASE_CAPS_NANO_USD,
    R1_TOTAL_CAP_NANO_USD,
    Round1ProjectBudget,
    Round1Runner,
    build_round1_config,
    build_round1_policy,
)


MODEL = "test/model-r1"
PROVIDER = "openai"
PRICE_HASH = "a" * 64
PRICE_TIME = "2026-10-29T00:00:00Z"


def budget(tmp_path):
    return Round1ProjectBudget(
        tmp_path / "round1.sqlite3",
        model_provider_map={MODEL: PROVIDER},
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
    )


def config(budget, *, phase="canary", structured=False):
    return build_round1_config(
        budget.policy,
        phase=phase,
        model=MODEL,
        max_price={"prompt": 0.40, "completion": 1.60},
        live_enabled=False,
    )


def capabilities(*, structured=False):
    return ProviderCapabilities(
        provider="openrouter",
        model=MODEL,
        structured_outputs=structured,
    )


def request(*, cost=0.01, schema=None):
    return ProviderRequest(
        prompt="SYNTHETIC R1 request",
        response_schema=schema,
        input_tokens_estimate=10,
        max_output_tokens=20,
        cost_upper_bound_usd=cost,
    )


def response(*, content="ok", cost=0.01, model=MODEL, provider="OpenAI"):
    return MockHTTPResponse(
        200,
        {
            "model": model,
            "provider": provider,
            "choices": [{"message": {"content": content}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15, "cost": cost},
        },
    )


def reserve(budget, attempt_id, *, phase="canary", amount="0.01"):
    return budget.reserve(
        attempt_id=attempt_id,
        phase=phase,
        model=MODEL,
        provider=PROVIDER,
        payload_sha256="b" * 64,
        upper_bound_usd=amount,
        bound_verified=True,
        data_class="public",
    )


def test_round1_policy_is_versioned_and_keeps_planned_caps():
    policy = build_round1_policy(
        {MODEL: PROVIDER},
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
    )
    assert policy["authorization_id"] == R1_AUTHORIZATION_ID
    assert policy["incremental_cap_nano_usd"] == R1_TOTAL_CAP_NANO_USD
    assert policy["admission_threshold_nano_usd"] == R1_ADMISSION_THRESHOLD_NANO_USD
    assert policy["phase_caps_nano_usd"] == R1_PHASE_CAPS_NANO_USD
    assert sum(policy["phase_caps_nano_usd"].values()) == R1_ADMISSION_THRESHOLD_NANO_USD
    assert policy["retries"] == 0 and policy["max_concurrency"] == 1


def test_round1_rejects_old_policy_database_without_rebinding(tmp_path):
    path = tmp_path / "shared.sqlite3"
    old = ProjectBudget(path)
    old.close()
    with pytest.raises(ValueError, match="policy mismatch"):
        Round1ProjectBudget(
            path,
            model_provider_map={MODEL: PROVIDER},
            pricing_snapshot_sha256=PRICE_HASH,
            pricing_snapshot_utc=PRICE_TIME,
        )
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM budget_attempts").fetchone()[0] == 0


def test_round1_two_writers_compete_atomically_near_cap(tmp_path):
    path = tmp_path / "shared.sqlite3"
    first = budget(tmp_path)
    first.close()

    def attempt(index):
        local = Round1ProjectBudget(
            path,
            model_provider_map={MODEL: PROVIDER},
            pricing_snapshot_sha256=PRICE_HASH,
            pricing_snapshot_utc=PRICE_TIME,
        )
        try:
            reserve(local, f"near-cap-{index}", phase="paired_pilot", amount="3.5")
            return "reserved"
        except BudgetExceededError:
            return "blocked"
        finally:
            local.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == ["blocked", "reserved"]


def test_round1_reservation_is_committed_before_send(tmp_path):
    current = budget(tmp_path)
    state = []

    class InspectingTransport:
        is_mock = True

        def send(self, **kwargs):
            with sqlite3.connect(current.path) as db:
                state.append(db.execute("SELECT state FROM budget_attempts WHERE attempt_id=?", ("before-send",)).fetchone()[0])
            return response()

    runner = Round1Runner(current, lambda: InspectingTransport())
    result = runner.complete(
        attempt_id="before-send",
        phase="canary",
        config=config(current),
        request=request(),
        capabilities=capabilities(),
        upper_bound_usd=0.01,
        data_class="public",
    )
    assert result.text == "ok"
    assert state == ["pending"]
    assert current.snapshot()["actual_nano_usd"] == 10_000_000
def test_round1_crash_after_reservation_blocks_resume_and_replay(tmp_path):
    current = budget(tmp_path)

    class PowerLoss(BaseException):
        pass

    class CrashingTransport:
        is_mock = True

        def send(self, **kwargs):
            raise PowerLoss()

    runner = Round1Runner(current, lambda: CrashingTransport())
    with pytest.raises(PowerLoss):
        runner.complete(
            attempt_id="crash-after-reserve",
            phase="canary",
            config=config(current),
            request=request(),
            capabilities=capabilities(),
            upper_bound_usd=0.01,
            data_class="public",
        )
    assert current.snapshot()["unknown_or_pending"] == ["crash-after-reserve"]
    with pytest.raises(BudgetExceededError, match="pending"):
        reserve(current, "new-after-crash")


def test_round1_timeout_keeps_unknown_billing_pending(tmp_path):
    current = budget(tmp_path)

    class TimeoutTransport:
        is_mock = True

        def send(self, **kwargs):
            raise TimeoutError("synthetic timeout")

    runner = Round1Runner(current, lambda: TimeoutTransport())
    with pytest.raises(RuntimeError, match="unknown_pending"):
        runner.complete(
            attempt_id="timeout",
            phase="canary",
            config=config(current),
            request=request(),
            capabilities=capabilities(),
            upper_bound_usd=0.01,
            data_class="public",
        )
    snapshot = current.snapshot()
    assert snapshot["unknown_or_pending"] == ["timeout"]
    assert snapshot["actual_nano_usd"] == 0


def test_round1_duplicate_attempt_id_cannot_send_again(tmp_path):
    current = budget(tmp_path)
    calls = []

    class CountingTransport:
        is_mock = True

        def send(self, **kwargs):
            calls.append(True)
            return response()

    runner = Round1Runner(current, lambda: CountingTransport())
    kwargs = dict(
        attempt_id="duplicate",
        phase="canary",
        config=config(current),
        request=request(),
        capabilities=capabilities(),
        upper_bound_usd=0.01,
        data_class="public",
    )
    runner.complete(**kwargs)
    with pytest.raises(BudgetExceededError, match="already consumed"):
        runner.complete(**kwargs)
    assert len(calls) == 1


def test_round1_rejects_config_from_another_policy_before_transport(tmp_path):
    current = budget(tmp_path)
    other = build_round1_policy(
        {MODEL: PROVIDER},
        pricing_snapshot_sha256="b" * 64,
        pricing_snapshot_utc=PRICE_TIME,
    )
    calls = []

    class CountingTransport:
        is_mock = True

        def send(self, **kwargs):
            calls.append(True)
            return response()

    runner = Round1Runner(current, lambda: CountingTransport())
    with pytest.raises(BudgetExceededError, match="verified policy"):
        runner.complete(
            attempt_id="wrong-policy",
            phase="canary",
            config=build_round1_config(other, phase="canary", model=MODEL, max_price={"prompt": 0.4, "completion": 1.6}),
            request=request(),
            capabilities=capabilities(),
            upper_bound_usd=0.01,
            data_class="public",
        )
    assert calls == [] and current.snapshot()["attempts"] == 0


@pytest.mark.parametrize("bad_cost", ["not-a-number", -0.01, float("nan"), float("inf")])
def test_round1_malformed_cost_is_unknown_not_zero(tmp_path, bad_cost):
    current = budget(tmp_path)
    runner = Round1Runner(current, lambda: MockHTTPTransport(response(cost=bad_cost)))
    with pytest.raises((RuntimeError, BudgetExceededError), match="unknown_pending|accounting"):
        runner.complete(
            attempt_id="bad-cost",
            phase="canary",
            config=config(current),
            request=request(),
            capabilities=capabilities(),
            upper_bound_usd=0.01,
            data_class="public",
        )
    snapshot = current.snapshot()
    assert snapshot["actual_nano_usd"] == 0
    assert snapshot["unknown_or_pending"] == ["bad-cost"]


def test_round1_observed_cost_above_reservation_is_retained_and_blocks(tmp_path):
    current = budget(tmp_path)
    runner = Round1Runner(current, lambda: MockHTTPTransport(response(cost=0.02)))
    with pytest.raises(BudgetExceededError, match="breach"):
        runner.complete(
            attempt_id="overrun",
            phase="canary",
            config=config(current),
            request=request(cost=0.01),
            capabilities=capabilities(),
            upper_bound_usd=0.01,
            data_class="public",
        )
    snapshot = current.snapshot()
    assert snapshot["actual_nano_usd"] == 20_000_000
    assert snapshot["breach"] is True and snapshot["dispatch_blocked"] is True


def test_round1_model_drift_is_billed_before_rejection(tmp_path):
    current = budget(tmp_path)
    runner = Round1Runner(current, lambda: MockHTTPTransport(response(model="wrong/model")))
    with pytest.raises(ModelDriftError):
        runner.complete(
            attempt_id="model-drift",
            phase="canary",
            config=config(current),
            request=request(),
            capabilities=capabilities(),
            upper_bound_usd=0.01,
            data_class="public",
        )
    assert current.snapshot()["actual_nano_usd"] == 10_000_000

def test_round1_provider_drift_is_billed_before_rejection(tmp_path):
    current = budget(tmp_path)
    runner = Round1Runner(current, lambda: MockHTTPTransport(response(provider="Google AI Studio")))
    with pytest.raises(ModelDriftError):
        runner.complete(
            attempt_id="provider-drift",
            phase="canary",
            config=config(current),
            request=request(),
            capabilities=capabilities(),
            upper_bound_usd=0.01,
            data_class="public",
        )
    assert current.snapshot()["actual_nano_usd"] == 10_000_000


def test_round1_schema_failure_is_billed_before_rejection(tmp_path):
    current = budget(tmp_path)
    schema = {"type": "object", "required": ["answer"], "properties": {"answer": {"type": "string"}}}
    runner = Round1Runner(current, lambda: MockHTTPTransport(response(content="{}")))
    with pytest.raises(ResponseValidationError):
        runner.complete(
            attempt_id="schema-failure",
            phase="canary",
            config=config(current),
            request=request(schema=schema),
            capabilities=capabilities(structured=True),
            upper_bound_usd=0.01,
            data_class="public",
        )
    assert current.snapshot()["actual_nano_usd"] == 10_000_000
