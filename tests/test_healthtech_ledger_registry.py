from __future__ import annotations

import pytest

from patent_to_pilot.providers.ledger_registry import (
    CanonicalLedgerError,
    default_registry_path,
    register_canonical_ledger,
    resolve_canonical_ledger,
)
from patent_to_pilot.providers.round1 import Round1ProjectBudget


MODEL = "qwen/qwen3-32b"
PROVIDER = "DeepInfra"
PRICE_HASH = "a" * 64
PRICE_TIME = "2026-10-31T00:00:00Z"
POLICY_HASH = "b" * 64
AUTH = "PTP-HT-OR-R1-20261028-USD8"


def test_registry_binds_one_existing_path_and_rejects_substitution(tmp_path):
    ledger = tmp_path / "existing.sqlite3"
    ledger.write_bytes(b"not-yet-opened")
    registry = tmp_path / "registry.json"
    binding = register_canonical_ledger(
        ledger,
        authorization_id=AUTH,
        policy_hash=POLICY_HASH,
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
        registry_path=registry,
    )
    assert binding.ledger_path == ledger.resolve()
    assert resolve_canonical_ledger(
        authorization_id=AUTH,
        policy_hash=POLICY_HASH,
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
        registry_path=registry,
    ) == binding
    with pytest.raises(CanonicalLedgerError, match="not the registered canonical ledger"):
        resolve_canonical_ledger(
            authorization_id=AUTH,
            policy_hash=POLICY_HASH,
            pricing_snapshot_sha256=PRICE_HASH,
            pricing_snapshot_utc=PRICE_TIME,
            requested_path=tmp_path / "substitute.sqlite3",
            registry_path=registry,
        )


def test_registry_does_not_rebind_existing_authorization(tmp_path):
    first = tmp_path / "first.sqlite3"
    second = tmp_path / "second.sqlite3"
    first.write_bytes(b"journal")
    second.write_bytes(b"journal")
    registry = tmp_path / "registry.json"
    register_canonical_ledger(
        first,
        authorization_id=AUTH,
        policy_hash=POLICY_HASH,
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
        registry_path=registry,
    )
    with pytest.raises(CanonicalLedgerError, match="already bound"):
        register_canonical_ledger(
            second,
            authorization_id=AUTH,
            policy_hash=POLICY_HASH,
            pricing_snapshot_sha256=PRICE_HASH,
            pricing_snapshot_utc=PRICE_TIME,
            registry_path=registry,
        )


def test_round1_mock_namespace_is_explicit_and_shared(tmp_path):
    path = tmp_path / "mock.sqlite3"
    first = Round1ProjectBudget(
        path,
        model_provider_map={MODEL: PROVIDER},
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
        namespace="mock",
    )
    second = Round1ProjectBudget(
        path,
        model_provider_map={MODEL: PROVIDER},
        pricing_snapshot_sha256=PRICE_HASH,
        pricing_snapshot_utc=PRICE_TIME,
        namespace="mock",
    )
    try:
        assert first.snapshot()["ledger_id"] == second.snapshot()["ledger_id"]
        assert first.snapshot()["ledger_namespace"] == "mock"
    finally:
        first.close()
        second.close()


def test_default_registry_is_worktree_independent_and_live_missing_registry_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "appdata"))
    first_root = tmp_path / "worktree-a"
    second_root = tmp_path / "worktree-b"
    first_root.mkdir()
    second_root.mkdir()
    monkeypatch.chdir(first_root)
    first = default_registry_path(AUTH)
    monkeypatch.chdir(second_root)
    second = default_registry_path(AUTH)
    assert first == second
    missing = tmp_path / "would-be-created.sqlite3"
    with pytest.raises(CanonicalLedgerError, match="registry is missing"):
        Round1ProjectBudget(
            missing,
            model_provider_map={MODEL: PROVIDER},
            pricing_snapshot_sha256=PRICE_HASH,
            pricing_snapshot_utc=PRICE_TIME,
            namespace="canonical",
        )
    assert not missing.exists()
