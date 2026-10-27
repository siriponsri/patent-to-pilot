"""HealthTech extensions to the shared source and product contracts (HT-W02)."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from typing import Any, Literal

from pydantic import ConfigDict, Field, model_validator

from patent_to_pilot.core.models import SourceRecord
from patent_to_pilot.product.contracts import Closed, ProjectBrief


def content_hash(value: Any) -> str:
    """Hash canonical JSON; the payload representation is part of this contract."""
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def canonical_patent_id(raw: str) -> str:
    """Normalize separators/case, preserve jurisdiction, leading zeros and kind.

    This is document identity, not a family merge or application/grant join.
    Unknown syntax fails closed; aliases require an explicit, sourced mapping.
    """
    value = re.sub(r"[\s,./-]", "", raw).upper()
    if not re.fullmatch(r"[A-Z]{2}[0-9]{4,14}(?:[A-Z][0-9]?)?", value):
        raise ValueError("unsupported patent document identifier")
    return value


class Contract(Closed):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class AcquisitionBudget(Contract):
    max_search_calls: int = Field(default=3, ge=0, le=100)
    max_returned_candidates: int = Field(default=60, ge=0, le=10000)
    accounting: Literal["offline_counts"] = "offline_counts"


class DeviceQuery(Contract):
    query_id: str = Field(min_length=1)
    brief: ProjectBrief
    device_id_raw: str = Field(min_length=1)
    device_id_canonical: str = Field(min_length=1)
    selected_comparator_source_id: str = Field(min_length=1)
    technical_description: str = Field(min_length=1)
    features_of_interest: list[str] = Field(default_factory=list)
    user_questions: list[str] = Field(default_factory=list)
    company_metadata: dict[str, str] = Field(default_factory=dict)
    company_source_id: str | None = None
    jurisdiction: str = Field(min_length=1)
    evidence_cutoff: date
    permitted_inputs: list[str] = Field(min_length=1)
    acquisition_budget: AcquisitionBudget = Field(default_factory=AcquisitionBudget)

    @model_validator(mode="after")
    def permitted(self):
        if self.brief.data_class == "private":
            raise ValueError("this local public/synthetic workflow does not accept private inputs")
        required = {self.selected_comparator_source_id}
        if self.company_metadata:
            if not self.company_source_id:
                raise ValueError("company metadata requires source basis")
            required.add(self.company_source_id)
        if not required <= set(self.permitted_inputs):
            raise ValueError("comparator/company source must be a permitted input")
        if any(not item.strip() for item in self.features_of_interest + self.user_questions):
            raise ValueError("features/questions must not be blank")
        return self


class SourcePayload(Contract):
    source: SourceRecord
    payload: str | dict[str, Any]
    jurisdiction: str = Field(min_length=1)
    source_date: date
    synthetic: bool

    @model_validator(mode="after")
    def hash_matches(self):
        if self.source.sha256 != content_hash(self.payload):
            raise ValueError("source payload hash mismatch")
        return self


class EvidenceItem(Contract):
    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    payload_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    locator: str = Field(min_length=1)
    quoted_span: str | None = None
    structured_field: str | None = None
    structured_value: Any = None
    evidence_kind: Literal["source_fact", "patent_disclosure", "reported_experiment",
                           "regulatory_record", "trial_record", "system_inference", "unresolved"]
    statement: str = Field(min_length=1)
    support_basis: str = Field(min_length=1)
    jurisdiction: str = Field(min_length=1)
    source_date: date
    extraction_method: Literal["literal_span", "structured_field", "authored_inference"]
    verification_status: Literal["not_checked", "exact_span_checked", "field_value_checked",
                                 "not_independently_validated"] = "not_checked"

    @model_validator(mode="after")
    def basis(self):
        if self.extraction_method == "literal_span" and (not self.quoted_span or self.structured_field):
            raise ValueError("literal evidence needs only a nonempty quoted span")
        if self.extraction_method == "structured_field" and (not self.structured_field or self.quoted_span):
            raise ValueError("field evidence needs only a field path")
        if self.evidence_kind in {"system_inference", "unresolved"}:
            if self.verification_status != "not_independently_validated":
                raise ValueError("inferences/unknowns cannot be promoted by exact-source checks")
        elif self.extraction_method == "authored_inference":
            raise ValueError("authored inference cannot be a source fact")
        return self


class PatentCandidate(Contract):
    patent_id_raw: str
    patent_id_canonical: str
    source_id: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    retrieval_action_ids: list[str] = Field(min_length=1)
    scores: dict[str, float]
    association_status: Literal["retrieved_candidate", "disclosed_link"] = "retrieved_candidate"
    disclosure_evidence_id: str | None = None
    family_id: str | None = None
    family_source_id: str | None = None

    @model_validator(mode="after")
    def identity(self):
        if canonical_patent_id(self.patent_id_raw) != self.patent_id_canonical:
            raise ValueError("raw/canonical patent identity mismatch")
        if self.association_status == "disclosed_link" and not self.disclosure_evidence_id:
            raise ValueError("disclosed link requires independent disclosure evidence")
        if self.family_id and not self.family_source_id:
            raise ValueError("family identity requires provenance")
        return self


StopReason = Literal["budget_exhausted", "fixed_schedule_complete", "no_new_candidates_under_policy",
                     "policy_stop", "source_unavailable", "run_failure", "user_cancelled"]


class AcquisitionEvent(Contract):
    run_id: str
    query_id: str
    step_id: str
    policy_id: Literal["HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3"]
    action_type: Literal["technical_search", "feature_search", "company_search", "stop"]
    input_reference_ids: list[str]
    returned_candidate_ids: list[str]
    new_candidate_count: int = Field(ge=0)
    started_at: datetime
    ended_at: datetime
    elapsed_seconds: float = Field(ge=0)
    search_calls: int = Field(ge=0, le=1)
    returned_candidates: int = Field(ge=0)
    retry_count: int = Field(default=0, ge=0)
    errors: list[str] = Field(default_factory=list)
    remaining_budget_before: AcquisitionBudget
    remaining_budget_after: AcquisitionBudget
    stop_reason: StopReason | None = None
    configuration_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision_summary: str
    cost_basis: Literal["measured_local_resources"] = "measured_local_resources"
    paid_cost_usd: Literal[0] = 0


class DossierVersion(Contract):
    project_id: str
    dossier_id: str
    version: int = Field(ge=1)
    parent_version: int | None = Field(default=None, ge=1)
    query: DeviceQuery
    input_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    sources: list[SourcePayload]
    evidence: list[EvidenceItem]
    candidates: list[PatentCandidate]
    unresolved_items: list[str]
    next_information_requests: list[str]
    user_edits: dict[str, str] = Field(default_factory=dict)
    run_id: str
    created_at: datetime
    validation_scope: Literal["source_integrity_only"] = "source_integrity_only"

    @model_validator(mode="after")
    def references(self):
        if self.project_id != self.query.brief.project_id:
            raise ValueError("project mismatch")
        if (self.version == 1) != (self.parent_version is None):
            raise ValueError("initial version has no parent; later versions require one")
        if self.parent_version is not None and self.parent_version != self.version - 1:
            raise ValueError("parent must be the preceding dossier version")
        sources = {s.source.source_id:s for s in self.sources}
        evidence = {e.evidence_id:e for e in self.evidence}
        if len(sources) != len(self.sources) or len(evidence) != len(self.evidence):
            raise ValueError("duplicate source/evidence IDs")
        if self.query.selected_comparator_source_id not in sources:
            raise ValueError("missing comparator source")
        for e in self.evidence:
            if e.source_id not in sources:
                raise ValueError("dangling evidence source")
        for c in self.candidates:
            if c.source_id not in sources:
                raise ValueError("dangling patent source")
            if c.association_status == "disclosed_link":
                e=evidence.get(c.disclosure_evidence_id)
                if e is None or e.evidence_kind != "patent_disclosure":
                    raise ValueError("disclosure needs source-backed disclosure evidence, never evaluator gold")
        return self


class RunManifest(Contract):
    run_id: str
    track: Literal["healthtech"] = "healthtech"
    evidence_level: Literal["synthetic_engineering", "public_source_engineering"]
    code_commit: str
    input_hash: str
    policy_id: Literal["HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3"]
    configuration_hash: str
    data_revision: str
    corpus_hash: str
    expected_query_ids: list[str]
    completed_query_ids: list[str]
    failed_query_ids: list[str]
    budget: AcquisitionBudget
    actual_search_calls: int
    actual_returned_candidates: int
    elapsed_seconds: float
    provider_calls: Literal[0] = 0
    paid_cost_usd: Literal[0] = 0
    cost_accounting_version: Literal["ht-offline-v1"] = "ht-offline-v1"
    model: Literal["not_used"] = "not_used"
    stop_reason: StopReason
    artifacts: dict[str, str]
    limitations: list[str]
