"""Score a sealed development interruption trace from its separate generator-state key."""
import argparse
import json
from collections import Counter
from pathlib import Path

from interruption_probe import ARMS, CAP, LOCK, ROOT, digest, verified


def evaluate(capture, keys):
    traces = capture["traces"]
    if traces.keys() != keys.keys() or any(set(arms) != set(ARMS) for arms in traces.values()):
        raise ValueError("missing or unexpected dossier or arm")
    by_case = {}
    for case, arms in traces.items():
        key = keys[case]
        valid = key["valid"]
        scores = {}
        for arm, trace in arms.items():
            events = trace["actions"]
            ids = {e["id"] for e in events}
            if len(events) > CAP or len(events) != len(ids):
                raise ValueError(f"cap or duplicate-source violation: {case}/{arm}")
            previous = {}
            opened = {}
            for event in events:
                opened[event["id"]] = event
                if any(name not in event["after"] or event["after"][name] != value
                       for name, value in previous.items()):
                    raise ValueError("a settled assertion changed")
                for ref in event["after"].values():
                    if ref["source"] not in opened or ref["sha256"] != opened[ref["source"]]["sha256"]:
                        raise ValueError("assertion was not tied to an observed source")
                previous = event["after"]
            out = trace["outgoing"]
            if out != previous or set(valid) != set(out).union(trace["absent_rows"]):
                raise ValueError("final assertion inventory differs from trace")
            first = events[0]["after"] if events else {}

            def supported(rows):
                return sum(ref["source"] in valid[row] and ref["locator"] == valid[row][ref["source"]]
                           for row, ref in rows.items())

            after_cap, after_one = supported(out), supported(first)
            scores[arm] = {
                "correct": after_cap, "prefix_one_correct": after_one, "unsupported": len(out) - after_cap,
                "correct_abstentions": sum(not valid[row] for row in trace["absent_rows"]),
                "missed_answerable": sum(bool(valid[row]) for row in trace["absent_rows"]),
                "actions": len(events), "bytes": sum(e["bytes"] for e in events),
                "mismatch_opens": sum(e.get("scope_pass") is False for e in events),
                "empty_locator_opens": sum(e["kind"] == "locator" and not e["revealed"] for e in events),
                "descriptor_checks": sum(e["descriptor_checks"] for e in events),
                "ranked_plan_options": sum(e["ranked_plan_options"] for e in events),
                "read_order": [e["id"] for e in events], "first_action_kind": events[0]["kind"] if events else None,
            }
        by_case[case] = {"family": key["family"], "layout": key["layout"], "arms": scores}

    totals = {arm: Counter() for arm in ARMS}
    strata = {}
    for case in by_case.values():
        summary = strata.setdefault(case["layout"], {arm: Counter() for arm in ARMS})
        for arm, metrics in case["arms"].items():
            subset = {k: v for k, v in metrics.items() if type(v) is int}
            totals[arm].update(subset)
            summary[arm].update(subset)
    return {"outcomes": by_case, "totals": totals, "by_layout": strata,
            "primary_delta_rows": totals["budget_forecast"]["correct"] - totals["nearest_complete"]["correct"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("original_sha256")
    args = parser.parse_args()
    lock_raw = LOCK.read_bytes()
    lock = json.loads(lock_raw)
    verified(ROOT / lock["scorer"]["path"], lock["scorer"]["sha256"])
    capture = json.loads(verified(args.directory / "original.json", args.original_sha256))
    if capture["lock_sha256"] != digest(lock_raw) or Path(lock["directory"]).resolve() != args.directory.resolve():
        raise ValueError("this trace path or freeze is not authorized")
    key = json.loads(verified(args.directory / "key.json", lock["key_sha256"]))
    print(json.dumps(evaluate(capture, key), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
