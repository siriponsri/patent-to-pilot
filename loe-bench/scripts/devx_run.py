"""Replay E7b and compare five predeclared techniques on sealed development splits."""
import argparse
from collections import Counter
from datetime import date, timedelta
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import random
import re
from unittest.mock import patch

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

from t2_dev_run import ROOT, _manifest, _verify
from e7_dev_run import dated_brands
from t4_power import FLAGS as SUBMISSIONS, TOKEN as JSON_TOKEN, project_development_anda

import numpy as np

from loe_bench import dataset, devx, evidence_graph as graph, moiety, ob_linkage, power, t2
from loe_bench.challenge import ChallengeIdentity, court_rows
from loe_bench.challenge_patents import FilingPatentIndex, PatentChallengeHistory
from loe_bench.common import add_months, read_jsonl
from loe_bench.ob_history import DEFAULT_DIR, OBHistory
from loe_bench.piv_history import EntityMatcher, PIVHistory
from loe_bench.seal import ENV_NAME, LOCK_PATH, TEST_FIRST
from loe_bench.t2_features import AsOfBuilder, edition_coverage

HORIZONS = (12, 24)
DEVELOPMENT_END = date(2016, 1, 1)
PRIMARY = {h: t2.development_split(h) for h in HORIZONS}
FORWARD = {12: ([date(2010, 1, 1), date(2011, 1, 1)],
                [date(2013, 1, 1), date(2014, 1, 1)]),
           24: ([date(2010, 1, 1), date(2011, 1, 1)], [date(2014, 1, 1)])}
PAIRS = (("M3", "B1"), ("M3", "M1"), ("M1", "B1"))
APP_NUMBER = re.compile(rb'"application_number"\s*:\s*"(ANDA\d+)"')
OB_APPROVAL = re.compile(rb'"approval_date"\s*:\s*"([0-9]{8})"')
OB_HISTORICAL = ("ob_nda.jsonl", "ob_anda_pre1982.jsonl", "ob_anda_to2009.jsonl", "ob_anda_2010s.jsonl")


def without_later_approvals(line):
    return OB_APPROVAL.sub(lambda match: match[0] if match[1] <= b"20160101"
                           else b'"approval_date":"outside_development"', line)


def undated_anda_identity(line):
    """Keep undated ingredient metadata without decoding any submission objects."""
    field = SUBMISSIONS.search(line)
    if field is None:
        return None
    depth = 1
    for token in JSON_TOKEN.finditer(line, field.end()):
        mark = token.group()
        if mark in (b"{", b"["):
            depth += 1
        elif mark in (b"}", b"]"):
            depth -= 1
        if depth == 0:
            record = json.loads(line[:field.end()] + line[token.start():])
            record["products"] = [item for item in record.get("products") or ()
                                  if item.get("approval_date") is None]
            return record
    raise ValueError("Unterminated submissions array in ANDA source")


def development_reader(path, *, identity=False):
    if Path(path).name != "df_anda.jsonl":
        yield from read_jsonl(path)
        return
    with Path(path).open("rb") as source:
        for line in source:
            line = without_later_approvals(line)
            record = project_development_anda(line)
            if record is None and identity:
                record = undated_anda_identity(line)
            if record is not None:
                yield record


def application_identity_reader(path):
    if Path(path).name != "df_anda.jsonl":
        yield from read_jsonl(path)
        return
    with Path(path).open("rb") as source:
        for line in source:
            match = APP_NUMBER.search(line)
            if match is not None:
                yield {"application_number": match[1].decode("ascii")}


def historical_orange_reader(path):
    if Path(path).name == "ob_nda.jsonl":
        yield from read_jsonl(path)
        return
    with Path(path).open("rb") as source:
        for line in source:
            dates = OB_APPROVAL.findall(line)
            if (dates and all(value <= b"20160101" for value in dates)
                    or not dates and Path(path).name == "ob_anda_pre1982.jsonl"):
                yield json.loads(line)


def inputs(raw, ob_dir, piv_dir, challenge_dir):
    used = {d for splits in (PRIMARY, FORWARD) for pair in splits.values()
            for dates in pair for d in dates}
    t2.require_development_cutoffs(used)
    s0, s0_ref = _manifest(ROOT / "data/S0_INPUT_MANIFEST.json")
    if date.fromisoformat(s0["t0"]) < DEVELOPMENT_END:
        raise ValueError("S0 inputs do not cover development observation")
    names = ("df_nda.jsonl", "df_anda.jsonl", *OB_HISTORICAL)
    raw_hashes = {item["raw_file"]: item["sha256"] for item in s0["files"] if item["raw_file"] in names}
    for name in names:
        _verify(raw / name, raw_hashes[name])
    gsrs = raw.resolve().parent / "moiety" / moiety.GSRS_FILE
    _verify(gsrs, moiety.GSRS_SHA256)

    # Keep the original NDA identity evidence and restrict ANDA inputs to
    # development approvals or plain application identifiers by consumer.
    make_linkage = dataset.build_moiety_linkage

    def identity_linkage(*args):
        with patch.object(dataset, "read_jsonl", lambda path: development_reader(path, identity=True)):
            return make_linkage(*args)

    with (patch.object(moiety, "ORANGE_FILES", OB_HISTORICAL),
          patch.object(moiety, "read_jsonl", historical_orange_reader)):
        with (patch.object(dataset, "read_jsonl", development_reader),
              patch.object(dataset, "build_moiety_linkage", identity_linkage)):
            entities = dataset.build_entities(raw, gsrs_path=gsrs)
        with patch.object(ob_linkage, "read_jsonl", application_identity_reader):
            linker = ob_linkage.HistoricalMoietyLinker(raw, entities, gsrs_path=gsrs)
        identity = ChallengeIdentity(linker, dated_brands(raw, linker))

    ob_manifest, ob_ref = _manifest(ROOT / "data/OB_EDITIONS.json")
    ob = OBHistory.from_records(ob_manifest, str(ob_dir))
    coverage = {d: edition_coverage(ob, d) for d in sorted(used)}
    for detail in coverage.values():
        source = detail["source"]
        if source:
            _verify(ob_dir / source["file"], source["sha256"])

    piv_path = ROOT / "data/PIV_EDITIONS.json"
    _, piv_ref = _manifest(piv_path)
    piv = PIVHistory(piv_path, piv_dir, EntityMatcher([]))
    sources, court_ref = _manifest(ROOT / "data/E7_sources.json")
    rai, documents = sources["rai"], sources["corroborating_documents"]
    for source in (rai, rai["metadata"], *documents.values()):
        _verify(challenge_dir / source["file"], source["sha256"])
    corroboration = [{**case, **documents[case["document"]]} for case in sources["corroborated_cases"]]
    court = court_rows(challenge_dir / rai["file"], max(used) + timedelta(days=1))
    challenge = PatentChallengeHistory(piv, identity, court, rai, corroboration, FilingPatentIndex(ob, linker))
    builder = AsOfBuilder(ob, linker=linker, challenge=challenge)
    provenance = {"s0_manifest": s0_ref, "s0_files": raw_hashes, "ob_manifest": ob_ref,
                  "gsrs": {"file": gsrs.name, "sha256": moiety.GSRS_SHA256},
                  "piv_manifest": piv_ref, "court_manifest": court_ref,
                  "orange_book_coverage": {d.isoformat(): details for d, details in coverage.items()}}
    return entities, builder, provenance


def partition(entities, builder, dates, horizon, training=False):
    rows = dataset.build_samples(entities, dates, horizon, DEVELOPMENT_END)
    breadth = {}
    for row in rows:
        key, cutoff, x = row["key"], row["t"], row["x"]
        row["asof"] = builder.build(key, cutoff, horizon, x)
        row["asof12"] = row["asof"] if horizon == 12 else builder.build(key, cutoff, 12, x)
        if cutoff not in breadth:
            source, _ = builder.history.available_source_asof(cutoff)
            breadth[cutoff] = source if source and source.edition_date >= add_months(cutoff, -6) else None
        source = breadth[cutoff]
        products = builder._indexes[source].linked_products.get(builder.linker.canonical(key), ()) if source else ()
        row["breadth"] = devx.presentation_breadth(products, source.edition_date if source else cutoff)
        if training:
            event = entities[key].anda_first
            row["first_event"] = event
            row["event12"] = int(event is not None and event <= add_months(cutoff, 12))
    return rows


def cohort(train, validation, horizon):
    observed_through = min(r["t"] for r in validation) - timedelta(days=1)
    return {
        "train_cutoffs": sorted({r["t"].isoformat() for r in train}),
        "validation_cutoffs": sorted({r["t"].isoformat() for r in validation}),
        "train_rows": len(train),
        "validation_rows": len(validation),
        "validation_drug_clusters": len({r["key"] for r in validation}),
        "validation_event_clusters": len({r["key"] for r in validation if r["y"]}),
        "validation_verdicts": dict(Counter(r["asof"].verdict for r in validation)),
        "verdicts_by_cutoff": {
            d.isoformat(): dict.fromkeys(t2.VERDICTS, 0) | dict(Counter(
                r["asof"].verdict for r in (*train, *validation) if r["t"] == d))
            for d in sorted({r["t"] for r in (*train, *validation)})},
        "validation_breadth_missing_rows": {
            name: sum(int(r["breadth"][name]) for r in validation) for name in devx.BREADTH[2:]},
        "hazard_train_intervals": dict(Counter(
            f"year_{interval + 1}" for row in train for interval, _ in devx.annual_targets(
                row["t"], observed_through, row["first_event"]))),
    }


class PairedEvaluation:
    def __init__(self, rows):
        self.labels = [r["y"] for r in rows]
        self.verdicts = [r["asof"].verdict for r in rows]
        # Cluster insertion order and random draws match the T2 bootstrap.
        keys = list(dict.fromkeys(r["key"] for r in rows))
        index = {key: i for i, key in enumerate(keys)}
        rng = random.Random(t2.BOOTSTRAP_SEED)
        n = len(keys)
        weights = np.stack([np.bincount([rng.randrange(n) for _ in keys], minlength=n)
                            for _ in range(t2.BOOTSTRAP_DRAWS)])
        self.weights = weights[:, [index[r["key"]] for r in rows]]
        self.total = self.weights.sum(axis=1)
        self.harmonic = power.harmonic_numbers(int(max(self.total)))

    def areas(self, predictions):
        answered = sorted((i for i, p in enumerate(predictions) if p.action != graph.ABSTAIN),
                          key=lambda i: predictions[i].score, reverse=True)
        if not answered:
            return np.full(len(self.total), np.nan)
        scores = [predictions[i].score for i in answered]
        starts = [0, *(i for i in range(1, len(scores)) if scores[i] != scores[i - 1])]
        errors = np.asarray([int((predictions[i].action == graph.PREDICT_ENTRY) != self.labels[i])
                             for i in answered])
        result = []
        for offset in range(0, len(self.total), 128):
            batch = self.weights[offset:offset + 128, answered]
            result.extend(power.area(np.add.reduceat(batch, starts, axis=1),
                                     np.add.reduceat(batch * errors, starts, axis=1),
                                     self.total[offset:offset + 128], self.harmonic))
        return np.asarray(result)

    def evaluate(self, predictions, diagnostics):
        arms = {arm: t2._metrics(pred, self.labels, self.verdicts) for arm, pred in predictions.items()}
        draws = {arm: self.areas(pred) for arm, pred in predictions.items()}
        pairs = {}
        for left, right in PAIRS:
            name = f"{left}_minus_{right}"
            pairs[name] = interval(difference(arms[left]["aurc80"], arms[right]["aurc80"]),
                                   draws[left] - draws[right])
            pairs[name]["meets_practical_threshold"] = (
                pairs[name]["delta"] is not None and pairs[name]["delta"] <= -0.01)
        return {"arms": arms, "paired_aurc80": pairs, "selector_folds": diagnostics}, draws


def difference(left, right):
    return left - right if left is not None and right is not None else None


def interval(point, draws):
    valid = np.sort(draws[np.isfinite(draws)]) if point is not None else []
    n = len(valid)
    return {"delta": point,
            "status": "evaluated" if n else "unevaluable",
            "ci95": [float(valid[int(n * 0.025)]), float(valid[int(n * 0.975)])] if n else None,
            "valid_draws": n, "invalid_draws": t2.BOOTSTRAP_DRAWS - n}


def compare(previous, candidate):
    before, old = previous
    after, new = candidate
    paired = {}
    for left, right in PAIRS:
        name = f"{left}_minus_{right}"
        point = difference(after["paired_aurc80"][name]["delta"], before["paired_aurc80"][name]["delta"])
        paired[name] = interval(point, (new[left] - new[right]) - (old[left] - old[right]))
    for arm in devx.ARMS:
        a, b = after["arms"][arm]["aurc80"], before["arms"][arm]["aurc80"]
        paired[arm] = interval(difference(a, b), new[arm] - old[arm])
    return {"current": before, "candidate": after, "candidate_minus_current": paired}


def verify_baseline(reference, details, observed):
    for name in ("train_rows", "validation_rows", "validation_drug_clusters",
                 "validation_event_clusters", "verdicts_by_cutoff", "validation_verdicts"):
        if details[name] != reference[name]:
            raise ValueError(f"E7b baseline {name} mismatch: {details[name]} vs {reference[name]}")
    for arm, metrics in observed["arms"].items():
        for name in ("aurc80", "brier", "ece", "coverage"):
            if abs(metrics[name] - reference["arms"][arm][name]) > 1e-12:
                raise ValueError(f"E7b baseline {arm} {name} mismatch: {metrics[name]} vs "
                                 f"{reference['arms'][arm][name]}")
    for name, observed_pair in observed["paired_aurc80"].items():
        expected = reference["paired_aurc80"][name]
        if not (np.allclose(observed_pair["ci95"], expected["ci95"], rtol=0, atol=1e-12)
                and observed_pair["valid_draws"] == expected["valid_draws"]):
            raise ValueError(f"E7b baseline {name} bootstrap mismatch")


def adoption(results):
    h24 = results["24"]["candidate_minus_current"]
    h12 = results["12"]["candidate_minus_current"]
    checks = {}
    for name, value, ceiling in (
        ("M3_minus_B1_at_24", h24["M3_minus_B1"]["delta"], -0.0010),
        ("M3_minus_B1_at_12", h12["M3_minus_B1"]["delta"], 0.0010),
        ("M1_minus_B1_at_24", h24["M1_minus_B1"]["delta"], 0.0010),
    ):
        checks[name] = {"delta": value, "ceiling": ceiling, "pass": value is not None and value <= ceiling}
    return all(check["pass"] for check in checks.values()), checks


def run(args):
    if LOCK_PATH.exists() or ENV_NAME in os.environ:
        raise ValueError("DEVX requires a closed test seal")
    receipt = ROOT.parent / "docs/loe-bench/receipts/DEVX.md"
    protocol = receipt.read_bytes().split(b"\n## Result", 1)[0].replace(b"\r\n", b"\n").rstrip()
    print("Loading verified development inputs.", flush=True)
    entities, builder, provenance = inputs(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir)
    reference, reference_ref = _manifest(ROOT / "data/E7b_dev_summary.json")

    def prepare(splits):
        datasets, evaluators, cohorts = {}, {}, {}
        for h, (train_dates, validation_dates) in splits.items():
            if any(add_months(d, h) >= validation_dates[0] for d in train_dates) or any(
                add_months(d, h) > DEVELOPMENT_END for d in validation_dates
            ):
                raise ValueError("development windows violate the embargo or observation boundary")
            train = partition(entities, builder, train_dates, h, training=True)
            validation = partition(entities, builder, validation_dates, h)
            datasets[h] = train, validation
            evaluators[h] = PairedEvaluation(validation)
            cohorts[str(h)] = cohort(train, validation, h)
        return datasets, evaluators, cohorts

    datasets, evaluators, cohorts = prepare(PRIMARY)

    def evaluate(flags, data, scorers):
        return {str(h): scorers[h].evaluate(*devx.predict(*data[h], h, flags)) for h in HORIZONS}

    flags = ()
    current = evaluate(flags, datasets, evaluators)
    for h in map(str, HORIZONS):
        if any(info["selected_l2"] != devx.L2 for info in reference["horizons"][h]["tuning"].values()):
            raise ValueError("DEVX L2 does not match E7b selection")
        verify_baseline(reference["horizons"][h], cohorts[h], current[h][0])
    print("E7b baseline parity verified.", flush=True)

    trials = []
    forward = None
    for name in devx.TRIALS:
        print(f"Comparing {name} against {flags or 'E7b'}.", flush=True)
        candidate_flags = (*flags, name)
        candidate = evaluate(candidate_flags, datasets, evaluators)
        results = {h: compare(current[h], candidate[h]) for h in current}
        adopted, checks = adoption(results)
        robustness = {"status": "NOT_RUN", "reason": "Candidate rejected on primary development."}
        if adopted:
            if forward is None:
                forward = prepare(FORWARD)
            data, scorers, forward_cohorts = forward
            before = evaluate(flags, data, scorers)
            after = evaluate(candidate_flags, data, scorers)
            forward_results = {h: compare(before[h], after[h]) for h in before}
            directions = {}
            for h, outcome in forward_results.items():
                delta = outcome["candidate_minus_current"]["M3_minus_B1"]["delta"]
                main = results[h]["candidate_minus_current"]["M3_minus_B1"]["delta"]
                directions[h] = {"delta": delta, "direction_holds": (
                    None if delta is None else bool(np.sign(delta) == np.sign(main)))}
            robustness = {"status": "DEVELOPMENT_ONLY", "cohorts": forward_cohorts,
                          "horizons": forward_results, "M3_minus_B1_direction": directions}
        trials.append({"id": name, "configurations": {
            arm: [{"role": "current", "flags": flags, "l2": devx.L2},
                  {"role": "candidate", "flags": candidate_flags, "l2": devx.L2}]
            for arm in devx.ARMS},
            "horizons": results, "adopted": adopted, "checks": checks, "robustness": robustness})
        print(f"{name}: {'ADOPT' if adopted else 'REJECT'} {checks}", flush=True)
        if adopted:
            flags, current = candidate_flags, candidate

    return {
        "status": "DEVELOPMENT_ONLY", "baseline_commit": "c4281994",
        "baseline_replay_verified": True, "protocol_sha256": sha256(protocol).hexdigest(),
        "observation_end": DEVELOPMENT_END.isoformat(), "sealed_test_start": TEST_FIRST.isoformat(),
        "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "input_sha256": {**provenance, "e7b_summary": reference_ref},
        "bootstrap": {"draws": t2.BOOTSTRAP_DRAWS, "seed": t2.BOOTSTRAP_SEED, "unit": "drug"},
        "primary_cohorts": cohorts, "trials": trials,
        "final_pipeline_flags": {name: name in flags for name in devx.TRIALS},
        "configuration_counts_per_arm": {
            arm: {"comparison_entries_per_horizon": 10, "comparison_entries_total_both_horizons": 20,
                  "new_candidates_per_horizon": 5, "distinct_primary_per_horizon_including_baseline": 6,
                  "distinct_primary_total_both_horizons_including_baseline": 12,
                  "robustness_refits_per_horizon": 2 * len(flags)}
            for arm in devx.ARMS},
    }


if __name__ == "__main__":
    base = Path(DEFAULT_DIR).parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=base / "raw-20261127")
    parser.add_argument("--ob-dir", type=Path, default=Path(DEFAULT_DIR))
    parser.add_argument("--piv-dir", type=Path, default=base / "piv")
    parser.add_argument("--challenge-dir", type=Path, default=base / "challenge")
    output = ROOT / "data/DEVX_results.json"
    output.write_text(json.dumps(run(parser.parse_args()), indent=2, sort_keys=True, allow_nan=False) + "\n",
                      encoding="utf-8", newline="\n")
    print(output)
