"""P2-T04 entry point checks with authored files and a deterministic in-memory backend."""
import gzip
import hashlib
import json

import pytest

from patent_to_pilot.workbench.relation_search import EligibilityMask, POLICY_V1_SHA256
from scripts.research import p2t04_run_screen as screen


class FixtureIndex:
    def __init__(self, rows, dates):
        self.unit_rows = {unit: i for i, (unit, _) in enumerate(rows)}
        assert set(self.unit_rows) == dates.keys()

    def eligibility_for(self, app, filing_date):
        assert filing_date == "2000-01-01"
        return EligibilityMask("fixture", exclude_ids={"A:" + app})

    def original(self, request, mask):
        assert request.query_text == "archived serialisation"
        return [("A:2", 1.5)]

    def search(self, query, limit, mask):
        return [("A:2", 1.5)]

    def rerank(self, request, pool):
        assert request.query_text.endswith("A valve closes when a sensor detects pressure.")
        return {unit: 1.0 for unit in pool}


def test_frozen_runtime_reproduces_bm25_and_writes_all_arms(tmp_path, monkeypatch):
    monkeypatch.setattr(screen, "BM25FullIndex", FixtureIndex)

    def pin(path):
        return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    payloads = {
        "queries": {
            "app_id": "1", "block": "P1-DEV", "title": "Valve fixture", "abstract": "Authored example",
            "claim": "A valve closes when a sensor detects pressure.",
        },
        "bm25_queries": {"app_id": "1", "block": "P1-DEV", "text": "archived serialisation"},
        "full_passages": {"unit": "A:2", "text": "A valve closes when a sensor detects excess pressure."},
    }
    inputs = {}
    for role, row in payloads.items():
        path = tmp_path / f"{role}.jsonl"
        path.write_text(json.dumps(row) + "\n", encoding="utf-8")
        inputs[role] = pin(path)
    tasks = tmp_path / "tasks.tsv"
    tasks.write_text("app_id\tblock\tfiling_date\n1\tP1-DEV\t2000-01-01\n", encoding="utf-8")
    units = tmp_path / "units.tsv"
    units.write_text("unit_id\tfirst_pub\nA:2\t1999-01-01\n", encoding="utf-8")
    inputs.update(tasks=pin(tasks), units=pin(units))
    for route in screen.ROUTES:
        directory = tmp_path / route
        directory.mkdir()
        path = directory / "run-P1-DEV.tsv.gz"
        with gzip.open(path, "wt", encoding="utf-8") as stream:
            stream.write("app_id\trank\tunit\tscore\n1\t1\tA:2\t1.5000\n")
        inputs["route_" + route] = pin(path)
    manifest = tmp_path / "freeze.json"
    data = {
        "schema": "ptp-p2t04-screen/1", "block": "P1-DEV", "policy_sha256": POLICY_V1_SHA256,
        "query_ids": ["1"], "inputs": inputs, "corpus_version": "fixture-v1",
        "seed_windows": dict(L=0, Q=2, P=2, A=0),
        "screen_limits": dict(seed=200, seed_reads=2, source_chars=400, feedback_terms=3, fetch=10,
                              returned=2, original_depth=3, final=200),
        "assessor_limits": dict(claim_chars=400, requirements=2, anchor_terms=2, source_passages=4,
                                source_chars=400, local_tokens=5),
    }
    manifest.write_text(json.dumps(data), encoding="utf-8")
    freeze_sha = pin(manifest)["sha256"]
    out = tmp_path / "result"
    screen.run(manifest, freeze_sha, out)
    assert json.loads((out / "bm25-reproduction.json").read_text())["status"] == "PASS"
    trace = json.loads((out / "trace.jsonl").read_text())
    assert trace["app_id"] == "1" and trace["frozen_manifest_sha256"] == freeze_sha
    assert set(trace["arms"]) == set(screen.ARMS)
    assert (out / "complete_content_fusion.tsv").read_text().splitlines()[1].startswith("1\t1\tA:2")
    with pytest.raises(ValueError, match="frozen SHA-256 mismatch"):
        screen.run(manifest, "0" * 64, tmp_path / "unfrozen")


def test_rejects_protected_path_before_open(tmp_path):
    with pytest.raises(ValueError, match="protected or credential"):
        screen.checked_digest(tmp_path / "P1-TEST" / "absent.tsv", "0" * 64)


@pytest.mark.parametrize("difference", ["tie", "raw", "display", "eligibility", "prefix", "top200", "short"])
def test_cutoff_exception_requires_a_proved_tie_below_top200(difference):
    ranked = [(f"u{i}", 2.0) for i in range(screen.TOPK - 1)] + [("current", 1.0)]
    if difference == "top200":
        ranked[screen.FINAL_DEPTH - 1:] = [(unit, 1.0) for unit, _ in ranked[screen.FINAL_DEPTH - 1:]]
    reproduced = [(i, unit, f"{score:.4f}") for i, (unit, score) in enumerate(ranked, 1)]
    archived = reproduced[:-1] + [(screen.TOPK, "historical", "1.0000")]
    if difference == "display":
        archived[-1] = (screen.TOPK, "historical", "1.0001")
    elif difference == "prefix":
        archived[screen.TOPK - 2] = (screen.TOPK - 1, "other", "2.0000")
    elif difference == "short":
        archived.pop()
    mask = EligibilityMask("fixture", exclude_ids={"historical"} if difference == "eligibility" else set())

    class Index:
        def rerank(self, request, units):
            assert request == "archived query" and units == ["historical"]
            return {"historical": 1.00001 if difference == "raw" else 1.0}

    result = screen.same_cutoff_tie(archived, reproduced, ranked, Index(), "archived query", mask)
    assert result is (difference == "tie")
