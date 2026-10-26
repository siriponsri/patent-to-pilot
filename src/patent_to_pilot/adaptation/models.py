"""Typed public inputs and graph records for bounded G11 adaptation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from patent_to_pilot.core.models import OrganizationProfile
from patent_to_pilot.integration.pipeline import PublicEvidence, PublicOption, PublicPolicy, WorkflowInput


class ChangeEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    changed_ids: list[str] = Field(default_factory=list)
    changed_fields: list[str] = Field(default_factory=list)
    reason: str = Field(min_length=1)
    event_order: int = Field(default=0, ge=0)
    version: int = Field(default=1, ge=1)


class AdaptationInput(BaseModel):
    """Caller-supplied packet; no hidden evaluator material is accepted."""
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1)
    brief: str = Field(min_length=1)
    profile: OrganizationProfile
    evidence: list[PublicEvidence] = Field(default_factory=list)
    options: list[PublicOption] = Field(min_length=1)
    policy: PublicPolicy
    change_event: ChangeEvent

    def to_workflow(self) -> WorkflowInput:
        from patent_to_pilot.integration.pipeline import PublicEvent
        event = PublicEvent(type=self.change_event.event_type, event_order=self.change_event.event_order, description=self.change_event.reason, policy_rule_id=self.policy.rule_id)
        return WorkflowInput(project_id=self.project_id, brief=self.brief, profile=self.profile, policy=self.policy, options=self.options, evidence=self.evidence, event=event)


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid")
    node_id: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    external_id: str = Field(min_length=1)


class DependencyLink(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dependent_id: str = Field(min_length=1)
    dependency_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class DependencyGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nodes: list[GraphNode]
    links: list[DependencyLink]

    def affected_by(self, changed_ids: list[str]) -> set[str]:
        aliases: dict[str, set[str]] = {}
        for node in self.nodes:
            for alias in (node.node_id, node.external_id):
                aliases.setdefault(alias, set()).add(node.node_id)
        frontier: set[str] = set()
        for changed_id in changed_ids:
            matches = aliases.get(changed_id, set())
            if len(matches) > 1:
                raise ValueError(f"ambiguous dependency ID {changed_id!r}; use a qualified node ID")
            frontier.update(matches)
        affected = set(frontier)
        while frontier:
            next_frontier = {link.dependent_id for link in self.links if link.dependency_id in frontier and link.dependent_id not in affected}
            affected.update(next_frontier)
            frontier = next_frontier
        return affected


class AdaptationComparison(BaseModel):
    model_config = ConfigDict(extra="forbid")
    equivalent: bool
    preserved_unaffected: bool
    affected_nodes: list[str]
    preserved_nodes: list[str]
    generator_invocations: int = Field(ge=0)
    actual_recomputed_nodes: int = Field(ge=0)
    selective_strategy: str
    generator: str


class AdaptationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    project_id: str
    states: list[dict[str, Any]]
    revisions: list[dict[str, Any]]
    graph: DependencyGraph
    comparisons: list[AdaptationComparison]
    metrics: dict[str, Any]
    provider_calls: str = "NOT_RUN"
