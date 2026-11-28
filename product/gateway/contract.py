"""Versioned wire models and provider output models."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints

Task = Literal["A1", "A2", "A3", "A4"]
Language = Literal["th", "en"]
Identifier = Annotated[str, StringConstraints(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:*\-]+$")]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=4000)]
Question = Literal["market_window", "competition", "thai_status", "next_checks"]
Audience = Literal["fto_evaluator", "dip", "thai_fda"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DossierSelection(StrictModel):
    dossier_id: Identifier
    snapshot: date
    horizon: Literal[12, 24]
    language: Language


class SummaryRequest(DossierSelection):
    task: Literal["A1"]


class LetterRequest(DossierSelection):
    task: Literal["A2"]
    audience: Audience = "fto_evaluator"


class QuestionRequest(DossierSelection):
    task: Literal["A3"]
    question_id: Question


class ReadingRequest(DossierSelection):
    task: Literal["A4"]
    patent_publication: Identifier
    claim_number: Annotated[int, Field(strict=True, ge=1, le=9999)]


TaskRequest = Annotated[
    SummaryRequest | LetterRequest | QuestionRequest | ReadingRequest, Field(discriminator="task")
]


class Proposition(StrictModel):
    text: Text
    claim_ids: Annotated[list[Identifier], Field(min_length=1, max_length=16)]


class Draft(StrictModel):
    items: Annotated[list[Proposition], Field(max_length=16)]


class SourceReference(StrictModel):
    source_id: Identifier
    version: str
    sha256: str | None
    locator: str
    url: HttpUrl | None


class Citation(StrictModel):
    claim_id: Identifier
    sources: list[SourceReference]


class Forecast(StrictModel):
    endpoint: Literal["first_final_us_anda"] = "first_final_us_anda"
    horizon: Literal[12, 24]
    m3_probability: Annotated[float, Field(ge=0, le=1)]
    claim_id: Identifier


class ClaimElement(StrictModel):
    item_index: Annotated[int, Field(ge=0)]
    start: Annotated[int, Field(ge=0)]
    end: Annotated[int, Field(gt=0)]


class ClaimReading(StrictModel):
    publication: Identifier
    claim_number: int
    source: SourceReference
    original_text: str
    parent_claim_numbers: list[int]
    elements: list[ClaimElement]


class Provenance(StrictModel):
    provider: str
    model: str
    prompt_version: str
    generated_at: datetime


class Accepted(StrictModel):
    state: Literal["ok"] = "ok"
    selection: DossierSelection
    task: Task
    label: Literal["AI draft", "AI-assisted reading; a patent professional must verify"]
    disclaimer: str
    items: list[Proposition]
    citations: list[Citation]
    provenance: Provenance
    forecast: Forecast | None = None
    reading: ClaimReading | None = None


Reason = Literal[
    "invalid_request", "identity_required", "cross_origin", "dossier_not_found", "claim_text_missing",
    "evidence_missing", "unsupported_evidence", "invalid_output", "duplicate_request", "request_in_progress",
    "daily_limit", "attempt_limit", "budget_limit", "envelope_expired", "unknown_billing",
    "route_or_price_changed", "provider_unqualified", "provider_unavailable", "ledger_unavailable",
]


class Problem(StrictModel):
    reason: Reason
    message: str
    next_step: str | None = None


class Abstained(Problem):
    state: Literal["abstained"] = "abstained"


class Rejected(Problem):
    state: Literal["rejected"] = "rejected"


class Unavailable(Problem):
    state: Literal["unavailable"] = "unavailable"


TaskResponse = Annotated[Accepted | Abstained | Rejected | Unavailable, Field(discriminator="state")]
