"""Freeze, capture and replay the local RA Pharma engineering fixture."""
import argparse
import json
from pathlib import Path
from time import perf_counter, process_time

from fixture_policy import READ_LIMIT, correct, cost, diagnose, digest, learn

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / "docs/ra-pharma/research/fixtures"
FILES = (
    "docs/ra-pharma/research/PROTOCOL.md", "docs/ra-pharma/research/FIXTURES.md",
    "docs/ra-pharma/research/fixtures/train-runtime.json",
    "docs/ra-pharma/research/fixtures/train-key.json",
    "docs/ra-pharma/research/fixtures/diagnostic-runtime.json",
    "docs/ra-pharma/research/fixtures/diagnostic-key.json",
    "scripts/research/ra_pharma/fixture_policy.py", "scripts/research/ra_pharma/fixture_run.py",
)
LOCK = PACKET / "freeze.json"
ORIGINAL = PACKET / "original"
ARM_NAMES = ("single", "fixed", "learned", "learned_without_role", "learned_unverified")


def read(path):
    return json.loads(path.read_bytes())


def write(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(data, output, indent=2, sort_keys=True, ensure_ascii=False)
        output.write("\n")


def freeze():
    write(LOCK, {
        "scope": "authored synthetic engineering fixtures only",
        "output_path": ORIGINAL.relative_to(ROOT).as_posix(),
        "inputs": {name: digest((ROOT / name).read_bytes()) for name in FILES},
    })


def verify_freeze():
    # Verify all hashes, except the diagnostic evaluator bytes until traces are sealed.
    lock = read(LOCK)
    if lock["output_path"] != ORIGINAL.relative_to(ROOT).as_posix():
        raise ValueError("unexpected output path in fixture freeze")
    locked = lock["inputs"]
    if set(locked) != set(FILES):
        raise ValueError("unexpected inventory in fixture freeze")
    for name, expected in locked.items():
        if not name.endswith("/diagnostic-key.json") and digest((ROOT / name).read_bytes()) != expected:
            raise ValueError(f"frozen asset changed: {name}")
    return locked


def capture(path):
    verify_freeze()
    path.mkdir(parents=True, exist_ok=False)
    started, cpu = perf_counter(), process_time()
    skills, ledger = learn(read(PACKET / "train-runtime.json"), read(PACKET / "train-key.json"))
    write(path / "skill.json", {"version": 1, "routes_by_role": skills, "training": ledger,
                                 "wall_seconds": perf_counter() - started, "cpu_seconds": process_time() - cpu})
    started, cpu = perf_counter(), process_time()
    cases = read(PACKET / "diagnostic-runtime.json")
    traces = list(diagnose(cases, read(path / "skill.json")["routes_by_role"]))
    write(path / "traces.json", {"traces": traces, "wall_seconds": perf_counter() - started,
                                "cpu_seconds": process_time() - cpu})
    write(path / "seal.json", {
        "freeze_sha256": digest(LOCK.read_bytes()),
        "captures": {name: digest((path / name).read_bytes()) for name in ("skill.json", "traces.json")},
    })


def evaluate(output, key):
    actions = output["actions"]
    outgoing = output["outgoing"]
    answered = outgoing["status"] == "supported"
    supported = correct(output, key)
    unread = set(key["permitted_sources"]) - {action["source_id"] for action in actions}
    issued = outgoing["sources"][0]["source_id"] if answered else None
    return {
        "answered": answered, "correct": supported, "unsupported": answered and not supported,
        "abstained": not answered, "known_missing": not key["permitted_sources"],
        "wrong_subject": issued in key["wrong_subject_sources"],
        "wrong_product": (issued in key["wrong_subject_sources"]
                          and outgoing["evidence_role"] == "applicant_result"),
        "harmful_stop": bool(unread) and len(actions) < READ_LIMIT and output["stop"] == "topic",
        "choice": bool(actions) and len(actions[0]["routes_available"]) > 1,
        **cost(actions),
    }


def validate_trace(row, case):
    arms = row["arms"]
    if set(arms) != set(ARM_NAMES):
        raise ValueError(f"wrong arm inventory: {row['case']}")
    if arms["single"]["actions"] != arms["fixed"]["actions"] or any(
        arms[arm]["actions"] != arms["learned"]["actions"]
        for arm in ("learned_without_role", "learned_unverified")
    ):
        raise ValueError(f"action parity failed: {row['case']}")
    for arm, trace in arms.items():
        remaining = {c["id"]: c for c in case["candidates"]}
        if len(trace["actions"]) > READ_LIMIT:
            raise ValueError(f"read cap exceeded: {row['case']}")
        for action in trace["actions"]:
            source_id = action["source_id"]
            source = case["sources"][source_id]
            text = source["text"].encode("utf-8")
            available = sorted({c["route"] for c in remaining.values()})
            if (action["inspections"], action["routes_available"]) != (len(remaining), available):
                raise ValueError(f"candidate ledger mismatch: {source_id}")
            candidate = remaining.pop(source_id)
            if (action["route"], action["locator"], action["issuer"], action["version"],
                    action["bytes"], action["sha256"]) != (
                    candidate["route"], source["locator"], source["issuer"], source["edition"],
                    len(text), digest(text)):
                raise ValueError(f"source identity mismatch: {source_id}")
        for item in (trace["evidence"], trace["outgoing"]):
            if item and item["trace_id"] != f"{row['case']}/{arm}":
                raise ValueError(f"handoff trace ID mismatch: {row['case']}")
            if item and item["status"] == "supported":
                if item["sources"] != [trace["actions"][-1] | {"source_owner": source["issuer"]}]:
                    raise ValueError(f"handoff source mismatch: {row['case']}")


def score(path):
    locked = verify_freeze()
    seal = read(path / "seal.json")
    if seal["freeze_sha256"] != digest(LOCK.read_bytes()):
        raise ValueError("capture freeze mismatch")
    if set(seal["captures"]) != {"skill.json", "traces.json"}:
        raise ValueError("capture seal does not cover both artifacts")
    for name, expected in seal["captures"].items():
        if digest((path / name).read_bytes()) != expected:
            raise ValueError(f"capture changed: {name}")
    key_bytes = (PACKET / "diagnostic-key.json").read_bytes()
    if digest(key_bytes) != locked["docs/ra-pharma/research/fixtures/diagnostic-key.json"]:
        raise ValueError("diagnostic key mismatch")
    keys = json.loads(key_bytes)
    traces = read(path / "traces.json")["traces"]
    if len({row["case"] for row in traces}) != len(traces) or {row["case"] for row in traces} != keys.keys():
        raise ValueError("trace and key case inventories differ")
    cases = {case["id"]: case for case in read(PACKET / "diagnostic-runtime.json")}
    for row in traces:
        validate_trace(row, cases[row["case"]])
    rows = {
        row["case"]: {arm: evaluate(output, keys[row["case"]]) for arm, output in row["arms"].items()}
        for row in traces
    }
    totals = {
        arm: {field: sum(row[arm][field] for row in rows.values()) for field in metrics}
        for arm, metrics in next(iter(rows.values())).items()
    }
    strata = {}
    for label, case_ids in (
        ("training_template_echo", [key for key in rows if key in {"d01", "d02", "d03", "d04"}]),
        ("additional_authored", [key for key in rows if key not in {"d01", "d02", "d03", "d04"}]),
    ):
        strata[label] = {"cases": case_ids, "correct": {
            arm: sum(rows[case][arm]["correct"] for case in case_ids) for arm in ARM_NAMES
        }}
    pairs = {}
    for control, candidate in (("single", "fixed"), ("fixed", "learned"),
                               ("learned", "learned_without_role"), ("learned", "learned_unverified")):
        matched = [v for v in rows.values() if v[control]["answered"] and v[candidate]["answered"]]
        pairs[f"{control} -> {candidate}"] = {
            "both_answered": len(matched),
            "unsupported_control": sum(row[control]["unsupported"] for row in matched),
            "unsupported_candidate": sum(row[candidate]["unsupported"] for row in matched),
            "gained_correct": [case for case, row in rows.items()
                               if not row[control]["correct"] and row[candidate]["correct"]],
            "lost_correct": [case for case, row in rows.items()
                             if row[control]["correct"] and not row[candidate]["correct"]],
        }
    same_actions = sum(row["arms"]["learned"]["actions"] == row["arms"]["learned_unverified"]["actions"]
                       for row in traces)
    ceiling = sum(bool(actions := row["arms"]["fixed"]["actions"])
                  and actions[0]["source_id"] in keys[row["case"]]["permitted_sources"] for row in traces)
    return {"cases": rows, "totals": totals, "strata": strata, "pairs": pairs, "first_read_ceiling": ceiling,
            "ablation_action_parity": same_actions, "natural_cases": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "capture", "score", "verify"))
    parser.add_argument("output", nargs="?", type=Path)
    args = parser.parse_args()
    if args.command == "freeze":
        freeze()
        return
    if args.output is None or args.output.resolve() != ORIGINAL.resolve():
        parser.error(f"frozen output path required: {ORIGINAL}")
    if args.command == "capture":
        capture(args.output)
    elif args.command == "score":
        write(args.output / "summary.json", score(args.output))
    elif score(args.output) != read(args.output / "summary.json"):
        raise SystemExit("retained summary differs from sealed replay")


if __name__ == "__main__":
    main()
