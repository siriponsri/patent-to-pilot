"""Hand-checkable protocol tests, independent of any S3 ranking output."""

import copy
import json

import pytest

from scripts.research.s1_packet import OUT, STATES, sha
from scripts.research.s1_scorer import IDENTITY, check_splits, score_case


def rows(name):
    return [json.loads(s) for s in (OUT / name).read_text(encoding="utf-8").splitlines()]


def fixture(lane="proposal"):
    units = {r["unit_id"]: r for r in rows(f"runtime/{lane}/units.jsonl")}
    labels = {r["case_id"]: r for r in rows(f"evaluator/{lane}/labels.jsonl")}
    return units, labels


def answer(label, corpus, ids, decision):
    evidence = [{**{k: corpus[uid][k] for k in IDENTITY}, "role": "support"} for uid in ids]
    return dict(case_id=label["case_id"], decision=decision, evidence=evidence,
                usage=dict(actions=2, inspected=10, candidate_depth=6, returned=len(ids),
                           model_tokens=0, elapsed_ms=17))


@pytest.mark.parametrize("lane", ["proposal", "selection", "dev"])
def test_pool_edits_source_spans_and_label_boundaries(lane):
    units, labels = fixture(lane)
    sources = {r["source_id"]: r for r in rows(f"runtime/{lane}/sources.jsonl")}
    requests = {r["case_id"]: r for r in rows(f"runtime/{lane}/requests.jsonl")}
    assert labels.keys() == requests.keys()
    for u in units.values():
        source = sources[u["source_id"]]
        assert u["text"] == source["text"][u["char_start"]:u["char_end"]]
        assert sha(u["text"].encode()) == u["unit_sha256"]
        assert sha(source["text"].encode()) == u["sha256"] == source["sha256"]
    for edge in rows(f"runtime/{lane}/edges.jsonl"):
        assert edge["basis"] == units[edge["from"]]["text"]
        assert units[edge["from"]]["family_id"] == units[edge["to"]]["family_id"]
    for cid, req in requests.items():
        assert set(req) == {"case_id", "question", "family_id", "language", "seed_pool"}
        pool = req["seed_pool"]
        assert len(set(pool)) == len(pool) == 4
        assert all(units[x]["family_id"] == req["family_id"] for x in pool)
        label = labels[cid]
        if label["status"] == "ANSWERABLE":
            required = set(label["witness_assignments"][0]["required"])
            assert required <= set(units)
            conditions = (required == set(pool[:2]), required == set(pool[-2:]), len(required - set(pool)) == 1)
            assert conditions[STATES.index(label["state"])] and sum(conditions) == 1
    for pair in rows(f"evaluator/{lane}/pairs.jsonl"):
        left, right = pair["cases"]
        assert requests[left]["family_id"] == requests[right]["family_id"]
        assert requests[left]["seed_pool"] == requests[right]["seed_pool"]
        assert (labels[left]["decision"] == labels[right]["decision"]) == (pair["edit"] == "invariant")


@pytest.mark.parametrize("family,first,second,locators,other_locators", [
    ("s1-reed", "5 วัน", "3 วัน", ("ข้อ 2", "ใบแนบ ข"), ("ข้อ 1", "ใบแนบ ก")),
    ("s1-fold", "felt", "cork", ("Claim 2", "Example Birch"), ("Claim 3", "Example Elm")),
])
def test_independent_handwritten_pair_answers(family, first, second, locators, other_locators):
    units, labels = fixture()
    by_locator = {u["locator"]: uid for uid,u in units.items() if u["family_id"] == family}
    a = [by_locator[loc] for loc in locators]
    b = [by_locator[loc] for loc in other_locators]
    requests = rows("runtime/proposal/requests.jsonl")
    if family == "s1-reed":
        q1, q2, q3 = "หากยืมวันที่ 1 เมษายน 2568", "๑ เมษายน ๒๕๖๘", "หากยืมวันที่ 1 เมษายน 2567"
    else:
        q1, q2, q3 = "curved clip use?", "bookmark's curved clip?", "straight clip use?"
    for cue, expected, required in [(q1, first, a), (q2, first, a), (q3, second, b)]:
        req = next(r for r in requests if r["family_id"] == family and cue in r["question"])
        label = labels[req["case_id"]]
        assert score_case(label, answer(label, units, required, expected), units) == 1
        assert score_case(label, answer(label, units, [a[0], b[1]], expected), units) == 0
        assert score_case(label, answer(label, units, required, "ABSTAIN"), units) == 0


def test_malformed_overbudget_and_finite_diagnostic():
    units, labels = fixture()
    label = next(l for l in labels.values() if l["status"] == "ANSWERABLE")
    ids = label["witness_assignments"][0]["required"]
    good = answer(label, units, ids, label["decision"])
    assert score_case(label, good, units) == 1
    for k, value in (("char_end", 0), ("locator", "unknown"), ("sha256", ""), ("text", []),
                     ("unit_id", []), ("role", [])):
        invalid = copy.deepcopy(good)
        invalid["evidence"][0][k] = value
        assert score_case(label, invalid, units) == 0
    for key in good["usage"]:
        invalid = copy.deepcopy(good)
        invalid["usage"][key] = 999999
        assert score_case(label, invalid, units) == 0
    for bad in [None, {}, [], {"usage": None}, {**good, "evidence": None}, {**good, "evidence": [False]}]:
        assert score_case(label, bad, units) == 0
    diagnostic = next(l for l in labels.values() if l["status"] == "FINITE_UNANSWERABLE")
    assert score_case(diagnostic, answer(diagnostic, units, [], "ABSTAIN"), units) == 1
    assert score_case(diagnostic, answer(diagnostic, units, [], "supported"), units) == 0
    assert score_case(diagnostic, answer(diagnostic, units, ids, "ABSTAIN"), units) == 0
    assert score_case({**label, "status": "UNADJUDICATED"}, None, units) is None


def test_equivalent_assignment_and_alternative_only():
    units, labels = fixture()
    label = next(l for l in labels.values() if l["status"] == "ANSWERABLE")
    ids = label["witness_assignments"][0]["required"]
    other = next(uid for uid, unit in units.items() if unit["family_id"] == label["family_id"] and uid not in ids)
    response = answer(label, units, [*ids, other], label["decision"])
    assert score_case(label, response, units) == 0
    response["evidence"][-1]["role"] = "alternative"
    assert score_case(label, response, units) == 1
    alternative = {**label, "witness_assignments": [*label["witness_assignments"],
                    {"required": [other], "permitted": [other]}]}
    assert score_case(alternative, answer(alternative, units, [other], label["decision"]), units) == 1


def test_translated_sibling_and_demo_leakage_are_rejected():
    groups = rows("evaluator/splits.jsonl")
    check_splits(groups)
    sibling = dict(family_id="s1-translated", lane="dev", lineages=["original-fold"])
    with pytest.raises(ValueError, match="crosses lanes"):
        check_splits([*groups, sibling])
    with pytest.raises(ValueError, match="namespace"):
        check_splits([*groups, {**sibling, "family_id": "demo-branch"}])
