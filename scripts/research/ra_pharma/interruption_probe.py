"""One exposed comparison of safe attachment completion under interruption."""
import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path
from time import perf_counter, process_time

ROOT = Path(__file__).resolve().parents[3]
LOCK = ROOT / "docs/ra-pharma/research/interruption/freeze.json"
ARMS = ("fixed_domain", "nearest_complete", "budget_forecast")
CAP = 2


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified(path, expected):
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"hash mismatch: {path.name}")
    return data


def choose(arm, catalog, request, pending, remaining):
    reads = []
    follow = []
    for card in catalog:
        rows = pending.intersection(card["advertises"])
        if not rows:
            continue
        if card["kind"] == "locator":
            if remaining >= 2:
                follow.append((card, rows))
        elif card["scope"] is None or card["scope"] == request:
            certainty = 0.5 if card["scope"] is None else 1.0
            reads.append((card, rows, certainty))

    descriptors = len(catalog)
    direct = [(len(rows)*p, len(rows)*p, card) for card, rows, p in reads]
    postponed = [(len(rows)*0.8, 0.0, card) for card, rows in follow]
    if arm == "fixed_domain":
        exact = [entry for entry in direct if entry[2]["scope"] == request]
        options = exact or postponed or direct
    elif arm == "nearest_complete":
        options = direct or postponed
    elif arm == "budget_forecast":
        options = direct + postponed
        if remaining >= 2:
            for (a, a_rows, p), (b, b_rows, q) in combinations(reads, 2):
                joint = len(a_rows)*p + len(b_rows)*q - len(a_rows & b_rows)*p*q
                options.extend(((joint, len(a_rows)*p, a), (joint, len(b_rows)*q, b)))
    else:
        raise ValueError(f"unknown arm: {arm}")
    preferred = min(options, key=lambda x: (-x[0], -x[1], digest(x[2]["id"].encode())), default=None)
    ledger = {"descriptor_checks": descriptors, "ranked_plan_options": len(options)}
    return preferred[2] if preferred else None, ledger


def run_case(packet, arm):
    catalog = {card["id"]: card for card in packet["catalog"]}
    supported = {}
    actions = []
    while len(actions) < CAP and len(supported) < len(packet["rows"]):
        remaining = CAP - len(actions)
        pending = set(packet["rows"]) - supported.keys()
        chosen, effort = choose(arm, catalog.values(), packet["request"], pending, remaining)
        if not chosen:
            break
        in_id = chosen["id"]
        raw = packet["documents"][in_id].encode("utf-8")
        doc = json.loads(raw)
        event = {"id": in_id, "kind": doc["kind"], "bytes": len(raw), "sha256": digest(raw), **effort}
        catalog.pop(in_id)
        if doc["kind"] == "locator":
            card = doc["follow"]
            if card is not None:
                if card["id"] in catalog or card["id"] in {entry["id"] for entry in actions} or card["id"] == in_id:
                    raise ValueError("duplicate follow-up descriptor")
                catalog[card["id"]] = card
            event["revealed"] = card
        else:
            accepted = doc["role"] == "applicant_result" and doc["scope"] == packet["request"]
            event["scope_pass"] = accepted
            if accepted:
                for row in sorted(pending.intersection(doc["results"])):
                    if doc["results"][row]:
                        supported[row] = {"source": in_id, "locator": f"/results/{row}", "sha256": digest(raw)}
        event["after"] = supported.copy()
        actions.append(event)
    return {"actions": actions, "outgoing": supported, "absent_rows": [r for r in packet["rows"] if r not in supported]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    lock_raw = LOCK.read_bytes()
    lock = json.loads(lock_raw)
    if Path(lock["directory"]).resolve() != args.directory.resolve():
        raise ValueError("output path differs from the engineering freeze")
    for name, expected in lock["capture_inputs"].items():
        verified(ROOT / name, expected)
    start, cpu = perf_counter(), process_time()
    raw = verified(args.directory / "runtime.json", lock["runtime_sha256"])
    runtime = json.loads(raw)
    prep_wall = perf_counter() - start
    prep_cpu = process_time() - cpu
    start, cpu = perf_counter(), process_time()
    traces = {case["id"]: {arm: run_case(case, arm) for arm in ARMS} for case in runtime}
    record = {"lock_sha256": digest(lock_raw), "runtime_bytes": len(raw),
              "preprocessing_wall_seconds": prep_wall, "preprocessing_cpu_seconds": prep_cpu,
              "policy_wall_seconds": perf_counter() - start, "policy_cpu_seconds": process_time() - cpu,
              "traces": traces}
    with (args.directory / "original.json").open("x", encoding="utf-8", newline="\n") as f:
        json.dump(record, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    main()
