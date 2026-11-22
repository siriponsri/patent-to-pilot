"""P2-T03: one bounded source-relation search action. SYNTHETIC TESTS ONLY.

Every packet here is authored and fictional (texts start with "SYNTHETIC"; the Workbench tests reuse the P0-T06
synthetic letter/annex packet). They check engineering behaviour -- exact requirements, deterministic selection, one
budgeted eligible search, real before/after membership, coverage re-check, original-query-only rerank, hypothesis
rejection and schema validity -- never retrieval quality. No research data is read and no number here is a result.
"""
from __future__ import annotations

import copy
import dataclasses
import itertools
import json
import sqlite3

import pytest

from patent_to_pilot.workbench import relation_search as R
from patent_to_pilot.workbench import trace_slice as T
from patent_to_pilot.workbench.core import EvidenceCore, ValidationFailed

# --------------------------------------------------------------------------- authored synthetic pure-form packet
QUERY = "SYNTHETIC: find prior art where the sensor closes the valve and the temperature exceeds the threshold."
R1, R2 = "the sensor closes the valve", "the temperature exceeds the threshold"
DOCS = {
    "SYN-Q": "SYNTHETIC Q. The sensor closes the valve when the temperature exceeds the threshold.",
    "SYN-D1": "SYNTHETIC D1. A sensor is mounted on the valve housing of the pump.",
    "SYN-D2": "SYNTHETIC D2. Temperature readings are logged every minute.",
    "SYN-D3": "SYNTHETIC D3. The sensor closes the valve once the temperature exceeds the threshold.",
    "SYN-D4": "SYNTHETIC D4. Shutoff shutoff shutoff relay shutoff.",
    "SYN-D5": "SYNTHETIC D5. Valve housing sensor closes in the same family.",
    "SYN-D6": "SYNTHETIC D6. The sensor closes the valve housing vent.",
    "SYN-D7": "SYNTHETIC D7. Valve housing materials.",
}
GROUPS = {"SYN-Q": "FAM-Q", "SYN-D5": "FAM-Q", "SYN-D1": "FAM-1", "SYN-D2": "FAM-2", "SYN-D3": "FAM-3",
          "SYN-D4": "FAM-4", "SYN-D6": "FAM-6", "SYN-D7": "FAM-7"}
DATES = {"SYN-Q": "2026-01-01", "SYN-D1": "2020-01-01", "SYN-D2": "2021-01-01", "SYN-D3": "2022-01-01",
         "SYN-D4": "2023-01-01", "SYN-D5": "2019-01-01", "SYN-D6": "2027-03-01"}   # SYN-D7: no date
SEED = ["SYN-D1", "SYN-D2"]
EVENT_TIME = "2026-11-22T00:00:00.000Z"


def span_ev(doc: str, phrase: str) -> T.SourceEvidence:
    s = DOCS[doc].index(phrase)
    return T.SourceEvidence(f"ev:{doc}#body[{s}:{s + len(phrase)}]", f"{doc}#body", s, s + len(phrase), phrase)


EV_D1_REF = span_ev("SYN-D1", "valve housing")
EV_D1_SENSOR = span_ev("SYN-D1", "A sensor is mounted")
EV_D2_REF = span_ev("SYN-D2", "Temperature readings")
EV_D2_LOG = span_ev("SYN-D2", "logged every minute")
EV_D3_BIND = span_ev("SYN-D3", "The sensor closes the valve")
HYP = T.SearchHypothesis("hyp:syn:valve->shutoff", "shutoff", "authored-synonym-table (synthetic; no model call)",
                         None, (EV_D1_REF.evidence_id,))


def qreq() -> R.QueryRequirements:
    return R.QueryRequirements.bind("syn-q-1", QUERY, [("r1", R1), ("r2", R2)])


def states_before() -> list[R.RelationState]:
    return [
        R.RelationState("r1:binding:D1", "r1", "feature_binding", "unresolved", "SYN-D1", "valve housing",
                        EV_D1_REF.evidence_id, ("sensor", "closes", "valve"), (EV_D1_REF.evidence_id,)),
        R.RelationState("r2:binding:D2", "r2", "feature_binding", "unresolved", "SYN-D2", "Temperature readings",
                        EV_D2_REF.evidence_id, ("temperature", "exceeds", "threshold"), (EV_D2_REF.evidence_id,)),
        R.RelationState("r1:mention:D1", "r1", "feature_mention", "supported", "SYN-D1",
                        evidence_ids=(EV_D1_SENSOR.evidence_id,)),
        R.RelationState("r2:contra:D2", "r2", "feature_binding", "contradicted", "SYN-D2",
                        evidence_ids=(EV_D2_LOG.evidence_id,)),
        R.RelationState("r1:closure:D1", "r1", "in_version_closure", "unresolved", "SYN-D1", anchor_terms=("valve",),
                        actionable=False),
    ]


def assessor(calls: list | None = None):
    """Authored synthetic coverage check: r1's binding counts as supported once SYN-D3 is in the pool."""
    def assess(after: tuple) -> list[R.RelationState]:
        if calls is not None:
            calls.append(after)
        out = []
        for s in states_before():
            if s.relation_key == "r1:binding:D1" and "SYN-D3" in after:
                s = dataclasses.replace(s, status="supported", evidence_ids=(EV_D3_BIND.evidence_id,))
            out.append(s)
        return out
    return assess


def mask(**kw) -> R.EligibilityMask:
    args = dict(profile_id="syn-own-family-and-date", exclude_ids={"SYN-Q"}, exclude_groups={"FAM-Q"},
                grouping="family", group_of=GROUPS, dates=DATES, date_cutoff="2026-01-01", missing_date="exclude")
    args.update(kw)
    return R.EligibilityMask(**args)


def registry() -> R.EvidenceRegistry:
    return R.EvidenceRegistry([EV_D1_REF, EV_D1_SENSOR, EV_D2_REF, EV_D2_LOG, EV_D3_BIND])


def context() -> R.TraceContext:
    srcs = tuple(R.TraceSource(d, "v1", "text/plain", t.encode("utf-8"), t, "authored-synthetic-text-v1",
                               "utf8-unmodified", (), GROUPS[d]) for d, t in DOCS.items())
    nodes = tuple(R.TraceNode(f"{d}#body", d, "v1", "paragraph", 0, len(t)) for d, t in DOCS.items())
    idx = R.make_index_identity("inmem-bm25:syn-p2t03", "syn-p2t03-corpus-1", "lowercase-word-tokens",
                                "whole-document", lexical_config={"algorithm": "BM25 (in-memory reference)",
                                                                  "tokenizer_id": "python-re-word-lower",
                                                                  "version": "1", "k1": 1.2, "b": 0.75})
    return R.TraceContext(run_id="synthetic-p2-t03-pure", mode="synthetic_demo", index=idx, identity_unit="document",
                          sources=srcs, nodes=nodes, assessor_id="authored-synthetic-assessor (not a judgement)",
                          route_id="inmem-bm25-global", event_time=EVENT_TIME)


class CountingBackend:
    def __init__(self, docs=DOCS) -> None:
        self.idx = R.InMemoryBM25(docs)
        self.calls: list = []

    def __call__(self, query, limit, eligibility):
        self.calls.append((query.text, limit))
        return self.idx.search(query, limit, eligibility)


class RecordingReranker:
    def __init__(self) -> None:
        self.inner = R.bm25_reranker(DOCS)
        self.requests: list = []

    def __call__(self, request, ids):
        self.requests.append((request, ids))
        return self.inner(request, ids)


def step(relations=None, budget=None, elig=None, reg=None, backend=None, reranker=None, calls=None, **kw):
    reg = reg or registry()
    return R.relation_search_step(
        requirements=kw.pop("requirements", qreq()), relations=relations if relations is not None else states_before(),
        pool_before=kw.pop("pool_before", SEED), search=backend or CountingBackend(),
        assess=kw.pop("assess", assessor(calls)), rerank=reranker or R.bm25_reranker(DOCS),
        budget=budget if budget is not None else R.ActionBudget(1), eligibility=elig or mask(), evidence=reg,
        hypotheses_for=kw.pop("hypotheses_for", lambda rel: [HYP] if rel.relation_key == "r1:binding:D1" else []),
        result_limit=kw.pop("result_limit", 5), fetch_limit=kw.pop("fetch_limit", 20),
        emit=kw.pop("emit", R.trace_emitter(context(), reg)), **kw)


# --------------------------------------------------------------------------- requirements
def test_requirements_are_exact_spans_and_preserved_unchanged():
    qr = qreq()
    assert [QUERY[r.start:r.end] for r in qr.requirements] == [R1, R2]
    with pytest.raises(ValidationFailed) as e:
        R.QueryRequirements("q", QUERY, (R.Requirement("r1", 0, 5, "WRONG"),))
    assert e.value.code == "requirement_not_bound"
    with pytest.raises(ValidationFailed):
        R.QueryRequirements.bind("q", QUERY, [("r", "the")])          # occurs more than once: refused, not guessed
    with pytest.raises(dataclasses.FrozenInstanceError):
        qr.text = "changed"                                             # type: ignore[misc]
    rec = step()
    assert rec["requirements"] == qr.as_record() and rec["requirements_sha256"] == qr.sha256()
    ev = rec["trace_event"]
    assert ev["original_query"] == {"query_id": "syn-q-1", "text": QUERY}
    for a in ev["runtime_assessments"]:
        sp = a["requirement_span"]
        assert QUERY[sp["start"]:sp["end"]] == R1


# --------------------------------------------------------------------------- named, versioned, pinned policy
def test_policy_is_named_versioned_and_pinned():
    assert R.POLICY_V1.name == "ptp-relsel-first-unresolved/1.0.0"
    assert R.POLICY_V1.fingerprint() == R.POLICY_V1_SHA256 == R.PINNED_POLICY_SHA256[R.POLICY_V1.name]
    assert R.POLICY_V1.max_expansion_searches == 1
    rec = step()
    assert rec["policy"]["name"] == R.POLICY_V1.name and rec["policy"]["sha256"] == R.POLICY_V1_SHA256
    assert rec["action_id"].startswith("ptp-relsel-first-unresolved-v1.0.0:")
    edited = dataclasses.replace(R.POLICY_V1, selection_rule=R.POLICY_V1.selection_rule[:2])
    with pytest.raises(ValidationFailed) as e:
        step(policy=edited)
    assert e.value.code == "policy_unknown"


# --------------------------------------------------------------------------- deterministic selection
def test_selection_is_deterministic_and_independent_of_input_order():
    base = step(relations=states_before())
    assert base["selection"]["selected_relation_key"] == "r1:binding:D1"
    assert [c["relation_key"] for c in base["selection"]["considered"]] == ["r1:binding:D1", "r2:binding:D2"]
    assert {s["relation_key"]: s["reason"] for s in base["selection"]["skipped"]} == {
        "r1:closure:D1": "not_search_actionable", "r1:mention:D1": "status_supported",
        "r2:contra:D2": "status_contradicted"}
    ref = json.dumps(base, sort_keys=True)
    for perm in itertools.permutations(states_before()):
        assert json.dumps(step(relations=list(perm)), sort_keys=True) == ref


def test_selection_rule_order_keys_and_skips():
    qr, reg = qreq(), registry()
    ev1b = span_ev("SYN-D1", "pump")
    reg.add_evidence(ev1b)

    def st(key, rid, frm, ref=None, ev=None, anchors=("valve",)):
        return R.RelationState(key, rid, "feature_binding", "unresolved", frm, ref, ev, anchors)
    sel = lambda states, **kw: R.select_relation(R.POLICY_V1, qr, states, SEED, reg, **kw)["selected"].relation_key  # noqa: E731,E501
    # (a) requirement position beats pool rank
    assert sel([st("z", "r2", "SYN-D1", anchors=("temperature",)), st("y", "r1", "SYN-D2")]) == "y"
    # (b) pool rank of the holding candidate (absent from the pool ranks last)
    assert sel([st("a", "r1", "SYN-D2"), st("b", "r1", "SYN-D1"), st("c", "r1", "SYN-NOT-IN-POOL")]) == "b"
    # (c) reference offset inside the same holder, then (d) relation key
    assert sel([st("m", "r1", "SYN-D1", "pump", ev1b.evidence_id),
                st("n", "r1", "SYN-D1", "valve housing", EV_D1_REF.evidence_id)]) == "n"
    assert sel([st("k2", "r1", "SYN-D1"), st("k1", "r1", "SYN-D1")]) == "k1"
    # already attempted and no-material relations are skipped
    out = R.select_relation(R.POLICY_V1, qr, [st("k1", "r1", "SYN-D1"), st("k2", "r1", "SYN-D2", anchors=())],
                            SEED, reg, attempted={"k1"})
    assert out["selected"] is None
    assert {s["relation_key"]: s["reason"] for s in out["skipped"]} == {"k1": "already_attempted",
                                                                         "k2": "no_search_material"}


# --------------------------------------------------------------------------- budget: exactly one expansion search
def test_exactly_one_expansion_search_within_the_action_budget():
    backend, budget = CountingBackend(), R.ActionBudget(1)
    rec = step(backend=backend, budget=budget)
    assert len(backend.calls) == 1 and rec["search_calls"] == 1 and rec["outcome"] == "searched"
    assert backend.calls[0] == (rec["query"]["submitted_text"], 20)
    assert rec["budget_before"]["used"] == 0 and rec["budget_after"] == {"limit": 1, "used": 1,
                                                                          "spent": ["relation_search"]}
    # a second action on the spent budget issues no search (the other unresolved relation stays untouched)
    again = step(backend=backend, budget=budget, attempted={"r1:binding:D1"})
    assert again["outcome"] == "budget_exhausted" and again["search_calls"] == 0 and len(backend.calls) == 1
    assert again["selection"]["selected_relation_key"] == "r2:binding:D2" and again["query"] is None
    with pytest.raises(R.BudgetExhausted):
        budget.consume("relation_search")
    # a zero budget: no search and no hypothesis generation
    gen = []
    zero = step(budget=R.ActionBudget(0), hypotheses_for=lambda rel: gen.append(rel) or [HYP])
    assert zero["outcome"] == "budget_exhausted" and zero["search_calls"] == 0 and gen == []


def test_no_unresolved_relation_means_no_search():
    backend = CountingBackend()
    rels = [s for s in states_before() if s.status != "unresolved" or not s.actionable]
    rec = step(relations=rels, backend=backend)
    assert rec["outcome"] == "no_unresolved_relation" and backend.calls == [] and rec["trace_event"] is None


# --------------------------------------------------------------------------- eligibility masks
def test_eligibility_mask_filters_the_expansion_route_and_is_recorded():
    rec = step()
    excluded = {x["candidate_id"]: x["reason"] for x in rec["search"]["excluded_ineligible"]}
    assert excluded == {"SYN-Q": "excluded_id", "SYN-D5": "excluded_group:FAM-Q", "SYN-D6": "date_not_before_cutoff",
                        "SYN-D7": "missing_date"}
    ranked = [x["candidate_id"] for x in rec["search"]["backend_ranked"]]
    assert set(excluded) <= set(ranked)                     # the backend really returned them; the mask removed them
    assert not set(excluded) & set(rec["candidate_delta"]["after_ids"])
    m = mask()
    assert rec["trace_event"]["action"]["eligibility_profile_id"] == m.trace_id
    assert rec["eligibility"]["sha256"] == m.fingerprint() != mask(date_cutoff="2027-12-31").fingerprint()
    # a declared 'include' rule for missing dates admits SYN-D7
    inc = step(elig=mask(missing_date="include"))
    assert "SYN-D7" in inc["candidate_delta"]["returned_ids"]
    assert "SYN-D7" not in {x["candidate_id"] for x in inc["search"]["excluded_ineligible"]}
    # the same mask must already hold for the pool before the action
    with pytest.raises(R.IneligibleCandidate):
        step(pool_before=["SYN-D1", "SYN-D6"])
    with pytest.raises(ValidationFailed):
        R.EligibilityMask(profile_id="x", missing_date="assume_eligible")


# --------------------------------------------------------------------------- merge and new-candidate accounting
def test_merge_records_real_before_after_membership_and_new_candidates():
    rec = step()
    d = rec["candidate_delta"]
    assert d["before_ids"] == SEED
    assert d["returned_ids"] == rec["search"]["eligible_returned"]
    eligible_backend = [x["candidate_id"] for x in rec["search"]["backend_ranked"]
                        if x["candidate_id"] not in {e["candidate_id"] for e in rec["search"]["excluded_ineligible"]}]
    assert d["returned_ids"] == eligible_backend[:5]
    assert d["after_ids"] == d["before_ids"] + [x for x in d["returned_ids"] if x not in d["before_ids"]]
    assert d["new_ids"] == [x for x in d["returned_ids"] if x not in d["before_ids"]]
    assert "SYN-D1" in d["returned_ids"] and "SYN-D1" not in d["new_ids"]     # re-found is not new
    assert set(d["new_ids"]) == {"SYN-D4", "SYN-D3"}
    assert {k: rec["trace_event"]["candidate_delta"][k] for k in d} == d

    def dup_backend(query, limit, eligibility):
        return [("SYN-D3", 2.0), ("SYN-D3", 1.0), ("SYN-D1", 0.5)]
    dd = step(backend=dup_backend)["candidate_delta"]
    assert dd["returned_ids"] == ["SYN-D3", "SYN-D1"] and dd["new_ids"] == ["SYN-D3"]


# --------------------------------------------------------------------------- coverage re-check
def test_coverage_is_rechecked_once_on_the_merged_pool():
    calls: list = []
    rec = step(calls=calls)
    assert calls == [tuple(rec["candidate_delta"]["after_ids"])]
    c = rec["coverage"]
    assert (c["selected_before"], c["selected_after"]) == ("unresolved", "supported")
    assert (c["requirement_before"], c["requirement_after"]) == ("unresolved", "unresolved")  # r1 closure still open
    statuses = [a["status"] for a in rec["trace_event"]["runtime_assessments"]]
    assert statuses == ["unresolved", "unresolved"]
    after = {s["relation_key"]: s for s in c["after"]}
    assert after["r1:binding:D1"]["evidence_ids"] == [EV_D3_BIND.evidence_id]


# --------------------------------------------------------------------------- rerank against the original query only
def test_rerank_uses_only_the_original_query_so_expansion_cannot_win_by_self_matching():
    rr = RecordingReranker()
    rec = step(reranker=rr)
    ((request, ids),) = rr.requests
    assert request == R.RerankRequest("syn-q-1", QUERY, (R1, R2)) and request.basis == R.RERANK_BASIS
    assert ids == tuple(rec["candidate_delta"]["after_ids"])
    seen = json.dumps(dataclasses.asdict(request)).lower()
    for term in rec["query"]["terms"]:
        if term["origin"] != "original_requirement":
            assert term["text"].lower() not in seen            # "valve housing", "shutoff" never reach the reranker
    # SYN-D4 matches only the generated hypothesis: first by the expansion query, last after the original-query rerank
    assert rec["search"]["backend_ranked"][0]["candidate_id"] == "SYN-D4"
    assert rec["candidate_delta"]["returned_ids"][0] == "SYN-D4"
    ranking = rec["rerank"]["ranking"]
    order = [r["candidate_id"] for r in ranking]
    assert order[0] == "SYN-D3" and order[-1] == "SYN-D4" and set(order[1:3]) == {"SYN-D1", "SYN-D2"}
    assert ranking[-1]["score"] is None and ranking[0]["is_new"] is True and ranking[0]["rerank_position"] == 1
    assert all(r["score"] is not None for r in ranking[:3])
    assert rec["rerank"]["final_ids"] == order
    assert step(final_k=2)["rerank"]["final_ids"] == order[:2]
    with pytest.raises(ValidationFailed) as e:
        step(reranker=lambda request, ids: {"SYN-OUTSIDE": 1.0})
    assert e.value.code == "rerank_output"


# --------------------------------------------------------------------------- generated hypotheses are never evidence
def test_a_generated_hypothesis_can_never_be_cited():
    rec = step()
    ev = rec["trace_event"]
    assert [h["hypothesis_id"] for h in ev["hypotheses"]] == [HYP.hypothesis_id]
    assert HYP.hypothesis_id in ev["action"]["query_artifact_ids"]
    assert HYP.hypothesis_id not in {e["evidence_id"] for e in ev["evidence"]}
    assert [t["origin"] for t in rec["query"]["terms"]] == ["source_copy", "original_requirement",
                                                            "original_requirement", "original_requirement",
                                                            "generated_hypothesis"]
    # the coverage re-check may not cite it
    def cites_hypothesis(after):
        return [dataclasses.replace(s, evidence_ids=(HYP.hypothesis_id,)) if s.relation_key == "r1:binding:D1" else s
                for s in states_before()]
    with pytest.raises(T.HypothesisNotEvidence):
        step(assess=cites_hypothesis)
    # nor can a relation's "copied" reference point at it, nor can the registry resolve it, nor can ids collide
    reg = registry()
    reg.register_hypothesis(HYP)
    with pytest.raises(T.HypothesisNotEvidence):
        reg.resolve([HYP.hypothesis_id])
    bad = [dataclasses.replace(states_before()[0], reference_text="shutoff", reference_evidence_id=HYP.hypothesis_id)]
    with pytest.raises(T.HypothesisNotEvidence):
        step(relations=bad, reg=reg)
    with pytest.raises(T.HypothesisNotEvidence):
        reg.add_evidence(T.SourceEvidence(HYP.hypothesis_id, "SYN-D1#body", 0, 1, "S"))
    with pytest.raises(T.HypothesisNotEvidence):
        T.require_source_evidence(HYP)
    # and the trace checks catch it if someone edits the event afterwards
    tampered = copy.deepcopy(ev)
    tampered["runtime_assessments"][-1]["evidence_ids"].append(HYP.hypothesis_id)
    assert any("generated hypothesis" in m for m in T.semantic_errors(tampered))


# --------------------------------------------------------------------------- schema validity
def test_pure_form_emits_a_schema_valid_trace_and_tampering_is_caught():
    ev = step()["trace_event"]
    assert T.schema_errors(ev) == [] and T.semantic_errors(ev) == []
    assert ev["mode"] == "synthetic_demo" and ev["action"]["kind"] == "structural_expansion"
    assert ev["cost"]["state"] == "not_applicable" and ev["event_time"] == EVENT_TIME
    assert all(a["basis"] == "runtime_not_gold" for a in ev["runtime_assessments"])
    assert ev["action"]["selected_assessment_id"] == ev["runtime_assessments"][0]["assessment_id"]
    bad = copy.deepcopy(ev)
    bad["candidate_delta"]["new_ids"] = bad["candidate_delta"]["returned_ids"]
    assert T.semantic_errors(bad)
    bad = copy.deepcopy(ev)
    bad["evidence"][0]["quote"] += "!"
    assert T.semantic_errors(bad)
    # an emitter that misreports the action is refused by the operator
    good = R.trace_emitter(context(), registry())

    def lying(record, query, hyps):
        e = good(record, query, hyps)
        e["action"]["query_text"] = '"something else"'
        return e
    with pytest.raises(ValidationFailed) as err:
        step(emit=lying)
    assert err.value.code == "trace_mismatch"


# =========================================================================== Workbench adapter (P0-T06 packet)
@pytest.fixture
def wb(tmp_path):
    sl = R.RelationSearchSlice(EvidenceCore(tmp_path / "store"))
    sl.setup()
    return sl


def _count_searches(monkeypatch, sl) -> list:
    calls: list = []
    real = sl.search

    def counted(match, limit=T.RESULT_LIMIT):
        calls.append(match)
        return real(match, limit)
    monkeypatch.setattr(sl, "search", counted)
    return calls


def test_workbench_operator_reproduces_the_p0_t06_action_and_records_it(wb, tmp_path, monkeypatch):
    calls = _count_searches(monkeypatch, wb)
    res = wb.run_relation_search()
    rec = res["record"]
    ref = T.TraceSlice(EvidenceCore(tmp_path / "p0t06"))
    ref.setup()
    p0 = ref.run()
    assert len(calls) == 2                                              # seed + exactly one relation search
    assert res["seed_event"]["candidate_delta"]["returned_ids"] == p0["seed_event"]["candidate_delta"]["returned_ids"]
    x, y = res["expansion_event"], p0["expansion_event"]
    assert x["action"]["query_text"] == y["action"]["query_text"] == rec["query"]["submitted_text"]
    for k in ("before_ids", "returned_ids", "after_ids", "new_ids"):
        assert x["candidate_delta"][k] == y["candidate_delta"][k] == rec["candidate_delta"][k]
    assert res["assessment"]["status"] == p0["assessment"]["status"] == "supported"
    assert rec["selection"]["selected_relation_key"] == "annex-reference:ev:syn-letter@v1#clause-5[274:281]"
    for e in (res["seed_event"], x):
        assert T.schema_errors(e) == [] and T.semantic_errors(e) == []
        assert e["action"]["eligibility_profile_id"] == R.workbench_mask().trace_id
    run = wb.core.run_view(x["run_id"])
    assert run["status"] == "completed" and run["kind"] == "relation_search"
    assert [a["action_type"] for a in run["actions"]] == ["trace_search", "trace_search", "trace_rerank"]
    assert run["actions"][1]["detail"]["policy"] == R.POLICY_V1.name
    with sqlite3.connect(wb.store.path) as con:
        kinds = [r[0] for r in con.execute("SELECT action_kind FROM trace_events WHERE project_id=? ORDER BY "
                                           "action_seq", (R.PROJECT_ID,))]
    assert kinds == ["seed_search", "structural_expansion"]


def test_workbench_rerank_is_against_the_original_requirement_only(wb):
    rec = wb.run_relation_search()["record"]
    ranking = rec["rerank"]["ranking"]
    seed = rec["candidate_delta"]["before_ids"]
    assert [r["candidate_id"] for r in ranking[:2]] == seed and all(r["score"] is not None for r in ranking[:2])
    assert all(r["is_new"] and r["score"] is None for r in ranking[2:])  # expansion-only matches gain nothing
    assert rec["rerank"]["request"]["requirement_texts"] == [wb.requirement()["text"]]
    run = wb.core.run_view(wb.run_id)
    match = run["actions"][2]["detail"]["fts_match"]
    assert match == run["actions"][0]["detail"]["fts_match"]           # the seed (original requirement) expression
    assert "coastal" not in match and "annex" not in match


def test_workbench_eligibility_mask_applies_to_both_routes(wb):
    rec = wb.run_relation_search(R.workbench_mask("syn-exclude-annex-a", exclude_sources={"syn-annex-a"}))["record"]
    assert rec["search"]["excluded_ineligible"] == [{"candidate_id": "syn-annex-a@v1#annex-a-1",
                                                     "reason": "excluded_group:syn-annex-a"}]
    assert rec["candidate_delta"]["new_ids"] == ["syn-annex-b@v1#annex-heading", "syn-annex-b@v1#annex-b-1"]
    assert rec["coverage"]["selected_after"] == "supported"


def test_workbench_date_mask_keeps_a_late_annex_out_and_the_relation_unresolved(tmp_path):
    sl = R.RelationSearchSlice(EvidenceCore(tmp_path / "s"))
    sl.setup()
    m = R.workbench_mask("syn-date-cutoff", source_dates={"syn-letter": "2026-01-10", "syn-annex-a": "2026-01-10",
                                                          "syn-annex-b": "2026-12-01"}, date_cutoff="2026-11-01")
    res = sl.run_relation_search(m)
    rec = res["record"]
    assert {x["reason"] for x in rec["search"]["excluded_ineligible"]} == {"date_not_before_cutoff"}
    assert not [x for x in rec["candidate_delta"]["after_ids"] if x.startswith("syn-annex-b")]
    assert rec["coverage"]["selected_after"] == "unresolved" and res["assessment"]["status"] == "unresolved"
    # a missing date under the default 'exclude' rule removes the seed letter too: nothing to search for
    sl2 = R.RelationSearchSlice(EvidenceCore(tmp_path / "s2"))
    sl2.setup()
    res2 = sl2.run_relation_search(R.workbench_mask("syn-no-dates", date_cutoff="2026-11-01"))
    assert res2["seed_nodes"] == [] and res2["record"]["outcome"] == "no_unresolved_relation"
    assert res2["seed_event"] is None and res2["expansion_event"] is None
    detail = sl2.core.run_view(sl2.run_id)["actions"][0]["detail"]
    assert {x["reason"] for x in detail["excluded_ineligible"]} == {"missing_date"} and detail["new_ids"] == []


def test_workbench_budget_of_one_runs_the_seed_only(wb, monkeypatch):
    calls = _count_searches(monkeypatch, wb)
    budget = R.ActionBudget(1)
    res = wb.run_relation_search(budget=budget)
    assert len(calls) == 1 and res["record"]["outcome"] == "budget_exhausted" and res["expansion_event"] is None
    assert budget.spent == ["seed_search"]
    assert wb.core.run_view(wb.run_id)["counters"]["search_actions"] == 1


def test_workbench_hypothesis_is_typed_and_never_cited(wb):
    res = wb.run_relation_search()
    ev = res["expansion_event"]
    (hyp,) = ev["hypotheses"]
    assert hyp["text"] == "coastal" and hyp["hypothesis_id"] in ev["action"]["query_artifact_ids"]
    assert hyp["hypothesis_id"] not in {e["evidence_id"] for e in ev["evidence"]}
    with pytest.raises(T.HypothesisNotEvidence):
        R._StoreEvidence(wb).resolve([hyp["hypothesis_id"]])


def test_p0_t06_events_keep_their_original_profile_and_limit(tmp_path):
    sl = T.TraceSlice(EvidenceCore(tmp_path / "s"))
    sl.setup()
    res = sl.run()
    for e in (res["seed_event"], res["expansion_event"]):
        assert e["action"]["eligibility_profile_id"] == T.ELIGIBILITY_ID
        assert e["action"]["result_limit"] == T.RESULT_LIMIT
