"""Synthetic checks for the P2-T04 backend and the frozen BM25-full CLI."""
import csv
import hashlib
import json
import math
from types import SimpleNamespace

import pytest

from patent_to_pilot.workbench.relation_search import ExpansionQuery, QueryTerm, RerankRequest
from scripts.healthtech.bm25_bridgeret import TOPK, main as frozen_bm25
from scripts.research.p2t04_bm25_backend import (
    BM25FullEligibility,
    BM25FullIndex,
    _bm25_weights,
    _rank_positions,
)


def test_bm25_weighting_matches_hand_calculation():
    np = pytest.importorskip("numpy")
    sparse = pytest.importorskip("scipy.sparse")
    counts = sparse.csr_matrix(np.array([[2, 0, 1], [1, 0, 0], [0, 1, 0]], dtype=np.float32))
    weights = _bm25_weights(counts)
    n, avg_len = 3, 5 / 3
    first_idf = math.log1p((n - 2 + 0.5) / (2 + 0.5))
    other_idf = math.log1p((n - 1 + 0.5) / (1 + 0.5))
    long_norm = 1.5 * (1 - 0.75 + 0.75 * 3 / avg_len)
    short_norm = 1.5 * (1 - 0.75 + 0.75 / avg_len)
    expected = [
        [2 * 2.5 * first_idf / (2 + long_norm), 2.5 * first_idf / (1 + short_norm), 0],
        [0, 0, 2.5 * other_idf / (1 + short_norm)],
        [2.5 * other_idf / (1 + long_norm), 0, 0],
    ]
    assert weights.dtype == np.float32
    np.testing.assert_allclose(weights.toarray(), expected, rtol=2e-7, atol=0)


def test_depth_keeps_archived_boundary_selection_and_corpus_tie_order():
    np = pytest.importorskip("numpy")
    native = np.full(TOPK + 10, 2, dtype=np.float32)
    selected = np.argpartition(-native, TOPK)[:TOPK]
    assert _rank_positions(native, TOPK).tolist() == sorted(selected.tolist())
    assert _rank_positions(native, 3).tolist() == sorted(selected.tolist())[:3]
    small = np.array([1, 2, 2, 2, 2, 1, 0, -np.inf], dtype=np.float32)
    assert _rank_positions(small, TOPK).tolist() == [1, 2, 3, 4, 0, 5]


def test_mask_preserves_strict_cutoff_and_archived_missing_date_rule():
    index = SimpleNamespace(
        unit_rows={"A:app": 0, "equal": 1, "older": 2, "undated": 3},
        publication_days=(20200101, 20260101, 20251231, 0),
        publication_sha256=hashlib.sha256(b"synthetic publication table").hexdigest(),
    )
    mask = BM25FullEligibility(index, "app", "2026-01-01")
    assert mask.reason("A:app") == "excluded_id"
    assert mask.reason("equal") == "date_not_before_cutoff"
    assert mask.reason("older") is mask.reason("undated") is None
    assert mask.reason("unknown") == "unit_absent_from_corpus"
    assert mask.describe()["ordered_unit_publication_sha256"] == index.publication_sha256
    assert mask.describe()["dates"] == {}
    assert mask.fingerprint() != BM25FullEligibility(index, "app", "2026-02-01").fingerprint()


def test_retrieval_masks_before_depth_and_rerank_reuses_only_original_scores():
    np = pytest.importorskip("numpy")
    # Supply a fixed score row to exercise the shared callbacks independently of vectorization.
    index = BM25FullIndex.__new__(BM25FullIndex)
    index.unit_ids = ("A:app", "future", "a", "b")
    index.unit_rows = {unit_id: row for row, unit_id in enumerate(index.unit_ids)}
    index.publication_days = np.array([20200101, 20270101, 20200101, 20190101])
    index.publication_sha256 = hashlib.sha256(b"synthetic publication table").hexdigest()
    index._last_rerank = None
    queries = []

    def scores(text):
        queries.append(text)
        return np.array([75, 99, 9, 6] if text == "full original query" else [75, 99, 5, 8], dtype=np.float32)

    index._scores = scores
    mask = index.eligibility_for("app", "2026-01-01")
    query = ExpansionQuery("syn", (QueryTerm("new words", "source_copy"),))
    request = RerankRequest("app", "full original query", ("query",))
    with pytest.raises(ValueError, match="native depth"):
        index.search(query, TOPK + 1, mask)
    assert index.search(query, 1, mask) == [("b", 8.0)]
    assert index.rerank(request, ["b", "a"]) == {"a": 9.0, "b": 6.0}
    assert index.rerank(request, ["a"]) == {"a": 9.0}
    assert queries == ["new words", "full original query"]


def test_original_query_matches_frozen_cli_and_shares_search_rerank_backend(tmp_path):
    pytest.importorskip("sklearn")
    records = [
        ("A:app", "bearing bearing valve", "2019-01-01"),
        ("equal", "bearing bearing valve", "2026-01-01"),
        ("future", "bearing bearing valve", "2026-01-02"),
        ("undated", "bearing bearing valve", ""),
        ("z-old", "bearing bearing valve", "2019-01-01"),
        ("a-old", "bearing bearing valve", "2019-01-01"),
        ("no-match", "timer", "2019-01-01"),
    ]
    # More than one thousand tied matches exercise the archive's boundary partition.
    records += [(f"u-{i:04d}", "a VALVE bearing joint", "2020-01-01") for i in range(TOPK + 10)]
    inputs = tmp_path / "serialised"
    inputs.mkdir()
    (inputs / "passages.jsonl").write_text(
        "".join(json.dumps({"unit": unit, "text": text}) + "\n" for unit, text, _ in records),
        encoding="utf-8",
    )
    query_text = "VALVE bearing-bearing."
    (inputs / "queries.jsonl").write_text(
        json.dumps({"app_id": "app", "block": "P1-DEV", "text": query_text}) + "\n", encoding="utf-8",
    )
    units = tmp_path / "units.tsv"
    units.write_text(
        "unit_id\tfirst_pub\n" + "".join(f"{unit}\t{day}\n" for unit, _, day in records),
        encoding="utf-8",
    )
    tasks = tmp_path / "tasks.tsv"
    tasks.write_text("app_id\tfiling_date\napp\t2026-01-01\n", encoding="utf-8")
    out = tmp_path / "out"
    frozen_bm25([str(inputs), str(units), str(tasks), str(out), "P1-DEV"])
    with (out / "run-P1-DEV.tsv").open(encoding="utf-8", newline="") as handle:
        expected = [(row["unit"], row["score"]) for row in csv.DictReader(handle, delimiter="\t")]
    backend = BM25FullIndex(
        ((unit, text) for unit, text, _ in records), {unit: day for unit, _, day in records},
    )
    mask = backend.eligibility_for("app", "2026-01-01")
    request = RerankRequest("app", query_text, ("bearing",))
    original = backend.original(request, mask)
    assert [(unit, f"{score:.4f}") for unit, score in original] == expected
    assert [unit for unit, _ in original[:3]] == ["undated", "z-old", "a-old"]
    same_query = ExpansionQuery("synthetic", (QueryTerm(query_text, "original_query"),))
    assert backend.search(same_query, TOPK, mask) == original
    assert backend.search(same_query, 15, mask) == original[:15]
    assert backend.rerank(request, ["no-match", "z-old"]) == {"no-match": 0.0, "z-old": original[1][1]}
