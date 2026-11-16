"""CPU tests for E3 (claim-element deficit-aware search). Authored doubles only."""

from __future__ import annotations

import dataclasses
import inspect
import json

import pytest

from patent_to_pilot.research import funnel_eval as fe
from patent_to_pilot.research import patex_arms as pa

ABSTRACTS = {
    "D03": "Ångström  valve\nregulates pressure.",
    "D07": "A force sensor measures fluid force.",
    "D41": "A controller adjusts the actuator.",
}
KEYWORDS = {"e1": "valve", "e2": "sensor", "e3": "controller"}


class HopStore:
    """Authored store D00..D59; search and hops only ever return D00..D49."""

    def __init__(self):
        self.calls: list[tuple] = []

    def search(self, method, query, top_n):
        self.calls.append(("search", method, top_n))
        start = len(query) % 7 if method == "dense" else 0
        ids = [f"D{(start + i) % 50:02d}" for i in range(50)] if method == "dense" else \
              [f"D{49 - i:02d}" for i in range(50)]
        return ids[:top_n]

    def neighbours(self, doc_id, relation, top_n):
        self.calls.append(("hop", relation, doc_id, top_n))
        n = int(doc_id[1:])
        shift = 20 if relation == "cpc" else 36
        return [f"D{(n + shift + i) % 50:02d}" for i in range(top_n)]

    def version(self, doc_id):
        n = int(doc_id[1:]) if doc_id[1:].isdigit() else -1
        return f"v1-{doc_id}" if 0 <= n < 60 else None

    def field_text(self, doc_id, field_name):
        if self.version(doc_id) is None:
            return None
        if field_name == "abstract":
            return ABSTRACTS.get(doc_id, f"Abstract of {doc_id}: a valve regulates pressure.")
        if field_name == "claims":
            return f"1. An apparatus {doc_id}."
        return None


def splitter(text):
    return [pa.ClaimElement(f"e{i}", part.strip()) for i, part in enumerate(text.split(";"), start=1)]


REFORM = {"e1": "hold fluid", "e2": "measure fluid force", "e3": "regulate operation"}


def reformulator(el):
    return REFORM[el.element_id]


class Extractor:
    """Proposes the first keyword occurrence; ``noisy`` adds bad proposals first."""

    def __init__(self, noisy=False, silent=False):
        self.noisy, self.silent = noisy, silent
        self.seen: list[tuple[str, str, tuple]] = []

    def __call__(self, el, doc, excerpts):
        self.seen.append((el.element_id, doc, tuple(sorted(excerpts))))
        if self.silent:
            return []
        text = excerpts.get("abstract", "")
        pos = text.encode("utf-8").find(KEYWORDS[el.element_id].encode("utf-8"))
        if pos < 0:
            return []
        end = pos + len(KEYWORDS[el.element_id].encode("utf-8"))
        good = {"field": "abstract", "start": pos, "end": end, "quote": KEYWORDS[el.element_id]}
        if not self.noisy:
            return [good]
        return [dict(good, quote="wrong words"), dict(good, end=10_000), {"field": "abstract"}, good]


BUDGET = pa.ArmBudget(max_actions=20, max_llm_calls=8, max_tokens=200000, max_wall_seconds=60,
                      max_returned_ids=700, max_visits=8, max_selects=3, max_observation_bytes=4000,
                      max_rerank_docs=100)
WIDE = dataclasses.replace(BUDGET, max_actions=40, max_visits=20, max_observation_bytes=20000)
Q3 = pa.Query("q-ceds-1", "a valve body; a pressure sensor; a controller")
EXPECTED_MOVES = [["e1", "element_query"], ["e2", "element_query"], ["e3", "element_query"],
                  ["e2", "function_reformulation"], ["e3", "function_reformulation"],
                  ["e3", "cpc_hop"], ["e3", "citation_hop"]]


def make_env(store=None):
    store = store or HopStore()
    return store, pa.PatexEnv(store, pa.default_patex_cost_model(max_visit_bytes=200), max_visit_bytes=200)


def make_e3(env, budget=BUDGET, extractor=None, **kw):
    extractor = extractor or Extractor()
    arm = pa.DeficitAwareArm(env, budget, splitter=splitter, extractor=extractor, reformulator=reformulator,
                             pool_size=30, top_n=5, hop_top_n=3, **kw)
    return arm, extractor


def test_element_coverage_bookkeeping():
    store, env = make_env()
    arm, ex = make_e3(env)
    res = arm.run(Q3)
    assert res.stop_reason == pa.STOP_ALL_COVERED
    assert res.extras["moves"] == EXPECTED_MOVES
    assert res.extras["coverage"] == {"e1": ["D05"], "e2": ["D07"], "e3": ["D41"]}
    assert res.extras["covered"] == res.extras["elements"] == 3 and res.extras["rejected"] == {}
    assert [s["doc_id"] for s in res.selections] == ["D05", "D07", "D41"]
    assert res.visited == ("D05", "D03", "D06", "D07", "D04", "D25", "D41")
    # hops seeded from the earliest visited doc
    assert ("hop", "cpc", "D05", 3) in store.calls and ("hop", "citation", "D05", 3) in store.calls
    # selected passages are mechanically grounded for the evaluator too
    for sel in res.selections:
        assert fe.check_selection(store, sel)["grounded"]
    # funnel order holds and the extractor only ever saw visited documents
    assert {s["doc_id"] for s in res.selections} <= set(res.visited) <= set(res.searched)
    assert {doc for _, doc, _ in ex.seen} <= set(res.visited)
    # covered elements are not re-extracted
    assert [e for e, d, _ in ex.seen if d == "D41"] == ["e3"]


def test_bad_proposals_rejected_and_counted():
    _, env = make_env()
    arm, _ = make_e3(env, extractor=Extractor(noisy=True), max_proposals=4)
    res = arm.run(Q3)
    assert res.stop_reason == pa.STOP_ALL_COVERED
    assert res.extras["rejected"] == {"BAD_SHAPE": 3, "OUT_OF_VISIBLE": 3, "QUOTE_MISMATCH": 3}
    arm2, _ = make_e3(make_env()[1], budget=WIDE, extractor=Extractor(noisy=True), max_proposals=3)
    res2 = arm2.run(Q3)  # the good proposal is 4th: never considered
    assert res2.extras["covered"] == 0 and res2.stop_reason == pa.STOP_MOVES_EXHAUSTED


@pytest.mark.parametrize("proposal, reason", [
    ({"field": "abstract", "start": 0, "end": 1, "quote": "Å"}, "OFF_BOUNDARY"),
    ({"field": "claims", "start": 0, "end": 2, "quote": "Ån"}, "FIELD_NOT_VISITED"),
    ({"field": "abstract", "start": 0, "end": 2, "quote": "  "}, "EMPTY_QUOTE"),
    ({"field": "abstract", "start": 0, "end": True, "quote": "x"}, "BAD_SHAPE"),
    ({"field": "abstract", "start": 0, "end": 18, "quote": "Ångström valve"}, None),
])
def test_verify_passage_rules(proposal, reason):
    ok, why = pa.verify_passage({"abstract": ABSTRACTS["D03"]}, proposal)
    assert why == reason and ok is (reason is None)


def test_moves_exhausted_when_nothing_covers():
    _, env = make_env()
    arm, _ = make_e3(env, budget=WIDE, extractor=Extractor(silent=True))
    res = arm.run(Q3)
    assert res.stop_reason == pa.STOP_MOVES_EXHAUSTED
    assert len(res.extras["moves"]) == 12 and res.selections == ()


def test_budget_refusal_recorded_and_not_retried():
    budget = dataclasses.replace(BUDGET, max_actions=4)
    store, env = make_env()
    arm, _ = make_e3(env, budget=budget)
    res = arm.run(Q3)
    # SEARCH, VISIT, SELECT, SEARCH admitted; the next VISIT is refused
    assert res.stop_reason == pa.STOP_BUDGET_REFUSED
    assert len(res.refusals) == 1 and res.refusals[0]["what"] == "VISIT"
    assert res.refusals[0]["exceeded"] == ["actions"]
    assert [r["event"] for r in res.trajectory.records].count("refused") == 1
    assert sum(c[0] == "search" for c in store.calls) == 2
    assert res.cost.actions == 4


def test_costed_extractor_refused_by_llm_cap():
    budget = dataclasses.replace(BUDGET, max_llm_calls=1)
    _, env = make_env()
    arm, ex = make_e3(env, budget=budget, extract_cost=pa.ActionCost(llm_calls=1, tokens=100))
    res = arm.run(Q3)
    assert res.stop_reason == pa.STOP_BUDGET_REFUSED
    assert res.refusals[0]["what"] == "EXTRACT" and res.refusals[0]["exceeded"] == ["llm_calls"]
    assert len(ex.seen) == 1 and res.cost.llm_calls == 1


def test_same_budget_as_other_arms_and_within_caps():
    store, env = make_env()
    e3, _ = make_e3(env)
    e0 = pa.FixedRetrievalArm(env, BUDGET, method="dense", top_n=50, pool_size=30,
                              policy=pa.FixedFunnelPolicy(visit_top=3, select_top=2))
    deep = pa.DeepRetrievalArm(env, BUDGET, method="dense", top_n=500, reranker=lambda q, ids: list(reversed(ids)),
                               rerank_top=40, pool_size=30)
    e1 = pa.MultiQueryArm(env, BUDGET, [pa.QueryTemplate("a", "dense", 50), pa.QueryTemplate("b", "bm25", 50)],
                          pool_size=30)
    llm = lambda m, n: json.dumps({"action": "STOP", "args": {}})
    e2 = pa.ReActArm(env, BUDGET, pa.SolverSpec(llm, pa.whitespace_token_counter, 16), pool_size=30,
                     fallback=e0.run)
    arms = [e0, deep, e1, e2, e3]
    assert len({id(a.budget) for a in arms}) == 1
    report = pa.run_arms([Q3], arms)
    for row in report["per_query"]:
        for name, cap in BUDGET.limits().items():
            assert row["cost"][name] <= cap, (row["arm"], name)
    e3_row = next(r for r in report["per_query"] if r["arm"] == "E3")
    assert e3_row["stop_reason"] == pa.STOP_ALL_COVERED and e3_row["extras"]["covered"] == 3
    other = dataclasses.replace(BUDGET)
    with pytest.raises(ValueError, match="budget"):
        pa.run_arms([Q3], [e0, make_e3(env, budget=other)[0]])


def test_e3_never_reads_gold():
    assert list(inspect.signature(pa.DeficitAwareArm.run).parameters) == ["self", "query"]
    params = set(inspect.signature(pa.DeficitAwareArm.__init__).parameters)
    assert not params & {"labels", "gold", "qrels", "k", "references"}
    # D59 is a K-only id: no tool returns it, so nothing E3 does can mention it
    store, env = make_env()
    arm, ex = make_e3(env)
    res = arm.run(Q3)
    blob = "\n".join(res.trajectory.lines()) + json.dumps(res.extras) + json.dumps(ex.seen)
    assert "D59" not in blob
    labels_a = [fe.ReferenceLabel("D59", "OUT", "103")]
    labels_b = [fe.ReferenceLabel("D41", "OUT", "103"), fe.ReferenceLabel("D59", "IN", "102")]
    rec = res.funnel_record()
    assert fe.evaluate([rec], {Q3.query_id: labels_a}) != fe.evaluate([rec], {Q3.query_id: labels_b})
    again = make_e3(make_env()[1])[0].run(Q3)
    assert again.funnel_record() == rec


def test_e3_deterministic():
    r1 = make_e3(make_env()[1], extractor=Extractor(noisy=True), max_proposals=4)[0].run(Q3)
    r2 = make_e3(make_env()[1], extractor=Extractor(noisy=True), max_proposals=4)[0].run(Q3)
    assert r1.trajectory.lines() == r2.trajectory.lines()
    assert r1.summary() == r2.summary()
    text = "\n".join(r1.trajectory.lines())
    for leaked in ("a valve body", "pressure sensor", "controller adjusts", "measure fluid force"):
        assert leaked not in text


def test_e3_config_validation():
    _, env = make_env()
    with pytest.raises(ValueError):
        make_e3(env, moves=("teleport",))
    with pytest.raises(ValueError):
        make_e3(env, moves=())
    bad = pa.DeficitAwareArm(env, BUDGET, splitter=lambda t: [], extractor=Extractor(), reformulator=reformulator,
                             pool_size=30)
    with pytest.raises(ValueError, match="splitter"):
        bad.run(Q3)
