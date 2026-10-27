"""Closed no-code discovery contracts. Synthetic claims never become real facts."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ProjectBrief(Closed):
    project_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    version: int = Field(ge=1)
    objective: str = Field(min_length=1, max_length=4000)
    audience: Literal["entrepreneur", "investor", "researcher"]
    data_class: Literal["synthetic", "public", "private"]
    language: Literal["en", "th"] = "en"
    theme: Literal["formal-light", "formal-dark", "kmitl-inspired", "ict-inspired"] = "formal-light"


class EvidenceCard(Closed):
    evidence_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_version: int = Field(ge=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    locator: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    basis: Literal["source_assertion", "stipulation", "interpretation", "unknown"]
    support: Literal["supported", "contradicted", "missing", "unknown"]
    synthetic: bool
    limitation: str = Field(min_length=1)


class ReviewDecision(Closed):
    decision_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    expected_version: int = Field(ge=1)
    scope: Literal["critical_assumption", "outbound_disclosure", "release_export"]
    decision: Literal["confirm", "reject", "request_revision"]
    evidence_ids: list[str] = Field(min_length=1)
    reason: str = Field(min_length=1)


class JobStatus(Closed):
    job_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    state: Literal["queued", "running", "ready_for_review", "blocked", "failed", "cancelled"]
    reason: str | None = None
    affected_routes: list[str] = Field(default_factory=list)
    preserved_routes: list[str] = Field(default_factory=list)
    provider_calls: int = Field(default=0, ge=0)
    cost_status: Literal["not_run", "known", "unknown_pending"] = "not_run"

    @model_validator(mode="after")
    def consistent(self):
        if set(self.affected_routes) & set(self.preserved_routes):
            raise ValueError("affected and preserved routes overlap")
        if self.state in {"blocked", "failed"} and not self.reason:
            raise ValueError("blocked/failed jobs require an actionable reason")
        if self.cost_status == "not_run" and self.provider_calls:
            raise ValueError("dispatched calls cannot be reported not_run")
        return self
