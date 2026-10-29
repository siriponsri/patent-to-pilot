from scripts.healthtech.analyze_scifact_errors import build_analysis, classify_claim


def _row(claim_id: int, *, abstract: dict, sentence: dict) -> dict:
    return {"claim_id": claim_id, "abstract": abstract, "sentence": sentence}


def test_classify_scifact_failure_modes_separately():
    row = _row(
        1,
        abstract={"relevant": 2, "retrieved": 3, "correct_label_only": 1, "correct_rationalized": 0},
        sentence={"relevant": 3, "retrieved": 9, "correct_selection": 0, "correct_label": 0},
    )
    assert classify_claim(row) == [
        "abstract_partial_retrieval",
        "abstract_rationale_mismatch",
        "sentence_retrieval_miss",
    ]


def test_classify_no_gold_evidence_without_calling_it_a_miss():
    row = _row(
        2,
        abstract={"relevant": 0, "retrieved": 3, "correct_label_only": 0, "correct_rationalized": 0},
        sentence={"relevant": 0, "retrieved": 8, "correct_selection": 0, "correct_label": 0},
    )
    assert classify_claim(row) == ["abstract_no_gold_evidence", "sentence_no_gold_evidence"]


def test_build_analysis_is_deterministic_and_keeps_runtime_boundary():
    manifest = {
        "format": "ht-t2-scifact-prediction-manifest-v1",
        "split": "dev",
        "inputs": {"claims": 2, "corpus_documents": 10},
        "prediction_method": "test",
        "runtime_only_generation": True,
        "evaluator_labels_read_by_generator": False,
    }
    score = {"status": "PASS_COMPONENT_SCORE"}
    rows = [
        _row(1, abstract={"relevant": 1, "retrieved": 3, "correct_label_only": 1, "correct_rationalized": 1}, sentence={"relevant": 1, "retrieved": 3, "correct_selection": 1, "correct_label": 1}),
        _row(2, abstract={"relevant": 0, "retrieved": 3, "correct_label_only": 0, "correct_rationalized": 0}, sentence={"relevant": 0, "retrieved": 3, "correct_selection": 0, "correct_label": 0}),
    ]
    analysis, claim_rows = build_analysis(
        manifest=manifest,
        score=score,
        per_claim=rows,
        input_hashes={"manifest": "a"},
    )
    assert analysis["status"] == "PASS_COMPONENT_ERROR_ANALYSIS_DEV_ONLY"
    assert analysis["runtime_only_generation"] is True
    assert analysis["evaluator_labels_read_by_generator"] is False
    assert analysis["error_buckets"]["abstract_fully_aligned"]["count"] == 1
    assert analysis["error_buckets"]["abstract_no_gold_evidence"]["count"] == 1
    assert claim_rows[0]["claim_id"] == 1
