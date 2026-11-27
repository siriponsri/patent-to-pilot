from pathlib import Path
import sys
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/research/ra_pharma"))
from claim_branch_probe import packet, parent_options


def test_alternatives_remain_separate_and_shared_parent_reuses_one_passage():
    index = {}
    for number, text in {
        1: "A widget.",
        2: "A widget as claimed in claim 1, including a holder.",
        3: "A widget as claimed in claim 1 or 2, including a latch.",
        4: "A widget as claimed in claim 3, including a handle.",
    }.items():
        node = ElementTree.Element("claim", {"id": f"test-claim-{number}"})
        node.text = text
        index[number] = node

    shared = packet(index, "shared", 4)
    assert shared["rows"][4] == [
        {"claims": (4, 3, 1), "status": "supported"},
        {"claims": (4, 3, 2, 1), "status": "supported"},
    ]
    assert shared["rows"] == packet(index, "cache_walk", 4)["rows"]
    assert [row["claim"] for row in shared["reads"]].count(1) == 1
    assert shared["shared_requests"] == [{"claim": 1, "requested_by_distinct_rows": 3}]
    missing = packet(index, "shared", 4, unavailable=(1,))
    assert missing["rows"][4][0]["request"] == {
        "claim": 1, "edition": "2011-03-23", "source_id": "EP2298134 A1",
        "reason": "passage-unavailable",
    }


def test_dependency_parser_fails_closed_for_unresolved_conjunction_and_forward_reference():
    assert parent_options("An item as claimed in claims 1 and 2, with a cover.", 3) is None
    assert parent_options("An item as claimed in claim 3, with a cover.", 3) is None
