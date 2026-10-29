"""Bounded HealthTech controller actions and offline policy.

The controller sees only structured retrieval observations. It cannot emit URLs,
arbitrary tools, evaluator fields, family answers, or executable content.
"""
from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, model_validator

from patent_to_pilot.healthtech.contracts import Contract


ControllerActionType = Literal["technical_search", "feature_search", "stop"]
ControllerReason = Literal[
    "initial_query",
    "low_novelty",
    "high_disagreement",
    "budget_guard",
    "source_unavailable",
    "bounded_stop",
]


class ControllerObservation(Contract):
    query_id: str = Field(min_length=1)
    step_index: int = Field(ge=0, le=4)
    max_steps: int = Field(ge=1, le=4)
    remaining_query_calls: int = Field(ge=0, le=8)
    remaining_candidate_budget: int = Field(ge=0, le=1000)
    source_available: bool
    available_feature_indices: list[int] = Field(default_factory=list)
    used_feature_indices: list[int] = Field(default_factory=list)
    last_new_candidate_count: int = Field(default=0, ge=0, le=1000)
    last_disagreement: float = Field(default=0.0, ge=0.0, le=1.0)
    last_action: ControllerActionType | None = None

    @model_validator(mode="after")
    def validate_state(self):
        if len(self.available_feature_indices) != len(set(self.available_feature_indices)):
            raise ValueError("available feature indices must be unique")
        if len(self.used_feature_indices) != len(set(self.used_feature_indices)):
            raise ValueError("used feature indices must be unique")
        if set(self.available_feature_indices) & set(self.used_feature_indices):
            raise ValueError("available and used feature indices overlap")
        if self.step_index > self.max_steps:
            raise ValueError("step index exceeds max steps")
        return self


class ControllerAction(Contract):
    action_type: ControllerActionType
    feature_index: int | None = Field(default=None, ge=0, le=100)
    reason_code: ControllerReason

    @model_validator(mode="after")
    def validate_shape(self):
        if self.action_type == "feature_search" and self.feature_index is None:
            raise ValueError("feature search requires a feature index")
        if self.action_type != "feature_search" and self.feature_index is not None:
            raise ValueError("only feature search may carry a feature index")
        return self


CONTROLLER_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "action_type": {"type": "string", "enum": ["technical_search", "feature_search", "stop"]},
        "feature_index": {"type": ["integer", "null"], "minimum": 0, "maximum": 100},
        "reason_code": {
            "type": "string",
            "enum": ["initial_query", "low_novelty", "high_disagreement", "budget_guard", "source_unavailable", "bounded_stop"],
        },
    },
    "required": ["action_type", "feature_index", "reason_code"],
}


def validate_controller_action(payload: Any, observation: ControllerObservation) -> ControllerAction:
    """Validate one bounded action against the current structured observation."""
    action = ControllerAction.model_validate(payload)
    if observation.step_index >= observation.max_steps and action.action_type != "stop":
        raise ValueError("controller must stop at the step cap")
    if not observation.source_available and action.action_type != "stop":
        raise ValueError("controller cannot search when source is unavailable")
    if observation.remaining_query_calls <= 0 or observation.remaining_candidate_budget <= 0:
        if action.action_type != "stop":
            raise ValueError("controller must stop when a hard budget is exhausted")
    if action.action_type == "technical_search" and observation.step_index != 0:
        raise ValueError("technical search is only allowed at step zero")
    if action.action_type == "feature_search":
        if action.feature_index not in observation.available_feature_indices:
            raise ValueError("feature index is not currently available")
        if action.feature_index in observation.used_feature_indices:
            raise ValueError("feature index was already used")
    return action


def deterministic_controller_action(observation: ControllerObservation) -> ControllerAction:
    """Offline bounded policy used to test the action seam before paid calls.

    The policy stops after a high-yield, low-disagreement first query and
    continues when novelty is weak or lexical/dense retrieval disagrees.
    """
    if (
        not observation.source_available
        or observation.remaining_query_calls <= 0
        or observation.remaining_candidate_budget <= 0
        or observation.step_index >= observation.max_steps
    ):
        reason = "source_unavailable" if not observation.source_available else "budget_guard"
        return ControllerAction(action_type="stop", reason_code=reason)
    if observation.step_index == 0:
        return ControllerAction(action_type="technical_search", reason_code="initial_query")
    if not observation.available_feature_indices:
        return ControllerAction(action_type="stop", reason_code="bounded_stop")
    if observation.last_new_candidate_count == 0:
        return ControllerAction(action_type="stop", reason_code="low_novelty")
    if observation.last_new_candidate_count >= 5 and observation.last_disagreement < 0.5:
        return ControllerAction(action_type="stop", reason_code="bounded_stop")
    return ControllerAction(
        action_type="feature_search",
        feature_index=observation.available_feature_indices[0],
        reason_code="high_disagreement" if observation.last_disagreement >= 0.5 else "low_novelty",
    )
