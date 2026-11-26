from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/research/ra_pharma"))
from interruption_probe import choose
from interruption_score import evaluate


def test_forecast_and_greedy_take_distinct_initial_actions_under_shared_observations():
    scope = {"sequence": "0004"}
    cards = [
        {"id": "known", "kind": "report", "scope": scope, "advertises": ["a"]},
        {"id": "opaque", "kind": "report", "scope": None, "advertises": ["b"]},
        {"id": "index", "kind": "locator", "scope": None, "advertises": ["a", "b"]},
    ]
    assert choose("nearest_complete", cards, scope, {"a", "b"}, 2)[0]["id"] == "known"
    assert choose("budget_forecast", cards, scope, {"a", "b"}, 2)[0]["id"] == "index"
    assert choose("budget_forecast", cards, scope, {"a", "b"}, 1)[0]["id"] == "known"


def test_scoring_does_not_credit_an_unopened_witness():
    trace = {"actions": [{"id": "index", "kind": "locator", "sha256": "x",
                          "after": {"a": {"source": "never-opened", "sha256": "x"}}}],
             "outgoing": {}, "absent_rows": ["a"]}
    arms = {name: trace for name in ("fixed_domain", "nearest_complete", "budget_forecast")}
    try:
        evaluate({"traces": {"case": arms}},
                 {"case": {"valid": {"a": {"never-opened": "/results/a"}},
                           "family": "family", "layout": "fixture"}})
    except ValueError as error:
        assert "observed source" in str(error)
    else:
        raise AssertionError("unopened witness was credited")
