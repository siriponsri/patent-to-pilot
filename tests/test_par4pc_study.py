import math

import pytest

from patent_to_pilot.evaluation.par4pc_study import (
    app_macro, bm25_margin, cascade, holm, paired_cluster_bootstrap, rank_by_scores, row_metrics, rrf,
)


def test_rank_ties_are_deterministic():
    assert rank_by_scores({"B": 1.0, "A": 1.0, "C": 2.0}) == ["C", "A", "B"]


def test_rrf_hand_computed():
    # A: 1/61 + 1/62 ; B: 1/62 + 1/61 ; C: 1/63 + 1/63 -> A,B tie broken by letter
    assert rrf([["A", "B", "C"], ["B", "A", "C"]]) == ["A", "B", "C"]
    # A and C: 1/61 + 1/63 = 0.032266 > B: 2/62 = 0.032258
    assert rrf([["A", "B", "C"], ["C", "B", "A"]]) == ["A", "C", "B"]


def test_margin_and_cascade():
    assert bm25_margin({"A": 10.0, "B": 5.0}) == 0.5
    assert bm25_margin({"A": 0.0, "B": 0.0}) == 0.0
    assert cascade(["A", "B"], ["B", "A"], 0.5, 0.4) == (["A", "B"], False)
    assert cascade(["A", "B"], ["B", "A"], 0.3, 0.4) == (["B", "A"], True)


def test_row_metrics_hand_computed():
    m = row_metrics(["X", "G", "S", "Y"], gold={"G"}, silver={"S"})
    assert m["rr"] == 0.5 and m["hit1"] == 0.0 and m["recall3"] == 1.0
    dcg = 3 / math.log2(3) + 1 / math.log2(4)
    idcg = 3 / math.log2(2) + 1 / math.log2(3)
    assert m["ndcg8"] == pytest.approx(dcg / idcg)
    assert row_metrics(["A"], gold={"B"})["rr"] == 0.0
    with pytest.raises(ValueError):
        row_metrics(["A"], gold=set())


def test_app_macro_weights_applications_equally():
    groups = {"r1": "a1", "r2": "a1", "r3": "a2"}
    assert app_macro({"r1": 1.0, "r2": 0.0, "r3": 1.0}, groups) == 0.75


def test_bootstrap_identical_methods_is_zero_and_constant_gain_is_exact():
    groups = {f"r{i}": f"a{i % 5}" for i in range(20)}
    a = {k: 0.5 for k in groups}
    r = paired_cluster_bootstrap(a, a, groups, resamples=200)
    assert r["delta"] == 0 and r["ci95_low"] == 0 and r["ci95_high"] == 0 and r["groups"] == 5
    b = {k: 0.25 for k in groups}
    r = paired_cluster_bootstrap(a, b, groups, resamples=200)
    assert r["ci95_low"] == pytest.approx(0.25) and r["p_bootstrap"] == 0.0


def test_holm():
    adj = holm({"c1": 0.01, "c2": 0.04, "c3": 0.03})
    assert adj == {"c1": 0.03, "c3": 0.06, "c2": 0.06}
