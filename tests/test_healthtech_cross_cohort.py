import json
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "compare_cross_cohort", ROOT / "scripts/healthtech/compare_cross_cohort.py"
)
_MODULE = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODULE)
build_comparison = _MODULE.build_comparison
render_report = _MODULE.render_report


def _inputs():
    methods = ("HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3")

    def frontier(device_count: int, values: dict[str, float]) -> dict:
        return {
            "status": "DESCRIPTIVE_DEVELOPMENT_FRONTIER",
            "primary_k": 20,
            "error_count": 0,
            "by_method": {
                method: {
                    "macro_known_link_recall_at_20": values[method],
                    "device_count": device_count,
                    "failed_device_count": 0,
                    "realized_query_count": float(device_count),
                }
                for method in methods
            },
            "quality_resource_frontier": {
                "fixed_prefix_alignment": {"first_query_match_across_fixed_methods": True},
                "rows": [],
            },
        }

    model_revisions = {"encoder": "fixture-encoder@r1", "reranker": "fixture-reranker@r1"}
    return {
        "abbott_protocol": {
            "status": "FIXTURE_DEVELOPMENT_ONLY",
            "counts": {"eligible_devices": 3, "universe_patents": 41, "disclosed_pairs": 61, "unjudged_distractor_pairs": 4},
            "split": {"final_holdout": []},
            "source_refs": {"fixture": "authored"},
        },
        "abbott_receipt": {"model_revisions": model_revisions},
        "abbott_frontier": frontier(3, {
            "HT-B0a": 0.442739,
            "HT-B0b": 0.6622417082775139,
            "HT-B1": 0.498802,
            "HT-B2": 0.568912,
            "HT-B3": 0.498802,
        }),
        "abbott_groups": {
            "company_groups": ["fixture-company"],
            "shared_exact_patent_groups": ["fixture-patent-1", "fixture-patent-2"],
            "family_mapping": {"status": "UNKNOWN"},
            "group_evidence": [],
        },
        "abbott_split": {"final_holdout": []},
        "abbott_distractors": {"status": "AUTHORED_FIXTURE"},
        "boston_manifest": {
            "status": "FIXTURE_DEVELOPMENT_ONLY",
            "devices": 2,
            "patents": 7,
            "reference_pairs": 8,
            "unjudged_distractor_pairs": 2,
            "cohort_sha256": "fixture",
        },
        "boston_receipt": {"model_revisions": model_revisions},
        "boston_frontier": frontier(2, {method: 1.0 for method in methods}),
        "boston_groups": {
            "company_groups": ["fixture-company"],
            "shared_exact_patent_groups": ["fixture-patent-1"],
            "family_mapping": {"status": "UNKNOWN"},
            "group_evidence": [],
        },
        "boston_split": {"final_holdout": []},
        "boston_distractors": {"status": "AUTHORED_FIXTURE"},
    }


def test_cross_cohort_comparison_flags_ceiling_and_low_group_status():
    data = _inputs()
    source_files = {key: ROOT / "pyproject.toml" for key in data}
    comparison = build_comparison(run_id="test", source_files=source_files, **data)

    assert comparison["status"] == "PASS"
    assert comparison["cohorts"]["Abbott"]["exact_patent_group_count"] == 2
    assert comparison["cohort_flags"]["Abbott"]["descriptive_low_effective_group_status"] is True
    assert comparison["cohort_flags"]["Boston Scientific WATCHMAN"]["k_exceeds_candidate_universe"] is True
    assert comparison["cohorts"]["Abbott"]["company_group_count"] == 1
    assert comparison["cohorts"]["Abbott"]["exact_patent_group_count"] == 2
    assert comparison["methods_by_cohort"]["HT-B0b"]["abbott"]["macro_known_link_recall_at_20"] == 0.6622417082775139
    assert comparison["methods_by_cohort"]["HT-B0a"]["boston_minus_abbott"]["macro_known_link_recall_at_20"] > 0.5
    assert comparison["comparability"]["cross_cohort_score_comparison_allowed"] is False
    assert "ceiling-limited" in render_report(comparison)


def test_cross_cohort_comparison_rejects_method_set_drift():
    data = _inputs()
    data["boston_frontier"] = json.loads(json.dumps(data["boston_frontier"]))
    del data["boston_frontier"]["by_method"]["HT-B3"]
    source_files = {key: ROOT / "pyproject.toml" for key in data}
    comparison = build_comparison(run_id="test", source_files=source_files, **data)

    assert comparison["status"] == "FAIL"
    assert any("method set" in issue for issue in comparison["validation"]["issues"])
