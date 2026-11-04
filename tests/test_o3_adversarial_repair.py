from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys

import pytest

from o3_test_support import MODEL, PROVIDER, PRICE_HASH, PRICE_TIME, credit, reviewed_fixture
from patent_to_pilot.providers.credit import normalize_credit
from patent_to_pilot.providers.history_export import inspect_history_export
from patent_to_pilot.providers.ledger_registry import CanonicalLedgerError, register_canonical_ledger, resolve_canonical_ledger
from patent_to_pilot.providers.openrouter import BudgetExceededError, CapabilityError, OpenRouterHTTPTransport, ProviderRequest
from patent_to_pilot.providers.round1 import R1_AUTHORIZATION_ID, Round1ProjectBudget, build_round1_config


def binding(path, digest, **kwargs):
    return register_canonical_ledger(path, authorization_id=R1_AUTHORIZATION_ID, policy_hash=digest,
        pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, **kwargs)


def open_budget(path, *, price=PRICE_HASH, at=PRICE_TIME):
    return Round1ProjectBudget(path, model_provider_map={MODEL: PROVIDER},
        pricing_snapshot_sha256=price, pricing_snapshot_utc=at)


def reserve(budget, aid, amount, observation):
    return budget.reserve(attempt_id=aid, phase="paired_pilot", model=MODEL, provider=PROVIDER,
        payload_sha256="c" * 64, upper_bound_usd=amount, bound_verified=True, data_class="synthetic", credit_snapshot=observation)


@pytest.fixture
def canonical(tmp_path, monkeypatch):
    registry = tmp_path / "canonical.json"
    monkeypatch.setattr("patent_to_pilot.providers.ledger_registry.default_registry_path", lambda _: registry)
    monkeypatch.setattr("patent_to_pilot.providers.local_epoch.active", lambda: False)
    path = tmp_path / "canonical.sqlite3"
    digest = reviewed_fixture(path)
    binding(path, digest)
    return path, digest, registry


@pytest.mark.parametrize("data", [b"", b"new zero ledger", b"SQLite format 3\0not-a-database"])
def test_non_journals_cannot_bootstrap_allowance(tmp_path, data):
    path = tmp_path / "invalid.sqlite3"
    path.write_bytes(data)
    with pytest.raises(CanonicalLedgerError):
        binding(path, "f" * 64)
    assert path.read_bytes() == data


def test_fresh_r1_history_with_abundant_credit_is_still_unknown(tmp_path):
    path = tmp_path / "unknown.sqlite3"
    digest = reviewed_fixture(path, anchor=False)
    # Even an R1-shaped DB is insufficient; old pilot and large credit grant no R1 history.
    assert normalize_credit(credit(amount=1000))["remaining_credits_usd"] == 1000
    with pytest.raises(CanonicalLedgerError, match="all-attempt history"):
        binding(path, digest)


def test_copied_db_alternate_registry_and_relative_path(canonical, tmp_path, monkeypatch):
    path, digest, registry = canonical
    copy = tmp_path / "copy.sqlite3"
    shutil.copyfile(path, copy)
    with pytest.raises(CanonicalLedgerError, match="copied or relocated"):
        binding(copy, digest)
    with pytest.raises(CanonicalLedgerError, match="alternate registry"):
        binding(path, digest, registry_path=tmp_path / "second.json")
    monkeypatch.chdir(tmp_path)
    budget = open_budget(Path("canonical.sqlite3"))
    assert budget.path == path
    budget.close()


def test_same_ledger_can_refresh_price_without_reset(canonical):
    path, _, _ = canonical
    budget = open_budget(path)
    observation = credit()
    reserve(budget, "first", .01, observation)
    budget.settle("first", .005)
    budget.close()
    budget = open_budget(path, price="b" * 64, at="2026-10-31T12:00:00Z")
    try:
        reserve(budget, "second", .01, observation)
        budget.settle("second", .005)
        assert budget.snapshot()["actual_nano_usd"] == 10_000_000
        assert budget.db.execute("SELECT pricing_sha256 FROM budget_attempt_context ORDER BY attempt_id").fetchall() == [("a" * 64,), ("b" * 64,)]
    finally:
        budget.close()


@pytest.mark.parametrize("amount", [-1, float("nan"), float("inf"), True, None])
def test_invalid_credit_values_rejected(amount):
    with pytest.raises(ValueError):
        normalize_credit(credit(amount=amount))


@pytest.mark.parametrize("seconds", [-1, 301])
def test_credit_future_or_stale_rejected(seconds):
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="future-dated or stale"):
        normalize_credit(credit(at=(now - timedelta(seconds=seconds)).isoformat()), now=now, require_current=True)


def test_self_asserted_hash_is_never_provider_verification():
    raw = normalize_credit(credit(source="approved_integration"))
    assert normalize_credit(raw, require_current=True)["verification"] == "asserted_observation_not_provider_verified"


@pytest.mark.parametrize("updates", [{"key_scope": "other"}, {"account_scope": "other"}, {"authorization_id": "other"}, {"key_remaining_usd": 0}])
def test_scoped_key_limit_checked_before_reservation(canonical, updates):
    budget = open_budget(canonical[0])
    try:
        with pytest.raises(BudgetExceededError):
            reserve(budget, "reject", .01, credit(**updates))
        assert budget.snapshot()["attempts"] == 0
    finally:
        budget.close()


def test_repeated_runs_do_not_reuse_observed_credit(canonical):
    budget = open_budget(canonical[0])
    observation = credit(amount=.015)
    try:
        reserve(budget, "first", .01, observation)
        budget.settle("first", .005)
        with pytest.raises(BudgetExceededError):
            reserve(budget, "second", .01, observation)
        assert budget.snapshot()["actual_nano_usd"] == 5_000_000
    finally:
        budget.close()


def test_crash_and_above_bound_debit_keep_full_exposure(canonical):
    path = canonical[0]
    budget = open_budget(path)
    reserve(budget, "crashed", .01, credit())
    budget.close()  # Simulate process loss before/after send, before settlement.
    budget = open_budget(path)
    try:
        assert budget.snapshot()["unknown_or_pending"] == ["crashed"]
        with pytest.raises(BudgetExceededError):
            reserve(budget, "retry", .01, credit())
        with pytest.raises(BudgetExceededError):
            budget.settle("crashed", .02)
        assert budget.snapshot()["actual_nano_usd"] == 20_000_000
        with pytest.raises(BudgetExceededError):
            budget.settle("crashed", .02)
        assert budget.snapshot()["actual_nano_usd"] == 20_000_000
        with pytest.raises(ValueError, match="conflicting"):
            budget.settle("crashed", 0)
    finally:
        budget.close()


def test_two_processes_share_one_atomic_reservation(tmp_path):
    path = tmp_path / "mock-only.sqlite3"
    budget = Round1ProjectBudget(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, namespace="mock")
    budget.close()
    program = '''import sys
from pathlib import Path
from patent_to_pilot.providers.round1 import Round1ProjectBudget
from patent_to_pilot.providers.openrouter import BudgetExceededError
b=Round1ProjectBudget(Path(sys.argv[1]),model_provider_map={"qwen/qwen3-32b":"DeepInfra"},pricing_snapshot_sha256="a"*64,pricing_snapshot_utc="2026-10-31T00:00:00Z",namespace="mock")
try:
 b.reserve(attempt_id=sys.argv[2],phase="paired_pilot",model="qwen/qwen3-32b",provider="DeepInfra",payload_sha256="b"*64,upper_bound_usd=3.5,bound_verified=True,data_class="synthetic")
 print("reserved")
except BudgetExceededError: print("blocked")
finally: b.close()
'''
    import os
    env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1] / "src"))
    workers = [subprocess.Popen([sys.executable, "-B", "-c", program, str(path), f"writer{i}"], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for i in range(2)]
    results = [worker.communicate(timeout=30) for worker in workers]
    assert all(worker.returncode == 0 for worker in workers), results
    assert sorted(out.strip() for out, _ in results) == ["blocked", "reserved"]


@pytest.mark.parametrize("field", ["messages", "model", "provider", "stream", "response_format", "tools"])
def test_parameter_cannot_replace_bound_wire_fields(tmp_path, field):
    budget = Round1ProjectBudget(tmp_path / "mock.sqlite3", model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, namespace="mock")
    try:
        config = build_round1_config(budget.policy, phase="paired_pilot", model=MODEL, max_price={"prompt": .08, "completion": .28})
        with pytest.raises(CapabilityError):
            OpenRouterHTTPTransport._request_payload(config, ProviderRequest(prompt="synthetic", parameters={field: "override"}))
    finally:
        budget.close()


def export():
    scope = {"authorization_id": R1_AUTHORIZATION_ID, "account_scope": "fixture-account", "key_scope": "fixture-key", "currency": "USD"}
    return {"format": "ptp-r1-all-attempt-export-v1", **scope, "coverage": {"attempt_count": 1},
        "attempts": [{**scope, "attempt_id": "retry-1", "phase": "paired_pilot", "model": MODEL, "upstream_provider": PROVIDER, "mode": "live", "purpose": "retry", "state": "unknown_pending", "reserved_usd": .02, "actual_usd": None, "provider_generation_id": None, "payload_sha256": "f" * 64}]}


def test_export_consistency_cannot_certify_completeness_or_activate():
    result = inspect_history_export(export())
    assert result["unresolved_reserved_nano_usd"] == 20_000_000
    assert result["history_completeness"] == "NOT_VERIFIED"
    assert not result["live_admission_enabled"] and not result["import_performed"]


@pytest.mark.parametrize("field,value", [("mode", "mock"), ("reserved_usd", -1), ("reserved_usd", float("nan")), ("currency", "THB"), ("account_scope", "another"), ("state", "failed-zero-assumed")])
def test_export_rejects_ambiguous_history(field, value):
    raw = export()
    raw["attempts"][0][field] = value
    with pytest.raises(ValueError):
        inspect_history_export(raw)


def test_export_rejects_duplicate_conflict_or_missing_attempt():
    raw = export()
    raw["attempts"].append(deepcopy(raw["attempts"][0]))
    raw["attempts"][1]["reserved_usd"] = 3
    with pytest.raises(ValueError):
        inspect_history_export(raw)
    raw = export()
    raw["attempts"].clear()
    with pytest.raises(ValueError, match="count"):
        inspect_history_export(raw)


def test_transport_key_scope_binding_uses_only_synthetic_key(tmp_path):
    import hashlib
    budget = Round1ProjectBudget(tmp_path / "mock.sqlite3", model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, namespace="mock")
    try:
        config = build_round1_config(budget.policy, phase="paired_pilot", model=MODEL, max_price={"prompt": .08, "completion": .28})
        config.api_key_sha256 = hashlib.sha256(b"SYNTHETIC-NOT-A-CREDENTIAL").hexdigest()
        OpenRouterHTTPTransport._check_credential_scope(config, "SYNTHETIC-NOT-A-CREDENTIAL")
        with pytest.raises(CapabilityError, match="reviewed key scope"):
            OpenRouterHTTPTransport._check_credential_scope(config, "SYNTHETIC-DIFFERENT")
    finally:
        budget.close()


def test_direct_budget_component_cannot_admit_unregistered_second_ledger(canonical, tmp_path):
    from patent_to_pilot.providers.project_budget import ProjectBudget
    from patent_to_pilot.providers.round1 import build_round1_policy
    second = tmp_path / "second.sqlite3"
    reviewed_fixture(second)
    policy = build_round1_policy({MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME)
    budget = ProjectBudget(second, policy=policy, namespace="canonical", canonical_path=second,
        ledger_id=R1_AUTHORIZATION_ID + ":canonical", authorization_id=R1_AUTHORIZATION_ID,
        pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME)
    try:
        with pytest.raises(CanonicalLedgerError, match="not the registered"):
            reserve(budget, "bypass", .01, credit())
        assert budget.snapshot()["attempts"] == 0
    finally:
        budget.close()


def test_credit_rounds_availability_down_instead_of_minting_fractional_credit():
    assert normalize_credit(credit(amount="0.0000000001"))["remaining_credits_usd"] == 0


def test_credit_captured_while_request_in_flight_keeps_that_reservation(canonical):
    budget = open_budget(canonical[0])
    try:
        reserve(budget, "in-flight", .01, credit())
        newer_observation = credit(amount=.015)
        budget.settle("in-flight", .01)
        with pytest.raises(BudgetExceededError):
            reserve(budget, "after-capture", .01, newer_observation)
        assert budget.snapshot()["actual_nano_usd"] == 10_000_000
    finally:
        budget.close()
