"""Fail-closed intake for rights-cleared semantic relevance judgments.

This contract keeps product disclosure links separate from semantic labels and
leaves every unlisted query-patent pair unjudged.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import re
from typing import Any

from patent_to_pilot.healthtech.contracts import canonical_patent_id


FORMAT = "ht-relevance-judgment-cohort-v1"
ALLOWED_LABELS = {"relevant", "not_relevant"}
ALLOWED_BASES = {"expert_adjudication", "benchmark_gold", "authored_fixture"}
ALLOWED_SPLITS = {"development", "pilot", "final_holdout"}
ALLOWED_LOCAL_DECISIONS = {
    "ALLOWED",
    "ALLOWED_WITH_ATTRIBUTION",
    "ALLOWED_LOCAL_RESEARCH",
    "ALLOWED_LOCAL_SNAPSHOT",
}
REQUIRED_RUNTIME_EXCLUSIONS = {
    "semantic_judgments",
    "split_answers",
    "gold_derived_query_variants",
    "family_labels",
}
HEX64 = re.compile(r"^[a-f0-9]{64}$")


class JudgmentValidationError(ValueError):
    """Raised when a judgment manifest cannot support evaluation safely."""


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JudgmentValidationError(f"{field} must be a nonempty string")
    return value.strip()


def _require_hash(value: Any, field: str) -> str:
    value = _require_text(value, field)
    if not HEX64.fullmatch(value):
        raise JudgmentValidationError(f"{field} must be a lowercase SHA-256")
    return value


def _require_list(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise JudgmentValidationError(f"{field} must be a list")
    return value


def _split_overlap(rows: list[dict[str, Any]], field: str) -> dict[str, list[str]]:
    by_split: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        value = row.get(field)
        if value:
            by_split[str(row["split"])].add(str(value))
    splits = sorted(by_split)
    overlaps: dict[str, list[str]] = {}
    for left_index, left in enumerate(splits):
        for right in splits[left_index + 1 :]:
            shared = sorted(by_split[left] & by_split[right])
            if shared:
                overlaps[f"{left}::{right}"] = shared
    return overlaps


def validate_relevance_judgment_manifest(
    manifest: dict[str, Any],
    *,
    runtime_query_ids: list[str],
    runtime_universe: list[str],
    runtime_sha256: str | None = None,
) -> dict[str, Any]:
    """Validate a semantic-judgment manifest against a runtime-only universe."""
    if not isinstance(manifest, dict):
        raise JudgmentValidationError("manifest must be a JSON object")
    if manifest.get("format") != FORMAT:
        raise JudgmentValidationError(f"manifest format must be {FORMAT}")
    status = _require_text(manifest.get("status"), "status")
    if status not in {"DRAFT_VALIDATED_RELEVANCE_JUDGMENT_COHORT", "FROZEN_RELEVANCE_JUDGMENT_COHORT"}:
        raise JudgmentValidationError("status must identify a validated or frozen judgment cohort")

    expected_queries = [str(value) for value in runtime_query_ids]
    if not expected_queries or len(expected_queries) != len(set(expected_queries)):
        raise JudgmentValidationError("runtime query IDs must be nonempty and unique")
    canonical_universe = [canonical_patent_id(str(value)) for value in runtime_universe]
    if len(canonical_universe) != len(set(canonical_universe)):
        raise JudgmentValidationError("runtime universe contains duplicate canonical IDs")
    query_set = set(expected_queries)
    universe_set = set(canonical_universe)

    if runtime_sha256 is not None:
        declared_runtime_sha = _require_hash(manifest.get("runtime_sha256"), "runtime_sha256")
        if declared_runtime_sha != runtime_sha256:
            raise JudgmentValidationError("runtime SHA-256 does not match the supplied runtime")

    runtime_exclusions = {
        _require_text(value, "runtime_exclusions item")
        for value in _require_list(manifest.get("runtime_exclusions"), "runtime_exclusions")
    }
    missing_exclusions = sorted(REQUIRED_RUNTIME_EXCLUSIONS - runtime_exclusions)
    if missing_exclusions:
        raise JudgmentValidationError(f"runtime exclusions are incomplete: {missing_exclusions}")

    source_rows = _require_list(manifest.get("sources"), "sources")
    sources: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        if not isinstance(row, dict):
            raise JudgmentValidationError("source rows must be objects")
        source_id = _require_text(row.get("source_id"), "source_id")
        if source_id in sources:
            raise JudgmentValidationError(f"duplicate source_id: {source_id}")
        source = {
            "source_id": source_id,
            "source_revision": _require_text(row.get("source_revision"), f"{source_id}.source_revision"),
            "source_sha256": _require_hash(row.get("source_sha256"), f"{source_id}.source_sha256"),
            "rights_policy_id": _require_text(row.get("rights_policy_id"), f"{source_id}.rights_policy_id"),
            "intended_use": _require_text(row.get("intended_use"), f"{source_id}.intended_use"),
            "use_decision": _require_text(row.get("use_decision"), f"{source_id}.use_decision"),
            "locator": _require_text(row.get("locator"), f"{source_id}.locator"),
        }
        if source["intended_use"] != "semantic_relevance_judgment":
            raise JudgmentValidationError(f"source {source_id} lacks semantic judgment intended use")
        if source["use_decision"] not in ALLOWED_LOCAL_DECISIONS:
            raise JudgmentValidationError(f"source {source_id} is not cleared for local judgment use")
        sources[source_id] = source

    judgment_rows = _require_list(manifest.get("judgments"), "judgments")
    if not judgment_rows:
        raise JudgmentValidationError("judgments must contain at least one explicit label")
    judgment_ids: set[str] = set()
    pair_labels: dict[tuple[str, str], str] = {}
    label_counts: Counter[str] = Counter()
    query_counts: Counter[str] = Counter()
    for row in judgment_rows:
        if not isinstance(row, dict):
            raise JudgmentValidationError("judgment rows must be objects")
        judgment_id = _require_text(row.get("judgment_id"), "judgment_id")
        if judgment_id in judgment_ids:
            raise JudgmentValidationError(f"duplicate judgment_id: {judgment_id}")
        judgment_ids.add(judgment_id)
        query_id = _require_text(row.get("query_id"), f"{judgment_id}.query_id")
        if query_id not in query_set:
            raise JudgmentValidationError(f"judgment query is absent from runtime: {query_id}")
        try:
            patent_id = canonical_patent_id(_require_text(row.get("patent_id_raw"), f"{judgment_id}.patent_id_raw"))
            declared_patent_id = canonical_patent_id(_require_text(row.get("patent_id_canonical"), f"{judgment_id}.patent_id_canonical"))
        except ValueError as exc:
            raise JudgmentValidationError(f"invalid patent identity in {judgment_id}") from exc
        if patent_id != declared_patent_id:
            raise JudgmentValidationError(f"raw/canonical patent mismatch in {judgment_id}")
        if patent_id not in universe_set:
            raise JudgmentValidationError(f"judgment patent is absent from runtime universe: {patent_id}")
        label = _require_text(row.get("label"), f"{judgment_id}.label")
        if label not in ALLOWED_LABELS:
            raise JudgmentValidationError(f"unsupported judgment label: {label}")
        basis = _require_text(row.get("basis"), f"{judgment_id}.basis")
        if basis not in ALLOWED_BASES:
            raise JudgmentValidationError(f"unsupported judgment basis: {basis}")
        if basis == "authored_fixture" and row.get("synthetic") is not True:
            raise JudgmentValidationError("authored_fixture judgments must be marked synthetic=true")
        if basis != "authored_fixture" and row.get("synthetic") is True:
            raise JudgmentValidationError("non-fixture judgments cannot be marked synthetic")
        if basis == "product_disclosure" or row.get("source_class") == "product_disclosure":
            raise JudgmentValidationError("product disclosure cannot be promoted to semantic relevance judgment")
        source_id = _require_text(row.get("source_id"), f"{judgment_id}.source_id")
        source = sources.get(source_id)
        if source is None:
            raise JudgmentValidationError(f"judgment source is not registered: {source_id}")
        if _require_text(row.get("source_revision"), f"{judgment_id}.source_revision") != source["source_revision"]:
            raise JudgmentValidationError(f"source revision mismatch in {judgment_id}")
        if _require_hash(row.get("source_sha256"), f"{judgment_id}.source_sha256") != source["source_sha256"]:
            raise JudgmentValidationError(f"source hash mismatch in {judgment_id}")
        _require_text(row.get("locator"), f"{judgment_id}.locator")
        if basis == "expert_adjudication":
            _require_text(row.get("adjudicator_role"), f"{judgment_id}.adjudicator_role")
        pair = (query_id, patent_id)
        if pair in pair_labels:
            raise JudgmentValidationError(f"duplicate or conflicting judgment pair: {query_id}::{patent_id}")
        pair_labels[pair] = label
        label_counts[label] += 1
        query_counts[query_id] += 1

    split_rows = _require_list(manifest.get("split_rows"), "split_rows")
    if {row.get("query_id") for row in split_rows if isinstance(row, dict)} != query_set:
        raise JudgmentValidationError("split_rows must cover every runtime query exactly once")
    split_by_query: dict[str, dict[str, Any]] = {}
    for row in split_rows:
        if not isinstance(row, dict):
            raise JudgmentValidationError("split rows must be objects")
        query_id = _require_text(row.get("query_id"), "split query_id")
        if query_id in split_by_query:
            raise JudgmentValidationError(f"duplicate split row: {query_id}")
        split = _require_text(row.get("split"), f"{query_id}.split")
        if split not in ALLOWED_SPLITS:
            raise JudgmentValidationError(f"unsupported split: {split}")
        company_group_id = _require_text(row.get("company_group_id"), f"{query_id}.company_group_id")
        family_group_id = row.get("family_group_id")
        if family_group_id is not None:
            family_group_id = _require_text(family_group_id, f"{query_id}.family_group_id")
        split_by_query[query_id] = {
            "query_id": query_id,
            "split": split,
            "company_group_id": company_group_id,
            "family_group_id": family_group_id,
        }

    holdout_policy = manifest.get("holdout_policy")
    if not isinstance(holdout_policy, dict):
        raise JudgmentValidationError("holdout_policy must be an object")
    company_disjoint = holdout_policy.get("company_disjoint") is True
    family_disjoint = holdout_policy.get("family_disjoint") is True
    require_family = holdout_policy.get("require_family_mapping_for_final_holdout") is True
    split_records = list(split_by_query.values())
    company_overlap = _split_overlap(split_records, "company_group_id")
    family_overlap = _split_overlap(split_records, "family_group_id")
    if company_disjoint and company_overlap:
        raise JudgmentValidationError(f"company groups cross splits: {company_overlap}")
    if family_disjoint and family_overlap:
        raise JudgmentValidationError(f"family groups cross splits: {family_overlap}")
    holdout_rows = [row for row in split_records if row["split"] == "final_holdout"]
    if holdout_rows and require_family and any(row["family_group_id"] is None for row in holdout_rows):
        raise JudgmentValidationError("final holdout requires sourced family mapping under this policy")

    split_query_counts = Counter(row["split"] for row in split_records)
    company_groups_by_split = {
        split: sorted({row["company_group_id"] for row in split_records if row["split"] == split})
        for split in sorted(split_query_counts)
    }
    family_groups_by_split = {
        split: sorted({row["family_group_id"] for row in split_records if row["split"] == split and row["family_group_id"]})
        for split in sorted(split_query_counts)
    }
    family_known = sum(row["family_group_id"] is not None for row in split_records)
    family_coverage = family_known / len(split_records)
    generalization_status = "NOT_ESTIMABLE"
    if holdout_rows and family_coverage == 1.0 and len(set(row["company_group_id"] for row in split_records)) >= 2:
        generalization_status = "DESCRIPTIVE_HOLDOUT_READY"

    total_pairs = len(expected_queries) * len(universe_set)
    judged_pairs = len(pair_labels)
    return {
        "format": "ht-relevance-judgment-validation-v1",
        "status": "PASS",
        "manifest_status": status,
        "runtime_query_count": len(expected_queries),
        "runtime_patent_count": len(universe_set),
        "judged_pair_count": judged_pairs,
        "unjudged_pair_count": total_pairs - judged_pairs,
        "label_counts": dict(sorted(label_counts.items())),
        "queries_with_judgments": sorted(query_counts),
        "queries_without_judgments": sorted(query_set - set(query_counts)),
        "split_query_counts": dict(sorted(split_query_counts.items())),
        "company_groups_by_split": company_groups_by_split,
        "family_groups_by_split": family_groups_by_split,
        "family_coverage": family_coverage,
        "company_split_overlap": company_overlap,
        "family_split_overlap": family_overlap,
        "generalization_status": generalization_status,
        "runtime_exclusions": sorted(runtime_exclusions),
        "source_count": len(sources),
        "judgment_basis_counts": dict(sorted(Counter(str(row.get("basis")) for row in judgment_rows).items())),
        "interpretation": "Explicit semantic labels only; absent query-patent pairs remain unjudged and are not negatives.",
    }
