"""Score one sealed page-2 original with the independently keyed D31 rules."""
import argparse
import json
from collections import Counter
from pathlib import Path
from time import perf_counter, process_time

from ocs_correspondence_score import evaluate as score_d31
from ocs_extract_pair import ARMS, LOCK, ROOT, verified

D31_NAMES = {"issue_conditioned": "adaptive_page", "lexical_diversity": "exact_conflict",
             "d31_fixed": "literal_lexical"}


def evaluate(original, key, canonical):
    projected = {}
    for identifier, arms in original["traces"].items():
        if set(arms) != set(ARMS):
            raise ValueError("unexpected arm inventory")
        fixed = arms["d31_fixed"]
        if any((trace.get("identity") != fixed.get("identity") or trace["actions"] != fixed["actions"])
               for trace in arms.values()):
            raise ValueError("arm changed the common document binding or actions")
        projected[identifier] = {d31_name: arms[name] for name, d31_name in D31_NAMES.items()}
    report = score_d31({"traces": projected}, key, canonical)

    totals = {}
    for name, earlier in D31_NAMES.items():
        totals[name] = report["totals"][earlier]
        totals[name]["options_evaluated"] = sum(
            row[name]["options_evaluated"] for row in original["traces"].values()
        )
        totals[name]["window_cap_stops"] = sum(row[name]["window_cap_stop"] for row in original["traces"].values())
    counts = Counter(both_complete=0, candidate_only=0, control_only=0, neither_complete=0,
                     unknown=0, different_spans_all=0, different_spans_known=0)
    for identifier, row in report["rows"].items():
        row["arms"] = {name: row["arms"][earlier] for name, earlier in D31_NAMES.items()}
        trace = original["traces"][identifier]
        different = trace["issue_conditioned"]["spans"] != trace["lexical_diversity"]["spans"]
        counts["different_spans_all"] += different
        if row["adjudication"] == "unknown":
            counts["unknown"] += 1
            continue
        counts["different_spans_known"] += different
        candidate = row["arms"]["issue_conditioned"]["complete"]
        control = row["arms"]["lexical_diversity"]["complete"]
        cell = "both_complete" if candidate and control else "candidate_only" if candidate else (
            "control_only" if control else "neither_complete")
        counts[cell] += 1

    report["totals"] = totals
    report["paired"] = dict(counts)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exact_freeze_sha256")
    parser.add_argument("original_sha256")
    args = parser.parse_args()
    start, cpu = perf_counter(), process_time()
    lock = json.loads(verified(LOCK, args.exact_freeze_sha256))
    for name, sha in lock["implementation"].items():
        verified(ROOT / name, sha)

    source = Path(lock["original"])
    original = json.loads(verified(source, args.original_sha256))
    seal = Path(lock["seal"]).read_text(encoding="ascii").split()
    if seal != [args.original_sha256, source.name] or original["lock_sha256"] != args.exact_freeze_sha256:
        raise ValueError("original seal differs from release or snapshot")
    canonical = json.loads(verified(Path(lock["source_directory"]) / "canonical-pages.json", lock["canonical_sha256"]))
    pages = {name: canonical[name] for name in lock["source_ids"]}
    key = json.loads(verified(Path(lock["key"]["path"]), lock["key"]["sha256"]))
    report = evaluate(original, key, pages)
    report["scoring_wall_seconds"] = perf_counter() - start
    report["scoring_cpu_seconds"] = process_time() - cpu
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
