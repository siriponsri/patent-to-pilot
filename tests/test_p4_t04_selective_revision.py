"""P4-T04: selective revision against full recomputation (authored synthetic fixtures; no network, model or paid call).

The harness is ``scripts/verify_selective_revision.py``; these tests run a subset of its scenarios (the full set is in
the receipt) and pin the two engine changes of this task. Engineering checks only: no retrieval effectiveness claim."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from patent_to_pilot.workbench import core as C
from patent_to_pilot.workbench import relation_search as R

_PATH = Path(__file__).resolve().parents[1] / "scripts" / "verify_selective_revision.py"
_SPEC = importlib.util.spec_from_file_location("verify_selective_revision", _PATH)
H = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(H)


def scenario(sid: str) -> dict:
    return next(s for s in H.SCENARIOS if s["id"] == sid)


def run(tmp_path, sid: str, **kw) -> dict:
    return H.run_scenario(scenario(sid), tmp_path / sid, **kw)


def zero_model_work(rep: dict) -> None:
    for path in ("selective_work", "full_in_place_work", "full_scratch_work"):
        w = rep[path]
        assert w["paid_model_calls"] == w["remote_calls"] == w["provider_client_requests"] == 0, path
        assert w["provider_usage_rows"] == 0, path


# --------------------------------------------------------------------------- the three kinds of change
def test_source_text_change_matches_a_full_rerun_and_reassesses_less(tmp_path):
    rep = run(tmp_path, "a1-text-cited-annex")
    assert rep["verdict"] == "MATCH" and rep["mismatch_selective_vs_scratch"] == {}
    assert rep["truth_changed_cells"] == ["C1/T1"] and rep["missed"] == []
    assert rep["cells_after"]["C1/T1"]["outcome"] == "does_not_meet"          # 20 to 45 C no longer covers 10-50
    assert "C1/T1" in rep["selective_reacquired"] and rep["selective_revalidated"] == ["C1/P1"]
    assert rep["selective_untouched"] == ["C2/P1", "C2/S1", "C2/T1"]          # the other candidate is not touched
    sel, full = rep["selective_work"], rep["full_in_place_work"]
    assert sel["obligations_reassessed"] < full["obligations_reassessed"] == 6
    assert sel["passages_indexed"] == full["passages_indexed"] < rep["full_scratch_work"]["passages_indexed"]
    # every executed seed search is in the run counters (no hidden verification search; policy 2.1.0 sibling seed
    # searches have their own counter)
    for path in ("selective_work", "full_in_place_work", "full_scratch_work"):
        w = rep[path]
        assert w["seed_searches"] == w["run_counter_acquisition_actions"] + w["run_counter_sibling_seed_searches"], path
    # D25: C2/S1 (no hit) no longer records a history-dependent anchor list, so a full rerun in place equals scratch
    assert rep["full_in_place_vs_scratch"] == "MATCH" and rep["acquisition_policy"] == R.POLICY_V2_1.name
    zero_model_work(rep)


def test_scope_edge_resolved_by_an_unrelated_member_is_reacquired(tmp_path):
    rep = run(tmp_path, "b4-edge-resolved-by-unrelated-member")
    assert rep["verdict"] == "MATCH" and rep["missed"] == []
    assert rep["truth_changed_cells"] == ["C1/S1"] and "C1/S1" in rep["selective_reacquired"]
    zero_model_work(rep)


def test_corpus_member_added_that_resolves_an_edge_matches_a_full_rerun(tmp_path):
    rep = run(tmp_path, "c1-member-added-resolves-edge")
    assert rep["verdict"] == "MATCH" and rep["missed"] == []
    s1 = rep["cells_after"]["C1/S1"]
    assert s1["action"] == "resolve_reference" and s1["citation"].startswith("spec#")


def test_harness_detects_the_original_reuse_defect_when_the_fix_is_disabled(tmp_path):
    rep = run(tmp_path, "c1-member-added-resolves-edge", disable_scope_fix=True)
    assert rep["verdict"] == "MISMATCH_SELECTIVE" and rep["missed"] == ["C1/S1"]
    d = rep["mismatch_selective_vs_scratch"]["C1/S1"]
    assert d["acquisition"]["left"]["outcome"] == "no_actionable_gap"         # reused: the old 'no target' state
    assert d["acquisition"]["right"]["action"] == "resolve_reference"         # full rerun: the edge now resolves
    assert set(d) == {"acquisition", "explanation", "search_hits"}            # outcome and citation are equal


def test_member_added_to_another_candidate_leaves_this_candidate_untouched(tmp_path):
    rep = run(tmp_path, "c3-member-added-other-candidate")
    assert rep["verdict"] == "MATCH" and rep["full_in_place_vs_scratch"] == "MATCH"
    assert rep["selective_untouched"] == ["C1/P1", "C1/S1", "C1/T1"]


def test_corpus_member_removal_is_reported_as_unsupported(tmp_path):
    rep = run(tmp_path, "c4-member-removed")
    assert rep["verdict"] == "NOT_SUPPORTED" and "no corpus-removal operation" in rep["reason"]


# --------------------------------------------------------------------------- D2 fixed by policy 2.1.0 (owner decision D25)
def test_sibling_anchored_action_is_independent_of_history(tmp_path):
    """Formerly the strict xfail of defect D2: selective, full-in-place and from-scratch runs now agree on d1."""
    rep = run(tmp_path, "d1-sibling-anchor-order")
    assert rep["acquisition_policy"] == "ptp-structural-acquisition/2.1.0"
    assert rep["verdict"] == "MATCH" and rep["full_in_place_vs_scratch"] == "MATCH"
    assert rep["mismatch_selective_vs_in_place"] == {} and rep["missed"] == []
    a1 = rep["cells_after"]["C1/A1"]
    assert a1["action"] == "search_within_source" and a1["citation"].startswith("profile#p0004")
    zero_model_work(rep)


def test_policy_2_0_0_still_reproduces_defect_d2(tmp_path):
    """The old rule is kept selectable for reproduction; the harness still shows the D2 history dependence under it."""
    rep = run(tmp_path, "d1-sibling-anchor-order", policy=R.POLICY_V2.name)
    assert rep["acquisition_policy"] == R.POLICY_V2.name
    assert rep["verdict"] == "MISMATCH_HISTORY" and rep["full_in_place_vs_scratch"] == "MISMATCH_HISTORY"
    d = rep["mismatch_selective_vs_scratch"]["C1/A1"]
    assert d["citation"]["left"]["source_id"] == "profile" and d["citation"]["right"]["source_id"] == "pricing"


ORDER_PERMUTED = [{**H.ORDER_REQUIREMENTS[0], "requirement_id": "Z1"}, H.ORDER_REQUIREMENTS[1]][::-1]


def _order_store(tmp_path, name: str, reqs: list, policy: str | None):
    with H.structural_policy(policy):
        core, _m = H._new_core(tmp_path / name)
        pid = core.create_project("P4-T04 order check", H.CANDIDATES, reqs)["project_id"]
        for sid, cand, fn, text in H.ORDER_BASE:
            H._ingest(core, pid, sid, cand, fn, text)
        first = core.run_comparison(pid)
    return core, pid, first


def _cell(sig: dict, key: str) -> dict:
    return {f: v for f, v in sig[key].items() if f != H.PROVENANCE}


@pytest.mark.parametrize("policy, independent", [(None, True), (R.POLICY_V2.name, False)])
def test_permuting_requirement_ids_does_not_change_the_evidence(tmp_path, policy, independent):
    """The no-hit requirement sorts BEFORE its sibling (A1 < E1) in one project and AFTER it (Z1 > E1, listed first)
    in the other: same corpus, same requirement texts. Under 2.1.0 the evidence signatures are identical."""
    core_a, pid_a, run_a = _order_store(tmp_path, "a1-first", H.ORDER_REQUIREMENTS, policy)
    core_z, pid_z, run_z = _order_store(tmp_path, "z1-last", ORDER_PERMUTED, policy)
    sa, sz = H.signatures(core_a, pid_a), H.signatures(core_z, pid_z)
    assert _cell(sa, "C1/E1") == _cell(sz, "C1/E1")
    assert (_cell(sa, "C1/A1") == _cell(sz, "C1/Z1")) is independent
    if independent:
        anchors = sa["C1/A1"]["acquisition"]["anchors"]
        assert [a["kind"] for a in anchors] == ["sibling_seed_unit"] and anchors[0]["source_id"] == "profile"
        # E1's seed is searched for the anchor when A1 comes first, and reused from the run when it comes later
        assert run_a["counters"]["sibling_seed_searches"] == 1
        assert run_z["counters"].get("sibling_seed_searches", 0) == 0


@pytest.mark.parametrize("policy, independent", [(None, True), (R.POLICY_V2.name, False)])
def test_a_second_full_run_without_any_change_reproduces_the_first(tmp_path, policy, independent):
    core, pid, _first = _order_store(tmp_path, "rerun", H.ORDER_REQUIREMENTS, policy)
    before = H.signatures(core, pid)
    with H.structural_policy(policy):
        core.run_comparison(pid)
    after = H.signatures(core, pid)
    assert (H.diff(before, after) == {}) is independent


def test_sibling_seed_anchor_never_reads_stored_results(tmp_path, monkeypatch):
    """2.1.0 S1a reads only this run's seed hits: with every stored citation hidden from the anchor step, the receipt is
    unchanged."""
    core, pid, _first = _order_store(tmp_path, "hidden", H.ORDER_REQUIREMENTS, None)
    before = H.signatures(core, pid)
    real = core.acquisition._sibling_seed_anchor
    seen = []

    def spy(con, project_id, eligible, seeds):
        seen.append([(rid, sorted({h["source_id"] for h in hits})) for rid, hits in seeds])
        return real(con, project_id, eligible, seeds)
    monkeypatch.setattr(core.acquisition, "_sibling_seed_anchor", spy)
    with core.store.tx() as con:   # the 2.0.0 anchor input: drop every stored citation (the rerun writes new ones)
        con.execute("DELETE FROM citations")
    core.run_comparison(pid)
    assert seen == [[("E1", ["profile"])]]
    after = H.signatures(core, pid)
    assert _cell(before, "C1/A1")["acquisition"] == _cell(after, "C1/A1")["acquisition"]


# --------------------------------------------------------------------------- the engine rule itself
def _receipt_store(tmp_path, receipt: dict | None) -> tuple:
    core = C.EvidenceCore(tmp_path / "store")
    if receipt is not None:
        with core.store.tx() as con:
            con.execute("INSERT INTO acquisition_receipts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        ("p", "run-1", 1, "C1", "R1", "x", 1, "structural", "pol", "sha", None, "o",
                         json.dumps(receipt), "d", "asm-1", "new_version", "t", "t"))
    return core


@pytest.mark.parametrize("receipt, expected", [
    (None, True),                                                                  # decision never recorded
    ({"gaps": [], "selection": {"candidates": []}}, False),                        # scope-independent for equal seed
    ({"gaps": ["unresolved_reference"], "selection": {"candidates": [{"state": "unresolved_no_target"}]}}, True),
    ({"gaps": [], "selection": {"candidates": [{"state": "resolved_in_pool"}]}}, True),
    ({"gaps": ["no_hit"], "selection": {"candidates": []}}, True),
])
def test_decision_depends_on_scope(tmp_path, receipt, expected):
    core = _receipt_store(tmp_path, receipt)
    with core.store.read() as con:
        assert core._decision_depends_on_scope(con, "asm-1") is expected
