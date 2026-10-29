import importlib.util
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts/healthtech/run_dapfam_bm25.py"
SPEC = importlib.util.spec_from_file_location("dapfam_bm25", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_tokenize_is_lowercase_and_stable():
    assert MODULE.tokenize("Valve-XL / 10mm") == ["valve", "xl", "10mm"]


def test_sparse_bm25_matches_reference_scores():
    from rank_bm25 import BM25Okapi

    corpus = [
        MODULE.tokenize("cardiac valve implant"),
        MODULE.tokenize("portable battery case"),
        MODULE.tokenize("catheter valve delivery"),
    ]
    query = MODULE.tokenize("valve catheter")
    reference = BM25Okapi(corpus, k1=1.5, b=0.75, epsilon=0.25).get_scores(query)
    actual = MODULE.SparseBM25(corpus, k1=1.5, b=0.75, epsilon=0.25).get_scores(query)

    np.testing.assert_allclose(actual, reference, rtol=1e-12, atol=1e-12)


def test_ndcg_and_recall_ignore_unjudged_ids():
    ranked = {"q1": ["unjudged", "p2", "p1"]}
    qrels = {"q1": {"p1": 1.0, "p2": 0.0}}
    result = MODULE.evaluate(ranked, qrels, k=3)

    assert result["query_count"] == 1
    assert result["positive_qrels"] == 1
    assert result["hits_at_k"] == 1
    assert result["macro_recall_at_k"] == 1.0
    assert 0.0 < result["macro_ndcg_at_k"] < 1.0


def test_duplicate_qrels_are_rejected(tmp_path):
    qrels = tmp_path / "qrels.tsv"
    qrels.write_text(
        "query_id\trelevant_id\trelevance_score\tdomain_rel\n"
        "q1\tp1\t1\tIN\n"
        "q1\tp1\t1\tIN\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate qrel pair"):
        MODULE.read_qrels(qrels)


def test_display_path_supports_external_smoke_inputs(tmp_path):
    path = tmp_path / "fixture.parquet"
    assert MODULE.display_path(path) == str(path)


def test_manifest_code_provenance_binds_working_tree_source():
    provenance = MODULE.code_provenance()

    assert provenance["entrypoint"].replace("\\", "/").endswith("scripts/healthtech/run_dapfam_bm25.py")
    assert len(provenance["sha256"]) == 64
    assert provenance["git_revision"]
    assert isinstance(provenance["working_tree_dirty"], bool)
