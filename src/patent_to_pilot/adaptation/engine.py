"""Deterministic full regeneration and explicit dependency-guided repair."""

from __future__ import annotations

import html
import json
import time
from pathlib import Path
from typing import Any

from patent_to_pilot.core.models import ChangeRecord, RouteRecord
from patent_to_pilot.core.repository import SQLiteRecordRepository
from patent_to_pilot.integration.pipeline import IntegrationPipeline, IntegrationResult

from .models import AdaptationComparison, AdaptationInput, AdaptationReport, DependencyGraph, DependencyLink, GraphNode


class DeterministicGenerator:
    """One generator shared by full regeneration and selective repair."""

    name = "IntegrationPipeline deterministic public-input generator"

    def __init__(self) -> None:
        self.pipeline = IntegrationPipeline()

    def generate(self, item: AdaptationInput) -> IntegrationResult:
        return self.pipeline.run_workflow(item.to_workflow())


def build_dependency_graph(item: AdaptationInput) -> DependencyGraph:
    """Build links only from explicit IDs in the caller packet."""

    project = f"project:{item.project_id}"
    profile = f"profile:{item.profile.profile_id}@{item.profile.profile_version}"
    policy_external = item.policy.rule_id or f"{item.project_id}-policy"
    policy = f"policy:{policy_external}"
    nodes = [
        GraphNode(node_id=project, kind="project", external_id=item.project_id),
        GraphNode(node_id=profile, kind="profile", external_id=item.profile.profile_id),
        GraphNode(node_id=policy, kind="policy", external_id=policy_external),
    ]
    links = [
        DependencyLink(dependent_id=project, dependency_id=profile, reason="declared project profile"),
        DependencyLink(dependent_id=project, dependency_id=policy, reason="declared project policy"),
    ]
    evidence_nodes: dict[str, str] = {}
    for evidence in item.evidence:
        node_id = f"evidence:{evidence.evidence_id}"
        evidence_nodes[evidence.evidence_id] = node_id
        nodes.append(GraphNode(node_id=node_id, kind="evidence", external_id=evidence.evidence_id))
    known_node_ids = {node.node_id for node in nodes}
    for option in item.options:
        option_id = option.option_id or option.candidate_id or "unknown"
        option_node = f"option:{item.project_id}:{option_id}"
        nodes.append(GraphNode(node_id=option_node, kind="option", external_id=option_id))
        links.append(DependencyLink(dependent_id=option_node, dependency_id=policy, reason="option evaluated against declared policy"))
        for evidence_id in option.evidence_ids:
            evidence_node = evidence_nodes.get(evidence_id, f"evidence:{evidence_id}")
            if evidence_node not in known_node_ids:
                nodes.append(GraphNode(node_id=evidence_node, kind="evidence", external_id=evidence_id))
                known_node_ids.add(evidence_node)
            links.append(DependencyLink(dependent_id=option_node, dependency_id=evidence_node, reason="option supplied evidence ID"))
        route_node = f"route:{item.project_id}:{option_id}"
        nodes.append(GraphNode(node_id=route_node, kind="route", external_id=f"{item.project_id}:{option_id}"))
        links.extend([
            DependencyLink(dependent_id=route_node, dependency_id=option_node, reason="route is generated from option"),
            DependencyLink(dependent_id=route_node, dependency_id=policy, reason="route policy check"),
        ])
        for evidence_id in option.evidence_ids:
            links.append(DependencyLink(dependent_id=route_node, dependency_id=evidence_nodes.get(evidence_id, f"evidence:{evidence_id}"), reason="route traceability"))
    return DependencyGraph(nodes=nodes, links=links)


def _option_id(option: dict[str, Any]) -> str:
    return str(option.get("option_id") or option.get("candidate_id") or "unknown")


class DependencyGuidedAdapter:
    """Run a bounded adaptation sequence and persist route/revision payloads."""

    def __init__(self, repository_path: str | Path = ":memory:") -> None:
        self.repository_path = repository_path
        self.generator = DeterministicGenerator()

    def run_sequence(self, inputs: list[AdaptationInput]) -> AdaptationReport:
        if not inputs:
            raise ValueError("adaptation sequence must not be empty")
        project_id = inputs[0].project_id
        if any(item.project_id != project_id for item in inputs):
            raise ValueError("all adaptation states must use the same project_id")
        if self.repository_path != ":memory:":
            Path(self.repository_path).parent.mkdir(parents=True, exist_ok=True)
        started = time.perf_counter()
        repo = SQLiteRecordRepository(self.repository_path)
        states: list[dict[str, Any]] = []
        revisions: list[dict[str, Any]] = []
        comparisons: list[AdaptationComparison] = []
        previous_result: IntegrationResult | None = None
        previous_graph: DependencyGraph | None = None
        try:
            for item in inputs:
                graph = build_dependency_graph(item)
                full_result = self.generator.generate(item)
                if previous_result is None:
                    selective_result = full_result
                    affected = {node.node_id for node in graph.nodes}
                    preserved: set[str] = set()
                    generator_invocations = 1
                    actual_recomputed_nodes = len(graph.nodes)
                    selective_strategy = "full_initial_generation"
                else:
                    old_graph = previous_graph or graph
                    affected = graph.affected_by(item.change_event.changed_ids) | old_graph.affected_by(item.change_event.changed_ids)
                    selective_result = self._selective_repair(previous_result, full_result, affected, item.project_id)
                    preserved = (set(node.node_id for node in graph.nodes) | set(node.node_id for node in old_graph.nodes)) - affected
                    generator_invocations = 1
                    # The current bounded implementation always invokes the
                    # full generator and then merges its output. It therefore
                    # does not claim that only affected nodes were actually
                    # recomputed.
                    actual_recomputed_nodes = len(graph.nodes)
                    selective_strategy = "full_generator_then_scoped_merge"
                full_payload = full_result.model_dump(mode="json")
                selective_payload = selective_result.model_dump(mode="json")
                comparisons.append(AdaptationComparison(
                    equivalent=self._equivalent(full_payload, selective_payload),
                    preserved_unaffected=self._preserved(previous_result, selective_result, affected),
                    affected_nodes=sorted(affected),
                    preserved_nodes=sorted(preserved),
                    generator_invocations=generator_invocations,
                    actual_recomputed_nodes=actual_recomputed_nodes,
                    selective_strategy=selective_strategy,
                    generator=self.generator.name,
                ))
                self._persist(repo, item, selective_result, previous_result, revisions)
                states.append(selective_payload)
                previous_result, previous_graph = selective_result, graph
        finally:
            repo.close()
        elapsed = time.perf_counter() - started
        return AdaptationReport(
            kind="bounded_offline_g11_adaptation",
            project_id=project_id,
            states=states,
            revisions=revisions,
            graph=previous_graph or build_dependency_graph(inputs[-1]),
            comparisons=comparisons,
            metrics={
                "state_count": len(states),
                "revision_count": len(revisions),
                "elapsed_seconds": elapsed,
                "sqlite_readback": all(revision["read_back"] for revision in revisions),
                "output_equivalence": all(comparison.equivalent for comparison in comparisons),
                "unaffected_preservation": all(comparison.preserved_unaffected for comparison in comparisons),
                "paid_api": False,
                "model_calls": False,
                "provider_transport": "mock_only_not_live",
                "planned_models": ["google/gemini-2.5-flash-lite", "openai/gpt-4.1-mini"],
            },
        )

    @staticmethod
    def _selective_repair(previous: IntegrationResult, full: IntegrationResult, affected: set[str], project_id: str) -> IntegrationResult:
        """Merge full generator output, replacing only affected option/route nodes."""
        result = previous.model_copy(deep=True)
        result.state_id = full.state_id
        result.project_display_name = full.project_display_name
        result.profile_id = full.profile_id
        result.profile_version = full.profile_version
        result.brief = full.brief
        result.allowed_evidence = full.allowed_evidence
        result.source_integrity = full.source_integrity
        result.fictional_stipulations = full.fictional_stipulations
        result.interpretations = full.interpretations
        result.interface_status = full.interface_status
        result.mock_provider_called = full.mock_provider_called
        result.handoff = full.handoff
        result.unknowns = full.unknowns
        result.proposed_next_tests = full.proposed_next_tests
        result.agent_input_fields = full.agent_input_fields
        changed_evidence = {node.split(":", 1)[1] for node in affected if node.startswith("evidence:")}
        if changed_evidence:
            result.source_facts = [fact for fact in previous.source_facts if not fact.get("field", "").startswith("evidence:") or fact["field"].split(":", 1)[1] not in changed_evidence]
            result.source_facts.extend(fact for fact in full.source_facts if fact.get("field", "").startswith("evidence:") and fact["field"].split(":", 1)[1] in changed_evidence)
        affected_options = {node.split(":", 2)[-1] for node in affected if node.startswith("option:")}
        full_options = {_option_id(option): option for option in full.options}
        previous_options = {_option_id(option): option for option in previous.options}
        result.options = [previous_options[option_id] for option_id in previous_options if option_id in full_options and option_id not in affected_options]
        result.options.extend(full_options[option_id] for option_id in full_options if option_id in affected_options or option_id not in previous_options)
        result.options.sort(key=_option_id)
        affected_routes = {node.split(":", 1)[1] for node in affected if node.startswith("route:")}
        full_routes = {route["route_id"]: route for route in full.routes}
        previous_routes = {route["route_id"]: route for route in previous.routes}
        result.routes = [previous_routes[route_id] for route_id in previous_routes if route_id in full_routes and route_id not in affected_routes]
        result.routes.extend(full_routes[route_id] for route_id in full_routes if route_id in affected_routes or route_id not in previous_routes)
        result.routes.sort(key=lambda route: route["route_id"])
        return result

    @staticmethod
    def _equivalent(full: dict[str, Any], selective: dict[str, Any]) -> bool:
        for payload in (dict(full), dict(selective)):
            payload.pop("state_id", None)
            payload.pop("project_display_name", None)
        normalized_full = dict(full)
        normalized_selective = dict(selective)
        normalized_full.pop("state_id", None)
        normalized_full.pop("project_display_name", None)
        normalized_selective.pop("state_id", None)
        normalized_selective.pop("project_display_name", None)
        return normalized_full == normalized_selective

    @staticmethod
    def _preserved(previous: IntegrationResult | None, current: IntegrationResult, affected: set[str]) -> bool:
        if previous is None:
            return True
        affected_options = {node.split(":", 2)[-1] for node in affected if node.startswith("option:")}
        old = {_option_id(option): option for option in previous.options}
        new = {_option_id(option): option for option in current.options}
        return all(old[option_id] == new[option_id] for option_id in set(old) & set(new) - affected_options)

    @staticmethod
    def _persist(repo: SQLiteRecordRepository, item: AdaptationInput, result: IntegrationResult, previous: IntegrationResult | None, revisions: list[dict[str, Any]]) -> None:
        route_versions: dict[str, int] = {}
        prior_versions: dict[str, int | None] = {}
        for route in result.routes:
            history = repo.history("RouteRecord", route["route_id"])
            prior_versions[route["route_id"]] = history[-1]["version"] if history else None
            version = (history[-1]["version"] + 1) if history else 1
            route_versions[route["route_id"]] = version
            record = RouteRecord(record_id=route["route_id"], route_id=route["route_id"], project_id=item.project_id, label=route["label"], status=route["status"], evidence_ids=route["evidence_ids"], constraint_ids=route["constraint_ids"], unknowns=route["unknowns"], version=version)
            repo.save(record)
            read_back = repo.read_latest("RouteRecord", route["route_id"], RouteRecord)
            if read_back is None or read_back.model_dump(mode="json") != record.model_dump(mode="json"):
                raise RuntimeError(f"route payload read-back failed: {route['route_id']}")
        if previous is None:
            return
        before = previous.model_dump(mode="json")
        after = result.model_dump(mode="json")
        affected_fields, preserved_fields = IntegrationPipeline._diff_fields(before, after)
        prior = [value for value in prior_versions.values() if value is not None]
        after_version = max(route_versions.values(), default=1)
        before_version = max(prior) if prior else None
        event = item.change_event
        revision_id = f"{item.project_id}:adaptation:{event.event_id}"
        change = ChangeRecord(record_id=revision_id, change_id=revision_id, entity_type="adaptation_result", entity_id=item.project_id, before_version=before_version, after_version=after_version, affected_fields=affected_fields, preserved_fields=preserved_fields, reason=event.reason, source_refs=list(event.changed_ids), version=event.version)
        repo.save(change)
        read_back = repo.read_latest("ChangeRecord", revision_id, ChangeRecord)
        revisions.append({"event_id": event.event_id, "reason": event.reason, "before_version": before_version, "after_version": after_version, "affected_fields": affected_fields, "preserved_fields": preserved_fields, "before": before, "after": after, "read_back": read_back is not None and read_back.model_dump(mode="json") == change.model_dump(mode="json"), "route_history_versions": {route_id: [entry["version"] for entry in repo.history("RouteRecord", route_id)] for route_id in route_versions}})


def write_reports(report: AdaptationReport | dict[str, Any], output_dir: str | Path) -> None:
    """Write JSON, Markdown, and a small static HTML view from an actual run."""
    payload = report.model_dump(mode="json") if isinstance(report, AdaptationReport) else report
    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    (target / "adaptation.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    metrics = payload["metrics"]
    lines = ["# G11 bounded offline adaptation", "", "Deterministic development slice; not G12 learning, an LLM benchmark, or a scientific superiority result.", "", f"- States: {metrics['state_count']}", f"- Revisions: {metrics['revision_count']}", f"- Elapsed seconds: {metrics['elapsed_seconds']:.6f}", f"- SQLite read-back: {'PASS' if metrics['sqlite_readback'] else 'FAIL'}", f"- Full/selective equivalence: {'PASS' if metrics['output_equivalence'] else 'FAIL'}", f"- Unaffected preservation: {'PASS' if metrics['unaffected_preservation'] else 'FAIL'}", "- Selective implementation: full generator followed by scoped merge; actual recomputation is not claimed selective", f"- Provider transport: {metrics['provider_transport']}", f"- Planned model targets only: {', '.join(metrics['planned_models'])}", "- Provider calls: NOT_RUN", ""]
    lines.extend(
        f"- affected={len(item['affected_nodes'])}; generator_invocations={item['generator_invocations']}; "
        f"actual_recomputed_nodes={item['actual_recomputed_nodes']}; strategy={item['selective_strategy']}; "
        f"equivalent={item['equivalent']}; preserved={item['preserved_unaffected']}"
        for item in payload["comparisons"]
    )
    (target / "adaptation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    rows = []
    for state in payload["states"]:
        routes = "<br>".join(html.escape(f"{route['route_id']}: {route['status']} / {route['policy_check_state']} / evidence={','.join(route['evidence_ids']) or 'none'}") for route in state["routes"])
        rows.append(f"<tr><td>{html.escape(state['state_id'])}</td><td>{html.escape(state['brief'])}</td><td>{routes}</td><td>{html.escape(state['handoff']['status'])}</td></tr>")
    document = "<!doctype html><meta charset='utf-8'><title>G11 bounded offline adaptation</title><style>body{font:16px system-ui;max-width:1200px;margin:2rem auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:.5rem;vertical-align:top}</style><h1>G11 bounded offline adaptation</h1><p>Deterministic offline slice; provider calls not run; no scientific superiority claim.</p><table><tr><th>State</th><th>Brief</th><th>Routes / evidence</th><th>Handoff</th></tr>" + "".join(rows) + "</table><h2>Before/after revisions</h2><pre>" + html.escape(json.dumps(payload["revisions"], indent=2, ensure_ascii=False)) + "</pre>"
    (target / "adaptation.html").write_text(document, encoding="utf-8")
