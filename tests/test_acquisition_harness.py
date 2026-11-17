"""CPU tests for the Paper 2 acquisition harness. Authored doubles only."""

from __future__ import annotations

import json

import pytest

from patent_to_pilot.research import acquisition_harness as h


class FakeBackend:
    """Deterministic authored corpus of synthetic family ids F00..F39."""

    def __init__(self):
        self.calls: list[tuple] = []

    def dense(self, query, k):
        self.calls.append(("dense", query, k))
        start = len(query) % 5
        return [f"F{(start + i) % 40:02d}" for i in range(k)]

    def bm25(self, query, k):
        self.calls.append(("bm25", query, k))
        return [f"F{(39 - i) % 40:02d}" for i in range(k)] + ["F39"]  # trailing duplicate

    def cpc_codes(self, fid):
        return ["A61B"] if int(fid[1:]) % 2 == 0 else ["G06F"]

    def citations(self, fid, k):
        self.calls.append(("cite", fid, k))
        n = int(fid[1:])
        return [f"F{(n + 7 * i) % 40:02d}" for i in range(1, k + 1)]

    def text(self, fid):
        return f"authored synthetic text for {fid}"


class ScriptedLLM:
    def __init__(self, outputs):
        self.outputs = list(outputs)
        self.calls = 0

    def __call__(self, messages, max_output_tokens):
        self.calls += 1
        if messages[0]["content"].startswith("Rewrite"):
            return "a component that controls fluid pressure"  # fixed-union view, not scripted
        return self.outputs.pop(0) if self.outputs else '{"action": "stop", "args": {}}'


def act(action, **args):
    return json.dumps({"action": action, "args": args})


STEPS = (
    h.Step("dense_search", k=10),
    h.Step("bm25_search", k=10),
    h.Step("llm_view", name="function", instruction="Rewrite as functions."),
    h.Step("dense_search", k=10, query_ref="view:function"),
)
Q = h.Query("q-synthetic-1", "a synthetic valve that regulates pressure")


def make(budget=None, outputs=(), pool_size=15):
    backend = FakeBackend()
    counter = h.whitespace_token_counter
    toolbox = h.ToolBox(backend, h.default_cost_model(counter))
    llm = h.LLMSpec(ScriptedLLM(outputs), counter, max_output_tokens=50)
    budget = budget or h.Budget(max_tool_calls=6, max_llm_calls=4, max_tokens=5000, max_wall_seconds=60)
    fixed = h.FixedUnionController(toolbox, budget, STEPS, pool_size=pool_size, llm=llm)
    agent = h.AgentController(toolbox, budget, llm, pool_size=pool_size, fallback=fixed.run)
    return backend, toolbox, llm, fixed, agent


def test_rrf_fuse_dedupes_caps_and_breaks_ties_deterministically():
    out = h.rrf_fuse([["a", "b", "a"], ["b", "c"]], pool_size=2)
    assert out == ["b", "a"]
    assert h.rrf_fuse([["y"], ["x"]], pool_size=5) == ["x", "y"]


def test_fixed_union_completes_and_respects_pool_cap_without_duplicates():
    _, _, llm, fixed, _ = make()
    res = fixed.run(Q)
    assert res.stop_reason == h.STOP_SEQUENCE_COMPLETE
    assert len(res.ranking) == 15
    assert len(set(res.ranking)) == len(res.ranking)
    assert res.cost.tool_calls == 3 and res.cost.llm_calls == 1
    assert llm.llm.calls == 1


def test_budget_refusal_is_recorded_before_execution_and_not_retried():
    budget = h.Budget(max_tool_calls=1, max_llm_calls=4, max_tokens=5000, max_wall_seconds=60)
    backend, _, _, fixed, _ = make(budget=budget)
    res = fixed.run(Q)
    assert res.stop_reason == h.STOP_BUDGET_REFUSED
    assert [c[0] for c in backend.calls] == ["dense"]  # bm25 never executed
    assert len(res.refusals) == 1 and res.refusals[0]["exceeded"] == ["tool_calls"]
    events = [r["event"] for r in res.trajectory.records]
    assert events.count("refused") == 1 and events[-1] == "stop"
    assert res.cost.tool_calls <= budget.max_tool_calls


def test_token_cap_refuses_llm_call():
    budget = h.Budget(max_tool_calls=6, max_llm_calls=4, max_tokens=10, max_wall_seconds=60)
    _, _, llm, _, agent = make(budget=budget)
    res = agent.run(Q)
    assert llm.llm.calls == 0
    assert res.cost.tokens == 0
    assert res.trajectory.records[1]["event"] == "refused"
    # empty own pool -> fixed-union fallback keeps a ranking
    assert res.stop_reason == h.STOP_EMPTY_POOL
    assert res.ranking_source == h.RANKING_FALLBACK


def test_wall_time_cap_counts_declared_seconds():
    budget = h.Budget(max_tool_calls=6, max_llm_calls=4, max_tokens=5000, max_wall_seconds=0.15)
    _, _, _, fixed, _ = make(budget=budget)
    res = fixed.run(Q)
    assert res.stop_reason == h.STOP_BUDGET_REFUSED
    assert res.refusals[0]["exceeded"] == ["wall_seconds"]


@pytest.mark.parametrize("bad, reason", [
    ("not json", "NOT_JSON"),
    ('{"action": "dense_search"}', "BAD_ENVELOPE"),
    (act("delete_everything"), "UNKNOWN_ACTION"),
    (act("dense_search", query="x"), "BAD_ARGS"),
    (act("dense_search", query="x", k=0), "BAD_K"),
    (act("dense_search", query="x", k=True), "BAD_K"),
    (act("bm25_search", query="  ", k=5), "BAD_QUERY"),
    (act("read", family_id="F99"), "FAMILY_NOT_IN_POOL"),
    (act("cpc_filter", codes=[]), "BAD_CODES"),
    ('{"action": "stop", "args": {}, "extra": 1}', "BAD_ENVELOPE"),
])
def test_invalid_action_stops_and_falls_back_to_fixed_union(bad, reason):
    _, _, llm, fixed, agent = make(outputs=[bad])
    res = agent.run(Q)
    assert res.stop_reason == h.STOP_INVALID_ACTION
    assert res.ranking_source == h.RANKING_FALLBACK
    assert res.ranking == fixed.run(Q).ranking
    invalid = [r for r in res.trajectory.records if r["event"] == "invalid_action"]
    assert len(invalid) == 1 and invalid[0]["reason"] == reason
    assert res.fallback_cost.tool_calls == 3


def test_invalid_action_after_progress_still_falls_back():
    outs = [act("dense_search", query="valve", k=5), "garbage"]
    _, _, _, _, agent = make(outputs=outs)
    res = agent.run(Q)
    assert res.stop_reason == h.STOP_INVALID_ACTION
    assert res.ranking_source == h.RANKING_FALLBACK
    assert res.cost.tool_calls == 1 and res.cost.llm_calls == 2


def test_agent_valid_trajectory_and_stop_reason():
    outs = [
        act("dense_search", query="pressure valve", k=8),
        act("citation_expand", family_id="F05", k=3),
        act("cpc_filter", codes=["A61B"]),
        act("read", family_id="F04"),
        act("stop"),
    ]
    budget = h.Budget(max_tool_calls=6, max_llm_calls=5, max_tokens=50000, max_wall_seconds=60)
    backend, _, _, _, agent = make(budget=budget, outputs=outs)
    res = agent.run(Q)
    assert res.stop_reason == h.STOP_AGENT_STOP
    assert res.ranking_source == h.RANKING_OWN
    assert len(set(res.ranking)) == len(res.ranking) <= 15
    assert res.cost.tool_calls == 4 and res.cost.llm_calls == 5
    tools = [r["tool"] for r in res.trajectory.records if r["event"] == "tool"]
    assert tools == ["dense_search", "citation_expand", "cpc_filter", "read"]
    # query text never written into the trajectory
    assert "pressure valve" not in "\n".join(res.trajectory.lines())


def test_agent_budget_refusal_keeps_own_ranking():
    budget = h.Budget(max_tool_calls=1, max_llm_calls=4, max_tokens=50000, max_wall_seconds=60)
    outs = [act("dense_search", query="valve", k=5), act("bm25_search", query="valve", k=5)]
    backend, _, _, _, agent = make(budget=budget, outputs=outs)
    res = agent.run(Q)
    assert res.stop_reason == h.STOP_BUDGET_REFUSED
    assert res.ranking_source == h.RANKING_OWN
    assert [c[0] for c in backend.calls] == ["dense"]


def test_agent_llm_cap_stops_loop():
    budget = h.Budget(max_tool_calls=20, max_llm_calls=2, max_tokens=50000, max_wall_seconds=60)
    outs = [act("dense_search", query="valve", k=5)] * 5
    _, _, llm, _, agent = make(budget=budget, outputs=outs)
    res = agent.run(Q)
    assert llm.llm.calls == 2
    assert res.stop_reason == h.STOP_BUDGET_REFUSED
    assert res.cost.llm_calls == 2


def test_determinism_same_backends_same_trajectory():
    outs = [act("dense_search", query="valve", k=8), act("bm25_search", query="valve", k=8), act("stop")]
    a = make(outputs=outs)[4].run(Q)
    b = make(outputs=outs)[4].run(Q)
    assert a.trajectory.lines() == b.trajectory.lines()
    assert a.summary() == b.summary()
    f1, f2 = make()[3].run(Q), make()[3].run(Q)
    assert f1.trajectory.lines() == f2.trajectory.lines()


def test_matched_budget_comparison_accounting(tmp_path):
    backend = FakeBackend()
    counter = h.whitespace_token_counter
    toolbox = h.ToolBox(backend, h.default_cost_model(counter))
    outs = [act("dense_search", query="valve", k=8), act("stop"), "bad"]
    llm = h.LLMSpec(ScriptedLLM(outs), counter, max_output_tokens=50)
    budget = h.Budget(max_tool_calls=6, max_llm_calls=4, max_tokens=5000, max_wall_seconds=60)
    queries = [h.Query("q1", "valve a"), h.Query("q2", "pump b")]
    report = h.compare_matched_budget(queries, toolbox=toolbox, budget=budget, steps=STEPS, llm=llm,
                                      pool_size=12, out_dir=tmp_path)
    rows = report["per_query"]
    assert len(rows) == 4
    for row in rows:
        c = row["cost"]
        assert c["tool_calls"] <= budget.max_tool_calls
        assert c["llm_calls"] <= budget.max_llm_calls
        assert c["tokens"] <= budget.max_tokens
        assert row["ranking_size"] <= 12
    assert report["totals"]["agent"]["fallbacks"] == 1
    assert report["totals"]["agent"]["stop_reasons"] == {"AGENT_STOP": 1, "INVALID_ACTION": 1}
    # fallback ranking is the identical fixed-union ranking
    assert report["rankings"]["q2"]["agent"] == report["rankings"]["q2"]["fixed_union"]
    files = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*.jsonl"))
    assert files == ["agent/q1.jsonl", "agent/q2.jsonl", "fixed_union/q1.jsonl", "fixed_union/q2.jsonl"]
    with pytest.raises(FileExistsError):
        h.compare_matched_budget(queries, toolbox=toolbox, budget=budget, steps=STEPS, llm=llm,
                                 pool_size=12, out_dir=tmp_path)


def test_trajectory_write_refuses_overwrite(tmp_path):
    res = make()[3].run(Q)
    path = tmp_path / "t.jsonl"
    sha = res.trajectory.write(path)
    assert len(sha) == 64
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(x)["seq"] for x in lines] == list(range(len(lines)))
    with pytest.raises(FileExistsError):
        res.trajectory.write(path)


def test_cost_validation_rejects_negative_and_nonfinite():
    with pytest.raises(ValueError):
        h.Cost(tokens=-1)
    with pytest.raises(ValueError):
        h.Cost(wall_seconds=float("nan"))
    with pytest.raises(ValueError):
        h.ToolBox(FakeBackend(), {"dense_search": lambda a: h.Cost(tool_calls=1)})
