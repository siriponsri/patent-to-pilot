"""Typed source-rights policies and fail-closed product boundaries."""
from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Literal

from patent_to_pilot.healthtech.contracts import DossierVersion, SourcePayload, SourceRights


ExportPurpose = Literal["local_research", "product_display", "redistribution"]


class RightsBoundaryError(ValueError):
    """Raised when a requested surface exceeds the recorded source rights."""


def load_rights_matrix(path: str | Path) -> dict[str, SourceRights]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("sources"), list):
        raise ValueError("rights matrix must contain a sources list")
    policies: dict[str, SourceRights] = {}
    for item in raw["sources"]:
        if not isinstance(item, dict):
            raise ValueError("rights matrix source entries must be objects")
        source_id = str(item["source_id"])
        if source_id in policies:
            raise ValueError(f"duplicate rights policy: {source_id}")
        intended = item.get("intended_use")
        if not isinstance(intended, dict):
            raise ValueError(f"rights policy missing intended_use: {source_id}")
        policy = SourceRights(
            rights_id=source_id,
            source_id_prefixes=[str(value) for value in item.get("source_id_prefixes", [])],
            source_types=[str(value) for value in item.get("source_types", [])],
            basis_url=str(item.get("url", "")),
            checked_date=item.get("checked_date", raw.get("checked_date")),
            basis_revision=str(item.get("source_revision", "")),
            basis_sha256=str(item.get("source_sha256", "")),
            clause_locator=str(item.get("clause_locator", "")),
            clause=str(item.get("clause", "")),
            interpretation=str(item.get("interpretation", "")),
            acquisition=str(intended.get("acquisition", "UNRESOLVED")),
            local_evaluation=str(intended.get("local_evaluation", "UNRESOLVED")),
            product_display=str(intended.get("product_display", "UNRESOLVED")),
            redistribution=str(intended.get("redistribution", "UNRESOLVED")),
            displayable_fields=[str(value) for value in item.get("displayable_fields", [])],
            limits=[str(value) for value in item.get("limits", [])],
        )
        policies[source_id] = policy
    return policies


def select_rights_policy(
    policies: dict[str, SourceRights], *, source_id: str, source_type: str
) -> SourceRights:
    exact = policies.get(source_id)
    if exact is not None:
        return exact
    prefix_matches = [
        policy for policy in policies.values()
        if any(source_id.startswith(prefix) for prefix in policy.source_id_prefixes)
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]
    type_matches = [policy for policy in policies.values() if source_type in policy.source_types]
    if len(type_matches) == 1:
        return type_matches[0]
    if not prefix_matches and not type_matches:
        raise RightsBoundaryError(
            f"no rights policy for source {source_id} ({source_type})"
        )
    raise RightsBoundaryError(
        f"ambiguous rights policy for source {source_id} ({source_type})"
    )


def attach_rights(source: SourcePayload, policy: SourceRights) -> SourcePayload:
    return source.model_copy(update={"rights": policy})


def source_rights_summary(source: SourcePayload) -> dict[str, Any]:
    rights = source.rights
    if rights is None:
        return {
            "source_id": source.source.source_id,
            "source_type": source.source.source_type,
            "status": "MISSING_POLICY",
        }
    return {
        "source_id": source.source.source_id,
        "source_type": source.source.source_type,
        "rights_id": rights.rights_id,
        "basis_url": rights.basis_url,
        "basis_revision": rights.basis_revision,
        "basis_sha256": rights.basis_sha256,
        "checked_date": rights.checked_date.isoformat(),
        "clause_locator": rights.clause_locator,
        "intended_use": {
            "acquisition": rights.acquisition,
            "local_evaluation": rights.local_evaluation,
            "product_display": rights.product_display,
            "redistribution": rights.redistribution,
        },
        "displayable_fields": list(rights.displayable_fields),
        "limits": list(rights.limits),
    }


def _decision_allowed(decision: str, purpose: ExportPurpose) -> bool:
    if purpose == "local_research":
        return decision in {
            "ALLOWED",
            "ALLOWED_WITH_ATTRIBUTION",
            "ALLOWED_LOCAL_SNAPSHOT",
            "ALLOWED_LOCAL_RESEARCH",
            "ALLOWED_ONLY_FOR_REVIEWED_PUBLIC_DOMAIN_FIELDS",
        }
    return decision in {"ALLOWED", "ALLOWED_WITH_ATTRIBUTION"}


def enforce_source_rights(source: SourcePayload, *, purpose: ExportPurpose) -> None:
    if source.synthetic:
        return
    rights = source.rights
    if rights is None:
        raise RightsBoundaryError(
            f"{purpose} blocked: source {source.source.source_id} has no rights policy"
        )
    decision = getattr(rights, "local_evaluation" if purpose == "local_research" else purpose)
    if not _decision_allowed(decision, purpose):
        raise RightsBoundaryError(
            f"{purpose} blocked for source {source.source.source_id}: {decision}; "
            f"basis {rights.basis_url}#{rights.clause_locator}"
        )


def enforce_displayable_field(source: SourcePayload, field: str, *, purpose: ExportPurpose) -> None:
    """Reject fields that are not reviewed for externally visible surfaces."""
    if purpose == "local_research" or source.synthetic:
        return
    rights = source.rights
    if rights is None:
        raise RightsBoundaryError(
            f"{purpose} blocked: source {source.source.source_id} has no rights policy"
        )
    if field not in rights.displayable_fields:
        raise RightsBoundaryError(
            f"{purpose} blocked for source {source.source.source_id}: "
            f"field {field} is not listed in displayable_fields"
        )


def limit_displayable_payload(source: SourcePayload, payload: Any, *, purpose: ExportPurpose) -> Any:
    """Keep externally visible mapping payloads to reviewed top-level fields."""
    if purpose == "local_research" or source.synthetic:
        return payload
    rights = source.rights
    if rights is None:
        raise RightsBoundaryError(
            f"{purpose} blocked: source {source.source.source_id} has no rights policy"
        )
    if not isinstance(payload, dict):
        raise RightsBoundaryError(
            f"{purpose} blocked for source {source.source.source_id}: "
            "displayable_fields require a mapping payload"
        )
    return {key: value for key, value in payload.items() if key in rights.displayable_fields}


def enforce_dossier_rights(dossier: DossierVersion, *, purpose: ExportPurpose) -> None:
    for source in dossier.sources:
        enforce_source_rights(source, purpose=purpose)
