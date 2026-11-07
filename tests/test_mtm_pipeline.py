import importlib.util
import json
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts/healthtech"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


build = _load("build_mtm_inputs")
analyze = _load("analyze_mtm")


def _row(role, fam, prio, c3, **extra):
    base = {"role": role, "split": extra.pop("split", ""), "publication_number": f"US-{fam}-B2", "family_id": fam,
            "priority_date": str(prio), "c3": json.dumps(c3), "title": " T ", "abstract": "A  b", "claims_head": "c",
            "targets": json.dumps(extra.pop("targets", [])), "in_small_corpus": extra.pop("small", "")}
    return base


def test_build_merges_sets_and_drops_uniform_duplicates():
    rows = [_row("query", "q1", 20150101, ["A61"], split="dev", targets=[{"t_family": "t1", "t_priority": 20000101}]),
            _row("target", "t1", 20000101, ["B01"], small="True"),
            _row("distractor", "d1", 20010101, ["B01"], small="True"),
            _row("distractor", "d2", 20010101, ["H01"], small="False")]
    uniform = [_row("uniform_distractor", "u1", 20180101, ["G06"]), _row("uniform_distractor", "d2", 20010101, ["H01"])]
    pubdates = {"US-t1-B2": 20030101, "US-d1-B2": 20020101, "US-d2-B2": 20020101, "US-u1-B2": 20190101}
    corpus, queries, stats = build.build(rows, uniform, pubdates)
    sets = {r["id"]: r["sets"] for r in corpus}
    assert sets == {"d1": ["matched", "small"], "d2": ["matched"], "t1": ["target"], "u1": ["uniform"]}
    assert queries[0]["targets"] == ["t1"] and corpus[0]["abstract"] == "A b"
    assert stats == {"no_publication_date": 0, "gold_pairs_dropped_not_yet_published": 0,
                     "queries_dropped_no_visible_target": 0}


def test_build_drops_targets_not_yet_published_and_undated_documents():
    rows = [_row("query", "q1", 20150101, ["A61"], split="dev", targets=[{"t_family": "t1", "t_priority": 20000101}]),
            _row("query", "q2", 20150101, ["A61"], split="test", targets=[{"t_family": "t2", "t_priority": 20000101}]),
            _row("target", "t1", 20000101, ["B01"]), _row("target", "t2", 20000101, ["B01"]),
            _row("distractor", "d1", 20010101, ["B01"])]
    corpus, queries, stats = build.build(rows, [], {"US-t1-B2": 20160101, "US-t2-B2": 20020101})
    assert [r["id"] for r in corpus] == ["t1", "t2"] and [q["id"] for q in queries] == ["US-q2-B2"]
    assert stats == {"no_publication_date": 1, "gold_pairs_dropped_not_yet_published": 1,
                     "queries_dropped_no_visible_target": 1}


def test_runner_keep_mask_applies_time_family_view_and_lane():
    spec = importlib.util.spec_from_file_location("m", SCRIPTS / "run_mtm_dense_pool.py")
    source = (SCRIPTS / "run_mtm_dense_pool.py").read_text(encoding="utf-8")
    namespace = {}
    exec(source[source.index("def keep_mask"):source.index("def main")], namespace)
    keep_mask = namespace["keep_mask"]
    priority = np.array([20000101, 20200101, 20050101, 20050101])
    view = np.array([True, True, True, False])
    assert keep_mask(priority, 20150101, None, view, [], "U").tolist() == [True, False, True, False]
    assert keep_mask(priority, 20150101, 0, view, [2], "X").tolist() == [False, False, False, False]
    assert keep_mask(priority, 20150101, None, view, [2], "U").tolist() == [True, False, True, False]


def test_analysis_metrics_mixed_and_missing_rankings():
    assert analyze.mixed(["u1", "u2", "x1"], ["x1", "x2"], k=4) == ["u1", "u2", "x1", "x2"]
    m = analyze.metrics(["a", "g", "b"], {"g", "h"})
    assert m == {"hit20": 1.0, "recall20": 0.5, "hit100": 1.0, "mrr100": 0.5}
    meta = [{"id": "q1", "priority": 20150101, "targets": ["g"]}, {"id": "q2", "priority": 20150101, "targets": ["h"]}]
    arms = {"U": {"q1": ["a"]}, "X": {"q1": ["g"], "q2": ["h"]}}
    out = analyze.evaluate(meta, arms, {"g": 20000101, "h": 20050101, "a": 20010101})
    assert out["missing_rankings"] == {"U": 1, "X": 0}
    assert out["means"]["U"]["hit20"] == 0.0 and out["means"]["X"]["hit20"] == 1.0
    assert out["hit_gap_years_median"]["X"] == 12.5
