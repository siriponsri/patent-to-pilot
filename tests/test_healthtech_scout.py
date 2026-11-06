import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from patent_to_pilot.healthtech.scout import (
    LITERAL_MATCH_LABEL,
    LaneSplit,
    ScoutBrief,
    ScoutCandidate,
    ScoutSession,
    TransferRationale,
    check_quote,
    class_member_indices,
    normalize_ipc3,
    partition_by_field,
    two_lane_shortlist,
)

FIXTURE = Path(__file__).parent / "fixtures" / "scout" / "synthetic-session.json"
SOURCE = ("SYNTHETIC. A stent frame keeps steady radial force on the vessel wall\n"
          "while the  patient moves, because nickel-titanium struts recover their shape.")


def _session() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_normalize_ipc3_and_class_member_indices():
    assert normalize_ipc3(["f16", "A61", "F16 "]) == ("A61", "F16")
    with pytest.raises(ValueError):
        normalize_ipc3(["A6"])
    with pytest.raises(ValueError):
        normalize_ipc3(["Z99"])
    members = {"A61": [4, 1], "F16": [1, 7]}
    assert class_member_indices(["F16", "A61", "X99"], members) == [1, 4, 7]
    assert class_member_indices([], members) == []


def test_partition_by_field_keeps_order_and_puts_unclassed_in_other_lane():
    ipc = {"a": ["F16"], "b": ["A61"], "c": [], "d": ["B60", "F04"]}
    own, other = partition_by_field(["a", "b", "a", "c", "d", "e"], ipc, ["F04", "F16"])
    assert own == ["a", "d"]
    assert other == ["b", "c", "e"]
    assert two_lane_shortlist(own, other, 1, 2) == [
        ("own_field", 1, "a"), ("other_fields", 1, "b"), ("other_fields", 2, "c")]


def test_partition_matches_runner_mask_semantics():
    # The dense runner's excluded_ipc3 mask removes exactly the own-field families, so the
    # other-fields lane equals the masked ranking in the same order.
    ipc = {"a": ["F16"], "b": ["A61"], "c": ["F16", "H01"], "d": []}
    ranked = ["c", "b", "a", "d"]
    position = {f: i for i, f in enumerate(ranked)}
    members: dict[str, list[int]] = {}
    for family, codes in ipc.items():
        for code in codes:
            members.setdefault(code, []).append(position[family])
    excluded = set(class_member_indices(["F16"], members))
    masked = [f for f in ranked if position[f] not in excluded]
    assert partition_by_field(ranked, ipc, ["F16"])[1] == masked


def test_check_quote_is_literal_with_exact_offsets():
    ok = check_quote("keeps steady radial force on the vessel wall while the patient moves", SOURCE)
    assert ok.status == "matched"
    assert SOURCE[ok.start:ok.end].split() == "keeps steady radial force on the vessel wall while the patient moves".split()
    assert check_quote("keeps steady radial force on the artery", SOURCE).status == "not_found"
    assert check_quote("Keeps steady radial force on the vessel", SOURCE).status == "not_found"  # case is exact
    assert check_quote("radial force", SOURCE).status == "too_short"
    assert check_quote(" ".join(["w"] * 61), SOURCE).status == "too_long"


def test_session_fixture_round_trips_and_enforces_lanes():
    session = ScoutSession.model_validate(_session())
    assert ScoutSession.model_validate_json(session.model_dump_json()) == session
    assert all(c.judgment == "not_judged" for c in session.candidates)
    assert session.receipt.paid_calls == 0

    wrong_lane = _session()
    wrong_lane["candidates"][2]["ipc3"] = ["F16"]
    with pytest.raises(ValidationError, match="IPC3 codes say otherwise"):
        ScoutSession.model_validate(wrong_lane)

    gap = _session()
    gap["candidates"][1]["rank_in_lane"] = 3
    with pytest.raises(ValidationError, match="ranks must run"):
        ScoutSession.model_validate(gap)

    over = _session()
    over["split"] = {"n_own": 1, "n_other": 2}
    with pytest.raises(ValidationError, match="more candidates"):
        ScoutSession.model_validate(over)

    dup = _session()
    dup["candidates"][3]["family_id"] = "SYN-F003"
    dup["candidates"][3]["rank_in_lane"] = 2
    with pytest.raises(ValidationError, match="duplicate"):
        ScoutSession.model_validate(dup)

    paid = _session()
    paid["receipt"]["paid_calls"] = 1
    with pytest.raises(ValidationError):
        ScoutSession.model_validate(paid)


def test_brief_and_candidate_identifier_rules():
    base = _session()["brief"]
    with pytest.raises(ValidationError, match="normalized"):
        ScoutBrief.model_validate({**base, "own_ipc3": ["f16", "F04"]})
    with pytest.raises(ValidationError):
        ScoutBrief.model_validate({**base, "data_class": "private"})
    with pytest.raises(ValidationError, match="reference_patent basis"):
        ScoutBrief.model_validate({**base, "own_ipc3_basis": "reference_patent"})
    ref = ScoutBrief.model_validate({**base, "own_ipc3_basis": "reference_patent",
                                     "reference_patent_raw": "US 10,123,456 B2",
                                     "reference_patent_canonical": "US10123456B2"})
    assert ref.reference_patent_canonical == "US10123456B2"
    with pytest.raises(ValidationError, match="canonical"):
        ScoutCandidate(family_id="x", lane="other_fields", rank_in_lane=1, score=0.1,
                       representative_raw="EP 1 234 567 A1", representative_canonical="EP1234567")
    with pytest.raises(ValidationError):
        LaneSplit(n_own=0, n_other=0)
    with pytest.raises(ValidationError):
        LaneSplit(n_own=150, n_other=60)


def test_transfer_rationale_status_follows_quote_checks():
    quotes = [check_quote("nickel-titanium struts recover their shape", SOURCE),
              check_quote("a spring made of shape memory alloy wire", SOURCE)]
    fields = dict(session_id="syn-scout-001", family_id="SYN-F003", source_sha256="4" * 64, model="qwen3-8b",
                  model_revision="fixture", prompt_version="ptp-scout-rationale-v0",
                  what_it_does="Keeps contact force steady under motion.",
                  transferable_mechanism="A superelastic element that recovers its shape.")
    rationale = TransferRationale(**fields, quotes=quotes, quote_status="some_unmatched")
    assert rationale.label == LITERAL_MATCH_LABEL and rationale.basis == "system_inference"
    assert [q.status for q in rationale.quotes] == ["matched", "not_found"]
    with pytest.raises(ValidationError, match="quote_status"):
        TransferRationale(**fields, quotes=quotes, quote_status="all_matched")
    with pytest.raises(ValidationError):
        TransferRationale(**fields, quotes=[], quote_status="all_matched")
