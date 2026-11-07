import importlib.util
from pathlib import Path

import pytest

from patent_to_pilot.evaluation.scout_frozen import (
    brief_gap,
    e1_e2,
    grounding_decision,
    recall,
    two_lane_pool,
)

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts" / "healthtech"


def _script(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_pools_and_recall():
    assert two_lane_pool(["o1", "o2", "o3"], ["x1", "x2", "x3"], 4) == ["o1", "o2", "x1", "x2"]
    assert two_lane_pool(["o1"], ["x1", "x2"], 4) == ["o1", "x1", "x2"]
    assert recall(["a", "b", "c"], {"b", "z"}, 2) == 0.5


def test_e1_e2_on_a_synthetic_case():
    out_rel = {"q1": {"x1"}, "q2": {"x9"}}
    in_rel = {"q1": {"o1"}, "q2": set()}
    rankings = {}
    for view in ("P", "T", "R2"):
        rankings[f"u-{view}"] = {"q1": ["o1"] + [f"o{i}" for i in range(2, 30)] + ["x1"], "q2": ["x9"]}
        rankings[f"o-{view}"] = {"q1": ["o1"] + [f"o{i}" for i in range(2, 30)], "q2": []}
        rankings[f"x-{view}"] = {"q1": ["x1"], "q2": ["x9"]}
    result = e1_e2(rankings, out_rel, in_rel)
    k20 = result["E1"]["P"]["k20"]
    assert k20["out"]["single"] == 0.5 and k20["out"]["two_lane"] == 1.0
    assert k20["in"]["single"] == 1.0 and k20["in"]["two_lane"] == 1.0 and k20["in"]["queries"] == 1
    assert result["E2"]["protocol_effect"]["P"]["k20"]["other_fields_only"] == 1.0
    assert set(result["primary"]) == {"H1a_out_recall_at20", "H1b_in_recall_at20"}
    assert all("p_holm" in v for v in result["primary"].values())
    assert result["E2"]["brief_cost"]["P_minus_R2_at200"]["out_full_candidates"]["delta"] == 0


def test_grounding_decision_rules():
    rows = [{"key": f"k{i}", "cluster": f"c{i % 10}", "v0_g1": i % 2, "v1_g1": 1, "v0_g2": 1, "v1_g2": 1} for i in range(60)]
    assert grounding_decision(rows)["decision"] == "ADOPT_V1"
    worse = [{**r, "v1_g2": 0 if i % 3 == 0 else 1} for i, r in enumerate(rows)]
    assert grounding_decision(worse)["decision"] == "KEEP_V0"


def test_brief_gap():
    result = brief_gap({"q": ["a", "b"]}, {"q": ["b", "c"]}, {"q": {"a"}, "r": set()})
    assert result["k20"]["full"] == 1.0 and result["k20"]["title"] == 0.0 and result["k20"]["queries"] == 1


def test_quote_by_reference_units_and_parser():
    r = _script("run_qwen_scout_rationales")
    from patent_to_pilot.healthtech.scout import check_quote

    text = ("Short title\n\nThe overcoat imparts a superhydrophobic surface to a painted object. It resists abrasion well "
            "in tests.\n\n1. A coating comprising particles. 2. The coating of claim 1, wherein " + " ".join(["w"] * 90) + ".")
    units = r.split_sentences(text)
    assert all(5 <= len(u.split()) <= 60 for u in units)
    assert all(check_quote(u, text).status == "matched" for u in units)
    parsed, error = r.parse_rationale_v1('{"what_it_does":"a","transferable_mechanism":"b","evidence":[1, 99]}', len(units))
    assert error is None and parsed["invalid_references"] == 1
    assert r.render_quotes([1, 99], units)[1] == "[invalid reference S99]"
    assert r.parse_rationale_v1('{"what_it_does":"a","transferable_mechanism":"b","evidence":["1"]}', 3)[1]
    assert r.parse_rationale_v1('{"what_it_does":"a","transferable_mechanism":"b","evidence":[1,2,3,4]}', 5)[1]


def test_test_inputs_views_and_patenteb_split():
    b = _script("build_scout_test_inputs")
    files = b.views([{"id": "q1", "title": "Seal", "own_ipc3": ["F16"]}, {"id": "q2", "title": "Gasket", "own_ipc3": []}],
                    {"q1": {"P": {"parsed": None}}, "q2": {"P": {"parsed": "A brief."}}},
                    {"q1": "encode query for different document retrieval: full"})
    assert [r["id"] for r in files["u-T"]] == ["q1", "q2"]
    assert "u-P" in files and [r["id"] for r in files["u-P"]] == ["q2"]  # a failed P brief writes no row
    assert files["o-T"][0]["allowed_ipc3"] == ["F16"] and files["x-T"][0]["excluded_ipc3"] == ["F16"]
    assert [r["id"] for r in files.get("x-P", [])] == []  # q2 has no own classes, so no lane rows
    assert files["u-R2"][0]["text"].endswith("full")
    p = _script("analyze_patenteb_brief_gap")
    assert p.split_text("edible oil [SEP] provide  an oil") == ("edible oil", "provide an oil")
    assert p.split_text("no separator") == ("no separator", "")


def test_frozen_analysis_refuses_to_overwrite(tmp_path):
    out = tmp_path / "done.json"
    out.write_text("{}", encoding="utf-8")
    import subprocess
    import sys

    proc = subprocess.run([sys.executable, str(SCRIPTS / "analyze_scout_frozen_test.py"), "--rankings-dir", str(tmp_path),
                           "--split", str(tmp_path / "missing.json"), "--output", str(out)], capture_output=True, text=True)
    assert proc.returncode != 0 and "runs once" in proc.stderr
