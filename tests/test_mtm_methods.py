import importlib.util
import math
from pathlib import Path

import numpy as np

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts/healthtech"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


hybrid = _load("run_mtm_hybrid")
rerank = _load("run_mtm_rerank_ce")
methods = _load("analyze_mtm_methods")


def test_tokenize_drops_stopwords_short_tokens_and_case():
    assert hybrid.tokenize("The Ear-Tag applicator, a 2nd X jaw of 10 mm") == ["ear", "tag", "applicator", "2nd", "jaw", "10", "mm"]


def test_bm25_weights_match_hand_computation():
    vocab, w = hybrid.build_bm25(iter([["jaw", "jaw", "pin"], ["pin"]]), k1=0.9, b=0.4)
    avgdl, n = 2.0, 2
    idf_jaw = math.log1p((n - 1 + 0.5) / (1 + 0.5))
    expected = idf_jaw * 2 * 1.9 / (2 + 0.9 * (1 - 0.4 + 0.4 * 3 / avgdl))
    assert w.shape == (2, 2)
    assert math.isclose(w[0, vocab["jaw"]], expected, rel_tol=1e-5)
    q = hybrid.query_matrix([["pin", "pin", "unknown"]], vocab)
    assert vocab == {"jaw": 0, "pin": 1} and q.toarray().tolist() == [[0.0, 1.0]]


def test_topk_is_deterministic_on_ties_and_skips_minus_inf():
    scores = np.array([1.0, 2.0, 2.0, -np.inf, 2.0, 0.5])
    id_rank = np.array([5, 4, 0, 3, 2, 1])
    assert hybrid.topk(scores, 3, id_rank).tolist() == [2, 4, 1]
    assert hybrid.topk(scores, 10, id_rank).tolist() == [2, 4, 1, 0, 5]
    assert hybrid.topk(np.full(3, -np.inf), 2, id_rank[:3]).tolist() == []


def test_hybrid_lambda_one_reproduces_dense_order():
    rng = np.random.default_rng(0)
    dense, bm25 = rng.normal(size=50), rng.normal(size=50)
    dense[[3, 7]] = -np.inf
    bm25[[3, 7]] = -np.inf
    id_rank = np.arange(50)
    out = hybrid.hybrid_order(dense, bm25, [0.0, 1.0], id_rank, union_depth=20, depth=10)
    assert out[1.0].tolist() == hybrid.topk(dense, 10, id_rank).tolist()
    assert out[0.0].tolist() == hybrid.topk(bm25, 10, id_rank).tolist()
    assert 3 not in out[0.0] and 7 not in out[1.0]


def test_rerank_reorders_only_the_head_and_keeps_ties_stable():
    fams = ["a", "b", "c", "d", "e"]
    assert rerank.rerank(fams, {"a": 0.1, "b": 0.9, "c": 0.9}, 3) == ["b", "c", "a", "d", "e"]
    assert rerank.candidate_text({"title": " Jaw  tool ", "abstract": "A\npin."}) == "Jaw tool. A pin."


def _rows(values):
    return {q: {"hit20": h20, "recall20": h20, "hit100": h100, "mrr100": 0.0} for q, (h20, h100) in values.items()}


def test_new_and_lost_gold_and_cv_choice():
    base = _rows({"q1": (0, 0), "q2": (1, 1), "q3": (0, 1), "q4": (0, 0)})
    method = _rows({"q1": (1, 1), "q2": (1, 1), "q3": (0, 0), "q4": (0, 0)})
    out = methods.compare(method, base)
    assert out["new_gold100"] == 0.25 and out["lost_gold100"] == 0.25
    assert out["means"]["hit20"] == 0.5
    tie = {"hyb-0.5": method, "hyb-0.9": method}
    assert methods.choose(tie, list(base), "hyb-") == "hyb-0.9"
    cv = methods.cross_validate(tie, base, "hyb-")
    assert set(cv["chosen_per_fold"].values()) == {"hyb-0.9"} and sum(cv["fold_sizes"].values()) == 4
    assert methods.fold_of("US-7641158-B2") == methods.fold_of("US-7641158-B2") in range(4)
