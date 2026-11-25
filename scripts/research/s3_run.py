"""S3 freeze, isolated replay and evaluator. Every output is create-only."""

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
from math import floor, ceil
import json
import os
from pathlib import Path
import platform
from random import Random
import statistics
import subprocess
import sys
import tempfile
from time import get_clock_info, perf_counter_ns
import unicodedata

from s1_scorer import LIMITS, score_case
from s3_trace import identities, validate


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT / "docs/evidence-scope/research"
AUDIT = ROOT / "docs/healthtech/audits/S3-20261125"
PIN = AUDIT / "freeze.json"
ORIGINALS = ROOT.parent / "_private_artifacts" / "ptp-s3-20261125"
SEAL = ORIGINALS / "original-captures.json"
NAMES = ("requests", "sources", "units", "edges")
ARMS = ("static", "rerank", "complete_first", "coverage", "scope")
PRIMARY = ("scope", "coverage")
STATES = ("present", "displaced", "outside")
SEED = 20261125
SOURCE_FILES = (
    "scripts/research/s3_policy.py", "scripts/research/s3_trace.py",
    "scripts/research/s3_run.py", "scripts/research/s1_scorer.py",
    "tests/test_s3_policy.py", "docs/evidence-scope/research/MEASUREMENT.md",
    "docs/evidence-scope/FREEZE.md",
)


def digest(path, lf=False):
    data = path.read_bytes()
    return sha256(data.replace(b"\r\n", b"\n") if lf else data).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(path.read_bytes())


def read_rows(path):
    return [json.loads(line) for line in path.read_bytes().splitlines()]


def write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(data, file, ensure_ascii=True, indent=2, sort_keys=True, allow_nan=False)
        file.write("\n")


def environment():
    return dict(python=sys.version, implementation=platform.python_implementation(),
                os=platform.platform(), machine=platform.machine(),
                cpu=platform.processor(), logical_cpus=os.cpu_count(),
                unicode=unicodedata.unidata_version, workers=1, query_threads=1,
                timer=vars(get_clock_info("perf_counter")))


def pins():
    return dict(
        revision="S3-fixed-v2", s1_manifest_sha256=digest(PACKET / "manifest.json"),
        files_lf_sha256={key: digest(ROOT / key, lf=True) for key in SOURCE_FILES},
        ceilings=LIMITS, arms=ARMS, primary=PRIMARY, primary_language="th",
        transfer_language="en", replicates=10_000, resampling_seed=SEED,
    )


def verified_pin(mode):
    frozen = read_json(PIN)
    current = json.loads(json.dumps(pins()))
    if any(frozen[key] != value for key, value in current.items()):
        raise SystemExit("S3 pre-run pin mismatch")
    if mode == "run" and frozen["environment"] != environment():
        raise SystemExit("owner execution environment differs from preregistration")
    manifest = read_json(PACKET / "manifest.json")
    if manifest["limits"] != LIMITS:
        raise SystemExit("S1/S3 budget mismatch")
    return manifest


def load_runtime(manifest, lane, lang):
    data = {}
    for name in NAMES:
        relative = f"runtime/{lane}/{name}.jsonl"
        path = PACKET / relative
        if digest(path) != manifest["files"][relative]["sha256"]:
            raise SystemExit(f"runtime hash mismatch: {relative}")
        data[name] = read_rows(path)
    family_ids = {row["family_id"] for row in data["sources"] if row["language"] == lang}
    for name in ("requests", "sources", "units"):
        data[name] = [row for row in data[name] if row["family_id"] in family_ids]
    ids = {unit["unit_id"] for unit in data["units"]}
    data["edges"] = [edge for edge in data["edges"] if edge["from"] in ids]
    data["requests"] = [
        {key: request[key] for key in ("case_id", "family_id", "question", "language", "seed_pool")}
        for request in data["requests"]
    ]
    if not all(request["language"] == lang for request in data["requests"]):
        raise SystemExit("language mismatch")
    identities(data)
    return data


def run(data, args):
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    write_json(out / "launch.json", dict(
        lane=args.lane, language=args.language, mode=args.command, launched_utc=utc(),
        environment=environment(), freeze_sha256=digest(PIN),
        ordered_case_ids=[row["case_id"] for row in data["requests"]],
    ))
    with tempfile.TemporaryDirectory(prefix="ptp-s3-runtime-") as tmp:
        capsule = Path(tmp)
        worker = capsule / "s3_policy.py"
        worker.write_bytes((ROOT / SOURCE_FILES[0]).read_bytes())
        runtime_hashes = {}
        for name, rows in data.items():
            path = capsule / f"{name}.jsonl"
            path.write_bytes(b"".join((json.dumps(row, ensure_ascii=False) + "\n").encode()
                                      for row in rows))
            runtime_hashes[path.name] = digest(path)
        write_json(out / "capsule.json", runtime_hashes)
        started = perf_counter_ns()
        with (out / "trace.jsonl").open("xb") as stdout, (out / "stderr.txt").open("xb") as stderr:
            status = subprocess.run([sys.executable, "-I", worker.name, "."], cwd=capsule,
                                    stdout=stdout, stderr=stderr, check=False)
        elapsed = perf_counter_ns() - started
    write_json(out / "capture.json", dict(returncode=status.returncode, ended_utc=utc(),
                                         subprocess_elapsed_ns=elapsed,
                                         trace_sha256=digest(out / "trace.jsonl"),
                                         stderr_sha256=digest(out / "stderr.txt")))
    return status.returncode


def read_labels(manifest, lane, case_ids):
    selected = {}
    for name in ("labels", "pairs"):
        key = f"evaluator/{lane}/{name}.jsonl"
        if digest(PACKET / key) != manifest["files"][key]["sha256"]:
            raise SystemExit(f"evaluator hash mismatch: {key}")
        selected[name] = read_rows(PACKET / key)
    labels = {row["case_id"]: row for row in selected["labels"] if row["case_id"] in case_ids}
    pairs = [row for row in selected["pairs"] if set(row["cases"]) <= case_ids]
    if set(labels) != case_ids:
        raise SystemExit("request and label identities differ")
    return labels, pairs


def capture_receipt(output, lane, language, mode):
    launch = read_json(output / "launch.json")
    capture = read_json(output / "capture.json")
    if (launch["lane"], launch["language"], launch["mode"], launch["freeze_sha256"]) != (
        lane, language, mode, digest(PIN)
    ):
        raise SystemExit("launch identity mismatch")
    if any(capture[key] != digest(output / name) for key, name in (
        ("trace_sha256", "trace.jsonl"), ("stderr_sha256", "stderr.txt")
    )):
        raise SystemExit("capture identity mismatch")
    return launch, capture, {name: digest(output / name) for name in (
        "launch.json", "capture.json", "capsule.json", "trace.jsonl", "stderr.txt")}


def original_captures():
    th_launch, th_capture, th = capture_receipt(ORIGINALS / "th", "dev", "th", "run")
    en_launch, _, en = capture_receipt(ORIGINALS / "en", "dev", "en", "run")
    if datetime.fromisoformat(th_capture["ended_utc"]) > datetime.fromisoformat(en_launch["launched_utc"]):
        raise SystemExit("the original captures must run Thai first and execute serially")
    return {"freeze_sha256": th_launch["freeze_sha256"], "th": th, "en": en}


def audit_trials(out, data, labels):
    units, edges = identities(data)
    ingestion = None
    trials = {}
    failures = []
    requests = {row["case_id"]: row for row in data["requests"]}
    for number, line in enumerate((out / "trace.jsonl").read_bytes().splitlines(), 1):
        try:
            trial = json.loads(line)
            if number == 1 and trial["kind"] == "ingestion":
                ingestion = trial
                continue
            key = trial["case_id"], trial["arm"]
            if key[1] not in ARMS or trial["kind"] != "trial":
                raise ValueError("unknown arm or row kind")
            if key in trials:
                trials[key] = {"trace_valid": False, "failure": "duplicate trial"}
                raise ValueError("duplicate trial")
            trials[key] = {"trace_valid": False}
            response = validate(trial, requests[key[0]], units, edges)
            label = labels[key[0]]
            support = sorted(item["unit_id"] for item in response["evidence"] if item["role"] == "support")
            permitted = [set(w["permitted"]) for w in label["witness_assignments"]]
            incompatible = bool(support and not any(set(support) <= allowed for allowed in permitted))
            trials[key] = dict(trace_valid=True, success=score_case(label, response, units),
                               decision=response["decision"], support=support,
                               incompatible=incompatible, usage=response["usage"],
                               elapsed_ns=trial["end_ns"] - trial["start_ns"],
                               cpu_ns=trial["cpu_ns"], stop=trial["stop"])
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            failures.append(dict(line=number, error=str(error)))
    rows = []
    for cid, label in labels.items():
        results = {arm: trials.get((cid, arm), {"trace_valid": False, "failure": "missing"}) for arm in ARMS}
        rows.append(dict(case_id=cid, family_id=label["family_id"], state=label["state"],
                         status=label["status"], arms=results))
    return rows, failures, ingestion


def success(row, arm):
    return row["arms"][arm].get("success", 0)


def counts(rows):
    result = {"n": len(rows)}
    for arm in ARMS:
        result[arm] = sum(success(row, arm) for row in rows)
    method, control = PRIMARY
    result["paired"] = dict(
        improved=sum(success(row, method) > success(row, control) for row in rows),
        worsened=sum(success(row, method) < success(row, control) for row in rows),
        both_correct=sum(success(row, method) == success(row, control) == 1 for row in rows),
        both_failed=sum(success(row, method) == success(row, control) == 0 for row in rows),
    )
    result["delta"] = (result[method] - result[control]) / len(rows) if rows else None
    return result


def effect(rows):
    deltas = [counts([row for row in rows if row["state"] == state])["delta"] for state in STATES]
    return statistics.mean(deltas) if all(delta is not None for delta in deltas) else None


def interval(families):
    rng = Random(SEED)
    groups = [families[key] for key in sorted(families)]
    values = sorted(effect([case for group in rng.choices(groups, k=len(groups)) for case in group])
                    for _ in range(10_000))

    def percentile(p):
        index = (len(values) - 1) * p
        return values[floor(index)] + (index - floor(index)) * (values[ceil(index)] - values[floor(index)])

    return [percentile(0.025), percentile(0.975)]


def aggregate(rows, pairs):
    families = defaultdict(list)
    answerable = [row for row in rows if row["status"] == "ANSWERABLE"]
    finite = [row for row in rows if row["status"] == "FINITE_UNANSWERABLE"]
    for row in answerable:
        families[row["family_id"]].append(row)
    lookup = {row["case_id"]: row for row in rows}
    pair_counts = {role: {"n": 0, **dict.fromkeys(ARMS, 0)} for role in ("invariant", "changing")}
    for pair in pairs:
        role = pair["edit"]
        pair_counts[role]["n"] += 1
        a, b = (lookup[cid] for cid in pair["cases"])
        for arm in ARMS:
            if success(a, arm) and success(b, arm):
                signature_a = tuple(a["arms"][arm][key] for key in ("decision", "support"))
                signature_b = tuple(b["arms"][arm][key] for key in ("decision", "support"))
                pair_counts[role][arm] += (signature_a == signature_b) == (role == "invariant")

    resource = {}
    for arm in ARMS:
        valid = [row["arms"][arm] for row in rows if row["arms"][arm]["trace_valid"]]
        resource[arm] = dict(expected=len(rows), trace_valid=len(valid),
                             failures=len(rows) - len(valid),
                             answers=sum(row["decision"] != "ABSTAIN" for row in valid),
                             abstentions=sum(row["decision"] == "ABSTAIN" for row in valid),
                             incompatible=sum(row["incompatible"] for row in valid),
                             elapsed_ns=sum(row["elapsed_ns"] for row in valid),
                             cpu_ns=sum(row["cpu_ns"] for row in valid),
                             stops=dict(Counter(row["stop"] for row in valid)),
                             **{key: sum(row["usage"][key] for row in valid)
                                for key in ("actions", "inspected", "returned", "model_tokens")},
                             groups={str(key): dict(n=len(group),
                                 actions=sum(row["usage"]["actions"] for row in group),
                                 abstentions=sum(row["decision"] == "ABSTAIN" for row in group),
                                 incompatible=sum(row["incompatible"] for row in group))
                                 for key in (*STATES, None) if (group := [
                                     row["arms"][arm] for row in rows if row["state"] == key
                                     and row["arms"][arm]["trace_valid"]])})
    delta = effect(answerable)
    return dict(total=counts(answerable), finite=counts(finite),
                excluded=len(rows) - len(answerable) - len(finite), delta=delta,
                interval=interval(families) if delta is not None else None,
                states={key: counts([row for row in answerable if row["state"] == key]) for key in STATES},
                families={key: counts(group) | {"states": {
                    state: counts([row for row in group if row["state"] == state])
                    for state in STATES}} for key, group in families.items()},
                pairs=pair_counts, resources=resource)


def main():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("freeze")
    subs.add_parser("seal-originals")
    for action in ("run", "replay-audit", "score", "score-audit"):
        command = subs.add_parser(action)
        command.add_argument("lane", choices=("proposal", "selection", "dev"))
        command.add_argument("language", choices=("th", "en"))
        command.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "freeze":
        PIN.parent.mkdir(parents=True, exist_ok=True)
        write_json(PIN, pins() | {"frozen_utc": utc(), "environment": environment()})
        return 0
    manifest = verified_pin(args.command)
    if args.command == "seal-originals":
        write_json(SEAL, original_captures() | {"sealed_utc": utc()})
        return 0
    is_original = args.command in ("run", "score")
    if args.lane == "dev" and is_original:
        if args.output.resolve() != (ORIGINALS / args.language).resolve():
            raise SystemExit("the original DEV capture must use its canonical path")
        if args.command == "run" and args.language == "en":
            capture_receipt(ORIGINALS / "th", "dev", "th", "run")
        if args.command == "score":
            sealed = read_json(SEAL)
            if any(sealed[key] != value for key, value in original_captures().items()):
                raise SystemExit("the original capture seal differs")
    elif args.output.resolve() in ((ORIGINALS / "th").resolve(), (ORIGINALS / "en").resolve()):
        raise SystemExit("the canonical path is reserved for the original DEV capture")
    data = load_runtime(manifest, args.lane, args.language)
    if args.command in ("run", "replay-audit"):
        return run(data, args)
    mode = "run" if is_original else "replay-audit"
    launch, capture, _ = capture_receipt(args.output, args.lane, args.language, mode)
    labels, pairs = read_labels(manifest, args.lane, {row["case_id"] for row in data["requests"]})
    rows, failures, ingestion = audit_trials(args.output, data, labels)
    write_json(args.output / "case-results.json", rows)
    write_json(args.output / "summary.json", aggregate(rows, pairs) | {
        "failures": failures, "ingestion": ingestion, "capture": capture, "launch": launch})
    return 0


if __name__ == "__main__":
    sys.exit(main())
