import json

from patent_to_pilot.adaptation import AdaptationInput, ChangeEvent, DependencyGuidedAdapter
from patent_to_pilot.adaptation.engine import build_dependency_graph
from patent_to_pilot.integration.pipeline import PublicCaseAdapter, PublicEvidence, PublicOption, PublicPolicy


def _input(*, event_id: str, event_type: str, changed_ids: list[str], forbidden: list[str] = (), evidence_text: str = "Polymer-X coating candidate.") -> AdaptationInput:
    profile = PublicCaseAdapter()._profile("PTP-0001").model_copy(update={"record_id": "G11-ORG", "profile_id": "G11-ORG", "profile_version": "1.0.0"})
    return AdaptationInput(
        project_id="G11-PROJECT",
        brief="Offline adaptation fixture",
        profile=profile,
        policy=PublicPolicy(rule_id="G11-POLICY", component="coating", forbidden_materials=list(forbidden)),
        options=[
            PublicOption(option_id="O-X", selected_component="coating", selected_material="polymer-x", evidence_ids=["E-X"]),
            PublicOption(option_id="O-Y", selected_component="coating", selected_material="polymer-y", evidence_ids=["E-Y"]),
        ],
        evidence=[
            PublicEvidence(evidence_id="E-X", text=evidence_text, source_id="G11-SOURCE", source_locator="G11-SOURCE#x"),
            PublicEvidence(evidence_id="E-Y", text="Polymer-Y coating candidate.", source_id="G11-SOURCE", source_locator="G11-SOURCE#y"),
        ],
        change_event=ChangeEvent(event_id=event_id, event_type=event_type, changed_ids=changed_ids, reason=event_type, event_order=0 if event_id == "E0" else 1),
    )


def test_graph_uses_only_explicit_ids_and_overlapping_dependencies():
    item = _input(event_id="E0", event_type="initial", changed_ids=[])
    graph = build_dependency_graph(item)
    assert any(link.dependency_id == "evidence:E-X" for link in graph.links)
    affected = graph.affected_by(["E-X"])
    assert "option:G11-PROJECT:O-X" in affected
    assert "route:G11-PROJECT:O-X" in affected
    assert "option:G11-PROJECT:O-Y" not in affected


def test_ambiguous_unqualified_dependency_id_is_rejected_but_qualified_id_traverses():
    item = _input(event_id="E0", event_type="initial", changed_ids=[])
    item.policy.rule_id = "E-X"
    graph = build_dependency_graph(item)
    import pytest
    with pytest.raises(ValueError, match="ambiguous dependency ID"):
        graph.affected_by(["E-X"])
    qualified = graph.affected_by(["evidence:E-X"])
    assert "route:G11-PROJECT:O-X" in qualified


def test_unknown_evidence_id_is_explicit_and_new_input_is_not_case_lookup(tmp_path):
    item = _input(event_id="E0", event_type="initial", changed_ids=[])
    item.options[0].evidence_ids = ["E-NOT-SUPPLIED"]
    report = DependencyGuidedAdapter(tmp_path / "g11.sqlite").run_sequence([item])
    route = next(route for route in report.states[0]["routes"] if route["route_id"].endswith(":O-X"))
    assert route["policy_check_state"] == "unknown"
    assert "evidence:E-NOT-SUPPLIED" in {node.node_id for node in report.graph.nodes}
    assert "PTP-0001" not in json.dumps(report.model_dump(mode="json"))


def test_policy_change_and_withdrawal_compare_full_and_selective_with_sqlite_readback(tmp_path):
    initial = _input(event_id="E0", event_type="initial", changed_ids=[])
    policy_change = _input(event_id="E1", event_type="policy_change", changed_ids=["G11-POLICY"], forbidden=["polymer-x"])
    withdrawal = _input(event_id="E2", event_type="evidence_withdrawal", changed_ids=["E-X"], forbidden=[], evidence_text="withdrawn evidence")
    withdrawal.evidence = [withdrawal.evidence[1]]
    report = DependencyGuidedAdapter(tmp_path / "g11.sqlite").run_sequence([initial, policy_change, withdrawal])
    assert report.metrics["sqlite_readback"] is True
    assert report.metrics["output_equivalence"] is True
    assert report.metrics["unaffected_preservation"] is True
    assert report.revisions[0]["before_version"] == 1
    assert report.revisions[0]["after_version"] == 2
    assert report.revisions[1]["read_back"] is True
    assert report.comparisons[1].actual_recomputed_nodes == len(report.comparisons[1].affected_nodes) + len(report.comparisons[1].preserved_nodes)
    assert report.comparisons[1].generator_invocations == 1
    assert report.comparisons[1].selective_strategy == "full_generator_then_scoped_merge"
    assert report.states[1]["routes"][0]["policy_check_state"] == "fails_this_explicit_check"
    assert report.states[2]["routes"][0]["policy_check_state"] == "unknown"


def test_irrelevant_change_preserves_routes_and_new_ids_are_not_case_lookup(tmp_path):
    initial = _input(event_id="E0", event_type="initial", changed_ids=[])
    irrelevant = _input(event_id="E1", event_type="irrelevant_change", changed_ids=["NEW-UNRELATED-ID"])
    report = DependencyGuidedAdapter(tmp_path / "g11.sqlite").run_sequence([initial, irrelevant])
    assert report.metrics["output_equivalence"] is True
    assert report.comparisons[1].actual_recomputed_nodes > 0
    assert report.comparisons[1].affected_nodes == []
    assert "G11-PROJECT" in json.dumps(report.model_dump(mode="json"))
    assert "PTP-0001" not in json.dumps(report.model_dump(mode="json"))


def test_selective_result_uses_authoritative_profile_metadata_from_new_input(tmp_path):
    initial = _input(event_id="E0", event_type="initial", changed_ids=[])
    changed = _input(event_id="E1", event_type="profile_change", changed_ids=["G11-ORG"])
    changed.profile.profile_version = "2.0.0"
    changed.profile.organization_label = "G11 revised profile"
    report = DependencyGuidedAdapter(tmp_path / "g11.sqlite").run_sequence([initial, changed])
    state = report.states[1]
    assert state["profile_id"] == "G11-ORG"
    assert state["profile_version"] == "2.0.0"
    assert state["interface_status"]["organization_profiles"]["profile_version"] == "2.0.0"
