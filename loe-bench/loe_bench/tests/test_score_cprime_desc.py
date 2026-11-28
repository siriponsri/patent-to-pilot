"""Synthetic fixtures for the CPRIME-DESC aggregate workflow."""

from math import sqrt
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import score_cprime_desc as desc


def test_calibration_uses_higher_bin_on_boundary_and_includes_one():
    probabilities = [0.0] * 5 + [0.099] * 5 + [0.1] * 10 + [1.0] * 10
    labels = ([0] * 5 + [1] * 5) * 3
    bins = desc.calibration_bins(probabilities, labels)
    assert len(bins) == 10
    for index, predicted_mean in ((0, 0.0495), (1, 0.1), (9, 1.0)):
        cell = bins[index]
        assert (cell["rows"], cell["events"]) == (10, 5)
        assert cell["mean_calibrated_probability"] == pytest.approx(predicted_mean)
        assert cell["observed_event_rate"] == 0.5
        assert cell["wilson_95"] == pytest.approx([0.236593, 0.763407], abs=1e-6)
    assert bins[8]["rows"] == bins[8]["events"] == "<5"
    assert bins[8]["mean_calibrated_probability"] is None
    assert bins[9]["upper_inclusive"]


def test_small_bin_withholds_statistics_and_complement():
    bins = desc.calibration_bins([0.02] * 4 + [0.15] * 10 + [0.25] * 10,
                                 [1] * 4 + ([0] * 5 + [1] * 5) * 2)
    assert bins[0]["rows"] == bins[0]["events"] == "<5"
    assert bins[0]["mean_calibrated_probability"] is None
    assert bins[0]["wilson_95"] is None
    # Equal-sized complementary candidates use the lower bin.
    assert bins[1]["events"] == "WITHHELD"
    assert bins[1]["observed_event_rate"] is None
    assert bins[1]["mean_calibrated_probability"] == pytest.approx(0.15)
    assert bins[2]["events"] == 5


def test_large_bin_with_small_outcome_cell_withholds_rate():
    bins = desc.calibration_bins([0.23] * 10 + [0.33] * 10,
                                 [0] * 2 + [1] * 8 + [0] * 9 + [1])
    assert bins[2]["events"] == "WITHHELD"
    assert bins[3]["events"] == "<5"
    for cell in bins[2:4]:
        assert cell["rows"] == 10
        assert cell["mean_calibrated_probability"] is not None
        assert cell["observed_event_rate"] is None
        assert cell["wilson_95"] is None


def test_development_uses_observed_numeric_values_and_encoded_flags():
    rows = [{"x": {"strength_count": value, "strength_missing": 0}} for value in range(1, 6)]
    rows.extend({"x": {"strength_count": 0, "strength_missing": 1}} for _ in range(5))
    result = desc.development_predictors(rows, ("strength_count", "strength_missing"))
    assert result["strength_count"] == {
        "count": 5, "missing": 5, "mean": 3.0, "sd": sqrt(2.5),
        "quantiles": {"5": 1.2, "25": 2.0, "50": 3.0, "75": 4.0, "95": 4.8},
    }
    assert result["strength_missing"] == {"levels": {"0": 5, "1": 5}}
    sparse = desc.numeric_summary([2.0, 3.0], 8)
    assert (sparse["count"], sparse["missing"], sparse["mean"], sparse["sd"]) == ("<5", 8, None, None)
    assert all(value is None for value in sparse["quantiles"].values())


def test_export_reconciles_score_and_preserves_unavailable_fields():
    rows = [{"y": i % 2, **dict.fromkeys(desc.supplement.ARMS, 0.5)} for i in range(10)]
    calibrator = {"intercept": 0, "weight": 1, "mean": 0, "scale": 1}
    settings = dict.fromkeys(desc.supplement.ARMS, {"calibrator": calibrator})
    score = {
        "rows": 10, "event_rows": 5,
        "arms": dict.fromkeys(desc.supplement.ARMS, {"ece_bin_counts": [0] * 5 + [10] + [0] * 4}),
        "levels": dict.fromkeys(desc.supplement.ARMS,
                                 {"brier": {"estimate": 0.25}, "ece": {"estimate": 0.0}}),
        "eligibility_and_coverage": {"fixture": {
            "dated_nda_drugs": 25, "no_eligible_type1": 10, "prior_final_anda": 5,
            "eligible_rows": 10, "events": 5, "missing_features": {"strength_missing": 5},
            "graph_verdict": {"OPEN": 5, "BLOCKED": 5},
        }},
    }
    result = desc.cprime_summary(rows, settings, score,
                                 ("b1_age_hazard_logit", "age_years", "strength_count",
                                  "strength_missing", "verdict_OPEN", "orphan"))
    assert result["calibration"]["B1"][5]["events"] == 5
    assert result["predictors"]["b1_age_hazard_logit"]["sd"] == 0.0
    assert result["predictors"]["age_years"]["mean"] == "UNAVAILABLE"
    assert result["predictors"]["strength_count"]["missing"] == 5
    assert result["predictors"]["verdict_OPEN"] == {"levels": {"0": 5, "1": 5}}
    assert result["predictors"]["orphan"] == {"levels": {"0": "UNAVAILABLE", "1": "UNAVAILABLE"}}
    assert result["eligibility_flow"]["dated_type1_candidates"] == 15
    assert result["eligibility_flow"]["prior_final_anda_before_nda"] == "UNAVAILABLE"
    with pytest.raises(ValueError, match="SCORE overall"):
        desc.cprime_summary(rows, settings, {**score, "event_rows": 6}, ())
