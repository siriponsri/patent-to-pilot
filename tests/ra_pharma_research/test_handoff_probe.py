from pathlib import Path
import sys
from xml.etree import ElementTree

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/research/ra_pharma"))
from handoff_probe import ARMS, cell_text, run_case
from handoff_score import evaluate


def test_word_runs_preserve_sequence_zeros():
    node = ElementTree.fromstring(
        '<w:tc xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:p><w:r><w:t>00</w:t></w:r><w:r><w:t>01</w:t></w:r></w:p></w:tc>'
    )
    assert cell_text(node) == "0001"


def test_an_unread_equivalent_witness_is_not_a_harmful_stop():
    request = {"applicant": "a", "application": "f", "round": "2", "sequence": "0001",
               "role": "applicant_result", "issuer": "test-lab"}
    case = {
        "id": "duplicate", "request": request, "patent_context": False,
        "catalog": [{"id": name, "scope": request, "rank": rank, "edition": "fixture",
                     "locator": name} for rank, name in enumerate(("first", "other"), start=1)],
    }
    traces = {"duplicate": {arm: run_case(case, arm, {"sha256": "fixture"}, None) for arm in ARMS}}
    outcomes = evaluate({"traces": traces}, {"duplicate": {"valid": {"first": "first", "other": "other"},
                                         "patent_context": None, "binding": request}})
    assert all(result["reads"] == ["first"] and result["correct_reply"] and not result["harmful_stop"]
               for result in outcomes["duplicate"].values())
