"""Prepare and score the registered C-prime L1/L1e run locally."""
from collections import Counter
from datetime import date, timedelta
from hashlib import sha256
import json
from math import isfinite
from pathlib import Path
import subprocess

import l1dev_local as local
import l1e_protocol as protocol
from e7_dev_run import dated_brands
from t2_dev_run import _verify

from loe_bench import dataset, devx, l1e_prompt, llm_arm, moiety, seal
from loe_bench.challenge import ChallengeIdentity, court_rows
from loe_bench.challenge_patents import FilingPatentIndex, PatentChallengeHistory
from loe_bench.ob_history import OBHistory
from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.piv_history import EntityMatcher, PIVHistory
from loe_bench.t2_features import AsOfBuilder, edition_coverage


freeze = local.freeze
PRIVATE = local.PRIVATE.parent / "scorellm"
SCORE_MANIFEST = PRIVATE.parent / "score/C1_score_export_manifest.json"
LOCK = "3f91145251465b0ed9c89233337748e1b9fd84db8c4c2a6158860374670e1c77"
PIPELINE = "f683017c4fb73aadd91bb97f3381f5dd9308c9ca"
CUTOFFS = {12: tuple(date(y, 1, 1) for y in range(2017, 2026)),
           24: tuple(date(y, 1, 1) for y in range(2017, 2025))}
PINS = {
    "FROZEN_CONFIG.json": "d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39",
    "L1_FROZEN_CONFIG.json": "e5e5ade357ee5faf83efa0ce24ad25feddacdfcbf49ddd817a6b10e494a9ef16",
    "L1E_FROZEN_CONFIG.json": "dd1dd4ac0d592a48de081c5fc29f68e0ccc78fd7a8daad771d280c7f15901e40",
}
ARM_CONFIGS = {"L1": "L1_FROZEN_CONFIG.json", "L1e": "L1E_FROZEN_CONFIG.json"}
STEMS = {"L1": "L1DEV", "L1e": "L1E"}
COMPARATORS = {"L1": ("B1", "M3"), "L1e": ("L1", "M3", "B1")}


def configs():
    for name, digest in PINS.items():
        if freeze.manifest(name)["sha256"] != digest:
            raise ValueError(f"freeze digest mismatch: {name}")
    for name in ARM_CONFIGS.values():
        config = freeze.read_json(name)
        for path, digest in (config["harness_lf_sha256"] | config.get("restage_lf_sha256", {})).items():
            if freeze.manifest(f"../{path}")["sha256"] != digest:
                raise ValueError(f"pinned inference code differs: {path}")
    return {arm: freeze.read_json(name) for arm, name in ARM_CONFIGS.items()}


def release():
    seal.require_cutoffs(CUTOFFS[12])
    if freeze.read_json("PREREG_LOCK.json")["sha256"] != LOCK:
        raise ValueError("registration lock differs from the approved release")
    if sha256((freeze.DATA / "OSF_REGISTRATION_P2SMD.json").read_bytes()).hexdigest() != LOCK:
        raise ValueError("canonical registration record differs from the approved release")
    repo = freeze.DATA.parent.parent
    gate = (repo / "docs/loe-bench/receipts/GATE.md").read_text(encoding="utf-8")
    decisions = (repo / "docs/maintenance/OWNER-DECISIONS-20261122.md").read_text(encoding="utf-8")
    if ("Verdict **PASS**." not in gate or LOCK not in gate
            or "as first author, the owner authorized opening the sealed test" not in decisions):
        raise ValueError("missing matching GATE PASS receipt")
    configs()
    code = subprocess.check_output(["rtk", "proxy", "git", "diff", "--name-status", PIPELINE,
                                    "--", "loe-bench/loe_bench", "loe-bench/scripts"], cwd=repo, text=True)
    allowed = {"llm_arm.py", "llm_arm_run.py", "test_llm_arm.py", "freeze_gate.py"}
    if any(status != "A" and (status != "M" or Path(path).name not in allowed)
           for status, path in (line.split("\t", 1) for line in code.splitlines())):
        raise ValueError("the inherited frozen pipeline has changed")
    return LOCK


def sources(args):
    lock = freeze.read_json("FROZEN_CONFIG.json")
    frozen = lock["input_sha256"]
    for key in ("s0_manifest", "ob_manifest", "piv_manifest", "court_manifest"):
        if freeze.manifest(frozen[key]["file"]) != frozen[key]:
            raise ValueError(f"source manifest differs from the freeze: {key}")
    s0 = freeze.read_json(frozen["s0_manifest"]["file"])
    end = date.fromisoformat(s0["t0"])
    schedule = lock["sealed_test"]
    if (schedule["outcomes_observed_through"] != end.isoformat()
            or any([d.isoformat() for d in days] != schedule["schedule"][str(h)]["test_cutoffs"]
                   for h, days in CUTOFFS.items())):
        raise ValueError("C-prime schedule differs from the freeze")
    raw = {item["raw_file"]: item["sha256"] for item in s0["files"]}
    for name in ("df_nda.jsonl", "df_anda.jsonl", *moiety.ORANGE_FILES):
        _verify(args.raw / name, raw[name])
    gsrs = args.raw.resolve().parent / "moiety" / frozen["gsrs"]["file"]
    _verify(gsrs, frozen["gsrs"]["sha256"])
    ob = OBHistory.from_records(freeze.read_json(frozen["ob_manifest"]["file"]), args.ob_dir)
    for day in CUTOFFS[12]:
        coverage = edition_coverage(ob, day)
        if coverage["status"] != "FRESH":
            raise ValueError(f"required FDA ZIP unavailable: {day}")
        source = coverage["source"]
        _verify(args.ob_dir / source["file"], source["sha256"])
    court_data = freeze.read_json(frozen["court_manifest"]["file"])
    rai, documents = court_data["rai"], court_data["corroborating_documents"]
    for source in (rai, rai["metadata"], *documents.values()):
        _verify(args.challenge_dir / source["file"], source["sha256"])
    return end, gsrs, ob, court_data


def forecast_rows(args):
    end, gsrs, ob, court_data = sources(args)
    entities = dataset.build_entities(args.raw, gsrs_path=gsrs)
    linker = HistoricalMoietyLinker(args.raw, entities, gsrs_path=gsrs)
    identity = ChallengeIdentity(linker, dated_brands(args.raw, linker))
    piv = PIVHistory(freeze.DATA / "PIV_EDITIONS.json", args.piv_dir, EntityMatcher([]))
    rai, documents = court_data["rai"], court_data["corroborating_documents"]
    cases = [{**case, **documents[case["document"]]} for case in court_data["corroborated_cases"]]
    court = court_rows(args.challenge_dir / rai["file"], max(CUTOFFS[12]) + timedelta(days=1))
    challenge = PatentChallengeHistory(piv, identity, court, rai, cases, FilingPatentIndex(ob, linker))
    builder = AsOfBuilder(ob, linker=linker, challenge=challenge)
    rows = []
    for horizon, days in CUTOFFS.items():
        panel = dataset.build_samples(entities, days, horizon, end)
        for row in sorted(panel, key=lambda row: (row["t"], row["key"])):
            key, day = row["key"], row["t"]
            asof = builder.build(key, day, horizon, row["x"])
            source, _ = ob.available_source_asof(day)
            products = builder._indexes[source].linked_products.get(linker.canonical(key), ())
            breadth = devx.presentation_breadth(products, source.edition_date)
            evidence = l1e_prompt.from_m3({"t": day, "asof": asof, "breadth": breadth})
            rows.append(({"key": key, "t0": day.isoformat(), "horizon_months": horizon}, evidence))
    required = {part[2:] for row, _ in rows for part in row["key"].split("|") if part.startswith("U:")}
    names = local.gsrs_names(gsrs, required)
    roster = [row for row, _ in rows]
    l1 = [{"entity": local.entity_name(row["key"], names), "t0": row["t0"],
           "horizon_months": row["horizon_months"]} for row in roster]
    l1e = [dict(row, as_of_evidence=evidence) for row, (_, evidence) in zip(l1, rows, strict=True)]
    return roster, {"L1": l1, "L1e": l1e}


def write_json(path, value):
    path.write_bytes((json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode())


def prepare(args):
    from scorellm_gpu import check_inputs, load_arms

    files = ["manifest.json", "roster.jsonl", *(f"{stem}_inputs.jsonl" for stem in STEMS.values())]
    if any((args.private / name).exists() for name in files):
        raise FileExistsError("select a new private directory for a new input freeze")
    roster, inputs = forecast_rows(args)
    counts = Counter((row["horizon_months"], row["t0"]) for row in roster)
    plan = {"registration_sha256": LOCK, "config_lf_sha256": PINS,
            "cutoffs": {str(h): {day.isoformat(): counts[h, day.isoformat()] for day in days}
                        for h, days in CUTOFFS.items()},
            "rows": len(roster), "arms": {}}
    args.private.mkdir(parents=True, exist_ok=True)
    roster_bytes = protocol.jsonl(roster)
    with (args.private / "roster.jsonl").open("xb") as stream:
        stream.write(roster_bytes)
    for arm, rows in inputs.items():
        renderer = llm_arm.build_prompt if arm == "L1" else l1e_prompt.build_prompt
        data = protocol.jsonl(rows)
        plan["arms"][arm] = {"input_sha256": sha256(data).hexdigest(),
                             "messages_sha256": protocol.digest_lines(map(renderer, rows))}
        check_inputs(data, plan, arm)
        with (args.private / f"{STEMS[arm]}_inputs.jsonl").open("xb") as stream:
            stream.write(data)
    plan["roster_sha256"] = sha256(roster_bytes).hexdigest()
    write_json(args.private / "manifest.json", plan)
    load_arms(args.private, freeze.DATA)
    print(json.dumps(plan, sort_keys=True))


def parse_run(folder, manifest, roster, inputs, arm):
    stem = STEMS[arm]
    summary = json.loads((folder / f"{stem}_summary.json").read_bytes())
    path = folder / f"{stem}_outputs.jsonl"
    parsed, gate = protocol.read_outputs(path, summary, inputs, manifest["arms"][arm]["input_sha256"])
    output = [json.loads(line) for line in path.read_bytes().splitlines()]
    prompts = [row["prompt_sha256"] for row in output]
    if any(len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest) for digest in prompts):
        raise ValueError("invalid rendered chat hash in model output")
    gate.update({"output_sha256": summary["output_sha256"],
                 "rendered_chat_hashes_sha256": protocol.digest_lines(prompts),
                 "valid_json": summary["valid_json"], "abstains": summary["abstains"],
                 "inference_wall_s": summary["inference_wall_s"], "gpu": summary["gpu"]})
    if gate["status"] != "PASS" or not gate["full_roster"]:
        return gate, None
    scores = protocol.native_risks(parsed)
    predictions = protocol.jsonl(dict(row, p_entry=risk) for row, risk in zip(roster, scores, strict=True))
    (folder / f"{stem}_predictions.jsonl").write_bytes(predictions)
    gate["predictions_sha256"] = sha256(predictions).hexdigest()
    return gate, scores


def score_rows(ref, horizon, roster):
    data = Path(ref["path"]).read_bytes()
    if sha256(data).hexdigest() != ref["sha256"]:
        raise ValueError("SCORE row export failed SHA-256 verification")
    payload = json.loads(data)
    if (payload["status"] != "AUTHORIZED_CPRIME" or payload["prediction_horizon_months"] != horizon
            or payload["frozen_config_sha256"] != PINS["FROZEN_CONFIG.json"]
            or payload["implementation_sha"] != PIPELINE):
        raise ValueError("SCORE export is outside the released frozen panel")
    indexed = {(row["key"], row["cutoff"]): row for row in payload["rows"]}
    keys = [(row["key"], row["t0"]) for row in roster]
    if len(indexed) != len(payload["rows"]) or len(indexed) != ref["rows"] or set(indexed) != set(keys):
        raise ValueError("SCORE export does not match the entire ordered prediction roster")
    matched = [indexed[key] for key in keys]
    if any(type(row["y"]) is not int or row["y"] not in (0, 1)
           or any(not isfinite(row[arm]) or not 0 <= row[arm] <= 1 for arm in ("B1", "M3"))
           for row in matched):
        raise ValueError("SCORE export includes an invalid label or native risk")
    labels = [{"key": row["key"], "t": date.fromisoformat(row["cutoff"]), "y": row["y"]} for row in matched]
    return labels, {arm: [row[arm] for row in matched] for arm in ("B1", "M3")}


def compare(predictions, refs, roster):
    panels = {}
    for horizon, days in CUTOFFS.items():
        selected = [i for i, row in enumerate(roster) if row["horizon_months"] == horizon]
        rows, native = score_rows(refs[str(horizon)], horizon, [roster[i] for i in selected])
        native.update({arm: [scores[i] for i in selected] for arm, scores in predictions.items()})
        panels[str(horizon)] = {
            arm: local.score_panel(rows, native, days, arms=(arm, *(c for c in COMPARATORS[arm] if c in native)))
            for arm in predictions
        }
    return panels


def results(args):
    from scorellm_gpu import load_arms

    manifest_path = args.private / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    roster_data = (args.private / "roster.jsonl").read_bytes()
    if manifest["registration_sha256"] != LOCK or sha256(roster_data).hexdigest() != manifest["roster_sha256"]:
        raise ValueError("unverified roster or registration digest")
    roster = [json.loads(line) for line in roster_data.splitlines()]
    if len(roster) != manifest["rows"]:
        raise ValueError("roster length differs from the freeze")
    gates, predictions = {}, {}
    for arm, (inputs, _, _) in load_arms(args.private, freeze.DATA).items():
        try:
            gate, risks = parse_run(args.private, manifest, roster, inputs, arm)
        except (OSError, KeyError, ValueError) as exc:
            gate = {"status": "NOT_RUN", "full_roster": False, "verification_error": type(exc).__name__}
            risks = None
        gate["arm_status"] = "COMPLETE" if risks is not None else "NOT_RUN"
        gates[arm] = gate
        if risks is not None:
            predictions[arm] = risks
    summary = {"status": "NOT_RUN", "role": "EXPLORATORY", "quality_gates": gates,
               "input_manifest_sha256": sha256(manifest_path.read_bytes()).hexdigest(),
               "input_freeze": manifest, "comparisons": {}, "horizons": {}}
    for arm, comps in COMPARATORS.items():
        for comp in comps:
            ready = arm in predictions and (comp != "L1" or comp in predictions)
            summary["comparisons"][f"{arm}-{comp}"] = "PENDING_SCORE_EXPORT" if ready else "NOT_RUN"
    if predictions:
        summary["status"] = "PENDING_SCORE_EXPORT"
    if predictions and args.score_manifest.is_file():
        try:
            score_manifest = args.score_manifest.read_bytes()
            summary["score_export_manifest_sha256"] = sha256(score_manifest).hexdigest()
            summary["horizons"] = compare(predictions, json.loads(score_manifest), roster)
        except (OSError, KeyError, TypeError, ValueError) as exc:
            summary["score_export_error"] = str(exc)
            summary["status"] = "NOT_RUN"
            summary["comparisons"] = dict.fromkeys(summary["comparisons"], "NOT_RUN")
        else:
            for panels in summary["horizons"].values():
                for panel in panels.values():
                    for contrast in panel["contrasts"]:
                        summary["comparisons"][contrast] = "PASS"
            summary["status"] = "SCORED_EXPLORATORY"
    ledger = args.private / "runpod_ledger.json"
    if ledger.is_file():
        summary["runpod"] = json.loads(ledger.read_bytes())
    freeze.write_json("SCORELLM_CPRIME_RESULTS.json", summary)


def main():
    parser = freeze.parser(__doc__)
    parser.add_argument("mode", nargs="?", choices=("prepare", "score"), default="prepare")
    parser.add_argument("--private", type=Path, default=PRIVATE)
    parser.add_argument("--score-manifest", type=Path, default=SCORE_MANIFEST)
    args = parser.parse_args()
    release()
    (prepare if args.mode == "prepare" else results)(args)


if __name__ == "__main__":
    main()
