"""Fit a development-only simulator and estimate criteria v2 operating characteristics."""
import argparse
import hashlib
import json
import math
import os
import platform
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from datetime import date
from pathlib import Path
from unittest.mock import patch

# The small bootstrap products run concurrently across scenarios.
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loe_bench import dataset, evidence_graph as graph, moiety, power, t2
from loe_bench import ob_linkage
from loe_bench.baselines import AgeHazardTable, Logistic
from loe_bench.common import add_months, read_jsonl, years_between
from loe_bench.ob_history import DEFAULT_DIR, OBHistory
from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.seal import TEST_FIRST
from loe_bench.t2_features import AsOfBuilder, MODEL_FEATURES, edition_coverage
from t2_dev_run import _manifest, _verify

HORIZONS = (24, 12)
DEV_FIRST = date(2010, 1, 1)
DEV_LAST_EVENT = date(2016, 1, 1)
SEED = 20261127
TARGET_TOLERANCE = 0.0006
REPETITIONS = 5000
DRAWS = 120
CHECK_REPETITIONS = 400
CALIBRATION_MULTIPLIER = 36
VERIFICATION_MULTIPLIER = 80
FLAGS = re.compile(rb'"submissions"\s*:\s*\[')
# Walk JSON delimiters while treating quoted strings as opaque bytes.
TOKEN = re.compile(rb'"(?:[^"\\]|\\.)*"|[\[\]{}]')
DEV_DATE = re.compile(rb'"submission_status_date"\s*:\s*"((?:19\d\d|20(?:0\d|1[0-5]))\d{4}|20160101)"')
ORIGINAL = re.compile(rb'"submission_type"\s*:\s*"ORIG"')
APPROVED = re.compile(rb'"submission_status"\s*:\s*"AP"')


def project_development_anda(line):
    """Decode application identity and only the approved development dates.

    The pinned JSONL is a mixed-period public source. No submission object
    from this file is decoded. The only date payload admitted to Python data
    is a matched development ORIG/AP date, at or before DEV_LAST_EVENT.
    """
    field = FLAGS.search(line)
    if field is None:
        return None
    depth = 1
    dates = []
    for token in TOKEN.finditer(line, field.end()):
        mark = token.group()
        if mark in (b"{", b"["):
            if depth == 1:
                start = token.start()
            depth += 1
        elif mark in (b"}", b"]"):
            depth -= 1
            if depth == 1:
                submission = line[start:token.end()]
                match = DEV_DATE.search(submission)
                if match and ORIGINAL.search(submission) and APPROVED.search(submission):
                    dates.append(match[1].decode("ascii"))
            if depth == 0:
                if not dates:
                    return None
                record = json.loads(line[:field.end()] + line[token.start():])
                record["submissions"] = [{"submission_type": "ORIG", "submission_status": "AP",
                                          "submission_status_date": min(dates)}]
                return record
    raise ValueError("Unterminated submissions array in the pinned ANDA source")


def projected_reader(development):
    def projected(path):
        name = Path(path).name
        if name == "df_anda.jsonl" and development:
            with Path(path).open("rb") as source:
                for line in source:
                    record = project_development_anda(line)
                    if record is not None:
                        yield record
        elif name == "df_nda.jsonl":
            yield from read_jsonl(path)
        elif name != "df_anda.jsonl":
            raise ValueError(f"Unexpected projected input: {name}")

    return projected


def build_projected_entities(raw, gsrs, *, development):
    """Use FIX2b's moiety algorithm with separate feature and event input roles."""
    with (patch.object(dataset, "read_jsonl", projected_reader(development)),
          patch.object(moiety, "ORANGE_FILES", ("ob_nda.jsonl",))):
        return dataset.build_entities(raw, gsrs_path=gsrs)


def candidate_counts(entities, data_end):
    """Read only dated NDA/NME features. Emit aggregate horizon and cutoff sizes."""
    result = {}
    for horizon in HORIZONS:
        by_cutoff, union = {}, set()
        for year in range(TEST_FIRST.year, data_end.year + 1):
            cutoff = date(year, 1, 1)
            if add_months(cutoff, horizon) > data_end:
                continue
            keys = {key for key, item in entities.items()
                    if item.nda_first is not None and item.nda_first <= cutoff and item.flag_at("nme", cutoff)}
            by_cutoff[cutoff.isoformat()] = {"rows": len(keys), "drug_clusters": len(keys)}
            union.update(keys)
        result[str(horizon)] = {"by_cutoff": by_cutoff, "drug_clusters": len(union),
                                "rows": sum(c["rows"] for c in by_cutoff.values())}
    return result


def development_predictions(train, validation, horizon):
    """Replay the T2b selection and action rules on projected development rows."""
    t2.require_development_cutoffs(row["t"] for row in (*train, *validation))
    age = AgeHazardTable().fit(train)
    train_age = age.predict(train)
    val_age = age.predict(validation)
    features = (MODEL_FEATURES + (t2.AGE_SIGNAL,),
                MODEL_FEATURES + (t2.AGE_SIGNAL,) + t2.VERDICT_FEATURES)
    train_x = [t2._with_labels(t2._inputs(train, train_age, verdict), train) for verdict in (False, True)]
    val_x = [t2._inputs(validation, val_age, verdict) for verdict in (False, True)]
    candidates = defaultdict(list)
    labels = [row["y"] for row in validation]
    for l2 in t2.L2_GRID:
        m1, m3 = [Logistic(l2=l2, feats=features[i]).fit(train_x[i]).predict(val_x[i]) for i in range(2)]
        calibrated = t2._cross_calibrate(validation, m1, m3)
        for arm in ("M1", "M3"):
            candidate = calibrated[arm]
            candidates[arm].append((t2.brier(candidate, labels), l2, candidate))
    m1, m3 = (min(candidates[arm], key=lambda item: item[:2])[2] for arm in ("M1", "M3"))
    p = (
        [t2.Prediction(x, graph.PREDICT_ENTRY if x >= 0.5 else graph.PREDICT_NO_ENTRY) for x in val_age],
        [t2.Prediction(x, t2._flat_action(x)) for x in m1],
        [t2.Prediction(x, graph.decide(row["asof"].snapshot, row["t"], horizon, x,
                                      lo=t2.LO, hi=t2.HI)["action"])
         for row, x in zip(validation, m3, strict=True)],
    )
    return p


def fit_confidence(validation, predictions, edges):
    age_band = np.searchsorted(edges, [row["x"]["age_years"] for row in validation])
    labels = np.asarray([row["y"] for row in validation], dtype=bool)
    actions = np.asarray([[item.action for item in arm] for arm in predictions]).T
    scores = np.asarray([[item.score for item in arm] for arm in predictions]).T
    # Midranks preserve the large age-clock tie groups during correlation fit.
    ranks = np.empty_like(scores)
    tie_sizes = []
    for i, column in enumerate(scores.T):
        _, index, count = np.unique(column, return_inverse=True, return_counts=True)
        ranks[:, i] = (np.cumsum(count) - count / 2)[index] / len(column)
        tie_sizes.append(int(count.max()))
    standardized = (ranks - ranks.mean(axis=0)) / ranks.std(axis=0)
    means = np.array([standardized[age_band == j].mean() if np.any(age_band == j) else 0.
                      for j in range(len(edges) + 1)])
    residual = standardized - means[age_band, None]
    shift = residual[~labels].mean(axis=0) - residual[labels].mean(axis=0)
    residual += labels[:, None] * shift
    scale = max(float(residual.std()), 0.05)
    means /= scale
    skill = float(np.mean(shift) / scale)
    corr = np.corrcoef(residual.T)
    # Mild diagonal shrinkage keeps correlated arms simulatable under Cholesky.
    corr = 0.98 * corr + 0.02 * np.eye(3)
    by_key = defaultdict(list)
    for i, row in enumerate(validation):
        by_key[row["key"]].append(i)
    left, right = [], []
    for indices in by_key.values():
        left.extend(indices[:-1])
        right.extend(indices[1:])
    rho = float(np.clip(np.corrcoef(residual[left].ravel(), residual[right].ravel())[0, 1], 0, 0.98))
    abstention = (actions == graph.ABSTAIN).mean(axis=0)[1:]
    call_entry = [(actions[labels == value] == graph.PREDICT_ENTRY).mean() for value in (False, True)]
    return means, skill, corr, rho, abstention, call_entry, tie_sizes


def history_templates(entities):
    cutoffs = [date(year, 1, 1) for year in range(DEV_FIRST.year, DEV_LAST_EVENT.year)]
    rows = dataset.build_samples(entities, cutoffs, 12, DEV_LAST_EVENT)
    first_by_key = {}
    for row in rows:
        first_by_key.setdefault(row["key"], row)
    events, non_events = [], []
    for key, start in first_by_key.items():
        when = entities[key].anda_first
        age = start["x"]["age_years"]
        index = start["t"].year - DEV_FIRST.year
        if when is None:
            non_events.append((age, index, 0))
        elif not start["t"] < when <= DEV_LAST_EVENT:
            raise ValueError("Unadmitted event in development history")
        else:
            lag = when.year - start["t"].year + (when > date(when.year, 1, 1))
            events.append((age, index, lag))
    arrivals = [record for record in non_events if record[1] == len(cutoffs) - 1]
    return np.asarray(non_events), np.asarray(events), np.asarray(arrivals), len(cutoffs)


def prepare(raw, ob_dir, ob_manifest, gsrs):
    manifest, s0_ref = _manifest(ROOT / "data" / "S0_INPUT_MANIFEST.json")
    data_end = date.fromisoformat(manifest["t0"])
    raw_hashes = {item["raw_file"]: item["sha256"] for item in manifest["files"]
                  if item["raw_file"] in {"df_nda.jsonl", "df_anda.jsonl", "ob_nda.jsonl"}}
    for name, digest in raw_hashes.items():
        _verify(raw / name, digest)
    _verify(gsrs, moiety.GSRS_SHA256)
    counts = candidate_counts(build_projected_entities(raw, gsrs, development=False), data_end)
    entities = build_projected_entities(raw, gsrs, development=True)
    ob_records, ob_ref = _manifest(ob_manifest)
    history = OBHistory.from_records(ob_records, str(ob_dir))
    with (patch.object(moiety, "ORANGE_FILES", ("ob_nda.jsonl",)),
          patch.object(ob_linkage, "read_jsonl", projected_reader(True))):
        linker = HistoricalMoietyLinker(raw, entities, gsrs_path=gsrs)
    builder = AsOfBuilder(history, key_mode="moiety", linker=linker)
    editions = {}
    audits = {}
    fitted = []
    edges = np.array([5, 10, 15, 25, 40])
    for horizon in HORIZONS:
        partitions = []
        for cutoffs in t2.development_split(horizon):
            t2.require_development_cutoffs(cutoffs)
            if any(add_months(cutoff, horizon) > DEV_LAST_EVENT for cutoff in cutoffs):
                raise ValueError("Development horizon crosses the admitted event endpoint")
            for cutoff in cutoffs:
                selected = edition_coverage(history, cutoff)["source"]
                if selected and selected["sha256"] not in editions:
                    _verify(ob_dir / selected["file"], selected["sha256"])
                    editions[selected["sha256"]] = selected
            rows = dataset.build_samples(entities, cutoffs, horizon, DEV_LAST_EVENT)
            for row in rows:
                row["asof"] = builder.build(row["key"], row["t"], horizon, row["x"])
            partitions.append(rows)
        train, validation = partitions
        predictions = development_predictions(train, validation, horizon)
        fit = fit_confidence(validation, predictions, edges)
        fitted.append(fit[:-1])
        audits[str(horizon)] = {
            "train_rows": len(train), "validation_rows": len(validation),
            "cutoff_rows": {d.isoformat(): sum(row["t"] == d for row in train + validation)
                            for split in t2.development_split(horizon) for d in split},
            "drug_clusters": len({row["key"] for row in validation}),
            "event_clusters": len({row["key"] for row in validation if row["y"]}),
            "event_rows": sum(row["y"] for row in validation),
            "validation_aurc80": [t2._aurc80(arm, [row["y"] for row in validation]) for arm in predictions],
            "largest_confidence_tie": fit[-1],
        }
    templates = history_templates(entities)
    profile = power.Profile(*templates, edges, *(np.asarray(value) for value in zip(*fitted)))
    audit = {
        "data_end": data_end.isoformat(), "last_admitted_development_event": DEV_LAST_EVENT.isoformat(),
        "input_sha256": {"s0_manifest": s0_ref, "ob_manifest": ob_ref, "raw": raw_hashes,
                         "gsrs": {"file": gsrs.name, "sha256": moiety.GSRS_SHA256},
                         "used_development_editions": list(editions.values())},
        "candidate_frame": counts, "development": audits,
        "generator": {
            "history_cutoffs": templates[-1],
            "non_event_templates": len(templates[0]), "event_templates": len(templates[1]),
            "extra_arrival_templates": len(templates[2]),
            "event_lag_histogram": np.bincount(templates[1][:, 2].astype(int)).tolist(),
            "age_edges": edges.tolist(), "age_confidence_weights": profile.age_means.tolist(),
            "error_ranking_skill": profile.skill.tolist(), "latent_correlation": profile.arm_correlations.tolist(),
            "within_drug_residual_correlation": profile.cluster_correlation.tolist(),
            "m1_m3_abstention": profile.abstention.tolist(), "common_call_entry_by_outcome": profile.call_entry.tolist(),
        },
    }
    return profile, audit


def scenario_grid(counts):
    main = counts["24"]["drug_clusters"]
    extra = counts["12"]["drug_clusters"] - main
    years = len(counts["24"]["by_cutoff"])
    rows = [power.Scenario(f"events_{events}", main, extra, years, events) for events in (30, 50, 75, 100, 150)]
    rows.extend((
        power.Scenario("drift_minus_30pct", main, extra, years, 53),
        power.Scenario("drift_plus_30pct", main, extra, years, 97),
        power.Scenario("young", main, extra, years, 75, young=True),
        power.Scenario("low_correlation", main, extra, years, 75, correlation=0.25),
        power.Scenario("high_correlation", main, extra, years, 75, correlation=0.90),
        power.Scenario("near_coverage_gate", main, extra, years, 75, coverage_stress=True),
    ))
    return rows


def pass_targets(population, expected):
    return [bool(math.isfinite(x) and abs(x - y) <= TARGET_TOLERANCE)
            for x, y in zip(population["delta"], expected, strict=True)]


def run_scenario(profile, scenario, sequence, repetitions, draws, check_repetitions,
                 calibration_multiplier, verification_multiplier):
    from dataclasses import asdict

    rng_cal, rng_verify, rng_run = (np.random.default_rng(seed) for seed in sequence.spawn(3))
    settings = power.calibration(profile, scenario, rng_cal, calibration_multiplier)
    configurations = {"null": (0., 0., 0.), "useful": (-power.EFFECT,) * 3}
    if scenario.name == "events_75":
        configurations.update(H2_null=(-power.EFFECT, 0., -power.EFFECT),
                              H3_null=(-power.EFFECT, -power.EFFECT, 0.))
    results = {}
    for name, target in configurations.items():
        useful_supported = all(setting["useful_skill"] is not None for setting in settings)
        if not useful_supported and name != "null":
            results[name] = {"status": "UNATTAINABLE", "target": target}
            continue
        population = power.verify_population(profile, scenario, settings,
                                             np.random.default_rng(rng_verify.integers(2**63)),
                                             verification_multiplier, name)
        operation = power.simulate(
            profile, scenario, settings, int(rng_run.integers(2**63)), repetitions, draws, name,
            check_repetitions if scenario.name == "events_75" and name in ("null", "useful") else 0,
        )
        verified = pass_targets(population, target)
        results[name] = {"status": "PASS" if all(verified) else "TARGET_CHECK_FAILED",
                         "target": target, "target_verified": verified, "population": population,
                         "operating_characteristics": operation}
    result = {"scenario": asdict(scenario), "calibration": settings, "results": results}
    print(f"{scenario.name} complete", flush=True)
    return result


def clean_json(value):
    if isinstance(value, dict):
        return {k: clean_json(x) for k, x in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean_json(x) for x in value]
    if isinstance(value, np.generic):
        return clean_json(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--gsrs", type=Path)
    parser.add_argument("--ob-dir", type=Path, default=Path(DEFAULT_DIR))
    parser.add_argument("--ob-manifest", type=Path, default=ROOT / "data" / "OB_EDITIONS.json")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    start = time.perf_counter()
    gsrs = args.gsrs or args.raw.resolve().parent / "moiety" / moiety.GSRS_FILE
    profile, audit = prepare(args.raw, args.ob_dir, args.ob_manifest, gsrs)
    if args.prepare_only:
        print(json.dumps(clean_json(audit), indent=2, allow_nan=False))
        return
    print("Development fit and candidate-frame counts complete.", flush=True)
    scenarios = scenario_grid(audit["candidate_frame"])
    seeds = np.random.SeedSequence(SEED).spawn(len(scenarios))
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs = [pool.submit(run_scenario, profile, scenario, seed, REPETITIONS, DRAWS, CHECK_REPETITIONS,
                            CALIBRATION_MULTIPLIER, VERIFICATION_MULTIPLIER)
                for scenario, seed in zip(scenarios, seeds, strict=True)]
        results = [job.result() for job in jobs]
    grid = [result for result in results if result["scenario"]["name"].startswith("events_")]
    qualifying = [result["scenario"]["event_clusters"] for result in grid
                  if result["results"]["useful"]["status"] == "PASS" and
                  result["results"]["useful"]["operating_characteristics"]["rates"]["H1"]["overall"]["rate"] >= 0.8]
    output = ROOT / "data" / "T4_power.json"
    result = {
        "scope": "development-calibrated synthetic data and feature-only candidate counts",
        "seed": SEED, "alpha": power.ALPHA, "common_coverage": power.COVERAGE,
        "arm_order": ["B1", "M1", "M3"], "horizon_order": HORIZONS, "contrast_order": power.CONTRASTS,
        "calibration_multiplier": CALIBRATION_MULTIPLIER, "verification_multiplier": VERIFICATION_MULTIPLIER,
        "target_tolerance": TARGET_TOLERANCE, "minimum_grid_event_clusters_at_80pct_H1": min(qualifying, default=None),
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "workers": args.workers,
                    "elapsed_seconds": round(time.perf_counter() - start, 1)},
        "seal_sha256": hashlib.sha256((ROOT / "loe_bench" / "seal.py").read_bytes()).hexdigest(),
        **audit, "scenarios": results,
    }
    output.write_text(json.dumps(clean_json(result), sort_keys=True, indent=2, allow_nan=False) + "\n",
                      encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
