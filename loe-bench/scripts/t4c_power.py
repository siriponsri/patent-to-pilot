"""Replay sealed development and measure the criteria v3 operating characteristics."""
import argparse
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, replace
from datetime import date, timedelta
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import time
from unittest.mock import patch

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import numpy as np

import k20t1_run as pipeline
import t4_power as guarded
from loe_bench import power_v3 as v3, seal
from loe_bench.baselines import AgeHazardTable


SEED = 2026112704
HORIZONS = (24, 12)
REPS = 5000
FULL = 2000
REDUCED = 400
NULL_REPS = 12000
CAL_REPS = 2500
VERIFY_REPS = 5000
EFFECT_TOL = .005
CHECK_REPS = 400
CURVE = (.05, .075, .10, .15, .20, .25, .30)
CORRELATION_STRESS = {"low_correlation": (.25, -1.5), "high_correlation": (.995, 2.5)}
OUT = guarded.ROOT / "data" / "T4c_power.json"


def require_sealed():
    if seal.LOCK_PATH.exists() or seal.ENV_NAME in os.environ:
        raise PermissionError("T4c must run without a test lock or authorization")


def development_inputs(raw, ob_dir):
    """Override every CP4 outcome reader with the T4b byte-level allowlist."""
    replay = pipeline.replay
    reader = guarded.projected_reader(True)

    def development_reader(path, *, identity=False):
        return reader(path)

    with (patch.object(replay, "development_reader", development_reader),
          patch.object(replay, "historical_orange_reader", reader),
          patch.object(replay, "application_identity_reader", reader)):
        return replay.inputs(raw, ob_dir, ob_dir.parent / "piv", ob_dir.parent / "challenge")


def dev_panel(rows):
    keys = {}
    return v3.Panel(np.array([keys.setdefault(r["key"], len(keys)) for r in rows]),
                    np.array([r["t"].year for r in rows]),
                    np.array([r["x"]["age_years"] for r in rows]),
                    np.array([bool(r["y"]) for r in rows]), len(keys))


def development(raw, ob_dir):
    require_sealed()
    entities, builder, provenance = development_inputs(raw, ob_dir)
    manifest, _ = guarded._manifest(guarded.ROOT / "data" / "S0_INPUT_MANIFEST.json")
    gsrs = raw.resolve().parent / "moiety" / guarded.moiety.GSRS_FILE
    roster = guarded.candidate_counts(guarded.build_projected_entities(raw, gsrs, development=False),
                                      date.fromisoformat(manifest["t0"]))
    templates = guarded.history_templates(entities)
    # T4b emits the age band, so unit edges retain the native one-year clock bin.
    history = guarded.power.Profile(*templates, np.arange(1, 31), None, None, None, None, None, None)
    result = []
    for h in HORIZONS:
        train_dates, validation_dates = pipeline.replay.PRIMARY[h]
        pipeline.verify_windows(train_dates, validation_dates, h)
        guarded.t2.require_development_cutoffs([*train_dates, *validation_dates])
        train = pipeline.replay.partition(entities, builder, train_dates, h, training=True)
        rows = pipeline.replay.partition(entities, builder, validation_dates, h)
        models, age = pipeline.devx.raw_predictions(train, rows, h, pipeline.FLAGS,
                                                    min(validation_dates) - timedelta(days=1))
        panel = dev_panel(rows)
        score = np.column_stack((age, models["M1"], models["M3"]))
        clock = AgeHazardTable().fit(train)
        b1 = np.array([clock.rate.get(i, clock.base) for i in range(31)])
        np.testing.assert_array_equal(score[:, 0], b1[v3.age_index(panel.age)])
        rng = random.Random(guarded.t2.BOOTSTRAP_SEED)
        counts = np.array([np.bincount([rng.randrange(panel.clusters) for _ in range(panel.clusters)],
                                      minlength=panel.clusters) for _ in range(FULL)], dtype=np.float32)
        empirical = v3.contrasts(v3.recalls(panel, score, counts))
        result.append((panel, score, empirical, v3.fit_ranks(panel, score, b1)))
    require_sealed()
    return result, history, roster, provenance


def draw_validation(panel, fit, seed, reps, tilts=None):
    rng = np.random.default_rng(seed)
    diagnostics, thresholds = [], []
    for _ in range(reps):
        score = v3.native_scores(panel, fit, rng.standard_normal((panel.clusters, 2)),
                                rng.standard_normal((len(panel.drug), 2)))
        if tilts is None:
            thresholds.append([v3.breakpoints(panel, column) for column in score[:, 1:].T])
        else:
            score[panel.event, 1:] += tilts
            diagnostics.append(v3.diagnostics(panel, score))
    if tilts is None:
        return np.concatenate(thresholds, axis=1)
    return np.asarray(diagnostics)


def diagnostic_table(diagnostic, cutoffs):
    result = {}
    for t, (denom, hits, tie, discord) in zip(cutoffs, diagnostic, strict=True):
        rows, events, slots = denom
        result[str(t)] = {"rows": rows, "events": events, "slots": slots,
                          "capture": hits.tolist(), "recall": (hits / events).tolist() if events else [None] * len(hits),
                          "precision": (hits / slots).tolist() if slots else [None] * len(hits),
                          "boundary_tie_size": tie.tolist(),
                          "paired_capture_discordance_event_units": discord.tolist()}
    return result


def variance_fit(panel, native, empirical, base, seed):
    empirical_d = v3.diagnostics(panel, native)
    targets = empirical_d[:, 1].sum(axis=0)[1:] / panel.event.sum()
    search_seed, verification_seed = seed.spawn(2)
    # Fit nominal levels on the selection stream. Revisit persistence and
    # residual arm correlation if the conditional sampling variance misses.
    pairs = (base.pair, .99, .97, .93, .87, .75, .55, .25, 0.)
    persistence = (base.persistence, .95, .8, .6, .3, 0.)
    trials = []
    choices = []
    for persist in persistence:
        for pair in pairs:
            candidate = replace(base, pair=pair, persistence=persist)
            threshold = draw_validation(panel, candidate, search_seed, 250)
            tilts = [v3.tilt_for(t, target) for t, target in zip(threshold, targets, strict=True)]
            sample = draw_validation(panel, candidate, search_seed, 350, tilts)
            paired = v3.contrasts(sample[:, :, 1].sum(axis=1) / panel.event.sum())
            check = v3.variance_report(empirical, paired)
            ratio = [item["ratio"] for item in check.values()]
            error = max(abs(x - 1) for x in ratio)
            trials.append({"pair": pair, "persistence": persist, "selection_sd_ratio": ratio})
            choices.append((error, candidate, tilts))
        if min(c[0] for c in choices) < .14:
            break
    for _, fit, tilts in sorted(choices, key=lambda item: item[0]):
        # A previously unseen stream is used for each verification attempt.
        sim = draw_validation(panel, fit, verification_seed.spawn(1)[0], 2500, tilts)
        sample = v3.contrasts(sim[:, :, 1].sum(axis=1) / panel.event.sum())
        check = v3.variance_report(empirical, sample)
        trials.append({"pair": fit.pair, "persistence": fit.persistence, "verification": check})
        if all(item["pass"] for item in check.values()):
            cutoffs = np.unique(panel.cutoff)
            return fit, {"pass": True, "contrasts": check, "trials": trials, "fit": asdict(fit),
                         "seed_spawn_key": seed.spawn_key,
                         "validation_tilts": tilts, "clusters": panel.clusters,
                         "event_clusters": len(np.unique(panel.drug[panel.event])),
                         "empirical_by_cutoff": diagnostic_table(empirical_d, cutoffs),
                         "simulated_mean_by_cutoff": diagnostic_table(sim.mean(axis=0), cutoffs)}
    return base, {"pass": False, "trials": trials}


def json_ready(item):
    if isinstance(item, np.ndarray):
        return guarded.clean_json(item.tolist())
    if isinstance(item, dict):
        return {key: json_ready(value) for key, value in item.items()}
    if isinstance(item, (list, tuple)):
        return [json_ready(value) for value in item]
    return guarded.clean_json(item)


def null_scores(score, panel, fit, drug, row, pair):
    z = np.sqrt(fit.persistence) * drug[panel.drug] + np.sqrt(1 - fit.persistence) * row
    z[:, 1] = pair * z[:, 0] + np.sqrt(1 - pair**2) * z[:, 1]
    return v3.tied_null(score[:, 0], z)


def score_panels(history, scenario, fits, rng):
    data = list(v3.panels(history, scenario, rng))
    # T4b shares underlying drug and row draws across horizons. The 24-month
    # rows are a subset of the 12-month frame in the same order.
    full = data[1]
    drug = rng.standard_normal((full.clusters, 2))
    row = rng.standard_normal((len(full.drug), 2))
    for h, (panel, fit) in enumerate(zip(data, fits, strict=True)):
        pair, clock_weight = CORRELATION_STRESS.get(scenario.name, (fit.pair, 0.))
        row_z = row if h else row[full.cutoff < scenario.years]
        score = v3.native_scores(panel, fit, drug, row_z, exchangeable=True,
                                 pair=pair, clock_weight=clock_weight)
        yield panel, score, drug, row_z, pair


def summarize_pool(history, scenario, fits, seed, reps, verify_null=False):
    rng = np.random.default_rng(seed)
    thresholds = [[], []]
    base_hits, events, row_counts = np.zeros(2), np.zeros(2), np.zeros(2)
    null_hits = np.zeros((2, 2))
    base_by_cutoff = [np.zeros((scenario.years + h, 5)) for h in range(2)]
    for _ in range(reps):
        for h, (panel, score, drug, row, pair) in enumerate(score_panels(history, scenario, fits, rng)):
            tie_rank = null_scores(score, panel, fits[h], drug, row, pair) if verify_null else None
            for t in np.unique(panel.cutoff):
                idx = panel.cutoff == t
                y = panel.event[idx]
                hit, _, tied = v3.point_queue(score[idx, 0], y)
                base_by_cutoff[h][t] += [idx.sum(), y.sum(), idx.sum() // 5, hit, tied]
                base_hits[h] += hit
                if verify_null:
                    null_hits[h] += [v3.point_queue(column, y)[0] for column in tie_rank[idx].T]
            events[h] += panel.event.sum()
            row_counts[h] += len(panel.drug)
            thresholds[h].append(np.concatenate([v3.breakpoints(panel, column) for column in score[:, 1:].T]))
    values = [np.sort(np.concatenate(t)) for t in thresholds]
    return values, base_hits / events, (events / row_counts).tolist(), [x / reps for x in base_by_cutoff], null_hits / events[:, None]


def target_cells(scenario):
    cells = [("useful", (.10, .02, .10))]
    if scenario.name == "events_75":
        cells.extend((f"curve_{effect:.3f}", (effect, .02, .10)) for effect in CURVE if effect != .10)
        cells.extend((f"h2_{effect:.3f}", (.10, effect, .10)) for effect in (0., .05))
        cells.extend([("global_null", (0., 0., 0.)), ("mixed_h3_null", (.10, .05, 0.))])
    return cells


def calibrate(history, scenario, fits, seed):
    cal_seed, verify_seed = seed.spawn(2)
    threshold, base, _, _, _ = summarize_pool(history, scenario, fits, cal_seed, CAL_REPS)
    reference = scenario.name == "events_75"
    eval_threshold, eval_base, prevalence, by_cutoff, tie_level = summarize_pool(
        history, scenario, fits, verify_seed, VERIFY_REPS, verify_null=reference)
    settings = {}
    for name, (h1, h2, h3) in target_cells(scenario):
        targets = ((h1 - h2, h1), (h3, h3))
        shifts, levels = [], []
        for h, effects in enumerate(targets):
            tied = (h == 0 and h1 == 0) or (h == 1 and h3 == 0)
            tilt = None if tied else [v3.tilt_for(threshold[h], base[h] + effect) for effect in effects]
            shifts.append(tilt)
            arm_level = tie_level[h] if tied else [np.searchsorted(eval_threshold[h], x) /
                                                  len(eval_threshold[h]) for x in tilt]
            levels.append([eval_base[h], *arm_level])
        observed = v3.contrasts(np.asarray(levels))
        delta = [observed[0, 0], observed[0, 1], observed[1, 0]]
        passed = bool(np.all(np.abs(np.asarray(delta) - [h1, h2, h3]) <= EFFECT_TOL))
        settings[name] = {"target": [h1, h2, h3], "verified_population_delta": delta,
                          "verification_pass": passed, "verified_recall_by_horizon": levels,
                          "shifts_M1_M3": shifts}
    return {"seed_spawn_key": seed.spawn_key, "settings": settings, "event_row_prevalence": prevalence,
            "mean_candidate_cutoff_stats_order": ["rows", "events", "slots", "B1_capture", "B1_boundary_tie"],
            "mean_candidate_cutoff_stats": by_cutoff}


def bounds_for_task(history, scenario, fits, config, seed, repetitions, draws, alphas, *, check=False):
    rng = np.random.default_rng(seed)
    replication = np.empty((len(alphas), repetitions, 3))
    reduced = np.empty((len(alphas), repetitions, 3)) if check else None
    point = np.zeros(3)
    covariance = np.zeros((2, 3, 3))
    totals = None
    for i in range(repetitions):
        data_rng, boot_rng = (np.random.default_rng(key) for key in rng.integers(2**63, size=2))
        sample = []
        audit = []
        for h, (panel, score, drug, row, pair) in enumerate(score_panels(history, scenario, fits, data_rng)):
            tilt = config["shifts_M1_M3"][h]
            if tilt is None:
                score[:, 1:] = null_scores(score, panel, fits[h], drug, row, pair)
            else:
                score[panel.event, 1:] += tilt
            pairs = ((2, 0), (2, 1)) if h == 0 else ((2, 0),)
            used = score if h == 0 else score[:, [0, 2]]
            sample.append(v3.paired_draws(panel, used, boot_rng, draws, pairs if h == 0 else ((1, 0),)))
            if i < 250:
                diagnostic = v3.diagnostics(panel, score)
                audit.append(diagnostic)
                d = v3.contrasts(diagnostic[:, 1].sum(axis=0) / panel.event.sum())
                if h == 0:
                    point[:2] += d[:2]
                else:
                    point[2] += d[0]
                covariance[h] += np.corrcoef(score.T)
        if audit:
            totals = audit if totals is None else [a + b for a, b in zip(totals, audit, strict=True)]
        deltas = np.column_stack(sample)
        for a, alpha in enumerate(alphas):
            replication[a, i] = v3.lower_bounds(deltas, alpha)
            if check:
                reduced[a, i] = v3.lower_bounds(deltas[:REDUCED], alpha)
    n_audit = min(250, repetitions)
    diagnostics = {"seed_spawn_key": seed.spawn_key, "diagnostic_datasets": n_audit,
                   "mean_dataset_delta": point / n_audit, "mean_score_correlation": covariance / n_audit,
                   "mean_by_cutoff": [diagnostic_table(x / n_audit, range(len(x))) for x in totals]}
    return replication, reduced, diagnostics


def compare_draws(full, reduced):
    result = {}
    for alpha, f, r in zip(v3.ALPHAS, full, reduced, strict=True):
        match = (f > 0) == (r > 0)
        diff = (r > 0).mean(axis=0) - (f > 0).mean(axis=0)
        result[str(alpha)] = {"marginal_rejection_difference": diff,
                              "disagreement": [v3.interval(n, len(f)) for n in (~match).sum(axis=0)],
                              "pass": bool(np.max(np.abs(diff)) <= .035 and np.min(match.mean(axis=0)) >= .90
                                           and np.array_equal(np.isfinite(f), np.isfinite(r)))}
    return result


def reserve_jobs(pool, history, scenario, fits, config, seed, alpha):
    return [pool.submit(bounds_for_task, history, scenario, fits, config, child, 500, FULL, (alpha,))
            for child in seed.spawn(NULL_REPS // 500)]


def collect_null(jobs, true_nulls):
    arrays, _, diagnostics = zip(*(job.result() for job in jobs), strict=True)
    return {"rates": v3.decision_rates(np.concatenate(arrays, axis=1)[0], true_nulls),
            "datasets": NULL_REPS, "draws": FULL, "batches": diagnostics}


def mde_from_curve(cells, alpha):
    curve = sorted((item["population"]["target"][0], item["population"]["verified_population_delta"][0],
                    item["rates"][str(alpha)]["H1"]["sequence"]["rate"])
                   for name, item in cells.items() if name == "useful" or name.startswith("curve_"))
    for lower, upper in zip(curve, curve[1:]):
        if lower[2] < .80 <= upper[2]:
            estimate = lower[1] + (.80 - lower[2]) * (upper[1] - lower[1]) / (upper[2] - lower[2])
            return {"interpolated_verified_effect": estimate, "bracket": [lower, upper], "curve": curve}
    return {"interpolated_verified_effect": None, "bracket": None, "curve": curve}


def scenario_metadata(scenario):
    fields = asdict(scenario)
    # The inherited v2 correlation setting described B1's simulated latent noise.
    # V3 keeps B1 deterministic and instead stresses regulatory residuals and clock loading.
    del fields["correlation"], fields["coverage_stress"]
    pair, clock = CORRELATION_STRESS.get(scenario.name, (None, 0.))
    return dict(fields, regulatory_residual_correlation_override=pair, b1_rank_loading_adjustment=clock)


def run_power(pool, history, fits, roster, provenance, validation, seed, start, workers):
    scenarios = guarded.scenario_grid(roster)
    cal, checks, null, power_seed = seed.spawn(4)
    cal_jobs = [pool.submit(calibrate, history, s, fits, child)
                for s, child in zip(scenarios, cal.spawn(len(scenarios)), strict=True)]
    reference = scenarios[2]
    settings = {s.name: job.result() for s, job in zip(scenarios, cal_jobs, strict=True)}
    failures = [(scenario, name) for scenario, value in settings.items() for name, config in value["settings"].items()
                if not config["verification_pass"]]
    if failures:
        raise RuntimeError(f"Independent population effect verification failed: {failures}")
    print("Independent population effect verification passed", flush=True)

    ref_config = settings[reference.name]["settings"]
    check_cases = ((scenarios[0], "useful"), (reference, "curve_0.075"), (reference, "curve_0.200"))
    check_jobs = [pool.submit(bounds_for_task, history, s, fits, settings[s.name]["settings"][name], child,
                              CHECK_REPS, FULL, v3.ALPHAS, check=True)
                  for (s, name), child in zip(check_cases, checks.spawn(len(check_cases)), strict=True)]
    null_025_seed, null_020_seed, mixed2_seed, mixed3_seed = null.spawn(4)
    null_jobs = reserve_jobs(pool, history, reference, fits, ref_config["global_null"], null_025_seed, .025)
    checked = {}
    for (s, name), job in zip(check_cases, check_jobs, strict=True):
        f, r, _ = job.result()
        checked[f"{s.name}/{name}"] = compare_draws(f, r)
    draws = REDUCED if all(x["pass"] for values in checked.values() for x in values.values()) else FULL
    print(f"Paired draw-count check selected {draws} inner draws for power", flush=True)
    cells = [(s, name) for s in scenarios for name, _ in target_cells(s)
             if name not in {"global_null", "mixed_h3_null"}]
    jobs = [pool.submit(bounds_for_task, history, s, fits, settings[s.name]["settings"][name], child,
                        REPS, draws, v3.ALPHAS)
            for (s, name), child in zip(cells, power_seed.spawn(len(cells)), strict=True)]
    primary = collect_null(null_jobs, (0, 1, 2))
    selected = .025 if primary["rates"]["H1"]["sequence"]["wilson_95"][1] <= .025 else .020
    null_results = {"global_null_alpha_0.025": primary}
    backstop = reserve_jobs(pool, history, reference, fits, ref_config["global_null"], null_020_seed, .020) if selected == .020 else None
    mixed2 = reserve_jobs(pool, history, reference, fits, ref_config["h2_0.000"], mixed2_seed, selected)
    mixed3 = reserve_jobs(pool, history, reference, fits, ref_config["mixed_h3_null"], mixed3_seed, selected)
    print(f"RULE_SELECTED_ALPHA={selected:.3f}", flush=True)

    for (s, name), job in zip(cells, jobs, strict=True):
        observed, _, diagnostics = job.result()
        settings[s.name].setdefault("power", {})[name] = {
            "population": settings[s.name]["settings"][name], "diagnostics": diagnostics,
            "rates": {str(a): v3.decision_rates(o) for a, o in zip(v3.ALPHAS, observed, strict=True)},
        }
        print(f"Complete {s.name}/{name}", flush=True)
    if backstop is not None:
        null_results["global_null_alpha_0.020"] = collect_null(backstop, (0, 1, 2))
    null_results["mixed_H2_null_selected_alpha"] = collect_null(mixed2, (1,))
    null_results["mixed_H3_null_selected_alpha"] = collect_null(mixed3, (2,))
    minimum = min((s.event_clusters for s in scenarios if s.name.startswith("events_") and
                   settings[s.name]["power"]["useful"]["rates"][str(selected)]["H1"]["sequence"]["rate"] >= .80),
                  default=None)
    require_sealed()
    result = {"scope": "DEVELOPMENT_ONLY native K07 replay and synthetic NDA-only roster scenarios",
              "seed": SEED, "RULE_SELECTED_ALPHA": selected, "arm_order": v3.ARMS,
              "contrast_order": v3.PAIR_NAMES, "horizon_order": HORIZONS,
              "power_datasets_per_cell": REPS, "power_bootstrap_draws": draws, "null_bootstrap_draws": FULL,
              "power_draw_check": {"datasets_per_cell": CHECK_REPS, "reduced_draws": REDUCED, "results": checked},
              "population_calibration_datasets": CAL_REPS, "population_verification_datasets": VERIFY_REPS,
              "population_target_tolerance": EFFECT_TOL, "variance": validation, "null": null_results,
              "minimum_grid_event_clusters_at_80pct_H1_useful": minimum,
              "H1_mde80_at_75_clusters": mde_from_curve(settings[reference.name]["power"], selected),
              "scenario_definitions": {s.name: scenario_metadata(s) for s in scenarios}, "scenarios": settings,
              "candidate_frame": roster, "development_input_provenance": provenance,
              "history_templates": {"event": len(history.events), "other": len(history.non_events),
                                    "late_arrivals": len(history.extra_arrivals), "development_years": history.years},
              "seal": {"test_starts": seal.TEST_FIRST.isoformat(),
                       "development_observation_ends": guarded.DEV_LAST_EVENT.isoformat(),
                       "guard_source_sha256": hashlib.sha256(Path(seal.__file__).read_bytes()).hexdigest(),
                       "lock_present": seal.LOCK_PATH.exists(),
                       "authorization_variable_present": seal.ENV_NAME in os.environ},
              "runtime": {"python": platform.python_version(), "numpy": np.__version__, "workers": workers,
                          "elapsed_seconds": round(time.perf_counter() - start, 1)}}
    OUT.write_text(json.dumps(json_ready(result), indent=2, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    print(OUT, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path(guarded.DEFAULT_DIR).parent / "raw-20261127")
    parser.add_argument("--ob-dir", type=Path, default=Path(guarded.DEFAULT_DIR))
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    start = time.perf_counter()
    dev, history, roster, provenance = development(args.raw, args.ob_dir)
    print("Pinned development replay and NDA-only frame complete", flush=True)
    fit_root, sim_root = np.random.SeedSequence(SEED).spawn(2)
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs = [pool.submit(variance_fit, *inputs, seed) for inputs, seed in zip(dev, fit_root.spawn(2), strict=True)]
        fits, audit = zip(*(job.result() for job in jobs))
        check = {str(h): item for h, item in zip(HORIZONS, audit, strict=True)}
        if args.validate_only or not all(item["pass"] for item in audit):
            print(json.dumps(json_ready(check), indent=2, allow_nan=False), flush=True)
        if not all(item["pass"] for item in audit):
            raise RuntimeError("Variance gate failed before power simulation")
        if args.validate_only:
            return
        run_power(pool, history, fits, roster, provenance, check, sim_root, start, args.workers)


if __name__ == "__main__":
    main()
