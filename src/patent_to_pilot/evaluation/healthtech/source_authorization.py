"""Fail-closed preflight for an authorized semantic-judgment source."""
from __future__ import annotations

import re
from typing import Any


FORMAT = "ht-semantic-source-authorization-v1"
ALLOWED_STATUSES = {
    "DRAFT_SOURCE_AUTHORIZATION",
    "APPROVED_LOCAL_RESEARCH_SOURCE",
}
ALLOWED_LOCAL_DECISIONS = {
    "ALLOWED_LOCAL_RESEARCH",
    "ALLOWED_LOCAL_SNAPSHOT",
    "ALLOWED_WITH_ATTRIBUTION",
}
ALLOWED_LABELS = {"relevant", "not_relevant"}
HEX64 = re.compile(r"^[a-f0-9]{64}$")


class SourceAuthorizationError(ValueError):
    """Raised when a source authorization manifest is unsafe or incomplete."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceAuthorizationError(f"{field} must be a nonempty string")
    return value.strip()


def _hash(value: Any, field: str) -> str:
    value = _text(value, field)
    if not HEX64.fullmatch(value):
        raise SourceAuthorizationError(f"{field} must be a lowercase SHA-256")
    return value


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise SourceAuthorizationError(f"{field} must be boolean")
    return value


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise SourceAuthorizationError(f"{field} must be a positive integer")
    return value


def _relative_path(value: Any, field: str) -> str:
    path = _text(value, field).replace("\\", "/")
    if path.startswith("/") or re.match(r"^[A-Za-z]:/", path):
        raise SourceAuthorizationError(f"{field} must be relative")
    parts = [part for part in path.split("/") if part not in {"", "."}]
    if not parts or ".." in parts:
        raise SourceAuthorizationError(f"{field} contains an unsafe path")
    return "/".join(parts)


def validate_semantic_source_authorization(manifest: dict[str, Any]) -> dict[str, Any]:
    """Validate an owner-authorized source manifest before acquisition or ingest."""
    if not isinstance(manifest, dict):
        raise SourceAuthorizationError("manifest must be a JSON object")
    if manifest.get("format") != FORMAT:
        raise SourceAuthorizationError(f"manifest format must be {FORMAT}")
    status = _text(manifest.get("status"), "status")
    if status not in ALLOWED_STATUSES:
        raise SourceAuthorizationError("status is not an allowed authorization state")

    source = manifest.get("source")
    if not isinstance(source, dict):
        raise SourceAuthorizationError("source must be an object")
    source_id = _text(source.get("source_id"), "source.source_id")
    source_revision = _text(source.get("source_revision"), "source.source_revision")
    source_sha256 = _hash(source.get("source_sha256"), "source.source_sha256")
    source_locator = _text(source.get("locator"), "source.locator")
    source_class = _text(source.get("source_class"), "source.source_class")

    rights = manifest.get("rights")
    if not isinstance(rights, dict):
        raise SourceAuthorizationError("rights must be an object")
    rights_policy_id = _text(rights.get("rights_policy_id"), "rights.rights_policy_id")
    rights_basis = _text(rights.get("rights_basis"), "rights.rights_basis")
    rights_clause = _text(rights.get("rights_clause"), "rights.rights_clause")
    intended_use = _text(rights.get("intended_use"), "rights.intended_use")
    if intended_use != "semantic_relevance_judgment":
        raise SourceAuthorizationError("rights.intended_use must be semantic_relevance_judgment")
    use_decision = _text(rights.get("use_decision"), "rights.use_decision")
    if use_decision not in ALLOWED_LOCAL_DECISIONS:
        raise SourceAuthorizationError("rights.use_decision is not cleared for local research")
    for field in ("provider_transfer_allowed", "public_redistribution_allowed"):
        if _bool(rights.get(field), f"rights.{field}"):
            raise SourceAuthorizationError(f"rights.{field} must be false")
    attribution_required = _bool(rights.get("attribution_required"), "rights.attribution_required")

    acquisition = manifest.get("acquisition")
    if not isinstance(acquisition, dict):
        raise SourceAuthorizationError("acquisition must be an object")
    retrieval_method = _text(acquisition.get("retrieval_method"), "acquisition.retrieval_method")
    resumable = _bool(acquisition.get("resumable"), "acquisition.resumable")
    if not resumable:
        raise SourceAuthorizationError("acquisition.resumable must be true")
    expected_bytes = _positive_int(acquisition.get("expected_bytes"), "acquisition.expected_bytes")
    max_bytes = _positive_int(acquisition.get("max_bytes"), "acquisition.max_bytes")
    if expected_bytes > max_bytes:
        raise SourceAuthorizationError("acquisition.expected_bytes exceeds max_bytes")
    expected_files = _positive_int(acquisition.get("expected_files"), "acquisition.expected_files")
    max_files = _positive_int(acquisition.get("max_files"), "acquisition.max_files")
    if expected_files > max_files:
        raise SourceAuthorizationError("acquisition.expected_files exceeds max_files")
    storage_relpath = _relative_path(acquisition.get("storage_relpath"), "acquisition.storage_relpath")
    raw_relpath = _relative_path(acquisition.get("raw_relpath"), "acquisition.raw_relpath")
    normalized_relpath = _relative_path(acquisition.get("normalized_relpath"), "acquisition.normalized_relpath")
    if raw_relpath == normalized_relpath:
        raise SourceAuthorizationError("raw_relpath and normalized_relpath must be distinct")

    labels = manifest.get("judgment_contract")
    if not isinstance(labels, dict):
        raise SourceAuthorizationError("judgment_contract must be an object")
    declared_labels = labels.get("allowed_labels")
    if not isinstance(declared_labels, list) or {str(value) for value in declared_labels} != ALLOWED_LABELS:
        raise SourceAuthorizationError("judgment_contract.allowed_labels must be relevant and not_relevant")
    if _text(labels.get("absent_pair_policy"), "judgment_contract.absent_pair_policy") != "unjudged_not_negative":
        raise SourceAuthorizationError("absent_pair_policy must preserve unjudged pairs")
    if not _bool(labels.get("exact_locator_required"), "judgment_contract.exact_locator_required"):
        raise SourceAuthorizationError("exact_locator_required must be true")
    if not _bool(labels.get("adjudicator_role_required"), "judgment_contract.adjudicator_role_required"):
        raise SourceAuthorizationError("adjudicator_role_required must be true")

    cohort = manifest.get("cohort_requirements")
    if not isinstance(cohort, dict):
        raise SourceAuthorizationError("cohort_requirements must be an object")
    company_groups = _positive_int(cohort.get("minimum_independent_company_groups"), "cohort_requirements.minimum_independent_company_groups")
    family_groups = _positive_int(cohort.get("minimum_independent_family_groups"), "cohort_requirements.minimum_independent_family_groups")
    if company_groups < 2 or family_groups < 2:
        raise SourceAuthorizationError("cohort requirements must include at least two company and family groups")
    if not _bool(cohort.get("final_holdout_predeclared"), "cohort_requirements.final_holdout_predeclared"):
        raise SourceAuthorizationError("final_holdout_predeclared must be true")
    if _text(cohort.get("cross_split_leakage_policy"), "cohort_requirements.cross_split_leakage_policy") != "reject":
        raise SourceAuthorizationError("cross_split_leakage_policy must be reject")

    return {
        "format": "ht-semantic-source-authorization-validation-v1",
        "status": "PASS",
        "authorization_status": status,
        "source_id": source_id,
        "source_revision": source_revision,
        "source_sha256": source_sha256,
        "source_locator": source_locator,
        "source_class": source_class,
        "rights_policy_id": rights_policy_id,
        "rights_basis": rights_basis,
        "use_decision": use_decision,
        "attribution_required": attribution_required,
        "retrieval_method": retrieval_method,
        "resumable": resumable,
        "storage_bounds": {
            "expected_bytes": expected_bytes,
            "max_bytes": max_bytes,
            "expected_files": expected_files,
            "max_files": max_files,
        },
        "relative_paths": {
            "storage": storage_relpath,
            "raw": raw_relpath,
            "normalized": normalized_relpath,
        },
        "allowed_labels": sorted(ALLOWED_LABELS),
        "absent_pair_policy": "unjudged_not_negative",
        "minimum_independent_company_groups": company_groups,
        "minimum_independent_family_groups": family_groups,
        "final_holdout_predeclared": True,
        "interpretation": "Authorization preflight only; it creates no semantic labels and does not acquire or publish source data.",
    }
