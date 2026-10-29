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


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def _inputs():
    return {
        "abbott_protocol": _load("results/healthtech/ht-abbott-development-20261028-r1/protocol.json"),
        "abbott_receipt": _load("results/healthtech/ht-real-baselines-20261029-frozen-r1/receipt.json"),
        "abbott_frontier": _load("results/healthtech/ht-real-baselines-20261029-frozen-r1/frontier_diagnostics.json"),
        "abbott_groups": _load("results/healthtech/ht-abbott-development-20261028-r1/protocol.json")["groups"],
        "abbott_split": _load("results/healthtech/ht-abbott-development-20261028-r1/split_manifest.json"),
        "abbott_distractors": _load("results/healthtech/ht-abbott-development-20261028-r1/distractors.json"),
        "boston_manifest": _load("results/healthtech/ht-boston-watchman-20261028-r4/manifest.json"),
        "boston_receipt": _load("results/healthtech/ht-boston-baselines-20261028-r3/receipt.json"),
        "boston_frontier": _load("results/healthtech/ht-boston-baselines-20261028-r3/frontier_diagnostics.json"),
        "boston_groups": _load("results/healthtech/ht-boston-watchman-20261028-r4/groups.json"),
        "boston_split": _load("results/healthtech/ht-boston-watchman-20261028-r4/split_manifest.json"),
        "boston_distractors": _load("results/healthtech/ht-boston-watchman-20261028-r4/distractors.json"),
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
