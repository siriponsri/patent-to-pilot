"""Analyze family-aware evaluator groups without changing runtime inputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from patent_to_pilot.evaluation.healthtech.retrieval import shared_reference_groups


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def analyze(references_path: str | Path, groups_path: str | Path, mapping_path: str | Path) -> dict[str, Any]:
    references_payload = _read_json(Path(references_path))
    groups_payload = _read_json(Path(groups_path))
    mapping_payload = _read_json(Path(mapping_path))
    references = references_payload.get("references")
    exact_groups = groups_payload.get("shared_exact_patent_groups")
    mapping_rows = mapping_payload.get("mappings")
    if not isinstance(references, dict) or not isinstance(exact_groups, list) or not isinstance(mapping_rows, list):
        raise ValueError("references, groups, or mapping payload has the wrong shape")
    family_map = {}
    for row in mapping_rows:
        if not isinstance(row, dict) or not isinstance(row.get("patent_id_canonical"), str) or not isinstance(row.get("family_id"), str):
            raise ValueError("family mapping contains an invalid row")
        if row["patent_id_canonical"] in family_map and family_map[row["patent_id_canonical"]] != row["family_id"]:
            raise ValueError(f"family mapping conflicts for {row['patent_id_canonical']}")
        family_map[row["patent_id_canonical"]] = row["family_id"]
    family_groups = shared_reference_groups(references, families=family_map)
    exact_sets = {frozenset(group) for group in exact_groups}
    family_sets = {frozenset(group) for group in family_groups}
    merged_family_groups = [
        sorted(group)
        for group in family_sets
        if sum(bool(group & exact_group) for exact_group in exact_sets) > 1
    ]
    return {
        "format": "ht-family-aware-group-analysis-v1",
        "status": "PASS_OFFLINE_FAMILY_SENSITIVITY",
        "family_mapping_status": mapping_payload.get("status"),
        "family_mapping_sha256": mapping_payload.get("mapping_sha256"),
        "counts": {
            "reference_queries": len(references),
            "exact_group_count": len(exact_groups),
            "family_aware_group_count": len(family_groups),
            "family_mapped_patents": len(family_map),
            "families_observed": len(set(family_map.values())),
            "family_merged_exact_group_count": len(merged_family_groups),
        },
        "exact_groups": sorted([sorted(group) for group in exact_groups]),
        "family_aware_groups": family_groups,
        "family_merged_exact_groups": sorted(merged_family_groups),
        "interpretation": [
            "Family-aware groups are evaluator-side uncertainty structure only; retrieval rankings and runtime inputs are unchanged.",
            "This analysis does not turn product-level disclosures into semantic relevance judgments.",
            "No unlisted pair is recoded as a negative and no final-holdout claim is created by this sensitivity pass.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--groups", type=Path, required=True)
    parser.add_argument("--family-mapping", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a fresh path")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = analyze(args.references, args.groups, args.family_mapping)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "counts": payload["counts"], "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
