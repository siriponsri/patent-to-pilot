"""Freeze the bounded Abbott development universe and unjudged distractors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "src"))

from patent_to_pilot.healthtech.abbott import build_abbott_development_protocol
from patent_to_pilot.healthtech.contracts import content_hash


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh directory")
    args.output.mkdir(parents=True)
    protocol = build_abbott_development_protocol(args.cohort)
    protocol["protocol_sha256"] = content_hash(protocol)
    (args.output / "protocol.json").write_text(json.dumps(protocol, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "distractors.json").write_text(json.dumps({
        "format": protocol["format"],
        "status": protocol["status"],
        "selection_rule": protocol["distractor_rule"],
        "universe": protocol["universe"],
        "distractors_by_query": protocol["distractors_by_query"],
        "counts": protocol["counts"],
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "group_evidence.json").write_text(json.dumps({
        "format": "ht-group-evidence-v1",
        "status": protocol["status"],
        "groups": protocol["groups"],
        "source_refs": protocol["source_refs"],
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "split_manifest.json").write_text(json.dumps({
        "format": "ht-development-split-v1",
        "status": protocol["status"],
        "split": protocol["split"],
        "eligible_query_ids": protocol["eligible_query_ids"],
        "evidence_cutoffs": protocol["evidence_cutoffs"],
    }, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output / "README.md").write_text(
        "# Abbott development freeze\n\n"
        "This is a bounded development-only universe derived from the local public cohort.\n\n"
        "- Unlisted device-patent pairs are unjudged distractors, never negatives.\n"
        "- Family identity remains unknown unless separately sourced.\n"
        "- All three devices remain in development; no final holdout or generalization claim is made.\n"
        "- Raw third-party pages remain in the permitted local cohort storage and are not copied here.\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": protocol["status"],
        "eligible_devices": protocol["counts"]["eligible_devices"],
        "universe_patents": protocol["counts"]["universe_patents"],
        "disclosed_pairs": protocol["counts"]["disclosed_pairs"],
        "unjudged_distractor_pairs": protocol["counts"]["unjudged_distractor_pairs"],
        "protocol_sha256": protocol["protocol_sha256"],
        "output": str(args.output),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
