"""One descriptive extract-selection replay on the closed D31 training cohort."""
import argparse
import json
from pathlib import Path
from time import perf_counter, process_time

from ocs_correspondence import LOCK as D31_LOCK, Document
from ocs_extract_pair import compare, read_queries, verified, write_json
from ocs_extract_pair_score import evaluate

D31_LOCK_SHA = "46cf4105be76671749530885fe6774044b6c9235affdd40f84211b4ae9b209f3"
D31_ORIGINAL_SHA = "af251a6d9862ae7c1e987fba6f9b40caf2539561738c8929afc3ef4ef27e2191"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("training_receipt", type=Path)
    args = parser.parse_args()
    if args.training_receipt.exists():
        raise ValueError("one training receipt already exists")

    start, cpu = perf_counter(), process_time()
    lock = json.loads(verified(D31_LOCK, D31_LOCK_SHA))
    original = json.loads(verified(Path(lock["original"]), D31_ORIGINAL_SHA))
    if original["lock_sha256"] != D31_LOCK_SHA:
        raise ValueError("closed D31 signature mismatch")
    pages = json.loads(verified(Path(lock["source_directory"]) / "canonical-pages.json", lock["canonical_sha256"]))
    queries = read_queries(verified(Path(lock["queries"]["path"]), lock["queries"]["sha256"]))
    docs = {name: Document.index(name, raw) for name, raw in sorted(pages.items())}
    indexing_wall = perf_counter() - start
    traces = {q["id"]: compare(q, docs, original["traces"][q["id"]]["exact_conflict"]) for q in queries}
    keys = json.loads(verified(Path(lock["key"]["path"]), lock["key"]["sha256"]))
    report = evaluate({"traces": traces}, keys, pages)
    report["training_original_sha256"] = D31_ORIGINAL_SHA
    report["indexing_wall_seconds"] = indexing_wall
    report["wall_seconds"] = perf_counter() - start
    report["cpu_seconds"] = process_time() - cpu
    report["selection_locators"] = {
        key: {name: [[s["page"], s["start"], s["end"]] for s in arm["spans"]] for name, arm in choices.items()}
        for key, choices in traces.items()
    }
    write_json(args.training_receipt, report)


if __name__ == "__main__":
    main()
