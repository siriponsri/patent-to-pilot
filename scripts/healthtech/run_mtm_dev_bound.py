"""Prospective dev/main baseline parity entry point. No test or re-encode option.

Requires independently pinned curator manifests and immutable isolated inputs.
Delegates unchanged historical numerical behavior after all CPU input checks.
This preserves the historical torch.topk cutoff-tie limitation for parity.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.research.mtm_preflight import preflight_dev  # noqa: E402
from patent_to_pilot.research.mtm_queries import load_dev_queries  # noqa: E402
from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json, load_dev_metadata  # noqa: E402
from patent_to_pilot.research.vector_identity import sha256  # noqa: E402


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    for name in ("metadata-root", "query-root", "corpus", "vectors", "model-root", "projection-receipt",
                 "original-identity", "output-dir"):
        result.add_argument("--" + name, type=Path, required=True)
    for name in ("metadata-manifest-sha256", "query-manifest-sha256", "projection-receipt-sha256",
                 "original-identity-sha256", "runner-source-sha256"):
        result.add_argument("--" + name, required=True)
    result.add_argument("--batch-size", type=int, default=64)
    return result


def run(args) -> int:
    # No output allocation, dynamic runner import, model or GPU before validation.
    if args.output_dir.exists() or args.batch_size <= 0:
        raise InputBoundaryError("output exists or invalid batch size")
    encoder_source = Path(__file__).with_name("run_dapfam_dense_pool.py")
    runner_source = Path(__file__).with_name("run_mtm_dense_pool.py")
    for path, digest in ((args.metadata_root / "manifest.json", args.metadata_manifest_sha256),
                         (args.original_identity, args.original_identity_sha256),
                         (runner_source, args.runner_source_sha256)):
        if sha256(path) != digest:
            raise InputBoundaryError("trusted input or runner hash mismatch")
    metadata = load_dev_metadata(args.metadata_root)
    queries = load_dev_queries(args.query_root, args.query_manifest_sha256, set(metadata))
    trusted = decode_json(args.original_identity.read_bytes())
    gate = preflight_dev(metadata_root=args.metadata_root, corpus=args.corpus, vectors=args.vectors,
                         model_root=args.model_root, encoder_source=encoder_source,
                         projection_receipt=args.projection_receipt,
                         trusted_receipt_sha256=args.projection_receipt_sha256, trusted_original=trusted)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    receipt = {"status": "PREFLIGHT_PASS_RUN_PENDING", "preflight": gate,
               "cohort_queries": len(metadata), "available_queries": len(queries["rows"]),
               "missing_queries": len(queries["missing_ids"]), "query_view": queries["view"],
               "query_manifest_sha256": args.query_manifest_sha256,
               "original_identity_sha256": args.original_identity_sha256,
               "runner_source_sha256": args.runner_source_sha256,
               "ranking_parity": "NOT_ASSESSED", "numerical_behavior": "UNCHANGED_HISTORICAL_MAIN_U_X"}
    def write_receipt(name):
        with (args.output_dir / name).open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2)
            handle.write("\n")
    write_receipt("bound-preflight.json")
    previous = sys.argv
    try:
        spec = importlib.util.spec_from_file_location("mtm_bound_historical", runner_source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        sys.argv = [str(runner_source), "--corpus", str(args.corpus), "--queries", str(args.query_root / "queries.jsonl"),
                    "--queries-meta", str(args.metadata_root / "metadata.jsonl"), "--model-dir", str(args.model_root),
                    "--output-dir", str(args.output_dir), "--name", queries["view"] + "-dev",
                    "--views", "main", "--reuse-vectors", str(args.vectors), "--batch-size", str(args.batch_size)]
        code = module.main()
        receipt["status"] = "RUN_COMPLETED_PARITY_PENDING" if code == 0 else "RUN_FAILED"
        receipt["exit_code"] = code
        write_receipt("bound-outcome.json")
        return code
    except BaseException:
        # Preserve partial output and original exception; do not write its contents.
        receipt["status"] = "RUN_FAILED_OR_INTERRUPTED"
        write_receipt("bound-failure.json")
        raise
    finally:
        sys.argv = previous


if __name__ == "__main__":
    raise SystemExit(run(parser().parse_args()))
