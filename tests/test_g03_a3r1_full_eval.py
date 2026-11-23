"""A3r1 full evaluation package (docs/healthtech/research/g03-dev/A3R1-FULL-EVAL-RUNPOD.md): hand-checkable fixtures for
the Stage B ledger check, the VAL text rule, the v0 F* block guard, and a synthetic smoke run of the frozen
`g03_a3_decide.py full` path (F3* tie rule and the CONTINUE / REVISE / PARK rule). Synthetic numbers only; no real data."""
from __future__ import annotations

import hashlib
import json
import pickle
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
RESEARCH = REPO / "scripts" / "research"
sys.path.insert(0, str(RESEARCH))

import g03_a3r1_full_gate as fg  # noqa: E402
import g03_a3r1_full_inputs as fi  # noqa: E402

M = fg.MSTAR


def _rec(app, block, status, **kw):
    return {"app_id": app, "block": block, "model": M, "protocol": "A3r1", "max_tokens": 800, "status": status, **kw}


def _write(path: Path, recs):
    path.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")


def _ledgers(tmp_path, dev, val):
    d = tmp_path / "ledger"
    d.mkdir()
    _write(d / "P1-DEV.jsonl", dev)
    if val is not None:
        _write(d / "VAL.jsonl", val)
    first = (d / "P1-DEV.jsonl").read_bytes().split(b"\n", 1)[0] + b"\n"
    return d, {"bytes": len(first), "sha256": hashlib.sha256(first).hexdigest()}


def test_ledger_complete_with_transport_failed_after_three_attempts(tmp_path):
    dev = [_rec("a1", "P1-DEV", "ok"), _rec("a2", "P1-DEV", "content_unusable")]
    dev += [_rec("a3", "P1-DEV", "transport_error_unbilled", attempt=i) for i in range(3)]
    d, prefix = _ledgers(tmp_path, dev, [_rec("v1", "VAL", "ok")])
    res = fg.check_ledgers(d, {"P1-DEV": ["a1", "a2", "a3"], "VAL": ["v1"]}, prefix)
    assert res["complete"] is True
    assert res["P1-DEV"]["apps_terminal"] == 2 and res["P1-DEV"]["apps_transport_failed"] == 1
    assert res["P1-DEV"]["apps_usable"] == 1 and res["pilot_prefix"]["passed"]
    assert res["passed"] is False   # the fixture populations are not the frozen 25,626 / 1,919


def test_ledger_incomplete_when_an_app_is_missing_or_paused(tmp_path):
    dev = [_rec("a1", "P1-DEV", "ok"), _rec("a2", "P1-DEV", "transport_error", cost_status="unknown_paused")]
    dev += [_rec("a2", "P1-DEV", "transport_error_unbilled", attempt=i) for i in (1, 2)]
    d, prefix = _ledgers(tmp_path, dev, None)
    res = fg.check_ledgers(d, {"P1-DEV": ["a1", "a2", "a3"], "VAL": ["v1"]}, prefix)
    assert res["complete"] is False
    assert res["P1-DEV"]["apps_missing"] == 2        # a2 has an unreconciled unknown cost, a3 has no record
    assert res["VAL"] == {"present": False, "population": 1}


def test_ledger_rejects_foreign_records_and_prefix_change(tmp_path):
    dev = [_rec("a1", "P1-DEV", "ok"), _rec("zz", "P1-DEV", "ok"), _rec("a2", "VAL", "ok")]
    d, prefix = _ledgers(tmp_path, dev, [_rec("v1", "VAL", "ok")])
    res = fg.check_ledgers(d, {"P1-DEV": ["a1", "a2"], "VAL": ["v1"]}, {**prefix, "sha256": "0" * 64})
    assert res["P1-DEV"]["clean"] is False
    assert res["P1-DEV"]["records_outside_population"] == 1 and res["P1-DEV"]["non_block_records"] == 1
    assert res["pilot_prefix"]["passed"] is False


def test_ledger_stops_on_test_block(tmp_path):
    d, prefix = _ledgers(tmp_path, [_rec("a1", "P1-TEST", "ok")], [])
    with pytest.raises(SystemExit):
        fg.check_ledgers(d, {"P1-DEV": ["a1"], "VAL": []}, prefix)


def test_val_text_rule_matches_builder_fields():
    with_doc = fi.derive_val_record({"app_id": "1", "block": "VAL", "title": "T", "abstract": "", "claim": "c"})
    no_doc = fi.derive_val_record({"app_id": "2", "block": "VAL", "title": "", "abstract": "", "claim": ""})
    built = {"app_id": "1", "block": "VAL", "doc": "PG2010", "pub": "2010-01-01", "title": "T", "abstract": None,
             "claim": "c", "claim_variant": "first_independent"}
    assert fi.ser_key(with_doc) == fi.ser_key(built)
    assert no_doc["doc"] is None and fi.ser_key(no_doc) == fi.ser_key({"app_id": "2", "block": "VAL", "doc": None,
                                                                        "variant": "no_pgpub"})


def test_v0_rebuild_refuses_test_block(tmp_path):
    out = subprocess.run([sys.executable, "-I", str(RESEARCH / "g03_a3r1_runpod_v0.py"), str(RESEARCH), str(tmp_path),
                          str(tmp_path), "P1-TEST"], capture_output=True, text=True)
    assert out.returncode != 0 and "refusing block" in out.stderr


def _eval(path: Path, block, per_query):
    keys = ("ALL_R@200", "IN_R@200", "OUT_R@200")
    means = {k: {"mean": sum(v[k] for v in per_query.values()) / len(per_query)} for k in keys}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"block": block, "run": "synthetic", "n_queries_run": len(per_query),
                                "metrics": means, "per_query": per_query}))


def _pq(apps, base, shift=0.0):
    return {a: {"ALL_R@200": base + shift, "IN_R@200": base + shift, "OUT_R@200": base + shift} for a in apps}


def test_decide_full_tie_rule_and_continue_on_synthetic_evals(tmp_path):
    dev, val = [f"d{i}" for i in range(8)], [f"v{i}" for i in range(6)]
    meta = {"queries": {"P1-DEV": [{"app": a, "au": f"u{i % 3}"} for i, a in enumerate(dev)],
                        "VAL": [{"app": a, "au": f"u{i % 2}"} for i, a in enumerate(val)]}}
    (tmp_path / "meta.pkl").write_bytes(pickle.dumps(meta))
    ev, ev0 = tmp_path / "evals-a3r1-full", tmp_path / "evals"
    for b, apps in (("P1-DEV", dev), ("VAL", val)):
        _eval(ev0 / b / "alloc-L0-Q2-P2-A0.json", b, _pq(apps, 0.40))
        _eval(ev / b / "alloc-L0-Q2-P2-H0-K0.json", b, _pq(apps, 0.40))
        _eval(ev / b / "alloc-L4-Q0-P0-H0-K0.json", b, _pq(apps, 0.30))
        _eval(ev / b / "alloc-L0-Q0-P0-H1-K0.json", b, _pq(apps, 0.60))       # B = 1: never a candidate
        _eval(ev / b / "alloc-L0-Q1-P1-H1-K1.json", b, _pq(apps, 0.45))       # best mean, four routes
        _eval(ev / b / "alloc-L0-Q0-P2-H2-K0.json", b, _pq(apps, 0.4496, 0.0 if b == "P1-DEV" else 0.05))
    out = tmp_path / "results.json"
    run = subprocess.run([sys.executable, "-I", str(RESEARCH / "g03_a3_decide.py"), "full", "--evals", str(ev),
                          "--v0-evals", str(ev0), "--meta", str(tmp_path / "meta.pkl"), "--out", str(out)],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stderr
    res = json.loads(out.read_text())
    assert res["integrity_Fstar_equal"] == {"P1-DEV": True, "VAL": True}
    assert res["F3_star"] == "alloc-L0-Q0-P2-H2-K0"      # within 0.0005 of the best, fewer routes
    assert res["decision"].startswith("CONTINUE")
    assert res["principal_VAL_F3star_minus_Fstar"]["ALL_R@200"]["n"] == len(val)
