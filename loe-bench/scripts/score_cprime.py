"""Execute the authorized C-prime card against byte-verified local inputs."""

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from hashlib import file_digest, sha256
import json
from math import isclose
import os
from pathlib import Path
import platform
import subprocess
from unittest.mock import patch
from zipfile import ZipFile

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

import freeze_run as frozen
import e7_dev_run
import t4_power
from c3_dev_guard import nda_reader
from c3_edition_applicants import Listing
from c3_dev_run import WindowApplicants, _comparison, _historical_identity
from freeze_dev_scores import require_match
from freeze_gate import verified_cutoffs
from osf_lock import API, canonical_record, fetch

import numpy as np

from loe_bench import c3, dataset, moiety, ob_linkage
from loe_bench.baselines import AgeHazardTable, Logistic
from loe_bench.challenge import ChallengeIdentity, court_rows
from loe_bench.challenge_patents import FilingPatentIndex, PatentChallengeHistory
from loe_bench.common import add_months, read_jsonl
from loe_bench.piv_history import EntityMatcher, PIVHistory
from loe_bench.seal import ENV_NAME, require_cutoffs
from loe_bench.t2_features import AsOfBuilder, edition_coverage


DATA = frozen.DATA
REPO = DATA.parents[1]
PRIVATE = Path("C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench")
PIN = "f683017c4fb73aadd91bb97f3381f5dd9308c9ca"
LOCK = "3f91145251465b0ed9c89233337748e1b9fd84db8c4c2a6158860374670e1c77"
DIGESTS = {
    "FROZEN_CONFIG.json": "d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39",
    "S0_INPUT_MANIFEST.json": "7d40be5e2004d887480ce5f337afffd611909f26017622e90ad304a0386d2d1d",
    "C3_SPEC.json": "8179101bb7a0adf9e8659bcb0978c73bd32ee869506a50027537741a45e3b0fd",
    "C4_SPEC.json": "c0644bb4c1ed9d6050e256191c85bb34dd120a73b6da78850a1faf80e2c400f0",
}
UPDATES = ("6b0a5e871c2cd96b1746bce7", "6b0a61a4341762fcbae66946")
ARMS = frozen.ARMS
DRAWS, SEED, ALPHA = 2000, 20261127, 0.025
MISSING = (*frozen.MODEL_FEATURES, *frozen.CHALLENGE_FEATURES, *frozen.devx.BREADTH)


def verify(condition, detail):
    if not condition:
        raise ValueError(detail)


def checked_json(name, digest):
    data = (DATA / name).read_bytes().replace(b"\r\n", b"\n")
    verify(sha256(data).hexdigest() == digest, f"{name} LF digest mismatch")
    return json.loads(data)


def raw_digest(path):
    with path.open("rb") as source:
        return file_digest(source, "sha256").hexdigest()


def check_raw(path, digest):
    verify(raw_digest(path) == digest, f"Digest mismatch for {path.name}")


def git(*args):
    return subprocess.check_output(["rtk", "proxy", "git", *args], cwd=REPO).decode().strip()


def release(args):
    cfg, s0, competition, c4spec = (checked_json(name, digest) for name, digest in DIGESTS.items())
    verify(cfg["code_commit_sha"] == PIN, "FREEZE implementation pin differs")
    verify(cfg["runtime"] == {"python": platform.python_version(), "numpy": np.__version__},
           "Pinned Python or NumPy version differs")
    # Verify the original implementation's runtime tree at the blob level.
    changes = git("diff", "--name-status", PIN, "--", "loe-bench/loe_bench", "loe-bench/scripts")
    verify(all(line.startswith("A\t") or (
        line.startswith("M\t") and Path(line.split("\t")[1]).name in
        {"freeze_gate.py", "llm_arm.py", "llm_arm_run.py", "test_llm_arm.py"})
        for line in changes.splitlines()), "Changed code in the frozen runtime")
    verify(git("branch", "--show-current") == "loe/SCORE", "Require assigned SCORE branch")
    verify(git("merge-base", "HEAD", "e0f1872e").startswith("e0f1872e"), "Unexpected branch base")
    note = (REPO / "docs/maintenance/OWNER-DECISIONS-20261122.md").read_text(encoding="utf-8")
    gate = (REPO / "docs/loe-bench/receipts/GATE.md").read_text(encoding="utf-8")
    verify("as first author, the owner authorized opening the sealed test" in note
           and "Verdict **PASS**." in gate and LOCK in gate, "Owner authorization or custodian PASS absent")

    reg = fetch(API)["data"]
    replies = fetch(API + "schema_responses/")["data"]
    states = {reply["id"]: reply["attributes"]["reviews_state"] for reply in replies}
    verify(reg["id"] == "p2smd" and reg["attributes"]["public"] and not reg["attributes"]["withdrawn"]
           and reg["attributes"]["date_registered"].startswith("2026-11-28T03:59:")
           and reg["attributes"]["reviews_state"] == "accepted"
           and reg["relationships"]["latest_response"]["data"]["id"] == UPDATES[-1]
           and all(states.get(update) == "approved" for update in UPDATES), "OSF release differs")
    canonical = canonical_record()
    verify(sha256(canonical).hexdigest() == LOCK and json.loads(canonical)["doi"] == "10.17605/OSF.IO/P2SMD"
           and (DATA / "OSF_REGISTRATION_P2SMD.json").read_bytes() == canonical
           and frozen.read_json("PREREG_LOCK.json")["sha256"] == LOCK, "Registration lock differs")
    verify(ENV_NAME not in os.environ, "Require a process with no inherited seal authorization")

    refs = cfg["input_sha256"]
    manifests = {key: checked_json(ref["file"], ref["sha256"])
                 for key, ref in refs.items() if key.endswith("_manifest")}
    end = date.fromisoformat(s0["t0"])
    verify(end.isoformat() == cfg["sealed_test"]["outcomes_observed_through"] == "2026-11-27",
           "S0 observation end differs")
    schedule = {h: [date(year, 1, 1) for year in range(2017, 2026 if h == 12 else 2025)]
                for h in (12, 24)}
    history = frozen.OBHistory.from_records(manifests["ob_manifest"], str(args.ob_dir))
    for h, days in schedule.items():
        verify([d.isoformat() for d in days] == cfg["sealed_test"]["schedule"][str(h)]["test_cutoffs"]
               and add_months(days[-1], h) <= end
               and verified_cutoffs(history, days, args.ob_dir), f"{h}m cutoff release failed")
    c3_days = competition["sealed_test"]["cutoffs"]
    verify(c3_days == [f"{year}-01-01" for year in range(2017, 2024)]
           and competition["frozen_queue"]["config_sha256"] == DIGESTS["FROZEN_CONFIG.json"],
           "C3 schedule or FREEZE digest differs")
    for row in s0["files"]:
        check_raw(args.raw / row["raw_file"], row["sha256"])
    for row in manifests["ob_manifest"]["editions"]:
        check_raw(args.ob_dir / row["file"], row["sha256"])
    for row in manifests["piv_manifest"]["editions"]:
        if row["parse_status"] == "PASS":
            check_raw(args.piv_dir / row["file"], row["sha256"])
    court = manifests["court_manifest"]
    for row in (court["rai"], court["rai"]["metadata"], *court["corroborating_documents"].values()):
        check_raw(args.challenge_dir / row["file"], row["sha256"])
    check_raw(args.raw.resolve().parent / "moiety" / refs["gsrs"]["file"], refs["gsrs"]["sha256"])
    c4_inputs = checked_json(c4spec["input_manifest"], c4spec["input_manifest_sha256"])
    audit = {"status": "PASS", "base": git("rev-parse", "HEAD"), "osf_id": reg["id"],
             "checked_at_utc": datetime.now(timezone.utc).isoformat(),
             "doi": json.loads(canonical)["doi"], "registered_utc": reg["attributes"]["date_registered"],
             "approved_schema_responses": list(UPDATES), "latest_schema_response": UPDATES[-1],
             "canonical_prereg_sha256": LOCK, "lock_wrapper_sha256": raw_digest(DATA / "PREREG_LOCK.json"),
             "first_author_authorization": "PASS", "custodian_gate": "PASS",
             "config_and_manifest_lf_sha256": DIGESTS, "implementation_pin": PIN,
             "scoring_adapter_sha256": raw_digest(Path(__file__)),
             "runtime": cfg["runtime"], "source_checks": "PASS", "cutoff_edition_checks": "PASS",
             "observation_end": end.isoformat(), "cpu_only": True}
    return cfg, s0, competition, c4_inputs, manifests, end, schedule, history, audit


def fit_development(args, cfg):
    """Recreate final development fits and verify their predictions while the seal is closed."""
    verify(ENV_NAME not in os.environ, "Development replay requires disabled authorization")
    replay = frozen.t1.replay
    reader = replay.read_jsonl

    def guarded(path):
        return nda_reader(path, reader, projector=t4_power, redact_dates=replay.without_later_approvals)

    with patch.object(replay, "read_jsonl", guarded), patch.object(e7_dev_run, "read_jsonl", guarded):
        entities, builder, _ = replay.inputs(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir)
    reference = checked_json("FREEZE_dev_report.json", cfg["development_report_sha256"])
    export_refs = frozen.read_json("FREEZE_DEV_SCORES_MANIFEST.json")
    fits = {}
    for h, (train_days, val_days) in replay.PRIMARY.items():
        settings = cfg["horizons"][str(h)]
        observed = min(val_days) - timedelta(days=1)
        frozen.t1.verify_windows(train_days, val_days, h)
        train = replay.partition(entities, builder, train_days, h, training=True)
        calibrators, policies, inner = frozen.inner_fits(train, h, observed)
        require_match({"train_cutoffs": [d.isoformat() for d in train_days],
                       "train_rows": len(train), "train_labels_observed_through": observed.isoformat(),
                       "validation_cutoffs": [d.isoformat() for d in val_days], "inner": inner,
                       "arms": policies}, settings, f"{h}m TRAIN")
        # Same B1 and K07 logistic fit steps as pinned devx.raw_predictions.
        b1 = AgeHazardTable().fit(train)
        age = b1.predict(train)
        models = {arm: Logistic(l2=frozen.devx.L2, feats=cfg["features"][arm]).fit(
            frozen.t2._with_labels(frozen.devx.model_inputs(train, age, arm, frozen.t1.FLAGS), train))
            for arm in ("M1", "M3")}
        validation = replay.partition(entities, builder, val_days, h)
        native = predict(b1, models, validation)
        expected = export_refs["exports"][str(h)]
        path = Path(expected["path"])
        check_raw(path, expected["sha256"])
        published = json.loads(path.read_bytes())["rows"]
        actual = [{"key": row["key"], "cutoff": row["t"].isoformat(),
                   **{arm: native[arm][i] for arm in ("B1", "M3")}}
                  for i, row in enumerate(validation)]
        require_match(actual, published, f"{h}m published native scores")
        panel = frozen.t1v3.QueuePanel(validation, val_days, native)
        point = panel.evaluate(np.ones(len(panel.keys), dtype=int))
        for arm in ARMS:
            require_match(point["arms"][arm], reference["horizons"][str(h)]["arms"][arm],
                          f"{h}m {arm} development queue")
        fits[h] = (b1, models, calibrators, policies)
    return fits


def predict(b1, models, rows):
    age = b1.predict(rows)
    native = {"B1": age}
    for arm, model in models.items():
        native[arm] = model.predict(frozen.devx.model_inputs(rows, age, arm, frozen.t1.FLAGS))
    return native


def test_inputs(args, history, court, end, days):
    require_cutoffs(days)
    gsrs = args.raw.resolve().parent / "moiety" / moiety.GSRS_FILE
    registry = moiety.registry_for(args.raw, gsrs)
    orange = moiety.orange_products(args.raw)
    linkage = dataset.build_moiety_linkage(args.raw, registry, orange)
    entities = dataset.build_entities(args.raw, gsrs_path=gsrs)
    linker = ob_linkage.HistoricalMoietyLinker(args.raw, entities, gsrs_path=gsrs)
    identity = ChallengeIdentity(linker, frozen.t1.replay.dated_brands(args.raw, linker))
    piv = PIVHistory(DATA / "PIV_EDITIONS.json", args.piv_dir, EntityMatcher([]))
    rai = court["rai"]
    corroboration = [{**item, **court["corroborating_documents"][item["document"]]}
                     for item in court["corroborated_cases"]]
    witnesses = court_rows(args.challenge_dir / rai["file"], max(days) + timedelta(days=1))
    challenge = PatentChallengeHistory(piv, identity, witnesses, rai, corroboration,
                                       FilingPatentIndex(history, linker))
    verify(all(e.anda_first is None or e.anda_first <= end for e in entities.values()),
           "S0 ANDA date exceeds observation end")
    return entities, AsOfBuilder(history, linker=linker, challenge=challenge), registry, orange, linkage


def test_rows(entities, builder, days, h, end):
    require_cutoffs(days)
    rows = dataset.build_samples(entities, days, h, end)
    verify(set(days) == {r["t"] for r in rows} and len(rows) == len({(r["key"], r["t"]) for r in rows}),
           "Incomplete or duplicate C-prime roster")
    audit = {}
    for day in days:
        coverage = edition_coverage(builder.history, day)
        verify(coverage["status"] == "FRESH", "C-prime cutoff without fresh evidence")
        source, _ = builder.history.available_source_asof(day)
        group = [row for row in rows if row["t"] == day]
        for row in group:
            row["asof"] = builder.build(row["key"], day, h, row["x"])
            products = builder._indexes[source].linked_products.get(builder.linker.canonical(row["key"]), ())
            row["breadth"] = frozen.devx.presentation_breadth(products, source.edition_date)
        dated = [e for e in entities.values() if e.nda_first and e.nda_first <= day]
        nme = [e for e in dated if e.flag_at("nme", day)]
        prior = sum(e.anda_first is not None and e.anda_first <= day for e in nme)
        verify(len(group) == len(nme) - prior, "C-prime eligibility reconciliation failed")
        audit[day.isoformat()] = {
            "dated_nda_drugs": len(dated), "no_eligible_type1": len(dated) - len(nme),
            "prior_final_anda": prior, "eligible_rows": len(group),
            "events": sum(row["y"] for row in group), "orange_book_edition": coverage,
            "orange_book_status": dict(Counter(row["asof"].edition_status for row in group)),
            "graph_verdict": dict(Counter(row["asof"].verdict for row in group)),
            "missing_features": {name: sum(int(row["asof"].x[name] if name in row["asof"].x
                                               else row["breadth"][name]) for row in group)
                                 for name in MISSING if name.endswith("_missing")},
            "low_confidence_keys": sum(entities[row["key"]].key_confidence == "LOW_CONFIDENCE" for row in group),
        }
    return rows, audit


def interval(point, draws):
    bad = int(np.count_nonzero(~np.isfinite(draws)))
    point = float(point) if np.isfinite(point) else None
    return {"estimate": point, "undefined_draws": bad,
            "ci95": np.quantile(draws, (ALPHA, 1 - ALPHA), method="linear").tolist()
            if point is not None and not bad else None}


def score_panel(rows, days, h, scores, probabilities, policies, eligibility, young):
    require_cutoffs(days)
    times = np.asarray([row["t"] for row in rows])
    keys, groups = np.unique(np.asarray([row["key"] for row in rows], dtype=str), return_inverse=True)
    labels = np.asarray([row["y"] for row in rows], dtype=int)
    positive = labels == 1
    event_groups = np.unique(groups[positive])
    verify(all(len(p) == len(rows) and np.isfinite(p).all() and all(0 <= s <= 1 for s in p)
               for p in (*scores.values(), *probabilities.values())), "Nonfinite or invalid risk")
    secondary = {arm: frozen.Secondary(rows, h, arm, scores[arm], probabilities[arm], policies[arm])
                 for arm in ARMS}
    harmonic = frozen.power.harmonic_numbers(len(keys) * len(days))
    by_day = {day: np.flatnonzero(times == day) for day in days}

    def measure(copies, summarize=False):
        weights = copies[groups]
        events = int(weights @ labels)
        event_drugs = int(copies[event_groups].sum())
        expected = {day: int(weights[ix].sum()) // 5 for day, ix in by_day.items()}
        values, details = [], {}
        for arm in ARMS:
            operations = secondary[arm]
            shares, slots = operations.queue.allocation(weights)
            verify(slots == sum(expected.values()) and all(
                isclose(float(shares[ix] @ weights[ix]), expected[day], rel_tol=0, abs_tol=1e-9)
                for day, ix in by_day.items()), "Sampled queue capacity mismatch")
            hits = float(shares @ (weights * labels))
            missed = np.ones(len(keys))
            np.multiply.at(missed, groups[positive], 1 - shares[positive])
            distinct = float((1 - missed) @ copies)
            values.append([hits / events if events else np.nan,
                           hits / slots if slots else np.nan,
                           distinct / event_drugs if event_drugs else np.nan,
                           *operations.measure(weights, harmonic)])
            if summarize:
                details[arm] = {"expected_queued_events": hits, "expected_captured_event_drugs": distinct,
                                "cutoffs": {day.isoformat(): {
                                    "slots": expected[day], "expected_queued_events": float(shares[ix] @ labels[ix]),
                                    "boundary_tie_rows": int(((shares[ix] > 0) & (shares[ix] < 1)).sum()),
                                } for day, ix in by_day.items()}}
                if young is not None:
                    numerator = float(shares[young] @ labels[young])
                    denominator = int(labels[young].sum())
                    details[arm]["young_cohort"] = {"cutoff": "2024-01-01", "rows": int(young.sum()),
                        "events": denominator, "expected_hits": numerator,
                        "recall": numerator / denominator if denominator else None}
        return np.asarray(values), details

    points, details = measure(np.ones(len(keys), dtype=int), summarize=True)
    rng = np.random.default_rng(SEED)
    draws = np.stack([measure(np.bincount(rng.integers(len(keys), size=len(keys)),
                                         minlength=len(keys)))[0] for _ in range(DRAWS)])
    levels = {arm: {name: interval(points[i, j], draws[:, i, j])
                    for j, name in enumerate(frozen.METRICS)} for i, arm in enumerate(ARMS)}
    contrasts = {}
    for left, right in frozen.t1v3.PAIRS:
        a, b = ARMS.index(left), ARMS.index(right)
        contrasts[f"{left}-{right}"] = {
            name: interval(points[a, j] - points[b, j], draws[:, a, j] - draws[:, b, j])
            for j, name in enumerate(frozen.METRICS)}
    for arm in ARMS:
        p, policy = probabilities[arm], policies[arm]
        legacy, conflicts = frozen.k20t1.apply_policy(arm, rows, p, h, policy["legacy_90"]["threshold"])
        details[arm]["legacy_policy_90"] = frozen.legacy_summary(legacy, labels, conflicts)
        details[arm]["ece_bin_counts"] = np.bincount(secondary[arm].ece_bins, minlength=10).tolist()
        for day, ix in by_day.items():
            details[arm]["cutoffs"][day.isoformat()].update(
                native_mean=float(np.asarray(scores[arm])[ix].mean()),
                calibrated_mean=float(np.asarray(p)[ix].mean()),
                event_rate=float(labels[ix].mean()),
            )
        actions = [frozen.t1v3.action(arm, row, h, risk, policy["lo"], policy["hi"])
                   for row, risk in zip(rows, p, strict=True)]
        values = np.asarray([action for action, _ in actions])
        g = frozen.graph
        clear, flag, refer = (values == name for name in (g.PREDICT_NO_ENTRY, g.PREDICT_ENTRY, g.ABSTAIN))
        counts = {name: int(mask.sum()) for name, mask in (("clear", clear), ("flag", flag), ("refer", refer))}
        misses = int(labels[clear].sum())
        safety = frozen.t1v3.clear_rate_ci(labels[clear], keys[groups[clear]])
        details[arm]["asymmetric_policy"] = {
            "rows": counts, "rates": {key: value / len(rows) for key, value in counts.items()},
            "flag_events": int(labels[flag].sum()), "referred_events": int(labels[refer].sum()),
            "conflict_referrals": sum(conflict for _, conflict in actions),
            "missed_clear_events": misses,
            "missed_clear_rate": misses / counts["clear"] if counts["clear"] else None,
            "missed_clear_ci95": safety, "auto_clear_safety": "UNEVALUABLE" if safety is None else
            ("PASS" if safety[1] <= 0.03 else "FAIL"),
        }
    report = {"rows": len(rows), "drug_clusters": len(keys), "event_rows": int(labels.sum()),
              "event_drugs": len(event_groups), "slots": sum(len(ix) // 5 for ix in by_day.values()),
              "eligibility_and_coverage": eligibility, "arms": details, "levels": levels,
              "contrasts": contrasts, "bootstrap_draws": DRAWS, "bootstrap_seed": SEED,
              "undefined_draws_any_metric": int(np.count_nonzero(~np.isfinite(draws).all(axis=(1, 2)))),
              "undefined_draws_recall_cause": "no event rows"}
    return report, draws


def primary(reports):
    result, reached = {}, True
    for name, (h, pair) in frozen.t1.HYPOTHESES.items():
        x = reports[str(h)]["contrasts"][pair]["recall"]
        lower = x["ci95"][0] if x["ci95"] else None
        decision = "NOT_REACHED_DESCRIPTIVE"
        if reached:
            decision = "UNEVALUABLE" if lower is None else ("PASS" if lower > 0 else "FAIL")
        result[name] = {"horizon_months": h, "contrast": pair, **x, "one_sided_lower": lower,
                        "reached": reached, "decision": decision, "meets_plus_10pp":
                        x["estimate"] >= 0.10 if x["estimate"] is not None else None}
        reached = reached and decision == "PASS"
    return result


def collect_listings(history_rows, approvals, directory, end):
    """Use the byte-verified FDA editions in the allowed post-2017 label windows."""
    listings, inventory = defaultdict(list), []
    for row in sorted(history_rows, key=lambda item: item["edition_date"]):
        day = date.fromisoformat(row["edition_date"])
        numbers = {app[4:].encode("ascii"): app for app, when in approvals.items()
                   if when <= day <= min(add_months(when, 12), end)}
        if not numbers:
            continue
        src = row.get("wayback_url") or row["source_url"]
        path = directory / row["file"]
        found = set()
        with ZipFile(path) as archive:
            member, = [name for name in archive.namelist() if Path(name).stem.lower() == "products"]
            with archive.open(member) as source:
                columns = source.readline().rstrip(b"\r\n").lower().split(b"~")
                kind, number, name = (columns.index(k) for k in (b"appl_type", b"appl_no", b"applicant"))
                for i, line in enumerate(source, 1):
                    fields = line.rstrip(b"\r\n").split(b"~")
                    if len(fields) != len(columns) or fields[kind].strip() != b"A":
                        continue
                    app = numbers.get(fields[number].strip().zfill(6))
                    if app:
                        witness = c3.Evidence(src, day.isoformat(), row["sha256"], f"{member} data row {i}")
                        listings[app].append(Listing(app, day, fields[name].decode("latin-1").strip() or None,
                                                     "fda_zip", witness))
                        found.add(app)
        inventory.append({"edition": day.isoformat(), "source": src, "sha256": row["sha256"],
                          "matching_applications": len(found)})
    return listings, inventory


def competition(args, entities, registry, orange, linkage, rows, risks, spec, source, ob, end):
    days = [date.fromisoformat(day) for day in spec["sealed_test"]["cutoffs"]]
    windows = c3.window_ends(days, end)
    scores = {arm: {(r["key"], r["t"]): p for r, p in zip(rows, risks[arm], strict=True)
                    if r["t"] in windows} for arm in c3.ARMS}
    roster = set(scores["M3"])
    groups = {key for key, _ in roster}
    approvals, metadata, by_app = [], {}, {}
    digest = next(item["sha256"] for item in source["files"] if item["raw_file"] == "df_anda.jsonl")
    for i, entry in enumerate(read_jsonl(args.raw / "df_anda.jsonl"), 1):
        app = entry.get("application_number", "")
        if not c3.ANDA.fullmatch(app):
            continue
        day = min((d for d, _ in dataset._final_originals(entry)), default=None)
        if day is None or not min(days) < day <= max(windows.values()):
            continue
        for key, approved, _ in dataset._original_compositions(entry, day, registry, orange, linkage):
            if key not in groups or approved is None:
                continue
            verify(entities[key].anda_first is not None and entities[key].anda_first <= approved,
                   "C3 approval conflicts with C1 first approval")
            proof = c3.Evidence("openFDA Drugs@FDA df_anda.jsonl", source["fetched_at_utc"], digest,
                                f"line {i}, {app}, ORIG/AP {day.isoformat()}")
            item = c3.Approval(key, app, approved, proof)
            approvals.append(item)
            by_app[app] = item
            metadata[app] = {"sponsor": entry.get("sponsor_name"), "line": i}
    empty = c3.ApplicantIndex()
    unresolved = c3.build_labels(roster, approvals, empty, observed_through=end)
    used = {app for label in unresolved.values() for app in label.applications}
    listings, inventory = collect_listings(ob, {app: by_app[app].approved for app in used}, args.ob_dir, end)
    # The only byte-bound direct overrides in the registered package are development approvals.
    records = {}
    for app in sorted(used):
        item = by_app[app]
        sponsor = metadata[app]["sponsor"]
        records[app] = {"approval_evidence": asdict(item.evidence),
            "primary": _historical_identity(item, empty, listings.get(app, ())),
            "sensitivity": {"name": c3.name_key(sponsor) if sponsor and sponsor.strip() else None,
                            "listed_name": sponsor, "evidence": {**asdict(item.evidence),
                                "locator": f"line {metadata[app]['line']}, sponsor_name"}}}

    results, labels = {}, {}
    for rule in ("primary", "sensitivity"):
        index = WindowApplicants({app: row[rule]["name"] for app, row in records.items()})
        labels[rule] = c3.build_labels(roster, approvals, index, observed_through=end)
        panel = labels[rule]
        bad = (bool(used) and all(not index.names.get(app) for app in used)) or any(
            label.event is None and not label.confirmed_applicants for label in panel.values())
        result = c3.score({key: label.event for key, label in panel.items()}, scores,
                          observed_through=end, history_irrecoverable=bad)
        results[rule] = {**result, "distinct_linked_applications": len(used),
                         "unresolved_applications": sum(not index.names.get(app) for app in used),
                         "by_cutoff": {day.isoformat(): {
                             "labels": {status: sum(label.event is flag for (key, cutoff), label in panel.items()
                                                    if cutoff == day)
                                        for status, flag in (("positive", True), ("negative", False), ("unknown", None))},
                             "unresolved_applications": len({app for (_, cutoff), label in panel.items()
                                 if cutoff == day for app in label.unresolved_applications}),
                         } for day in days}}
    results["identity_comparison"] = {"pooled": _comparison(roster, labels["primary"], labels["sensitivity"], records),
        "by_cutoff": {day.isoformat(): _comparison({item for item in roster if item[1] == day},
                      labels["primary"], labels["sensitivity"], records) for day in days}}
    results["edition_inventory"] = inventory
    return results, records


def json_file(path, obj):
    raw = (json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n").encode("utf-8")
    with path.open("xb") as target:
        target.write(raw)
    digest = raw_digest(path)
    verify(digest == sha256(raw).hexdigest(), "Written artifact failed hash verification")
    return {"path": path.as_posix(), "sha256": digest}


def main():
    parser = frozen.parser(__doc__)
    parser.add_argument("--preflight-only", action="store_true", help="Leave C-prime sealed")
    args = parser.parse_args()
    cfg, s0, c3_spec, c4_inputs, manifests, end, schedule, history, audit = release(args)
    print("Release checks PASS. Replaying the fixed development fits.", flush=True)
    fits = fit_development(args, cfg)
    audit["development_parity"] = "PASS"
    if args.preflight_only:
        print(json.dumps(audit, indent=2), flush=True)
        return

    out = PRIVATE / "score"
    result_path = DATA / "SCORE_CPRIME_RESULTS.json"
    verify(not out.exists() and not result_path.exists(), "SCORE output already exists; reconcile before replay")
    out.mkdir()
    os.environ[ENV_NAME] = LOCK
    try:
        all_days = sorted(set(schedule[12]) | set(schedule[24]))
        entities, builder, registry, orange, linkage = test_inputs(
            args, history, manifests["court_manifest"], end, all_days)
        reports, exports, draws_by_horizon = {}, {}, {}
        for h, days in schedule.items():
            print(f"Scoring registered {h}-month panel.", flush=True)
            rows, eligibility = test_rows(entities, builder, days, h, end)
            b1, models, calibrators, policies = fits[h]
            prediction_inputs = [{k: row[k] for k in ("x", "asof", "breadth")} for row in rows]
            native = predict(b1, models, prediction_inputs)
            probabilities = {arm: calibrators[arm].predict(frozen.t1.calibrator_inputs(native[arm])) for arm in ARMS}
            if h == 24:
                verify(len({r["key"] for r in rows if r["y"]}) >= 50, "C1 event-drug gate disagreement")
                young = np.asarray([row["t"] == date(2024, 1, 1) and
                    date(2023, 1, 1) < entities[row["key"]].nda_first <= date(2024, 1, 1) for row in rows])
            else:
                young = None
            reports[str(h)], draws_by_horizon[str(h)] = score_panel(
                rows, days, h, native, probabilities, policies, eligibility, young)
            payload = {"status": "AUTHORIZED_CPRIME", "prediction_horizon_months": h,
                "frozen_config_sha256": DIGESTS["FROZEN_CONFIG.json"], "implementation_sha": PIN,
                "rows": [{"key": row["key"], "cutoff": row["t"].isoformat(), "y": row["y"],
                          **{arm: native[arm][i] for arm in ARMS}} for i, row in enumerate(rows)]}
            exports[str(h)] = {**json_file(out / f"C1_scores_{h}m.json", payload), "rows": len(rows),
                               "row_fields": ["key", "cutoff", "y", *ARMS]}
        artifact = json_file(out / "C1_score_export_manifest.json", exports)
        draw_path = out / "C1_bootstrap_draws.npz"
        np.savez_compressed(draw_path, **draws_by_horizon)
        print("Scoring the registered C3 queues.", flush=True)
        c3_results, applicant_records = competition(args, entities, registry, orange, linkage, rows, native,
                                                    c3_spec, s0, manifests["ob_manifest"]["editions"], end)
        c3_artifact = json_file(out / "C3_applicant_evidence.json", applicant_records)
        c4 = {"status": "NOT_RUN", "reason": "Reserved origins and no pinned target coverage from 2018",
              "vintage": "RETROSPECTIVE_VINTAGE_UNCONTROLLED",
              "origins_scored": 0, "earliest_missing_outcome_year": 2018, "as_of_proven": "NOT_RUN",
              "covered_frozen_outcome_span": c4_inputs["outcome_freeze"]["quarters"],
              "carry_forward": "NOT_RUN", "drift": "NOT_RUN", "M3_adjusted": "NOT_RUN",
              "B1_adjusted": "NOT_RUN", "coverage": "NOT_RUN"}
        result = {"status": "CONFIRMATORY_CPRIME", "release": audit, "primary": primary(reports),
                  "horizons": reports, "C3": c3_results, "C4": c4, "deviations": [],
                  "native_exports": exports, "native_export_manifest": artifact,
                  "bootstrap_draws": {"path": draw_path.as_posix(), "sha256": raw_digest(draw_path),
                                      "axes": ["draw", list(ARMS), list(frozen.METRICS)]},
                  "C3_applicant_evidence": c3_artifact}
        print(json.dumps(json_file(result_path, result), indent=2), flush=True)
    finally:
        del os.environ[ENV_NAME]


if __name__ == "__main__":
    main()
