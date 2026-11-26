"""Read-only D31 evaluator. It opens the independent key after verifying the seal."""
import argparse
import json
import re
from collections import Counter
from pathlib import Path
from time import perf_counter, process_time

from ocs_correspondence import ARMS, LOCK, PAGE_CAP, ROOT, SPAN_CAP, WIDTH, digest, normal, verified


def opinion_id(text):
    match = re.fullmatch(r"0*(\d{1,4})[/\-](25\d{2})", normal(text))
    if not match:
        raise ValueError("unrecognized opinion key")
    return f"{int(match[1])}/{match[2]}"


def keyed_occurrences(row, pages):
    doc = pages[row["source_case"]]
    results = []
    for item in row["requirements"]:
        page = item["page"]
        phrase = normal(item["quote"])
        if not 1 <= page <= len(doc) or not 14 <= len(phrase) <= 85:
            raise ValueError("invalid reference page or distinctive quote size")
        matches = [m.start() for m in re.finditer(f"(?={re.escape(phrase)})", doc[page - 1])]
        if "start" in item:
            matches = [offset for offset in matches if offset == item["start"]]
        if len(matches) != 1:
            raise ValueError("reference quote missing or ambiguous on its keyed page")
        results.append((page, matches[0], matches[0] + len(phrase)))
    if not results:
        raise ValueError("adjudicated issue needs at least one reference fragment")

    def fits(window):
        return window[0][0] == window[-1][0] and max(r[2] for r in window) - window[0][1] <= WIDTH

    packed = sorted(results)
    if not fits(packed) and not any(
        fits(packed[:i]) and fits(packed[i:]) and
        (packed[i-1][0] != packed[i][0] or max(r[2] for r in packed[:i]) <= packed[i][1])
        for i in range(1, len(packed))
    ):
        raise ValueError("reference fragments cannot fit two legal windows")
    return results


def validate_spans(trace, pages):
    visits = {(a["source"], a["page"]) for a in trace["actions"]}
    if (len(visits) != len(trace["actions"]) or len(visits) > PAGE_CAP or any(
        source not in pages or not 1 <= page <= len(pages[source]) for source, page in visits
    )):
        raise ValueError("invalid page view ledger")
    spans = trace["spans"]
    if len(spans) > SPAN_CAP or bool(spans) != (trace["status"] == "issued"):
        raise ValueError("invalid answer/abstention envelope")
    if spans:
        if len(spans) == 2 and spans[0]["page"] == spans[1]["page"] and (
            min(p["end"] for p in spans) > max(p["start"] for p in spans)
        ):
            raise ValueError("overlapping answer spans")
        source = trace["identity"]["source"]
        for span in spans:
            page, start, end = span["page"], span["start"], span["end"]
            if ((source, page) not in visits or not 0 <= start < end <= len(pages[source][page-1])
                    or end - start > WIDTH or pages[source][page-1][start:end] != span["quote"]):
                raise ValueError("unbound or excessive answer span")


def evaluate(original, key, canonical):
    pages = {k: [normal(p) for p in v] for k, v in canonical.items()}
    rows = {r["id"]: r for r in key}
    traces = original["traces"]
    if len(rows) != len(key) or rows.keys() != traces.keys():
        raise ValueError("query and key need identical unique IDs")
    reports = {}
    totals = {arm: Counter() for arm in ARMS}
    for qid, arms in traces.items():
        row = rows[qid]
        if set(arms) != set(ARMS) or row["adjudication"] not in {"adjudicated", "unknown"}:
            raise ValueError("unknown arm inventory or adjudication value")
        known = row["adjudication"] == "adjudicated"
        occurrences = keyed_occurrences(row, pages) if known else []
        report = {"adjudication": row["adjudication"], "provenance": row["request_provenance"], "arms": {}}
        for arm, trace in arms.items():
            validate_spans(trace, pages)
            issued = trace["status"] == "issued"
            identity = trace.get("identity", {})
            same_link = bool(known and identity and
                identity["source"] == row["source_case"] and
                identity["opinion"] == opinion_id(row["opinion"]) and
                normal(identity["agency"]) == normal(row["agency"]) and
                normal(identity["reference"]) == normal(row["reference"]))
            spans = trace["spans"]
            matches = [[same_link and span["page"] == p and span["start"] <= start and span["end"] >= end
                        for p, start, end in occurrences] for span in spans]
            every = bool(same_link and issued and all(
                any(found[i] for found in matches) for i in range(len(occurrences))
            ))
            metrics = {"complete": every, "linked": same_link, "issued": issued, "known": known,
                       "unsupported_issued": known and issued and not every,
                       "nonmatching_spans": sum(not any(m) for m in matches) if known else 0,
                       "unresolved": not issued, "page_opens": len(trace["actions"]),
                       "windows_ranked": trace["windows_ranked"]}
            report["arms"][arm] = metrics
            totals[arm].update({k: int(v) for k, v in metrics.items()})
        reports[qid] = report
    return {"rows": reports, "totals": totals, "known": sum(r["adjudication"] == "adjudicated" for r in key),
            "total_issues": len(key),
            "primary_delta_complete": totals["adaptive_page"]["complete"] - totals["exact_conflict"]["complete"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exact_freeze_sha256")
    parser.add_argument("original_sha256")
    args = parser.parse_args()
    start, cpu = perf_counter(), process_time()
    lock = json.loads(verified(LOCK, args.exact_freeze_sha256))
    for name, sha in lock["implementation"].items():
        verified(ROOT / name, sha)
    original = json.loads(verified(Path(lock["original"]), args.original_sha256))
    if original["lock_sha256"] != args.exact_freeze_sha256:
        raise ValueError("original not bound to this lock")
    canonical = json.loads(verified(Path(lock["source_directory"]) / "canonical-pages.json", lock["canonical_sha256"]))
    key = json.loads(verified(Path(lock["key"]["path"]), lock["key"]["sha256"]))
    report = evaluate(original, key, canonical)
    report["scoring_wall_seconds"] = perf_counter() - start
    report["scoring_cpu_seconds"] = process_time() - cpu
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
