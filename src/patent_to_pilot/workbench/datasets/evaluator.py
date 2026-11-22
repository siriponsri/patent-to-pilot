"""Evaluator-side label reader (stdlib only). Runtime code must not import this module.

Holds qrels, evidence spans/text, gold verdicts/reasoning and gold citations. Missing citation
identifiers stay missing (``None`` or the native empty value); nothing is fabricated or repaired.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .registry import get_dataset, load_registry


@dataclass(frozen=True)
class DapfamRelation:
    query_id: str
    relevant_id: str
    relevance_score: float
    domain_rel: str | None


@dataclass(frozen=True)
class GazetteEvidence:
    query_id: str
    corpus_id: str
    score: int
    start: int
    end: int
    evidence_text: str
    passage_text: str | None


@dataclass(frozen=True)
class NitiCitation:
    case_id: str
    sub_index: int
    law: str | None
    section: str | None
    version_uri: str | None
    valid_from: str | None
    valid_to: str | None
    current_uri: str | None

    @property
    def resolved(self) -> bool:
        return self.version_uri not in (None, "")


@dataclass(frozen=True)
class NitiSubQuestionLabel:
    case_id: str
    sub_index: int
    question_type: str | None
    verdict: object
    reasoning: str | None
    citations: tuple


def dapfam_relations(rows: Iterable[dict], *, positive_only: bool = True) -> list[DapfamRelation]:
    out = []
    for r in rows:
        score = float(r["relevance_score"])
        if positive_only and score <= 0:
            continue
        out.append(DapfamRelation(str(r["query_id"]), str(r["relevant_id"]), score, r.get("domain_rel")))
    return out


def gazette_evidence(rows: Iterable[dict]) -> list[GazetteEvidence]:
    return [GazetteEvidence(str(r["query-id"]), str(r["corpus-id"]), int(r["score"]), int(r["evidence_start_char"]),
                            int(r["evidence_end_char"]), r["evidence_text"], r.get("passage_text")) for r in rows]


def gazette_document_qrels(evidence: Iterable[GazetteEvidence]) -> dict[str, set[str]]:
    """Document-level qrels deduplicated by (query_id, corpus_id); span rows stay separate elsewhere."""
    out: dict[str, set[str]] = {}
    for e in evidence:
        out.setdefault(e.query_id, set()).add(e.corpus_id)
    return out


def check_gazette_span(evidence: GazetteEvidence, corpus_text: str) -> bool:
    """Native invariant: corpus[corpus-id].text[start:end] == evidence_text (code points)."""
    return 0 <= evidence.start <= evidence.end <= len(corpus_text) and corpus_text[evidence.start:evidence.end] == evidence.evidence_text


def nitibench_labels(case_row: dict, registry: dict | None = None) -> list[NitiSubQuestionLabel]:
    fm = get_dataset("VISAI-AI/nitibench-plus", registry or load_registry())["field_map"]
    case_id = case_row.get(fm["case_id"])
    labels = []
    for i, sub in enumerate(case_row.get(fm["sub_questions"]) or []):
        cites = tuple(
            NitiCitation(case_id, i, c.get(fm["law"]), c.get(fm["section"]), c.get("version_uri"),
                         c.get("valid_from"), c.get("valid_to"), c.get("current_uri"))
            for c in (sub.get(fm["citations"]) or [])
        )
        labels.append(NitiSubQuestionLabel(case_id, i, sub.get(fm["question_type"]), sub.get(fm["verdict"]),
                                           sub.get(fm["reasoning"]), cites))
    return labels
