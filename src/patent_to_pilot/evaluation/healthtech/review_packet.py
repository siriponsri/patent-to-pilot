"""Prepare a provenance-bound, unlabeled semantic-review packet.

The packet freezes the runtime universe and group/split denominator without
creating semantic gold. Every query-patent pair remains explicitly unjudged.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import re
from typing import Any, Mapping

from patent_to_pilot.healthtech.contracts import canonical_patent_id


FORMAT = "ht-relevance-review-packet-v1"
STATUS = "READY_FOR_SEMANTIC_REVIEW_NOT_GOLD"
ALLOWED_SPLITS = {"development", "pilot", "final_holdout"}
RUNTIME_EXCLUSION_ALIASES = {
    "semantic_judgments": {
        "semantic_judgments",
        "semantic judgments",
        "evaluator references",
        "evaluator relations",
        "evaluator labels",
        "final holdout labels",
    },
    "split_answers": {"split_answers", "split answers"},
    "gold_derived_query_variants": {
        "gold_derived_query_variants",
        "gold-derived query variants",
        "evaluator references",
    },
    "family_labels": {"family_labels", "family labels"},
}
_SLUG_RE = re.compile(r"[^a-z0-9]+")


class ReviewPacketValidationError(ValueError):
    """Raised when an unlabeled review packet is not safe to use."""


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewPacketValidationError(f"{field} must be a nonempty string")
    return value.strip()


def _require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise ReviewPacketValidationError(f"{field} must be a list")
    return value


def _slug(value: str) -> str:
    normalized = _SLUG_RE.sub("-", value.casefold()).strip("-")
    return normalized or "unknown"


def _exclusion_evidence(values: list[Any]) -> dict[str, str]:
    normalized = {
        _require_text(value, "runtime exclusion").casefold()
        for value in values
    }
    evidence: dict[str, str] = {}
    for required, aliases in RUNTIME_EXCLUSION_ALIASES.items():
        matches = sorted(normalized.intersection(aliases))
        if not matches:
            raise ReviewPacketValidationError(f"runtime exclusions are incomplete: ['{required}']")
        evidence[required] = matches[0]
    return evidence


def _company_groups(groups: Mapping[str, Any], query_ids: set[str]) -> dict[str, str]:
    rows = _require_list(groups.get("company_groups"), "groups.company_groups")
    result: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ReviewPacketValidationError("company group rows must be objects")
        company = _require_text(row.get("company"), "company group company")
        group_id = f"company::{_slug(company)}"
        for query_id in _require_list(row.get("query_ids"), f"{group_id}.query_ids"):
            query_id = _require_text(query_id, f"{group_id}.query_id")
            if query_id not in query_ids:
                raise ReviewPacketValidationError(f"company group references unknown query: {query_id}")
            if query_id in result and result[query_id] != group_id:
                raise ReviewPacketValidationError(f"query has conflicting company groups: {query_id}")
            result[query_id] = group_id
    missing = sorted(query_ids - set(result))
    if missing:
        raise ReviewPacketValidationError(f"company groups do not cover runtime queries: {missing}")
    return result


def _split_rows(split_manifest: Mapping[str, Any], query_ids: set[str]) -> dict[str, dict[str, str]]:
    rows = _require_list(split_manifest.get("rows"), "split_manifest.rows")
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise ReviewPacketValidationError("split rows must be objects")
        query_id = _require_text(row.get("query_id"), "split query_id")
        if query_id not in query_ids:
            raise ReviewPacketValidationError(f"split references unknown query: {query_id}")
        if query_id in result:
            raise ReviewPacketValidationError(f"duplicate split row: {query_id}")
        split = _require_text(row.get("split"), f"{query_id}.split")
        if split not in ALLOWED_SPLITS:
            raise ReviewPacketValidationError(f"unsupported split: {split}")
        result[query_id] = {
            "split": split,
            "group_id": _require_text(row.get("group_id"), f"{query_id}.group_id"),
        }
    if set(result) != query_ids:
        raise ReviewPacketValidationError("split rows must cover every runtime query exactly once")
    if not any(row["split"] == "final_holdout" for row in result.values()):
        raise ReviewPacketValidationError("review packet requires a nonempty final holdout")
    return result


def _validate_company_split_disjointness(
    query_rows: Mapping[str, Mapping[str, str]],
    company_by_query: Mapping[str, str],
) -> dict[str, list[str]]:
    by_split: dict[str, set[str]] = defaultdict(set)
    for query_id, row in query_rows.items():
        by_split[row["split"]].add(company_by_query[query_id])
    overlap: dict[str, list[str]] = {}
    splits = sorted(by_split)
    for index, left in enumerate(splits):
        for right in splits[index + 1 :]:
            shared = sorted(by_split[left] & by_split[right])
            if shared:
                overlap[f"{left}::{right}"] = shared
    if overlap:
        raise ReviewPacketValidationError(f"company groups cross splits: {overlap}")
    return overlap


def _source_bindings(
    runtime_rows: list[Mapping[str, Any]],
    source_registry: Mapping[str, Any],
) -> list[dict[str, Any]]:
    source_rows = _require_list(source_registry.get("sources"), "source_registry.sources")
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in source_rows:
        if not isinstance(row, dict):
            raise ReviewPacketValidationError("source registry rows must be objects")
        source_id = _require_text(row.get("source_id"), "source_id")
        if source_id in by_id:
            raise ReviewPacketValidationError(f"duplicate source registry ID: {source_id}")
        by_id[source_id] = row

    needed = sorted({_require_text(row.get("source_id"), "runtime source_id") for row in runtime_rows})
    bindings: list[dict[str, Any]] = []
    for source_id in needed:
        source = by_id.get(source_id)
        if source is None:
            raise ReviewPacketValidationError(f"runtime source is absent from registry: {source_id}")
        hashes = {
            key: str(source[key])
            for key in ("sha256", "raw_html_sha256", "normalized_sha256", "pdf_sha256")
            if isinstance(source.get(key), str) and source[key]
        }
        bindings.append({
            "source_id": source_id,
            "source_type": source.get("source_type", ""),
            "revision": source.get("revision", ""),
            "rights_policy_id": source.get("rights_policy_id", ""),
            "rights_statement": source.get("rights", ""),
            "runtime_allowed": source.get("runtime_allowed") is True,
            "locator": source.get("url") or source.get("linked_document_url") or source.get("source_id"),
            "hashes": hashes,
            "semantic_judgment_clearance": "NOT_CLEARED_BY_THIS_PACKET",
            "intended_use": "local_review_packet_metadata_only",
        })
    return bindings


def _family_lookup(family_mapping: Mapping[str, Any] | None) -> tuple[dict[str, str], str]:
    if family_mapping is None:
        return {}, "NOT_SUPPLIED"
    mappings = _require_list(family_mapping.get("mappings"), "family_mapping.mappings")
    result: dict[str, str] = {}
    for row in mappings:
        if not isinstance(row, dict):
            raise ReviewPacketValidationError("family mapping rows must be objects")
        patent_id = canonical_patent_id(_require_text(row.get("patent_id_canonical"), "family patent ID"))
        family_id = _require_text(row.get("family_id"), "family_id")
        if patent_id in result and result[patent_id] != family_id:
            raise ReviewPacketValidationError(f"patent has conflicting family IDs: {patent_id}")
        result[patent_id] = family_id
    return result, "SOURCED_LOCAL_EVALUATOR_MAPPING_ONLY"


def build_relevance_review_packet(
    runtime: Mapping[str, Any],
    split_manifest: Mapping[str, Any],
    groups: Mapping[str, Any],
    source_registry: Mapping[str, Any],
    *,
    runtime_path: str,
    runtime_sha256: str,
    split_manifest_path: str,
    split_manifest_sha256: str,
    groups_path: str,
    groups_sha256: str,
    source_registry_path: str,
    source_registry_sha256: str,
    family_mapping: Mapping[str, Any] | None = None,
    family_mapping_path: str | None = None,
    family_mapping_sha256: str | None = None,
) -> dict[str, Any]:
    if runtime.get("status") != "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS":
        raise ReviewPacketValidationError("runtime must declare evaluator-label isolation")
    devices = _require_list(runtime.get("devices"), "runtime.devices")
    patents = _require_list(runtime.get("patents"), "runtime.patents")
    if not devices or not patents:
        raise ReviewPacketValidationError("runtime must contain devices and patents")
    query_ids = {_require_text(row.get("query_id"), "runtime query_id") for row in devices if isinstance(row, dict)}
    patent_ids = {
        canonical_patent_id(_require_text(row.get("patent_id_canonical"), "runtime patent ID"))
        for row in patents
        if isinstance(row, dict)
    }
    if len(query_ids) != len(devices) or len(patent_ids) != len(patents):
        raise ReviewPacketValidationError("runtime query and patent IDs must be unique")

    runtime_exclusion_values = _require_list(runtime.get("runtime_exclusions"), "runtime.runtime_exclusions")
    runtime_exclusions = {_require_text(value, "runtime exclusion") for value in runtime_exclusion_values}
    exclusion_evidence = _exclusion_evidence(runtime_exclusion_values)

    company_by_query = _company_groups(groups, query_ids)
    split_by_query = _split_rows(split_manifest, query_ids)
    company_overlap = _validate_company_split_disjointness(split_by_query, company_by_query)
    family_lookup, family_status = _family_lookup(family_mapping)
    bindings = _source_bindings([*devices, *patents], source_registry)

    device_by_query = {row["query_id"]: row for row in devices}
    patent_by_id = {canonical_patent_id(row["patent_id_canonical"]): row for row in patents}
    query_rows = []
    for query_id in sorted(query_ids):
        device = device_by_query[query_id]
        split = split_by_query[query_id]
        query_rows.append({
            "query_id": query_id,
            "split": split["split"],
            "company_group_id": company_by_query[query_id],
            "frozen_group_id": split["group_id"],
            "device_id_canonical": device["device_id_canonical"],
            "device_id_raw": device["device_id_raw"],
            "company": device.get("company", ""),
            "trade_name": device.get("trade_name", ""),
            "pma_number": device.get("pma_number", ""),
            "source_id": device["source_id"],
            "evidence_cutoff": device["evidence_cutoff"],
        })

    patent_rows = []
    for patent_id in sorted(patent_ids):
        patent = patent_by_id[patent_id]
        patent_rows.append({
            "patent_id_raw": patent["patent_id_raw"],
            "patent_id_canonical": patent_id,
            "document_kind": patent["document_kind"],
            "jurisdiction": patent["jurisdiction"],
            "title": patent["title"],
            "source_id": patent["source_id"],
            "source_revision": patent["source_revision"],
            "source_url": patent["source_url"],
            "source_date": patent["source_date"],
            "raw_html_sha256": patent["raw_html_sha256"],
            "normalized_sha256": patent["normalized_sha256"],
            "family_id": family_lookup.get(patent_id),
            "content_policy": "local_runtime_content_not_copied_into_review_packet",
        })

    review_rows = []
    for query in query_rows:
        for patent in patent_rows:
            review_rows.append({
                "review_row_id": f"{query['query_id']}::{patent['patent_id_canonical']}",
                "query_id": query["query_id"],
                "patent_id_canonical": patent["patent_id_canonical"],
                "split": query["split"],
                "company_group_id": query["company_group_id"],
                "frozen_group_id": query["frozen_group_id"],
                "judgment_state": "UNJUDGED",
                "candidate_basis": "runtime_candidate_universe",
                "product_disclosure_used": False,
                "review_locator": f"runtime://{query['query_id']}/{patent['patent_id_canonical']}",
            })

    split_query_counts = Counter(row["split"] for row in query_rows)
    packet = {
        "format": FORMAT,
        "status": STATUS,
        "semantic_gold_created": False,
        "runtime": {
            "path": runtime_path,
            "sha256": runtime_sha256,
            "query_count": len(query_rows),
            "patent_count": len(patent_rows),
            "runtime_exclusions": sorted(runtime_exclusions),
            "runtime_exclusion_evidence": exclusion_evidence,
        },
        "split": {
            "path": split_manifest_path,
            "sha256": split_manifest_sha256,
            "query_counts": dict(sorted(split_query_counts.items())),
            "final_holdout_query_ids": sorted(query["query_id"] for query in query_rows if query["split"] == "final_holdout"),
            "final_holdout_company_groups": sorted({query["company_group_id"] for query in query_rows if query["split"] == "final_holdout"}),
            "family_group_count": split_manifest.get("family_group_count"),
            "family_split_overlap_count": split_manifest.get("family_split_overlap_count"),
            "company_split_overlap": company_overlap,
        },
        "group_inputs": {
            "path": groups_path,
            "sha256": groups_sha256,
            "company_group_count": len(set(company_by_query.values())),
            "family_mapping_status": family_status,
            "family_mapping_path": family_mapping_path,
            "family_mapping_sha256": family_mapping_sha256,
        },
        "source_registry": {
            "path": source_registry_path,
            "sha256": source_registry_sha256,
            "bindings": bindings,
        },
        "queries": query_rows,
        "patents": patent_rows,
        "review_rows": review_rows,
        "counts": {
            "query_count": len(query_rows),
            "patent_count": len(patent_rows),
            "pair_denominator": len(review_rows),
            "unjudged_pair_count": len(review_rows),
            "semantic_label_count": 0,
        },
        "policy": {
            "unlisted_pair_policy": "UNJUDGED_NOT_NEGATIVE",
            "product_disclosure_promoted_to_semantic_gold": False,
            "evaluator_relations_read_by_packet_builder": False,
            "gold_derived_query_variants_used": False,
            "pending_requirements": [
                "rights-cleared semantic judgment source",
                "adjudicator role and source locator for each explicit label",
                "frozen judgment denominator after label intake",
            ],
        },
    }
    validate_relevance_review_packet(packet)
    return packet


def validate_relevance_review_packet(packet: Mapping[str, Any]) -> dict[str, Any]:
    if packet.get("format") != FORMAT:
        raise ReviewPacketValidationError(f"packet format must be {FORMAT}")
    if packet.get("status") != STATUS:
        raise ReviewPacketValidationError(f"packet status must be {STATUS}")
    if packet.get("semantic_gold_created") is not False:
        raise ReviewPacketValidationError("review packet cannot claim semantic gold")
    runtime = packet.get("runtime")
    split = packet.get("split")
    queries = _require_list(packet.get("queries"), "packet.queries")
    patents = _require_list(packet.get("patents"), "packet.patents")
    review_rows = _require_list(packet.get("review_rows"), "packet.review_rows")
    if not isinstance(runtime, dict) or not isinstance(split, dict):
        raise ReviewPacketValidationError("runtime and split metadata are required")
    _exclusion_evidence(_require_list(runtime.get("runtime_exclusions"), "packet.runtime_exclusions"))
    query_ids = [_require_text(row.get("query_id"), "packet query_id") for row in queries if isinstance(row, dict)]
    patent_ids = [canonical_patent_id(_require_text(row.get("patent_id_canonical"), "packet patent ID")) for row in patents if isinstance(row, dict)]
    if len(query_ids) != len(set(query_ids)) or len(patent_ids) != len(set(patent_ids)):
        raise ReviewPacketValidationError("packet query and patent IDs must be unique")
    query_rows_by_id = {row["query_id"]: row for row in queries if isinstance(row, dict)}
    if set(query_rows_by_id) != set(query_ids):
        raise ReviewPacketValidationError("packet query rows must be objects with unique IDs")
    company_by_query = {
        query_id: _require_text(row.get("company_group_id"), f"{query_id}.company_group_id")
        for query_id, row in query_rows_by_id.items()
    }
    split_by_query = {
        query_id: {"split": _require_text(row.get("split"), f"{query_id}.split")}
        for query_id, row in query_rows_by_id.items()
    }
    _validate_company_split_disjointness(split_by_query, company_by_query)
    expected_pairs = {(query_id, patent_id) for query_id in query_ids for patent_id in patent_ids}
    seen_pairs: set[tuple[str, str]] = set()
    for row in review_rows:
        if not isinstance(row, dict):
            raise ReviewPacketValidationError("review rows must be objects")
        pair = (
            _require_text(row.get("query_id"), "review query_id"),
            canonical_patent_id(_require_text(row.get("patent_id_canonical"), "review patent ID")),
        )
        if pair in seen_pairs:
            raise ReviewPacketValidationError(f"duplicate review pair: {pair[0]}::{pair[1]}")
        seen_pairs.add(pair)
        if row.get("judgment_state") != "UNJUDGED":
            raise ReviewPacketValidationError("review packet rows must remain UNJUDGED")
        if row.get("product_disclosure_used") is not False:
            raise ReviewPacketValidationError("product disclosure cannot seed review labels")
        if any(key in row for key in ("label", "basis", "adjudicator_role", "gold", "known_link")):
            raise ReviewPacketValidationError("review rows cannot contain semantic labels or evaluator shortcuts")
    if seen_pairs != expected_pairs:
        raise ReviewPacketValidationError("review rows must cover the full query-patent cartesian product exactly once")
    counts = packet.get("counts")
    if not isinstance(counts, dict):
        raise ReviewPacketValidationError("packet counts are required")
    if counts.get("pair_denominator") != len(expected_pairs) or counts.get("unjudged_pair_count") != len(expected_pairs):
        raise ReviewPacketValidationError("packet denominator counts are inconsistent")
    if counts.get("semantic_label_count") != 0:
        raise ReviewPacketValidationError("packet semantic label count must remain zero")
    holdout_ids = split.get("final_holdout_query_ids")
    if not isinstance(holdout_ids, list) or not holdout_ids:
        raise ReviewPacketValidationError("packet must retain a final holdout")
    return {
        "format": "ht-relevance-review-packet-validation-v1",
        "status": "PASS",
        "query_count": len(query_ids),
        "patent_count": len(patent_ids),
        "pair_denominator": len(expected_pairs),
        "unjudged_pair_count": len(expected_pairs),
        "semantic_label_count": 0,
        "final_holdout_query_count": len(holdout_ids),
        "interpretation": "Packet freezes candidate coverage only; every pair remains unjudged and no semantic gold was created.",
    }
