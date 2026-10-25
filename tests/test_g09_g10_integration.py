import json
from pathlib import Path

import pytest

from patent_to_pilot.integration.pipeline import AgentPacket, DevelopmentEvaluator, IntegrationPipeline, PublicCaseAdapter, PublicEvidence, PublicEvent, PublicOption, PublicPolicy, WorkflowInput


def test_public_adapter_has_no_evaluator_fields_and_preserves_bindings():
    adapter = PublicCaseAdapter()
    for case_id, profile_id in (("PTP-0001", "PTP-FIC-ORG-A"), ("PTP-0002", "PTP-FIC-ORG-B"), ("PTP-0003", "PTP-FIC-ORG-C")):
        loaded = adapter.load(case_id, "S0")
        payload = loaded.packet.model_dump()
        encoded = json.dumps(payload)
        assert loaded.packet.profile_id == profile_id
        assert "expected_doc_ids" not in encoded
        assert "evaluator-only" not in encoded
        assert loaded.packet.input_boundary == "public-input-only"


def test_adapter_rejects_evaluator_field_without_reading_archive(tmp_path):
    source_root = Path(__file__).parents[1] / "methodology" / "evaluation" / "cases"
    case_root = tmp_path / "cases" / "PTP-0002" / "public-input"
    case_root.mkdir(parents=True)
    payload = json.loads((source_root / "PTP-0002" / "public-input" / "S0.json").read_text(encoding="utf-8"))
    payload["expected_doc_ids"] = ["hidden"]
    (case_root / "S0.json").write_text(json.dumps(payload), encoding="utf-8")
    org_root = tmp_path / "organizations"
    profile = Path(__file__).parents[1] / "methodology" / "organizations" / "fictional-profile-b"
    target = org_root / "fictional-profile-b" / "v1"
    target.mkdir(parents=True)
    (target / "profile.json").write_text((profile / "v1" / "profile.json").read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden evaluator field"):
        PublicCaseAdapter(tmp_path / "cases", org_root).load("PTP-0002", "S0")


def test_case_rules_and_revision_preservation():
    pipeline = IntegrationPipeline()
    case1 = pipeline.run_case("PTP-0001")
    assert case1["states"][0]["options"][0]["policy_check_state"] == "passes_this_explicit_check"
    assert case1["states"][0]["options"][1]["policy_check_state"] == "passes_this_explicit_check"
    assert case1["states"][1]["options"][0]["policy_check_state"] == "fails_this_explicit_check"
    assert case1["states"][3]["options"][1]["policy_check_state"] == "unknown"
    assert any(change["reason"] == "project_name_only" and "source_integrity" in change["preserved_fields"] for change in case1["changes"])
    case2 = pipeline.run_case("PTP-0002")
    assert case2["states"][0]["options"][0]["policy_check_state"] == "passes_this_explicit_check"
    assert case2["states"][3]["options"][1]["policy_check_state"] == "unknown"
    case3 = pipeline.run_case("PTP-0003")
    facts = {fact["field"]: fact for fact in case3["states"][0]["source_facts"]}
    assert facts["reported_intermediate_stage_count"]["value"] == 5
    assert facts["BTC_stage_use_count"]["value"] == 2
    assert facts["all_manufacturing_operations"]["value"] is None
    assert case3["states"][1]["options"][0]["policy_check_state"] == "fails_this_explicit_check"
    assert case3["states"][3]["options"][0]["policy_check_state"] == "unknown"


def test_runner_and_static_exports(tmp_path):
    pipeline = IntegrationPipeline()
    report = pipeline.run_all()
    assert report["benchmark"] is False
    assert report["metrics"]["case_count"] == 3
    assert report["metrics"]["elapsed_seconds"] >= 0
    assert report["metrics"]["revision_read_back"] is True
    assert len(report["cases"][0]["evaluations"]) == 5
    assert report["cases"][0]["states"][0]["fictional_stipulations"]["basis"].startswith("public development")
    assert report["cases"][0]["states"][0]["interpretations"]
    interfaces = report["cases"][0]["states"][0]["interface_status"]
    assert interfaces["typed_core"]["status"] == "used"
    assert interfaces["ingestion"]["status"] == "not_invoked"
    assert interfaces["retrieval"]["status"] == "not_invoked"
    assert interfaces["extraction"]["model_called"] is False
    assert report["api_smoke"]["status"] == "NOT_RUN"
    pipeline.write_reports(report, tmp_path)
    assert json.loads((tmp_path / "integration.json").read_text(encoding="utf-8"))["metrics"]["state_count"] == 15
    assert "not a model benchmark" in (tmp_path / "integration.md").read_text(encoding="utf-8")
    markdown = (tmp_path / "integration.md").read_text(encoding="utf-8")
    assert "Independent evaluator: PASS" in markdown and "Route-local status: PASS" in markdown
    html = (tmp_path / "integration.html").read_text(encoding="utf-8")
    assert "<table>" in html and "before/after changes" in html and "Evidence:" in html


def test_negative_methods_are_detected_by_separate_evaluator():
    adapter = PublicCaseAdapter()
    pipeline = IntegrationPipeline(adapter)
    for state_id in ("S0", "S1", "S2", "S3", "S4"):
        loaded = adapter.load("PTP-0001", state_id)
        s0_loaded = adapter.load("PTP-0001", "S0")
        s0_result = pipeline.run_state(s0_loaded)
        evaluation = DevelopmentEvaluator.evaluate(loaded.packet, s0_result)
        if state_id != "S0":
            assert evaluation.passed is False
            assert evaluation.failures

    loaded = adapter.load("PTP-0001", "S0")
    result = pipeline.run_state(loaded).model_copy(deep=True)
    result.source_facts[-1].update({"state": "known", "value": 99})
    evaluation = DevelopmentEvaluator.evaluate(loaded.packet, result)
    assert evaluation.passed is False
    assert any("yield" in failure for failure in evaluation.failures)


def test_nested_allowlist_profile_version_and_span_integrity_in_temp(tmp_path):
    source_root = Path(__file__).parents[1]
    cases_root = tmp_path / "cases"
    org_root = tmp_path / "organizations"
    case_dir = cases_root / "PTP-0002" / "public-input"
    case_dir.mkdir(parents=True)
    original = source_root / "methodology" / "evaluation" / "cases" / "PTP-0002" / "public-input" / "S0.json"
    payload = json.loads(original.read_text(encoding="utf-8"))
    payload["case_stipulations"]["policy"]["unexpected_nested"] = True
    (case_dir / "S0.json").write_text(json.dumps(payload), encoding="utf-8")
    profile_dir = org_root / "fictional-profile-b" / "v1"
    profile_dir.mkdir(parents=True)
    profile_source = source_root / "methodology" / "organizations" / "fictional-profile-b" / "v1" / "profile.json"
    (profile_dir / "profile.json").write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")
    adapter = PublicCaseAdapter(cases_root, org_root)
    with pytest.raises(ValueError, match="extra_forbidden|unsupported public packet field"):
        adapter.load("PTP-0002", "S0")

    payload = json.loads(original.read_text(encoding="utf-8"))
    payload["organization_ref"]["profile_version"] = "9.9.9"
    (case_dir / "S0.json").write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="profile version mismatch"):
        adapter.load("PTP-0002", "S0")

    payload = json.loads(original.read_text(encoding="utf-8"))
    payload["sources"][0]["text"] += " altered"
    (case_dir / "S0.json").write_text(json.dumps(payload), encoding="utf-8")
    loaded = adapter.load("PTP-0002", "S0")
    result = IntegrationPipeline(adapter).run_state(loaded)
    assert result.source_integrity["valid"] is False
    assert result.source_integrity["invalid_evidence_ids"]
    peg = next(fact for fact in result.source_facts if fact["field"] == "PEG_role")
    assert peg["state"] == "unknown"
    assert any(fact["state"] == "known" for fact in result.source_facts if fact["field"] in {"PVP_role", "HPMC_role"})
    assert all(option["policy_check_state"] == "unknown" for option in result.options)


def test_role_specific_material_match_does_not_use_silicon_compound():
    packet = AgentPacket(
        case_id="PTP-0001", state_id="S0", event=PublicEvent(type="initial", event_order=0), brief="fixture",
        profile_id="PTP-FIC-ORG-A", profile_version="1.0.0",
        policy=PublicPolicy(component="substrate", permitted_materials=["silicon"], forbidden_materials=[]),
        options=[PublicOption(candidate_id="A", selected_component="substrate", selected_material="silicon")],
        evidence=[PublicEvidence(evidence_id="C-CARBIDE", text="silicon carbide pattern", source_id="fixture", source_locator="fixture#1", locator={"char_start": 0, "char_end": 21, "offset_unit": "Unicode code points, end-exclusive"}, char_start=0, char_end=21)], unknowns=[],
    )
    result = IntegrationPipeline().run_state(type("Loaded", (), {"packet": packet, "raw": {"display_name": "fixture"}})())
    assert result.source_facts[0]["state"] == "unknown"
    assert result.options[0]["policy_check_state"] == "unknown"


def test_evaluator_rejects_route_status_or_payload_mismatch():
    adapter = PublicCaseAdapter()
    loaded = adapter.load("PTP-0001", "S0")
    result = IntegrationPipeline(adapter).run_state(loaded).model_copy(deep=True)
    result.routes[0]["status"] = "ready_for_review"
    evaluation = DevelopmentEvaluator.evaluate(loaded.packet, result)
    assert evaluation.passed is False
    assert any("route-local status mismatch" in failure for failure in evaluation.failures)


def test_evaluator_checks_each_route_and_unsupported_required_values():
    adapter = PublicCaseAdapter()
    loaded = adapter.load("PTP-0001", "S1")
    result = IntegrationPipeline(adapter).run_state(loaded).model_copy(deep=True)
    # Swap route outcomes: a single failing route must not make the pack pass.
    result.routes[0]["policy_check_state"] = "passes_this_explicit_check"
    result.routes[0]["status"] = "candidate"
    result.routes[1]["policy_check_state"] = "fails_this_explicit_check"
    result.routes[1]["status"] = "draft"
    evaluation = DevelopmentEvaluator.evaluate(loaded.packet, result)
    assert evaluation.passed is False
    assert any("policy result mismatch" in failure for failure in evaluation.failures)

    cost_result = IntegrationPipeline(PublicCaseAdapter()).run_state(PublicCaseAdapter().load("PTP-0003", "S0")).model_copy(deep=True)
    cost_result.source_facts.append({"field": "numeric_total_batch_cost", "state": "known", "value": 999, "evidence_ids": [], "role": "source_fact"})
    cost_eval = DevelopmentEvaluator.evaluate(PublicCaseAdapter().load("PTP-0003", "S0").packet, cost_result)
    assert cost_eval.passed is False
    assert any("numeric_total_batch_cost" in failure for failure in cost_eval.failures)


def test_closed_locator_and_nested_expected_output_are_rejected():
    with pytest.raises(Exception):
        PublicEvidence.model_validate({
            "evidence_id": "E1", "text": "x", "source_id": "S", "source_locator": "S#1",
            "locator": {"dataset_field": "Abstract", "expected_output": "hidden"},
        })
    with pytest.raises(Exception):
        PublicEvidence.model_validate({
            "evidence_id": "E1", "text": "x", "source_id": "S", "source_locator": "S#1",
            "locator": {"g08_trimmed_component_offsets": {"char_start": 0, "char_end": 1, "basis": "x", "expected_output": "hidden"}},
        })


def test_declared_policy_event_conflict_is_rejected(tmp_path):
    source_root = Path(__file__).parents[1]
    payload = json.loads((source_root / "methodology" / "evaluation" / "cases" / "PTP-0001" / "public-input" / "S1.json").read_text(encoding="utf-8"))
    payload["organization_brief"]["policy"]["forbidden_materials"] = []
    case_root = tmp_path / "cases" / "PTP-0001" / "public-input"
    org_root = tmp_path / "organizations"
    case_root.mkdir(parents=True, exist_ok=True)
    (case_root / "S1.json").write_text(json.dumps(payload), encoding="utf-8")
    profile_dir = org_root / "fictional-profile-a" / "v1"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_source = source_root / "methodology" / "organizations" / "fictional-profile-a" / "v1" / "profile.json"
    (profile_dir / "profile.json").write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="event/policy conflict"):
        PublicCaseAdapter(tmp_path / "cases", org_root).load("PTP-0001", "S1")


def test_new_input_workflow_does_not_use_case_id_lookup(tmp_path):
    profile = PublicCaseAdapter()._profile("PTP-0001").model_copy(update={"record_id": "NEW-ORG-Z", "profile_id": "NEW-ORG-Z", "profile_version": "2.0.0", "organization_label": "New Lab Z"})
    states = [
        WorkflowInput(
            project_id="NEW-PROJECT-ALPHA", brief="New coating comparison", profile=profile,
            policy=PublicPolicy(rule_id="NEW-POLICY-1", component="coating", permitted_materials=["polymer-x", "polymer-y"]),
            options=[PublicOption(option_id="NEW-A", selected_component="coating", selected_material="polymer-x", evidence_ids=["NEW-E1"]), PublicOption(option_id="NEW-B", selected_component="coating", selected_material="polymer-y", evidence_ids=["NEW-E2"])],
            evidence=[PublicEvidence(evidence_id="NEW-E1", text="Polymer-X coating candidate", source_id="NEW-SOURCE", source_locator="new#1"), PublicEvidence(evidence_id="NEW-E2", text="Polymer-Y coating candidate", source_id="NEW-SOURCE", source_locator="new#2")],
            unknowns=["coating uniformity", "pilot yield"],
        ),
        WorkflowInput(
            project_id="NEW-PROJECT-ALPHA", brief="New coating comparison", profile=profile,
            policy=PublicPolicy(rule_id="NEW-POLICY-2", component="coating", permitted_materials=["polymer-x", "polymer-y"], forbidden_materials=["polymer-x"]),
            options=[PublicOption(option_id="NEW-A", selected_component="coating", selected_material="polymer-x", evidence_ids=["NEW-E1"]), PublicOption(option_id="NEW-B", selected_component="coating", selected_material="polymer-y", evidence_ids=["NEW-E2"])],
            evidence=[PublicEvidence(evidence_id="NEW-E1", text="Polymer-X coating candidate", source_id="NEW-SOURCE", source_locator="new#1"), PublicEvidence(evidence_id="NEW-E2", text="Polymer-Y coating candidate", source_id="NEW-SOURCE", source_locator="new#2")],
            event=PublicEvent(type="policy_change", event_order=1), unknowns=["coating uniformity", "pilot yield"],
        ),
    ]
    report = IntegrationPipeline().run_workflow_sequence(states)
    assert report["case_id"] == "NEW-PROJECT-ALPHA"
    assert report["states"][0]["profile_id"] == "NEW-ORG-Z"
    assert report["states"][1]["routes"][0]["policy_check_state"] == "fails_this_explicit_check"
    assert report["states"][1]["routes"][1]["policy_check_state"] == "passes_this_explicit_check"
    assert report["states"][1]["routes"][1]["status"] == "candidate"
    assert report["changes"][0]["read_back"] is True
    assert "PTP-0001" not in json.dumps(report)


def test_coordinate_contract_rejects_wrong_unit_and_span_length(tmp_path):
    source_root = Path(__file__).parents[1]
    cases_root = tmp_path / "cases"
    org_root = tmp_path / "organizations"
    case_dir = cases_root / "PTP-0002" / "public-input"
    case_dir.mkdir(parents=True)
    original = source_root / "methodology" / "evaluation" / "cases" / "PTP-0002" / "public-input" / "S0.json"
    payload = json.loads(original.read_text(encoding="utf-8"))
    payload["sources"][0]["locator"]["offset_unit"] = "bytes"
    (case_dir / "S0.json").write_text(json.dumps(payload), encoding="utf-8")
    profile_dir = org_root / "fictional-profile-b" / "v1"
    profile_dir.mkdir(parents=True)
    profile_source = source_root / "methodology" / "organizations" / "fictional-profile-b" / "v1" / "profile.json"
    (profile_dir / "profile.json").write_text(profile_source.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(ValueError, match="offset_unit"):
        PublicCaseAdapter(cases_root, org_root).load("PTP-0002", "S0")

    payload = json.loads(original.read_text(encoding="utf-8"))
    payload["sources"][1]["locator"]["char_end"] += 1
    (case_dir / "S0.json").write_text(json.dumps(payload), encoding="utf-8")
    loaded = PublicCaseAdapter(cases_root, org_root).load("PTP-0002", "S0")
    result = IntegrationPipeline(PublicCaseAdapter(cases_root, org_root)).run_state(loaded)
    assert result.source_integrity["valid"] is False
    assert set(result.source_integrity["invalid_evidence_ids"]) == {"PTP-0002-P02"}
    assert next(fact for fact in result.source_facts if fact["field"] == "PEG_role")["state"] == "known"
    pvp = next(fact for fact in result.source_facts if fact["field"] == "PVP_role")
    assert pvp["state"] == "known" and pvp["evidence_ids"] == ["PTP-0002-P03"]
    assert next(fact for fact in result.source_facts if fact["field"] == "HPMC_role")["state"] == "known"


def test_field_specific_cost_evidence_rejects_five_stage_witness():
    adapter = PublicCaseAdapter()
    loaded = adapter.load("PTP-0003", "S0")
    result = IntegrationPipeline(adapter).run_state(loaded).model_copy(deep=True)
    result.source_facts.append({"field": "numeric_total_batch_cost", "state": "known", "value": 999, "evidence_ids": ["PTP-0003-P01"], "role": "source_fact"})
    evaluated = DevelopmentEvaluator.evaluate(loaded.packet, result)
    assert evaluated.passed is False
    assert any("field-specific evidence mismatch" in failure and "numeric_total_batch_cost" in failure for failure in evaluated.failures)


@pytest.mark.parametrize(("reported_value", "expected_pass"), [(100, True), (999, False)])
def test_cost_witness_value_is_checked_through_workflow(reported_value, expected_pass):
    adapter = PublicCaseAdapter()
    loaded = adapter.load("PTP-0003", "S0")
    cost_evidence = PublicEvidence(
        evidence_id="SYN-COST-100",
        text="The total batch cost is 100 currency units.",
        source_id="synthetic-cost-source",
        source_locator="synthetic-cost-source#1",
    )
    packet = loaded.packet.model_copy(update={"evidence": [*loaded.packet.evidence, cost_evidence]})
    synthetic_loaded = type("Loaded", (), {"packet": packet, "raw": loaded.raw})()
    result = IntegrationPipeline(adapter).run_state(synthetic_loaded).model_copy(deep=True)
    cost_fact = next(fact for fact in result.source_facts if fact["field"] == "numeric_total_batch_cost")
    cost_fact.update({"state": "known", "value": reported_value, "evidence_ids": ["SYN-COST-100"], "role": "source_fact"})
    evaluated = DevelopmentEvaluator.evaluate(packet, result)
    assert evaluated.passed is expected_pass
    if not expected_pass:
        assert any("field-specific evidence mismatch" in failure for failure in evaluated.failures)


@pytest.mark.parametrize("sentence", [
    "The total batch cost was 100 USD; 999 tablets were produced.",
    "For batch 999, the total batch cost was 100 USD.",
])
@pytest.mark.parametrize(("reported_value", "expected_pass"), [(100, True), (999, False)])
def test_cost_phrase_binds_value_not_unrelated_number(sentence, reported_value, expected_pass):
    adapter = PublicCaseAdapter()
    loaded = adapter.load("PTP-0003", "S0")
    cost_evidence = PublicEvidence(
        evidence_id="SYN-COST-PHRASE", text=sentence, source_id="synthetic-cost-source", source_locator="synthetic-cost-source#phrase",
    )
    packet = loaded.packet.model_copy(update={"evidence": [*loaded.packet.evidence, cost_evidence]})
    synthetic_loaded = type("Loaded", (), {"packet": packet, "raw": loaded.raw})()
    result = IntegrationPipeline(adapter).run_state(synthetic_loaded).model_copy(deep=True)
    cost_fact = next(fact for fact in result.source_facts if fact["field"] == "numeric_total_batch_cost")
    cost_fact.update({"state": "known", "value": reported_value, "evidence_ids": ["SYN-COST-PHRASE"], "role": "source_fact"})
    evaluated = DevelopmentEvaluator.evaluate(packet, result)
    assert evaluated.passed is expected_pass
    if not expected_pass:
        assert any("field-specific evidence mismatch" in failure for failure in evaluated.failures)


def test_ambiguous_cost_phrase_is_not_supported():
    adapter = PublicCaseAdapter()
    loaded = adapter.load("PTP-0003", "S0")
    cost_evidence = PublicEvidence(
        evidence_id="SYN-COST-AMBIGUOUS",
        text="The total batch cost was 100 USD, later revised to 120 USD.",
        source_id="synthetic-cost-source",
        source_locator="synthetic-cost-source#ambiguous",
    )
    packet = loaded.packet.model_copy(update={"evidence": [*loaded.packet.evidence, cost_evidence]})
    synthetic_loaded = type("Loaded", (), {"packet": packet, "raw": loaded.raw})()
    result = IntegrationPipeline(adapter).run_state(synthetic_loaded).model_copy(deep=True)
    cost_fact = next(fact for fact in result.source_facts if fact["field"] == "numeric_total_batch_cost")
    cost_fact.update({"state": "known", "value": 100, "evidence_ids": ["SYN-COST-AMBIGUOUS"], "role": "source_fact"})
    evaluated = DevelopmentEvaluator.evaluate(packet, result)
    assert evaluated.passed is False
    assert any("field-specific evidence mismatch" in failure for failure in evaluated.failures)


@pytest.mark.parametrize("sentence", [
    "The substrate can be constructed from silicon carbide.",
    "The substrate can be constructed from silicon nitride.",
    "The substrate can be constructed from silicon oxide.",
])
def test_elemental_silicon_rule_rejects_compounds(sentence):
    packet = AgentPacket(
        case_id="PTP-0001", state_id="S0", event=PublicEvent(type="initial", event_order=0), brief="fixture",
        profile_id="PTP-FIC-ORG-A", profile_version="1.0.0",
        policy=PublicPolicy(component="substrate", permitted_materials=["silicon"]),
        options=[PublicOption(candidate_id="A", selected_component="substrate", selected_material="silicon")],
        evidence=[PublicEvidence(evidence_id="E-COMPOUND", text=sentence, source_id="fixture", source_locator="fixture#1")], unknowns=[],
    )
    loaded = type("Loaded", (), {"packet": packet, "raw": {"display_name": "fixture"}})()
    result = IntegrationPipeline().run_state(loaded)
    assert result.source_facts[0]["state"] == "unknown"
    assert result.routes[0]["policy_check_state"] == "unknown"


def test_elemental_silicon_positive_control():
    packet = AgentPacket(
        case_id="PTP-0001", state_id="S0", event=PublicEvent(type="initial", event_order=0), brief="fixture",
        profile_id="PTP-FIC-ORG-A", profile_version="1.0.0",
        policy=PublicPolicy(component="substrate", permitted_materials=["silicon"]),
        options=[PublicOption(candidate_id="A", selected_component="substrate", selected_material="silicon")],
        evidence=[PublicEvidence(evidence_id="E-SILICON", text="The substrate can be constructed from silicon.", source_id="fixture", source_locator="fixture#1")], unknowns=[],
    )
    loaded = type("Loaded", (), {"packet": packet, "raw": {"display_name": "fixture"}})()
    result = IntegrationPipeline().run_state(loaded)
    assert result.source_facts[0]["state"] == "known"
    assert result.routes[0]["policy_check_state"] == "passes_this_explicit_check"


def test_locator_is_invalid_when_canonical_span_does_not_cover_text():
    evidence = PublicEvidence.model_validate({
        "evidence_id": "E-LONG", "text": "x" * 46, "source_id": "fixture", "source_locator": "fixture#1",
        "locator": {"char_start": 0, "char_end": 1, "offset_unit": "Unicode code points, end-exclusive"},
    })
    integrity = IntegrationPipeline._integrity([evidence])
    assert integrity["valid"] is False
    assert "locator_span_length_mismatch" in integrity["reasons"]["E-LONG"]


def test_generic_policy_scope_and_unsupported_count_are_explicit_unknown():
    profile = PublicCaseAdapter()._profile("PTP-0001").model_copy(update={"record_id": "GEN-ORG", "profile_id": "GEN-ORG"})
    workflow = WorkflowInput(
        project_id="GEN-PROJECT", brief="synthetic", profile=profile,
        policy=PublicPolicy(rule_id="GEN-POLICY", component="substrate", count_kind="count", operator="between"),
        options=[PublicOption(option_id="O1", selected_component="coating", selected_material="polymer", evidence_ids=["E1"])],
        evidence=[PublicEvidence(evidence_id="E1", text="A polymer coating candidate.", source_id="S", source_locator="S#1")],
    )
    result = IntegrationPipeline().run_workflow(workflow)
    route = result.routes[0]
    assert route["policy_check_state"] == "unknown"
    assert route["policy_scope_status"] == "unknown"
    assert any("does not match" in reason for reason in route["policy_reasons"])
    assert any("unsupported count policy form" in reason for reason in route["policy_reasons"])


def test_generic_revision_gap_uses_stored_sqlite_versions():
    profile = PublicCaseAdapter()._profile("PTP-0001").model_copy(update={"record_id": "GAP-ORG", "profile_id": "GAP-ORG"})
    def workflow(order, forbidden=()):
        return WorkflowInput(
            project_id="GAP-PROJECT", brief="synthetic", profile=profile,
            policy=PublicPolicy(rule_id=f"POLICY-{order}", component="coating", forbidden_materials=list(forbidden)),
            options=[PublicOption(option_id="O1", selected_component="coating", selected_material="polymer", evidence_ids=["E1"])],
            evidence=[PublicEvidence(evidence_id="E1", text="A polymer coating candidate.", source_id="S", source_locator="S#1")],
            event=PublicEvent(type="initial" if order == 0 else "policy_change", event_order=order),
        )
    report = IntegrationPipeline().run_workflow_sequence([workflow(0), workflow(3, ("polymer",))])
    change = report["changes"][0]
    assert change["before_version"] == 1 and change["after_version"] == 2
    assert change["route_history_versions"] == [1, 2]


def test_generic_profile_excludes_evaluator_fields_but_preserves_allowed_context():
    profile = PublicCaseAdapter()._profile("PTP-0001").model_copy(deep=True)
    profile.public_source_context["gold_answer"] = {"hidden": True}
    with pytest.raises(ValueError, match="forbidden evaluator field"):
        WorkflowInput(
            project_id="PROFILE-GUARD", brief="synthetic", profile=profile,
            policy=PublicPolicy(component="coating"),
            options=[PublicOption(option_id="O1", selected_component="coating", selected_material="polymer")],
        )
    allowed = PublicCaseAdapter()._profile("PTP-0001").model_copy(deep=True)
    workflow = WorkflowInput(
        project_id="PROFILE-OK", brief="synthetic", profile=allowed,
        policy=PublicPolicy(component="coating"),
        options=[PublicOption(option_id="O1", selected_component="coating", selected_material="polymer")],
    )
    assert workflow.profile.public_source_context["source_ref"] == "ORG-SRC-NCATS-TRND-2023"


def test_invalid_evidence_and_prohibited_option_complete_generic_workflow():
    profile = PublicCaseAdapter()._profile("PTP-0001").model_copy(update={"record_id": "INVALID-ORG", "profile_id": "INVALID-ORG"})
    workflow = WorkflowInput(
        project_id="INVALID-EVIDENCE-PROJECT", brief="synthetic route isolation", profile=profile,
        policy=PublicPolicy(rule_id="INVALID-POLICY", component="coating", forbidden_materials=["polymer-x"]),
        options=[
            PublicOption(option_id="FORBIDDEN", selected_component="coating", selected_material="polymer-x", evidence_ids=["BAD-EVIDENCE"]),
            PublicOption(option_id="UNRELATED", selected_component="coating", selected_material="polymer-y", evidence_ids=["GOOD-EVIDENCE"]),
        ],
        evidence=[
            PublicEvidence(evidence_id="BAD-EVIDENCE", text="Polymer-X coating candidate.", source_id="SYN-SOURCE", source_locator="SYN-SOURCE#bad", text_sha256="not-the-real-hash"),
            PublicEvidence(evidence_id="GOOD-EVIDENCE", text="Polymer-Y coating candidate.", source_id="SYN-SOURCE", source_locator="SYN-SOURCE#good"),
        ],
    )
    report = IntegrationPipeline().run_workflow_sequence([workflow])
    routes = {route["route_id"]: route for route in report["states"][0]["routes"]}
    assert routes["INVALID-EVIDENCE-PROJECT:FORBIDDEN"]["policy_check_state"] == "fails_this_explicit_check"
    assert routes["INVALID-EVIDENCE-PROJECT:UNRELATED"]["policy_check_state"] == "passes_this_explicit_check"
    assert report["states"][0]["source_integrity"]["invalid_evidence_ids"] == ["BAD-EVIDENCE"]
    assert report["states"][0]["handoff"]["status"] == "draft"


def test_generic_event_policy_rule_mismatch_is_rejected():
    profile = PublicCaseAdapter()._profile("PTP-0001").model_copy(update={"record_id": "EVENT-ORG", "profile_id": "EVENT-ORG"})
    with pytest.raises(ValueError, match="event/policy conflict"):
        WorkflowInput(
            project_id="EVENT-PROJECT", brief="synthetic", profile=profile,
            policy=PublicPolicy(rule_id="POLICY-A", component="coating"),
            options=[PublicOption(option_id="O1", selected_component="coating", selected_material="polymer")],
            event=PublicEvent(type="policy_change", event_order=3, policy_rule_id="POLICY-B"),
        )
