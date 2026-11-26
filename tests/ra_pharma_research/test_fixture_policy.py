from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/research/ra_pharma"
sys.path.insert(0, str(SCRIPTS))
from fixture_policy import cost, handoff, read_case


def test_wrong_subject_can_only_issue_with_verification_disabled():
    request = {
        "topic": "measurement", "role": "applicant_result", "subject": "product-A",
        "issuer": "lab", "jurisdiction": "demo", "edition": "r1", "as_of": "2026-11-26",
    }
    source = request | {
        "subject": "product-B", "value": "12", "text": "product-B result is 12",
        "locator": "page 1",
    }
    case = {
        "id": "unit-case", "request": request, "sources": {"report": source},
        "candidates": [{"id": "report", "rank": 1, "route": "attachment"}],
    }
    actions, candidate = read_case(case)
    gated = handoff(case, actions, candidate, specialists=True, verify=True)
    ungated = handoff(case, actions, candidate, specialists=True, verify=False)

    assert gated["actions"] == ungated["actions"]
    assert gated["outgoing"]["status"] == "missing"
    assert gated["outgoing"]["sources"] == []
    assert ungated["outgoing"]["statement"] == "12"
    assert ungated["outgoing"]["depends_on"] == [ungated["evidence"]["item_id"]]
    assert ungated["evidence"]["subject_id"] == "product-B"
    assert cost(actions) == {"reads": 1, "candidate_inspections": 1, "source_bytes": 22}
