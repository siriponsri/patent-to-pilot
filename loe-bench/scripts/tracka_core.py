"""Prepare the registered Track A core package from local, pre-t0 inputs."""
import argparse
from collections import Counter
from datetime import date, timedelta
from hashlib import sha256
import json
from math import fsum, isclose, isfinite
import os
from pathlib import Path
import platform
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np

import freeze_run as frozen
import l1e_protocol as llm_input
from c9_dev_projection import corroboration_date, evidence, nda_evidence, nda_proofs
from e7_dev_run import dated_brands
from l1dev_local import entity_name, gsrs_names
from scorellm_gpu import load_arms
from scorellm_local import LOCK, PINS, configs

from c9 import inputs as c9_input
from loe_bench import dataset, devx, evidence_graph, k20t1, l1e_prompt, llm_arm, moiety, t1v3, t2
from loe_bench.baselines import AgeHazardTable, Logistic, exclusivity_rule_score
from loe_bench.challenge import ChallengeIdentity, court_rows
from loe_bench.challenge_patents import FilingPatentIndex, PatentChallengeHistory
from loe_bench.common import add_months
from loe_bench.ob_history import OBHistory
from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.piv_history import EntityMatcher, PIVHistory
from loe_bench.review_metrics import ReviewQueue
from loe_bench.seal import ENV_NAME
from loe_bench.t2_features import AsOfBuilder, edition_coverage
from loe_bench.trackA_freeze import _verify_manifest


REPO = frozen.DATA.parents[1]
PRIVATE = Path("C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench")
MANIFEST = "TRACKA_CORE_MANIFEST.json"
T0 = date(2026, 11, 27)
TAG = "loe-S0-input-20261127"
HORIZONS = (12, 24)
ARMS = ("B1", "B3", "M1", "M3")
PIN = "f683017c4fb73aadd91bb97f3381f5dd9308c9ca"
FROZEN_CODE = (
    "baselines", "challenge", "challenge_patents", "common", "dataset", "devx",
    "evidence_graph", "k20t1", "kleene", "moiety", "moiety_linkage", "ob_history",
    "ob_linkage", "piv_history", "review_metrics", "t1v3", "t2", "t2_features", "trackA_freeze",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args):
    return subprocess.check_output(["rtk", "proxy", "git", *args], cwd=REPO)


def network_guard(event, _args):
    if event.startswith("socket."):
        raise RuntimeError(f"Track A preparation forbids network access: {event}")


def check_local_release():
    require(ENV_NAME not in os.environ, "Run Track A with retrospective scoring authorization unset")
    require(not git("status", "--porcelain", "--", "loe-bench"), "Commit LOE-Bench code before execution")
    paths = [f"loe-bench/loe_bench/{name}.py" for name in FROZEN_CODE]
    paths.extend(f"loe-bench/scripts/{name}.py" for name in ("freeze_run", "t1v3_run", "k20t1_run"))
    require(not git("diff", "--name-only", PIN, "HEAD", "--", *paths), "Frozen code differs from the pin")
    require(sha256((frozen.DATA / "OSF_REGISTRATION_P2SMD.json").read_bytes()).hexdigest() == LOCK
            and frozen.read_json("PREREG_LOCK.json")["sha256"] == LOCK, "Registration lock mismatch")
    receipt = REPO / "docs/loe-bench/receipts"
    require("Verdict **PASS**." in (receipt / "GATE.md").read_text(encoding="utf-8")
            and "No deviation from the registered C′ inference procedure." in
            (receipt / "SCORE.md").read_text(encoding="utf-8"), "Missing completed C′ disposition")
    configs()
    c9_input.specification()
    cfg = frozen.read_json("FROZEN_CONFIG.json")
    require(cfg["code_commit_sha"] == PIN
            and cfg["runtime"] == {"python": platform.python_version(), "numpy": np.__version__},
            "Code or CPU runtime differs from the freeze")
    return cfg, git("rev-parse", "HEAD").decode().strip()


def source_inputs(private, cfg, destination):
    pins = cfg["input_sha256"]
    refs = {name: pins[name] for name in ("s0_manifest", "ob_manifest", "piv_manifest", "court_manifest")}
    for source in refs.values():
        require(frozen.manifest(source["file"]) == source, f"Unpinned source manifest: {source['file']}")
    s0_path = frozen.DATA / refs["s0_manifest"]["file"]
    tagged = git("show", f"{TAG}:loe-bench/data/{s0_path.name}")
    require(sha256(tagged).hexdigest() == refs["s0_manifest"]["sha256"], "S0 input tag differs")
    s0 = json.loads(tagged)
    raw = private / "raw-20261127"
    require(_verify_manifest(raw, s0_path, T0, destination) == T0, "S0 observation boundary differs")
    hashes = {item["raw_file"]: item["sha256"] for item in s0["files"]}
    gsrs_pin = pins["gsrs"]
    gsrs = private / "moiety" / gsrs_pin["file"]
    require(c9_input.file_digest(gsrs) == gsrs_pin["sha256"], "GSRS export digest mismatch")
    court = frozen.read_json(refs["court_manifest"]["file"])
    rai = court["rai"]
    documents = court["corroborating_documents"]
    challenge_dir = private / "challenge"
    for source in (rai, rai["metadata"], *documents.values()):
        require(c9_input.file_digest(challenge_dir / source["file"]) == source["sha256"],
                f"Challenge evidence digest mismatch: {source['file']}")
    ob = OBHistory.from_records(frozen.read_json(refs["ob_manifest"]["file"]), private / "ob_editions")
    piv = PIVHistory(frozen.DATA / refs["piv_manifest"]["file"], private / "piv", EntityMatcher([]))
    corroboration = [{**case, **documents[case["document"]]} for case in court["corroborated_cases"]]
    witnesses = tuple(court_rows(challenge_dir / rai["file"], T0 + timedelta(days=1)))
    entities = dataset.build_entities(raw, gsrs_path=gsrs)
    require(all(e.anda_first is None or e.anda_first <= T0 for e in entities.values()),
            "An S0 first final ANDA date exceeds the observation boundary")
    linker = HistoricalMoietyLinker(raw, entities, gsrs_path=gsrs)
    identity = ChallengeIdentity(linker, dated_brands(raw, linker))
    challenge = PatentChallengeHistory(piv, identity, witnesses, rai, corroboration,
                                       FilingPatentIndex(ob, linker))
    builder = AsOfBuilder(ob, linker=linker, challenge=challenge)
    return raw, gsrs, entities, builder, {
        **refs, "s0_tag_object": git("rev-parse", TAG).decode().strip(),
        "s0_tag_commit": git("rev-parse", f"{TAG}^{{commit}}").decode().strip(),
        "s0_fetch_utc": s0["fetched_at_utc"], "s0_raw_sha256": hashes, "gsrs": gsrs_pin,
        "court_sha256": {source["file"]: source["sha256"] for source in
                         (rai, rai["metadata"], *documents.values())},
    }


def schedule(history, horizon):
    result = {}
    for year in range(1995, T0.year + 1):
        day = date(year, 1, 1)
        end = add_months(day, horizon)
        coverage = edition_coverage(history, day)
        status = ("WINDOW_OPEN" if end > T0 else
                  "ELIGIBLE" if coverage["status"] == "FRESH" else f"OB_{coverage['status']}")
        result[day] = {"window_ends": end.isoformat(), "status": status, "orange_book": coverage}
    return tuple(day for day, item in result.items() if item["status"] == "ELIGIBLE"), result


def verify_editions(builder, days):
    audit = {}
    for day in sorted(days):
        source, coverage = builder.select_edition(day)
        require(source is not None and source.identity["kind"] == "fda_zip", f"No eligible FDA ZIP at {day}")
        pin = source.identity
        require(c9_input.file_digest(Path(builder.history.data_dir) / pin["file"]) == pin["sha256"],
                f"FDA ZIP digest mismatch: {pin['file']}")
        piv = builder.challenge._piv(day)[1]
        require(piv["status"] != "UNVERIFIED", f"Selected PIV edition could not be verified at {day}")
        audit[day.isoformat()] = {"orange_book": coverage,
                                 "paragraph_iv": {k: v for k, v in piv.items() if k != "unmatched_examples"}}
    return audit


def forecast_roster(entities):
    dated = [e for e in entities.values() if e.nda_first is not None and e.nda_first <= T0]
    type1 = [e for e in dated if e.flag_at("nme", T0)]
    eligible = sorted((e for e in type1 if e.anda_first is None or e.anda_first > T0), key=lambda e: e.key)
    require(bool(eligible), "The prospective roster is empty")
    rows = [{"key": e.key, "t": T0, "x": dataset.features_at(e, T0)} for e in eligible]
    return rows, {"dated_original_nda": len(dated), "dated_type1": len(type1),
                  "prior_final_anda": len(type1) - len(eligible), "eligible": len(eligible),
                  "low_confidence_identity": sum(e.key_confidence == "LOW_CONFIDENCE" for e in eligible)}


def add_predictors(rows, builder, horizon):
    sources = {day: builder.select_edition(day)[0] for day in {row["t"] for row in rows}}
    for row in rows:
        key, day = row["key"], row["t"]
        asof = builder.build(key, day, horizon, row["x"])
        source = sources[day]
        products = builder._indexes[source].linked_products.get(builder.linker.canonical(key), ())
        row.update(asof=asof, breadth=devx.presentation_breadth(products, source.edition_date))


def calibrate(train, horizon):
    """Use FREEZE's five-fold whole-drug algorithm on newly matured TRAIN windows."""
    day = max(row["t"] for row in train)
    inner = [row for row in train if row["t"] == day]
    groups = [t2._fold(row["key"]) for row in inner]
    scores = {arm: [None] * len(inner) for arm in t1v3.ARMS}
    counts = {}
    for fold in sorted(set(groups)):
        fit = [row for row in train if t2._fold(row["key"]) != fold]
        held = [i for i, group in enumerate(groups) if group == fold]
        native = frozen.t1.native(fit, [inner[i] for i in held], horizon, T0)
        counts[str(fold)] = {"fit_rows": len(fit), "held_rows": len(held)}
        for arm, probabilities in native.items():
            for i, probability in zip(held, probabilities, strict=True):
                scores[arm][i] = probability
    labels = [row["y"] for row in inner]
    verdicts = [row["asof"].verdict for row in inner]
    calibrators, policies = {}, {}
    for arm, native in scores.items():
        x = frozen.t1.calibrator_inputs(native)
        calibrator = Logistic(feats=("logit",)).fit(t2._with_labels(x, inner))
        p = calibrator.predict(x)
        lo, hi = t1v3.choose_thresholds(p, labels, [arm == "M3" and v == "BLOCKED" for v in verdicts])
        decisions = [t1v3.action(arm, row, horizon, value, lo, hi)[0]
                     for row, value in zip(inner, p, strict=True)]
        flags = decisions.count(evidence_graph.PREDICT_ENTRY)
        clears = decisions.count(evidence_graph.PREDICT_NO_ENTRY)
        misses = sum(y for y, action in zip(labels, decisions, strict=True)
                     if action == evidence_graph.PREDICT_NO_ENTRY)
        require(flags <= len(inner) // 5 and (not clears or misses / clears <= t1v3.CLEAR_EVENT_LIMIT),
                "Inner policy exceeds the registered flag or missed-clear target")
        legacy = k20t1.choose_operating_points("M3" if arm == "M3" else "M1", p, verdicts)[-1]
        calibrators[arm] = calibrator
        policies[arm] = {"lo": lo, "hi": hi, "legacy_90": legacy, "inner_flags": flags,
                         "inner_clears": clears, "inner_misses": misses}
    return calibrators, policies, {"cutoff": day.isoformat(), "rows": len(inner), "events": sum(labels),
                                   "fold_counts": counts, "flag_capacity": len(inner) // 5}


def logistic_parameters(model):
    return {"features": model.feats, "mean": model.mu, "scale": model.sd, "weight": model.w,
            "intercept": model.b, "l2": model.l2, "epochs": model.epochs, "learning_rate": model.lr}


def core_models(train, forecast, b3_clocks, horizon, cfg):
    calibrators, policies, inner = calibrate(train, horizon)
    b1 = AgeHazardTable().fit(train)
    train_age, age = b1.predict(train), b1.predict(forecast)
    native = {"B1": age, "B3": [exclusivity_rule_score(b3_clocks.get(row["key"], {}), T0, horizon)
                               for row in forecast]}
    fitted = {"B1": {"base": b1.base, "bin_rates": b1.rate, "bin_years": b1.bw,
                     "max_age": b1.max_age, "prior_strength": b1.m}}
    for arm in ("M1", "M3"):
        tr = devx.model_inputs(train, train_age, arm, frozen.t1.FLAGS)
        va = devx.model_inputs(forecast, age, arm, frozen.t1.FLAGS)
        model = Logistic(l2=devx.L2, feats=cfg["features"][arm]).fit(t2._with_labels(tr, train))
        native[arm] = model.predict(va)
        fitted[arm] = logistic_parameters(model)
    calibrated = {arm: calibrator.predict(frozen.t1.calibrator_inputs(native[arm]))
                  for arm, calibrator in calibrators.items()}
    fitted["calibration"] = {arm: logistic_parameters(model) for arm, model in calibrators.items()}
    fitted["policies"] = policies
    return native, calibrated, fitted, inner


def queue_allocation(scores, days):
    require(all(isfinite(p) and 0 <= p <= 1 for p in scores), "Invalid forecast risk")
    weights, slots = ReviewQueue(scores, days).allocation(np.ones(len(scores), dtype=int))
    require(slots == len(scores) // 5 and isclose(fsum(weights), slots, abs_tol=1e-10),
            "Forecast queue failed expected capacity")
    boundary = sorted(scores, reverse=True)[slots - 1] if slots else None
    above = sum(score > boundary for score in scores) if slots else 0
    tied = scores.count(boundary)
    return weights.tolist(), {"capacity": slots, "boundary_native_score": boundary, "above_boundary": above,
                              "boundary_rows": tied, "slots_at_boundary": slots - above,
                              "boundary_inclusion_probability": (slots - above) / tied if tied else None}


def distribution(values):
    return {key: float(value) for key, value in zip(("min", "p25", "median", "p75", "max"),
                                                    np.quantile(values, [0, .25, .5, .75, 1]), strict=True)}


def predictions(roster, forecast, horizon, native, calibrated, policies):
    report = {}
    rows = [dict(row, arms={}) for row in roster]
    for arm in ARMS:
        scores = native[arm]
        weights, queue = queue_allocation(scores, [T0] * len(rows))
        probabilities = calibrated.get(arm)
        decisions = [(None, None)] * len(rows)
        if probabilities is not None:
            require(all(isfinite(p) and 0 <= p <= 1 for p in probabilities), "Invalid calibrated risk")
            policy = policies[arm]
            decisions = [t1v3.action(arm, row, horizon, p, policy["lo"], policy["hi"])
                         for row, p in zip(forecast, probabilities, strict=True)]
        for i, (action, conflict) in enumerate(decisions):
            rows[i]["arms"][arm] = {"native": scores[i], "calibrated": probabilities[i] if probabilities else None,
                                    "queue_inclusion_probability": weights[i], "diagnostic_action": action,
                                    "graph_conflict": conflict}
        report[arm] = {"queue": queue, "native": distribution(scores),
                       "calibrated": distribution(probabilities) if probabilities is not None else None,
                       "diagnostic_actions": dict(Counter(action for action, _ in decisions)) if probabilities else None}
    return rows, report


def prompt_evidence(row, builder, nda_records, inputs):
    # The S0 acquisition day is conservative proof of availability for its dated NDA fields.
    yield from (dict(item, available_on=T0.isoformat()) for item in
                nda_proofs(nda_records[row["key"]], T0, inputs["s0_raw_sha256"], T0.isoformat()))
    gsrs = inputs["gsrs"]
    for part in row["key"].split("|"):
        if part.startswith("U:"):
            yield evidence(gsrs["file"], "2026-08-06", gsrs["sha256"], f"approvalID {part[2:]}",
                           date(2026, 8, 6), T0)
    source, coverage = builder.select_edition(T0)
    key = builder.linker.canonical(row["key"])
    index = builder._indexes[source]
    products = index.linked_products.get(key, ())
    patents, exclusivities = index.records(key)
    locators = [entry["locator"] for entry in (*products, *(patents or ()), *(exclusivities or ()))]
    locator = "; ".join(locators) or f"products table, no linked NDA presentation under FIX2c for {key}"
    proof = coverage["availability_proof"]
    pin = source.identity
    yield evidence(pin["file"], source.edition_date.isoformat(), pin["sha256"],
                   f"{locator}; availability {proof['url']}", source.edition_date, date.fromisoformat(proof["date"]))
    for witness in row["asof"].challenge.witnesses:
        yield evidence(witness.source, witness.version, witness.sha256, witness.locator, witness.date, T0)
        if witness.source == "RAI_COURT":
            doc = witness.corroboration
            date_bound = corroboration_date(doc)
            locator = doc["locator"]
            if date_bound is None:
                # E7 records the FDA approval package's year, with no publication day.
                date_bound = date(int(doc["version"].rsplit(", ", 1)[1]), 12, 31)
                locator += "; edition year upper bound"
            yield evidence(doc["file"], doc["version"], doc["sha256"], locator, date_bound, T0)
        elif witness.source == "RAI_OB_PATENT":
            for match in witness.corroboration["matches"]:
                listing = match["orange_book"]
                proof = listing["availability_proof"]
                yield evidence(listing["file"], listing["edition_date"], listing["sha256"],
                               f"{listing['locator']}; availability {proof['url']}",
                               date.fromisoformat(listing["edition_date"]), date.fromisoformat(proof["date"]))


def write_json(path, value):
    raw = (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    path.write_bytes(raw)


def export_prompts(out, roster, features, raw, gsrs, builder, inputs):
    required = {part[2:] for row in roster for part in row["key"].split("|") if part.startswith("U:")}
    names = gsrs_names(gsrs, required)
    forecasts = [{"entity": entity_name(row["key"], names), "t0": row["t0"],
                  "horizon_months": row["horizon_months"]} for row in roster]
    enriched = [dict(item, as_of_evidence=l1e_prompt.from_m3(row))
                for item, row in zip(forecasts, features, strict=True)]
    counts = Counter(row["horizon_months"] for row in roster)
    plan = {"registration_sha256": LOCK, "config_lf_sha256": PINS, "rows": len(roster),
            "cutoffs": {str(h): {T0.isoformat(): counts[h]} for h in HORIZONS}, "arms": {}}
    roster_bytes = llm_input.jsonl(roster)
    (out / "roster.jsonl").write_bytes(roster_bytes)
    plan["roster_sha256"] = sha256(roster_bytes).hexdigest()
    for arm, stem, rows, renderer in (
        ("L1", "L1DEV", forecasts, llm_arm.build_prompt),
        ("L1e", "L1E", enriched, l1e_prompt.build_prompt),
    ):
        data = llm_input.jsonl(rows)
        messages = llm_input.jsonl(map(renderer, rows))
        (out / f"{stem}_inputs.jsonl").write_bytes(data)
        (out / f"{stem}_messages.jsonl").write_bytes(messages)
        plan["arms"][arm] = {"input_sha256": sha256(data).hexdigest(),
                             "messages_sha256": sha256(messages).hexdigest()}
    write_json(out / "manifest.json", plan)
    load_arms(out, frozen.DATA)

    orange = moiety.orange_products(raw)
    trace = {"registry": builder.linker.registry, "orange": orange, "reader": dataset.read_jsonl,
             "linkage": dataset.build_moiety_linkage(raw, builder.linker.registry, orange)}
    nda_records = nda_evidence(raw, trace)
    c9_rows = [{"drug_key": row["key"], "forecast": item,
                "provenance": {"as_of": list(prompt_evidence(row, builder, nda_records, inputs))}}
               for item, row in zip(enriched, features, strict=True) if item["horizon_months"] == 24]
    projection = out / "C9_track_a.json"
    c9_input.write_json(projection, {"schema": "c9-track-a-v1", "rows": c9_rows,
                                    "s0_manifest_lf_sha256": inputs["s0_manifest"]["sha256"]})
    projection_hash = c9_input.file_digest(projection)
    checked = c9_input.track_rows(c9_input.load_projection(projection, projection_hash, training=False))
    require([row["drug_key"] for row in checked] == [row["key"] for row in roster if row["horizon_months"] == 24],
            "C9 and core ordered drug keys disagree")
    expected = [l1e_prompt.build_prompt(item) for item in enriched if item["horizon_months"] == 24]
    require([row["messages"] for row in checked] == expected, "C9 and 24-month L1e messages disagree")
    c9_messages = out / "C9_messages.jsonl"
    c9_messages.write_bytes(c9_input.jsonl_bytes(expected))
    return {**plan, "C9": {"projection_sha256": projection_hash, "rows": len(checked),
                           "keys_sha256": c9_input.digest(c9_input.jsonl_bytes(
                               [row["drug_key"], row["t0"]] for row in checked)),
                           "messages_sha256": c9_input.file_digest(c9_messages),
                           "spec_lf_sha256": c9_input.SPEC_SHA256}}


def prepare(private, out):
    require(not any(out.iterdir()), f"Nonempty Track A staging directory: {out}")
    cfg, revision = check_local_release()
    raw, gsrs, entities, builder, inputs = source_inputs(private, cfg, out)
    calendars = {h: schedule(builder.history, h) for h in HORIZONS}
    days = {T0} | {day for chosen, _ in calendars.values() for day in chosen}
    edition_audit = verify_editions(builder, days)
    base_roster, eligibility = forecast_roster(entities)
    roster, features, models, summaries = [], [], {}, {}
    b3_clocks = dataset.snapshot_features(raw, T0, entities, gsrs_path=gsrs)
    for horizon, (chosen, calendar) in calendars.items():
        print(f"{horizon}m: fit frozen models on {len(chosen)} matured annual cutoffs", flush=True)
        train = dataset.build_samples(entities, chosen, horizon, T0)
        require({row["t"] for row in train} == set(chosen)
                and len(train) == len({(r["t"], r["key"]) for r in train})
                and {row["y"] for row in train} == {0, 1}, "Missing, duplicate or single-class TRAIN")
        forecast = [dict(row) for row in base_roster]
        add_predictors(train, builder, horizon)
        add_predictors(forecast, builder, horizon)
        native, calibrated, fitted, inner = core_models(train, forecast, b3_clocks, horizon, cfg)
        identities = [{"key": row["key"], "t0": T0.isoformat(), "horizon_months": horizon} for row in forecast]
        per_row, stats = predictions(identities, forecast, horizon, native, calibrated, fitted["policies"])
        roster.extend(identities)
        features.extend(forecast)
        models[str(horizon)] = fitted
        (out / f"core_predictions_{horizon}m.jsonl").write_bytes(llm_input.jsonl(per_row))
        summary = {day.isoformat(): detail for day, detail in calendar.items()}
        for row in train:
            item = summary[row["t"].isoformat()]
            item["rows"] = item.get("rows", 0) + 1
            item["events"] = item.get("events", 0) + row["y"]
        summaries[str(horizon)] = {
            "roster_rows": len(forecast), "training_rows": len(train), "training_events": sum(r["y"] for r in train),
            "training_drugs": len({r["key"] for r in train}), "training_windows": summary,
            "inner_calibration": inner, "policy_thresholds": fitted["policies"], "arms": stats,
            "orange_book_row_status": dict(Counter(r["asof"].edition_status for r in forecast)),
            "graph_verdicts": dict(Counter(r["asof"].verdict for r in forecast)),
            "challenge_state": dict(Counter(r["asof"].challenge.state.name for r in forecast)),
        }
    write_json(out / "fitted_models.json", {"horizons": models, "model_settings": cfg["model_settings"],
                                           "B3": {"rule": "all recorded S0 expiry dates <= horizon end"}})
    prompts = export_prompts(out, roster, features, raw, gsrs, builder, inputs)
    result = {
        "status": "CPU_CORE_PREPARED", "t0": T0.isoformat(), "code_commit_sha": revision,
        "registered_pipeline_commit_sha": PIN, "registration_sha256": LOCK, "runtime": cfg["runtime"],
        "cpu_only": True, "network": "PYTHON_SOCKET_OPERATIONS_DENIED", "inputs": inputs,
        "edition_audit": edition_audit, "eligibility": eligibility, "horizons": summaries, "prompts": prompts,
        "b3_s0_snapshot_rows": sum(row["key"] in b3_clocks for row in base_roster),
        "files_sha256": {p.name: c9_input.file_digest(p) for p in sorted(out.iterdir())},
    }
    write_json(out / MANIFEST, result)
    sums = [f"{c9_input.file_digest(path)}  {path.name}\n" for path in sorted(out.iterdir())]
    (out / "SHA256SUMS").write_bytes("".join(sums).encode("ascii"))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--private", type=Path, default=PRIVATE)
    args = parser.parse_args()
    sys.addaudithook(network_guard)
    private = args.private.resolve()
    target = private / "trackA"
    require(not target.exists(), f"Existing Track A directory: {target}")
    with TemporaryDirectory(prefix="trackA-stage-", dir=private) as temporary:
        staged = Path(temporary) / "outputs"
        staged.mkdir()
        result = prepare(private, staged)
        require(not target.exists(), f"Concurrent Track A output: {target}")
        staged.rename(target)
    print(f"Prepared {result['eligibility']['eligible']} rows per horizon in {target}", flush=True)


if __name__ == "__main__":
    main()
