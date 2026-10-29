import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "analyze_long_run", ROOT / "scripts/healthtech/analyze_long_run.py"
)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
build_analysis = _MODULE.build_analysis
write_outputs = _MODULE.write_outputs


METHODS = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3")


def _rows(recall_values):
    return [
        {
            "method": method,
            "macro_known_link_recall_at_20": recall_values[method],
            "wall_seconds": wall,
            "query_calls": 1,
        }
        for method, wall in zip(METHODS, (0.1, 0.2, 1.0, 2.0, 1.5))
    ]


def _frontier():
    values = {
        "HT-B0a": (0.2, 0.4),
        "HT-B0b": (0.8, 0.9),
        "HT-B1": (0.7, 0.8),
        "HT-B2": (0.7, 0.8),
        "HT-B3": (0.6, 0.7),
    }
    return {
        "groups": [
            {"group_id": str(group_id), "method": method, "k": 20, "macro_known_link_recall": value}
            for method, method_values in values.items()
            for group_id, value in enumerate(method_values)
        ]
    }


def test_analysis_marks_observed_frontier_and_holdout_delta():
    summary = {
        "code_commit": "test-commit",
        "protocol_hash": "protocol",
        "cohort_manifest_hash": "cohort",
        "development": {"rows": _rows({m: 0.9 for m in METHODS})},
        "final_holdout": {
            "rows": _rows(
                {
                    "HT-B0a": 0.7,
                    "HT-B0b": 0.8,
                    "HT-B1": 0.75,
                    "HT-B2": 0.75,
                    "HT-B3": 0.7,
                }
            )
        },
        "b4_provider_shaped_mock": {
            "row": {
                "macro_known_link_recall_at_20": 0.9,
                "simulated_cost_usd": 0.001,
                "paid_cost_usd": 0.0,
            }
        },
    }
    analysis = build_analysis(
        summary=summary,
        dev_frontier=_frontier(),
        holdout_frontier=_frontier(),
        input_hashes={"summary": "hash"},
    )

    assert analysis["status"] == "PASS_DESCRIPTIVE_ANALYSIS_NOT_ESTIMABLE"
    assert analysis["code_commit"] == "test-commit"
    assert analysis["development"]["rows"][0]["pareto_frontier"] is True
    assert analysis["development"]["pareto_frontier_methods"] == ["HT-B0a"]
    assert analysis["final_holdout"]["pareto_frontier_methods"] == ["HT-B0a", "HT-B0b"]
    assert analysis["holdout_minus_development"][1]["macro_recall_delta_holdout_minus_development"] == pytest.approx(-0.1)
    assert analysis["b4_provider_shaped_mock"]["status"] == "MOCK_ONLY_NOT_PROVIDER_EVIDENCE"
    paired = analysis["paired_group_uncertainty"]["development"]["methods"]["HT-B0a"]
    assert paired["paired_group_count"] == 2
    assert paired["mean_delta"] == pytest.approx(-0.55)
    assert paired["population_sd"] == pytest.approx(0.05)
    assert paired["status"] == "NOT_ESTIMABLE"


def test_analysis_writes_reproducible_tables_and_svg_plots(tmp_path):
    summary = {
        "code_commit": "test-commit",
        "protocol_hash": "protocol",
        "cohort_manifest_hash": "cohort",
        "development": {"rows": _rows({m: 0.9 for m in METHODS})},
        "final_holdout": {"rows": _rows({m: 0.8 for m in METHODS})},
        "b4_provider_shaped_mock": {
            "row": {
                "macro_known_link_recall_at_20": 0.9,
                "simulated_cost_usd": 0.001,
                "paid_cost_usd": 0.0,
            }
        },
    }
    analysis = build_analysis(summary=summary, dev_frontier=_frontier(), holdout_frontier=_frontier())
    output = tmp_path / "out"
    write_outputs(output, analysis)

    assert (output / "analysis.json").exists()
    assert (output / "quality_cost_frontier.csv").read_text(encoding="utf-8").count("HT-B0a") == 2
    assert "<svg" in (output / "quality_cost_development.svg").read_text(encoding="utf-8")
    assert "final-holdout" in (output / "recall_comparison.svg").read_text(encoding="utf-8")
    assert "Paired group diagnostic" in (output / "ANALYSIS.md").read_text(encoding="utf-8")


def test_paired_group_diagnostic_rejects_duplicate_group_rows():
    frontier = _frontier()
    frontier["groups"].append({"method": "HT-B0a", "k": 20, "group_id": "0", "macro_known_link_recall": 0.3})
    with pytest.raises(ValueError, match="duplicate group_id"):
        _MODULE._paired_group_uncertainty(frontier)
