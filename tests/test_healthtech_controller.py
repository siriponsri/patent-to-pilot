import pytest
from pydantic import ValidationError

from patent_to_pilot.healthtech.controller import (
    CONTROLLER_RESPONSE_SCHEMA,
    ControllerObservation,
    deterministic_controller_action,
    validate_controller_action,
)


def _observation(**changes):
    values = {
        "query_id": "q1",
        "step_index": 0,
        "max_steps": 3,
        "remaining_query_calls": 3,
        "remaining_candidate_budget": 100,
        "source_available": True,
        "available_feature_indices": [1, 2],
        "used_feature_indices": [],
    }
    values.update(changes)
    return ControllerObservation.model_validate(values)


def test_controller_policy_uses_first_query_then_stops_or_continues_from_observations():
    first = deterministic_controller_action(_observation())
    assert first.action_type == "technical_search"

    stop = deterministic_controller_action(_observation(
        step_index=1,
        last_new_candidate_count=12,
        last_disagreement=0.2,
        available_feature_indices=[1],
    ))
    assert stop.action_type == "stop"

    continue_action = deterministic_controller_action(_observation(
        step_index=1,
        last_new_candidate_count=12,
        last_disagreement=0.8,
        available_feature_indices=[1],
    ))
    assert continue_action.action_type == "feature_search"
    assert continue_action.feature_index == 1


def test_controller_rejects_evaluator_fields_and_invalid_feature_selection():
    observation = _observation(step_index=1, available_feature_indices=[1])
    with pytest.raises(ValueError, match="feature index"):
        validate_controller_action(
            {"action_type": "feature_search", "feature_index": 2, "reason_code": "high_disagreement"},
            observation,
        )
    with pytest.raises(ValidationError):
        validate_controller_action(
            {"action_type": "stop", "feature_index": None, "reason_code": "bounded_stop", "gold_links": ["US1"]},
            observation,
        )


def test_controller_schema_is_strict_and_budget_guard_is_fail_closed():
    assert CONTROLLER_RESPONSE_SCHEMA["additionalProperties"] is False
    observation = _observation(step_index=1, remaining_query_calls=0)
    with pytest.raises(ValueError, match="hard budget"):
        validate_controller_action(
            {"action_type": "feature_search", "feature_index": 1, "reason_code": "low_novelty"},
            observation,
        )
