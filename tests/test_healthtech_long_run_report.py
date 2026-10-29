import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "build_long_run_report", ROOT / "scripts/healthtech/build_long_run_report.py"
)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
build_summary = _MODULE.build_summary
render_report = _MODULE.render_report


METHODS = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3")


def _write_json(path: Path, value: object) -> Path:
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _frontier(recall: float) -> dict:
    return {
        "by_method": {
            method: {
                "realized_query_count": 1,
                "macro_known_link_recall_at_20": recall,
                "query_calls": 2,
                "rerank_pairs": 3,
                "embedding_query_tokens": 4,
                "rerank_tokens": 5,
                "returned_candidates": 6,
                "failed_device_count": 0,
            }
            for method in METHODS
        },
        "groups": [
            {"method": method, "group_id": "group-1"}
            for method in METHODS
        ],
    }


def _method_summary() -> dict:
    return {
        method: {
            "resources": {
                "method_wall_seconds": 1.5,
                "method_cpu_seconds": 0.5,
            }
        }
        for method in METHODS
    }


def test_long_run_report_aggregates_frozen_inputs_and_renders_boundaries(tmp_path):
    dev_frontier = _write_json(tmp_path / "dev-frontier.json", _frontier(0.9))
    holdout_frontier = _write_json(tmp_path / "holdout-frontier.json", _frontier(0.4))
    dev_summary = _write_json(tmp_path / "dev-summary.json", _method_summary())
    holdout_summary = _write_json(tmp_path / "holdout-summary.json", _method_summary())
    dev_receipt = _write_json(tmp_path / "dev-receipt.json", {"status": "DEV"})
    holdout_receipt = _write_json(tmp_path / "holdout-receipt.json", {"status": "HOLDOUT"})
    b4_frontier = _write_json(
        tmp_path / "b4-frontier.json",
        {
            "device_count": 1,
            "failed_device_count": 0,
            "macro_known_link_recall_at_20": 1.0,
            "per_device": [{"resources": {"query_calls": 2, "rerank_pairs": 3}}],
        },
    )
    b4_receipt = _write_json(
        tmp_path / "b4-receipt.json",
        {
            "patents": 2,
            "paid_cost_usd": 0.0,
            "simulated_cost_usd": 0.001,
            "ledger_snapshot": {"unknown_or_pending": [], "actual_nano_usd": 1000000},
            "policy": {
                "models": {"openai/gpt-4.1-mini": "openai"},
                "pricing_snapshot_sha256": "pricing-hash",
                "pricing_snapshot_utc": "2026-10-29T00:00:00Z",
            },
        },
    )
    b4_raw_rankings = tmp_path / "b4-raw-rankings.jsonl"
    b4_raw_rankings.write_text(
        json.dumps(
            {
                "actions": [
                    {
                        "controller_call": {
                            "input_token_bound": 10,
                            "output_token_bound": 4,
                            "latency_seconds": 0.25,
                            "response_schema_valid": True,
                        }
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    b4_verification = _write_json(tmp_path / "b4-verification.json", {"status": "MOCK"})

    summary = build_summary(
        dev_frontier=dev_frontier,
        dev_summary=dev_summary,
        dev_receipt=dev_receipt,
        holdout_frontier=holdout_frontier,
        holdout_summary=holdout_summary,
        holdout_receipt=holdout_receipt,
        b4_frontier=b4_frontier,
        b4_receipt=b4_receipt,
        b4_raw_rankings=b4_raw_rankings,
        b4_verification=b4_verification,
        code_commit="test-commit",
        protocol_hash="protocol-hash",
        cohort_manifest_hash="cohort-hash",
    )

    assert len(summary["development"]["rows"]) == 5
    assert summary["development"]["rows"][0]["macro_known_link_recall_at_20"] == 0.9
    assert summary["final_holdout"]["rows"][0]["macro_known_link_recall_at_20"] == 0.4
    assert summary["b4_provider_shaped_mock"]["row"]["provider_shaped_calls"] == 1
    assert summary["b4_provider_shaped_mock"]["row"]["schema_valid_calls"] == 1
    assert summary["b4_provider_shaped_mock"]["row"]["unknown_billing"] == 0
    assert len(summary["input_hashes"]) == 10

    report = render_report(summary)
    assert "PARTIAL" in report
    assert "HT-B4 provider-shaped mock" in report
    assert "NOT_RUN / BLOCKED_LOCAL" in report
    assert "semantic relevance gold" in report

    holdout_b4_frontier = _write_json(
        tmp_path / "b4-holdout-frontier.json",
        {
            "device_count": 1,
            "failed_device_count": 0,
            "macro_known_link_recall_at_20": 0.8,
            "per_device": [{"resources": {"query_calls": 3, "rerank_pairs": 4}}],
        },
    )
    holdout_b4_receipt = _write_json(
        tmp_path / "b4-holdout-receipt.json",
        {
            "patents": 2,
            "paid_cost_usd": 0.0,
            "simulated_cost_usd": 0.002,
            "ledger_snapshot": {"unknown_or_pending": [], "actual_nano_usd": 2000000},
            "policy": {
                "models": {"openai/gpt-4.1-mini": "openai"},
                "pricing_snapshot_sha256": "pricing-hash",
                "pricing_snapshot_utc": "2026-10-29T00:00:00Z",
            },
        },
    )
    holdout_b4_raw_rankings = tmp_path / "b4-holdout-raw-rankings.jsonl"
    holdout_b4_raw_rankings.write_text(b4_raw_rankings.read_text(encoding="utf-8"), encoding="utf-8")
    holdout_b4_verification = _write_json(tmp_path / "b4-holdout-verification.json", {"status": "MOCK_HOLDOUT"})
    holdout_summary = build_summary(
        dev_frontier=dev_frontier,
        dev_summary=dev_summary,
        dev_receipt=dev_receipt,
        holdout_frontier=holdout_frontier,
        holdout_summary=holdout_summary,
        holdout_receipt=holdout_receipt,
        b4_frontier=b4_frontier,
        b4_receipt=b4_receipt,
        b4_raw_rankings=b4_raw_rankings,
        b4_verification=b4_verification,
        b4_holdout_frontier=holdout_b4_frontier,
        b4_holdout_receipt=holdout_b4_receipt,
        b4_holdout_raw_rankings=holdout_b4_raw_rankings,
        b4_holdout_verification=holdout_b4_verification,
        code_commit="test-commit",
        protocol_hash="protocol-hash",
        cohort_manifest_hash="cohort-hash",
    )
    assert holdout_summary["b4_provider_shaped_holdout"]["row"]["split"] == "final_holdout"
    assert holdout_summary["b4_provider_shaped_holdout"]["row"]["macro_known_link_recall_at_20"] == 0.8
    assert len(holdout_summary["input_hashes"]) == 14
    assert "Final holdout B4 mock" in render_report(holdout_summary)
