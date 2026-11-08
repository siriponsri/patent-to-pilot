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
    return {q: {"hit20": h20, "recall20": h20, "hit100": h100, "mrr100": 0.0, "hit200": h100}
            for q, (h20, h100) in values.items()}


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


def test_dense_prefix_is_stripped_for_bm25_and_rerankers_only():
    import sys

    sys.path.insert(0, str(SCRIPTS.parents[1] / "src"))
    from patent_to_pilot.evaluation.dapfam_acquisition import DENSE_QUERY_PREFIX

    assert hybrid.DENSE_QUERY_PREFIX == DENSE_QUERY_PREFIX
    stored = DENSE_QUERY_PREFIX + "Intravenous stand"
    assert hybrid.tokenize(hybrid.strip_prefix(stored)) == ["intravenous", "stand"]
    assert rerank.query_text(stored) == "Intravenous stand"
    assert hybrid.strip_prefix("Intravenous stand") == "Intravenous stand"


fusion = _load("run_mtm_fusion")
llm = _load("run_mtm_rerank_llm")


def test_fuse_head_lambda_one_keeps_dense_order_and_zero_uses_method():
    fams = ["a", "b", "c", "d"]
    dense, method = [0.9, 0.5, 0.1], [0.0, 1.0, 2.0]
    assert fusion.fuse_head(fams, dense, method, 1.0, 3) == ["a", "b", "c", "d"]
    assert fusion.fuse_head(fams, dense, method, 0.0, 3) == ["c", "b", "a", "d"]
    assert fusion.fuse_head(fams, [1.0, 1.0, 1.0], [1.0, 1.0, 1.0], 0.5, 3) == fams


def test_joint_cv_over_prompts_uses_number_after_last_dash():
    base = _rows({"q1": (0, 0), "q2": (0, 0)})
    good = _rows({"q1": (1, 1), "q2": (1, 1)})
    assert methods.choose({"llmN-0.5": base, "llmC-0.9": good, "llmC-0.5": good}, ["q1", "q2"], "llm") == "llmC-0.9"
    assert methods._suffix("hyb-0.7", "hyb-") == 0.7


def test_llm_prompts_and_candidate_text_are_frozen():
    assert set(llm.PROMPTS) == {"N", "C"} and "different technical field" in llm.PROMPTS["C"]
    row = {"title": "Jaw  tool", "abstract": " ".join(["w"] * 250)}
    assert llm.candidate_text(row) == "Jaw tool. " + " ".join(["w"] * 200)
    msgs = llm.messages("sys", "N", "a problem", "a patent")
    assert msgs[0] == {"role": "system", "content": "sys"} and "Problem: a problem" in msgs[1]["content"]


prf = _load("run_mtm_prf")


def test_prf_query_mixes_normalised_vectors_and_keeps_q_at_weight_one():
    q = np.array([1.0, 0.0])
    fb = np.array([[0.0, 2.0], [0.0, 4.0]])
    assert np.allclose(prf.prf_query(q, fb, 1.0), q) and np.allclose(prf.prf_query(q, [], 0.7), q)
    mixed = prf.prf_query(q, fb, 0.5)
    assert np.isclose(np.linalg.norm(mixed), 1.0) and np.allclose(mixed, [2 ** -0.5, 2 ** -0.5])


def test_winning_passage_and_variant_order():
    scores = np.array([0.1, 0.9, 0.3, 0.2, 0.8])
    starts = np.array([0, 2, 5])
    assert prf.winning_passages(scores, starts, [1, 0]) == [4, 1]
    assert prf.variant_names([3, 5], [0.8, 0.9])[:3] == ["prfK0-1.0", "prfK3-0.8", "prfK5-0.8"]
    assert methods.choose({"prfK3-0.8": _rows({"q": (1, 1)}), "prfK5-0.9": _rows({"q": (1, 1)})}, ["q"], "prf") == "prfK5-0.9"


def test_new_and_lost_gold_at_200():
    base = {"q1": {"hit20": 0, "recall20": 0, "hit100": 0, "mrr100": 0, "hit200": 0},
            "q2": {"hit20": 0, "recall20": 0, "hit100": 0, "mrr100": 0, "hit200": 1}}
    rows = {"q1": {**base["q1"], "hit200": 1}, "q2": {**base["q2"], "hit200": 0}}
    out = methods.compare(rows, base)
    assert out["new_gold200"] == 0.5 and out["lost_gold200"] == 0.5
