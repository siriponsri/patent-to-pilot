"""Score C4 v2 mapped US Medicaid forecasts on locked development origins."""

import argparse
import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from hashlib import sha256
from itertools import combinations
from math import isfinite
from pathlib import Path

import numpy as np

from . import c4, seal

SCOPE = "DEVELOPMENT_ONLY"
VINTAGE_LABEL = "retrospective, vintage-uncontrolled"
BASELINE_ARMS = ("carry_forward", "drift")
QUEUE_ARMS = ("B1", "M3")
PENDING = "PENDING_SCORE_EXPORT"
ENDPOINTS = {
    "annual_prescriptions": ("counts", sum),
    "reimbursement_per_prescription_q4": ("reimbursement_per_prescription", lambda values: values[-1]),
    "annual_reimbursement": ("reimbursed_cents", sum),
}


@dataclass(frozen=True)
class Forecast:
    ingredient: str
    actual: float
    predictions: dict[str, float]


@dataclass(frozen=True)
class EntryQueue:
    keys: frozenset[str]
    selected: dict[str, frozenset[str]]


def build_queues(rows, expected_sizes, tie_seed):
    by_cutoff = defaultdict(dict)
    for row in rows:
        if row.keys() != {"cutoff", "key", *QUEUE_ARMS}:
            raise ValueError("Expected only C3b cutoff, active-moiety key and native B1/M3 scores")
        cutoff = date.fromisoformat(row["cutoff"])
        if cutoff >= c4.DEV_END or row["cutoff"] not in expected_sizes:
            raise ValueError("Unexpected cutoff in frozen 12-month development export")
        key = row["key"]
        if not isinstance(key, str) or not key.strip() or key in by_cutoff[cutoff]:
            raise ValueError("Each cutoff needs unique, nonempty active-moiety keys")
        scores = {arm: row[arm] for arm in QUEUE_ARMS}
        if any(type(score) not in (int, float) or not isfinite(score) or not 0 <= score <= 1
               for score in scores.values()):
            raise ValueError("Native entry scores must be finite probabilities")
        by_cutoff[cutoff][key] = scores
    if {day.isoformat(): len(rows) for day, rows in by_cutoff.items()} != expected_sizes:
        raise ValueError("Score export has a different roster size from the frozen development report")

    queues = {}
    for day, scores in sorted(by_cutoff.items()):
        # The same predeclared permutation resolves both arms' boundary ties.
        ties = {key: sha256(f"{tie_seed}|{day.isoformat()}|{key}".encode()).digest()
                for key in scores}
        slots = len(scores) // 5
        selected = {}
        for arm in QUEUE_ARMS:
            ranked = sorted(scores, key=lambda key: (-scores[key][arm], ties[key], key))
            selected[arm] = frozenset(ranked[:slots])
        queues[day] = EntryQueue(frozenset(scores), selected)
    return queues


def load_queues(paths, policy):
    saw_other_horizon = False
    for path in paths:
        if not path.is_file():
            continue
        content = path.read_bytes()
        data = json.loads(content)
        if (data["status"] != SCOPE
                or data["frozen_config_sha256"] != policy["config_sha256"]):
            raise ValueError("Expected the frozen C3b development score export")
        if data["prediction_horizon_months"] == 24:
            saw_other_horizon = True
            continue
        if data["prediction_horizon_months"] != 12:
            raise ValueError("Unexpected horizon in C3b score export")
        digest = sha256(content).hexdigest()
        if digest != policy["export_sha256"]:
            raise ValueError("C3b 12-month score export SHA-256 mismatch")
        queues = build_queues(data["rows"], policy["rows_by_cutoff"], policy["tie_seed"])
        return queues, {"status": "AVAILABLE", "file": path.name, "sha256": digest}
    reason = "12-month export absent" if not saw_other_horizon else "Only a 24-month export exists"
    return {}, {"status": PENDING, "reason": reason}


def quarterly_value(item, ingredient, field):
    if field == "counts":
        return item.counts.get(ingredient)
    cents = item.reimbursed_cents.get(ingredient)
    if cents is None:
        return None
    if field == "reimbursed_cents":
        return cents / 100
    count = item.counts.get(ingredient)
    return cents / (100 * count) if count else None


def make_forecasts(ingredients, fit, target, lag, field, reduce):
    rows = []
    exclusions = Counter(incomplete_history=0, incomplete_outcome=0)
    for ingredient in ingredients:
        history = [quarterly_value(item, ingredient, field) for item in fit]
        if None in history:
            exclusions["incomplete_history"] += 1
            continue
        observed = [quarterly_value(item, ingredient, field) for item in target]
        if None in observed:
            exclusions["incomplete_outcome"] += 1
            continue
        forecast = c4.project_quarters(history, lag)
        predictions = {arm: reduce(forecast[arm]) for arm in BASELINE_ARMS}
        rows.append(Forecast(ingredient, reduce(observed), predictions))
    return rows, dict(exclusions)


def apply_queue(rows, links, queue, factor):
    counts = Counter(matched_rows=0, unresolved_moiety=0, outside_roster=0, B1_triggers=0, M3_triggers=0)
    paired = []
    for row in rows:
        key = links.get(row.ingredient)
        if key is None:
            counts["unresolved_moiety"] += 1
            continue
        if key not in queue.keys:
            counts["outside_roster"] += 1
            continue
        predictions = dict(row.predictions)
        for arm in QUEUE_ARMS:
            selected = key in queue.selected[arm]
            counts[f"{arm}_triggers"] += selected
            predictions[f"{arm}_adjusted"] = predictions["carry_forward"] * (factor if selected else 1)
        paired.append(Forecast(row.ingredient, row.actual, predictions))
    counts["matched_rows"] = len(paired)
    return paired, dict(counts)


def metrics(rows, *, draws=0, seed=0):
    if not rows:
        return {"status": "NOT_ESTIMABLE", "paired_rows": 0, "ingredients": 0}
    arms = tuple(rows[0].predictions)
    errors = np.array([[row.predictions[arm] - row.actual for arm in arms] for row in rows])
    absolute = np.abs(errors)
    contrasts = list(combinations(range(len(arms)), 2))
    names = [f"{arm}_mae" for arm in arms] + [f"{arm}_bias" for arm in arms]
    names += [f"{arms[b]}_minus_{arms[a]}_mae" for a, b in contrasts]
    values = np.column_stack([absolute, errors, *(absolute[:, b] - absolute[:, a] for a, b in contrasts)])
    clusters = sorted({row.ingredient for row in rows})
    result = {"status": "ESTIMATED", "paired_rows": len(rows), "ingredients": len(clusters),
              "estimates": dict(zip(names, values.mean(axis=0).tolist()))}
    if draws:
        indices = {ingredient: i for i, ingredient in enumerate(clusters)}
        membership = [indices[row.ingredient] for row in rows]
        sizes = np.bincount(membership)
        sums = np.zeros((len(clusters), len(names)))
        np.add.at(sums, membership, values)
        # Resample whole ingredients and retain all their origin rows per draw.
        samples = np.random.default_rng(seed).integers(len(clusters), size=(draws, len(clusters)))
        weights = np.zeros(samples.shape, dtype=int)
        np.add.at(weights, (np.arange(draws)[:, None], samples), 1)
        estimates = (weights @ sums) / (weights @ sizes)[:, None]
        limits = np.quantile(estimates, (0.025, 0.975), axis=0).T.tolist()
        result.update(bootstrap_draws=draws, ci95=dict(zip(names, limits)))
    return result


def ingredient_coverage(items, frame_complete):
    mapped, count, amount, joint = Counter(), Counter(), Counter(), Counter()
    for item in items:
        mapped.update(item.mapped_packages)
        count.update(item.count_complete_packages)
        amount.update(item.amount_complete_packages)
        joint.update(item.joint_complete_packages)
    return {name: {"mapped_package_quarters": n, "count_complete_share": count[name] / n,
                   "amount_complete_share": amount[name] / n, "joint_complete_share": joint[name] / n,
                   "full_ingredient_identity_share": 1.0 if frame_complete else None}
            for name, n in sorted(mapped.items())}


def window_coverage(periods, series):
    overall = c4.coverage(periods, series)
    packages = overall["packages"]
    by_ingredient = ingredient_coverage((series[period] for period in periods if period in series),
                                        overall["complete_frame_quarters"] == len(periods))
    overall["mapped_identity_share"] = (packages - overall["unresolved_packages"]) / packages if packages else None
    return {"frame": overall, "ingredients": by_ingredient}


def score_origin(origin, anchor, training, outcomes):
    index = c4.dev_origin(origin)
    if anchor > index:
        raise ValueError("Training anchor follows the forecast origin")
    fit_periods = range(anchor - c4.HISTORY + 1, anchor + 1)
    target_periods = range(index + 1, index + c4.HORIZON + 1)
    fit = [training.get(period, c4.IngredientQuarter()) for period in fit_periods]
    target = [outcomes.get(period, c4.IngredientQuarter()) for period in target_periods]
    ingredients = sorted(set().union(*(item.counts.keys() for item in fit)))
    coverage = {"fit": window_coverage(fit_periods, training),
                "annual_outcome": window_coverage(target_periods, outcomes),
                "q4_outcome": window_coverage(target_periods[-1:], outcomes)}
    results = {}
    for endpoint, (field, reducer) in ENDPOINTS.items():
        target_items = target[-1:] if field == "reimbursement_per_prescription" else target
        mapped, exclusions = make_forecasts(ingredients, fit, target_items, index - anchor, field, reducer)
        results[endpoint] = {
            "mapped": mapped, "exclusions": exclusions,
            "full": mapped if all(item.frame_complete for item in fit + target_items) else [],
        }
    return ingredients, coverage, results


def run(spec, manifest, raw_dir, registry, queues, score_export):
    origins, pooled = [], defaultdict(list)
    links = {}
    for origin, vintage, anchor, fit, target in c4.pilot_windows(
            spec, manifest, raw_dir, include_reimbursement=True):
        if vintage != c4.RETROSPECTIVE:
            raise ValueError("C4 v2 only admits the frozen retrospective vintage for these origins")
        ingredients, coverage, endpoints = score_origin(origin, anchor, fit, target)
        for name in ingredients:
            if name not in links:
                composition = registry.composition([name])
                links[name] = composition.key if composition.parts and not composition.low_confidence else None

        cutoff = origin + timedelta(days=1)
        queue = queues.get(cutoff) if cutoff < c4.DEV_END else None
        origin_report = {"origin": origin.isoformat(), "vintage": vintage,
                         "last_fit_quarter": c4.quarter_label(anchor), "queue_cutoff": cutoff.isoformat(),
                         "queue_cutoff_status": "AVAILABLE" if queue else
                         "RESERVED_CUTOFF" if cutoff >= c4.DEV_END else
                         "NO_FROZEN_CUTOFF" if queues else PENDING,
                         "candidate_ingredients": len(ingredients), "coverage": coverage, "endpoints": {}}
        for endpoint, result in endpoints.items():
            mapped = result["mapped"]
            report = {"mapped_baselines": metrics(mapped), "full_national": metrics(result["full"]),
                      "exclusions": result["exclusions"],
                      "linked_ingredients": sum(bool(links[row.ingredient]) for row in mapped)}
            pooled[endpoint, "mapped_baselines"].extend(mapped)
            pooled[endpoint, "full_national"].extend(result["full"])
            if endpoint != "annual_prescriptions":
                report["entry_adjusted"] = {"status": origin_report["queue_cutoff_status"]}
                if queue:
                    adjusted, linkage = apply_queue(mapped, links, queue, spec["entry_policy"]["factor"])
                    report["entry_adjusted"] = {**metrics(adjusted), "linkage": linkage}
                    pooled[endpoint, "entry_adjusted"].extend(adjusted)
            origin_report["endpoints"][endpoint] = report
        origins.append(origin_report)

    boot = spec["metrics"]["bootstrap"]
    summary = {}
    for endpoint in ENDPOINTS:
        summary[endpoint] = {}
        arms = ["mapped_baselines", "full_national"]
        if endpoint != "annual_prescriptions":
            arms.append("entry_adjusted")
        for arm in arms:
            rows = pooled[endpoint, arm]
            result = metrics(rows, draws=boot["draws"], seed=boot["seed"])
            result["evaluable_origins"] = sum(bool(origin["endpoints"][endpoint][arm].get("paired_rows"))
                                               for origin in origins)
            if arm == "entry_adjusted" and not queues:
                result["status"] = PENDING
            if arm == "mapped_baselines":
                names = {row.ingredient for row in rows}
                result["linked_ingredients"] = sum(bool(links[name]) for name in names)
            summary[endpoint][arm] = result
    return {"scope": SCOPE, "vintage": c4.RETROSPECTIVE, "vintage_label": VINTAGE_LABEL,
            "as_of_proven": {"status": "NOT_RUN", "admitted_origins": 0},
            "score_export": score_export,
            "queue_sizes": {day.isoformat(): {"eligible_keys": len(queue.keys),
                                              **{arm: len(queue.selected[arm]) for arm in QUEUE_ARMS}}
                            for day, queue in queues.items()},
            "origins": origins, "pooled": summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--gsrs", type=Path, required=True)
    parser.add_argument("--scores", type=Path, help="Explicit C3b 12-month development export")
    parser.add_argument("--out", type=Path, required=True, help="New report path outside Git")
    args = parser.parse_args()
    if seal.LOCK_PATH.exists() or seal.ENV_NAME in os.environ:
        parser.error("C4 v2 requires the protected LOE-Bench seal to remain closed")
    if args.out.exists():
        parser.error("Choose a new report path")
    spec_bytes = c4.lock_bytes(args.spec)
    spec_digest = sha256(spec_bytes).hexdigest()
    if spec_digest != args.spec.with_suffix(".sha256").read_text(encoding="utf-8").split()[0]:
        parser.error("C4 v2 spec SHA-256 mismatch")
    spec = json.loads(spec_bytes)
    if spec["protocol_version"] != "C4-v2" or spec["scope"] != SCOPE:
        parser.error("Expected the frozen C4 development protocol v2")
    for name, digest in spec["code_sha256"].items():
        if sha256(c4.lock_bytes(Path(__file__).with_name(name))).hexdigest() != digest:
            parser.error(f"Pinned scorer SHA-256 mismatch for {name}")
    manifest_bytes = c4.lock_bytes(args.inputs)
    if sha256(manifest_bytes).hexdigest() != spec["input_manifest_sha256"]:
        parser.error("C4 input manifest SHA-256 mismatch")
    manifest = json.loads(manifest_bytes)
    origins = c4.pilot_origins(spec, manifest)
    if any(entry["verdict"] != c4.RETROSPECTIVE for entry in origins.values()):
        parser.error("C4 v2 admits the seven frozen retrospective origins only")
    root = args.raw_dir.parent
    score_paths = [args.scores] if args.scores else [root / "FREEZE_dev_scores_12m.json",
                                                    root / "FREEZE_dev_scores.json"]
    queues, export = load_queues(score_paths, spec["entry_policy"])
    c4.verify_file(args.gsrs, spec["gsrs_sha256"])
    registry = c4.registry_for(args.raw_dir, args.gsrs)
    report = run(spec, manifest, args.raw_dir, registry, queues, export)
    report.update(spec_sha256=spec_digest, input_manifest_sha256=spec["input_manifest_sha256"])
    with args.out.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(f"{SCOPE}, {VINTAGE_LABEL}, queue export {export['status']}: {args.out}")


if __name__ == "__main__":
    main()
