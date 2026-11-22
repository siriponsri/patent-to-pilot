"""Shared, transaction-safe budget ledger for paid model calls (owner task P0-T05).

One SQLite file holds every envelope, every owner approval record and one row per attempted paid request, for all callers
on this machine (the G03 A3 research caller and the Workbench provider client). Stdlib only.

Dispatch rule (checked inside one ``BEGIN IMMEDIATE`` transaction, so concurrent threads and processes are serialised):

    settled cost + outstanding reservations + unresolved unknown-cost reservations + this attempt's maximum
        <= operational limit of the envelope

* The operational limit is the stop-and-report threshold when the envelope has one (E1: USD 6.00), else the hard limit
  (E1R: USD 50). Going past a stop threshold needs an explicit ``continue_past_stop`` approval record; the hard limit can
  never be passed.
* Every attempt (first tries and retries alike) is one attempted request and counts against ``max_requests``.
* Each attempt reserves a conservative maximum cost before any socket is opened, then is ``settle``d with the provider's
  reported cost, ``release``d when the request certainly was not billed (an HTTP error answer, or a connection refused
  before sending), or marked ``unknown`` (timeout after send, response without a cost). An unknown entry keeps its
  reservation and PAUSES all further dispatch on the envelope until it is ``reconcile``d with an evidence reference.
  Missing cost is never treated as zero.
* Reservations survive restarts (the row stays ``reserved``); ``recover_stale`` turns reservations older than a lease into
  ``unknown`` so a crashed process cannot hide spend.
* An envelope dispatches only with an approval record. E1 is seeded with its recorded owner approval (D9). E1R is
  configured but carries no approval, so it refuses dispatch until ``approve`` is called with the owner's evidence. An
  approved envelope that ``supersedes`` another stops the older one from dispatching; ``includes`` makes the older
  envelope's spend count inside the newer one (E1R is cumulative including E1 spend).

The ledger lives OUTSIDE the git repository: ``%PTP_BUDGET_LEDGER%`` if set, else
``%LOCALAPPDATA%/PatentToPilot/budget/ledger.sqlite3`` (``~/.local/share/...`` elsewhere). A path inside a git work tree is
refused. No credential is ever passed to or stored by this module.

CLI (no network):
  python -m patent_to_pilot.budget.ledger status [--ledger PATH]
  python -m patent_to_pilot.budget.ledger approve --envelope E1R --evidence "<where the owner said it>" [--kind dispatch]
  python -m patent_to_pilot.budget.ledger reconcile --entry ID --cost-usd 0.0012 --evidence "<generation lookup ...>"
  python -m patent_to_pilot.budget.ledger recover-stale [--max-age-s 900]
  python -m patent_to_pilot.budget.ledger import-workbench --store PATH/workbench.sqlite3
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

SCHEMA_VERSION = "ptp-budget-ledger-v1"
EPS = 1e-12

# --------------------------------------------------------------------------------------------- prices
# USD per million tokens. RESERVATION prices are the MAXIMUM over all endpoints OpenRouter listed for the model on
# 2026-11-22 (read with the free list-model-endpoints catalogue tool), because OpenRouter may route a request to any of
# them unless the request pins the provider. LIST prices are the owner's planning prices (cheapest standard endpoint).
# ``tiers`` apply when the prompt-token upper bound reaches ``min_prompt_tokens``.
PRICE_SNAPSHOT = {"checked": "2026-11-22", "source": "OpenRouter list-model-endpoints (max over endpoints)"}
RESERVATION_PRICES: dict[str, dict[str, dict]] = {
    "openrouter": {
        "qwen/qwen3-32b": {"input": 0.14, "output": 0.57},
        "deepseek/deepseek-v4-flash-0731": {"input": 0.44, "output": 1.32},
        "google/gemini-2.5-flash-lite": {"input": 0.18, "output": 0.72},
        "qwen/qwen3.7-flash": {"input": 0.03, "output": 0.13,
                               "tiers": [{"min_prompt_tokens": 32000, "input": 0.1, "output": 0.4},
                                         {"min_prompt_tokens": 256000, "input": 0.2, "output": 0.8}]},
        "anthropic/claude-haiku-5.5": {"input": 0.1, "output": 0.5,
                                       "tiers": [{"min_prompt_tokens": 100000, "input": 0.5, "output": 2.5}]},
    },
}
LIST_PRICES: dict[str, dict[str, dict]] = {
    "openrouter": {
        "qwen/qwen3-32b": {"input": 0.08, "output": 0.28},
        "deepseek/deepseek-v4-flash-0731": {"input": 0.0419, "output": 0.30},
        "google/gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
        "qwen/qwen3.7-flash": {"input": 0.03, "output": 0.13},
        "anthropic/claude-haiku-5.5": {"input": 0.10, "output": 0.50},
    },
}
PROMPT_OVERHEAD_TOKENS = 256      # chat-template/special tokens on top of the UTF-8 byte bound


def _price_overrides() -> dict:
    p = os.environ.get("PTP_BUDGET_PRICES")
    if not p:
        return {}
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def price_for(provider: str, model: str) -> dict | None:
    """Reservation price for (provider, model), or None when unknown (an unknown price is never zero)."""
    over = _price_overrides().get(provider, {}).get(model)
    if over is not None:
        return over
    return RESERVATION_PRICES.get(provider, {}).get(model)


def estimate_chat_max_usd(price: dict | None, input_bytes: int, max_output_tokens: int, *,
                          overhead_tokens: int = PROMPT_OVERHEAD_TOKENS, margin: float = 1.0) -> float | None:
    """Conservative maximum cost of one request.

    Prompt tokens are bounded by the UTF-8 byte length of what is sent plus a template overhead (byte-level BPE and
    byte-fallback tokenisers never produce more tokens than bytes); completion tokens (reasoning included) are bounded
    by ``max_output_tokens``. Returns None when the price is unknown."""
    if not price:
        return None
    in_tok = max(0, int(input_bytes)) + max(0, int(overhead_tokens))
    pin, pout = float(price["input"]), float(price["output"])
    for t in sorted(price.get("tiers") or [], key=lambda t: t["min_prompt_tokens"]):
        if in_tok >= t["min_prompt_tokens"]:
            pin, pout = float(t["input"]), float(t["output"])
    usd = (in_tok * pin + max(0, int(max_output_tokens)) * pout) / 1_000_000 * float(margin)
    return usd if math.isfinite(usd) else None


def provider_for_endpoint(url: str) -> str:
    host = (urlsplit(url).hostname or "").lower()
    if host == "openrouter.ai" or host.endswith(".openrouter.ai"):
        return "openrouter"
    if host.endswith("opentyphoon.ai"):
        return "typhoon"
    if host == "api.anthropic.com":
        return "anthropic"
    return host or "unknown"


# --------------------------------------------------------------------------------------------- envelopes
@dataclass
class Envelope:
    envelope_id: str
    providers: list[str]
    hard_limit_usd: float
    max_requests: int
    stop_usd: float | None = None
    notify_usd: float | None = None
    includes: list[str] = field(default_factory=list)       # older envelopes whose spend counts inside this one
    supersedes: list[str] = field(default_factory=list)     # envelopes that stop dispatching once this one is approved
    scope_caps_usd: dict[str, float] = field(default_factory=dict)
    requires_approval: bool = True
    scope_text: str = ""
    source_ref: str = ""

    @classmethod
    def from_dict(cls, d: dict) -> "Envelope":
        return cls(**d)


DEFAULT_ENVELOPES = [
    Envelope("E1", ["openrouter"], hard_limit_usd=8.00, max_requests=35000, stop_usd=6.00, notify_usd=None,
             scope_caps_usd={"workbench": 0.20},
             scope_text="G03 amendment 3 (A3) LLM query expansion; Workbench profile checks <= USD 0.20",
             source_ref="docs/maintenance/OWNER-DECISIONS-20261122.md D9; owner-note-22112026 config/budget_plan.json"),
    Envelope("E1R", ["openrouter", "typhoon"], hard_limit_usd=50.00, max_requests=100000, stop_usd=None,
             notify_usd=40.00, includes=["E1"], supersedes=["E1"], scope_caps_usd={"workbench": 0.20},
             scope_text="A3r1 plus bounded structural expansion / Thai checks (owner-note-22112026). Cumulative, "
                        "including E1 spend. No GPU rental. PROPOSED, NOT APPROVED until an approval record exists.",
             source_ref="owner-note-22112026 03_BUDGET_AND_AUTONOMY.md; config/budget_plan.json (PENDING_OWNER_APPROVAL)"),
]
SEED_APPROVALS = [
    {"envelope_id": "E1", "kind": "dispatch", "approved_by": "owner",
     "evidence_ref": 'docs/maintenance/OWNER-DECISIONS-20261122.md D9 (owner in chat 22 Nov 2026: "Approve E1 USD 8")',
     "note": "seeded by ledger v1"},
]
SEED_HISTORICAL = [
    {"import_key": "g03-a3r0-format-smoke-20261122", "envelope_id": "E1", "scope": "g03_a3", "provider": "openrouter",
     "model": "4 models (A3r0 panel)", "requests": 4, "cost_usd": 0.00064223,
     "detail": {"source": "docs/healthtech/research/g03-dev/g03-dev-a3-spend.json",
                "basis": "credits delta 1.63501153 - 1.6343693 (total, not per call; not independently re-billed)",
                "via": "OpenRouter MCP send-message tool, outside the caller JSONL ledger",
                "generation_ids": ["gen-1795329088-PoXlZfInAnenuBGWdJQQ", "gen-1795329113-gGBoYNxyz1mZwI3WORa8",
                                   "gen-1795329115-m11YdZ3VWFCW1tg0TNR7", "gen-1795329125-DNL7dY9dMDeHWnCBac5N"]}},
]


class BudgetRefused(Exception):
    """reason: not_approved | superseded | provider_not_covered | price_unknown | paused_unknown_cost |
    usd_limit | stop_threshold | request_cap | scope_cap | tag_cap | run_cap | unknown_envelope"""

    def __init__(self, reason: str, message: str, state: dict | None = None) -> None:
        super().__init__(message)
        self.reason = reason
        self.state = state or {}


@dataclass
class Reservation:
    entry_id: str
    envelope_id: str
    reserved_usd: float
    attempt: int
    limit_usd: float
    committed_after: float
    notify: bool = False


def default_ledger_path() -> Path:
    if os.environ.get("PTP_BUDGET_LEDGER"):
        return Path(os.environ["PTP_BUDGET_LEDGER"])
    base = os.environ.get("LOCALAPPDATA") or str(Path.home() / ".local" / "share")
    return Path(base) / "PatentToPilot" / "budget" / "ledger.sqlite3"


def _inside_git_repo(path: Path) -> bool:
    p = path.resolve()
    for parent in [p.parent, *p.parent.parents]:
        if (parent / ".git").exists():
            return True
    return False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS envelopes (envelope_id TEXT PRIMARY KEY, config_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS approvals (
  approval_id INTEGER PRIMARY KEY AUTOINCREMENT, envelope_id TEXT NOT NULL, kind TEXT NOT NULL,
  evidence_ref TEXT NOT NULL, approved_by TEXT NOT NULL, note TEXT, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS entries (
  entry_id TEXT PRIMARY KEY, envelope_id TEXT NOT NULL, scope TEXT NOT NULL, tag TEXT, provider TEXT, model TEXT,
  status TEXT NOT NULL CHECK (status IN ('reserved','settled','released','unknown')),
  requests INTEGER NOT NULL DEFAULT 1, attempt INTEGER NOT NULL DEFAULT 0,
  reserved_usd REAL NOT NULL, cost_usd REAL, outcome TEXT, generation_id TEXT, import_key TEXT UNIQUE,
  detail_json TEXT, pid INTEGER, created_ts REAL NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS entries_env ON entries (envelope_id, status);
CREATE TABLE IF NOT EXISTS events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT, envelope_id TEXT, kind TEXT NOT NULL, dedupe_key TEXT UNIQUE,
  detail_json TEXT, created_at TEXT NOT NULL);
"""


class BudgetLedger:
    def __init__(self, path: str | Path | None = None, *, allow_in_repo: bool = False, seed: bool = True) -> None:
        self.path = Path(path) if path else default_ledger_path()
        if not allow_in_repo and _inside_git_repo(self.path):
            raise ValueError(f"budget ledger {self.path} is inside a git work tree; keep it outside the repository "
                             "(set PTP_BUDGET_LEDGER)")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = self._connect()
        try:
            con.execute("PRAGMA journal_mode=WAL")
            con.executescript(SCHEMA)
        finally:
            con.close()
        if seed:
            self.seed_defaults()

    # ------------------------------------------------------------------ plumbing
    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), timeout=60.0, isolation_level=None)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA busy_timeout=60000")
        con.execute("PRAGMA synchronous=FULL")
        return con

    @contextmanager
    def _tx(self, immediate: bool = True):
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            try:
                yield con
            except BaseException:
                con.execute("ROLLBACK")
                raise
            else:
                con.execute("COMMIT")
        finally:
            con.close()

    @staticmethod
    def _envs(con) -> dict[str, Envelope]:
        return {r["envelope_id"]: Envelope.from_dict(json.loads(r["config_json"]))
                for r in con.execute("SELECT envelope_id, config_json FROM envelopes")}

    @staticmethod
    def _approved(con, envelope_id: str, kind: str = "dispatch") -> bool:
        return con.execute("SELECT 1 FROM approvals WHERE envelope_id=? AND kind=? LIMIT 1",
                           (envelope_id, kind)).fetchone() is not None

    def _superseded_by(self, con, envs: dict[str, Envelope], envelope_id: str) -> str | None:
        for e in envs.values():
            if envelope_id in e.supersedes and self._approved(con, e.envelope_id):
                return e.envelope_id
        return None

    @staticmethod
    def _family(envs: dict[str, Envelope], envelope_id: str) -> list[str]:
        out, todo = [], [envelope_id]
        while todo:
            x = todo.pop()
            if x in out:
                continue
            out.append(x)
            if x in envs:
                todo.extend(envs[x].includes)
        return out

    @staticmethod
    def _totals(con, family: list[str], scope: str | None = None, tag: str | None = None) -> dict:
        q = ("SELECT COALESCE(SUM(CASE WHEN status='settled' THEN cost_usd ELSE 0 END),0) AS spent,"
             " COALESCE(SUM(CASE WHEN status='reserved' THEN reserved_usd ELSE 0 END),0) AS reserved,"
             " COALESCE(SUM(CASE WHEN status='unknown' THEN reserved_usd ELSE 0 END),0) AS unknown_usd,"
             " COALESCE(SUM(CASE WHEN status='unknown' THEN 1 ELSE 0 END),0) AS unknown_n,"
             " COALESCE(SUM(requests),0) AS attempted FROM entries WHERE envelope_id IN (%s)"
             % ",".join("?" * len(family)))
        args: list = list(family)
        if scope is not None:
            q += " AND scope=?"
            args.append(scope)
        if tag is not None:
            q += " AND tag=?"
            args.append(tag)
        r = con.execute(q, args).fetchone()
        d = {k: r[k] for k in ("spent", "reserved", "unknown_usd", "unknown_n", "attempted")}
        d["committed"] = d["spent"] + d["reserved"] + d["unknown_usd"]
        return d

    def _limit(self, con, env: Envelope) -> tuple[float, str]:
        if env.stop_usd is not None and not self._approved(con, env.envelope_id, "continue_past_stop"):
            return min(env.stop_usd, env.hard_limit_usd), "stop_threshold"
        return env.hard_limit_usd, "usd_limit"

    def _event(self, con, envelope_id: str | None, kind: str, detail: dict, dedupe_key: str | None = None) -> bool:
        cur = con.execute("INSERT OR IGNORE INTO events (envelope_id, kind, dedupe_key, detail_json, created_at) "
                          "VALUES (?,?,?,?,?)", (envelope_id, kind, dedupe_key, json.dumps(detail, sort_keys=True),
                                                 _now()))
        return cur.rowcount == 1

    # ------------------------------------------------------------------ configuration
    def seed_defaults(self) -> None:
        with self._tx() as con:
            if con.execute("SELECT value FROM meta WHERE key='schema'").fetchone() is None:
                con.execute("INSERT INTO meta VALUES ('schema', ?)", (SCHEMA_VERSION,))
            for env in DEFAULT_ENVELOPES:
                con.execute("INSERT OR IGNORE INTO envelopes VALUES (?,?,?)",
                            (env.envelope_id, json.dumps(asdict(env), sort_keys=True), _now()))
            for a in SEED_APPROVALS:
                key = f"seed-approval:{a['envelope_id']}:{a['kind']}"
                if con.execute("SELECT 1 FROM meta WHERE key=?", (key,)).fetchone() is None:
                    con.execute("INSERT INTO approvals (envelope_id, kind, evidence_ref, approved_by, note, created_at)"
                                " VALUES (?,?,?,?,?,?)", (a["envelope_id"], a["kind"], a["evidence_ref"],
                                                          a["approved_by"], a["note"], _now()))
                    con.execute("INSERT INTO meta VALUES (?, ?)", (key, _now()))
        for h in SEED_HISTORICAL:
            self.import_historical(**h)

    def put_envelope(self, env: Envelope, replace: bool = False) -> None:
        with self._tx() as con:
            verb = "INSERT OR REPLACE" if replace else "INSERT OR IGNORE"
            con.execute(f"{verb} INTO envelopes VALUES (?,?,?)",
                        (env.envelope_id, json.dumps(asdict(env), sort_keys=True), _now()))

    def envelopes(self) -> dict[str, Envelope]:
        with self._tx(immediate=False) as con:
            return self._envs(con)

    def approve(self, envelope_id: str, *, evidence_ref: str, approved_by: str = "owner", kind: str = "dispatch",
                note: str = "") -> None:
        """Record an owner approval. ``evidence_ref`` must say where the owner gave it (never inferred by an agent)."""
        if kind not in ("dispatch", "continue_past_stop"):
            raise ValueError("kind must be 'dispatch' or 'continue_past_stop'")
        if not (evidence_ref or "").strip():
            raise ValueError("an approval needs an evidence reference")
        with self._tx() as con:
            if envelope_id not in self._envs(con):
                raise BudgetRefused("unknown_envelope", f"envelope {envelope_id} is not configured")
            con.execute("INSERT INTO approvals (envelope_id, kind, evidence_ref, approved_by, note, created_at) "
                        "VALUES (?,?,?,?,?,?)", (envelope_id, kind, evidence_ref.strip(), approved_by, note, _now()))
            self._event(con, envelope_id, f"approval_{kind}", {"evidence_ref": evidence_ref, "by": approved_by})

    # ------------------------------------------------------------------ dispatch
    def dispatch_envelope(self, provider: str) -> str:
        """The approved, non-superseded envelope covering ``provider``."""
        with self._tx(immediate=False) as con:
            envs = self._envs(con)
            ok = [e.envelope_id for e in envs.values() if provider in e.providers and self._approved(con, e.envelope_id)
                  and self._superseded_by(con, envs, e.envelope_id) is None]
        if not ok:
            raise BudgetRefused("provider_not_covered", f"no approved budget envelope covers provider {provider!r}")
        return sorted(ok)[0]

    def reserve(self, provider: str, est_usd: float | None, *, scope: str, envelope_id: str | None = None,
                model: str | None = None, tag: str | None = None, attempt: int = 0,
                tag_usd_cap: float | None = None, tag_max_requests: int | None = None,
                run_usd_cap: float | None = None, run_max_requests: int | None = None,
                detail: dict | None = None) -> Reservation:
        """Atomically reserve one attempted request and its maximum cost, or raise BudgetRefused."""
        if est_usd is None or not isinstance(est_usd, (int, float)) or not math.isfinite(est_usd) or est_usd < 0:
            raise BudgetRefused("price_unknown", f"no conservative cost bound for {provider}/{model}; an unknown "
                                                 "price is not zero, so the request is not dispatched")
        if envelope_id is None:
            envelope_id = self.dispatch_envelope(provider)
        refusal: list[BudgetRefused] = []
        res = self._reserve_tx(provider, est_usd, scope, envelope_id, model, tag, attempt, tag_usd_cap,
                               tag_max_requests, run_usd_cap, run_max_requests, detail, refusal)
        if refusal:              # raised after COMMIT so the stop-and-report event is kept
            raise refusal[0]
        return res

    def _reserve_tx(self, provider, est_usd, scope, envelope_id, model, tag, attempt, tag_usd_cap, tag_max_requests,
                    run_usd_cap, run_max_requests, detail, refusal) -> Reservation | None:
        with self._tx() as con:
            envs = self._envs(con)
            env = envs.get(envelope_id)
            if env is None:
                raise BudgetRefused("unknown_envelope", f"envelope {envelope_id} is not configured")
            if env.requires_approval and not self._approved(con, envelope_id):
                raise BudgetRefused("not_approved", f"envelope {envelope_id} has no owner approval record; it is "
                                                    "configured but disabled for dispatch")
            sup = self._superseded_by(con, envs, envelope_id)
            if sup:
                raise BudgetRefused("superseded", f"envelope {envelope_id} is superseded by approved {sup}")
            if provider not in env.providers:
                raise BudgetRefused("provider_not_covered", f"envelope {envelope_id} does not cover {provider!r}")
            fam = self._family(envs, envelope_id)
            t = self._totals(con, fam)
            limit, limit_kind = self._limit(con, env)
            state = {"envelope": envelope_id, "spent_usd": round(t["spent"], 8), "reserved_usd": round(t["reserved"], 8),
                     "unknown_usd": round(t["unknown_usd"], 8), "unknown_entries": t["unknown_n"],
                     "attempted_requests": t["attempted"], "limit_usd": limit, "max_requests": env.max_requests,
                     "remaining_usd": round(limit - t["committed"], 8), "next_reservation_usd": est_usd}
            if t["unknown_n"]:
                raise BudgetRefused("paused_unknown_cost", f"dispatch paused on {envelope_id}: {t['unknown_n']} "
                                    "attempt(s) with unknown cost must be reconciled first", state)
            if t["committed"] + est_usd > limit + EPS:
                exc = BudgetRefused(limit_kind, f"{envelope_id}: committed USD {t['committed']:.6f} + next "
                                    f"{est_usd:.6f} would exceed USD {limit:.2f} ({limit_kind})", state)
                if limit_kind == "stop_threshold":
                    self._event(con, envelope_id, "stop_and_report", state, dedupe_key=f"{envelope_id}:stop")
                    refusal.append(exc)
                    return None
                raise exc
            if t["attempted"] + 1 > env.max_requests:
                raise BudgetRefused("request_cap", f"{envelope_id}: {t['attempted']} attempted requests; cap "
                                    f"{env.max_requests}", state)
            cap = env.scope_caps_usd.get(scope)
            if cap is not None:
                ts = self._totals(con, fam, scope=scope)
                if ts["committed"] + est_usd > cap + EPS:
                    raise BudgetRefused("scope_cap", f"scope {scope}: USD {ts['committed']:.6f} + {est_usd:.6f} > "
                                                     f"cap {cap}", state)
            if tag is not None and (tag_usd_cap is not None or tag_max_requests is not None):
                tt = self._totals(con, fam, tag=tag)
                if tag_usd_cap is not None and tt["committed"] + est_usd > tag_usd_cap + EPS:
                    raise BudgetRefused("tag_cap", f"{tag}: USD {tt['committed']:.6f} + {est_usd:.6f} > "
                                                   f"cap {tag_usd_cap}", state)
                if tag_max_requests is not None and tt["attempted"] + 1 > tag_max_requests:
                    raise BudgetRefused("tag_cap", f"{tag}: request cap {tag_max_requests} reached", state)
            if run_usd_cap is not None and t["committed"] + est_usd > run_usd_cap + EPS:
                raise BudgetRefused("run_cap", f"caller ceiling USD {run_usd_cap} reached", state)
            if run_max_requests is not None and t["attempted"] + 1 > run_max_requests:
                raise BudgetRefused("run_cap", f"caller ceiling of {run_max_requests} requests reached", state)
            entry_id = uuid.uuid4().hex
            now = _now()
            con.execute("INSERT INTO entries (entry_id, envelope_id, scope, tag, provider, model, status, requests, "
                        "attempt, reserved_usd, cost_usd, outcome, generation_id, import_key, detail_json, pid, "
                        "created_ts, created_at, updated_at) VALUES (?,?,?,?,?,?,'reserved',1,?,?,NULL,NULL,NULL,NULL,"
                        "?,?,?,?,?)", (entry_id, envelope_id, scope, tag, provider, model, int(attempt), float(est_usd),
                                       None if detail is None else json.dumps(detail, sort_keys=True), os.getpid(),
                                       time.time(), now, now))
            committed_after = t["committed"] + est_usd
            notify = False
            if env.notify_usd is not None and committed_after >= env.notify_usd - EPS:
                notify = self._event(con, envelope_id, "notify_threshold",
                                     {**state, "committed_after": committed_after, "notify_usd": env.notify_usd},
                                     dedupe_key=f"{envelope_id}:notify")
        return Reservation(entry_id, envelope_id, float(est_usd), int(attempt), limit, committed_after, notify)

    def _finish(self, entry_id: str, status: str, cost: float | None, outcome: str, generation_id: str | None,
                detail: dict | None, allowed_from: tuple[str, ...]) -> dict:
        with self._tx() as con:
            r = con.execute("SELECT * FROM entries WHERE entry_id=?", (entry_id,)).fetchone()
            if r is None:
                raise KeyError(entry_id)
            if r["status"] not in allowed_from:
                raise ValueError(f"entry {entry_id} is {r['status']}; cannot move to {status}")
            old = json.loads(r["detail_json"]) if r["detail_json"] else {}
            if detail:
                old.update(detail)
            con.execute("UPDATE entries SET status=?, cost_usd=?, outcome=?, generation_id=COALESCE(?, generation_id), "
                        "detail_json=?, updated_at=? WHERE entry_id=?",
                        (status, cost, outcome, generation_id, json.dumps(old, sort_keys=True) if old else None, _now(),
                         entry_id))
            if status == "settled" and cost is not None and cost > r["reserved_usd"] + EPS:
                self._event(con, r["envelope_id"], "overrun", {"entry_id": entry_id, "reserved_usd": r["reserved_usd"],
                                                               "cost_usd": cost, "model": r["model"]})
            if status == "unknown":
                self._event(con, r["envelope_id"], "unknown_cost_pause", {"entry_id": entry_id, "outcome": outcome,
                                                                          "model": r["model"]})
        return {"entry_id": entry_id, "status": status, "cost_usd": cost}

    def settle(self, entry_id: str, cost_usd: float | None, *, generation_id: str | None = None, outcome: str = "ok",
               detail: dict | None = None) -> dict:
        """Replace the reservation with the reported actual cost. A missing cost marks the entry unknown (pause)."""
        if cost_usd is None or not isinstance(cost_usd, (int, float)) or isinstance(cost_usd, bool) \
                or not math.isfinite(cost_usd) or cost_usd < 0:
            return self.mark_unknown(entry_id, outcome=f"{outcome}:cost_missing", detail=detail)
        return self._finish(entry_id, "settled", float(cost_usd), outcome, generation_id, detail, ("reserved",))

    def release(self, entry_id: str, *, outcome: str, detail: dict | None = None) -> dict:
        """The attempt certainly was not billed (error answer, or never sent): cost 0, still one attempted request."""
        return self._finish(entry_id, "released", 0.0, outcome, None, detail, ("reserved",))

    def mark_unknown(self, entry_id: str, *, outcome: str, detail: dict | None = None) -> dict:
        return self._finish(entry_id, "unknown", None, outcome, None, detail, ("reserved",))

    def reconcile(self, entry_id: str, cost_usd: float, *, evidence: str, generation_id: str | None = None) -> dict:
        """Resolve an unknown (or stale reserved) entry with an actual cost and where that number came from."""
        if not (evidence or "").strip():
            raise ValueError("reconciliation needs an evidence reference")
        if not isinstance(cost_usd, (int, float)) or not math.isfinite(cost_usd) or cost_usd < 0:
            raise ValueError("cost_usd must be a finite non-negative number")
        return self._finish(entry_id, "settled", float(cost_usd), "reconciled", generation_id,
                            {"reconciled_evidence": evidence, "reconciled_at": _now()}, ("unknown", "reserved"))

    def recover_stale(self, max_age_s: float = 900.0) -> int:
        """After a restart: reservations older than the lease can no longer be live; mark them unknown (pause)."""
        cutoff = time.time() - max_age_s
        with self._tx() as con:
            rows = con.execute("SELECT entry_id, envelope_id, model FROM entries WHERE status='reserved' AND "
                               "created_ts < ?", (cutoff,)).fetchall()
            for r in rows:
                con.execute("UPDATE entries SET status='unknown', outcome='stale_reservation_after_restart', "
                            "updated_at=? WHERE entry_id=?", (_now(), r["entry_id"]))
                self._event(con, r["envelope_id"], "unknown_cost_pause", {"entry_id": r["entry_id"],
                                                                          "outcome": "stale_reservation_after_restart"})
        return len(rows)

    # ------------------------------------------------------------------ history
    def import_historical(self, *, import_key: str, envelope_id: str, scope: str, provider: str, model: str,
                          requests: int, cost_usd: float | None, detail: dict | None = None,
                          status: str | None = None) -> bool:
        """Idempotently add spend that happened outside the ledger. Returns True when newly imported."""
        st = status or ("settled" if cost_usd is not None else "unknown")
        with self._tx() as con:
            if con.execute("SELECT 1 FROM entries WHERE import_key=?", (import_key,)).fetchone():
                return False
            now = _now()
            con.execute("INSERT INTO entries (entry_id, envelope_id, scope, tag, provider, model, status, requests, "
                        "attempt, reserved_usd, cost_usd, outcome, generation_id, import_key, detail_json, pid, "
                        "created_ts, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,0,?,?,?,NULL,?,?,NULL,?,?,?)",
                        (uuid.uuid4().hex, envelope_id, scope, None, provider, model, st, int(requests),
                         float(cost_usd or 0.0), cost_usd, "historical_import", import_key,
                         json.dumps(detail or {}, sort_keys=True), time.time(), now, now))
            self._event(con, envelope_id, "historical_import", {"import_key": import_key, "requests": requests,
                                                                "cost_usd": cost_usd})
        return True

    def import_workbench_usage(self, store_path: str | Path, envelope_id: str = "E1") -> dict:
        """Import paid remote Workbench requests recorded in a Workbench store before the ledger existed.

        Rows that already carry a ledger entry id (made through this ledger) are skipped, so nothing is counted twice.
        ok with a reported cost -> settled; ok without cost, timeout or bad response -> unknown (pause until
        reconciled); HTTP error answers and unreachable endpoints -> released (attempted, not billed)."""
        store_path = Path(store_path)
        out = {"store": str(store_path), "exists": store_path.exists(), "imported": 0, "skipped": 0}
        if not store_path.exists():
            return out
        src = sqlite3.connect(f"file:{store_path.as_posix()}?mode=ro", uri=True)
        src.row_factory = sqlite3.Row
        try:
            prof = {r["profile_id"]: json.loads(r["config_json"])
                    for r in src.execute("SELECT profile_id, config_json FROM provider_profiles")}
            rows = src.execute("SELECT rowid, * FROM provider_usage WHERE billable=1 AND status NOT IN "
                               "('blocked','missing_credential')").fetchall()
        finally:
            src.close()
        for r in rows:
            cfg = prof.get(r["profile_id"]) or {}
            host = (urlsplit(cfg.get("endpoint", "")).hostname or "").lower()
            if host in ("", "localhost") or host.startswith("127.") or host == "::1":
                out["skipped"] += 1
                continue
            usage = json.loads(r["usage_json"]) if r["usage_json"] else {}
            if usage.get("budget_entry_id"):
                out["skipped"] += 1
                continue
            cost = usage.get("cost_usd")
            if r["status"] == "ok":
                status = "settled" if isinstance(cost, (int, float)) else "unknown"
            elif str(r["status"]).startswith("http_") or r["status"] == "unreachable":
                status, cost = "released", 0.0
            else:
                status, cost = "unknown", None
            key = f"workbench:{store_path.resolve().as_posix()}:{r['rowid']}"
            if self.import_historical(import_key=key, envelope_id=envelope_id, scope="workbench",
                                      provider=provider_for_endpoint(cfg.get("endpoint", "")),
                                      model=cfg.get("model_id"), requests=1, cost_usd=cost, status=status,
                                      detail={"profile_id": r["profile_id"], "status": r["status"],
                                              "created_at": r["created_at"]}):
                out["imported"] += 1
        return out

    # ------------------------------------------------------------------ reporting
    def status(self, envelope_id: str) -> dict:
        with self._tx(immediate=False) as con:
            envs = self._envs(con)
            env = envs[envelope_id]
            fam = self._family(envs, envelope_id)
            t = self._totals(con, fam)
            limit, limit_kind = self._limit(con, env)
            q = ",".join("?" * len(fam))
            c = con.execute(
                "SELECT COALESCE(SUM(CASE WHEN status='settled' AND outcome NOT IN ('historical_import') THEN 1 ELSE 0 "
                "END),0) AS completed, COALESCE(SUM(CASE WHEN attempt>0 THEN 1 ELSE 0 END),0) AS retried, "
                "COALESCE(SUM(CASE WHEN status IN ('released','unknown') THEN 1 ELSE 0 END),0) AS failed, "
                "COALESCE(SUM(CASE WHEN status='settled' AND cost_usd>0 THEN requests ELSE 0 END),0) AS billed, "
                "COALESCE(SUM(CASE WHEN outcome='historical_import' THEN requests ELSE 0 END),0) AS historical "
                f"FROM entries WHERE envelope_id IN ({q})", fam).fetchone()
            approvals = [dict(a) for a in con.execute("SELECT envelope_id, kind, evidence_ref, approved_by, created_at "
                                                      "FROM approvals WHERE envelope_id=?", (envelope_id,))]
            sup = self._superseded_by(con, envs, envelope_id)
            unknown_ids = [r[0] for r in con.execute(
                f"SELECT entry_id FROM entries WHERE status='unknown' AND envelope_id IN ({q})", fam)]
            by_scope = {r["scope"]: round(r["usd"], 8) for r in con.execute(
                "SELECT scope, SUM(COALESCE(cost_usd,0)) + SUM(CASE WHEN status IN ('reserved','unknown') THEN "
                f"reserved_usd ELSE 0 END) AS usd FROM entries WHERE envelope_id IN ({q}) GROUP BY scope", fam)}
        approved = bool(approvals) or not env.requires_approval
        return {
            "envelope": envelope_id, "family": fam, "config": asdict(env),
            "approval": "APPROVED" if approved else "PENDING_OWNER_APPROVAL", "approvals": approvals,
            "superseded_by": sup, "dispatch_enabled": approved and sup is None and not t["unknown_n"],
            "paused_unknown_cost": bool(t["unknown_n"]), "unknown_entry_ids": unknown_ids,
            "spent_usd": round(t["spent"], 8), "reserved_usd": round(t["reserved"], 8),
            "unknown_reserved_usd": round(t["unknown_usd"], 8), "committed_usd": round(t["committed"], 8),
            "operational_limit_usd": limit, "operational_limit_kind": limit_kind,
            "remaining_usd": round(limit - t["committed"], 8),
            "attempted_requests": t["attempted"], "max_requests": env.max_requests,
            "remaining_requests": env.max_requests - t["attempted"],
            "completed": c["completed"], "retried": c["retried"], "failed": c["failed"], "billed": c["billed"],
            "historical_requests": c["historical"], "committed_by_scope_usd": by_scope,
        }

    def events(self, envelope_id: str | None = None) -> list[dict]:
        with self._tx(immediate=False) as con:
            q = "SELECT * FROM events" + (" WHERE envelope_id=?" if envelope_id else "") + " ORDER BY event_id"
            rows = con.execute(q, (envelope_id,) if envelope_id else ()).fetchall()
        return [{**dict(r), "detail": json.loads(r["detail_json"]) if r["detail_json"] else None} for r in rows]

    def entry(self, entry_id: str) -> dict:
        with self._tx(immediate=False) as con:
            r = con.execute("SELECT * FROM entries WHERE entry_id=?", (entry_id,)).fetchone()
        if r is None:
            raise KeyError(entry_id)
        return dict(r)


_SHARED: dict[str, BudgetLedger] = {}
_SHARED_LOCK = threading.Lock()


def shared_ledger(path: str | Path | None = None) -> BudgetLedger:
    """One BudgetLedger object per resolved path in this process (each operation opens its own connection)."""
    p = Path(path) if path else default_ledger_path()
    key = str(p.resolve())
    with _SHARED_LOCK:
        if key not in _SHARED:
            _SHARED[key] = BudgetLedger(p)
        return _SHARED[key]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="PTP shared budget ledger (no network)")
    ap.add_argument("command", choices=["status", "approve", "reconcile", "recover-stale", "import-workbench",
                                        "events"])
    ap.add_argument("--ledger")
    ap.add_argument("--envelope")
    ap.add_argument("--evidence")
    ap.add_argument("--by", default="owner")
    ap.add_argument("--kind", default="dispatch")
    ap.add_argument("--entry")
    ap.add_argument("--cost-usd", type=float)
    ap.add_argument("--max-age-s", type=float, default=900.0)
    ap.add_argument("--store")
    a = ap.parse_args(argv)
    led = BudgetLedger(a.ledger)
    if a.command == "status":
        ids = [a.envelope] if a.envelope else sorted(led.envelopes())
        out = {"ledger": str(led.path), "price_snapshot": PRICE_SNAPSHOT, "envelopes": [led.status(i) for i in ids]}
    elif a.command == "approve":
        if not (a.envelope and a.evidence):
            ap.error("approve needs --envelope and --evidence")
        led.approve(a.envelope, evidence_ref=a.evidence, approved_by=a.by, kind=a.kind)
        out = led.status(a.envelope)
    elif a.command == "reconcile":
        if not (a.entry and a.cost_usd is not None and a.evidence):
            ap.error("reconcile needs --entry, --cost-usd and --evidence")
        out = led.reconcile(a.entry, a.cost_usd, evidence=a.evidence)
    elif a.command == "recover-stale":
        out = {"marked_unknown": led.recover_stale(a.max_age_s)}
    elif a.command == "import-workbench":
        if not a.store:
            ap.error("import-workbench needs --store")
        out = led.import_workbench_usage(a.store, a.envelope or "E1")
    else:
        out = led.events(a.envelope)
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
