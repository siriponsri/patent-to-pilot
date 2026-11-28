"""Produce the locked C-prime supplement from authenticated C1 score exports."""

import argparse
from datetime import date
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loe_bench.baselines import Logistic
from loe_bench.common import add_months
from loe_bench.metrics import auroc
from loe_bench.priorarms import classification, concordance, survival_target
from loe_bench.t2 import _logit


ARMS = ("B1", "M1", "M3")
NOT_ESTIMABLE = "NOT_ESTIMABLE"
PRIVATE = Path("C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/score")
FROZEN_CONFIG_SHA256 = "d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39"
EXPORT_SHA256 = {
    12: "a644f1d40271c9a59a5405b840724906332ce975854d2afedd3d22c4ded80891",
    24: "c3b9e51891fd8f577dfce9f7fbbfb466f25f29ae50ed4edd9d8b2d0fcbcc84e7",
}
# Annual rosters and rounded Brier values from SCORE and the locked analysis note.
LAST_CUTOFF_YEAR = {12: 2025, 24: 2024}
PANEL_ROWS = {12: 5259, 24: 4639}
BRIER = {12: (0.0373, 0.0354, 0.0352), 24: (0.0713, 0.0654, 0.0647)}


def checked_bytes(path, expected, *, normalize_lf=False):
    raw = path.read_bytes()
    if normalize_lf:
        raw = raw.replace(b"\r\n", b"\n")
    if sha256(raw).hexdigest() != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}")
    return raw


def export_name(horizon):
    return f"C1_scores_{horizon}m.json"


def validate_panel(export, horizon, implementation_sha):
    if (
        export.get("status") != "AUTHORIZED_CPRIME"
        or type(export.get("prediction_horizon_months")) is not int
        or export["prediction_horizon_months"] != horizon
        or export.get("implementation_sha") != implementation_sha
        or export.get("frozen_config_sha256") != FROZEN_CONFIG_SHA256
    ):
        raise ValueError(f"Unexpected {horizon}m export metadata")

    rows = export.get("rows")
    if not isinstance(rows, list) or len(rows) != PANEL_ROWS[horizon]:
        raise ValueError(f"Unexpected {horizon}m export row count")
    expected_cutoffs = {date(year, 1, 1).isoformat() for year in range(2017, LAST_CUTOFF_YEAR[horizon] + 1)}
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or row.keys() != {"key", "cutoff", "y", *ARMS}:
            raise ValueError(f"Unexpected {horizon}m export row fields")
        key, cutoff, label = row["key"], row["cutoff"], row["y"]
        if not isinstance(key, str) or not key or not isinstance(cutoff, str) or cutoff not in expected_cutoffs:
            raise ValueError(f"Invalid {horizon}m export key or cutoff")
        if (key, cutoff) in seen:
            raise ValueError(f"Duplicate (key, cutoff) in {horizon}m export")
        seen.add((key, cutoff))
        if type(label) is not int or label not in (0, 1):
            raise ValueError(f"Nonbinary label in {horizon}m export")
        if any(type(row[arm]) not in (int, float) or not 0 <= row[arm] <= 1 for arm in ARMS):
            raise ValueError(f"Invalid native probability in {horizon}m export")
    if {cutoff for _, cutoff in seen} != expected_cutoffs:
        raise ValueError(f"Missing registered cutoff in {horizon}m export")
    return rows


def frozen_probabilities(scores, parameters):
    """Restore the published TRAIN sigmoid and use SCORE's clipped native logit."""
    model = Logistic(feats=("logit",))
    model.b = parameters["intercept"]
    model.mu = [parameters["mean"]]
    model.sd = [parameters["scale"]]
    model.w = [parameters["weight"]]
    return model.predict([{"x": {"logit": _logit(score)}} for score in scores])


def pooled_auc(scores, labels):
    value = auroc(scores, labels)
    return value if isfinite(value) else NOT_ESTIMABLE


def within_cutoff_c_index(scores, labels, cutoffs, horizon, event_dates=None):
    """Use exact event dates when available and censor other rows at the horizon."""
    if event_dates is None:
        return {"estimate": NOT_ESTIMABLE, "comparable_pairs": None}
    observed_times = [
        survival_target({"t": cutoff, "t_end": add_months(cutoff, horizon), "y": label}, event)[1]
        for cutoff, label, event in zip(cutoffs, labels, event_dates, strict=True)
    ]
    result = concordance(scores, labels, observed_times, [cutoff.toordinal() for cutoff in cutoffs])
    if result["estimate"] is None:
        result["estimate"] = NOT_ESTIMABLE
    return result


def summarize_panel(rows, horizon, arm_settings):
    labels = [row["y"] for row in rows]
    cutoffs = [date.fromisoformat(row["cutoff"]) for row in rows]
    arms = {}
    for arm, brier in zip(ARMS, BRIER[horizon], strict=True):
        scores = [row[arm] for row in rows]
        probabilities = frozen_probabilities(scores, arm_settings[arm]["calibrator"])
        arms[arm] = {
            "roc_auc": pooled_auc(scores, labels),
            **classification(probabilities, labels),
            "brier_from_score": brier,
            # The authenticated export schema has no exact event dates.
            "c_index": within_cutoff_c_index(scores, labels, cutoffs, horizon),
        }
    events = sum(labels)
    return {
        "rows": len(rows),
        "unique_drugs": len({row["key"] for row in rows}),
        "event_rows": events,
        "event_drugs": len({row["key"] for row in rows if row["y"]}),
        "prevalence": events / len(rows),
        "arms": arms,
    }


def run():
    config = json.loads(checked_bytes(ROOT / "data" / "FROZEN_CONFIG.json", FROZEN_CONFIG_SHA256,
                                      normalize_lf=True))
    # Authenticate both exports before decoding the same verified bytes.
    exports = {h: checked_bytes(PRIVATE / export_name(h), digest) for h, digest in EXPORT_SHA256.items()}
    panels = {h: validate_panel(json.loads(raw), h, config["code_commit_sha"]) for h, raw in exports.items()}
    return {
        "status": "POST_HOC_DESCRIPTIVE",
        "probability_threshold": 0.5,
        "frozen_config_sha256_lf": FROZEN_CONFIG_SHA256,
        "score_exports_sha256": {export_name(h): digest for h, digest in EXPORT_SHA256.items()},
        "c_index_unavailable_reason": "C1 score exports omit exact event dates",
        "horizons": {str(h): summarize_panel(rows, h, config["horizons"][str(h)]["arms"])
                     for h, rows in panels.items()},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write data/CPRIME_SUPPLEMENT.json")
    args = parser.parse_args()
    try:
        summary = json.dumps(run(), indent=2, allow_nan=False) + "\n"
        if args.write:
            (ROOT / "data" / "CPRIME_SUPPLEMENT.json").write_text(summary, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(summary)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
