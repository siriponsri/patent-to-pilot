import json

from scripts.healthtech.render_current_head_frontier import (
    load_rows,
    render_budget_svg,
    render_recall_svg,
    stable_repo_path,
)


def test_renderer_manifest_path_is_machine_independent(tmp_path):
    path = tmp_path / "workspace" / "docs" / "healthtech" / "verification.json"
    assert stable_repo_path(path) == "docs/healthtech/verification.json"

    external = tmp_path / "private" / "metadata-observation.json"
    assert stable_repo_path(external) == "<external>/metadata-observation.json"


def test_current_head_frontier_renderer_binds_candidate_and_labels_limits(tmp_path):
    verification = {
        "format": "ptp-current-head-offline-verification-v1",
        "candidate": {"head": "abc123"},
        "frozen_inputs": {"protocol_hash": "p", "cohort_manifest_sha256": "c"},
        "results": {
            "HT-B0a": {"macro_recall_at_20": 0.4, "query_calls": 3, "rerank_pairs": 0, "failed_queries": 0},
            "HT-B0b": {"macro_recall_at_20": 0.6, "query_calls": 3, "rerank_pairs": 0, "failed_queries": 0},
            "HT-B1": {"macro_recall_at_20": 0.5, "query_calls": 3, "rerank_pairs": 12, "failed_queries": 0},
            "HT-B2": {"macro_recall_at_20": 0.55, "query_calls": 9, "rerank_pairs": 36, "failed_queries": 0},
            "HT-B3": {"macro_recall_at_20": 0.5, "query_calls": 5, "rerank_pairs": 20, "failed_queries": 0},
            "HT-B4-offline": {"macro_recall_at_20": 0.5, "micro_recall_at_20": 0.47, "query_calls": 5, "rerank_pairs": 20, "controller_steps": 8, "failed_queries": 0},
        },
    }
    path = tmp_path / "verification.json"
    path.write_text(json.dumps(verification), encoding="utf-8")
    data = load_rows(path, "abc123")
    assert [row["method"] for row in data["rows"]] == ["HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3", "HT-B4-offline"]
    assert "Current-head development-only" in render_recall_svg(data["rows"])
    assert "totals are observed, not equalized" in render_budget_svg(data["rows"])
