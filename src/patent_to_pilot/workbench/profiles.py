"""Persistent provider profiles, connection checks and the request ledger (G02).

Profiles live in the Workbench store. Secrets never do: a profile holds only the NAME of an environment variable.
Every network request a client makes (ok, failed or blocked) is appended to ``provider_usage``. Paid-route
requests are counted against the profile's ``max_requests`` cap across restarts.
"""
from __future__ import annotations

import hashlib
import json

from patent_to_pilot.workbench.providers import (ProviderClient, ProviderError, ProviderProfile, TEMPLATES,
                                                 connection_check)
from patent_to_pilot.workbench.store import Store, dumps, utc_now


def config_sha(profile: ProviderProfile) -> str:
    return hashlib.sha256(dumps(profile.to_dict()).encode("utf-8")).hexdigest()


class ProviderRegistry:
    def __init__(self, store: Store) -> None:
        self.store = store

    # ---------------- profiles
    def save(self, data: dict) -> dict:
        if not isinstance(data, dict):
            raise ProviderError("config", "profile must be a JSON object")
        profile = ProviderProfile.from_dict(data)
        now = utc_now()
        with self.store.tx() as con:
            row = con.execute("SELECT created_at FROM provider_profiles WHERE profile_id=?",
                              (profile.profile_id,)).fetchone()
            con.execute("INSERT OR REPLACE INTO provider_profiles VALUES (?,?,?,?,?,?)",
                        (profile.profile_id, profile.role, profile.adapter, dumps(profile.to_dict()),
                         row["created_at"] if row else now, now))
        return self.describe(profile.profile_id)

    def get(self, profile_id: str) -> ProviderProfile:
        with self.store.read() as con:
            row = con.execute("SELECT config_json FROM provider_profiles WHERE profile_id=?", (profile_id,)).fetchone()
        if not row:
            raise ProviderError("config", f"provider profile {profile_id} not found")
        return ProviderProfile.from_dict(json.loads(row["config_json"]))

    def delete(self, profile_id: str) -> dict:
        self.get(profile_id)
        with self.store.tx() as con:
            used = con.execute("SELECT project_id FROM project_settings WHERE embedding_profile_id=?",
                               (profile_id,)).fetchone()
            if used:
                raise ProviderError("config", f"profile is the embedding profile of project {used['project_id']}; "
                                              "switch that project to lexical mode first")
            con.execute("DELETE FROM provider_profiles WHERE profile_id=?", (profile_id,))
        return {"deleted": profile_id}

    def describe(self, profile_id: str) -> dict:
        p = self.get(profile_id)
        d = p.public()
        d["last_check"] = self.last_check(profile_id)
        d["status"] = self.status(profile_id, p)
        d["requests_counted"] = self.usage_count(profile_id)
        return d

    def list(self) -> list[dict]:
        with self.store.read() as con:
            ids = [r[0] for r in con.execute("SELECT profile_id FROM provider_profiles ORDER BY role, profile_id")]
        return [self.describe(i) for i in ids]

    @staticmethod
    def templates() -> list[dict]:
        return [dict(t) for t in TEMPLATES]

    # ---------------- checks and status
    def last_check(self, profile_id: str) -> dict | None:
        with self.store.read() as con:
            r = con.execute("SELECT * FROM provider_checks WHERE profile_id=? ORDER BY rowid DESC LIMIT 1",
                            (profile_id,)).fetchone()
        if not r:
            return None
        return {"overall": r["overall"], "checked_at": r["checked_at"], "config_sha256": r["config_sha256"],
                **json.loads(r["result_json"])}

    def status(self, profile_id: str, profile: ProviderProfile | None = None) -> str:
        """unchecked | ready | blocked | unavailable | failed | changed_since_check"""
        profile = profile or self.get(profile_id)
        last = self.last_check(profile_id)
        if last is None:
            return "unchecked"
        if last["config_sha256"] != config_sha(profile):
            return "changed_since_check"
        return last["overall"]

    def is_ready(self, profile_id: str) -> bool:
        return self.status(profile_id) == "ready"

    def check(self, profile_id: str) -> dict:
        profile = self.get(profile_id)
        result = connection_check(self.client(profile_id, profile))
        with self.store.tx() as con:
            con.execute("INSERT INTO provider_checks VALUES (?,?,?,?,?)",
                        (profile_id, config_sha(profile), result["overall"],
                         dumps({"items": result["items"], "facts": result["facts"]}), utc_now()))
        return self.describe(profile_id)

    # ---------------- ledger
    def ledger(self, event: dict) -> None:
        with self.store.tx() as con:
            con.execute("INSERT INTO provider_usage VALUES (?,?,?,?,?,?,?,?)",
                        (event["profile_id"], event["operation"], int(bool(event["billable"])), event["status"],
                         None if event["usage"] is None else dumps(event["usage"]), event["latency_ms"],
                         None if event["detail"] is None else str(event["detail"])[:500], utc_now()))

    def usage_count(self, profile_id: str) -> int:
        """Attempted billable requests (blocked and missing-credential attempts never left the machine)."""
        with self.store.read() as con:
            return con.execute("SELECT COUNT(*) FROM provider_usage WHERE profile_id=? AND billable=1 AND status "
                               "NOT IN ('blocked','missing_credential')", (profile_id,)).fetchone()[0]

    def usage(self, profile_id: str, limit: int = 50) -> list[dict]:
        with self.store.read() as con:
            rows = con.execute("SELECT * FROM provider_usage WHERE profile_id=? ORDER BY rowid DESC LIMIT ?",
                               (profile_id, limit)).fetchall()
        return [{**dict(r), "usage_json": None, "usage": json.loads(r["usage_json"]) if r["usage_json"] else None,
                 "cost_usd": "unknown"} for r in rows]

    def client(self, profile_id: str, profile: ProviderProfile | None = None) -> ProviderClient:
        profile = profile or self.get(profile_id)
        return ProviderClient(profile, ledger=self.ledger, used_requests=self.usage_count(profile_id))
