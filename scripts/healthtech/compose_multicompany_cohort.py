"""Compose a typed-policy multi-company cohort from existing local snapshots."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "src"))

from patent_to_pilot.healthtech.contracts import content_hash


def _read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_parent(alias: str, root: Path) -> dict:
    manifest = _read_json(root / "manifest.json")
    runtime = _read_json(root / str(manifest.get("runtime_path", "runtime.json")))
    references = _read_json(root / str(manifest.get("evaluator_path", "evaluator/references.json")))
    groups = _read_json(root / str(manifest.get("groups_path", "groups.json")))
    registry = _read_json(root / str(manifest.get("source_registry", "source_registry.json")))
    split = _read_json(root / str(manifest.get("split_path", "split_manifest.json")))
    sources = registry.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError(f"{alias} source registry has no sources")
    for source in sources:
        if not isinstance(source, dict) or not source.get("source_id"):
            raise ValueError(f"{alias} source registry has an invalid row")
        if not isinstance(source.get("rights_policy_id"), str) or not source["rights_policy_id"].strip():
            raise ValueError(f"{alias} source {source.get('source_id')} lacks a typed rights_policy_id")
    devices = runtime.get("devices")
    patents = runtime.get("patents")
    refs = references.get("references")
    evidence = references.get("disclosure_evidence")
    if not isinstance(devices, list) or not devices:
        raise ValueError(f"{alias} runtime.devices must be nonempty")
    if not isinstance(patents, list) or not patents:
        raise ValueError(f"{alias} runtime.patents must be nonempty")
    if not isinstance(refs, dict) or not refs:
        raise ValueError(f"{alias} references must be nonempty")
    if not isinstance(evidence, list) or not evidence:
        raise ValueError(f"{alias} disclosure_evidence must be nonempty")
    return {
        "alias": alias,
        "root": root,
        "manifest": manifest,
        "runtime": runtime,
        "references": references,
        "groups": groups,
        "registry": registry,
        "split": split,
    }


def _company_groups(groups: dict) -> list[dict]:
    value = groups.get("company_groups", [])
    if isinstance(value, dict):
        return [
            {"company": company, "query_ids": sorted(query_ids), "basis": "parent cohort company group"}
            for company, query_ids in value.items()
        ]
    if not isinstance(value, list):
        return []
    return [deepcopy(row) for row in value if isinstance(row, dict)]


def _query_group_ids(groups: dict, alias: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    rows = groups.get("group_evidence", [])
    if not isinstance(rows, list):
        return mapping
    for row in rows:
        if not isinstance(row, dict):
            continue
        group_id = str(row.get("group_id") or "")
        query_ids = row.get("device_query_ids", [])
        if not group_id or not isinstance(query_ids, list):
            continue
        composite_id = f"{alias}::{group_id}"
        for query_id in query_ids:
            query_id = str(query_id)
            if query_id in mapping:
                raise ValueError(f"query belongs to multiple {alias} groups: {query_id}")
            mapping[query_id] = composite_id
    return mapping


def _subset_groups(groups: dict, query_ids: set[str]) -> dict:
    result = deepcopy(groups)
    result["group_evidence"] = [
        row for row in result.get("group_evidence", [])
        if set(row.get("device_query_ids", [])) <= query_ids
    ]
    result["shared_exact_patent_groups"] = [
        sorted(row.get("device_query_ids", []))
        for row in result["group_evidence"]
    ]
    result["company_groups"] = [
        {
            **row,
            "query_ids": sorted(set(row.get("query_ids", [])) & query_ids),
        }
        for row in result.get("company_groups", [])
        if set(row.get("query_ids", [])) & query_ids
    ]
    return result


def _write_view(output: Path, name: str, query_ids: list[str], runtime: dict, references: dict, groups: dict) -> dict:
    view = output / "views" / name
    view.mkdir(parents=True, exist_ok=True)
    query_set = set(query_ids)
    view_runtime = deepcopy(runtime)
    view_runtime["devices"] = [device for device in runtime["devices"] if device.get("query_id") in query_set]
    view_runtime["status"] = "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS"
    view_references = deepcopy(references)
    view_references["references"] = {
        query_id: values for query_id, values in references["references"].items() if query_id in query_set
    }
    view_references["disclosure_evidence"] = [
        row for row in references["disclosure_evidence"] if row.get("query_id") in query_set
    ]
    view_groups = _subset_groups(groups, query_set)
    _write_json(view / "runtime.json", view_runtime)
    _write_json(view / "references.json", view_references)
    _write_json(view / "groups.json", view_groups)
    manifest = {
        "format": "ht-multi-company-view-v1",
        "name": name,
        "query_ids": query_ids,
        "runtime_path": f"views/{name}/runtime.json",
        "references_path": f"views/{name}/references.json",
        "groups_path": f"views/{name}/groups.json",
        "runtime_sha256": _file_sha256(view / "runtime.json"),
        "references_sha256": _file_sha256(view / "references.json"),
        "groups_sha256": _file_sha256(view / "groups.json"),
    }
    _write_json(view / "manifest.json", manifest)
    return manifest


def compose_cohort(
    *,
    boston_cohort: Path,
    stryker_cohort: Path,
    output: Path,
    holdout_company: str = "Stryker Neurovascular",
) -> dict:
    if output.exists():
        raise ValueError(f"output already exists; choose a fresh directory: {output}")
    parents = [
        _load_parent("boston", boston_cohort.resolve()),
        _load_parent("stryker", stryker_cohort.resolve()),
    ]
    freeze_timestamp = max(
        str(parent["manifest"].get("retrieved_at_utc") or "")
        for parent in parents
    )
    output.mkdir(parents=True)

    devices: list[dict] = []
    patents_by_id: dict[str, dict] = {}
    references: dict[str, list[str]] = {}
    evidence: list[dict] = []
    sources_by_id: dict[str, dict] = {}
    group_evidence: list[dict] = []
    company_groups: list[dict] = []
    query_group_ids: dict[str, str] = {}
    raw_files: list[dict] = []
    policy_ids: set[str] = set()
    parent_summaries: list[dict] = []

    for parent in parents:
        alias = parent["alias"]
        runtime = parent["runtime"]
        parent_devices = runtime["devices"]
        for device in parent_devices:
            query_id = str(device.get("query_id") or "")
            if not query_id or query_id in {row.get("query_id") for row in devices}:
                raise ValueError(f"duplicate or missing query_id: {query_id}")
            devices.append(deepcopy(device))
        for patent in runtime["patents"]:
            patent_id = str(patent.get("patent_id_canonical") or "")
            if not patent_id:
                raise ValueError(f"{alias} patent missing patent_id_canonical")
            prior = patents_by_id.get(patent_id)
            if prior is not None and prior != patent:
                raise ValueError(f"conflicting duplicate patent payload: {patent_id}")
            patents_by_id[patent_id] = deepcopy(patent)
        parent_refs = parent["references"].get("references", {})
        for query_id, values in parent_refs.items():
            if query_id in references:
                raise ValueError(f"duplicate reference query_id: {query_id}")
            references[query_id] = list(values)
        evidence.extend(deepcopy(parent["references"]["disclosure_evidence"]))
        for source in parent["registry"]["sources"]:
            source_id = str(source["source_id"])
            if source_id in sources_by_id and sources_by_id[source_id] != source:
                raise ValueError(f"conflicting source registry row: {source_id}")
            sources_by_id[source_id] = deepcopy(source)
            policy_ids.add(str(source["rights_policy_id"]))
        group_rows = parent["groups"].get("group_evidence", [])
        for row in group_rows:
            if not isinstance(row, dict):
                continue
            group = deepcopy(row)
            original_id = str(group.get("group_id") or "")
            group["group_id"] = f"{alias}::{original_id}"
            group_evidence.append(group)
        query_group_ids.update(_query_group_ids(parent["groups"], alias))
        company_groups.extend(_company_groups(parent["groups"]))
        for raw_file in parent["manifest"].get("raw_files", []):
            if isinstance(raw_file, dict):
                raw_files.append({"source_cohort": alias, **deepcopy(raw_file)})
        parent_summaries.append({
            "alias": alias,
            "path": str(parent["root"]),
            "manifest_sha256": _file_sha256(parent["root"] / "manifest.json"),
            "cohort_sha256": parent["manifest"].get("cohort_sha256"),
            "devices": parent["manifest"].get("devices"),
            "patents": parent["manifest"].get("patents"),
            "reference_pairs": parent["manifest"].get("reference_pairs"),
        })

    all_query_ids = {device["query_id"] for device in devices}
    if set(references) != all_query_ids:
        raise ValueError("combined references do not cover exactly the combined devices")
    if set(query_group_ids) != all_query_ids:
        missing = sorted(all_query_ids - set(query_group_ids))
        raise ValueError(f"combined groups do not cover all devices: {missing}")
    if not evidence:
        raise ValueError("combined disclosure evidence is empty")

    normalized_holdout = holdout_company.strip().casefold()
    holdout_query_ids = sorted(
        device["query_id"] for device in devices
        if str(device.get("company") or "").strip().casefold() == normalized_holdout
    )
    if not holdout_query_ids or len(holdout_query_ids) == len(devices):
        raise ValueError("holdout company must match a non-exhaustive device subset")
    development_query_ids = sorted(all_query_ids - set(holdout_query_ids))

    runtime = {
        "format": "ht-runtime-input-v1",
        "status": "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS",
        "retrieved_at_utc": freeze_timestamp,
        "devices": sorted(devices, key=lambda item: item["query_id"]),
        "patents": [patents_by_id[key] for key in sorted(patents_by_id)],
        "permitted_metadata": sorted({
            value for parent in parents for value in parent["runtime"].get("permitted_metadata", [])
        }),
        "runtime_exclusions": [
            "product disclosure relations",
            "evaluator references",
            "family labels",
            "split answers",
            "final holdout labels",
        ],
    }
    registry = {
        "format": "ht-source-registry-v1",
        "separation": "Runtime rows exclude independent disclosure and evaluator-only fields.",
        "sources": [sources_by_id[key] for key in sorted(sources_by_id)],
    }
    evaluator = {
        "format": "ht-evaluator-disclosures-v1",
        "status": "EVALUATOR_ONLY_REFERENCE_RELATIONS",
        "retrieved_at_utc": freeze_timestamp,
        "references": {query_id: references[query_id] for query_id in sorted(references)},
        "disclosure_evidence": sorted(evidence, key=lambda row: str(row.get("evidence_id"))),
        "limitations": [
            "Product-level marking relationships are not independent expert relevance judgments.",
            "Unlisted device-patent pairs remain unjudged and are not recoded as negatives.",
            "The final holdout is not used by the development view or tuning workflow.",
        ],
    }
    groups = {
        "format": "ht-group-evidence-v1",
        "status": "PREDECLARED_FINAL_HOLDOUT_NO_TUNING",
        "group_evidence": sorted(group_evidence, key=lambda row: row["group_id"]),
        "shared_exact_patent_groups": [
            sorted(row.get("device_query_ids", []))
            for row in sorted(group_evidence, key=lambda row: row["group_id"])
        ],
        "company_groups": sorted(company_groups, key=lambda row: str(row.get("company"))),
        "family_mapping": {
            "status": "UNKNOWN_NOT_ASSUMED",
            "mappings": [],
            "basis": "Parent cohorts did not provide a sourced family mapping; no family merge is inferred.",
        },
        "overlap_notes": [
            "Boston Scientific and Stryker Neurovascular are independent company groups in the composite.",
            "Exact-patent groups are carried forward from product-marking rows; family identity remains unknown.",
            "The Stryker company group is predeclared as the untouched final holdout.",
        ],
    }
    split = {
        "format": "ht-development-final-holdout-split-v1",
        "status": "PREDECLARED_FINAL_HOLDOUT_NO_TUNING",
        "assignment_rule": "Hold out the full Stryker Neurovascular company group; no query or group reassignment is permitted after freeze.",
        "seed": 0,
        "final_holdout_company_groups": [holdout_company],
        "final_holdout_group_ids": sorted({query_group_ids[query_id] for query_id in holdout_query_ids}),
        "rows": [
            {
                "query_id": query_id,
                "split": "final_holdout" if query_id in holdout_query_ids else "development",
                "group_id": query_group_ids[query_id],
            }
            for query_id in sorted(all_query_ids)
        ],
        "final_holdout": holdout_query_ids,
    }
    distractors = {
        "format": "ht-unjudged-distractors-v1",
        "by_query": {
            query_id: sorted(set(patents_by_id) - set(references[query_id]))
            for query_id in sorted(references)
        },
    }

    _write_json(output / "runtime.json", runtime)
    _write_json(output / "source_registry.json", registry)
    _write_json(output / "evaluator" / "references.json", evaluator)
    _write_json(output / "groups.json", groups)
    _write_json(output / "split_manifest.json", split)
    _write_json(output / "distractors.json", distractors)

    development_groups = _subset_groups(groups, set(development_query_ids))
    holdout_groups = _subset_groups(groups, set(holdout_query_ids))
    development_view = _write_view(output, "development", development_query_ids, runtime, evaluator, development_groups)
    holdout_view = _write_view(output, "final_holdout", holdout_query_ids, runtime, evaluator, holdout_groups)

    manifest_payload = {
        "format": "ht-multi-company-cohort-v1",
        "status": "PUBLIC_MULTI_COMPANY_COHORT_FROZEN",
        "retrieved_at_utc": freeze_timestamp,
        "parent_cohorts": parent_summaries,
        "devices": len(devices),
        "patents": len(patents_by_id),
        "reference_pairs": sum(len(values) for values in references.values()),
        "unjudged_distractor_pairs": sum(len(values) for values in distractors["by_query"].values()),
        "rights_policy_ids": sorted(policy_ids),
        "raw_files": raw_files,
        "runtime_path": "runtime.json",
        "runtime_sha256": _file_sha256(output / "runtime.json"),
        "source_registry": "source_registry.json",
        "source_registry_sha256": _file_sha256(output / "source_registry.json"),
        "evaluator_path": "evaluator/references.json",
        "references_sha256": _file_sha256(output / "evaluator" / "references.json"),
        "groups_path": "groups.json",
        "groups_sha256": _file_sha256(output / "groups.json"),
        "split_path": "split_manifest.json",
        "split_sha256": _file_sha256(output / "split_manifest.json"),
        "distractors_path": "distractors.json",
        "universe_sha256": content_hash(sorted(patents_by_id)),
        "cohort_sha256": content_hash({
            "runtime": runtime,
            "references": evaluator["references"],
            "groups": groups,
            "split": split,
        }),
        "final_holdout_query_ids": holdout_query_ids,
        "development_query_ids": development_query_ids,
        "views": {
            "development": development_view,
            "final_holdout": holdout_view,
        },
        "accounting": {
            "mode": "DERIVED_FROM_EXISTING_LOCAL_SNAPSHOTS",
            "actual_transferred_bytes": 0,
            "new_raw_acquisition": False,
        },
        "limitations": [
            "This is a derived local composite of two previously acquired typed-policy cohorts.",
            "Family mapping is unknown and not inferred.",
            "Product-level disclosure is not independent semantic relevance gold.",
            "Google-derived patent text and marking-page evidence remain local-only.",
            "One company is held out; this is a single-company transfer check, not a stable generalization estimate.",
        ],
    }
    _write_json(output / "manifest.json", manifest_payload)
    return manifest_payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boston-cohort", type=Path, required=True)
    parser.add_argument("--stryker-cohort", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--holdout-company", default="Stryker Neurovascular")
    args = parser.parse_args()
    manifest = compose_cohort(
        boston_cohort=args.boston_cohort,
        stryker_cohort=args.stryker_cohort,
        output=args.output,
        holdout_company=args.holdout_company,
    )
    print(json.dumps({
        "status": manifest["status"],
        "output": str(args.output.resolve()),
        "devices": manifest["devices"],
        "patents": manifest["patents"],
        "reference_pairs": manifest["reference_pairs"],
        "final_holdout_query_ids": manifest["final_holdout_query_ids"],
        "cohort_sha256": manifest["cohort_sha256"],
    }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
