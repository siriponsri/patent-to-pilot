"""Prepare a local-only, unlabeled semantic-review packet."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from patent_to_pilot.evaluation.healthtech.local_retrieval import validate_runtime_payload
from patent_to_pilot.evaluation.healthtech.review_packet import build_relevance_review_packet


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--split-manifest", type=Path, required=True)
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--source-registry", type=Path, required=True)
    parser.add_argument("--family-mapping", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh path")

    runtime = _read_json(args.runtime)
    validate_runtime_payload(runtime)
    split_manifest = _read_json(args.split_manifest)
    groups = _read_json(args.groups)
    source_registry = _read_json(args.source_registry)
    family_mapping = _read_json(args.family_mapping) if args.family_mapping else None
    packet = build_relevance_review_packet(
        runtime,
        split_manifest,
        groups,
        source_registry,
        runtime_path=str(args.runtime),
        runtime_sha256=_sha256(args.runtime),
        split_manifest_path=str(args.split_manifest),
        split_manifest_sha256=_sha256(args.split_manifest),
        groups_path=str(args.groups),
        groups_sha256=_sha256(args.groups),
        source_registry_path=str(args.source_registry),
        source_registry_sha256=_sha256(args.source_registry),
        family_mapping=family_mapping,
        family_mapping_path=str(args.family_mapping) if args.family_mapping else None,
        family_mapping_sha256=_sha256(args.family_mapping) if args.family_mapping else None,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": "PASS",
        "output": str(args.output),
        "query_count": packet["counts"]["query_count"],
        "patent_count": packet["counts"]["patent_count"],
        "pair_denominator": packet["counts"]["pair_denominator"],
        "semantic_label_count": packet["counts"]["semantic_label_count"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
