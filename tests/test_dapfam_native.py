import math

import pytest

from patent_to_pilot.evaluation.dapfam_native import evaluate_native_dev, evaluate_paper1_dev, native_dev_task
from patent_to_pilot.research.mtm_runtime import InputBoundaryError


def fixtures():
    corpus = [{"relevant_id": f, "title_en": f + " title", "abstract_en": "abstract", "claims_text": "claim"}
              for f in ("A", "B", "C")]
    queries = [{"query_id": q, "title_en": "query title", "abstract_en": "query abstract",
                "claims_text": "must not enter TA"} for q in ("q1", "q2", "q3")]
    relations = [{"query_id": "q1", "relevant_id": "A", "relevance_score": 2, "domain_rel": "IN"},
                 {"query_id": "q1", "relevant_id": "B", "relevance_score": 3, "domain_rel": "OUT"},
                 {"query_id": "q2", "relevant_id": "B", "relevance_score": 1, "domain_rel": "OUT"},
                 {"query_id": "q3", "relevant_id": "C", "relevance_score": 0, "domain_rel": "OUT"}]
    return corpus, queries, relations


def test_paper1_bridge_keeps_cutoffs_distinct_and_missing_queries_in_paired_data():
    # Relevant results straddle 10/100/200; an unretrieved positive must still
    # contribute to IDCG and recall denominators. q2 has no output at all.
    families = [f"F{i:03}" for i in range(202)]
    task = {"candidate_policy": "full", "partition": "OUT",
            "corpus": dict.fromkeys(families), "queries": {"q1": "", "q2": ""},
            "qrels": {"q1": {families[i]: 1 for i in (9, 99, 199, 201)},
                      "q2": {families[0]: 1}}}
    result = evaluate_paper1_dev(task, {"q1": families[:200]})
    assert result["metrics"]["Recall@10"] == .125
    assert result["metrics"]["Recall@100"] == .25
    assert result["metrics"]["Recall@200"] == .375
    ideal = sum(1 / math.log2(i + 2) for i in range(4))
    assert result["per_query"]["q1"]["NDCG@10"] == pytest.approx(1 / math.log2(11) / ideal)
    assert set(result["per_query"]) == {"q1", "q2"}
    assert all(v == 0 for v in result["per_query"]["q2"].values())
    assert result["queries"] == 2 and result["missing_rankings"] == 1
    assert result["metric_contract"]["primary_metric"] == "Recall@200"
    assert "per_query" not in evaluate_native_dev(task, {"q1": families[:200]})


def test_partitions_only_change_qrels_and_text_fields_are_exact():
    tasks = [native_dev_task(*fixtures(), partition=p) for p in ("ALL", "IN", "OUT")]
    assert tasks[0]["corpus"] == tasks[1]["corpus"] == tasks[2]["corpus"]
    assert tasks[0]["qrels"]["q1"] == {"A": 1, "B": 1}
    assert tasks[1]["qrels"] == {"q1": {"A": 1}}
    assert tasks[2]["qrels"] == {"q1": {"B": 1}, "q2": {"B": 1}}
    assert tasks[2]["queries_without_partition_positives"] == 1
    assert tasks[2]["corpus"]["A"] == {"title": "A title", "text": "abstract\nclaim"}
    assert tasks[2]["queries"]["q1"] == "query title\nquery abstract"


def test_hand_calculated_ndcg_and_same_domain_candidate_stays_in_out():
    task = native_dev_task(*fixtures(), partition="OUT")
    result = evaluate_native_dev(task, {"q1": ["A", "C", "B"], "q2": ["B", "A", "C"]}, cutoffs=(1, 3, 100))
    assert result["metrics"]["NDCG@1"] == 0.5
    assert result["metrics"]["NDCG@3"] == 0.75
    assert result["metrics"]["Recall@3"] == 1
    assert result["queries"] == 2
    task_all = native_dev_task(*fixtures(), partition="ALL")
    value = evaluate_native_dev(task_all, {"q1": ["A", "C", "B"], "q2": ["B"]}, cutoffs=(3,))
    expected = (1.5 / (1 + 1 / math.log2(3)) + 1) / 2
    assert value["metrics"]["NDCG@3"] == round(expected, 5)


def test_missing_and_empty_outputs_keep_denominator():
    task = native_dev_task(*fixtures(), partition="OUT")
    missing = evaluate_native_dev(task, {"q1": ["B"]})
    empty = evaluate_native_dev(task, {"q1": ["B"], "q2": []})
    assert missing["queries"] == empty["queries"] == 2
    assert missing["metrics"] == empty["metrics"] == {"NDCG@100": 0.5, "Recall@100": 0.5}
    assert missing["missing_rankings"] == empty["empty_rankings"] == 1


@pytest.mark.parametrize("ranking", [["B", "B"], ["unknown"], [{"id": "B"}]])
def test_bad_rankings_rejected(ranking):
    task = native_dev_task(*fixtures(), partition="OUT")
    with pytest.raises(InputBoundaryError):
        evaluate_native_dev(task, {"q1": ranking})


def test_native_out_cannot_activate_x_mask():
    with pytest.raises(InputBoundaryError):
        native_dev_task(*fixtures(), partition="OUT", candidate_policy="X")


def test_duplicate_ids_and_relations_rejected_instead_of_last_write_wins():
    corpus, queries, relations = fixtures()
    for inputs in ((corpus * 2, queries, relations), (corpus, queries * 2, relations),
                   (corpus, queries, relations * 2)):
        with pytest.raises(InputBoundaryError):
            native_dev_task(*inputs, partition="OUT")


def test_no_positive_partition_fails_explicitly_and_falsey_text_is_skipped():
    corpus, queries, relations = fixtures()
    corpus[0]["claims_text"] = None
    queries[0]["abstract_en"] = ""
    task = native_dev_task(corpus, queries, [], partition="OUT")
    assert task["corpus"]["A"]["text"] == "abstract"
    assert task["queries"]["q1"] == "query title"
    with pytest.raises(InputBoundaryError):
        evaluate_native_dev(task, {})


@pytest.mark.parametrize("partition", ["ALL", "IN", "OUT"])
def test_nonpositive_domain_markers_do_not_change_native_positive_qrels(partition):
    c, q, r = fixtures()
    expected = native_dev_task(c, q, r, partition=partition)
    r[-1]["domain_rel"] = "NONPOSITIVE_SYNTHETIC_MARKER"
    assert native_dev_task(c, q, r, partition=partition) == expected
    r[-1]["relevance_score"] = 1
    with pytest.raises(InputBoundaryError, match="annotation"):
        native_dev_task(c, q, r, partition=partition)
    r[-1]["relevance_score"] = float("nan")
    with pytest.raises(InputBoundaryError, match="annotation"):
        native_dev_task(c, q, r, partition=partition)
