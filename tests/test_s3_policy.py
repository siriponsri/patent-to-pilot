"""Independent hand-authored examples. No S1 corpus or labels."""

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "research"))
import s3_policy
from s3_policy import Index, solve
from s3_run import ARMS, STATES, aggregate
from s3_trace import identities, sha, validate


@pytest.fixture
def dossier():
    documents = {
        "order": [("§ Oak", "Amber class follows Table A."),
                  ("§ Pine", "Blue class follows Table B."),
                  ("Note 1", "Unrelated report."),
                  ("Note 2", "File is retained.")],
        "tables": [("Table A", "Time value: twelve."), ("Table B", "Time value: ninety.")],
    }
    sources, units = [], []
    for sid, rows in documents.items():
        body = "\n".join(f"{loc}\n{text}" for loc, text in rows)
        source = dict(source_id=sid, version="2", sha256=sha(body), family_id="fixture",
                      language="en", text=body)
        sources.append(source)
        for loc, text in rows:
            start = body.index(text)
            units.append(dict(source, text=text, unit_id=loc, locator=loc, char_start=start,
                              char_end=start + len(text), unit_sha256=sha(text)))
    edges = [
        {"from": "§ Oak", "to": "Table A", "basis": "follows Table A", "inferred": False},
        {"from": "§ Pine", "to": "Table B", "basis": "follows Table B", "inferred": False},
    ]
    corpus, graph = identities(dict(sources=sources, units=units, edges=edges))
    return Index(units, edges), corpus, graph


@pytest.mark.parametrize("seed,actions,answer", [
    (["Table A", "§ Oak", "§ Pine", "Table B"], ["seed"], "twelve"),
    (["Table B", "§ Pine", "Table A", "§ Oak"], ["seed", "rerank"], "twelve"),
    (["§ Oak", "Table B", "Note 1", "Note 2"], ["seed", "acquire", "rerank"], "twelve"),
])
def test_scope_replay(dossier, seed, actions, answer):
    index, corpus, graph = dossier
    request = dict(case_id="q", family_id="fixture", language="en",
                   question="amber class; time?", seed_pool=seed)
    trial = json.loads(json.dumps(solve(index, request, "scope")))
    checked = validate(trial, request, corpus, graph)
    assert [event["action"] for event in trial["events"]] == actions
    assert checked["decision"] == answer
    assert {item["unit_id"] for item in checked["evidence"]} == {"§ Oak", "Table A"}
    replay = solve(index, request, "scope")
    assert list(replay["chosen"]) == trial["chosen"]
    assert replay["decision"] == trial["decision"]


def test_coverage_sees_disjoint_matches_and_finite_absence(dossier):
    index, corpus, graph = dossier
    request = dict(case_id="q", family_id="fixture", language="en",
                   question="amber class; time?", seed_pool=["§ Oak", "Table B", "Note 1", "Note 2"])
    trial = json.loads(json.dumps(solve(index, request, "coverage")))
    checked = validate(trial, request, corpus, graph)
    assert checked["usage"]["actions"] == 2
    assert checked["decision"] == "ABSTAIN"
    assert checked["evidence"] == []
    for arm in ("scope", "coverage"):
        absent = dict(request, question="amber class; signer?")
        reply = json.loads(json.dumps(solve(index, absent, arm)))
        assert validate(reply, absent, corpus, graph)["decision"] == "ABSTAIN"
    # Sharing a source is insufficient to license a pair.
    conflicting = dict(request, question="amber class; blue class?",
                       seed_pool=["§ Oak", "§ Pine", "Table A", "Table B"])
    assert solve(index, conflicting, "static")["decision"] == "ABSTAIN"


@pytest.mark.parametrize("fault,reason", [
    ("unknown", "unknown/foreign"), ("repeated", "unknown/foreign"),
    ("clock", "nonmonotonic"), ("count", "unaccounted candidate search"),
    ("return", "uninspected"), ("hash", "altered returned identity"),
])
def test_trace_rejects_forged_operations(dossier, fault, reason):
    index, corpus, graph = dossier
    request = dict(case_id="q", family_id="fixture", language="en",
                   question="amber class; time?", seed_pool=["§ Oak", "Table B", "Note 1", "Note 2"])
    trace = json.loads(json.dumps(solve(index, request, "scope")))
    attempt = deepcopy(trace)
    if fault == "unknown":
        attempt["events"][1]["inspected"][0] = "invented"
    if fault == "repeated":
        attempt["events"][1]["inspected"][0] = attempt["events"][1]["inspected"][1]
    if fault == "clock":
        attempt["events"][1]["start_ns"] = attempt["events"][0]["end_ns"] - 1
    if fault == "count":
        attempt["events"][1]["inspected"].pop()
    if fault == "return":
        attempt["evidence"][0]["unit_id"] = "not inspected"
    if fault == "hash":
        attempt["evidence"][0]["unit_sha256"] = "0" * 64
    with pytest.raises(ValueError, match=reason):
        validate(attempt, request, corpus, graph)


def test_paired_analysis_uses_states_and_whole_families():
    rows = []
    for family, change in (("one", 1), ("two", 0), ("three", -1)):
        for state in STATES:
            arms = {
                arm: {"success": int(state == "outside" and (
                    (arm == "scope" and change == 1) or (arm == "coverage" and change == -1))),
                    "trace_valid": False}
                for arm in ARMS
            }
            rows.append(dict(case_id=(family, state), family_id=family, state=state,
                             status="ANSWERABLE", arms=arms))
    result = aggregate(rows, [])
    assert result["delta"] == 0
    assert result["interval"] == pytest.approx([-1 / 3, 1 / 3])
    assert result["states"]["outside"]["paired"] == dict(
        improved=1, worsened=1, both_correct=0, both_failed=1)


@pytest.mark.parametrize("arm,answer", [("coverage", "ABSTAIN"), ("scope", "twelve")])
def test_full_assignment_ranking_occurs_only_in_metered_rerank(dossier, monkeypatch, arm, answer):
    index, _, _ = dossier
    request = dict(case_id="q", family_id="fixture", language="en",
                   question="amber class; time?", seed_pool=["§ Oak", "Table B", "Note 1", "Note 2"])
    original = s3_policy.assignments
    calls = []

    def counted(*args, **kwargs):
        calls.append(args[0].events[-1]["action"])
        return original(*args, **kwargs)

    monkeypatch.setattr(s3_policy, "assignments", counted)
    trace = solve(index, request, arm)
    assert trace["decision"] == answer
    assert calls == ["rerank"] * sum(event["action"] == "rerank" for event in trace["events"])
    assert calls == ["rerank"]
