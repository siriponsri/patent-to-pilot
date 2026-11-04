from __future__ import annotations

import json
import sqlite3

import pytest

from o3_test_support import MODEL, PRICE_HASH, PRICE_TIME, PROVIDER
from patent_to_pilot.providers.history_migration import EXPECTED_LEDGER_ID, migrate_reviewed_r1_history
from patent_to_pilot.providers.history_review import history_digest
from patent_to_pilot.providers.ledger_registry import CanonicalLedgerError, register_canonical_ledger
from patent_to_pilot.providers.round1 import R1_AUTHORIZATION_ID, Round1ProjectBudget


def _existing_unbound_r1(path):
    budget = Round1ProjectBudget(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, namespace="mock")
    digest = budget.policy_hash
    budget.close()
    with sqlite3.connect(path) as db:
        db.execute(
            "UPDATE budget_ledger_meta SET ledger_id=?,authorization_id=?,namespace='canonical',canonical_path=?,pricing_snapshot_sha256=?,pricing_snapshot_utc=?",
            (EXPECTED_LEDGER_ID, R1_AUTHORIZATION_ID, str(path.resolve()), PRICE_HASH, PRICE_TIME),
        )
    return digest


def _review():
    return {
        "authorization_id": R1_AUTHORIZATION_ID,
        "ledger_id": EXPECTED_LEDGER_ID,
        "status": "reviewed_all_attempts",
        "baseline_count": 0,
        "baseline_sha256": history_digest([]),
        "export_sha256": "f" * 64,
        "review_reference": "R1-REVIEW-20261031",
        "account_scope": "owner-account",
        "key_scope": "sha256:" + "a" * 64,
        "writer_quiescence": "verified",
        "unresolved_exposure_usd": "0",
        "reviewed_at_utc": "2026-10-31T14:30:00Z",
    }


def _carryover():
    return {
        "kind": "conservative_pre_r1_carryover",
        "amount_usd": "0.0001464",
        "currency": "USD",
        "original_date_scope": "legacy pilot records; retain original dates",
        "account_scope": "owner-account",
        "key_scope": "sha256:" + "a" * 64,
        "evidence_sha256": "e" * 64,
        "review_reference": "R1-REVIEW-20261031",
        "recorded_at_utc": "2026-10-31T14:30:00Z",
    }


def test_reviewed_migration_is_append_only_idempotent_and_counts_carryover(tmp_path, monkeypatch):
    path = tmp_path / "existing-r1.sqlite3"
    registry = tmp_path / "registry.json"
    _existing_unbound_r1(path)
    monkeypatch.setattr("patent_to_pilot.providers.ledger_registry.default_registry_path", lambda _: registry)
    monkeypatch.setattr("patent_to_pilot.providers.local_epoch.active", lambda: False)
    first = migrate_reviewed_r1_history(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, review=_review(), carryover=_carryover(), registry_path=registry)
    second = migrate_reviewed_r1_history(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, review=_review(), carryover=_carryover(), registry_path=registry)
    assert first == second
    budget = Round1ProjectBudget(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME)
    try:
        snapshot = budget.snapshot()
        assert snapshot["historical_carryover_nano_usd"] == 146_400
        assert snapshot["actual_nano_usd"] == 146_400
        assert snapshot["committed_nano_usd"] == 146_400
        assert snapshot["remaining_to_admission_nano_usd"] == 7_000_000_000 - 146_400
        assert budget.db.execute("SELECT COUNT(*) FROM budget_pre_r1_carryover").fetchone()[0] == 1
    finally:
        budget.close()
    refreshed = Round1ProjectBudget(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256="b" * 64, pricing_snapshot_utc="2026-10-31T15:00:00Z")
    try:
        assert refreshed.snapshot()["historical_carryover_nano_usd"] == 146_400
    finally:
        refreshed.close()


def test_migration_rejects_unverified_quiescence_without_mutation(tmp_path, monkeypatch):
    path = tmp_path / "existing-r1.sqlite3"
    registry = tmp_path / "registry.json"
    _existing_unbound_r1(path)
    monkeypatch.setattr("patent_to_pilot.providers.ledger_registry.default_registry_path", lambda _: registry)
    review = _review() | {"writer_quiescence": "unknown"}
    with pytest.raises(ValueError, match="complete and quiescent"):
        migrate_reviewed_r1_history(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, review=review, carryover=_carryover(), registry_path=registry)
    assert not registry.exists()
    with sqlite3.connect(path) as db:
        assert db.execute("SELECT COUNT(*) FROM budget_history_anchor").fetchone()[0] == 0 if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_history_anchor'").fetchone() else True


def test_migration_rejects_mock_namespace_and_does_not_promote_fixture(tmp_path):
    path = tmp_path / "mock.sqlite3"
    budget = Round1ProjectBudget(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, namespace="mock")
    budget.close()
    with pytest.raises(CanonicalLedgerError, match="mock promotion"):
        migrate_reviewed_r1_history(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, review=_review(), carryover=_carryover(), registry_path=tmp_path / "registry.json")


def test_live_transport_requires_reviewed_carryover(tmp_path, monkeypatch):
    path = tmp_path / "canonical.sqlite3"
    digest = _existing_unbound_r1(path)
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE budget_history_anchor(review_json TEXT NOT NULL)")
        review = _review()
        db.execute("INSERT INTO budget_history_anchor VALUES(?)", (json.dumps(review),))
    registry = tmp_path / "registry.json"
    monkeypatch.setattr("patent_to_pilot.providers.ledger_registry.default_registry_path", lambda _: registry)
    monkeypatch.setattr("patent_to_pilot.providers.local_epoch.active", lambda: False)
    register_canonical_ledger(path, authorization_id=R1_AUTHORIZATION_ID, policy_hash=digest, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, registry_path=registry, ledger_id=EXPECTED_LEDGER_ID)
    # A canonical journal without the separately reviewed carryover remains offline-only.
    budget = Round1ProjectBudget(path, model_provider_map={MODEL: PROVIDER}, pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME)
    try:
        from patent_to_pilot.providers import MockHTTPTransport, ProviderRequest
        from patent_to_pilot.providers.project_budget import BudgetedTransport
        from patent_to_pilot.providers.round1 import build_round1_config, request_payload_hash
        config = build_round1_config(budget.policy, phase="canary", model=MODEL, max_price={"prompt": 0.08, "completion": 0.28}, live_enabled=True)
        request = ProviderRequest(prompt="synthetic", input_tokens_estimate=1, max_output_tokens=1, cost_upper_bound_usd=0.01)
        wrapped = BudgetedTransport(MockHTTPTransport([]), budget, {
            "attempt_id": "live-gate", "phase": "canary", "payload_sha256": request_payload_hash(config, request),
            "upper_bound_usd": 0.01, "bound_verified": True, "data_class": "public",
        })
        with pytest.raises(Exception, match="carryover"):
            wrapped.send(config=config, request=request)
    finally:
        budget.close()
