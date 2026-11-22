"""P0-T05: shared budget reservation ledger. Fake providers only: no network, no paid call, no credential."""
from __future__ import annotations

import json
import os
import socket
import sqlite3
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

import pytest

from patent_to_pilot.budget import ledger as L
from patent_to_pilot.budget.ledger import BudgetLedger, BudgetRefused, Envelope

REPO = Path(__file__).resolve().parents[1]
SMOKE_USD = 0.00064223


@pytest.fixture()
def led(tmp_path):
    return BudgetLedger(tmp_path / "budget" / "ledger.sqlite3")


def _approved_envelope(led, cap=1.0, max_requests=10000, envelope_id="T1"):
    led.put_envelope(Envelope(envelope_id, ["fake"], hard_limit_usd=cap, max_requests=max_requests))
    led.approve(envelope_id, evidence_ref="test fixture", approved_by="test")
    return envelope_id



def test_seed_has_e1_approved_e1r_pending_and_historical_smoke(tmp_path):
    p = tmp_path / "l.sqlite3"
    led = BudgetLedger(p)
    e1 = led.status("E1")
    assert e1["approval"] == "APPROVED" and e1["dispatch_enabled"] is True
    assert e1["spent_usd"] == pytest.approx(SMOKE_USD) and e1["attempted_requests"] == 4
    assert e1["historical_requests"] == 4 and e1["operational_limit_usd"] == 6.0
    assert e1["operational_limit_kind"] == "stop_threshold" and e1["max_requests"] == 35000
    e1r = led.status("E1R")
    assert e1r["approval"] == "PENDING_OWNER_APPROVAL" and e1r["dispatch_enabled"] is False
    assert e1r["config"]["hard_limit_usd"] == 50 and e1r["config"]["notify_usd"] == 40
    assert e1r["config"]["max_requests"] == 100000
    assert e1r["spent_usd"] == pytest.approx(SMOKE_USD)          # cumulative: includes E1 spend
    BudgetLedger(p)                                              # re-open: seeding is idempotent
    assert BudgetLedger(p).status("E1")["attempted_requests"] == 4


def test_ledger_refuses_a_path_inside_the_git_repository():
    with pytest.raises(ValueError, match="git work tree"):
        BudgetLedger(REPO / "budget-ledger-must-not-be-here.sqlite3")
    assert not (REPO / "budget-ledger-must-not-be-here.sqlite3").exists()


def test_default_path_is_env_or_user_data_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("PTP_BUDGET_LEDGER", str(tmp_path / "x.sqlite3"))
    assert L.default_ledger_path() == tmp_path / "x.sqlite3"
    monkeypatch.delenv("PTP_BUDGET_LEDGER")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "lad"))
    assert L.default_ledger_path() == tmp_path / "lad" / "PatentToPilot" / "budget" / "ledger.sqlite3"


def test_reserve_settle_release_counts(led):
    env = _approved_envelope(led)
    a = led.reserve("fake", 0.10, scope="s", envelope_id=env)
    assert led.status(env)["reserved_usd"] == pytest.approx(0.10)
    led.settle(a.entry_id, 0.04, generation_id="gen-1")
    b = led.reserve("fake", 0.10, scope="s", envelope_id=env, attempt=0)
    led.release(b.entry_id, outcome="http_503")
    c = led.reserve("fake", 0.10, scope="s", envelope_id=env, attempt=1)
    led.settle(c.entry_id, 0.02)
    s = led.status(env)
    assert s["spent_usd"] == pytest.approx(0.06) and s["reserved_usd"] == 0
    assert (s["attempted_requests"], s["completed"], s["retried"], s["failed"], s["billed"]) == (3, 2, 1, 1, 2)
    with pytest.raises(ValueError):
        led.settle(a.entry_id, 0.01)                             # an entry settles once


def test_thread_reservations_never_exceed_the_cap(led):
    env = _approved_envelope(led, cap=1.0)
    ok, refused = [], []

    def worker():
        for _ in range(20):
            try:
                ok.append(led.reserve("fake", 0.03, scope="s", envelope_id=env).entry_id)
            except BudgetRefused as e:
                refused.append(e.reason)

    ts = [threading.Thread(target=worker) for _ in range(16)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    assert len(ok) == 33 and len(refused) == 16 * 20 - 33         # floor(1.00 / 0.03)
    assert set(refused) == {"usd_limit"}
    s = led.status(env)
    assert s["reserved_usd"] <= 1.0 + 1e-9 and s["attempted_requests"] == 33


def test_process_reservations_never_exceed_the_cap(tmp_path):
    path = tmp_path / "shared.sqlite3"
    led = BudgetLedger(path)
    env = _approved_envelope(led, cap=1.0)
    script = (
        "import sys\n"
        "from patent_to_pilot.budget.ledger import BudgetLedger, BudgetRefused\n"
        "led = BudgetLedger(sys.argv[1])\n"
        "n = 0\n"
        "for _ in range(30):\n"
        "    try:\n"
        "        led.reserve('fake', 0.05, scope='s', envelope_id=sys.argv[2]); n += 1\n"
        "    except BudgetRefused:\n"
        "        pass\n"
        "print(n)\n")
    env_vars = dict(os.environ, PYTHONPATH=str(REPO / "src"))
    procs = [subprocess.Popen([sys.executable, "-c", script, str(path), env], stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, env=env_vars) for _ in range(4)]
    counts = []
    for p in procs:
        out, err = p.communicate(timeout=180)
        assert p.returncode == 0, err
        counts.append(int(out.strip()))
    assert sum(counts) == 20                                       # 1.00 / 0.05, across 4 processes
    s = led.status(env)
    assert s["attempted_requests"] == 20 and s["reserved_usd"] == pytest.approx(1.0)


def test_retries_are_attempts_and_the_request_cap_holds(led):
    env = _approved_envelope(led, cap=100.0, max_requests=5)
    for attempt in (0, 1, 2, 0, 1):
        r = led.reserve("fake", 0.001, scope="s", envelope_id=env, attempt=attempt)
        led.release(r.entry_id, outcome="http_503")
    with pytest.raises(BudgetRefused) as e:
        led.reserve("fake", 0.001, scope="s", envelope_id=env)
    assert e.value.reason == "request_cap"
    s = led.status(env)
    assert s["attempted_requests"] == 5 and s["retried"] == 3 and s["spent_usd"] == 0


def test_unknown_cost_pauses_dispatch_until_reconciled(led):
    env = _approved_envelope(led)
    a = led.reserve("fake", 0.05, scope="s", envelope_id=env)
    assert led.settle(a.entry_id, None)["status"] == "unknown"   # a missing cost is never zero
    with pytest.raises(BudgetRefused) as e:
        led.reserve("fake", 0.01, scope="s", envelope_id=env)
    assert e.value.reason == "paused_unknown_cost" and e.value.state["unknown_entries"] == 1
    s = led.status(env)
    assert s["paused_unknown_cost"] and s["unknown_reserved_usd"] == pytest.approx(0.05)
    with pytest.raises(ValueError):
        led.reconcile(a.entry_id, 0.03, evidence="")
    led.reconcile(a.entry_id, 0.03, evidence="generation lookup gen-x (fake)")
    assert led.status(env)["spent_usd"] == pytest.approx(0.03)
    led.reserve("fake", 0.01, scope="s", envelope_id=env)         # dispatch resumes
    assert any(ev["kind"] == "unknown_cost_pause" for ev in led.events(env))


def test_reservations_persist_across_restart_and_stale_ones_pause(tmp_path):
    p = tmp_path / "l.sqlite3"
    led = BudgetLedger(p)
    env = _approved_envelope(led, cap=0.10)
    led.reserve("fake", 0.08, scope="s", envelope_id=env)          # the process "dies" here
    led2 = BudgetLedger(p)                                          # restart
    assert led2.status(env)["reserved_usd"] == pytest.approx(0.08)
    with pytest.raises(BudgetRefused) as e:
        led2.reserve("fake", 0.05, scope="s", envelope_id=env)      # still counted against the cap
    assert e.value.reason == "usd_limit"
    assert led2.recover_stale(max_age_s=3600) == 0                 # a fresh reservation may still be live
    assert led2.recover_stale(max_age_s=0) == 1                    # past its lease: unknown, pause
    with pytest.raises(BudgetRefused) as e:
        led2.reserve("fake", 0.001, scope="s", envelope_id=env)
    assert e.value.reason == "paused_unknown_cost"


def test_disabled_e1r_refuses_until_an_owner_approval_record(led):
    with pytest.raises(BudgetRefused) as e:
        led.reserve("openrouter", 0.001, scope="g03_a3", envelope_id="E1R")
    assert e.value.reason == "not_approved"
    assert led.dispatch_envelope("openrouter") == "E1"
    with pytest.raises(BudgetRefused) as e:
        led.dispatch_envelope("typhoon")                           # only E1R covers Typhoon, and it is pending
    assert e.value.reason == "provider_not_covered"
    with pytest.raises(ValueError):
        led.approve("E1R", evidence_ref="  ")
    led.approve("E1R", evidence_ref="owner chat (test fixture)", approved_by="test")
    assert led.dispatch_envelope("openrouter") == "E1R"
    with pytest.raises(BudgetRefused) as e:
        led.reserve("openrouter", 0.001, scope="g03_a3", envelope_id="E1")
    assert e.value.reason == "superseded"
    r = led.reserve("openrouter", 0.001, scope="g03_a3")
    s = led.status("E1R")
    assert r.envelope_id == "E1R" and s["attempted_requests"] == 5 and s["family"] == ["E1R", "E1"]
    assert s["operational_limit_usd"] == 50.0 and s["operational_limit_kind"] == "usd_limit"


def test_e1_stop_threshold_then_hard_limit(led):
    a = led.reserve("openrouter", 5.99, scope="g03_a3", envelope_id="E1")
    with pytest.raises(BudgetRefused) as e:
        led.reserve("openrouter", 0.01, scope="g03_a3", envelope_id="E1")   # 0.00064 + 5.99 + 0.01 > 6.00
    assert e.value.reason == "stop_threshold" and e.value.state["remaining_usd"] < 0.01
    assert [ev["kind"] for ev in led.events("E1")].count("stop_and_report") == 1
    led.approve("E1", kind="continue_past_stop", evidence_ref="owner chat (test fixture)", approved_by="test")
    led.reserve("openrouter", 1.5, scope="g03_a3", envelope_id="E1")
    with pytest.raises(BudgetRefused) as e:
        led.reserve("openrouter", 0.6, scope="g03_a3", envelope_id="E1")    # would pass the USD 8 hard limit
    assert e.value.reason == "usd_limit"
    led.settle(a.entry_id, 0.5)


def test_notify_threshold_is_reported_once(led):
    led.approve("E1R", evidence_ref="test fixture", approved_by="test")
    assert led.reserve("openrouter", 39.0, scope="g03_a3").notify is False
    assert led.reserve("openrouter", 1.0, scope="g03_a3").notify is True
    assert led.reserve("openrouter", 1.0, scope="g03_a3").notify is False
    assert [ev["kind"] for ev in led.events("E1R")].count("notify_threshold") == 1


def test_workbench_scope_cap_inside_e1(led):
    led.reserve("openrouter", 0.15, scope="workbench", envelope_id="E1")
    with pytest.raises(BudgetRefused) as e:
        led.reserve("openrouter", 0.06, scope="workbench", envelope_id="E1")
    assert e.value.reason == "scope_cap"
    led.reserve("openrouter", 0.06, scope="g03_a3", envelope_id="E1")       # research scope is not capped at 0.20


def test_unknown_price_is_refused_and_estimates_are_bounds(led):
    with pytest.raises(BudgetRefused) as e:
        led.reserve("typhoon", L.estimate_chat_max_usd(L.price_for("typhoon", "typhoon-v2.5-30b-a3b-instruct"),
                                                       3000, 800), scope="g03_a3", envelope_id="E1")
    assert e.value.reason == "price_unknown"
    p = {"input": 0.03, "output": 0.13, "tiers": [{"min_prompt_tokens": 32000, "input": 0.1, "output": 0.4}]}
    assert L.estimate_chat_max_usd(p, 744, 800) == pytest.approx(((744 + 256) * 0.03 + 800 * 0.13) / 1e6)
    assert L.estimate_chat_max_usd(p, 40000, 0) == pytest.approx((40256 * 0.1) / 1e6)
    assert L.provider_for_endpoint("https://openrouter.ai/api/v1") == "openrouter"


def _fake_workbench_store(path: Path):
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE provider_profiles (profile_id TEXT, role TEXT, adapter TEXT, config_json TEXT, "
                "created_at TEXT, updated_at TEXT)")
    con.execute("CREATE TABLE provider_usage (profile_id TEXT, operation TEXT, billable INTEGER, status TEXT, "
                "usage_json TEXT, latency_ms REAL, detail TEXT, created_at TEXT)")
    con.execute("INSERT INTO provider_profiles VALUES ('or','chat','openai_compatible',?,'t','t')",
                (json.dumps({"endpoint": "https://openrouter.ai/api/v1", "model_id": "qwen/qwen3-32b"}),))
    con.execute("INSERT INTO provider_profiles VALUES ('loc','chat','ollama',?,'t','t')",
                (json.dumps({"endpoint": "http://127.0.0.1:11434", "model_id": "qwen3:8b"}),))
    rows = [("or", "ok", {"cost_usd": 0.0001}), ("or", "ok", {"prompt_tokens": 9}), ("or", "http_500", None),
            ("or", "ok", {"cost_usd": 0.0002, "budget_entry_id": "abc"}), ("loc", "ok", None),
            ("or", "blocked", None)]
    for pid, st, u in rows:
        con.execute("INSERT INTO provider_usage VALUES (?,?,1,?,?,1.0,NULL,'t')",
                    (pid, "chat", st, None if u is None else json.dumps(u)))
    con.commit()
    con.close()


def test_import_workbench_usage_reconciles_without_double_counting(led, tmp_path):
    store = tmp_path / "workbench.sqlite3"
    _fake_workbench_store(store)
    out = led.import_workbench_usage(store)
    assert out["imported"] == 3 and out["skipped"] == 2            # loopback + already-in-ledger rows skipped
    assert led.import_workbench_usage(store)["imported"] == 0       # idempotent
    s = led.status("E1")
    assert s["attempted_requests"] == 4 + 3 and s["spent_usd"] == pytest.approx(SMOKE_USD + 0.0001)
    assert s["paused_unknown_cost"] is True                         # ok without cost must be reconciled
    assert led.import_workbench_usage(tmp_path / "absent.sqlite3") == {
        "store": str(tmp_path / "absent.sqlite3"), "exists": False, "imported": 0, "skipped": 0}


# ------------------------------------------------------------------ Workbench provider client through the ledger
class _Resp:
    def __init__(self, body: bytes):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return self.body


class _Opener:
    def __init__(self):
        self.calls = 0
        self.mode = "ok"

    def open(self, req, timeout=None):
        self.calls += 1
        if self.mode == "timeout":
            raise socket.timeout("timed out")
        return _Resp(json.dumps({"choices": [{"message": {"content": "OK"}}], "id": "gen-fake",
                                 "usage": {"prompt_tokens": 9, "completion_tokens": 1, "cost": 0.0000123}}).encode())


@pytest.fixture()
def remote_openrouter(monkeypatch, tmp_path):
    monkeypatch.setenv("PTP_BUDGET_LEDGER", str(tmp_path / "shared-ledger.sqlite3"))
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-NOT-A-SECRET")
    monkeypatch.setattr(L, "_SHARED", {})
    opener = _Opener()
    monkeypatch.setattr(urllib.request, "build_opener", lambda *h: opener)
    return opener


def test_workbench_paid_remote_calls_use_the_shared_ledger(remote_openrouter, tmp_path):
    from patent_to_pilot.workbench.providers import TEMPLATES, ProviderClient, ProviderError, ProviderProfile
    t = next(x for x in TEMPLATES if x["profile_id"] == "openrouter-qwen3-32b")
    events = []
    client = ProviderClient(ProviderProfile.from_dict(t), ledger=events.append)
    out = client.chat([{"role": "user", "content": "ping"}], max_tokens=8)
    assert out["text"] == "OK" and remote_openrouter.calls == 1
    led = BudgetLedger(tmp_path / "shared-ledger.sqlite3")
    s = led.status("E1")
    assert s["attempted_requests"] == 5 and s["committed_by_scope_usd"]["workbench"] == pytest.approx(0.0000123)
    assert events[-1]["usage"]["budget_envelope"] == "E1" and events[-1]["usage"]["cost_source"] == "usage.cost"
    remote_openrouter.mode = "timeout"
    with pytest.raises(ProviderError) as e:
        client.chat([{"role": "user", "content": "ping"}], max_tokens=8)
    assert e.value.kind == "timeout" and led.status("E1")["paused_unknown_cost"] is True
    with pytest.raises(ProviderError) as e:
        client.chat([{"role": "user", "content": "ping"}], max_tokens=8)
    assert e.value.kind == "blocked" and "paused_unknown_cost" in str(e.value)
    assert remote_openrouter.calls == 2                              # the paused call never left the machine
    assert b"test-key-NOT-A-SECRET" not in (tmp_path / "shared-ledger.sqlite3").read_bytes()


def test_workbench_paid_route_without_an_envelope_is_blocked(remote_openrouter):
    from patent_to_pilot.workbench.providers import TEMPLATES, ProviderClient, ProviderError, ProviderProfile
    t = dict(next(x for x in TEMPLATES if x["profile_id"] == "api-claude-haiku"), spend_cap_usd=1.0,
             max_requests=5)
    os.environ["ANTHROPIC_API_KEY_PTP_TEST"] = "x"
    try:
        t["credential_ref"] = "ANTHROPIC_API_KEY_PTP_TEST"
        with pytest.raises(ProviderError) as e:
            ProviderClient(ProviderProfile.from_dict(t)).chat([{"role": "user", "content": "hi"}], max_tokens=4)
    finally:
        del os.environ["ANTHROPIC_API_KEY_PTP_TEST"]
    assert e.value.kind == "blocked" and remote_openrouter.calls == 0
