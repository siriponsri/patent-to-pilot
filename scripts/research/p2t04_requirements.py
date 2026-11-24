"""Proposed lexical assessor for the P2-T04 offline screen.

Claim bounds must come from the caller's original query representation. English
cue clauses and local token co-occurrence are reproducible retrieval signals.
They do not establish a logical relation, semantic entailment or relevance.
"""
from __future__ import annotations

import re
from collections.abc import Callable, Iterator, Sequence
from dataclasses import asdict, dataclass
from typing import Protocol

from patent_to_pilot.workbench.relation_search import QueryRequirements, RelationState, Requirement
from patent_to_pilot.workbench.trace_slice import STOPWORDS, SourceEvidence


_CUE = re.compile(r"\b(?:wherein|when|in[ \t]+response[ \t]+to)\b", re.IGNORECASE)
_BOUNDARY = re.compile(r"[;!?\r\n]|(?<!\d)\.|\.(?!\d)")
_TOKEN = re.compile(r"\b[A-Za-z0-9]+\b")
_FILLER = STOPWORDS | frozenset("be been being in response said that to was were when wherein".split())
_CONDITION = "condition:"


@dataclass(frozen=True)
class AssessorLimits:
    claim_chars: int
    requirements: int
    anchor_terms: int
    source_passages: int
    source_chars: int
    local_tokens: int

    def __post_init__(self) -> None:
        if any(type(n) is not int or n < 1 for n in asdict(self).values()):
            raise ValueError("assessor bounds must be positive integers")
        if not 2 <= self.anchor_terms <= self.local_tokens:
            raise ValueError("the local window must accommodate at least two anchors")


class InspectedPassage(Protocol):
    @property
    def candidate_id(self) -> str: ...

    @property
    def text(self) -> str: ...


def _clauses(text: str) -> Iterator[tuple[int, int, bool]]:
    start = 0
    for boundary in _BOUNDARY.finditer(text):
        yield start, boundary.start(), True
        start = boundary.end()
    yield start, len(text), False


def _terms(text: str) -> tuple[str, ...]:
    words = (match[0].lower() for match in _TOKEN.finditer(text))
    return tuple(dict.fromkeys(word for word in words if word not in _FILLER))


def extract_requirements(
    query_id: str,
    query_text: str,
    *,
    claim_start: int,
    claim_end: int,
    limits: AssessorLimits,
) -> QueryRequirements:
    """Take ordered cue clauses with at least two terms as exact query spans.

    An empty claim range represents unavailable claim text. A query with no
    qualifying cue still has an exact context span for the static control.
    """
    if not query_text.strip() or not 0 <= claim_start <= claim_end <= len(query_text):
        raise ValueError("a nonblank query and valid claim bounds are required")
    scan_end = min(claim_end, claim_start + limits.claim_chars)
    claim = query_text[claim_start:scan_end]
    found = []
    for clause_start, clause_end, complete in _clauses(claim):
        cues = list(_CUE.finditer(claim, clause_start, clause_end))
        for i, cue in enumerate(cues):
            next_cue = cues[i + 1] if i + 1 < len(cues) else None
            if next_cue is None and not complete and scan_end < claim_end:
                continue
            end = next_cue.start() if next_cue else clause_end
            phrase = claim[cue.start():end].rstrip()
            if len(_terms(phrase[cue.end() - cue.start():])) < 2:
                continue
            start = claim_start + cue.start()
            found.append(Requirement(f"{_CONDITION}{start}", start, start + len(phrase), phrase))
            if len(found) == limits.requirements:
                return QueryRequirements(query_id, query_text, tuple(found))
    if not found:
        if claim.strip():
            start, context = claim_start, claim
        else:
            start = len(query_text) - len(query_text.lstrip())
            context = query_text[start:start + limits.claim_chars]
        found.append(Requirement("query-context", start, start + len(context), context))
    return QueryRequirements(query_id, query_text, tuple(found))


def _source_clauses(text: str) -> Iterator[list[tuple[str, int, int]]]:
    for start, end, _ in _clauses(text):
        # The inspected input can be a truncated prefix. An alphanumeric run
        # at the very end has no verified right token boundary.
        yield [
            (m[0].lower(), m.start(), m.end())
            for m in _TOKEN.finditer(text, start, end) if m.end() < len(text)
        ]


def _support_span(
    tokens: list[tuple[str, int, int]], anchors: set[str], window: int,
) -> tuple[int, int] | None:
    last = {}
    for i, (word, _, end) in enumerate(tokens):
        if word in anchors:
            last[word] = i
            if len(last) == len(anchors):
                start = min(last.values())
                if i - start < window:
                    return tokens[start][1], end
    return None


def _partial_span(
    tokens: list[tuple[str, int, int]], anchors: set[str], requirement_terms: set[str], window: int,
) -> tuple[int, int] | None:
    prior = None
    for i, (word, start, end) in enumerate(tokens):
        if word in _FILLER:
            continue
        if prior is not None:
            prior_i, prior_word, prior_start = prior
            related = (
                (word in anchors and prior_word not in requirement_terms)
                or (prior_word in anchors and word not in requirement_terms)
            )
            if related and i - prior_i < window:
                return prior_start, end
        prior = (i, word, start)
    return None


@dataclass(frozen=True)
class LexicalAssessor:
    """Score ordered bounded prefixes using only observed lexical material.

    All chosen anchors in a local clause window produce a coverage signal.
    Otherwise the first adjacent pair of informative seed words containing a
    chosen anchor and one term absent from the requirement supplies an exact
    source quote. Without either signal the assessor emits no relation state.
    """

    limits: AssessorLimits

    def __call__(
        self,
        requirements: QueryRequirements,
        inspected: Sequence[InspectedPassage],
        bind: Callable[[str, int, int], SourceEvidence],
    ) -> tuple[RelationState, ...]:
        limits = self.limits
        sources = [
            (p.candidate_id, tuple(_source_clauses(p.text[:limits.source_chars])))
            for p in inspected[:limits.source_passages]
        ]
        states = []
        for req in requirements.ordered()[:limits.requirements]:
            if len(req.text) > limits.claim_chars:
                raise ValueError("requirement exceeds the assessor's claim text bound")
            cue = _CUE.match(req.text)
            if not req.requirement_id.startswith(_CONDITION) or cue is None:
                continue
            terms = _terms(req.text[cue.end():])
            anchors = terms[:limits.anchor_terms]
            if len(anchors) < 2:
                continue
            anchor_set, term_set = set(anchors), set(terms)
            supported, partial = None, None
            for candidate_id, clauses in sources:
                for clause in clauses:
                    full = _support_span(clause, anchor_set, limits.local_tokens)
                    if full:
                        supported = (candidate_id, *full)
                        break
                    if partial is None:
                        hit = _partial_span(clause, anchor_set, term_set, limits.local_tokens)
                        if hit:
                            partial = (candidate_id, *hit)
                if supported:
                    break
            key = f"lexical-{req.requirement_id}"
            if supported:
                evidence = bind(*supported)
                states.append(RelationState(
                    key, req.requirement_id, "lexical_condition", "supported",
                    from_id=supported[0], anchor_terms=anchors, evidence_ids=(evidence.evidence_id,),
                    actionable=False, note="Local co-occurrence of the selected anchors.",
                ))
            elif partial:
                evidence = bind(*partial)
                states.append(RelationState(
                    key, req.requirement_id, "lexical_condition", "unresolved",
                    from_id=partial[0], reference_text=evidence.quote,
                    reference_evidence_id=evidence.evidence_id, anchor_terms=anchors,
                    note="No local coverage; an observed source phrase supplies search material.",
                ))
        return tuple(states)
