"""Compare hash-pinned dev/main ranking bundles, without reading relevance labels."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.mtm_ranking_parity import compare_rankings, load_rankings  # noqa: E402
from patent_to_pilot.research.mtm_queries import load_dev_queries  # noqa: E402
from patent_to_pilot.research.mtm_runtime import InputBoundaryError, load_dev_metadata  # noqa: E402
from patent_to_pilot.research.vector_identity import sha256  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("metadata-root", "query-root", "reference-root", "candidate-root", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("metadata-manifest-sha256", "query-manifest-sha256", "reference-manifest-sha256", "candidate-manifest-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--lane", choices=("U", "X"), required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise InputBoundaryError("parity output already exists")
    if sha256(args.metadata_root / "manifest.json") != args.metadata_manifest_sha256:
        raise InputBoundaryError("metadata manifest differs from trusted digest")
    metadata = load_dev_metadata(args.metadata_root)
    queries = load_dev_queries(args.query_root, args.query_manifest_sha256, set(metadata))
    available = {row["id"] for row in queries["rows"]}
    reference = load_rankings(args.reference_root, manifest_sha256=args.reference_manifest_sha256,
                              query_ids=available, view=queries["view"], lane=args.lane)
    candidate = load_rankings(args.candidate_root, manifest_sha256=args.candidate_manifest_sha256,
                              query_ids=available, view=queries["view"], lane=args.lane)
    report = compare_rankings(reference, candidate, cohort_ids=set(metadata), missing_ids=set(queries["missing_ids"]))
    report.update(view=queries["view"], lane=args.lane, corpus_view="main", inputs_sha256={
        "metadata_manifest": args.metadata_manifest_sha256, "query_manifest": args.query_manifest_sha256,
        "reference_manifest": args.reference_manifest_sha256, "candidate_manifest": args.candidate_manifest_sha256})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps(report))
    return 0 if report["status"] == "EXACT_RANKING_PARITY_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
