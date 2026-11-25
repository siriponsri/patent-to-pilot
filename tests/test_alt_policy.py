"""Independent typed-source fixtures. No evaluation packet is imported."""

from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "research"))
from alt_evaluate import digest, score_case, validate_labels, validate_packet, validate_trace
from alt_policy import ARMS, Index, solve


def build_fixture(name, records, seed, expected, witnesses, *, region="East"):
    sources, units, edges = [], [], []
    for uid, version, root, facts, answer, links in records:
        basis = [f"See {target} for {kind}." for target, kind in links]
        body = " ".join([f"{uid} concerns repair.", *basis,
                         *(f"{key}: {value}." for key, value in facts.items()),
                         f"Outcome: {answer}." if answer else ""])
        locator = f"Record {uid}"
        source_id = f"{name}-{uid}"
        original = f"{locator}\n{body}"
        sha = digest(original)
        sources.append(dict(source_id=source_id, family_id=name, version=version,
                            language="en", text=original, sha256=sha))
        units.append(dict(unit_id=uid, source_id=source_id, family_id=name, version=version,
                          sha256=sha, text=body, locator=locator, char_start=len(locator) + 1,
                          char_end=len(original), unit_sha256=digest(body), root=root,
                          topic="repair" if root else None, facts=facts, answer=answer))
        edges.extend({"from": uid, "to": target, "kind": kind, "basis": quote}
                     for (target, kind), quote in zip(links, basis))
    request = dict(case_id=name + "-q", family_id=name, language="en",
                   question=f"What is the repair time in {region}?", topic="repair",
                   conditions={"region": region}, seed=seed)
    label = dict(case_id=request["case_id"], family_id=name,
                 status="ANSWERABLE" if witnesses else "FINITE_UNANSWERABLE", decision=expected,
                 witness_assignments=[dict(required=witnesses, permitted=witnesses)] if witnesses else [])
    return dict(sources=sources, units=units, edges=edges, requests=[request]), label


def development_fixtures():
    basic = [
        ("east", "v2", True, {"region": "East"}, "nine days", [("prior", "amendment")]),
        ("west", "v1", True, {"region": "West"}, "nine days", []),
        ("prior", "v1", False, {}, None, []),
        ("noise", "v2", False, {}, None, []),
    ]
    yield build_fixture("alt-fixture-keep", basic, ["east", "prior", "west"], "nine days", ["east", "prior"])
    yield build_fixture("alt-fixture-rerank", basic, ["west", "prior", "east"], "nine days", ["east", "prior"])
    yield build_fixture("alt-fixture-acquire", basic, ["east", "noise"], "nine days", ["east", "prior"])
    yield build_fixture("alt-fixture-abstain", basic, ["east", "west"], "ABSTAIN", [], region="North")
    same = [
        ("good", "2", True, {"region": "East"}, "nine days", []),
        ("bad-a", "2", True, {}, "nine days", [("00-a", "applicability"), ("99-west", "applicability")]),
        ("bad-b", "2", True, {}, "nine days", [("00-b", "applicability"), ("99-west", "applicability")]),
        ("good-b", "2", True, {"region": "East"}, "nine days", []),
        ("00-a", "2", False, {}, None, []),
        ("00-b", "2", False, {}, None, []),
        ("99-west", "1", False, {"region": "West"}, None, []),
    ]
    packet, label = build_fixture("alt-fixture-same-answer", same, ["bad-a", "bad-b", "good-b", "good"],
                                  "nine days", ["good"])
    label["witness_assignments"].append(dict(required=["good-b"], permitted=["good-b"]))
    yield packet, label
    bridge = [
        ("east", "v2", True, {}, "nine days", [("schedule-index", "dependency")]),
        ("west", "v2", True, {"region": "West"}, "five days", []),
        ("schedule-index", "v2", False, {}, None, [("registry", "qualification")]),
        ("registry", "v1", False, {"region": "East"}, None, []),
        ("noise", "v2", False, {}, None, []),
    ]
    yield build_fixture("alt-fixture-two-hops", bridge, ["east", "west"],
                        "nine days", ["east", "schedule-index", "registry"])


def exercise(packet, arm):
    data = validate_packet(packet)
    request = packet["requests"][0]
    trace = solve(Index(packet["units"], packet["edges"]), request, arm)
    trace = json.loads(json.dumps(trace))
    usage = validate_trace(trace, request, data[0], data[1][request["family_id"]], data[2])
    return trace, usage


@pytest.mark.parametrize("position,disposition", [(0, "keep"), (1, "rerank"), (2, "acquire"), (3, "abstain")])
def test_expected_dispositions(position, disposition):
    packet, label = list(development_fixtures())[position]
    for arm in ARMS:
        trace, usage = exercise(packet, arm)
        assert trace["disposition"] == disposition
        assert score_case(label, trace, usage) == 1
        assert len(trace["events"]) == usage["actions"]


def test_same_literal_answer_disagreement_choose_binding():
    packet, label = list(development_fixtures())[4]
    proposed, usage = exercise(packet, "assignments")
    premise, baseline_usage = exercise(packet, "premise")
    assert score_case(label, proposed, usage) == 1
    assert score_case(label, premise, baseline_usage) == 1
    assert proposed["events"][2]["plan"]["target"] == "99-west"
    assert premise["events"][2]["plan"]["target"] != "99-west"
    assert usage["actions"] < baseline_usage["actions"]
    disabled, disabled_usage = exercise(packet, "no_disagreement")
    assert score_case(label, disabled, disabled_usage) == 1
    assert disabled["events"][2]["plan"]["target"] != "99-west"


def test_ablation_and_primary_control_keep_options_and_neutral_ties():
    packet, _ = list(development_fixtures())[4]
    first_options = {}
    for arm in ("assignments", "premise", "no_disagreement"):
        trace, _ = exercise(packet, arm)
        first_options[arm] = {row["target"]: row for row in trace["events"][2]["plan"]["options"]}
    assert set(first_options["assignments"]) == {"00-a", "00-b", "99-west"}
    assignments = first_options["assignments"]
    for arm in ("premise", "no_disagreement"):
        compared = first_options[arm]
        assert set(compared) == set(assignments)
        for target, candidate in compared.items():
            assert candidate["priority"][1:] == assignments[target]["priority"][1:]
            for key in ("basis", "target", "affected_roots", "kind_priority"):
                assert candidate[key] == assignments[target][key]
    assert all(row["split"] == 0 for row in first_options["no_disagreement"].values())
    assert assignments["99-west"]["split"] == 4


def test_premise_baseline_observes_a_new_reference_after_retrieval():
    packet, label = list(development_fixtures())[5]
    trace, usage = exercise(packet, "premise")
    assert score_case(label, trace, usage) == 1
    assert [e["plan"]["target"] for e in trace["events"] if e["kind"] == "acquire"] == [
        "schedule-index", "registry"]


def test_label_pair_can_change_witness_without_changing_literal_answer():
    packet, first = next(development_fixtures())
    root = packet["requests"][0]
    alternative = dict(root, case_id="west", question="What is the repair time in West?",
                       conditions={"region": "West"})
    second = dict(first, case_id="west",
                  witness_assignments=[dict(required=["west"], permitted=["west"])])
    packet["requests"].append(alternative)
    _, families, _, requests = validate_packet(packet)
    pair = dict(pair_id="changed", kind="changing", cases=[root["case_id"], "west"])
    labels = dict(cases=[first, second], pairs=[pair])
    assert set(validate_labels(labels, requests, families)) == set(requests)
    trace, usage = exercise(packet, "premise")
    assert score_case(first, trace, usage) == 1
    assert score_case(dict(second, case_id=first["case_id"]), trace, usage) == 0
    pair["kind"] = "invariant"
    with pytest.raises(ValueError, match="pair semantics"):
        validate_labels(labels, requests, families)


@pytest.mark.parametrize("fault", ["inspections", "new_graph", "identity", "clock"])
def test_validator_rejects_unmetered_or_invented_observations(fault):
    packet, _ = list(development_fixtures())[2]
    trace, _ = exercise(packet, "assignments")
    bad = deepcopy(trace)
    if fault == "inspections":
        bad["events"][2]["inspected"].pop()
    elif fault == "new_graph":
        bad["events"][2]["plan"]["target"] = "noise"
    elif fault == "identity":
        bad["evidence"][0]["version"] = "edited"
    else:
        bad["events"][2]["start_ns"] = bad["events"][1]["end_ns"] - 1
    units, families, edges, _ = validate_packet(packet)
    request = packet["requests"][0]
    with pytest.raises(ValueError):
        validate_trace(bad, request, units, families[request["family_id"]], edges)
