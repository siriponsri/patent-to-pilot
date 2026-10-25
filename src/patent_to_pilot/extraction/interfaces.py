"""Role-aware extraction interfaces with a deterministic lexical implementation."""

from __future__ import annotations

from typing import Protocol

from pydantic import BaseModel, Field

from patent_to_pilot.core.models import EvidenceState
from patent_to_pilot.ingestion.pls import PatentDocument


class ExtractionRequest(BaseModel):
    document_id: str
    role: str = Field(min_length=1)
    query: str = Field(min_length=1)
    component: str = "title"


class ExtractedFact(BaseModel):
    document_id: str
    role: str
    component: str
    query: str
    state: EvidenceState
    value: str | None = None
    char_start: int | None = None
    char_end: int | None = None
    source_locator: str
    method: str
    model_called: bool = False


class Extractor(Protocol):
    def extract(self, request: ExtractionRequest, document: PatentDocument) -> ExtractedFact: ...


class LexicalExtractor:
    allowed_components = {"title", "abstract", "claims", "description", "cpc", "ipc", "labels"}

    @staticmethod
    def _original_span(text: str, query: str) -> tuple[int, int] | None:
        folded_parts: list[str] = []
        folded_to_original: list[int] = []
        for original_index, character in enumerate(text):
            folded = character.casefold()
            folded_parts.append(folded)
            folded_to_original.extend([original_index] * len(folded))
        folded_text = "".join(folded_parts)
        folded_query = query.casefold()
        folded_start = folded_text.find(folded_query)
        if folded_start < 0:
            return None
        folded_end = folded_start + len(folded_query)
        start = folded_to_original[folded_start]
        end = folded_to_original[folded_end - 1] + 1
        if text[start:end].casefold() != folded_query:
            return None
        return start, end

    def extract(self, request: ExtractionRequest, document: PatentDocument) -> ExtractedFact:
        if request.document_id != document.document_id: raise ValueError("request/document ID mismatch")
        if request.component not in self.allowed_components: raise ValueError(f"unsupported component: {request.component}")
        text = getattr(document, request.component)
        span = self._original_span(text, request.query)
        if span is None:
            return ExtractedFact(document_id=document.document_id, role=request.role, component=request.component, query=request.query, state=EvidenceState.UNKNOWN, source_locator=document.source_locator, method="lexical_component_window", model_called=False)
        start, end = span
        return ExtractedFact(document_id=document.document_id, role=request.role, component=request.component, query=request.query, state=EvidenceState.SUPPORTED, value=text[start:end], char_start=start, char_end=end, source_locator=document.source_locator, method="lexical_component_window", model_called=False)


class ModelExtractionAdapter:
    def __init__(self, provider: object) -> None: self.provider = provider

    def extract(self, request: ExtractionRequest, document: PatentDocument) -> ExtractedFact:
        raise RuntimeError("model extraction is not enabled in the bounded G08 slice")
