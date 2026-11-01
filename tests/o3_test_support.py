"""Authored fake canonical history for offline tests; never use for recovery."""
from datetime import datetime, timezone
import json
import sqlite3

from patent_to_pilot.providers.history_review import history_digest
from patent_to_pilot.providers.round1 import Round1ProjectBudget, R1_AUTHORIZATION_ID

MODEL = "qwen/qwen3-32b"
PROVIDER = "DeepInfra"
PRICE_HASH = "a" * 64
PRICE_TIME = "2026-10-31T00:00:00Z"


def reviewed_fixture(path, *, anchor=True):
    budget = Round1ProjectBudget(path, model_provider_map={MODEL: PROVIDER},
        pricing_snapshot_sha256=PRICE_HASH, pricing_snapshot_utc=PRICE_TIME, namespace="mock")
    digest = budget.policy_hash
    budget.close()
    ledger_id = R1_AUTHORIZATION_ID + ":canonical"
    with sqlite3.connect(path) as db:
        # Test fixture only: production has no mock-to-live promotion API.
        db.execute("UPDATE budget_ledger_meta SET namespace='canonical',ledger_id=?", (ledger_id,))
        if anchor:
            db.execute("CREATE TABLE budget_history_anchor(review_json TEXT NOT NULL)")
            review = {"authorization_id": R1_AUTHORIZATION_ID, "ledger_id": ledger_id,
                "status": "reviewed_all_attempts", "baseline_count": 0,
                "baseline_sha256": history_digest([]), "export_sha256": "f" * 64,
                "review_reference": "SYNTHETIC-TEST-ONLY", "account_scope": "fixture-account", "key_scope": "fixture-key"}
            db.execute("INSERT INTO budget_history_anchor VALUES(?)", (json.dumps(review),))
    return digest


def credit(*, amount=10, at=None, **updates):
    return {"format": "ptp-openrouter-credit-snapshot-v2", "provider": "openrouter",
        "source": "owner_sanitized_snapshot", "as_of_utc": at or datetime.now(timezone.utc).isoformat(),
        "remaining_credits_usd": amount, "authorization_id": R1_AUTHORIZATION_ID,
        "account_scope": "fixture-account", "key_scope": "fixture-key", "currency": "USD",
        "key_remaining_usd": amount, "key_limit_unlimited": False, **updates}
