"""Verify two encoder vector bundles against one frozen runtime manifest.

The verifier reads owner-private artifacts in place and writes only a sanitized
integrity receipt. It never copies runtime text, vectors, labels, or model
weights into the repository.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from patent_to_pilot.evaluation.healthtech.vector_artifacts import (
    VectorArtifactError,
    load_vector_bundle,
    sha256_file,
)


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise VectorArtifactError(f"expected JSON object: {path.name}")
    return value


def _bundle_summary(root: Path, relative: str, expected_input: str) -> dict[str, Any]:
    bundle = load_vector_bundle(root / relative)
    manifest = dict(bundle.manifest)
    if manifest.get("input_sha256") != expected_input:
        raise VectorArtifactError(f"input binding mismatch: {relative}")
    return {
        "bundle": relative,
        "manifest_sha256": sha256_file(root / relative / "manifest.json"),
        "row_count": int(manifest["row_count"]),
        "dimension": int(manifest["dimension"]),
        "shard_count": len(manifest["shards"]),
        "model_id": manifest["model"]["model_id"],
        "revision": manifest["model"]["revision"],
        "model_sha256": manifest["model_sha256"],
        "config_sha256": manifest["config_sha256"],
        "input_sha256": manifest["input_sha256"],
        "item_order_sha256": manifest["item_order_sha256"],
        "document_order_sha256": manifest["document_order_sha256"],
    }


def verify(artifact_root: Path) -> dict[str, Any]:
    runtime_manifest_path = artifact_root / "inputs" / "device-runtime" / "manifest.json"
    runtime = _read_object(runtime_manifest_path)
    corpus_input = str(runtime["corpus_sha256"])
    query_input = str(runtime["queries_sha256"])
    bundles = [
        _bundle_summary(artifact_root, "outputs/device-patembed-corpus", corpus_input),
        _bundle_summary(artifact_root, "outputs/device-patembed-queries", query_input),
        _bundle_summary(artifact_root, "outputs/device-e5-corpus", corpus_input),
        _bundle_summary(artifact_root, "outputs/device-e5-queries", query_input),
    ]
    by_path = {row["bundle"]: row for row in bundles}
    for left, right, label in [
        ("outputs/device-patembed-corpus", "outputs/device-e5-corpus", "corpus"),
        ("outputs/device-patembed-queries", "outputs/device-e5-queries", "queries"),
    ]:
        for key in ("row_count", "dimension", "item_order_sha256", "document_order_sha256"):
            if by_path[left][key] != by_path[right][key]:
                raise VectorArtifactError(f"{label} cross-encoder binding mismatch: {key}")
    return {
        "format": "ptp-vector-bundle-pair-revalidation-v1",
        "status": "PASS_VECTOR_BUNDLE_INTEGRITY_PRIOR_ARTIFACT",
        "artifact_root_id": artifact_root.name,
        "runtime_manifest_sha256": sha256_file(runtime_manifest_path),
        "runtime": {
            "cases": runtime.get("cases", []),
            "corpus_rows": runtime.get("corpus", {}).get("row_count"),
            "query_rows": runtime.get("queries", {}).get("row_count"),
            "corpus_sha256": corpus_input,
            "queries_sha256": query_input,
        },
        "bundles": bundles,
        "checks": {
            "completed_bundle_loader": True,
            "shard_hashes_and_shapes": True,
            "finite_little_endian_float32": True,
            "unique_ids_and_order": True,
            "runtime_input_bindings": True,
            "cross_encoder_order_bindings": True,
        },
        "scope_limits": [
            "This verifies existing private vector artifacts; it is not a new encode or retrieval evaluation.",
            "Vector manifests carry model IDs, revisions, and model hashes; matching PatEmbed/e5 weight files were not reverified in this check.",
            "No evaluator labels, qrels, raw corpus text, vectors, or credentials are copied to the repository receipt.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    receipt = verify(args.artifact_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
