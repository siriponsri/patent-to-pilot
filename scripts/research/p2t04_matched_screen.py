"""Offline per-query adapter for P2-T04.

The benchmark entry point supplies the frozen seed, bounds, assessor, and BM25 backend.
The separate evaluator consumes the finished rankings.
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass, replace

from patent_to_pilot.workbench import relation_search as R
from patent_to_pilot.workbench.trace_slice import SourceEvidence

_TOKEN = re.compile(r"[a-z0-9]+", re.IGNORECASE | re.ASCII)
_LINE = re.compile(r"[^\r\n]+")


@dataclass(frozen=True)
class ScreenLimits:
    seed: int
    seed_reads: int
    source_chars: int
    feedback_terms: int
    fetch: int
    returned: int
    original_depth: int
    final: int

    def __post_init__(self):
        if (
            any(type(n) is not int for n in asdict(self).values())
            or not (1 <= self.seed_reads <= self.seed)
            or min(self.source_chars, self.feedback_terms, self.returned, self.final) < 1
            or not (0 <= self.original_depth <= self.fetch - self.returned)
            or self.final > self.seed + self.returned
        ):
            raise ValueError("invalid retrieval, source-read, or rerank bounds")


@dataclass(frozen=True)
class SourceUnit:
    """Pinned version of the source text used by the retrieval backend."""

    candidate_id: str
    source_id: str
    version_id: str
    text: str


@dataclass(frozen=True)
class _Passage:
    candidate_id: str
    text: str


class _Evidence(R.EvidenceRegistry):
    def __init__(self):
        super().__init__()
        self.locators = {}
        self._inspected = {}

    def inspect(self, ids, read_source, chars):
        for candidate_id in ids:
            if candidate_id in self._inspected:
                continue
            unit = read_source(candidate_id)
            if unit.candidate_id != candidate_id or not unit.source_id or not unit.version_id:
                raise ValueError("source provenance does not match the requested candidate")
            content_sha256 = hashlib.sha256(unit.text.encode("utf-8")).hexdigest()
            self._inspected[candidate_id] = (unit.source_id, unit.version_id, content_sha256, unit.text[:chars])
        return tuple(_Passage(candidate_id, self._inspected[candidate_id][3]) for candidate_id in ids)

    def span(self, candidate_id, start, end):
        source_id, version_id, content_sha256, text = self._inspected[candidate_id]
        if not (0 <= start < end <= len(text)):
            raise ValueError("source evidence lies outside the inspected text")
        locator = {
            "candidate_id": candidate_id,
            "source_id": source_id,
            "version_id": version_id,
            "content_sha256": content_sha256,
            "start": start,
            "end": end,
            "quote": text[start:end],
        }
        evidence_id = f"{candidate_id}#{content_sha256}[{start}:{end}]"
        self.locators[evidence_id] = locator
        return self.add_evidence(SourceEvidence(evidence_id, candidate_id, start, end, locator["quote"]))


def _source_term(evidence, passage, start, end):
    span = evidence.span(passage.candidate_id, start, end)
    return R.QueryTerm(span.quote, "source_copy", span.evidence_id)


def _frequency_feedback(passages, evidence, limit):
    counts, first = Counter(), {}
    for passage in passages:
        for match in _TOKEN.finditer(passage.text):
            token = match[0].lower()
            counts[token] += 1
            first.setdefault(token, (passage, match.start(), match.end()))
    terms = sorted(counts, key=lambda token: (-counts[token], token))[:limit]
    return tuple(_source_term(evidence, *first[token]) for token in terms)


def _extractive_feedback(query_text, passages, evidence, limit):
    query_tokens = set(_TOKEN.findall(query_text.lower()))
    best, best_overlap = None, 0
    for passage in passages:
        for line in _LINE.finditer(passage.text):
            tokens = list(_TOKEN.finditer(passage.text, line.start(), line.end()))[:limit]
            overlap = len(query_tokens.intersection(match[0].lower() for match in tokens))
            if overlap > best_overlap:
                best_overlap = overlap
                best = (passage, tokens[0].start(), tokens[-1].end())
    return (_source_term(evidence, *best),) if best else ()


def _rank_seed_or_control(rerank, request, pool, final):
    scores = dict(rerank(request, tuple(pool)) or {})
    for candidate_id, score in scores.items():
        if (
            candidate_id not in pool
            or isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not math.isfinite(score)
        ):
            raise ValueError("reranker must return finite scores for candidates in the merged pool")
    return sorted(pool, key=lambda candidate_id: (candidate_id not in scores, -scores.get(candidate_id, 0)))[:final]


def run_matched_query(
    *,
    requirements: R.QueryRequirements,
    seed_ids: Sequence[str],
    limits: ScreenLimits,
    eligibility: R.EligibilityMask,
    read_source: Callable[[str], SourceUnit],
    assess: Callable[[R.QueryRequirements, tuple[_Passage, ...], Callable], Iterable[R.RelationState]],
    search: Callable[[R.ExpansionQuery, int, R.EligibilityMask], Iterable[tuple[str, float]]],
    rerank: Callable[[R.RerankRequest, tuple[str, ...]], dict[str, float]],
) -> dict:
    """Compare matched actions over a single shared eligible seed and one pinned index.

    The assessor receives only inspected source prefixes and a function to record exact
    spans as `span(candidate_id, start, end)`. Search ranks globally with the supplied
    mask and respects the fetch bound. Each arm has one possible additional search and
    submits its final pool to the same original-query reranker.
    """
    seed = list(seed_ids)
    if len(seed) > limits.seed or len(set(seed)) != len(seed):
        raise ValueError("the shared seed exceeds its bound or contains duplicate candidates")
    if any(eligibility.reason(candidate_id) for candidate_id in seed):
        raise R.IneligibleCandidate("the shared seed contains an ineligible candidate", R.IneligibleCandidate.code)
    request = R.RerankRequest.from_requirements(requirements)
    evidence = _Evidence()
    inspected_seed = seed[:limits.seed_reads]
    passages = evidence.inspect(inspected_seed, read_source, limits.source_chars)

    def assess_passages(inspected):
        allowed = {passage.candidate_id for passage in inspected}

        def bind(candidate_id, start, end):
            if candidate_id not in allowed:
                raise ValueError("assessor cited a candidate outside its inspected sources")
            return evidence.span(candidate_id, start, end)

        states = tuple(assess(requirements, inspected, bind))
        for state in states:
            reference_id = state.reference_evidence_id
            if state.status == "unresolved" and state.actionable and not reference_id:
                raise ValueError("an actionable unresolved relation must cite an exact source span")
            evidence_ids = list(state.evidence_ids)
            if reference_id:
                evidence_ids.append(reference_id)
            for evidence_id in evidence_ids:
                if evidence_id not in evidence.locators or evidence.locators[evidence_id]["candidate_id"] not in allowed:
                    raise ValueError("relation uses evidence outside the inspected sources")
            if reference_id and evidence.locators[reference_id]["candidate_id"] != state.from_id:
                raise ValueError("a reference must come from its relation's source candidate")
        return states

    before = assess_passages(passages)

    def checked_search(query, limit, mask):
        rows = list(search(query, limit, mask))
        if len(rows) > limit or any(not isinstance(candidate_id, str) or not candidate_id for candidate_id, _ in rows):
            raise ValueError("search output exceeds its bound or contains an invalid candidate id")
        return rows

    post_search_reads = []

    def recheck(pool):
        post_search_reads.extend(pool[len(seed):])
        inspected = evidence.inspect(inspected_seed + post_search_reads, read_source, limits.source_chars)
        return assess_passages(inspected)

    budget = R.ActionBudget(2)
    budget.consume("shared_seed")
    targeted = R.relation_search_step(
        requirements=requirements, relations=before, pool_before=seed, search=checked_search,
        assess=recheck, rerank=rerank, budget=budget, eligibility=eligibility, evidence=evidence,
        policy=R.POLICY_V1, result_limit=limits.returned, fetch_limit=limits.fetch, final_k=limits.final,
        action_id=f"{requirements.query_id}:relation_search",
    )
    seed_final = _rank_seed_or_control(rerank, request, seed, limits.final)
    arms = {
        "seed_only": {"outcome": "seed_only", "search_calls": 0, "new_ids": [], "final_ids": seed_final},
        "unresolved_relation": {
            "outcome": targeted["outcome"],
            "search_calls": targeted["search_calls"],
            "new_ids": targeted["candidate_delta"]["new_ids"] if targeted["candidate_delta"] else [],
            "final_ids": targeted["rerank"]["final_ids"] if targeted["rerank"] else seed_final,
            "post_search_reads": post_search_reads,
            "policy_record": targeted,
        },
    }

    def control(name, terms, *, offset=0, skip="no_query_material", relation_key=None, extra=None):
        if not terms:
            arms[name] = {"outcome": skip, "search_calls": 0, "new_ids": [], "final_ids": seed_final}
            return
        query = R.ExpansionQuery(relation_key or name, terms)
        rows = checked_search(query, limits.fetch, eligibility)
        unique = list(dict.fromkeys(candidate_id for candidate_id, _ in rows))
        eligible_ids = [candidate_id for candidate_id in unique if not eligibility.reason(candidate_id)]
        returned = eligible_ids[offset:offset + limits.returned]
        new_ids = [candidate_id for candidate_id in returned if candidate_id not in seed]
        pool = seed + new_ids
        arms[name] = {
            "outcome": "searched", "search_calls": 1, "query": query.as_record(),
            "eligible_returned": returned, "new_ids": new_ids,
            "final_ids": _rank_seed_or_control(rerank, request, pool, limits.final),
            "eligible_offset": offset, **(extra or {}),
        }

    original = (R.QueryTerm(requirements.text, "original_query"),) if _TOKEN.search(requirements.text) else ()
    control("original_query_deeper", original, offset=limits.original_depth)
    first = next(iter(requirements.ordered()), None)
    static = (R.QueryTerm(first.text, "original_requirement"),) if first and _TOKEN.search(first.text) else ()
    control("static_requirement", static, extra={"requirement_id": first.requirement_id} if first else None)
    control("generic_feedback", _frequency_feedback(passages, evidence, limits.feedback_terms))
    control("extractive_feedback", _extractive_feedback(requirements.text, passages, evidence, limits.feedback_terms))

    states = {state.relation_key: state for state in before}
    selected = states.get(targeted["selection"]["selected_relation_key"])
    donor = None
    if selected:
        selected_text = _TOKEN.findall(selected.reference_text.lower())
        considered = [states[row["relation_key"]] for row in targeted["selection"]["considered"]]
        donor = next((
            state for state in considered
            if state.requirement_id != selected.requirement_id
            and _TOKEN.findall(state.reference_text.lower()) != selected_text
        ), None)
    if selected and donor:
        shuffled = replace(
            selected, reference_text=donor.reference_text, reference_evidence_id=donor.reference_evidence_id,
        )
        query = R.build_query(R.POLICY_V1, shuffled, requirements, (), evidence)
        control("shuffled_binding", query.terms, relation_key=selected.relation_key,
                extra={"donor_relation_key": donor.relation_key})
    else:
        control("shuffled_binding", (), skip="no_distinct_binding")

    return {
        "requirements_sha256": requirements.sha256(),
        "eligibility_sha256": eligibility.fingerprint(),
        "limits": asdict(limits),
        "shared_seed": seed,
        "inspected_seed": inspected_seed,
        "evidence": evidence.locators,
        "arms": arms,
    }
