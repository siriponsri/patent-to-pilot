"""Fit a development-only simulator and estimate criteria v2 operating characteristics."""
import argparse
import hashlib
import json
import math
import os
import platform
import re
import random
import sys
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import date
from itertools import product
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
from loe_bench import seal
from loe_bench.challenge import ChallengeEvidence, Witness
from loe_bench.common import add_months
from loe_bench.kleene import T3
from loe_bench.ob_history import DEFAULT_DIR, OBHistory
from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.seal import TEST_FIRST
from loe_bench.t2_features import AsOfBuilder, edition_coverage
from t2_dev_run import _manifest, _verify

HORIZONS = (24, 12)
DEV_FIRST = date(2010, 1, 1)
DEV_LAST_EVENT = date(2016, 1, 1)
SEED = 20261127
TARGET_TOLERANCE = 0.0006
REPETITIONS = 5000
DRAWS = 199
CHECK_REPETITIONS = 800
FULL_DRAWS = 2000
NULL_REPETITIONS = 12000
NULL_BATCH = 1000
CALIBRATION_MULTIPLIER = 36
VERIFICATION_MULTIPLIER = 80
OB_DEVELOPMENT = ("ob_anda_pre1982.jsonl", "ob_anda_to2009.jsonl", "ob_anda_2010s.jsonl")
JSON_TOKEN = re.compile(rb'"(?:[^"\\]|\\.)*"|[{}\[\],:]|[^\s{}\[\],:"]+')


def composite_items(payload):
    """Slice immediate JSON members as bytes, without decoding their values."""
    tokens = iter(JSON_TOKEN.finditer(payload))
    opening = next(tokens).group()
    if opening not in (b"{", b"["):
        raise ValueError("Expected a JSON object or array")
    closing = b"}" if opening == b"{" else b"]"
    item = next(tokens)
    while item.group() != closing:
        key = None
        if opening == b"{":
            key = item.group()[1:-1]
            if next(tokens).group() != b":":
                raise ValueError("Expected a JSON member separator")
            item = next(tokens)
        start = item.start()
        depth = int(item.group() in (b"{", b"["))
        while depth:
            item = next(tokens)
            depth += (item.group() in (b"{", b"[")) - (item.group() in (b"}", b"]"))
        yield key, payload[start:item.end()]
        item = next(tokens)
        if item.group() == b",":
            item = next(tokens)
        elif item.group() != closing:
            raise ValueError("Expected a JSON value separator")


def approved_by(value, *, undated=False):
    if value in (None, b"null"):
        return undated
    return bool(re.fullmatch(rb'"\d{8}"', value) and value <= b'"20160101"')


def select_members(fields, allowed):
    return b"{" + b",".join(b'"' + key + b'":' + value for key, value in fields.items()
                             if key in allowed) + b"}"


def projected_annotation(value):
    if value is None or value == b"null":
        return b"null"
    return select_members(dict(composite_items(value)), {b"unii", b"substance_name", b"brand_name", b"spl_id"})


def projected_product(fields, allowed):
    if b"openfda" in fields:
        fields[b"openfda"] = projected_annotation(fields[b"openfda"])
    return select_members(fields, allowed | {b"active_ingredients", b"brand_name", b"openfda",
                                              b"product_number", b"approval_date"})


def project_development_anda(line):
    """Admit only a development original approval and its compatible ingredient evidence."""
    fields = dict(composite_items(line))
    app = fields.get(b"application_number", b"")
    if not re.fullmatch(rb'"ANDA\d+"', app):
        return None
    dates = []
    for _, raw in composite_items(fields.get(b"submissions", b"[]")):
        submission = dict(composite_items(raw))
        when = submission.get(b"submission_status_date")
        if (approved_by(when) and submission.get(b"submission_type") == b'"ORIG"'
                and submission.get(b"submission_status") == b'"AP"'):
            dates.append(when)
    if not dates:
        return None
    first = min(dates)
    products = []
    for _, raw in composite_items(fields.get(b"products", b"[]")):
        product = dict(composite_items(raw))
        when = product.get(b"approval_date")
        if approved_by(when, undated=True) and (when in (None, b"null") or when <= first):
            products.append(projected_product(product, set()))
    payload = {
        b"application_number": app, b"openfda": projected_annotation(fields.get(b"openfda")),
        b"products": b"[" + b",".join(products) + b"]",
        b"submissions": b'[{"submission_type":"ORIG","submission_status":"AP",'
                        b'"submission_status_date":' + first + b"}]",
    }
    return json.loads(select_members(payload, payload))


def project_orange(line, *, nda):
    """Gate Orange Book products individually, including grouped source rows."""
    fields = dict(composite_items(line))
    products = []
    for _, raw in composite_items(fields.get(b"products", b"[]")):
        product = dict(composite_items(raw))
        if product.get(b"application_type") != (b'"N"' if nda else b'"A"'):
            continue
        when = product.get(b"approval_date")
        if when in (None, b"null", b'""'):
            when = fields.get(b"approval_date")
        prior = product.get(b"approved_prior_to_1982") == b"true" or fields.get(
            b"approved_prior_to_1982") == b"true"
        if nda or approved_by(when, undated=prior):
            if when not in (None, b"null"):
                product[b"approval_date"] = when
            products.append(projected_product(product, {b"application_type", b"application_number"}))
    if not products:
        return None
    fields = {b"products": b"[" + b",".join(products) + b"]",
              b"product_number": fields.get(b"product_number", b"null")}
    return json.loads(select_members(fields, fields))


def projected_reader(development):
    cache = {}

    def projected(path):
        path = Path(path)
        name = path.name
        if name == "df_anda.jsonl" or name in OB_DEVELOPMENT:
            if not development:
                return
        elif name not in {"df_nda.jsonl", "ob_nda.jsonl"}:
            raise ValueError(f"Unexpected projected input: {name}")
        if path not in cache:
            records = []
            with path.open("rb") as source:
                for line in source:
                    if name == "df_nda.jsonl":
                        app = dict(composite_items(line)).get(b"application_number", b"")
                        record = json.loads(line) if re.fullmatch(rb'"NDA\d+"', app) else None
                    elif name == "df_anda.jsonl":
                        record = project_development_anda(line)
                    else:
                        record = project_orange(line, nda=name == "ob_nda.jsonl")
                    if record is not None:
                        records.append(record)
            cache[path] = records
        yield from cache[path]

    return projected


def build_projected_entities(raw, gsrs, *, development):
    """Use FIX2b's moiety algorithm with separate feature and event input roles."""
    reader = projected_reader(development)
    with (patch.object(dataset, "read_jsonl", reader),
          patch.object(moiety, "read_jsonl", reader),
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


def capture_e7b(raw, ob_dir):
    """Replay E7b's admitted development witnesses and exact matched model pipeline."""
    captured = {}
    evaluate = t2.evaluate

    def capture(train, validation, horizon, **kwargs):
        arm_pairs = []

        def collect(metric, left, right, labels, groups, **_options):
            arm_pairs.append((left, right))
            return 0., 0., 0

        with patch.object(t2, "paired_cluster_bootstrap_ci", collect):
            summary = evaluate(train, validation, horizon, **kwargs)
        m3, m1 = arm_pairs[0]
        b1 = arm_pairs[1][1]
        captured[horizon] = (validation, (b1, m1, m3))
        return summary

    s0, s0_ref = _manifest(ROOT / "data/S0_INPUT_MANIFEST.json")
    ob, ob_ref = _manifest(ROOT / "data/OB_EDITIONS.json")
    e7b, e7b_ref = _manifest(ROOT / "data/E7b_dev_summary.json")
    secondary, secondary_ref = _manifest(ROOT / "data/E7_witnesses.json")
    patents, patents_ref = _manifest(ROOT / "data/E7b_patent_witnesses.json")
    verified_files = ("df_nda.jsonl", "df_anda.jsonl", "ob_nda.jsonl", *OB_DEVELOPMENT)
    raw_hashes = {item["raw_file"]: item["sha256"] for item in s0["files"]}
    for name in verified_files:
        _verify(raw / name, raw_hashes[name])
    gsrs = raw.resolve().parent / "moiety" / moiety.GSRS_FILE
    _verify(gsrs, moiety.GSRS_SHA256)
    reader = projected_reader(True)
    with (patch.object(dataset, "read_jsonl", reader),
          patch.object(ob_linkage, "read_jsonl", reader),
          patch.object(moiety, "read_jsonl", reader),
          patch.object(moiety, "ORANGE_FILES", ("ob_nda.jsonl", *OB_DEVELOPMENT))):
        entities = dataset.build_entities(raw, gsrs_path=gsrs)
        linker = HistoricalMoietyLinker(raw, entities, gsrs_path=gsrs)
    history = OBHistory.from_records(ob, str(ob_dir))
    by_cutoff = {}
    used_editions = {}
    for cutoff in t2.DEVELOPMENT_CUTOFFS:
        tag = cutoff.isoformat()
        witnesses = defaultdict(list)
        for records in (secondary[tag], patents):
            for key, entries in records.items():
                for entry in entries:
                    when = date.fromisoformat(entry["date"])
                    if when <= cutoff:
                        witnesses[linker.canonical(key)].append(Witness(**dict(entry, date=when)))
        fresh = e7b["source_linkage_by_cutoff"][tag]["FDA_PIV"]["status"] == "FRESH"
        by_cutoff[cutoff] = (witnesses, T3.FALSE if fresh else T3.UNKNOWN)
        selected = edition_coverage(history, cutoff)["source"]
        if selected and selected["sha256"] not in used_editions:
            _verify(ob_dir / selected["file"], selected["sha256"])
            used_editions[selected["sha256"]] = selected

    class FrozenChallenge:
        def lookup(self, key, cutoff):
            witnesses, default = by_cutoff[cutoff]
            found = tuple(witnesses.get(key, ()))
            return ChallengeEvidence(T3.TRUE if found else default, found)

    builder = AsOfBuilder(history, linker=linker, challenge=FrozenChallenge())
    summary = {"horizons": {}, "input_sha256": {
        "s0_manifest": s0_ref, "s0_files": {name: raw_hashes[name] for name in verified_files},
        "ob_manifest": ob_ref, "used_development_editions": list(used_editions.values()),
        "gsrs": {"file": gsrs.name, "sha256": moiety.GSRS_SHA256},
        "e7b_summary": e7b_ref, "secondary_witnesses": secondary_ref, "patent_witnesses": patents_ref,
    }}
    for horizon in HORIZONS:
        partitions = []
        train_dates, validation_dates = t2.development_split(horizon)
        for dates in (train_dates, validation_dates):
            t2.require_development_cutoffs(dates)
            rows = dataset.build_samples(entities, dates, horizon, DEV_LAST_EVENT)
            for row in rows:
                row["asof"] = builder.build(row["key"], row["t"], horizon, row["x"])
            partitions.append(rows)
        train, validation = partitions
        summary["horizons"][str(horizon)] = {
            "train_rows": len(train), "validation_cutoffs": [d.isoformat() for d in validation_dates],
            **capture(train, validation, horizon, with_challenge=True),
        }
    return summary, captured, entities


def empirical_bootstrap(validation, predictions):
    """Recreate E7b's Python Random stream and return the paired draw matrix."""
    id_by_key = {}
    ids, labels = [], []
    for row in validation:
        ids.append(id_by_key.setdefault(row["key"], len(id_by_key)))
        labels.append(row["y"])
    arms = []
    for arm in predictions:
        arms.append((np.asarray([p.score for p in arm]),
                     np.asarray([p.action != graph.ABSTAIN for p in arm]),
                     np.asarray([(p.action == graph.PREDICT_ENTRY) != bool(y)
                                 for p, y in zip(arm, labels, strict=True)])))
    rng = random.Random(t2.BOOTSTRAP_SEED)
    clusters = len(id_by_key)
    sampled = np.empty((t2.BOOTSTRAP_DRAWS, clusters), dtype=np.float32)
    for draw in sampled:
        draw[:] = np.bincount([rng.randrange(clusters) for _ in range(clusters)], minlength=clusters)
    batches = [power.empirical_areas(ids, labels, arms, sampled[i:i + 128])
               for i in range(0, len(sampled), 128)]
    return power.paired_differences(np.concatenate(batches))


def prepare_e7b(raw, ob_dir):
    summary, captured, entities = capture_e7b(raw, ob_dir)
    reference, ref = _manifest(ROOT / "data" / "E7b_dev_summary.json")
    audits, empirical = {}, {}
    for horizon in HORIZONS:
        tag = str(horizon)
        validation, predictions = captured[horizon]
        paired = empirical_bootstrap(validation, predictions)
        empirical[horizon] = paired
        checks = {}
        for i, name in enumerate(power.PAIR_NAMES):
            draws = np.sort(paired[np.isfinite(paired[:, i]), i])
            ci = draws[[int(.025 * len(draws)), int(.975 * len(draws))]].tolist()
            original = reference["horizons"][tag]["paired_aurc80"][name]
            projected = summary["horizons"][tag]["paired_aurc80"][name]
            checks[name] = {"sd": float(draws.std(ddof=1)), "ci95": ci, "valid_draws": len(draws),
                            "delta": projected["delta"], "e7b_delta": original["delta"],
                            "e7b_ci95": original["ci95"]}
        audits[tag] = {"structure": {field: summary["horizons"][tag][field] for field in (
            "train_rows", "validation_rows", "validation_drug_clusters", "validation_event_clusters",
            "validation_cutoffs", "validation_verdicts")},
            "event_rows": sum(row["y"] for row in validation),
            "rows_by_cutoff": {d: sum(row["t"].isoformat() == d for row in validation)
                               for d in summary["horizons"][tag]["validation_cutoffs"]},
            "event_rows_by_cutoff": {d: sum(row["y"] for row in validation if row["t"].isoformat() == d)
                                     for d in summary["horizons"][tag]["validation_cutoffs"]},
            "arms": {name: {key: metrics[key] for key in ("aurc80", "coverage")}
                     for name, metrics in summary["horizons"][tag]["arms"].items()},
            "empirical": checks}
    audit = {"development": audits, "e7b_reference": ref, "development_input_sha256": summary["input_sha256"]}
    return captured, empirical, audit, entities


def prepare_generator(raw, captured, entities):
    manifest, _ = _manifest(ROOT / "data" / "S0_INPUT_MANIFEST.json")
    gsrs = raw.resolve().parent / "moiety" / moiety.GSRS_FILE
    counts = candidate_counts(build_projected_entities(raw, gsrs, development=False),
                              date.fromisoformat(manifest["t0"]))
    edges = np.array([5, 10, 15, 25, 40])
    fitted, panels, targets = [], [], []
    for horizon in HORIZONS:
        validation, predictions = captured[horizon]
        fit = fit_confidence(validation, predictions, edges)
        fitted.append(fit)
        ids = {}
        labels = np.array([row["y"] for row in validation], dtype=bool)
        panels.append((np.asarray([ids.setdefault(row["key"], len(ids)) for row in validation]),
                       np.searchsorted(edges, [row["x"]["age_years"] for row in validation]), labels))
        targets.append([t2._aurc80(arm, labels) for arm in predictions])
    profile = power.Profile(*history_templates(entities), edges,
                            *(np.asarray(value) for value in zip(*(fit[:-1] for fit in fitted), strict=True)),
                            event_score_scale=np.ones(2))
    return profile, counts, panels, targets, fitted


def noise_profile(profile, h, b1_corr, pair_corr, scale, cluster_corr):
    arm_corr = profile.arm_correlations.copy()
    arm_corr[h] = [[1, b1_corr, b1_corr], [b1_corr, 1, pair_corr], [b1_corr, pair_corr, 1]]
    scales = profile.event_score_scale.copy()
    scales[h] = scale
    within = profile.cluster_correlation.copy()
    within[h] = cluster_corr
    return replace(profile, arm_correlations=arm_corr, event_score_scale=scales, cluster_correlation=within)


def fit_validation(profile, h, panel, targets, empirical):
    """Separate calibration, parameter selection and verification streams."""
    n = len(panel[0])
    baseline = np.asarray([np.nanstd(v, ddof=1) for v in empirical.T])
    population_seed, search_seed, verify_seed = (SEED + key + 10 * h for key in (1, 2, 3))

    def assess(trial, copies, repetitions, selection_seed):
        _, error, scores, _ = power.validation_score_panel(
            trial, h, panel, np.random.default_rng(population_seed), copies)
        setting = power.fit_rank_settings(error, scores, trial.abstention[h])
        setting["skills"]["development"] = power.fit_rank_skills(error, scores, setting, targets)
        values = power.validation_draws(trial, h, panel, setting, selection_seed, repetitions)
        ratio = np.nanstd(values, axis=0, ddof=1) / baseline
        return float(np.max(np.abs(np.log(ratio)))), setting, values

    original = replace(profile, event_score_scale=None)
    _, _, uncalibrated = assess(original, 64, 2000, verify_seed)
    rho = float(profile.cluster_correlation[h])
    tested = []
    for b1, pair, scale, within in product((-.25, .15, .50), (.60, .85, .96, .99),
                                           (1., 1.45, 1.9, 2.5), (rho, .80)):
        trial = noise_profile(profile, h, b1, pair, scale, within)
        criterion, _, _ = assess(trial, 12, 200, search_seed)
        tested.append((criterion, (b1, pair, scale, within)))
    finalists = []
    for _, parameters in sorted(tested)[:8]:
        trial = noise_profile(profile, h, *parameters)
        criterion, _, _ = assess(trial, 64, 900, search_seed + 100)
        finalists.append((criterion, parameters))
    _, parameters = min(finalists)
    trial = noise_profile(profile, h, *parameters)
    _, setting, verified = assess(trial, 64, 2500, verify_seed)
    result = {
        "fixed_rows": n, "fit_grid_candidates": len(tested), "fit_finalists": len(finalists),
        "parameters": dict(zip(("b1_to_regulatory_correlation", "m1_m3_correlation",
                                "error_score_scale", "within_drug_correlation"), parameters, strict=True)),
        "rank_settings": setting,
        "before_noise_calibration": power.variance_report(empirical, uncalibrated),
        "independent_verification": power.variance_report(empirical, verified),
        "verified_simulated_mean_delta": np.nanmean(verified, axis=0).tolist(),
    }
    print(f"{HORIZONS[h]}m variance ratios " + ", ".join(
        f"{item['ratio']:.3f}" for item in result["independent_verification"].values()), flush=True)
    return parameters, result


def scenario_grid(counts):
    roster = np.array([entry["drug_clusters"] for entry in counts["24"]["by_cutoff"].values()])
    main = counts["24"]["drug_clusters"]
    extra = counts["12"]["drug_clusters"] - main
    arrivals = tuple(np.diff(roster, prepend=0).tolist())
    if sum(arrivals) != main or min(arrivals) < 0:
        raise ValueError("Expected a nested, nondecreasing NDA-only roster")

    def scenario(name, events=75, **kwargs):
        return power.Scenario(name, main, extra, len(arrivals), events, arrivals=arrivals, **kwargs)

    return [
        *(scenario(f"events_{n}", n) for n in (30, 50, 75, 100, 150)),
        scenario("drift_minus_30pct", 53), scenario("drift_plus_30pct", 97),
        scenario("young", young=True), scenario("low_correlation", correlation=.25),
        scenario("high_correlation", correlation=.90),
    ]


def run_scenario(profile, scenario, sequence):
    cal, verify, simulate = sequence.spawn(3)
    settings = power.test_rank_settings(profile, scenario, np.random.default_rng(cal),
                                        CALIBRATION_MULTIPLIER, {"null": 0., "useful": power.EFFECT})
    population = {}
    for config, seed in zip(("null", "useful"), verify.spawn(2), strict=True):
        result = power.population_check(profile, scenario, settings, np.random.default_rng(seed),
                                        VERIFICATION_MULTIPLIER, config)
        expected = [-power.EFFECT, -power.EFFECT, 0.] if config == "useful" else [0.] * 3
        result["pass"] = bool(np.allclose(result["delta_by_horizon"], expected, atol=TARGET_TOLERANCE, rtol=0.))
        population[config] = result
    subset = CHECK_REPETITIONS if scenario.event_clusters in (30, 75) and scenario.name.startswith("events_") else 0
    arrays = power.bootstrap_experiment(profile, scenario, settings, simulate, REPETITIONS, DRAWS,
                                        "useful", exact_subset=subset)
    result = power.experiment_rates(*arrays, DRAWS, effect=power.EFFECT)
    print(f"{scenario.name} complete; H1 {result['nominal']['rates']['H1']['overall']['rate']:.3f}", flush=True)
    return {"scenario": asdict(scenario), "rank_settings": settings, "population": population, "power": result}


def run_reference_null(profile, scenario, settings, seed):
    result = power.bootstrap_experiment(profile, scenario, settings, seed, NULL_BATCH, FULL_DRAWS,
                                         "null", h1_only=True)
    print(f"Reference null batch {seed.spawn_key[-1] + 1} complete", flush=True)
    return result


def reference_mde_check(profile, scenario, effects, seed):
    cal, verify, runs = seed.spawn(3)
    configurations = {f"{effect:.5f}": effect for effect in effects}
    settings = power.test_rank_settings(profile, scenario, np.random.default_rng(cal),
                                        CALIBRATION_MULTIPLIER,
                                        {**configurations, "useful_anchor": power.EFFECT})
    result = {}
    for (config, effect), sample_seed, verify_seed in zip(
            configurations.items(), runs.spawn(len(effects)), verify.spawn(len(effects)), strict=True):
        population = power.population_check(profile, scenario, settings, np.random.default_rng(verify_seed),
                                            VERIFICATION_MULTIPLIER, config)
        arrays = power.bootstrap_experiment(profile, scenario, settings, sample_seed, REPETITIONS,
                                            DRAWS, config, h1_only=True)
        result[config] = {"target_effect": effect, "population": population,
                          "power": power.experiment_rates(*arrays, DRAWS, h1_only=True)}
        print(f"Direct H1 effect {effect:.5f} complete", flush=True)
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
    parser.add_argument("--raw", type=Path, default=Path(DEFAULT_DIR).parent / "raw-20261127")
    parser.add_argument("--ob-dir", type=Path, default=Path(DEFAULT_DIR))
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    start = time.perf_counter()
    captured, empirical, audit, entities = prepare_e7b(args.raw, args.ob_dir)
    if args.prepare_only:
        print(json.dumps(clean_json(audit), indent=2, allow_nan=False))
        return
    profile, counts, panels, targets, fitted = prepare_generator(args.raw, captured, entities)
    print("Projected E7b development and NDA-only frame complete", flush=True)
    seeds = np.random.SeedSequence(SEED).spawn(3)
    scenarios = scenario_grid(counts)
    reference = scenarios[2]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs = [pool.submit(fit_validation, profile, h, panels[h], targets[h], empirical[months])
                for h, months in enumerate(HORIZONS)]
        calibration = {}
        for h, (months, job) in enumerate(zip(HORIZONS, jobs, strict=True)):
            parameters, verification = job.result()
            calibration[str(months)] = verification
            profile = noise_profile(profile, h, *parameters)
            profile.skill[h] = verification["rank_settings"]["skills"]["development"][0]
        variance_pass = all(item["pass"] for v in calibration.values()
                            for item in v["independent_verification"].values())
        if not variance_pass:
            print(json.dumps(clean_json(calibration), indent=2, allow_nan=False), flush=True)

        jobs = [pool.submit(run_scenario, profile, scenario, seed)
                for scenario, seed in zip(scenarios, seeds[0].spawn(len(scenarios)), strict=True)]
        reference_result = jobs[2].result()
        null_seed, mde_seed = seeds[1:]
        null_jobs = [pool.submit(run_reference_null, profile, reference,
                                 reference_result["rank_settings"], seed)
                     for seed in null_seed.spawn(NULL_REPETITIONS // NULL_BATCH)]
        mde_values = [reference_result["power"][method]["H1_mde80_magnitude_location_shift"]
                      for method in ("nominal", "h1_alpha_020")]
        direct_effects = sorted({round(float(np.clip(value + offset, .0005, .020)), 5)
                                 for value in mde_values if value is not None
                                 for offset in (-.001, .001)})
        direct_job = pool.submit(reference_mde_check, profile, reference, direct_effects, mde_seed)
        results = [job.result() for job in jobs]
        null_batches = [job.result() for job in null_jobs]
        null_arrays = [np.concatenate(items) for items in zip(*null_batches, strict=True)]
        null_arrays[-1] = np.sum([item[-1] for item in null_batches], axis=0)
        null = power.experiment_rates(*null_arrays, FULL_DRAWS, h1_only=True)
        direct = direct_job.result()

    grid = [result for result in results if result["scenario"]["name"].startswith("events_")]
    minimum_counts = {}
    for method in ("nominal", "h1_alpha_020"):
        qualifying = [
            result["scenario"]["event_clusters"] for result in grid
            if result["population"]["useful"]["pass"]
            and result["power"][method]["rates"]["H1"]["overall"]["rate"] >= .80
        ]
        minimum_counts[method] = min(qualifying, default=None)
    output = ROOT / "data" / "T4b_power.json"
    result = {
        "scope": "development-projected E7b models and synthetic NDA-only candidate-frame power",
        "seed": SEED, "nominal_alpha": power.ALPHA, "alternative_h1_alpha": .020,
        "common_coverage": power.COVERAGE, "arm_order": ["B1", "M1", "M3"],
        "horizon_order": HORIZONS, "paired_contrast_order": power.PAIR_NAMES,
        "confirmatory_contrast_order": power.CONTRASTS,
        "population_target_tolerance": TARGET_TOLERANCE, "population_target": -power.EFFECT,
        "calibration_multiplier": CALIBRATION_MULTIPLIER, "verification_multiplier": VERIFICATION_MULTIPLIER,
        "independent_variance_gate_pass": variance_pass,
        "validation_calibration": calibration, "candidate_frame": counts,
        "minimum_grid_event_clusters_at_80pct_H1": minimum_counts,
        "reference_global_null": null, "reference_direct_h1_mde_check": direct,
        "generator": {
            "history_cutoffs": profile.years, "event_templates": len(profile.events),
            "non_event_templates": len(profile.non_events), "extra_arrival_templates": len(profile.extra_arrivals),
            "age_edges": profile.age_edges.tolist(), "age_confidence_weights": profile.age_means.tolist(),
            "within_drug": profile.cluster_correlation.tolist(), "arm_correlation": profile.arm_correlations.tolist(),
            "event_score_scale": profile.event_score_scale.tolist(),
            "common_call_entry_by_outcome": profile.call_entry.tolist(),
            "empirical_largest_tie": [item[-1] for item in fitted],
            "model_abstention": profile.abstention.tolist(),
        },
        "runtime": {"python": platform.python_version(), "numpy": np.__version__, "workers": args.workers,
                    "elapsed_seconds": round(time.perf_counter() - start, 1)},
        "seal": {"test_starts": TEST_FIRST.isoformat(), "development_events_through": DEV_LAST_EVENT.isoformat(),
                 "guard_source_sha256": hashlib.sha256((ROOT / "loe_bench" / "seal.py").read_bytes()).hexdigest(),
                 "lock_present": seal.LOCK_PATH.exists(), "authorization_variable_present": seal.ENV_NAME in os.environ},
        **audit, "scenarios": results,
    }
    output.write_text(json.dumps(clean_json(result), sort_keys=True, indent=2, allow_nan=False) + "\n",
                      encoding="utf-8", newline="\n")
    print(output, flush=True)


if __name__ == "__main__":
    main()
