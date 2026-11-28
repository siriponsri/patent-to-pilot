"""Summarize authenticated C′ exports and frozen development predictors."""

import argparse
from bisect import bisect_right
from collections import Counter
from datetime import date
import json
from math import fsum, isclose, sqrt
import os
import re
from statistics import stdev
import sys
from unittest.mock import patch

import score_cprime_supplement as supplement

from loe_bench import metrics, seal, t2
from loe_bench.baselines import AgeHazardTable
from loe_bench.t2_features import OB_FEATURES


DATA = supplement.ROOT / "data"
PRIVATE_ROOT = supplement.PRIVATE.parent
SCORE_SHA256 = "38f65240b57a4662349d3bdc89fd026908d888bdb2cfcb1ed63f430ed845d932"
DEVELOPMENT_COUNTS = {12: (547, 2161), 24: (547, 1083)}
BIN_EDGES = tuple(i / 10 for i in range(11))
QUANTILES = (5, 25, 50, 75, 95)
SMALL = "<5"
WITHHELD = "WITHHELD"
UNAVAILABLE = "UNAVAILABLE"
NUMERIC_MISSING = {
    **dict.fromkeys(("age_years", "age_sq", "n_nda_prior", t2.AGE_SIGNAL)),
    **{name: f"{name}_missing" for name in OB_FEATURES},
    "strength_count": "strength_missing",
    "form_route_count": "form_route_missing",
}


def count_cell(count):
    return SMALL if count < 5 else count


def wilson_95(events, rows):
    z = 1.959963984540054
    fraction = events / rows
    correction = z * z / rows
    center = fraction + correction / 2
    half_width = z * sqrt(fraction * (1 - fraction) / rows + correction / (4 * rows))
    return [(center - half_width) / (1 + correction), (center + half_width) / (1 + correction)]


def calibration_bins(probabilities, labels):
    bins = [[] for _ in range(10)]
    event_counts = [0] * 10
    for probability, label in zip(probabilities, labels, strict=True):
        index = bisect_right(BIN_EDGES[1:-1], probability)
        bins[index].append(probability)
        event_counts[index] += label

    hidden = {i for i, values in enumerate(bins) if values
              and min(event_counts[i], len(values) - event_counts[i]) < 5}
    if len(hidden) == 1:
        others = [i for i, values in enumerate(bins) if values and i not in hidden]
        if others:
            hidden.add(max(others, key=lambda i: (len(bins[i]), -i)))

    return [{
        "lower": BIN_EDGES[i],
        "upper": BIN_EDGES[i + 1],
        "upper_inclusive": i == 9,
        "rows": count_cell(len(values)),
        "events": WITHHELD if i in hidden and events >= 5 else count_cell(events),
        "mean_calibrated_probability": fsum(values) / len(values) if len(values) >= 5 else None,
        "observed_event_rate": events / len(values) if values and i not in hidden else None,
        "wilson_95": wilson_95(events, len(values)) if values and i not in hidden else None,
    } for i, (values, events) in enumerate(zip(bins, event_counts, strict=True))]


def numeric_summary(values, missing):
    count = len(values)
    if count >= 5:
        # Linear interpolation at index (n - 1) * q, using the observed values.
        ordered = sorted(values)
        quantiles = {}
        for percent in QUANTILES:
            index, remainder = divmod((count - 1) * percent, 100)
            low, high = ordered[index], ordered[index + 1]
            quantiles[str(percent)] = low + (high - low) * remainder / 100
        mean, sd = fsum(values) / count, stdev(values)
    else:
        mean, sd, quantiles = None, None, dict.fromkeys(map(str, QUANTILES))
    return {"count": count_cell(count), "missing": count_cell(missing),
            "mean": mean, "sd": sd, "quantiles": quantiles}


def binary_summary(ones, rows):
    return {"levels": {"0": count_cell(rows - ones), "1": count_cell(ones)}}


def cprime_predictors(rows, coverage, features):
    missing = sum((Counter(day["missing_features"]) for day in coverage), Counter())
    verdicts = sum((Counter(day["graph_verdict"]) for day in coverage), Counter())
    if sum(verdicts.values()) != len(rows):
        raise ValueError("SCORE graph counts do not reconcile")
    binary = {**{f"verdict_{name}": count for name, count in verdicts.items()},
              **{key: missing[key] for key in coverage[0]["missing_features"]}, "nme": len(rows)}
    summaries = {}
    for name in features:
        if name == t2.AGE_SIGNAL:
            summaries[name] = numeric_summary([t2._logit(row["B1"]) for row in rows], 0)
        elif name in binary:
            summaries[name] = binary_summary(binary[name], len(rows))
        elif name in NUMERIC_MISSING:
            indicator = NUMERIC_MISSING[name]
            absent = missing[indicator] if indicator is not None else 0
            summaries[name] = {
                "count": count_cell(len(rows) - absent), "missing": count_cell(absent),
                "mean": UNAVAILABLE, "sd": UNAVAILABLE,
                "quantiles": dict.fromkeys(map(str, QUANTILES), UNAVAILABLE),
            }
        else:
            summaries[name] = {"levels": dict.fromkeys(("0", "1"), UNAVAILABLE)}
    return summaries


def cprime_summary(rows, settings, score, features):
    labels = [row["y"] for row in rows]
    if len(rows) != score["rows"] or sum(labels) != score["event_rows"]:
        raise ValueError("SCORE overall rows or events do not reconcile")
    calibration = {}
    for arm in supplement.ARMS:
        probabilities = supplement.frozen_probabilities([row[arm] for row in rows],
                                                         settings[arm]["calibrator"])
        ece = metrics.ece(probabilities, labels)
        brier = metrics.brier(probabilities, labels)
        if (list(ece.bin_counts) != score["arms"][arm]["ece_bin_counts"]
                or not isclose(ece.ece, score["levels"][arm]["ece"]["estimate"],
                               rel_tol=0, abs_tol=1e-14)
                or not isclose(brier, score["levels"][arm]["brier"]["estimate"],
                               rel_tol=0, abs_tol=1e-14)):
            raise ValueError(f"SCORE calibration does not reconcile for {arm}")
        calibration[arm] = calibration_bins(probabilities, labels)

    coverage = list(score["eligibility_and_coverage"].values())
    flow = {key: sum(day[key] for day in coverage) for key in
            ("dated_nda_drugs", "no_eligible_type1", "prior_final_anda", "eligible_rows", "events")}
    flow["dated_type1_candidates"] = flow["dated_nda_drugs"] - flow["no_eligible_type1"]
    if (flow["dated_type1_candidates"] - flow["prior_final_anda"] != flow["eligible_rows"]
            or flow["eligible_rows"] != len(rows) or flow["events"] != sum(labels)):
        raise ValueError("SCORE eligibility flow does not reconcile")
    return {
        "calibration": calibration,
        "predictors": cprime_predictors(rows, coverage, features),
        "eligibility_flow": {**{key: count_cell(value) for key, value in flow.items()},
                             "prior_final_anda_before_nda": UNAVAILABLE,
                             "prior_final_anda_other": UNAVAILABLE},
    }


def development_predictors(input_rows, features):
    entries = [row["x"] for row in input_rows]
    summaries = {}
    for name in features:
        if name in NUMERIC_MISSING:
            indicator = NUMERIC_MISSING[name]
            values = [x[name] for x in entries if indicator is None or x[indicator] == 0]
            summaries[name] = numeric_summary(values, len(entries) - len(values))
        else:
            values = [x[name] for x in entries]
            if any(value not in (0, 1) for value in values):
                raise ValueError("Unexpected development indicator level")
            summaries[name] = binary_summary(int(sum(values)), len(entries))
    return summaries


def development_replay(config, features):
    # After registration the lock record exists. As in SCORE's guarded replay,
    # require absent authorization and use the development-only cutoff checks.
    if seal.ENV_NAME in os.environ:
        raise ValueError("Development replay requires disabled seal authorization")
    # Delay these imports so unit tests and export-only helpers do not touch source data.
    import e7_dev_run
    import t4_power

    # DEVX still imports the scanner names removed by the T4b merge. Restore
    # their original patterns during import only (T4, commit 7ef5e1ea).
    with patch.multiple(t4_power, create=True,
                        FLAGS=re.compile(rb'"submissions"\s*:\s*\['),
                        TOKEN=re.compile(rb'"(?:[^"\\]|\\.)*"|[\[\]{}]')):
        import devx_run as replay
        import t1v3_run
    from c3_dev_guard import nda_reader
    from t2_dev_run import _verify
    from loe_bench import devx
    from loe_bench.piv_history import EntityMatcher, PIVHistory

    refs = config["input_sha256"]
    manifests = {}
    for name in ("s0_manifest", "ob_manifest", "piv_manifest", "court_manifest"):
        ref = refs[name]
        manifests[name] = json.loads(supplement.checked_bytes(DATA / ref["file"], ref["sha256"],
                                                               normalize_lf=True))
    raw = PRIVATE_ROOT / "raw-20261127"
    ob_dir = PRIVATE_ROOT / "ob_editions"
    piv_dir = PRIVATE_ROOT / "piv"
    challenge_dir = PRIVATE_ROOT / "challenge"

    used = {day for pair in replay.PRIMARY.values() for days in pair for day in days}
    replay_dates = used | {day for pair in replay.FORWARD.values() for days in pair for day in days}
    t2.require_development_cutoffs(replay_dates)
    if replay.DEVELOPMENT_END != date(2016, 1, 1):
        raise ValueError("Development observation limit differs from the locked replay")
    piv = PIVHistory(DATA / refs["piv_manifest"]["file"], piv_dir, EntityMatcher([]))
    piv_editions = {edition for day in replay_dates if (edition := piv.edition_asof(day)) is not None}
    for edition in piv_editions:
        _verify(piv_dir / edition.file, edition.sha256)

    gsrs = refs["gsrs"]
    if gsrs != {"file": replay.moiety.GSRS_FILE, "sha256": replay.moiety.GSRS_SHA256}:
        raise ValueError("GSRS pin differs from guarded reader")
    decode = replay.read_jsonl

    def guarded(path):
        return nda_reader(path, decode, projector=t4_power, redact_dates=replay.without_later_approvals)

    with patch.object(replay, "read_jsonl", guarded), patch.object(e7_dev_run, "read_jsonl", guarded):
        entities, builder, provenance = replay.inputs(raw, ob_dir, piv_dir, challenge_dir)

    panels = {}
    for horizon, (train_days, val_days) in replay.PRIMARY.items():
        settings = config["horizons"][str(horizon)]
        t1v3_run.verify_windows(train_days, val_days, horizon)
        if (list(map(date.isoformat, train_days)) != settings["train_cutoffs"]
                or list(map(date.isoformat, val_days)) != settings["validation_cutoffs"]):
            raise ValueError("Development cutoffs differ from FREEZE")
        train = replay.partition(entities, builder, train_days, horizon, training=True)
        val = replay.partition(entities, builder, val_days, horizon)
        if (len(train), len(val)) != DEVELOPMENT_COUNTS[horizon] or len(train) != settings["train_rows"]:
            raise ValueError("Development counts differ from FREEZE and CLOSE-DISP")
        age = AgeHazardTable().fit(train)
        panels[str(horizon)] = {
            label: {
                "rows": len(rows),
                "features": development_predictors(
                    devx.model_inputs(rows, age.predict(rows), "M3", t1v3_run.FLAGS), features),
            } for label, rows in (("TRAIN", train), ("VAL", val))
        }

    court = manifests["court_manifest"]
    digests = {f"data/{refs[key]['file']}": refs[key]["sha256"] for key in manifests}
    digests.update({f"raw-20261127/{name}": digest for name, digest in provenance["s0_files"].items()})
    digests[f"moiety/{gsrs['file']}"] = gsrs["sha256"]
    for detail in provenance["orange_book_coverage"].values():
        source = detail["source"]
        if source:
            digests[f"ob_editions/{source['file']}"] = source["sha256"]
    for edition in piv_editions:
        digests[f"piv/{edition.file}"] = edition.sha256
    for source in (court["rai"], court["rai"]["metadata"], *court["corroborating_documents"].values()):
        digests[f"challenge/{source['file']}"] = source["sha256"]
    return panels, dict(sorted(digests.items()))


def run():
    config = json.loads(supplement.checked_bytes(DATA / "FROZEN_CONFIG.json",
                                                 supplement.FROZEN_CONFIG_SHA256, normalize_lf=True))
    score = json.loads(supplement.checked_bytes(DATA / "SCORE_CPRIME_RESULTS.json",
                                                SCORE_SHA256, normalize_lf=True))
    exports = {h: supplement.checked_bytes(supplement.PRIVATE / supplement.export_name(h), digest)
               for h, digest in supplement.EXPORT_SHA256.items()}
    features = tuple(dict.fromkeys(name for arm in supplement.ARMS for name in config["features"][arm]))
    horizons = {}
    for h, raw in exports.items():
        panel = supplement.validate_panel(json.loads(raw), h, config["code_commit_sha"])
        horizons[str(h)] = cprime_summary(panel, config["horizons"][str(h)]["arms"],
                                          score["horizons"][str(h)], features)
    try:
        development, development_digests = development_replay(config, features)
        development_status = "PASS"
    except (OSError, ValueError, RuntimeError, KeyError, TypeError):
        # Private parser exceptions can contain source values.
        development, development_digests = {}, {}
        development_status = UNAVAILABLE
    for horizon, result in horizons.items():
        result["predictors"] = {
            **development.get(horizon, dict.fromkeys(("TRAIN", "VAL"), UNAVAILABLE)),
            "CPRIME": {"rows": result["eligibility_flow"]["eligible_rows"],
                       "features": result["predictors"]},
        }
    return {
        "status": "POST_HOC_DESCRIPTIVE",
        "development_replay": development_status,
        "sha256": {
            "data/FROZEN_CONFIG.json": supplement.FROZEN_CONFIG_SHA256,
            "data/SCORE_CPRIME_RESULTS.json": SCORE_SHA256,
            **{f"score/{supplement.export_name(h)}": digest for h, digest in supplement.EXPORT_SHA256.items()},
            **development_digests,
        },
        "unavailable": {
            "cprime_predictors": "SCORE omits row-level values for features other than the native B1 logit.",
            "cprime_prior_anda_split": "The exports omit exclusions and SCORE pools the two prior-ANDA reasons.",
        },
        "horizons": horizons,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Write data/CPRIME_DESC.json")
    args = parser.parse_args()
    try:
        output = json.dumps(run(), indent=2, allow_nan=False) + "\n"
        if args.write:
            (DATA / "CPRIME_DESC.json").write_text(output, encoding="utf-8", newline="\n")
        else:
            sys.stdout.write(output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"CPRIME-DESC failed: {error}\n")


if __name__ == "__main__":
    main()
