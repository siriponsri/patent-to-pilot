"""Structural provenance checks for evaluator-only HealthTech cohorts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from patent_to_pilot.healthtech.contracts import SourceRights, canonical_patent_id, content_hash
from patent_to_pilot.healthtech.rights import load_rights_matrix


class CohortProvenanceError(ValueError):
    """Raised when a cohort cannot support auditable per-link provenance."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CohortProvenanceError(f"missing cohort artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CohortProvenanceError(f"invalid JSON artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise CohortProvenanceError(f"cohort artifact must be an object: {path}")
    return payload


def _canonical_ids(value: Any, *, field: str, allow_scalar: bool = False) -> list[str]:
    values = [value] if allow_scalar and isinstance(value, str) else value
    if not isinstance(values, list) or not values:
        raise CohortProvenanceError(f"{field} must be a nonempty list")
    result: list[str] = []
    for raw in values:
        if not isinstance(raw, str):
            raise CohortProvenanceError(f"{field} contains a non-string patent ID")
        try:
            result.append(canonical_patent_id(raw))
        except ValueError as exc:
            raise CohortProvenanceError(f"{field} contains invalid patent ID: {raw}") from exc
    if len(set(result)) != len(result):
        raise CohortProvenanceError(f"{field} contains duplicate canonical patent IDs")
    return result


def _reference_pairs(references: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for query_id, values in references.items():
        if not isinstance(query_id, str) or not query_id:
            raise CohortProvenanceError("references contains an invalid query ID")
        result[query_id] = _canonical_ids(values, field=f"references[{query_id!r}]")
    if not result:
        raise CohortProvenanceError("references must contain at least one eligible query")
    return result


def _rights_matrix_path(path: str | Path | None) -> Path:
    if path is not None:
        return Path(path)
    root = Path(__file__).resolve().parents[4]
    candidates = [
        root / "docs/healthtech/audits/luna-patent-dossiers-20261028-rights-cohort/rights-matrix.json",
        root / "docs/healthtech/audits/luna-patent-dossiers-20261028-atomic/rights-matrix.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise CohortProvenanceError("no reviewed HealthTech rights matrix is available")


def _resolve_typed_policy(
    policies: dict[str, SourceRights],
    *,
    policy_id: str,
    source_id: str,
    source_type: str,
) -> tuple[bool, str]:
    matches = [
        (key, policy)
        for key, policy in policies.items()
        if key == policy_id or policy.rights_id == policy_id
    ]
    if not matches:
        return False, "policy ID is absent from the reviewed rights matrix"
    if len(matches) != 1:
        return False, "policy ID is ambiguous in the reviewed rights matrix"
    key, policy = matches[0]
    if policy.source_types and source_type not in policy.source_types:
        return False, f"source type {source_type} does not match the policy catalog"
    if policy.source_id_prefixes:
        if not any(source_id.startswith(prefix) for prefix in policy.source_id_prefixes):
            return False, f"source ID {source_id} does not match the policy prefix"
    elif source_id not in {key, policy.rights_id}:
        return False, f"source ID {source_id} does not match the exact policy source"
    return True, "resolved against the reviewed rights matrix"


def verify_cohort_provenance(
    cohort_dir: str | Path,
    *,
    rights_matrix_path: str | Path | None = None,
) -> dict[str, Any]:
    """Verify source-backed disclosure coverage without reading raw third-party pages.

    The verifier checks the JSON boundary between runtime inputs and evaluator-only
    relations. It establishes structural provenance coverage only; it does not
    establish semantic relevance, patent validity, or rights beyond recorded policy.
    """
    cohort = Path(cohort_dir)
    manifest = _read_json(cohort / "manifest.json")
    try:
        rights_policies = load_rights_matrix(_rights_matrix_path(rights_matrix_path))
    except (OSError, ValueError, TypeError) as exc:
        raise CohortProvenanceError("reviewed rights matrix could not be loaded") from exc

    runtime = _read_json(cohort / str(manifest.get("runtime_path", "runtime.json")))
    references_payload = _read_json(
        cohort / str(manifest.get("evaluator_path", "evaluator/references.json"))
    )
    registry = _read_json(cohort / str(manifest.get("source_registry", "source_registry.json")))
    split = _read_json(cohort / str(manifest.get("split_path", "split_manifest.json")))

    devices = runtime.get("devices")
    patents = runtime.get("patents")
    if not isinstance(devices, list) or not devices:
        raise CohortProvenanceError("runtime.devices must be a nonempty list")
    if not isinstance(patents, list) or not patents:
        raise CohortProvenanceError("runtime.patents must be a nonempty list")

    query_ids = [item.get("query_id") for item in devices if isinstance(item, dict)]
    if len(query_ids) != len(devices) or any(not isinstance(value, str) or not value for value in query_ids):
        raise CohortProvenanceError("runtime.devices must have nonempty query_id values")
    if len(set(query_ids)) != len(query_ids):
        raise CohortProvenanceError("runtime.devices contain duplicate query IDs")
    query_set = set(query_ids)

    universe: set[str] = set()
    runtime_source_ids: set[str] = set()
    for item in patents:
        if not isinstance(item, dict):
            raise CohortProvenanceError("runtime.patents contains a non-object")
        patent_id = item.get("patent_id_canonical")
        normalized = _canonical_ids([patent_id], field="runtime.patents[].patent_id_canonical")
        if normalized[0] in universe:
            raise CohortProvenanceError(f"runtime universe repeats {normalized[0]}")
        universe.add(normalized[0])
        source_id = item.get("source_id")
        if not isinstance(source_id, str) or not source_id:
            raise CohortProvenanceError("runtime patent is missing source_id")
        runtime_source_ids.add(source_id)
    for item in devices:
        source_id = item.get("source_id")
        if isinstance(source_id, str) and source_id:
            runtime_source_ids.add(source_id)

    references = references_payload.get("references")
    if not isinstance(references, dict):
        raise CohortProvenanceError("evaluator references must be an object")
    reference_map = _reference_pairs(references)
    if not set(reference_map) <= query_set:
        raise CohortProvenanceError("references contain a query absent from runtime.devices")
    reference_pairs = {(query_id, patent_id) for query_id, ids in reference_map.items() for patent_id in ids}
    if not all(patent_id in universe for _, patent_id in reference_pairs):
        raise CohortProvenanceError("references contain a patent absent from runtime.patents")

    registry_rows = registry.get("sources")
    if not isinstance(registry_rows, list) or not registry_rows:
        raise CohortProvenanceError("source_registry.sources must be a nonempty list")
    registry_by_id: dict[str, dict[str, Any]] = {}
    for row in registry_rows:
        if not isinstance(row, dict) or not isinstance(row.get("source_id"), str):
            raise CohortProvenanceError("source registry contains an invalid row")
        source_id = row["source_id"]
        if source_id in registry_by_id:
            raise CohortProvenanceError(f"source registry repeats {source_id}")
        registry_by_id[source_id] = row

    evidence_rows = references_payload.get("disclosure_evidence")
    if not isinstance(evidence_rows, list) or not evidence_rows:
        raise CohortProvenanceError("disclosure_evidence must be a nonempty list")
    evidence_ids: set[str] = set()
    covered_pairs: dict[tuple[str, str], list[str]] = {}
    disclosure_source_ids: set[str] = set()
    legacy_rights_source_ids: set[str] = set()
    resolved_rights_policy_ids: set[str] = set()
    unresolved_rights_policy_ids: set[str] = set()
    unresolved_rights: list[dict[str, str | None]] = []
    rights_resolutions: list[dict[str, str | None]] = []
    for row in evidence_rows:
        if not isinstance(row, dict):
            raise CohortProvenanceError("disclosure_evidence contains a non-object")
        evidence_id = row.get("evidence_id")
        query_id = row.get("query_id")
        source_id = row.get("source_id")
        if not isinstance(evidence_id, str) or not evidence_id:
            raise CohortProvenanceError("disclosure evidence is missing evidence_id")
        if evidence_id in evidence_ids:
            raise CohortProvenanceError(f"disclosure evidence repeats {evidence_id}")
        evidence_ids.add(evidence_id)
        if query_id not in reference_map:
            raise CohortProvenanceError(f"evidence {evidence_id} has no eligible reference query")
        if not isinstance(source_id, str) or not source_id:
            raise CohortProvenanceError(f"evidence {evidence_id} is missing source_id")
        source = registry_by_id.get(source_id)
        if source is None:
            raise CohortProvenanceError(f"evidence {evidence_id} points to an unregistered source")
        if source.get("source_type") != "independent_disclosure":
            raise CohortProvenanceError(f"evidence {evidence_id} source is not an independent disclosure")
        rights_policy_id = source.get("rights_policy_id")
        if isinstance(rights_policy_id, str) and rights_policy_id.strip():
            normalized_policy_id = rights_policy_id.strip()
            resolved, reason = _resolve_typed_policy(
                rights_policies,
                policy_id=normalized_policy_id,
                source_id=source_id,
                source_type=str(source.get("source_type")),
            )
            rights_resolutions.append({
                "source_id": source_id,
                "rights_policy_id": normalized_policy_id,
                "status": "RESOLVED" if resolved else "UNRESOLVED",
                "reason": reason,
            })
            if resolved:
                resolved_rights_policy_ids.add(normalized_policy_id)
            else:
                unresolved_rights_policy_ids.add(normalized_policy_id)
                unresolved_rights.append({
                    "source_id": source_id,
                    "rights_policy_id": normalized_policy_id,
                    "reason": reason,
                })
        elif "rights_policy_id" in source:
            rights_resolutions.append({
                "source_id": source_id,
                "rights_policy_id": None,
                "status": "UNRESOLVED",
                "reason": "rights_policy_id is blank or not a string",
            })
            unresolved_rights_policy_ids.add("<blank>")
            unresolved_rights.append({
                "source_id": source_id,
                "rights_policy_id": None,
                "reason": "rights_policy_id is blank or not a string",
            })
        elif isinstance(source.get("rights"), str) and source["rights"].strip():
            legacy_rights_source_ids.add(source_id)
        else:
            raise CohortProvenanceError(f"evidence {evidence_id} source has no rights basis")
        if not isinstance(row.get("locator"), str) or not row["locator"].strip():
            raise CohortProvenanceError(f"evidence {evidence_id} is missing an exact locator")
        if not any(isinstance(row.get(field), str) and row[field].strip() for field in ("quoted_span", "structured_field")):
            raise CohortProvenanceError(f"evidence {evidence_id} is missing a quote or structured field")
        if not isinstance(row.get("support_basis"), str) or not row["support_basis"].strip():
            raise CohortProvenanceError(f"evidence {evidence_id} is missing support_basis")
        patent_ids = _canonical_ids(
            row.get("patent_id_canonical"),
            field=f"disclosure_evidence[{evidence_id!r}].patent_id_canonical",
            allow_scalar=True,
        )
        if not all(patent_id in reference_map[query_id] for patent_id in patent_ids):
            raise CohortProvenanceError(f"evidence {evidence_id} covers a pair absent from references")
        disclosure_source_ids.add(source_id)
        for patent_id in patent_ids:
            covered_pairs.setdefault((query_id, patent_id), []).append(evidence_id)

    missing_pairs = sorted(reference_pairs - set(covered_pairs))
    if missing_pairs:
        raise CohortProvenanceError(f"reference pairs without disclosure evidence: {missing_pairs[:3]}")
    extra_pairs = sorted(set(covered_pairs) - reference_pairs)
    if extra_pairs:
        raise CohortProvenanceError(f"disclosure evidence contains extra pairs: {extra_pairs[:3]}")

    runtime_exclusions = runtime.get("runtime_exclusions")
    exclusion_text = " ".join(str(value).lower() for value in runtime_exclusions or [])
    for required_term in ("disclosure", "evaluator", "split"):
        if required_term not in exclusion_text:
            raise CohortProvenanceError(f"runtime_exclusions must mention {required_term}")
    if runtime_source_ids & disclosure_source_ids:
        raise CohortProvenanceError("evaluator disclosure source leaked into runtime source IDs")

    split_payload = split.get("split") if isinstance(split.get("split"), dict) else split
    split_rows = split_payload.get("rows") if isinstance(split_payload, dict) else None
    if not isinstance(split_rows, list):
        raise CohortProvenanceError("split manifest is missing rows")
    split_query_ids = {row.get("query_id") for row in split_rows if isinstance(row, dict)}
    if split_query_ids != set(reference_map):
        raise CohortProvenanceError("split rows do not cover exactly the evaluator query set")
    final_holdout = split_payload.get("final_holdout", []) if isinstance(split_payload, dict) else []
    if not isinstance(final_holdout, list):
        raise CohortProvenanceError("split final_holdout must be a list")

    distractor_pairs = 0
    distractor_path = manifest.get("distractors_path")
    if isinstance(distractor_path, str):
        distractors = _read_json(cohort / distractor_path)
        by_query = distractors.get("by_query", distractors.get("distractors_by_query", {}))
        if not isinstance(by_query, dict):
            raise CohortProvenanceError("distractors must contain by_query")
        for query_id, values in by_query.items():
            if query_id not in reference_map:
                raise CohortProvenanceError("distractors contain an unknown query")
            ids = _canonical_ids(values, field=f"distractors[{query_id!r}]") if values else []
            if set(ids) & set(reference_map[query_id]):
                raise CohortProvenanceError("a distractor overlaps a disclosed reference pair")
            if not set(ids) <= universe:
                raise CohortProvenanceError("a distractor is absent from the runtime universe")
            distractor_pairs += len(ids)

    if manifest.get("reference_pairs") is not None and manifest["reference_pairs"] != len(reference_pairs):
        raise CohortProvenanceError("manifest reference_pairs disagrees with evaluator references")
    if manifest.get("unjudged_distractor_pairs") is not None and manifest["unjudged_distractor_pairs"] != distractor_pairs:
        raise CohortProvenanceError("manifest unjudged_distractor_pairs disagrees with distractors")

    if unresolved_rights:
        status = "PASS_WITH_UNRESOLVED_RIGHTS"
        rights_binding = "UNRESOLVED_TYPED_POLICY"
    elif legacy_rights_source_ids:
        status = "PASS_WITH_LEGACY_RIGHTS"
        rights_binding = "LEGACY_TEXT_ONLY"
    else:
        status = "PASS"
        rights_binding = "TYPED_POLICY_ID"
    return {
        "format": "ht-cohort-provenance-verification-v1",
        "status": status,
        "rights_binding": rights_binding,
        "cohort_status": manifest.get("status"),
        "counts": {
            "runtime_devices": len(devices),
            "runtime_patents": len(universe),
            "eligible_queries": len(reference_map),
            "disclosed_pairs": len(reference_pairs),
            "evidence_rows": len(evidence_rows),
            "covered_pairs": len(covered_pairs),
            "disclosure_sources": len(disclosure_source_ids),
            "distractor_pairs": distractor_pairs,
            "final_holdout_queries": len(final_holdout),
        },
        "query_ids_hash": content_hash(sorted(reference_map)),
        "hashes": {
            "manifest": content_hash(manifest),
            "runtime": content_hash(runtime),
            "references": content_hash(references_payload),
            "source_registry": content_hash(registry),
            "split": content_hash(split),
        },
        "disclosure_source_ids": sorted(disclosure_source_ids),
        "rights_policy_ids": sorted(resolved_rights_policy_ids),
        "rights_policy_resolutions": rights_resolutions,
        "unresolved_rights_policy_ids": sorted(unresolved_rights_policy_ids),
        "unresolved_rights": unresolved_rights,
        "legacy_rights_source_ids": sorted(legacy_rights_source_ids),
        "limitations": [
            "This verifies structural source-backed disclosure coverage only.",
            "Product-level disclosure is not an independent semantic relevance judgment.",
            "Unlisted pairs remain unjudged and are not recoded as negatives.",
            "Recorded rights policies govern use; this report does not grant redistribution rights.",
        ],
    }
