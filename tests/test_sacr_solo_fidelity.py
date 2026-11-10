import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.sacr_solo_fidelity import fixed_sample, required_cards, admit_cards, review_gate


def test_sampling_independent_of_input_order_and_configuration():
    ids = [f"q{i}" for i in range(140)]
    sample = fixed_sample("DAPFAM", ids)
    assert len(sample) == 100 and sample == fixed_sample("DAPFAM", reversed(ids))
    assert sample != fixed_sample("MTM", ids)


def test_missing_screen_results_escalate_and_excess_stops():
    sample = [f"q{i}" for i in range(100)]
    cards = required_cards("DAPFAM", "a" * 64, sample, sample[:19], sample[19:20])
    assert len(cards) == 30
    assert sum(c["category"] == "sentinel" for c in cards) == 10
    with pytest.raises(InputBoundaryError, match="REVIEW_CAP"):
        required_cards("DAPFAM", "a" * 64, sample, sample[:20], sample[20:21])


def test_cumulative_limits_count_new_config_and_both_benchmarks():
    sample = [f"q{i}" for i in range(100)]
    a = required_cards("DAPFAM", "a" * 64, sample, sample[:20])
    b = required_cards("MTM", "a" * 64, sample, sample[:20])
    assert admit_cards(a, b)["issued_total"] == 60
    extra = required_cards("DAPFAM", "b" * 64, sample, [])
    with pytest.raises(InputBoundaryError, match="BUDGET_EXHAUSTED"):
        admit_cards(a, extra)
    with pytest.raises(InputBoundaryError, match="duplicate card"):
        admit_cards(a, a)


@pytest.mark.parametrize("status,expected", [("unsupported", "FAIL_STOP_CONFIGURATION_REVIEW_REQUIRED"),
    ("ambiguous", "INCOMPLETE_NO_PASS"), ("unassessable", "INCOMPLETE_NO_PASS"),
    ("faithful", "SOLO_SCREEN_AND_SENTINEL_GATE_PASS")])
def test_sentinel_critical_or_unknown_never_passes(status, expected):
    cards = required_cards("DAPFAM", "a" * 64, ["q1"], [])
    key = ("DAPFAM", "a" * 64, "q1")
    assert review_gate(cards, {key: status}, automatic_screen_complete=True) == expected
    assert review_gate(cards, {}, automatic_screen_complete=True) == "INCOMPLETE_NO_PASS"
    assert review_gate(cards, {key: "faithful"}, automatic_screen_complete=False) == "INCOMPLETE_NO_PASS"
