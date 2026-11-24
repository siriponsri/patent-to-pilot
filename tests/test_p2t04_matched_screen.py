"""Authored fixtures for the offline P2-T04 adapter. No research data."""
import hashlib
from dataclasses import replace

import pytest

from patent_to_pilot.workbench import relation_search as R
from scripts.research.p2t04_matched_screen import ScreenLimits, SourceUnit, run_matched_query

QUERY = R.QueryRequirements.bind(
    "synthetic-q", "The sensor closes the valve. The timer controls the fan.",
    [("sensor", "The sensor closes the valve"), ("timer", "The timer controls the fan")],
)
LIMITS = ScreenLimits(seed=3, seed_reads=2, source_chars=100, feedback_terms=2, fetch=6, returned=2,
                      original_depth=2, final=3)
TEXTS = {
    "a": "Valve housing. A sensor sits in the housing.",
    "b": "Fan shaft. A timer sits in the housing.",
    "c": "Other item outside the seed inspection cap.",
    "new": "Sensor closes the valve.",
    "deep": "Original-query second-window candidate.",
    "future": "Ineligible candidate.",
}
MASK = R.EligibilityMask("synthetic-date-mask", date_cutoff="2026-01-01", dates={
    **{candidate_id: "2020-01-01" for candidate_id in TEXTS}, "future": "2026-01-01",
})


def test_matched_arms_use_exact_sources_common_caps_and_original_query():
    searches, reads, reranks = [], [], []

    def read_source(candidate_id):
        reads.append(candidate_id)
        return SourceUnit(candidate_id, f"doc:{candidate_id}", "v1", TEXTS[candidate_id])

    def assess(requirements, passages, span):
        assert requirements == QUERY
        inspected = {passage.candidate_id for passage in passages}
        valve = span("a", 0, 13)
        fan = span("b", 0, 9)
        if "new" in inspected:
            recovered = span("new", 0, 23)
            status, citations = "supported", (recovered.evidence_id,)
        else:
            status, citations = "unresolved", (valve.evidence_id,)
        return [
            R.RelationState("binding:a", "sensor", "binding", status, "a", valve.quote, valve.evidence_id,
                            ("sensor",), citations),
            R.RelationState("binding:b", "timer", "binding", "unresolved", "b", fan.quote, fan.evidence_id,
                            ("timer",), (fan.evidence_id,)),
        ]

    def search(query, limit, eligibility):
        searches.append((query, limit, eligibility))
        return [("future", 9), ("a", 8), ("a", 8), ("b", 7), ("deep", 6), ("new", 5)] if (
            query.relation_key == "original_query_deeper"
        ) else [("future", 9), ("new", 5), ("a", 4)]

    def rerank(request, pool):
        reranks.append((request, pool))
        return {candidate_id: 2 if candidate_id == "new" else 1 for candidate_id in pool}

    record = run_matched_query(
        requirements=QUERY, seed_ids=["a", "b", "c"], limits=LIMITS, eligibility=MASK,
        read_source=read_source, assess=assess, search=search, rerank=rerank,
    )
    arms = record["arms"]
    target = arms["unresolved_relation"]
    assert target["policy_record"]["policy"]["sha256"] == R.POLICY_V1_SHA256
    assert target["policy_record"]["coverage"]["selected_after"] == "supported"
    assert target["policy_record"]["query"]["terms"][0]["text"] == "Valve housing"
    assert target["new_ids"] == ["new"] and target["final_ids"] == ["new", "a", "b"]
    assert target["post_search_reads"] == ["new"]
    assert arms["original_query_deeper"]["eligible_returned"] == ["deep", "new"]
    assert arms["static_requirement"]["query"]["terms"][0]["text"] == QUERY.get("sensor").text
    assert arms["extractive_feedback"]["query"]["terms"][0]["text"] == "Valve housing"
    assert arms["shuffled_binding"]["donor_relation_key"] == "binding:b"
    assert [term["text"] for term in arms["shuffled_binding"]["query"]["terms"]] == ["Fan shaft", "sensor"]
    assert len(arms["generic_feedback"]["query"]["terms"]) == LIMITS.feedback_terms
    assert sum(arm["search_calls"] for arm in arms.values()) == len(searches) == 6
    assert all(limit == LIMITS.fetch and eligibility is MASK for _, limit, eligibility in searches)
    assert reads == ["a", "b", "new"]
    assert all(request == R.RerankRequest.from_requirements(QUERY) and "future" not in pool
               for request, pool in reranks)
    assert all(len(arm["final_ids"]) <= LIMITS.final and "future" not in arm["final_ids"] for arm in arms.values())
    for locator in record["evidence"].values():
        text = TEXTS[locator["candidate_id"]]
        assert locator["quote"] == text[locator["start"]:locator["end"]]
        assert locator["content_sha256"] == hashlib.sha256(text.encode()).hexdigest()
        assert locator["source_id"] == f"doc:{locator['candidate_id']}" and locator["version_id"] == "v1"


def test_skipped_arms_keep_same_seed_ranking_and_do_not_search():
    calls = []
    record = run_matched_query(
        requirements=QUERY, seed_ids=["a"], limits=LIMITS, eligibility=MASK,
        read_source=lambda candidate_id: SourceUnit(candidate_id, "doc:a", "v1", ""),
        assess=lambda *_: [], search=lambda query, *_: calls.append(query.relation_key) or [],
        rerank=lambda _request, pool: {candidate_id: 1 for candidate_id in pool},
    )
    arms = record["arms"]
    assert arms["unresolved_relation"]["outcome"] == "no_unresolved_relation"
    assert arms["shuffled_binding"]["outcome"] == "no_distinct_binding"
    assert arms["unresolved_relation"]["final_ids"] == arms["shuffled_binding"]["final_ids"] == ["a"]
    assert calls == ["original_query_deeper", "static_requirement"]


@pytest.mark.parametrize(
    ("seed", "assessor", "error", "message"),
    [
        (["future"], lambda *_: [], R.IneligibleCandidate, "ineligible"),
        (["a"], lambda _query, _passages, bind: bind("b", 0, 1), ValueError, "outside its inspected"),
        (["a"], lambda _query, _passages, bind: bind("a", 0, 6), ValueError, "outside the inspected text"),
        (["a"], lambda *_: [R.RelationState("r", "sensor", "binding", "unresolved", "a",
                                          anchor_terms=("sensor",))], ValueError, "exact source span"),
    ],
)
def test_invalid_seed_or_relation_fails_before_any_search(seed, assessor, error, message):
    with pytest.raises(error, match=message):
        run_matched_query(
            requirements=QUERY, seed_ids=seed, limits=replace(LIMITS, source_chars=5), eligibility=MASK,
            read_source=lambda candidate_id: SourceUnit(candidate_id, "doc:a", "v1", TEXTS[candidate_id]),
            assess=assessor, search=lambda *_: pytest.fail("search received invalid inputs"),
            rerank=lambda *_: pytest.fail("rerank received invalid inputs"),
        )
