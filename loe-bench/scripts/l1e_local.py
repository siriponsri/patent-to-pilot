"""Freeze the L1e development inputs and score an independently verified GPU run."""
from collections import Counter
from datetime import timedelta
from hashlib import sha256
import json
from pathlib import Path

import l1dev_local as l1_local
import l1dev_protocol as l1
import l1e_protocol as spec
import numpy as np

from loe_bench import devx, l1e_prompt, t2
from loe_bench.t2_features import CHALLENGE_FEATURES, MODEL_FEATURES


freeze = l1_local.freeze
t1 = l1_local.t1
CONFIG = "L1E_FROZEN_CONFIG.json"
RESULTS = "L1E_DEV_RESULTS.json"
ARMS = ("L1e", "L1", "M3", "B1")
PRIVATE = l1_local.PRIVATE.parent / "l1e_c2"
HARNESS = ("loe_bench/llm_arm.py", "loe_bench/l1e_prompt.py", "scripts/l1dev_protocol.py",
           "scripts/l1e_protocol.py", "scripts/runpod_l1dev.py", "scripts/runpod_l1e.py")
RESTAGE = ("scripts/runpod_l1e_restage.py", "scripts/runpod_e4b_stage.py", "data/E4b_model.json",
           "data/E4b_stage.json")


def inputs_from_cohorts(cohorts):
    identity, rows_by_h, *_ = cohorts
    return [dict(forecast, as_of_evidence=l1e_prompt.from_m3(row))
            for forecast, row in zip(identity, (r for rows in rows_by_h.values() for r in rows), strict=True)]


def prepare(args, cohorts):
    parent = freeze.read_json("L1_FROZEN_CONFIG.json")
    rows = inputs_from_cohorts(cohorts)
    if set(l1e_prompt.CROSSWALK) != set((*MODEL_FEATURES, *CHALLENGE_FEATURES, *devx.BREADTH)):
        raise ValueError("M3 source columns differ from the crosswalk")
    m3 = freeze.read_json("FROZEN_CONFIG.json")["features"]["M3"]
    if set(m3) != set(l1e_prompt.CROSSWALK) | set(l1e_prompt.EXCLUDED):
        raise ValueError("frozen M3 columns differ from the C2 disposition")
    data = spec.jsonl(rows)
    fields = ("model", "image", "runtime", "decoder", "parser", "evaluation", "quality_gate", "role")
    config = {field: parent[field] for field in fields}
    config.update(arm="L1e", status="FROZEN_FOR_DEVELOPMENT_RUN",
                  l1_config_lf_sha256=freeze.manifest("L1_FROZEN_CONFIG.json")["sha256"])
    config["harness_lf_sha256"] = {
        name: freeze.manifest(f"../{name}")["sha256"] for name in HARNESS
    }
    config["restage_lf_sha256"] = {
        name: freeze.manifest(f"../{name}")["sha256"] for name in RESTAGE
    }
    for name, digest in parent["harness_lf_sha256"].items():
        if config["harness_lf_sha256"][name] != digest:
            raise ValueError(f"pinned L1 implementation differs: {name}")
    config["prompt"] = dict(spec.prompt_digests(rows), chat_template=parent["prompt"]["chat_template"],
                            messages_bytes="LF-terminated UTF-8 JSON arrays of [system, user] before tokenization")
    config["development_input"] = dict(parent["development_input"], sha256=sha256(data).hexdigest(),
                                       l1_rows_sha256=parent["development_input"]["sha256"],
                                       fields=sorted(l1e_prompt.FIELDS))
    config["crosswalk"] = {"identity": sorted(l1.FIELDS), "as_of_evidence": l1e_prompt.CROSSWALK,
                           "additional_graph_sources": l1e_prompt.GRAPH_SOURCE_FIELDS,
                           "excluded_m3_columns": l1e_prompt.EXCLUDED,
                           "graph_verdict_supplied": False, "b1_hazard_supplied": False}
    config["quality_gate"]["result"] = {"status": "NOT_RUN"}
    config["evaluation"]["comparators"] = list(ARMS[1:])
    config["evaluation"]["failure_rule"] = (
        "Stop at 200 if fewer than 180 valid. Any failed, incomplete or unverifiable run yields NOT_RUN. "
        "The L1 comparator requires its original verified outputs. Invalid responses have native risk -1.0."
    )
    spec.verify_input(data, config)
    args.private.mkdir(parents=True, exist_ok=True)
    (args.private / "L1E_inputs.jsonl").write_bytes(data)
    freeze.write_json(CONFIG, config)
    print(f"Verified {len(rows)} enriched rows against the L1 identity roster", flush=True)


def check_reference(result, horizon, reference, arms):
    for arm in arms:
        for metric in l1_local.METRICS:
            new = result["levels"][arm][metric]
            old = reference[str(horizon)]["levels"][arm][metric]
            if (new["undefined_draws"] != old["undefined_draws"]
                    or not np.allclose([new["estimate"], *new["ci95"]], [old["estimate"], *old["ci95"]],
                                       rtol=0, atol=1e-12)):
                raise ValueError(f"{horizon}m {arm} {metric} differs from the frozen comparator")


def results_for_cohorts(cohorts, parsed, l1_parsed):
    identity, rows_by_h, entities, builder, reference = cohorts
    l1_reference = freeze.read_json("L1DEV_results.json")["horizons"]
    results = {}
    for h, rows in rows_by_h.items():
        train_days, days = t1.replay.PRIMARY[h]
        train = t1.replay.partition(entities, builder, train_days, h, training=True)
        native = t1.native(train, rows, h, min(days) - timedelta(days=1))
        selection = [i for i, row in enumerate(identity) if row["horizon_months"] == h]
        responses = [parsed[i] for i in selection]
        native["L1e"] = spec.native_risks(responses)
        arms = ("L1e", "M3", "B1")
        if l1_parsed is not None:
            native["L1"] = spec.native_risks(l1_parsed[i] for i in selection)
            arms = ARMS
        result = l1_local.score_panel(rows, native, days, arms=arms)
        check_reference(result, h, reference, ("B1", "M3"))
        if l1_parsed is not None:
            check_reference(result, h, l1_reference, ("L1",))
        result["valid_json"] = sum(row["valid"] for row in responses)
        result["actions"] = Counter(row["action"] for row in responses)
        result["parse_errors"] = Counter(row["error"] for row in responses if not row["valid"])
        results[str(h)] = result
    return results


def score(args, cohorts):
    config = freeze.read_json(CONFIG)
    rows = spec.verify_input(spec.jsonl(inputs_from_cohorts(cohorts)), config)
    summary = json.loads((args.private / "L1E_summary.json").read_bytes())
    parsed, gate = spec.read_outputs(args.private / "L1E_outputs.jsonl", summary, rows,
                                     config["development_input"]["sha256"])
    config["quality_gate"]["result"] = gate
    config["run_output_sha256"] = summary["output_sha256"]
    results = {"status": "DEVELOPMENT_ONLY", "arm": "L1e", "quality_gate": gate,
               "input_sha256": summary["input_sha256"], "output_sha256": summary["output_sha256"]}
    results["comparisons"] = {arm: "NOT_RUN" for arm in ARMS[1:]}
    if gate["status"] == "PASS" and gate["full_roster"]:
        prior = freeze.read_json("L1DEV_results.json")
        try:
            l1_summary = json.loads((args.l1_private / "L1DEV_summary.json").read_bytes())
            if l1_summary["output_sha256"] != prior["output_sha256"]:
                raise ValueError("L1 raw output does not match the published digest")
            l1_parsed, _ = spec.read_outputs(args.l1_private / "L1DEV_outputs.jsonl", l1_summary, cohorts[0],
                                             prior["input_sha256"], l1_output=True)
        except (OSError, KeyError, ValueError) as error:
            l1_parsed = None
            results["l1_blocker"] = str(error)
        results["horizons"] = results_for_cohorts(cohorts, parsed, l1_parsed)
        results["comparisons"].update(M3="PASS", B1="PASS")
        if l1_parsed is not None:
            results["comparisons"]["L1"] = "PASS"
    freeze.write_json(RESULTS, results)
    freeze.write_json(CONFIG, config)


def main():
    parser = freeze.parser(__doc__)
    parser.add_argument("mode", choices=("prepare", "score"))
    parser.add_argument("--private", type=Path, default=PRIVATE)
    parser.add_argument("--l1-private", type=Path, default=l1_local.PRIVATE)
    args = parser.parse_args()
    cohorts = l1_local.cohorts(args)
    if args.mode == "prepare":
        prepare(args, cohorts)
    else:
        score(args, cohorts)


if __name__ == "__main__":
    main()
