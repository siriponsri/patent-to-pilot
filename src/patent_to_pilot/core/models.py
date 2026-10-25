"""Typed records shared by ingestion, retrieval, handoff, and future API layers."""

from __future__ import annotations

from datetime import date, datetime, timezone
from enum import StrEnum
from typing import Any, ClassVar, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Basis(StrEnum):
    SOURCE_ASSERTION = "source_assertion"
    STIPULATION = "stipulation"
    CONFIRMED_INTERPRETATION = "confirmed_interpretation"
    UNKNOWN = "unknown"


class ConfirmationState(StrEnum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


class EvidenceState(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    MISSING = "missing"
    UNKNOWN = "unknown"


class RecordBase(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)
    canonical_id_field: ClassVar[str | None] = None
    record_id: str = Field(min_length=1)
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utc_now)

class SourceRecord(RecordBase):
    canonical_id_field: ClassVar[str] = "source_id"
    source_id: str = Field(min_length=1)
    source_type: str = Field(min_length=1)
    uri: str = Field(min_length=1)
    version_label: str = Field(min_length=1)
    license_note: str = Field(min_length=1)
    locator: str | None = None
    sha256: str | None = None
    retrieved_at: datetime | None = None
    limits: list[str] = Field(default_factory=list)


class OrganizationCapability(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1)
    state: Literal["owned", "external", "unknown"]
    basis: Basis
    confirmation_state: ConfirmationState
    source_ref: str | None = None
    locator: str | None = None
    note: str | None = None

    @model_validator(mode="after")
    def source_assertion_has_locator(self) -> "OrganizationCapability":
        if self.basis is Basis.SOURCE_ASSERTION and (not self.source_ref or not self.locator):
            raise ValueError("source_assertion capability requires source_ref and locator")
        return self


class OrganizationProfile(RecordBase):
    canonical_id_field: ClassVar[str] = "profile_id"
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    organization_kind: str = Field(min_length=1)
    status: str = Field(min_length=1)
    organization_label: str = Field(min_length=1)
    public_source_context: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[OrganizationCapability] = Field(default_factory=list)
    stipulations: list[dict[str, Any]] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    source_refs: list[str] = Field(default_factory=list)
    policy_version: str | None = None

class ConstraintRecord(RecordBase):
    canonical_id_field: ClassVar[str] = "constraint_id"
    constraint_id: str = Field(min_length=1)
    organization_id: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    state: Literal["allowed", "prohibited", "conditional", "unknown"]
    statement: str = Field(min_length=1)
    basis: Basis
    effective_date: date | None = None
    confirmation_state: ConfirmationState
    source_refs: list[str] = Field(default_factory=list)
    supersedes: str | None = None


class EvidenceRecord(RecordBase):
    canonical_id_field: ClassVar[str] = "evidence_id"
    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    locator: str = Field(min_length=1)
    claim: str = Field(min_length=1)
    role: Literal["source_fact", "stipulation", "interpretation", "unknown"]
    state: EvidenceState
    quote: str | None = None
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)


class RouteRecord(RecordBase):
    canonical_id_field: ClassVar[str] = "route_id"
    route_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    status: Literal["draft", "candidate", "blocked_by_missing_evidence", "unknown", "ready_for_review"]
    evidence_ids: list[str] = Field(default_factory=list)
    constraint_ids: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class ChangeRecord(RecordBase):
    canonical_id_field: ClassVar[str] = "change_id"
    change_id: str = Field(min_length=1)
    entity_type: str = Field(min_length=1)
    entity_id: str = Field(min_length=1)
    before_version: int | None = Field(default=None, ge=1)
    after_version: int = Field(ge=1)
    affected_fields: list[str] = Field(default_factory=list)
    preserved_fields: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    source_refs: list[str] = Field(default_factory=list)


class FeedbackRecord(RecordBase):
    canonical_id_field: ClassVar[str] = "feedback_id"
    feedback_id: str = Field(min_length=1)
    scope: Literal["organization", "project", "route", "evidence"]
    target_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    confirmation_state: ConfirmationState
    source_refs: list[str] = Field(default_factory=list)
    effective_date: date | None = None


Record = SourceRecord | OrganizationProfile | ConstraintRecord | EvidenceRecord | RouteRecord | ChangeRecord | FeedbackRecord


class ProviderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prompt: str = Field(min_length=1)
    input_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class ProviderResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str
    model: str
    text: str
    usage: dict[str, int] = Field(default_factory=dict)
    mock: bool = False


def new_record_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"
