"""P0-T05 / P1-T02 readiness: the G03 A3 caller reserves every attempt in the shared budget ledger, keeps the frozen
A3r0 prompt and request body, and can serve A3r1 from a config. Fake HTTP only: no network, no paid call."""
from __future__ import annotations

import importlib.util
import io
import json
import random
import re
import socket
import urllib.error
from pathlib import Path

import pytest

from patent_to_pilot.budget.ledger import BudgetLedger

REPO = Path(__file__).resolve().parents[1]
FAKE_KEY = "test-key-NOT-A-SECRET-a3"


def _load():
    spec = importlib.util.spec_from_file_location("g03_a3_llm_expand_t",
                                                  REPO / "scripts" / "research" / "g03_a3_llm_expand.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture()
def a3(monkeypatch):
    mod = _load()
    monkeypatch.setattr(mod, "BACKOFF_S", 0)
    monkeypatch.setenv("OPENROUTER_API_KEY", FAKE_KEY)
    return mod


def _ok(cost=0.0001, text=None):
    text = text or json.dumps({"priors": ["a b", "c d", "e f"], "keywords": "x y z"})
    return 200, json.dumps({"id": "gen-fake", "provider": "FakeProv", "choices": [
        {"message": {"content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 700, "completion_tokens": 300, "cost": cost}}).encode()


class FakePost:
    def __init__(self, script):
        self.script = list(script)
        self.bodies = []
        self.headers = []

    def __call__(self, url, data, headers, timeout):
        self.bodies.append(json.loads(data))
        self.headers.append(headers)
        step = self.script.pop(0) if self.script else "ok"
        if step == "ok":
            return _ok()
        if step == "nocost":
            s, b = _ok()
            d = json.loads(b)
            del d["usage"]["cost"]
            return s, json.dumps(d).encode()
        if step == "timeout":
            raise socket.timeout("timed out")
        if isinstance(step, int):
            raise urllib.error.HTTPError(url, step, "err", {}, io.BytesIO(b"busy"))
        raise AssertionError(step)


def _inputs(tmp_path, n=3, block="P1-DEV"):
    q = tmp_path / "queries.jsonl"
    rows = [{"app_id": f"{block}-{i:03d}", "block": block, "title": f"Title {i}", "abstract": "abstract " * (5 + i),
             "claim": "claim text"} for i in range(n)]
    q.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    apps = tmp_path / "apps.json"
    apps.write_text(json.dumps([r["app_id"] for r in rows]), encoding="utf-8")
    return q, apps


def _args(tmp_path, q, apps, *extra):
    return ["--queries", str(q), "--apps-file", str(apps), "--model", "qwen/qwen3-32b", "--concurrency", "1",
            "--ledger-root", str(tmp_path / "out"), "--budget-ledger", str(tmp_path / "ledger.sqlite3"), *extra]


def _jsonl(tmp_path):
    return [json.loads(x) for p in sorted((tmp_path / "out").rglob("*.jsonl"))
            for x in p.read_text(encoding="utf-8").splitlines()]


def test_a3r0_prompt_is_byte_identical_to_the_frozen_amendment_text(a3):
    doc = (REPO / "docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md").read_text(encoding="utf-8")
    block = re.search(r"```text\n(.*?)\n```", doc, re.S).group(1)
    system = re.search(r"- system: `([^`]*)`", doc).group(1)
    vals = {"title": "T-ttl", "abstract": "A-abs", "claim": "C-clm"}
    expect = block.replace("<title>", vals["title"]).replace("<abstract>", vals["abstract"]).replace(
        "<claim>", vals["claim"])
    assert a3.USER_TEMPLATE.format(**vals) == expect and a3.SYSTEM == system
    cfg = a3.a3r0_config()
    assert cfg["max_tokens"] == 400 == a3.MAX_TOKENS and cfg["envelope"] == "E1"
    body = a3.build_body(cfg["models"]["deepseek/deepseek-v4-flash-0731"], "P", 400, cfg["temperature"], cfg["seed"])
    assert list(body) == ["model", "messages", "max_tokens", "temperature", "seed", "reasoning"]
    assert body["reasoning"] == {"effort": "none"} and body["seed"] == 20261122 and body["temperature"] == 0


def test_every_attempt_is_reserved_retries_counted_and_costs_settled(a3, tmp_path, monkeypatch):
    q, apps = _inputs(tmp_path, n=2)
    fake = FakePost([503, "ok", "ok"])
    monkeypatch.setattr(a3, "_post", fake)
    assert a3.main(_args(tmp_path, q, apps)) == 0
    led = BudgetLedger(tmp_path / "ledger.sqlite3")
    s = led.status("E1")
    assert s["attempted_requests"] == 4 + 3 and s["retried"] == 1 and s["failed"] == 1 and s["billed"] == 4 + 2
    assert s["spent_usd"] == pytest.approx(0.00064223 + 0.0002) and s["reserved_usd"] == 0
    recs = _jsonl(tmp_path)
    assert [r["status"] for r in recs].count("ok") == 2 and all(r["ledger_entry"] for r in recs)
    assert all(r["max_tokens"] == 400 and r["protocol"] == "A3r0" for r in recs)
    assert all(b["max_tokens"] == 400 and b["reasoning"] == {"enabled": False} for b in fake.bodies)
    assert (tmp_path / "out" / "qwen__qwen3-32b" / "P1-DEV.jsonl").exists()       # historical A3r0 layout
    for f in [tmp_path / "ledger.sqlite3", *(tmp_path / "out").rglob("*")]:
        if f.is_file():
            assert FAKE_KEY.encode() not in f.read_bytes()


def test_timeout_after_send_pauses_dispatch_until_reconciled(a3, tmp_path, monkeypatch, capsys):
    q, apps = _inputs(tmp_path, n=3)
    fake = FakePost(["timeout"])
    monkeypatch.setattr(a3, "_post", fake)
    assert a3.main(_args(tmp_path, q, apps)) == 2
    assert len(fake.bodies) == 1                                  # no retry and no further query after unknown cost
    assert "paused" in capsys.readouterr().out
    led = BudgetLedger(tmp_path / "ledger.sqlite3")
    s = led.status("E1")
    assert s["paused_unknown_cost"] and len(s["unknown_entry_ids"]) == 1
    assert a3.main(_args(tmp_path, q, apps)) == 2 and len(fake.bodies) == 1    # restart: still paused, nothing sent
    led.reconcile(s["unknown_entry_ids"][0], 0.0001, evidence="fake generation lookup")
    assert a3.main(_args(tmp_path, q, apps)) == 0 and len(fake.bodies) == 4
    assert led.status("E1")["spent_usd"] == pytest.approx(0.00064223 + 0.0004)


def test_answer_without_usage_cost_is_unknown_not_zero(a3, tmp_path, monkeypatch):
    q, apps = _inputs(tmp_path, n=2)
    monkeypatch.setattr(a3, "_post", FakePost(["nocost"]))
    assert a3.main(_args(tmp_path, q, apps)) == 2
    s = BudgetLedger(tmp_path / "ledger.sqlite3").status("E1")
    assert s["paused_unknown_cost"] and s["spent_usd"] == pytest.approx(0.00064223)


def test_request_cap_includes_historical_calls_and_retries(a3, tmp_path, monkeypatch):
    q, apps = _inputs(tmp_path, n=3)
    fake = FakePost([503, 503, "ok"])
    monkeypatch.setattr(a3, "_post", fake)
    assert a3.main(_args(tmp_path, q, apps, "--max-requests", "7")) == 2     # 4 historical + 3 attempts
    assert len(fake.bodies) == 3
    assert BudgetLedger(tmp_path / "ledger.sqlite3").status("E1")["attempted_requests"] == 7


def test_calibration_selection_is_fixed_train_only_and_model_independent(a3, tmp_path):
    rows = [{"app_id": f"{12000000 + i}", "block": "TRAIN", "title": "t", "abstract": "w " * (i * 7 % 50),
             "claim": "c"} for i in range(60)]
    sel = a3.select_calibration(rows)
    shuffled = rows[:]
    random.Random(7).shuffle(shuffled)
    assert [r["app_id"] for r in a3.select_calibration(shuffled)] == [r["app_id"] for r in sel]
    assert len(sel) == 32 and sum(r["_selected"] == "long" for r in sel) == 8
    longest = sorted(rows, key=lambda r: -len(a3.build_prompt(r).encode()))[:8]
    assert min(len(a3.build_prompt(r).encode()) for r in sel if r["_selected"] == "long") == \
        min(len(a3.build_prompt(r).encode()) for r in longest)
    q = tmp_path / "train.jsonl"
    q.write_text("".join(json.dumps(r) + "\n" for r in rows + [dict(rows[0], app_id="x", block="P1-DEV")]),
                 encoding="utf-8")
    with pytest.raises(SystemExit, match="TRAIN-only"):
        a3.main(["--queries", str(q), "--model", "qwen/qwen3-32b", "--calibration", "--plan",
                 "--ledger-root", str(tmp_path / "out")])


def _a3r1_config(tmp_path, **flags):
    cfg = json.loads((REPO / "docs/healthtech/research/g03-dev/a3r1/a3r1-caller-config.json").read_text(
        encoding="utf-8"))
    cfg.update(flags)
    p = tmp_path / "a3r1.json"
    p.write_text(json.dumps(cfg), encoding="utf-8")
    return p


def test_tracked_a3r1_config_loads_800_tokens_and_stays_disabled(a3, tmp_path, monkeypatch):
    cfg = a3.load_config(REPO / "docs/healthtech/research/g03-dev/a3r1/a3r1-caller-config.json")
    assert cfg["protocol_id"] == "A3r1" and cfg["max_tokens"] == 800 and cfg["envelope"] == "E1R"
    assert sorted(cfg["models"]) == ["deepseek/deepseek-v4-flash-0731", "google/gemini-2.5-flash-lite",
                                     "qwen/qwen3-32b", "typhoon-v2.5-30b-a3b-instruct"]
    assert cfg["execution_enabled"] is False and cfg["calibration_enabled"] is False
    rows = [{"app_id": str(i), "block": "TRAIN", "title": "t", "abstract": "a", "claim": "c"} for i in range(40)]
    q = tmp_path / "train.jsonl"
    q.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    monkeypatch.setattr(a3, "_post", FakePost([]))
    with pytest.raises(SystemExit, match="calibration is disabled"):
        a3.main(["--config", str(REPO / "docs/healthtech/research/g03-dev/a3r1/a3r1-caller-config.json"),
                 "--calibration", "--queries", str(q), "--model", "qwen/qwen3-32b",
                 "--ledger-root", str(tmp_path / "out"), "--budget-ledger", str(tmp_path / "l.sqlite3")])


def test_a3r1_calibration_is_refused_by_the_ledger_while_e1r_is_pending(a3, tmp_path, monkeypatch, capsys):
    p = _a3r1_config(tmp_path, calibration_enabled=True)
    rows = [{"app_id": str(i), "block": "TRAIN", "title": "t", "abstract": "a " * i, "claim": "c"} for i in range(40)]
    q = tmp_path / "train.jsonl"
    q.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    fake = FakePost([])
    monkeypatch.setattr(a3, "_post", fake)
    args = ["--config", str(p), "--calibration", "--queries", str(q), "--model", "qwen/qwen3-32b",
            "--ledger-root", str(tmp_path / "out"), "--budget-ledger", str(tmp_path / "l.sqlite3")]
    assert a3.main(args) == 2 and fake.bodies == []
    assert "not_approved" in capsys.readouterr().out
    man = json.loads((tmp_path / "out" / "A3r1" / "calibration" / "calibration-manifest.json").read_text())
    assert man["cases"] == 32 and man["block"] == "TRAIN" and man["no_retrieval_scoring"] is True
    # after an owner approval record, the same command dispatches with the 800-token cap
    BudgetLedger(tmp_path / "l.sqlite3").approve("E1R", evidence_ref="test fixture", approved_by="test")
    assert a3.main(args) == 0 and len(fake.bodies) == 32
    assert {b["max_tokens"] for b in fake.bodies} == {800}
    s = BudgetLedger(tmp_path / "l.sqlite3").status("E1R")
    assert s["attempted_requests"] == 4 + 32 and s["committed_by_scope_usd"]["g03_a3"] == pytest.approx(
        0.00064223 + 32 * 0.0001)
    recs = _jsonl(tmp_path)
    assert all(r["block"] == "TRAIN" and r["protocol"] == "A3r1" for r in recs)


def test_typhoon_without_a_verified_price_is_never_dispatched(a3, tmp_path, monkeypatch, capsys):
    p = _a3r1_config(tmp_path, calibration_enabled=True)
    q = tmp_path / "train.jsonl"
    q.write_text(json.dumps({"app_id": "1", "block": "TRAIN", "title": "t", "abstract": "a", "claim": "c"}) + "\n",
                 encoding="utf-8")
    monkeypatch.setenv("TYPHOON_API_KEY", "test-NOT-A-SECRET")
    BudgetLedger(tmp_path / "l.sqlite3").approve("E1R", evidence_ref="test fixture", approved_by="test")
    fake = FakePost([])
    monkeypatch.setattr(a3, "_post", fake)
    assert a3.main(["--config", str(p), "--calibration", "--queries", str(q), "--model",
                    "typhoon-v2.5-30b-a3b-instruct", "--ledger-root", str(tmp_path / "out"),
                    "--budget-ledger", str(tmp_path / "l.sqlite3")]) == 2
    assert fake.bodies == [] and "price_unknown" in capsys.readouterr().out


def test_owner_shape_config_and_max_tokens_override(a3, tmp_path, monkeypatch, capsys):
    prof = {"generation_profiles": [{"profile_id": "qwen3_32b", "provider": "openrouter", "model_id": "qwen/qwen3-32b",
                                     "base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY"}]}
    (tmp_path / "model_profiles.json").write_text(json.dumps(prof), encoding="utf-8")
    owner = {"protocol_id": "A3r1", "primary_profile_ids": ["qwen3_32b"], "output_tokens": 800,
             "budget_authority": "PENDING_E1R_APPROVAL", "execution_enabled": False}
    (tmp_path / "a3r1_proposed.json").write_text(json.dumps(owner), encoding="utf-8")
    cfg = a3.load_config(tmp_path / "a3r1_proposed.json")
    m = cfg["models"]["qwen/qwen3-32b"]
    assert cfg["max_tokens"] == 800 and cfg["envelope"] == "E1R" and cfg["execution_enabled"] is False
    assert m["endpoint"] == "https://openrouter.ai/api/v1/chat/completions" and m["reasoning"] == {"enabled": False}
    q, apps = _inputs(tmp_path, n=2)
    assert a3.main(["--config", str(tmp_path / "a3r1_proposed.json"), "--queries", str(q), "--apps-file", str(apps),
                    "--model", "qwen/qwen3-32b", "--max-tokens", "600", "--plan",
                    "--ledger-root", str(tmp_path / "out")]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["max_tokens"] == 600 and out["rows"] == 2 and out["price_known"] is True
    assert not (tmp_path / "out").exists()                         # --plan writes nothing
