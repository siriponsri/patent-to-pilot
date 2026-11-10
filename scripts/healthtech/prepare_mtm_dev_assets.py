"""Curator-only preparation of immutable dev assets; no model loading or scoring.

Run after isolated metadata staging, outside the development agent environment.
This command does not configure isolation or authorize access to protected data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.mtm_corpus_projection import project_corpus  # noqa: E402
from patent_to_pilot.research.mtm_queries import load_dev_queries  # noqa: E402
from patent_to_pilot.research.mtm_runtime import (  # noqa: E402
    InputBoundaryError, decode_json, exact_fields, identifier, load_dev_metadata,
)
from patent_to_pilot.research.vector_identity import sha256  # noqa: E402


def prepare(args) -> dict:
    if args.output_root.exists() or args.expected_missing_count < 0 or args.view not in ("P", "T", "A"):
        raise InputBoundaryError("invalid output or preparation settings")
    if sha256(args.identity_report) != args.identity_report_sha256:
        raise InputBoundaryError("identity report differs from reviewed digest")
    trusted = decode_json(args.identity_report.read_bytes())["identity"]
    metadata = load_dev_metadata(args.metadata_root)
    raw = args.dev_queries.read_bytes()
    ids = set()
    for line in raw.splitlines():
        row = decode_json(line)
        exact_fields(row, {"id", "text"})
        identifier(row["id"])
        if (row["id"] in ids or row["id"] not in metadata or
                type(row["text"]) is not str or not row["text"].strip()):
            raise InputBoundaryError("invalid, duplicate or out-of-cohort query")
        ids.add(row["id"])
    missing = sorted(set(metadata) - ids)
    if not ids or len(missing) != args.expected_missing_count:
        raise InputBoundaryError("missing-query count differs from curator expectation")
    args.output_root.mkdir(parents=True, exist_ok=False)
    def write(path, value):
        with path.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2)
            handle.write("\n")
    identity_path = args.output_root / "original-identity.json"
    write(identity_path, trusted)
    query_root = args.output_root / "queries"
    query_root.mkdir()
    with (query_root / "queries.jsonl").open("xb") as handle:
        handle.write(raw)  # Preserve original bytes, ordering and prefixes.
    write(query_root / "manifest.json", {"format": "ptp-mtm-query-text-v1", "split": "dev",
                                          "view": args.view, "queries": len(ids), "missing_ids": missing,
                                          "sha256": sha256(query_root / "queries.jsonl")})
    query_digest = sha256(query_root / "manifest.json")
    load_dev_queries(query_root, query_digest, set(metadata))
    project_corpus(args.source_corpus, args.output_root / "corpus", trusted["corpus"])
    receipt = {"status": "PREPARED_NOT_ISOLATION_ATTESTED", "split": "dev", "view": args.view,
               "metadata_manifest_sha256": sha256(args.metadata_root / "manifest.json"),
               "query_manifest_sha256": query_digest, "original_identity_sha256": sha256(identity_path),
               "source_identity_report_sha256": args.identity_report_sha256,
               "projection_receipt_sha256": sha256(args.output_root / "corpus/projection.json"),
               "cohort_queries": len(metadata), "available_queries": len(ids), "missing_queries": len(missing),
               "physical_isolation": "CURATOR_ATTESTATION_REQUIRED"}
    write(args.output_root / "asset-receipt.json", receipt)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-corpus", "dev-queries", "metadata-root", "identity-report", "output-root"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--identity-report-sha256", required=True)
    parser.add_argument("--view", choices=("P", "T", "A"), required=True)
    parser.add_argument("--expected-missing-count", type=int, default=0)
    parser.add_argument("--trusted-curator", action="store_true", required=True)
    args = parser.parse_args()
    try:
        receipt = prepare(args)
    except (InputBoundaryError, OSError, KeyError, TypeError):
        print("Preparation failed; preserve the attempt and inspect only in the curator environment.", file=sys.stderr)
        return 1
    print(json.dumps(receipt))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
