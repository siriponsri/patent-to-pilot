"""Authored source snippets for the proposed P2-T04 assessor."""
import hashlib
from dataclasses import replace

import pytest

from patent_to_pilot.workbench.relation_search import EligibilityMask
from scripts.research.p2t04_matched_screen import ScreenLimits, SourceUnit, run_matched_query
from scripts.research.p2t04_requirements import AssessorLimits, LexicalAssessor, extract_requirements


LIMITS = AssessorLimits(300, 3, 3, 4, 120, 5)


def _requirements(claim, limits=LIMITS):
    prefix = "Équipement. Abstract wherein this is ignored.\n"
    return extract_requirements(
        "fictional-claim", prefix + claim, claim_start=len(prefix),
        claim_end=len(prefix + claim), limits=limits,
    )


def test_extracts_exact_ordered_claim_clauses_with_code_point_offsets():
    requirements = _requirements(
        "A device WHEREIN the volume is 6.5 litres; "
        "In response to a thermal alarm, the device closes. "
        "It restarts WHEN emergency power returns."
    )
    assert [r.text for r in requirements.requirements] == [
        "WHEREIN the volume is 6.5 litres",
        "In response to a thermal alarm, the device closes",
        "WHEN emergency power returns",
    ]
    for req in requirements.requirements:
        assert requirements.text[req.start:req.end] == req.text
        assert req.requirement_id == f"condition:{req.start}"
    assert len(_requirements("WHEREIN each pump works; WHEN mains power returns.",
                             replace(LIMITS, requirements=1)).requirements) == 1


@pytest.mark.parametrize(
    ("claim", "limit"),
    [("A device whenever a thermal switch opens.", 300),
     ("A device wherein pressure exceeds threshold.", 32),
     ("A device when x.", 300),
     ("", 300)],
)
def test_missing_or_truncated_condition_supplies_only_static_context(claim, limit):
    requirements = _requirements(claim, replace(LIMITS, claim_chars=limit))
    (req,) = requirements.requirements
    assert req.requirement_id == "query-context"
    assert requirements.text[req.start:req.end] == req.text
    source = SourceUnit("p", "fictional-p", "v1", "Pressure exceeds threshold.")
    assert LexicalAssessor(LIMITS)(
        requirements, (source,), lambda *_: pytest.fail("a static fallback must never cite"),
    ) == ()


def test_targeted_action_uses_exact_partial_source_and_rechecks_new_source():
    requirements = _requirements("Wherein pressure exceeds threshold.")
    text = {"seed": "A Pressure regulator uses a metal gasket.", "new": "Pressure exceeds the threshold."}
    derived_queries = []

    def search(query, *_):
        derived_queries.append(query)
        return [("new", 1.0)]

    record = run_matched_query(
        requirements=requirements, seed_ids=["seed"], eligibility=EligibilityMask("fixture"),
        limits=ScreenLimits(1, 1, 120, 3, 3, 1, 1, 2),
        read_source=lambda cad: SourceUnit(cad, f"fictional:{cad}", "v1", text[cad]),
        assess=LexicalAssessor(LIMITS), search=search,
        rerank=lambda request, pool: {cad: 1.0 for cad in pool},
    )
    target = record["arms"]["unresolved_relation"]
    assert target["search_calls"] == 1 and target["new_ids"] == ["new"]
    policy = target["policy_record"]
    assert policy["coverage"]["selected_before"] == "unresolved"
    assert policy["coverage"]["selected_after"] == "supported"
    assert derived_queries[0].terms[0].origin == "source_copy"
    assert derived_queries[0].terms[0].text == "Pressure regulator"
    evidence_id = policy["coverage"]["before"][0]["reference_evidence_id"]
    locator = record["evidence"][evidence_id]
    assert locator["quote"] == text["seed"][locator["start"]:locator["end"]]
    assert locator["source_id"] == "fictional:seed" and locator["version_id"] == "v1"
    assert locator["content_sha256"] == hashlib.sha256(text["seed"].encode()).hexdigest()


@pytest.mark.parametrize(
    ("limits", "source_texts"),
    [
        (LIMITS, ("Pressure. Exceeds threshold.",)),
        (replace(LIMITS, source_chars=len("Pressure exceeds threshold")), ("Pressure exceeds thresholdless.",)),
        (replace(LIMITS, source_passages=1), ("Nothing relevant.", "Pressure exceeds threshold.")),
        (replace(LIMITS, local_tokens=3), ("Pressure the the the exceeds threshold.",)),
    ],
)
def test_no_binding_across_boundaries_or_without_recoverable_search_material(limits, source_texts):
    sources = tuple(SourceUnit(str(i), f"fictional:{i}", "v1", t) for i, t in enumerate(source_texts))
    assert LexicalAssessor(limits)(
        _requirements("Wherein pressure exceeds threshold."), sources,
        lambda *_: pytest.fail("no local coverage or source-backed expansion is available"),
    ) == ()
