import json

from scripts.healthtech.summarize_private_frontier import summarize


def _write_fixture(root):
    receipt = {
        "status": "REAL_PUBLIC_DEVELOPMENT_RUN",
        "code_commit": "abc123",
        "protocol_hash": "protocol",
        "cohort_manifest_hash": "cohort",
        "methods": ["HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3"],
        "devices": 3,
        "patents": 41,
        "reference_pairs": 61,
        "candidate_depth": 41,
        "rerank_depth": 41,
        "provider_calls": 0,
        "paid_cost_usd": 0,
    }
    resources = {
        "attempt_count": 3,
        "query_calls": 3,
        "rerank_pairs": 123,
        "rerank_tokens": 0,
        "embedding_query_tokens": 0,
        "returned_candidates": 123,
        "method_cpu_seconds": 1.0,
        "method_wall_seconds": 0.5,
        "resource_accounting_status": "COMPLETE",
        "unknown_resource_fields": [],
    }
    method_summary = {
        method: {
            "completed_query_count": 3,
            "failed_query_count": 0,
            "method": method,
            "query_count": 3,
            "resources": {**resources, "query_calls": 3 if method != "HT-B2" else 9},
        }
        for method in receipt["methods"]
    }
    by_method = {
        method: {
            "macro_known_link_recall_at_20": 0.5,
            "micro_known_link_recall_at_20": 0.4,
        }
        for method in receipt["methods"]
    }
    prefix_rows = []
    for method in ["HT-B1", "HT-B2", "HT-B3"]:
        prefix_rows.append(
            {
                "method": method,
                "prefix": 1,
                "scheduled_query_count": 1,
                "reached_query_count": 3,
                "failed_query_count": 0,
                "not_realized_query_count": 0,
                "query_calls": 3,
                "rerank_pairs": 123,
                "rerank_tokens": 0,
                "embedding_query_tokens": 0,
                "returned_candidates": 123,
                "cpu_seconds": 1.0,
                "wall_seconds": 0.5,
                "macro_known_link_recall_at_20_all_devices": 0.5,
                "micro_known_link_recall_at_20_all_devices": 0.4,
                "first_query": "must not be exported",
                "query_ids": ["must-not-be-exported"],
            }
        )
    for name, data in {
        "receipt.json": receipt,
        "method_summary.json": method_summary,
        "frontier_diagnostics.json": {
            "by_method": by_method,
            "quality_resource_frontier": {
                "rows": prefix_rows,
                "uncertainty": {"status": "NOT_ESTIMABLE"},
            },
        },
        "per_device_group_results.json": {method: {"by_k": {}} for method in receipt["methods"]},
        "evaluator_validation.json": {
            "reference_query_count": 3,
            "reference_pair_count": 61,
            "shared_reference_groups": [["a", "b"], ["c"]],
            "runtime_reference_separation": "PASS",
        },
    }.items():
        (root / name).write_text(json.dumps(data), encoding="utf-8")
    (root / "raw_rankings.jsonl").write_text(
        "\n".join(json.dumps({"status": "completed", "query_text": "private"}) for _ in range(3)) + "\n",
        encoding="utf-8",
    )


def test_private_frontier_summary_omits_payload_and_marks_budget_boundary(tmp_path):
    _write_fixture(tmp_path)

    result = summarize(tmp_path)

    assert result["budget_comparability"]["equal_total_budget_across_methods"] is False
    assert result["budget_comparability"]["matched_first_action"]["status"] == "PASS_OBSERVED"
    slices = result["budget_comparability"]["budget_ceiling_slices"]
    assert len(slices) == 1
    assert slices[0]["ceiling"] == {"query_calls": 3, "rerank_pairs": 123}
    assert slices[0]["equal_realized_budget"] is True
    assert slices[0]["all_required_methods_present"] is True
    assert result["evaluation_scope"]["final_holdout"] == "NOT_PRESENT_IN_PRIVATE_DEVELOPMENT_RECEIPT"
    assert result["privacy"]["raw_query_or_patent_text_exported"] is False
    serialized = json.dumps(result)
    assert "must not be exported" not in serialized
    assert "must-not-be-exported" not in serialized
    assert result["raw_ranking_rows"] == 3
