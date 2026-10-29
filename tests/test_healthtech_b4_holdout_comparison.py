import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "compare_b4_holdout", ROOT / "scripts/healthtech/compare_b4_holdout.py"
)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
build_comparison = _MODULE.build_comparison
write_outputs = _MODULE.write_outputs


def _offline():
    return {
        "by_method": {
            "HT-B0a": {"macro_known_link_recall_at_20": 0.8, "query_calls": 3, "rerank_pairs": 0},
            "HT-B0b": {"macro_known_link_recall_at_20": 0.9, "query_calls": 3, "rerank_pairs": 0},
            "HT-B1": {"macro_known_link_recall_at_20": 0.85, "query_calls": 3, "rerank_pairs": 72},
            "HT-B2": {"macro_known_link_recall_at_20": 0.85, "query_calls": 12, "rerank_pairs": 288},
            "HT-B3": {"macro_known_link_recall_at_20": 0.75, "query_calls": 5, "rerank_pairs": 120},
        }
    }


def _b4_frontier():
    return {
        "device_count": 3,
        "failed_device_count": 0,
        "macro_known_link_recall_at_20": 0.75,
        "micro_known_link_recall_at_20": 0.7,
        "provider_calls": 8,
        "resources": {"query_calls": 5, "rerank_pairs": 120},
        "per_device": [{"resources": {"method_wall_seconds": 1.5, "method_cpu_seconds": 2.0}}],
    }


def _b4_receipt():
    return {
        "paid_cost_usd": 0.0,
        "simulated_cost_usd": 0.0008,
        "ledger_snapshot": {"unknown_or_pending": [], "breach": False},
        "policy": {"models": {"openai/gpt-4.1-mini": "openai"}, "pricing_snapshot_sha256": "hash", "pricing_snapshot_utc": "time"},
    }


def test_holdout_comparison_reports_b4_delta_and_mock_boundary():
    comparison = build_comparison(
        offline_frontier=_offline(),
        b4_frontier=_b4_frontier(),
        b4_receipt=_b4_receipt(),
        code_commit="code",
        protocol_hash="protocol",
        cohort_manifest_hash="cohort",
    )
    assert comparison["status"] == "PASS_B4_PROVIDER_SHAPED_HOLDOUT_DESCRIPTIVE"
    assert comparison["b4_provider_shaped_mock"]["provider_shaped_calls"] == 8
    assert comparison["deltas_vs_controls"][1]["b4_minus_control_macro_recall"] == pytest.approx(-0.15)
    assert comparison["b4_provider_shaped_mock"]["status"] == "MOCK_ONLY_NOT_PROVIDER_EVIDENCE"


def test_holdout_comparison_writes_outputs(tmp_path):
    comparison = build_comparison(
        offline_frontier=_offline(),
        b4_frontier=_b4_frontier(),
        b4_receipt=_b4_receipt(),
        code_commit="code",
        protocol_hash="protocol",
        cohort_manifest_hash="cohort",
    )
    output = tmp_path / "out"
    write_outputs(output, comparison)
    assert (output / "comparison.json").exists()
    assert "HT-B4-MOCK" in (output / "COMPARISON.md").read_text(encoding="utf-8")
