"""Prepare frozen validation input or score a complete L1DEV run locally."""
from collections import Counter
from datetime import timedelta
import gzip
from hashlib import file_digest, sha256
import json
from pathlib import Path

import numpy as np

import freeze_run as freeze
import l1dev_protocol as spec
from loe_bench import llm_arm, t1v3, t2
from loe_bench.review_metrics import ReviewQueue


t1 = freeze.t1
ARMS = ("L1", "B1", "M3")
METRICS = ("recall", "precision", "average_precision")
PRIVATE = Path(t1.replay.DEFAULT_DIR).parent / "llm_arm"


def jsonl(rows):
    return b"".join((json.dumps(row, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n").encode()
                    for row in rows)


def gsrs_names(path, required):
    found = {}
    with gzip.open(path, "rt", encoding="utf-8") as source:
        for line in source:
            if not line.strip():
                continue
            record = json.loads(line.split("\t", 2)[-1])
            code = record.get("approvalID")
            if code not in required:
                continue
            candidates = [(not item.get("displayName"), not item.get("preferred"), name)
                          for item in record.get("names", []) if (name := " ".join((item.get("name") or "").split()))]
            if candidates:
                if code in found:
                    raise ValueError("duplicate GSRS approval ID in the validation roster")
                found[code] = min(candidates)[2]
    if found.keys() != required:
        raise ValueError("some frozen roster identities do not have pinned GSRS names")
    return found


def entity_name(key, names):
    return " + ".join(names[part[2:]] if part.startswith("U:") else part.removeprefix("E:")
                      for part in key.split("|"))


def cohorts(args):
    t1.require_closed_seal()
    lock = freeze.read_json("FROZEN_CONFIG.json")
    if freeze.manifest("FREEZE_dev_report.json")["sha256"] != lock["development_report_sha256"]:
        raise ValueError("development report SHA-256 differs from the freeze")
    reference = freeze.read_json("FREEZE_dev_report.json")["horizons"]
    for key in ("s0_manifest", "ob_manifest", "piv_manifest", "court_manifest"):
        pin = lock["input_sha256"][key]
        if freeze.manifest(pin["file"]) != pin:
            raise ValueError(f"manifest differs from the freeze: {key}")
    entities, builder, sources = t1.replay.inputs(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir)
    for key in ("s0_files", "gsrs", "orange_book_coverage"):
        if sources[key] != lock["input_sha256"][key]:
            raise ValueError(f"source differs from the freeze: {key}")
    rows_by_h = {}
    for h, (train_days, days) in t1.replay.PRIMARY.items():
        t1.verify_windows(train_days, days, h)
        if tuple(day.isoformat() for day in days) != spec.CUTOFFS[h]:
            raise ValueError("validation schedule differs from the protocol")
        rows = t1.replay.partition(entities, builder, days, h)
        frozen = reference[str(h)]
        counts = Counter(row["t"].isoformat() for row in rows)
        if (counts != {item["cutoff"]: item["rows"] for item in frozen["cutoffs"]}
                or len({row["key"] for row in rows}) != frozen["drug_clusters"]
                or sum(row["y"] for row in rows) != frozen["event_rows"]):
            raise ValueError(f"{h}m partition differs from the development report")
        rows_by_h[h] = sorted(rows, key=lambda row: (row["t"], row["key"]))

    required = {part[2:] for rows in rows_by_h.values() for row in rows
                for part in row["key"].split("|") if part.startswith("U:")}
    names = gsrs_names(args.raw.resolve().parent / "moiety" / sources["gsrs"]["file"], required)
    inputs = [{"entity": entity_name(row["key"], names), "t0": row["t"].isoformat(), "horizon_months": h}
              for h, rows in rows_by_h.items() for row in rows]
    return inputs, rows_by_h, entities, builder, reference


def prepare(args, inputs):
    data = jsonl(inputs)
    digest = sha256(data).hexdigest()
    spec.validate_input(data, digest)
    args.private.mkdir(parents=True, exist_ok=True)
    (args.private / "L1DEV_inputs.jsonl").write_bytes(data)
    stage = freeze.read_json("E4b_stage.json")
    model = stage["model"]
    root = freeze.DATA.parent
    files = ("loe_bench/llm_arm.py", "scripts/l1dev_protocol.py", "scripts/runpod_l1dev.py")
    code = {name: sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest() for name in files}
    config = {
        "status": "FROZEN_FOR_DEVELOPMENT_RUN", "arm": "L1", "role": "secondary exploratory",
        "model": {"id": model["model_id"], "revision": model["revision"], "license": "Apache-2.0",
                  "files": [{k: item[k] for k in ("name", "bytes", "sha256")} for item in model["files"]]},
        "image": stage["pinned_image"], "runtime": {"torch": "2.8.0+cu128", "transformers": "4.55.2"},
        "harness_lf_sha256": code,
        "prompt": {"system_utf8_sha256": sha256(llm_arm.SYSTEM.encode()).hexdigest(),
                   "template_utf8_sha256": sha256(llm_arm.TEMPLATE.encode()).hexdigest(),
                   "source_lf_sha256": code["loe_bench/llm_arm.py"],
                   "chat_template": "pinned tokenizer; add_generation_prompt=true; enable_thinking=false"},
        "decoder": {"dtype": "float16", "do_sample": False, "num_beams": 1, "seed": spec.SEED,
                    "max_new_tokens": spec.MAX_NEW_TOKENS, "batch_size": spec.BATCH_SIZE,
                    "padding_side": "left", "pad_token": "tokenizer EOS", "memory_fraction": spec.MEMORY_FRACTION},
        "parser": {"entrypoint": "loe_bench.llm_arm.parse_response", "schema": ["p_entry", "action", "missing_evidence"],
                   "invalid": "abstain; tie below all valid native scores for queue and AP"},
        "evaluation": {"risk": "p_entry including schema-valid abstentions; ignore action for ranking",
                       "queue": "per-cutoff floor(N/5), expected boundary ties", "ap": "pooled grouped native score AP",
                       "bootstrap": {"unit": "whole drug with common draws for all arms", "draws": t2.BOOTSTRAP_DRAWS,
                                     "seed_per_horizon": t2.BOOTSTRAP_SEED, "interval": "two-sided 95% percentile"},
                       "comparators": ["B1", "M3"], "require_full_roster": True},
        "development_input": {"sha256": digest, "rows": len(inputs), "fields": sorted(spec.FIELDS),
                              "cutoffs": spec.CUTOFFS, "order": "horizon, cutoff, frozen active-moiety key",
                              "name": "pinned GSRS display name then preferred then lexical; native fallback names",
                              "frozen_pipeline_lf_sha256": freeze.manifest("FROZEN_CONFIG.json")["sha256"]},
        "quality_gate": {"rows": spec.GATE_ROWS, "minimum_schema_valid": spec.MINIMUM_VALID},
    }
    freeze.write_json("L1_FROZEN_CONFIG.json", config)
    print(f"{len(inputs)} label-free forecast rows, SHA-256 {digest}", flush=True)


def score_panel(rows, native, days, *, arms=ARMS):
    cutoffs = [row["t"] for row in rows]
    labels = np.array([row["y"] for row in rows])
    _, groups = np.unique([row["key"] for row in rows], return_inverse=True)
    n = int(groups.max()) + 1
    queues = [ReviewQueue(native[arm], cutoffs) for arm in arms]
    zeros = np.zeros(len(rows))

    def measure(copies):
        weights = copies[groups]
        return np.stack([queue.measure(labels, zeros, weights)[:3] for queue in queues])

    full = np.ones(n, dtype=int)
    point = measure(full)
    rng = np.random.default_rng(t2.BOOTSTRAP_SEED)
    draws = np.stack([measure(np.bincount(rng.integers(n, size=n), minlength=n))
                      for _ in range(t2.BOOTSTRAP_DRAWS)])

    def intervals(value, samples):
        return {metric: t1v3.interval(float(x) if np.isfinite(x) else None, column)
                for metric, x, column in zip(METRICS, value, samples.T, strict=True)}

    fractions, slots = queues[0].allocation(full[groups])
    allocations = []
    for day in days:
        idx = np.asarray(cutoffs) == day
        capacity = int(idx.sum()) // t1v3.REVIEW_DIVISOR
        if not np.isclose(fractions[idx].sum(), capacity, rtol=0, atol=1e-9):
            raise ValueError(f"{arms[0]} queue differs from the frozen review budget")
        allocations.append({"cutoff": day.isoformat(), "rows": int(idx.sum()), "capacity": capacity,
                            "boundary_tie_rows": int(((fractions[idx] > 0) & (fractions[idx] < 1)).sum()),
                            "expected_queued_events": float(fractions[idx] @ labels[idx])})
    return {"rows": len(rows), "drug_clusters": n, "event_rows": int(labels.sum()),
            "queue_slots": slots, f"{arms[0]}_cutoffs": allocations,
            "levels": {arm: intervals(point[i], draws[:, i]) for i, arm in enumerate(arms)},
            "contrasts": {f"{arms[0]}-{arm}": intervals(point[0] - point[i], draws[:, 0] - draws[:, i])
                          for i, arm in enumerate(arms) if i}}


def score(args, inputs, rows_by_h, entities, builder, reference):
    plan = freeze.read_json("L1_FROZEN_CONFIG.json")
    expected = plan["development_input"]["sha256"]
    spec.validate_input(jsonl(inputs), expected)
    out = args.private / "L1DEV_outputs.jsonl"
    summary_path = args.private / "L1DEV_summary.json"
    summary = json.loads(summary_path.read_bytes())
    with out.open("rb") as source:
        digest = file_digest(source, "sha256").hexdigest()
    if (summary["status"] != "COMPLETE" or summary["input_sha256"] != expected
            or summary["output_sha256"] != digest or summary["first_200_valid"] < spec.MINIMUM_VALID):
        raise ValueError("a complete, verified run and passing format gate are required")
    outputs = [json.loads(line) for line in out.read_bytes().splitlines()]
    by_h = {h: [] for h in rows_by_h}
    for forecast, output in zip(inputs, outputs, strict=True):
        if any(output[key] != forecast[key] for key in spec.FIELDS):
            raise ValueError("forecast row and output order do not match")
        parsed = llm_arm.parse_response(output["raw_text"])
        if any(output[key] != value for key, value in parsed.items()):
            raise ValueError("remote and local parsers disagree")
        by_h[forecast["horizon_months"]].append(parsed)

    results = {}
    for h, rows in rows_by_h.items():
        train_days, days = t1.replay.PRIMARY[h]
        train = t1.replay.partition(entities, builder, train_days, h, training=True)
        native = t1.native(train, rows, h, min(days) - timedelta(days=1))
        parsed = by_h[h]
        native["L1"] = [row["p_entry"] if row["valid"] else -1.0 for row in parsed]
        result = score_panel(rows, native, days)
        for arm in ("B1", "M3"):
            for metric in METRICS:
                new, old = result["levels"][arm][metric], reference[str(h)]["levels"][arm][metric]
                if (new["undefined_draws"] != old["undefined_draws"]
                        or not np.allclose([new["estimate"], *new["ci95"]], [old["estimate"], *old["ci95"]],
                                           rtol=0, atol=1e-12)):
                    raise ValueError(f"{h}m {arm} {metric} differs from the frozen report")
        result["valid_json"] = sum(row["valid"] for row in parsed)
        result["actions"] = Counter(row["action"] for row in parsed)
        result["parse_errors"] = Counter(row["error"] for row in parsed if not row["valid"])
        results[str(h)] = result
    freeze.write_json("L1DEV_results.json", {"status": "DEVELOPMENT_ONLY", "arm": "L1", "horizons": results,
                                             "input_sha256": expected, "output_sha256": digest})


def main():
    parser = freeze.parser(__doc__)
    parser.add_argument("mode", choices=("prepare", "score"))
    parser.add_argument("--private", type=Path, default=PRIVATE)
    args = parser.parse_args()
    inputs, *details = cohorts(args)
    if args.mode == "prepare":
        prepare(args, inputs)
    else:
        score(args, inputs, *details)


if __name__ == "__main__":
    main()
