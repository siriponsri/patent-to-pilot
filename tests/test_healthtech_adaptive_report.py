from __future__ import annotations

import pytest

from patent_to_pilot.healthtech.adaptive_report import (
    build_adaptive_policy_report,
    render_adaptive_policy_report,
    write_adaptive_policy_report,
)


def _holdout():
    methods = {
        "HT-B0a": (0.81, 3, 0),
        "HT-B0b": (0.95, 3, 0),
        "HT-B1": (0.93, 3, 72),
        "HT-B2": (0.93, 12, 288),
        "HT-B3": (0.88, 5, 120),
    }
    return {
        "status": "PASS_B4_PROVIDER_SHAPED_HOLDOUT_DESCRIPTIVE",
        "split": "final_holdout",
        "offline_controls": [
            {
                "method": method,
                "macro_known_link_recall_at_20": recall,
                "device_count": 3,
                "failed_device_count": 0,
                "query_calls": calls,
                "rerank_pairs": pairs,
                "paid_cost_usd": 0.0,
            }
            for method, (recall, calls, pairs) in methods.items()
        ],
        "b4_provider_shaped_mock": {
            "method": "HT-B4-MOCK",
            "status": "MOCK_ONLY_NOT_PROVIDER_EVIDENCE",
            "macro_known_link_recall_at_20": 0.88,
            "micro_known_link_recall_at_20": 0.84,
            "device_count": 3,
            "failed_device_count": 0,
            "query_calls": 5,
            "rerank_pairs": 120,
            "provider_shaped_calls": 8,
            "paid_cost_usd": 0.0,
            "simulated_cost_usd": 0.0008,
            "unknown_billing": 0,
            "ledger_breach": False,
        },
        "deltas_vs_controls": [{"method": method, "b4_minus_control_macro_recall": 0.0, "status": "DESCRIPTIVE_NOT_ESTIMABLE"} for method in methods],
        "interpretation": ["No superiority claim."],
    }


def _offline():
    def cohort(devices, patents, macro, micro, calls, steps):
        return {
            "devices": devices,
            "patents": patents,
            "metrics": {
                "macro_known_link_recall_at_20": macro,
                "micro_known_link_recall_at_20": micro,
                "query_calls": calls,
                "controller_steps": steps,
                "failed_devices": 0,
                "provider_calls": 0,
                "paid_cost_usd": 0.0,
            },
        }

    return {"cohorts": {"abbott": cohort(3, 41, 0.49, 0.47, 5, 8), "boston": cohort(2, 7, 1.0, 1.0, 2, 4)}}


def test_report_keeps_mock_boundary_and_offline_controller_separate():
    report = build_adaptive_policy_report(
        holdout_comparison=_holdout(),
        offline_verification=_offline(),
        cross_cohort_comparison={
            "status": "DEVELOPMENT_ONLY_FREEZE_NO_HOLDOUT",
            "methods": ["HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3"],
            "comparability": {"cross_cohort_score_comparison_allowed": False},
            "cohort_flags": {},
            "limitations": [],
        },
        code_commit="abc123",
        parent_audit="parent-audit",
        input_hashes={"holdout.json": "a" * 64},
    )
    assert report["status"] == "PARTIAL_OFFLINE_ADAPTIVE_POLICY_REPORT"
    assert report["adaptive_evidence"]["offline_deterministic_controller"]["is_llm"] is False
    assert report["adaptive_evidence"]["provider_shaped_mock"]["status"] == "MOCK_ONLY_NOT_PROVIDER_EVIDENCE"
    assert report["boundaries"]["live_qwen3_controller"] == "NOT_RUN_BLOCKED_LOCAL"
    assert "MOCK_ONLY_NOT_PROVIDER_EVIDENCE" in render_adaptive_policy_report(report)


def test_report_rejects_missing_fixed_control():
    payload = _holdout()
    payload["offline_controls"] = [row for row in payload["offline_controls"] if row["method"] != "HT-B2"]
    with pytest.raises(ValueError, match="required controls"):
        build_adaptive_policy_report(
            holdout_comparison=payload,
            offline_verification=_offline(),
            cross_cohort_comparison=None,
            code_commit="abc123",
            parent_audit="parent-audit",
            input_hashes={},
        )


def test_report_rejects_relabelled_live_adaptive_row():
    payload = _holdout()
    payload["b4_provider_shaped_mock"]["status"] = "LIVE_PROVIDER_EVIDENCE"
    with pytest.raises(ValueError, match="mock-only status"):
        build_adaptive_policy_report(
            holdout_comparison=payload,
            offline_verification=_offline(),
            cross_cohort_comparison=None,
            code_commit="abc123",
            parent_audit="parent-audit",
            input_hashes={},
        )


def test_report_writes_json_and_markdown(tmp_path):
    report = build_adaptive_policy_report(
        holdout_comparison=_holdout(),
        offline_verification=_offline(),
        cross_cohort_comparison=None,
        code_commit="abc123",
        parent_audit="parent-audit",
        input_hashes={},
    )
    write_adaptive_policy_report(tmp_path / "report", report)
    assert (tmp_path / "report" / "adaptive-policy-report.json").exists()
    assert "Adaptive acquisition policy report" in (tmp_path / "report" / "ADAPTIVE_POLICY_REPORT.md").read_text()
