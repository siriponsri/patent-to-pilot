"""CPU tests for the P2-OA arms and the funnel evaluator. Authored doubles only."""

from __future__ import annotations

import ast
import dataclasses
import inspect
import json
from pathlib import Path

import pytest

from patent_to_pilot.research import funnel_eval as fe
from patent_to_pilot.research import patex_arms as pa

SRC = Path(pa.__file__).parent
D03_ABSTRACT = "Ångström  valve\nregulates pressure."


class FakeStore:
    """Authored synthetic store D00..D59. Search only ever returns D00..D49."""

    def __init__(self):
        self.calls: list[tuple] = []

    def search(self, method, query, top_n):
        self.calls.append((method, top_n))
        if method == "dense":
            start = len(query) % 7
            ids = [f"D{(start + i) % 50:02d}" for i in range(50)]
        else:
            ids = [f"D{49 - i:02d}" for i in range(50)]
        return ids[:top_n]

    def version(self, doc_id):
        n = int(doc_id[1:]) if doc_id[1:].isdigit() else -1
        return f"v1-{doc_id}" if 0 <= n < 60 else None

    def field_text(self, doc_id, field_name):
        if self.version(doc_id) is None:
            return None
        if field_name == "abstract":
            return D03_ABSTRACT if doc_id == "D03" else f"Abstract of {doc_id}: a valve regulates pressure."
        if field_name == "title":
            return f"Title {doc_id}"
        return None


class ScriptedLLM:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.prompts: list[str] = []

    def __call__(self, messages, max_output_tokens):
        self.prompts.append("\n".join(m["content"] for m in messages))
        if messages[0]["content"].startswith("Rewrite"):
            return "a component that controls fluid pressure"
        return self.outputs.pop(0) if self.outputs else json.dumps({"action": "STOP", "args": {}})


def act(action, **args):
    return json.dumps({"action": action, "args": args})


BUDGET = pa.ArmBudget(max_actions=8, max_llm_calls=8, max_tokens=200000, max_wall_seconds=60,
                      max_returned_ids=700, max_visits=4, max_selects=3, max_observation_bytes=2000,
                      max_rerank_docs=100)
POLICY = pa.FixedFunnelPolicy(visit_top=3, select_top=2)
Q = pa.Query("q-synth-1", "pressure valve")  # len 14 -> dense starts at D00
VALID_E2 = [
    act("SEARCH", query="pressure valve", method="dense", top_n=10),
    act("VISIT", id="D03", fields=["abstract"]),
    act("SELECT", id="D03", passage_locations=[{"field": "abstract", "start": 0, "end": 10, "quote": "Ångström"}]),
    act("STOP"),
]


def build(outputs=(), budget=BUDGET):
    store = FakeStore()
    env = pa.PatexEnv(store, pa.default_patex_cost_model(max_visit_bytes=200), max_visit_bytes=200)
    llm = ScriptedLLM(outputs)
    solver = pa.SolverSpec(llm, pa.whitespace_token_counter, max_output_tokens=64)
    e0 = pa.FixedRetrievalArm(env, budget, method="dense", top_n=50, pool_size=30, policy=POLICY)
    deep = pa.DeepRetrievalArm(env, budget, method="dense", top_n=500, reranker=lambda q, ids: list(reversed(ids)),
                               rerank_top=40, pool_size=30, policy=POLICY)
    e1 = pa.MultiQueryArm(env, budget, [pa.QueryTemplate("orig-dense", "dense", 50),
                                        pa.QueryTemplate("orig-bm25", "bm25", 50),
                                        pa.QueryTemplate("func", "dense", 50, "llm", "Rewrite as functions.")],
                          pool_size=30, solver=solver, policy=pa.FixedFunnelPolicy(visit_top=3, select_top=2))
    e2 = pa.ReActArm(env, budget, solver, pool_size=30, fallback=e0.run)
    return store, llm, [e0, deep, e1, e2]


LABELS = [fe.ReferenceLabel("D03", "OUT", "103"), fe.ReferenceLabel("D05", "IN", "102"),
          fe.ReferenceLabel("D59", "OUT", "both")]


# ---- budget parity -------------------------------------------------------


def test_budget_parity_across_arms():
    _, _, arms = build(VALID_E2)
    assert len({id(a.budget) for a in arms}) == 1 and len({id(a.env) for a in arms}) == 1
    report = pa.run_arms([Q], arms)
    caps = BUDGET.limits()
    for row in report["per_query"]:
        for name, cap in caps.items():
            assert row["cost"][name] <= cap, (row["arm"], name)
    assert set(report["totals"]) == {"E0", "E0-deep", "E1", "E2"}
    assert report["totals"]["E2"]["stop_reasons"] == {"AGENT_STOP": 1}


def test_runner_rejects_unequal_budgets_envs_or_pools():
    _, _, arms = build()
    other = dataclasses.replace(BUDGET)  # equal values, different object
    e0b = pa.FixedRetrievalArm(arms[0].env, other, method="dense", top_n=50, pool_size=30)
    with pytest.raises(ValueError, match="budget"):
        pa.run_arms([Q], [arms[1], e0b])
    _, _, arms2 = build()
    with pytest.raises(ValueError, match="environment"):
        pa.run_arms([Q], [arms[0], arms2[1]])
    e0c = pa.FixedRetrievalArm(arms[0].env, BUDGET, method="dense", top_n=50, pool_size=10)
    with pytest.raises(ValueError, match="pool size"):
        pa.run_arms([Q], [arms[1], e0c])


def test_declared_schedule_must_fit_shared_budget():
    store = FakeStore()
    env = pa.PatexEnv(store, pa.default_patex_cost_model(max_visit_bytes=200))
    tight = pa.ArmBudget(max_actions=3, max_llm_calls=0, max_tokens=1000, max_wall_seconds=60)
    with pytest.raises(ValueError, match="exceeds"):
        pa.FixedRetrievalArm(env, tight, method="dense", top_n=10, pool_size=10, policy=POLICY)
    with pytest.raises(ValueError, match="exceeds"):
        pa.MultiQueryArm(env, tight, [pa.QueryTemplate("a", "dense", 5),
                                      pa.QueryTemplate("b", "bm25", 5, "llm", "Rewrite.")],
                         pool_size=10, solver=pa.SolverSpec(ScriptedLLM([]), len, 1))


def test_budget_refusal_before_execution_not_retried():
    budget = pa.ArmBudget(max_actions=8, max_llm_calls=8, max_tokens=200000, max_wall_seconds=60,
                          max_returned_ids=40)
    store, _, arms = build(budget=budget)
    res = arms[0].run(Q)  # E0 top_n=50 > 40 returned-id cap
    assert res.stop_reason == pa.STOP_BUDGET_REFUSED
    assert store.calls == []
    assert len(res.refusals) == 1 and res.refusals[0]["exceeded"] == ["returned_ids"]
    events = [r["event"] for r in res.trajectory.records]
    assert events.count("refused") == 1 and events[-1] == "stop"


def test_visit_cap_stops_fixed_funnel():
    budget = dataclasses.replace(BUDGET, max_visits=2)
    _, _, arms = build(budget=budget)
    res = arms[0].run(Q)
    assert res.stop_reason == pa.STOP_BUDGET_REFUSED
    assert len(res.visited) == 2 and res.selections == ()


# ---- funnel monotonicity --------------------------------------------------


def test_funnel_monotonicity_runtime_and_evaluator():
    _, _, arms = build(VALID_E2)
    report = pa.run_arms([Q], arms)
    for rec in report["funnel_records"]:
        sel = {s["doc_id"] for s in rec["selections"]}
        assert sel <= set(rec["visited"]) <= set(rec["searched"]), rec["arm"]
    ev = fe.evaluate(report["funnel_records"], {Q.query_id: LABELS})
    for row in ev["per_query"]:
        for stratum, cells in row["strata"].items():
            r = [cells[s]["recall"] for s in fe.STAGES]
            if None not in r:
                assert r[2] <= r[1] <= r[0], (row["arm"], stratum)


@pytest.mark.parametrize("script, reason", [
    ([act("SEARCH", query="pressure valve", method="dense", top_n=5), act("VISIT", id="D40", fields=["abstract"])],
     "UNSEARCHED_ID"),
    ([act("SEARCH", query="pressure valve", method="dense", top_n=5),
      act("SELECT", id="D01", passage_locations=[{"field": "abstract", "start": 0, "end": 3}])], "UNVISITED_ID"),
    ([act("SEARCH", query="pressure valve", method="dense", top_n=5), act("VISIT", id="D01", fields=["abstract"]),
      act("SELECT", id="D01", passage_locations=[{"field": "claims", "start": 0, "end": 3}])], "BAD_LOCATIONS"),
    ([act("SEARCH", query="pressure valve", method="dense", top_n=5), act("VISIT", id="D01", fields=["abstract"]),
      act("SELECT", id="D01", passage_locations=[{"field": "abstract", "start": 5, "end": 5}])], "BAD_LOCATIONS"),
    ([act("SEARCH", query="pressure valve", method="dense", top_n=5), act("VISIT", id="D01", fields=["abstract"]),
      act("SELECT", id="D01", passage_locations=[{"field": "abstract", "start": 0, "end": 3}]),
      act("SELECT", id="D01", passage_locations=[{"field": "abstract", "start": 0, "end": 3}])], "ALREADY_SELECTED"),
    ([act("SEARCH", query="pressure valve", method="dense", top_n=5), act("VISIT", id="D01", fields=["bogus"])],
     "BAD_FIELDS"),
    (["not json"], "NOT_JSON"),
    (['{"action": "STOP"}'], "BAD_ENVELOPE"),
    ([act("PURCHASE")], "UNKNOWN_ACTION"),
    ([act("SEARCH", query="x", method="dense")], "BAD_ARGS"),
    ([act("SEARCH", query="  ", method="dense", top_n=5)], "BAD_QUERY"),
    ([act("SEARCH", query="x", method="sparse", top_n=5)], "BAD_METHOD"),
    ([act("SEARCH", query="x", method="dense", top_n=201)], "BAD_TOP_N"),
    ([act("SEARCH", query="x", method="dense", top_n=True)], "BAD_TOP_N"),
])
def test_e2_invalid_action_stops_and_falls_back(script, reason):
    _, _, arms = build(script)
    e0, e2 = arms[0], arms[3]
    res = e2.run(Q)
    assert res.stop_reason == pa.STOP_INVALID_ACTION
    assert res.ranking_source == pa.RANKING_FALLBACK
    fb = e0.run(Q)
    assert res.ranking == fb.ranking and res.searched == fb.searched and res.stages_run == fb.stages_run
    assert res.fallback_cost == fb.cost
    invalid = [r for r in res.trajectory.records if r["event"] == "invalid_action"]
    assert len(invalid) == 1 and invalid[0]["reason"] == reason


def test_e2_empty_search_falls_back():
    _, _, arms = build([act("STOP")])
    res = arms[3].run(Q)
    assert res.stop_reason == pa.STOP_EMPTY_SEARCH and res.ranking_source == pa.RANKING_FALLBACK


# ---- observations ---------------------------------------------------------


def test_observations_logged_without_text():
    _, _, arms = build(VALID_E2)
    res = arms[3].run(Q)
    assert res.stop_reason == pa.STOP_AGENT_STOP and res.ranking_source == pa.RANKING_OWN
    obs = [r for r in res.trajectory.records if r["event"] == "observation"]
    assert [o["action"] for o in obs] == ["SEARCH", "VISIT", "SELECT"]
    s, v, sel = obs
    assert s["returned_ids"] == [f"D{i:02d}" for i in range(10)] and s["versions"][0] == "v1-D00"
    assert s["declared_seconds"] == 0.1
    assert v["version"] == "v1-D03" and v["excerpt_bytes"] == len(D03_ABSTRACT.encode("utf-8"))
    assert v["observation_tokens"] == 4
    assert sel["args"]["passage_locations"][0]["quote_sha256"]
    text = "\n".join(res.trajectory.lines())
    for leaked in ("pressure valve", "Ångström", "regulates"):
        assert leaked not in text
    assert res.ranking[0] == "D03"  # selected ids lead the final ranking


def test_deep_arm_reranks_and_checks_permutation():
    _, _, arms = build()
    res = arms[1].run(Q)
    rr = [r for r in res.trajectory.records if r.get("action") == "RERANK"]
    assert len(rr) == 1 and rr[0]["declared_cost"]["rerank_docs"] == 40
    assert res.ranking[:2] == [s["doc_id"] for s in res.selections]
    assert res.visited == tuple(rr[0]["output_ids"][:3])
    env, budget = arms[0].env, arms[0].budget
    bad = pa.DeepRetrievalArm(env, budget, method="dense", top_n=50, reranker=lambda q, ids: ids[:-1],
                              rerank_top=10, pool_size=30)
    with pytest.raises(ValueError, match="permutation"):
        bad.run(Q)


# ---- label isolation ------------------------------------------------------


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
            names.update(f"{node.module}.{a.name}" for a in node.names)
    return names


def test_label_isolation_runtime_cannot_read_k():
    runtime = _imports(SRC / "patex_arms.py") | _imports(SRC / "acquisition_harness.py")
    assert not any("funnel_eval" in n for n in runtime)
    assert not any("patex_arms" in n or "acquisition_harness" in n for n in _imports(SRC / "funnel_eval.py"))
    assert {f.name for f in dataclasses.fields(pa.Query)} == {"query_id", "text"}
    with pytest.raises(TypeError):
        pa.Query("q", "t", labels=LABELS)  # type: ignore[call-arg]
    for cls in (pa.FixedRetrievalArm, pa.DeepRetrievalArm, pa.MultiQueryArm, pa.ReActArm):
        assert list(inspect.signature(cls.run).parameters) == ["self", "query"]
    # a K-only id (never returned by any tool) never reaches the solver or the logs
    _, llm, arms = build(VALID_E2)
    report = pa.run_arms([Q], arms)
    blob = "\n".join(llm.prompts) + json.dumps(report)
    assert "D59" not in blob


def test_runtime_output_independent_of_labels():
    a = pa.run_arms([Q], build(VALID_E2)[2])
    b = pa.run_arms([Q], build(VALID_E2)[2])
    ev1 = fe.evaluate(a["funnel_records"], {Q.query_id: LABELS})
    ev2 = fe.evaluate(b["funnel_records"], {Q.query_id: LABELS[:1]})
    assert a == b and ev1 != ev2


# ---- determinism ----------------------------------------------------------


def test_determinism_all_arms():
    _, _, a1 = build(VALID_E2)
    _, _, a2 = build(VALID_E2)
    for x, y in zip(a1, a2):
        r1, r2 = x.run(Q), y.run(Q)
        assert r1.trajectory.lines() == r2.trajectory.lines(), x.arm_id
        assert r1.funnel_record() == r2.funnel_record()


def test_trajectories_written_once(tmp_path):
    _, _, arms = build(VALID_E2)
    pa.run_arms([Q], arms, out_dir=tmp_path)
    files = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.jsonl"))
    assert files == sorted(f"{a}/q-synth-1.jsonl" for a in ("E0", "E0-deep", "E1", "E2"))
    _, _, arms = build(VALID_E2)
    with pytest.raises(FileExistsError):
        pa.run_arms([Q], arms, out_dir=tmp_path)


# ---- evaluator ------------------------------------------------------------


def _rec(searched, visited, selected, stages=("search", "visit", "select"), arm="E2", qid="q1"):
    return {"query_id": qid, "arm": arm, "stages_run": list(stages), "searched": searched, "visited": visited,
            "selections": [{"doc_id": d, "version": f"v1-{d}", "locations": []} for d in selected],
            "ranking": searched, "ranking_source": "OWN"}


def test_evaluator_hand_computed_strata():
    rec = _rec([f"D{i:02d}" for i in range(10)], ["D03"], ["D03"])
    row = fe.query_funnel(rec, LABELS)["strata"]
    assert row["ALL"]["search"]["recall"] == pytest.approx(2 / 3)
    assert row["ALL"]["visit"]["recall"] == pytest.approx(1 / 3)
    assert row["OUT"]["select"]["recall"] == pytest.approx(1 / 2)
    assert row["IN"]["search"]["recall"] == 1.0 and row["IN"]["visit"]["recall"] == 0.0
    assert row["102"]["search"]["k"] == 2 and row["103"]["search"]["k"] == 2  # 'both' counts in each
    assert row["OUT-102"]["search"] == {"recall": 0.0, "na": None, "k": 1, "hits": 0}
    assert row["IN-103"]["search"]["na"] == fe.NA_K_EMPTY


def test_evaluator_na_rules_and_unjudged_not_negative():
    no_stage = _rec(["D03", "D05"], [], [], stages=("search",))
    cell = fe.query_funnel(no_stage, LABELS)["strata"]["ALL"]
    assert cell["visit"]["na"] == fe.NA_STAGE_NOT_RUN and cell["search"]["recall"] == pytest.approx(2 / 3)
    assert fe.query_funnel(no_stage, [])["strata"]["ALL"]["search"]["na"] == fe.NA_K_EMPTY
    assert fe.query_funnel(no_stage, None)["strata"]["ALL"]["search"]["na"] == fe.NA_NO_LABELS
    more = _rec(["D03", "D05", "D20", "D21"], [], [], stages=("search",))
    out = fe.query_funnel(more, LABELS, other_citations=["D20"])
    assert out["strata"]["ALL"]["search"]["recall"] == cell["search"]["recall"]  # unjudged do not hurt
    assert out["stage_sizes"]["search"] == {"size": 4, "judged": 2, "unjudged": 2, "other_citation": 1}
    ev = fe.evaluate([no_stage, _rec([], [], [], stages=("search",), qid="q2")], {"q1": LABELS, "q2": []})
    agg = ev["arms"]["E2"]["strata"]["ALL"]["search"]
    assert agg["n_eligible"] == 1 and agg["n_na"] == {fe.NA_K_EMPTY: 1}
    assert agg["macro_recall"] == pytest.approx(2 / 3) and agg["micro_recall"] == pytest.approx(2 / 3)
    with pytest.raises(ValueError):
        fe.query_funnel(no_stage, LABELS + [fe.ReferenceLabel("D03", "IN", "102")])
    with pytest.raises(ValueError):
        fe.ReferenceLabel("D01", "MID", "102")


def test_grounding_checks_are_mechanical():
    store = FakeStore()
    good = {"doc_id": "D03", "version": "v1-D03",
            "locations": [{"field": "abstract", "start": 0, "end": 18, "quote": " Ångström \t valve "}]}
    c = fe.check_selection(store, good)
    assert c["grounded"] and c["locators"][0]["quote_match"] is True
    wrong_quote = dict(good, locations=[{"field": "abstract", "start": 0, "end": 10, "quote": "Angstrom"}])
    assert fe.check_selection(store, wrong_quote)["grounded"] is False
    mid_char = dict(good, locations=[{"field": "abstract", "start": 0, "end": 1}])  # inside 'Å'
    assert fe.check_selection(store, mid_char)["locators"][0]["locator_valid"] is False
    out_of_range = dict(good, locations=[{"field": "abstract", "start": 0, "end": 999}])
    assert fe.check_selection(store, out_of_range)["grounded"] is False
    no_field = dict(good, locations=[{"field": "claims", "start": 0, "end": 2}])
    assert fe.check_selection(store, no_field)["grounded"] is False
    stale = dict(good, version="v0-D03")
    assert fe.check_selection(store, stale)["version_match"] is False
    ghost = {"doc_id": "X99", "version": "v1", "locations": [{"field": "abstract", "start": 0, "end": 2}]}
    assert fe.check_selection(store, ghost)["source_exists"] is False
    no_quote = dict(good, locations=[{"field": "abstract", "start": 0, "end": 10}])
    assert fe.check_selection(store, no_quote)["locators"][0]["quote_match"] is None
    assert fe.check_selection(store, no_quote)["grounded"] is True


def test_grounding_report_on_arm_runs():
    _, _, arms = build(VALID_E2)
    report = pa.run_arms([Q], arms)
    g = fe.grounding_report(report["funnel_records"], FakeStore())
    for arm, row in g["arms"].items():
        assert row["grounded"] == row["selections"], arm
    assert g["arms"]["E2"]["quote_match"] == 1 and g["normalisation"] == fe.NORMALISATION_ID
