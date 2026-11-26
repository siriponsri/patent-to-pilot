from fractions import Fraction
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/research/ra_pharma"))
from ocs_correspondence import Document, run_query
from ocs_extract_pair import Window, compare, select_pair
from ocs_extract_pair_score import evaluate


def test_conditioned_pair_can_choose_a_complementary_qualified_span():
    anchor = frozenset({"abc", "bcd"})
    conclusion = Window(1, 0, 360, anchor, True, False)
    overlapping = Window(1, 200, 560, anchor, True, True)
    lexical_duplicate = Window(2, 0, 360, anchor, False, False)
    qualification = Window(3, 0, 360, anchor, False, True)
    windows = [qualification, lexical_duplicate, overlapping, conclusion]
    control, control_count = select_pair(anchor, windows, Fraction(0))
    candidate, candidate_count = select_pair(anchor, windows, Fraction(1, 5))
    assert control == (conclusion, lexical_duplicate)
    assert candidate == (conclusion, qualification)
    assert candidate_count == control_count == 9


def test_shared_trace_can_be_scored_with_named_arms_and_unchanged_opens():
    query = {"id": "q", "agency": "กรมทดสอบ", "reference": "ทด.12/44", "question": "ส่งคืนกระถางได้หรือไม่"}
    pages = ["เรื่องเสร็จที่ 9/2560 กรมทดสอบมีหนังสือที่ ทด.12/44 ถามว่าส่งคืนกระถางได้หรือไม่",
             "คณะกรรมการกฤษฎีกาได้พิจารณาแล้วเห็นว่า เจ้าหน้าที่ส่งคืนกระถางได้เมื่อทำทะเบียนครบถ้วน"]
    doc = Document.index("p", pages)
    fixed = run_query(query, [doc], "exact_conflict")
    rows = compare(query, {"p": doc}, fixed)
    assert all(arm["actions"] == fixed["actions"] and arm["identity"] == fixed["identity"] for arm in rows.values())
    keys = [{"id": "q", "adjudication": "adjudicated", "request_provenance": "recited_in_opinion",
             "agency": query["agency"], "reference": query["reference"], "opinion": "9/2560",
             "source_case": "p", "requirements": [{"page": 2, "quote": "ส่งคืนกระถางได้เมื่อทำทะเบียนครบถ้วน"}]}]
    summary = evaluate({"traces": {"q": rows}}, keys, {"p": pages})
    assert summary["paired"]["both_complete"] == 1
    assert summary["primary_delta_complete"] == 0
    assert all(metrics["complete"] == 1 for metrics in summary["totals"].values())


def test_common_window_overcap_preserves_actions_and_abstains_in_all_arms():
    query = {"id": "q", "agency": "กรมทดสอบ", "reference": "ทด.12/44", "question": "ส่งคืนกระถางได้หรือไม่"}
    raw = ["เรื่องเสร็จที่ 9/2560 กรมทดสอบมีหนังสือที่ ทด.12/44 ถามว่าส่งคืนกระถางได้หรือไม่",
           "คณะกรรมการกฤษฎีกาได้พิจารณาแล้วเห็นว่า ส่งคืนกระถางได้" * 420]
    doc = Document.index("p", raw)
    fixed = run_query(query, [doc], "exact_conflict")
    rows = compare(query, {"p": doc}, fixed)
    assert all(arm["actions"] == fixed["actions"] and arm["window_cap_stop"] and
               not arm["spans"] and arm["status"] == "unresolved-window-cap" for arm in rows.values())


def test_unknown_stays_out_of_the_four_paired_correctness_cells():
    pages = {"p": ["valid-passage-long-enough"]}
    action = {"source": "p", "page": 1, "reason": "issuer-response"}
    identity = {"source": "p"}
    unresolved = {"actions": [action], "identity": identity, "status": "unresolved-response",
                  "spans": [], "windows_ranked": 1, "options_evaluated": 0, "window_cap_stop": False}
    issued = {**unresolved, "status": "issued",
              "spans": [{"page": 1, "start": 0, "end": len(pages["p"][0]), "quote": pages["p"][0]}]}
    original = {"traces": {"q": {"d31_fixed": unresolved, "lexical_diversity": unresolved,
                                 "issue_conditioned": issued}}}
    keys = [{"id": "q", "adjudication": "unknown", "request_provenance": "recited_in_opinion"}]
    summary = evaluate(original, keys, pages)
    assert summary["known"] == 0
    assert summary["total_issues"] == 1
    assert summary["paired"] == {
        "both_complete": 0, "candidate_only": 0, "control_only": 0, "neither_complete": 0,
        "unknown": 1, "different_spans_all": 1, "different_spans_known": 0,
    }
    assert summary["totals"]["issue_conditioned"]["issued"] == 1
    assert summary["totals"]["issue_conditioned"]["unsupported_issued"] == 0
