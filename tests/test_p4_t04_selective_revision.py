"""P4-T04: selective revision against full recomputation (authored synthetic fixtures; no network, model or paid call).

The harness is ``scripts/verify_selective_revision.py``; these tests run a subset of its scenarios (the full set is in
the receipt) and pin the two engine changes of this task. Engineering checks only: no retrieval effectiveness claim."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from patent_to_pilot.workbench import core as C

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
    # every executed seed search is in the run counters (no hidden verification search)
    assert sel["seed_searches"] == sel["run_counter_acquisition_actions"]
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


@pytest.mark.xfail(strict=True, reason="known defect (P4-T04 receipt D2): a no-hit requirement anchors its action on a "
                                       "sibling's citation from the store's history, so the result depends on the order "
                                       "in which results were committed, not only on the corpus")
def test_sibling_anchored_action_is_independent_of_history(tmp_path):
    rep = run(tmp_path, "d1-sibling-anchor-order")
    assert rep["verdict"] == "MATCH"


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
