"""Create-only fixture capture, protocol lock and separately authorized evaluation."""

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import runpy
import subprocess
import sys
import tempfile
from time import perf_counter_ns, get_clock_info
import unicodedata

from alt_evaluate import ARMS, IDENTITY, LIMITS, SEED, interval, matched_risk, score_case, validate_labels
from alt_evaluate import validate_packet, validate_trace


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/evidence-scope/alternative-evidence"
PACKET = DOCS / "packet"
LOCK = DOCS / "freeze.json"
ORIGINAL = ROOT.parent / "_private_artifacts" / "ptp-alt-evidence-20261125" / "original"
LANES = ("th", "en", "natural-th", "natural-en")
PRIMARY = ("assignments", "premise")
FROZEN = (
    "scripts/research/alt_policy.py", "scripts/research/alt_evaluate.py",
    "scripts/research/alt_experiment.py", "tests/test_alt_policy.py",
    "docs/evidence-scope/alternative-evidence/PROTOCOL.md",
    "docs/evidence-scope/05-alternative-evidence-literature.md",
    "docs/evidence-scope/alternative-evidence/fixture-checks.json",
)


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(path, lf=False):
    data = path.read_bytes()
    return sha256(data.replace(b"\r\n", b"\n") if lf else data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def write(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(value, file, indent=2, sort_keys=True, ensure_ascii=False)
        file.write("\n")


def environment():
    return dict(python=sys.version, platform=platform.platform(), cpu=platform.processor(),
                unicode=unicodedata.unidata_version, workers=1, threads=1,
                timer=vars(get_clock_info("perf_counter")), available_cpus=os.cpu_count())


def lock_payload():
    files = [ROOT / path for path in FROZEN]
    files.extend(sorted(path for path in PACKET.rglob("*") if path.is_file()
                        and "__pycache__" not in path.parts))
    return dict(protocol="alternative-evidence-v2", arms=ARMS, primary=PRIMARY,
                limits=LIMITS, minimum_delta=0.05, resamples=10_000, seed=SEED,
                files_lf_sha256={path.relative_to(ROOT).as_posix(): digest(path, lf=True)
                                 for path in files})


def validate_lanes():
    groups = {}
    ancestors = {}
    issued_cases = set()
    counts = {}
    for lane in LANES:
        packet = read(PACKET / lane / "runtime.json")
        label_data = read(PACKET / lane / "labels.json")
        _, families, _, requests = validate_packet(packet)
        labels = validate_labels(label_data, requests, families)
        require_lang = lane.rsplit("-", 1)[-1]
        if any(request["language"] != require_lang for request in requests.values()):
            raise ValueError(f"language mismatch for {lane}")
        if issued_cases & requests.keys():
            raise ValueError(f"case identity reused across lanes: {lane}")
        issued_cases.update(requests)
        for family in families:
            if family in groups or family.startswith(("s1-", "alt-fixture-", "demo-")):
                raise ValueError(f"family leakage: {family}")
            groups[family] = lane
        for source in packet["sources"]:
            family = source["family_id"]
            for identity in (("document", source["source_id"]), ("content", source["sha256"])):
                if ancestors.setdefault(identity, family) != family:
                    raise ValueError(f"source or exact content reused across families: {identity[0]}")
        counts[lane] = dict(families=len(families), cases=len(labels),
                            statuses=Counter(row["status"] for row in labels.values()),
                            strata=Counter(row["stratum"] for row in labels.values()),
                            pairs=Counter(row["kind"] for row in label_data["pairs"]))
    return counts


def freeze():
    counts = validate_lanes()
    write(LOCK, lock_payload() | {"frozen_utc": utc(), "environment": environment(),
                                  "packet_counts": counts})


def verify():
    frozen = read(LOCK)
    if any(frozen[key] != value for key, value in json.loads(json.dumps(lock_payload())).items()):
        raise SystemExit("prospective lock mismatch")
    if frozen["packet_counts"] != validate_lanes():
        raise SystemExit("packet counts differ")
    return frozen


def projected(packet):
    allowed = {
        "sources": ("source_id", "version", "language", "family_id", "text", "sha256"),
        "units": (*IDENTITY, "family_id", "root", "topic", "facts", "answer"),
        "edges": ("from", "to", "kind", "basis"),
        "requests": ("case_id", "family_id", "language", "question", "topic", "conditions", "seed"),
    }
    return {name: [{key: row[key] for key in columns} for row in packet[name]]
            for name, columns in allowed.items()}


def capture(packet, out):
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="ptp-alt-evidence-") as temp:
        temp = Path(temp)
        worker = temp / "alt_policy.py"
        worker.write_bytes((ROOT / FROZEN[0]).read_bytes())
        runtime = temp / "runtime.json"
        write(runtime, projected(packet))
        write(out / "launch.json", dict(
            utc=utc(), environment=environment(), runtime_sha256=digest(runtime),
            worker_lf_sha256=digest(worker, lf=True), command=["python", "-I", worker.name, runtime.name],
            ordered_cases=[row["case_id"] for row in packet["requests"]],
        ))
        began = perf_counter_ns()
        with (out / "trace.jsonl").open("xb") as stdout, (out / "stderr.txt").open("xb") as stderr:
            try:
                process = subprocess.run([sys.executable, "-I", worker.name, runtime.name],
                                         cwd=temp, stdout=stdout, stderr=stderr, timeout=120,
                                         check=False)
                code = process.returncode
            except subprocess.TimeoutExpired:
                code = "TIMEOUT"
    write(out / "capture.json", dict(utc=utc(), returncode=code, elapsed_ns=perf_counter_ns() - began,
                                     trace_sha256=digest(out / "trace.jsonl"),
                                     stderr_sha256=digest(out / "stderr.txt")))


def audit_capture(packet, labels, out):
    units, families, edges, requests = validate_packet(packet)
    results = {}
    duplicate = set()
    failures = []
    ingestion = None
    for i, line in enumerate((out / "trace.jsonl").read_bytes().splitlines(), 1):
        try:
            trace = json.loads(line)
            if i == 1 and trace.get("kind") == "ingestion":
                ingestion = trace
                continue
            cid, arm = trace["case_id"], trace["arm"]
            key = cid, arm
            if key in results or key in duplicate:
                results.pop(key, None)
                duplicate.add(key)
                raise ValueError("duplicate trace")
            request = requests[cid]
            label = labels[cid]
            usage = validate_trace(trace, request, units, families[request["family_id"]], edges)
            support = {item["unit_id"] for item in trace["evidence"]}
            answered = trace["response"] != "ABSTAIN"
            allowed = [set(row["permitted"]) for row in label["witness_assignments"]]
            results[key] = dict(trace_valid=True, hit=score_case(label, trace, usage),
                                response=trace["response"], support=sorted(support),
                                answered=answered, wrong_scope=bool(answered and
                                    not any(support <= witness for witness in allowed)),
                                usage=usage, disposition=trace["disposition"],
                                cpu_ns=trace["cpu_ns"], elapsed_ns=trace["end_ns"] - trace["start_ns"],
                                plan_ns=sum(event.get("plan_ns", 0) for event in trace["events"]),
                                actions=[{k: e[k] for k in ("kind", "opened", "inspected", "graph_reads")}
                                         | ({"target": e["plan"]["target"]} if "plan" in e else {})
                                         for e in trace["events"]])
        except (ValueError, KeyError, TypeError, AttributeError) as error:
            failures.append(dict(line=i, reason=str(error)))
    rows = []
    for cid, label in labels.items():
        arms = {arm: results.get((cid, arm), dict(
            trace_valid=False, hit=None if label["status"] == "UNADJUDICATED" else 0,
            answered=False, wrong_scope=False)) for arm in ARMS}
        rows.append({k: label.get(k) for k in ("case_id", "family_id", "status", "stratum")}
                    | {"arms": arms, "gold_decision": label["decision"]})
    return rows, failures, ingestion


def counts(rows, left, right):
    differences = [row["arms"][left]["hit"] - row["arms"][right]["hit"] for row in rows]
    return dict(n=len(rows), wins=differences.count(1), losses=differences.count(-1),
                ties=differences.count(0), delta=sum(differences) / len(rows) if rows else None,
                hits={arm: sum(row["arms"][arm]["hit"] for row in rows) for arm in ARMS})


def summarize(rows, pairs):
    answerable = [row for row in rows if row["status"] == "ANSWERABLE"]
    finite = [row for row in rows if row["status"] == "FINITE_UNANSWERABLE"]
    relevant = answerable + finite
    inventory = {row["case_id"]: row for row in rows}
    contrasts = {}
    for left, right in (PRIMARY, ("assignments", "no_disagreement")):
        valid_pairs = [(row["arms"][left], row["arms"][right]) for row in answerable
                       if row["arms"][left]["trace_valid"] and row["arms"][right]["trace_valid"]]
        same_actions = sum(
            [(event["kind"], event["opened"]) for event in a["actions"]] ==
            [(event["kind"], event["opened"]) for event in b["actions"]]
            for a, b in valid_pairs)
        same_outputs = sum((a["response"], a["support"]) == (b["response"], b["support"])
                           for a, b in valid_pairs)
        contrasts[f"{left}-{right}"] = (
            counts(answerable, left, right) | {"interval_95": interval(answerable, left, right),
                "matched_risk": matched_risk(relevant, left, right),
                "equivalence_diagnostic": dict(valid_pairs=len(valid_pairs),
                    same_action_sequences=same_actions, same_outputs=same_outputs)})
    pair_rows = []
    same_answer_cases = set()
    for pair in pairs:
        first, second = (inventory[cid] for cid in pair["cases"])
        a, b = first["arms"], second["arms"]
        same_literal = first["gold_decision"] == second["gold_decision"]
        if pair["kind"] == "changing" and same_literal:
            same_answer_cases.update(pair["cases"])
        pair_rows.append(dict(kind=pair["kind"], pair=pair["pair_id"], same_literal=same_literal, success={
            arm: bool(a[arm]["hit"] and b[arm]["hit"] and
                      ((a[arm]["response"], a[arm]["support"]) ==
                       (b[arm]["response"], b[arm]["support"])) == (pair["kind"] == "invariant"))
            for arm in ARMS}))
    same_answer = [row for row in answerable if row["case_id"] in same_answer_cases]
    return dict(answerable=counts(answerable, *PRIMARY), contrasts=contrasts,
                same_answer_changed_scope=counts(same_answer, *PRIMARY) | {
                    "interval_95": interval(same_answer, *PRIMARY)},
                finite=counts(finite, *PRIMARY), unadjudicated=len(rows) - len(relevant),
                by_family={key: counts([row for row in answerable if row["family_id"] == key], *PRIMARY)
                           for key in sorted({row["family_id"] for row in answerable})},
                by_stratum={key: counts([row for row in answerable if row["stratum"] == key], *PRIMARY)
                            for key in sorted({row["stratum"] for row in answerable})},
                arms={arm: dict(
                    valid=sum(row["arms"][arm]["trace_valid"] for row in rows),
                    answers=sum(row["arms"][arm]["answered"] for row in relevant),
                    wrong_scope=sum(row["arms"][arm]["wrong_scope"] for row in relevant),
                    timing_ns={key: sum(row["arms"][arm].get(key, 0) for row in rows)
                               for key in ("elapsed_ns", "cpu_ns", "plan_ns")},
                    usage={key: sum(row["arms"][arm].get("usage", {}).get(key, 0) for row in rows)
                           for key in LIMITS}
                ) for arm in ARMS}, controlled_pairs=pair_rows)


def fixtures(output):
    factory = runpy.run_path(str(ROOT / "tests/test_alt_policy.py"))["development_fixtures"]
    output.mkdir(parents=True, exist_ok=False)
    compact = []
    for packet, label in factory():
        family = label["family_id"]
        dest = output / family
        capture(packet, dest)
        rows, failures, ingest = audit_capture(packet, {label["case_id"]: label}, dest)
        write(dest / "case-results.json", rows)
        if failures or ingest is None or any(not value["trace_valid"] for value in rows[0]["arms"].values()):
            raise ValueError(f"invalid development trace: {family}")
        compact.extend(rows)
    write(output / "fixture-checks.json", compact)


def evaluate(output, authorization):
    if output.resolve() != ORIGINAL.resolve():
        raise SystemExit("reserved run must use the canonical original path")
    frozen = verify()
    approval = read(authorization)
    if (approval.get("freeze_sha256") != digest(LOCK) or approval.get("authorization") != "run-reserved"
            or not approval.get("reviewer") or not approval.get("evidence")):
        raise SystemExit("reserved run requires a post-checkpoint authorization for this lock")
    if frozen["environment"] != environment():
        raise SystemExit("execution environment differs from the frozen reference")
    output.mkdir(parents=True, exist_ok=False)
    write(output / "authorization.json", approval | {
        "original_started_utc": utc(), "registered_path": str(ORIGINAL),
    })
    for lane in LANES:
        capture(read(PACKET / lane / "runtime.json"), output / lane)
    seal = {lane: {name: digest(output / lane / name) for name in (
        "launch.json", "capture.json", "trace.jsonl", "stderr.txt")} for lane in LANES}
    write(output / "raw-seal.json", dict(freeze_sha256=digest(LOCK), sealed_utc=utc(), lanes=seal))
    for lane in LANES:
        packet = read(PACKET / lane / "runtime.json")
        label_data = read(PACKET / lane / "labels.json")
        labels = {label["case_id"]: label for label in label_data["cases"]}
        dest = output / lane
        if any(digest(dest / name) != value for name, value in seal[lane].items()):
            raise SystemExit(f"sealed capture changed for {lane}")
        rows, failures, ingestion = audit_capture(packet, labels, dest)
        write(dest / "case-results.json", rows)
        write(dest / "summary.json", summarize(rows, label_data["pairs"]) |
              {"trace_failures": failures, "ingestion": ingestion})


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("validate-packet", "freeze", "verify"):
        commands.add_parser(command)
    commands.add_parser("fixtures").add_argument("output", type=Path)
    held = commands.add_parser("evaluate")
    held.add_argument("output", type=Path)
    held.add_argument("--authorization", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "fixtures":
        fixtures(args.output)
    elif args.command == "validate-packet":
        print(json.dumps(validate_lanes(), indent=2))
    elif args.command == "freeze":
        freeze()
    elif args.command == "verify":
        print(json.dumps(verify()["packet_counts"], indent=2))
    else:
        evaluate(args.output, args.authorization)


if __name__ == "__main__":
    main()
