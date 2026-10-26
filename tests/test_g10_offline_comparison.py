from dataclasses import replace

import pytest

from patent_to_pilot.evaluation.comparison import (
    IntegrationPipeline,
    MockProvider,
    OfflineComparisonRunner,
    PublicCaseAdapter,
    _runtime_output,
    stage_loaded_case,
    stage_public_states,
    validate_runtime_output,
    validate_public_packet,
    validate_public_schema,
)


def test_offline_comparison_runs_public_slice_and_separates_b4_rg():
    report = OfflineComparisonRunner().run()

    assert report["status"] == "PASS"
    assert report["case_id"] == "PTP-0001"
    assert report["state_ids"] == ["S0", "S1", "S2"]
    assert set(report["methods"]) == {
        "B0_rules_only",
        "B1_full_regeneration",
        "B2_direct_revision",
        "B3_invalidation_same_generator",
        "P_existing_workflow",
    }
    assert all(method["status"] == "PASS" for method in report["methods"].values())
    assert report["b4_rg"] == {
        "implementation": "NOT_IMPLEMENTED",
        "readiness": "POOL_NOT_READY",
        "execution": "NOT_RUN",
        "reason": "This public case has no verified distractor/recoverable-evidence pool for adaptive-search comparison.",
    }
    assert report["search_readiness"]["status"] == "POOL_NOT_READY"
    assert "scientific pilot" in report["status_register"]["NOT_RUN"]


def test_noop_revision_preserves_unchanged_fields_for_all_methods():
    report = OfflineComparisonRunner().run()

    for method in report["methods"].values():
        state = next(item for item in method["states"] if item["state_id"] == "S2")
        assert state["status"] == "PASS"
        assert state["before_after_diff"]["affected_fields"] == []
        assert "routes" in state["before_after_diff"]["preserved_fields"]
        assert "source_facts" in state["before_after_diff"]["preserved_fields"]


def test_policy_revision_changes_only_publicly_allowed_fields():
    report = OfflineComparisonRunner().run()
    allowed = {"fictional_stipulations", "options", "routes"}

    for method in report["methods"].values():
        state = next(item for item in method["states"] if item["state_id"] == "S1")
        assert set(state["before_after_diff"]["affected_fields"]) <= allowed
        assert "source_facts" in state["before_after_diff"]["preserved_fields"]


def test_all_methods_share_identical_staged_input_schema_and_validator_contract():
    report = OfflineComparisonRunner().run()
    staging = {item["state_id"]: item for item in report["staging"]}

    for method_id, method in report["methods"].items():
        for call in method["provider_calls"]:
            staged = staging[call["state_id"]]
            assert call["input_sha256"] == staged["input_sha256"], method_id
            assert call["schema_sha256"] == staged["schema_sha256"], method_id
            assert call["runtime_contract_sha256"] == staged["runtime_contract_sha256"], method_id
            assert call["validator_sha256"] == staged["validator_sha256"], method_id

    assert report["methods"]["B0_rules_only"]["provider_calls"] == []
    assert report["methods"]["P_existing_workflow"]["provider_calls"] == []
    assert len(report["methods"]["B1_full_regeneration"]["provider_calls"]) == 3
    assert [call["metadata"]["generation_scope"] for call in report["methods"]["B2_direct_revision"]["provider_calls"]] == [
        "full_generation_for_initial_state",
        "direct_revision",
        "direct_revision",
    ]
    assert [call["metadata"]["generation_scope"] for call in report["methods"]["B3_invalidation_same_generator"]["provider_calls"]] == [
        "full_then_scoped_merge",
        "full_then_scoped_merge",
        "full_then_scoped_merge",
    ]


def test_mock_provider_failure_is_retained_without_retry_or_network():
    provider = MockProvider({"B1_full_regeneration:S1": "timeout"})
    report = OfflineComparisonRunner(provider=provider).run()
    method = report["methods"]["B1_full_regeneration"]

    assert method["status"] == "FAIL"
    assert method["states"][1]["status"] == "FAIL"
    assert method["failure_traces"][0]["failure_mode"] == "timeout"
    assert method["failure_traces"][0]["retry_count"] == 0
    assert report["accounting"]["network_calls_declared"] == 0
    assert report["accounting"]["network_observation"] == "NOT_MEASURED"
    assert report["accounting"]["failure_traces"][0]["state_id"] == "S1"


def test_invalid_schema_and_evaluator_only_input_fail_closed():
    with pytest.raises(ValueError, match="required_top_level"):
        validate_public_schema({"schema_version": "x", "required_option_fields": ["candidate_id"], "policy_states": ["unknown"]})

    with pytest.raises(ValueError, match="evaluator-only"):
        validate_public_packet({"input_boundary": "public-input-only", "expected_answers": {"hidden": True}})

    with pytest.raises(ValueError, match="public-input-only"):
        validate_public_packet({"input_boundary": "evaluator-input"})


def test_existing_workflow_uses_only_staged_states(monkeypatch):
    runner = OfflineComparisonRunner()

    def fail_run_case(*_args, **_kwargs):
        raise AssertionError("run_case must not be called by the bounded wrapper")

    monkeypatch.setattr(runner.pipeline, "run_case", fail_run_case)
    report = runner.run()

    assert report["status"] == "PASS"
    evidence = report["methods"]["P_existing_workflow"]["existing_workflow_evidence"]
    assert evidence["staged_state_ids"] == ["S0", "S1", "S2"]
    assert evidence["staged_state_count"] == 3
    assert evidence["run_case_called"] is False


def test_custom_staged_packet_changes_bounded_result():
    base_stage = stage_public_states(state_ids=("S0",))[0]
    custom_packet = base_stage.loaded.packet.model_copy(update={"brief": "custom staged brief"})
    custom_loaded = replace(base_stage.loaded, packet=custom_packet)
    custom_stage = stage_loaded_case(custom_loaded, base_stage.schema)

    report = OfflineComparisonRunner(stages=[custom_stage]).run()
    output = report["methods"]["P_existing_workflow"]["states"][0]["output"]

    assert output["brief"] == "custom staged brief"
    assert custom_stage.input_sha256 != base_stage.input_sha256


def test_runtime_output_contract_accepts_normal_mapped_output():
    stage = stage_public_states(state_ids=("S0",))[0]
    result = IntegrationPipeline().run_state(stage.loaded)
    output = _runtime_output(stage, result)

    validation = validate_runtime_output(stage, output)

    assert validation["passed"] is True
    assert validation["failures"] == []


def test_runtime_output_missing_required_field_fails_with_json_path():
    stage = stage_public_states(state_ids=("S0",))[0]
    result = IntegrationPipeline().run_state(stage.loaded)
    output = _runtime_output(stage, result)
    output.pop("event_id")

    validation = validate_runtime_output(stage, output)

    assert validation["passed"] is False
    assert "$ missing required field: event_id" in validation["failures"]


def test_runtime_output_rejects_invalid_policy_state():
    stage = stage_public_states(state_ids=("S0",))[0]
    result = IntegrationPipeline().run_state(stage.loaded)
    output = _runtime_output(stage, result)
    output["options"][0]["policy_check_state"] = "invalid_policy_state"

    validation = validate_runtime_output(stage, output)

    assert validation["passed"] is False
    assert "declared policy state" in " ".join(validation["failures"])


def test_runtime_output_rejects_option_evidence_mismatch():
    stage = stage_public_states(state_ids=("S0",))[0]
    result = IntegrationPipeline().run_state(stage.loaded)
    output = _runtime_output(stage, result)
    output["options"][0]["current_support_ids"] = ["evidence-not-in-packet"]

    validation = validate_runtime_output(stage, output)

    assert validation["passed"] is False
    assert "unknown evidence ID" in " ".join(validation["failures"])


def test_runtime_output_rejects_numeric_value_for_unknown_measurement():
    stage = stage_public_states(state_ids=("S0",))[0]
    result = IntegrationPipeline().run_state(stage.loaded)
    output = _runtime_output(stage, result)
    output["options"][0]["measured_production_yield"] = {"state": "unknown", "value": 0}

    validation = validate_runtime_output(stage, output)

    assert validation["passed"] is False
    assert "explicit unknown measurement shape" in " ".join(validation["failures"])


def test_shape_valid_but_domain_invalid_output_fails_overall():
    stage = stage_public_states(state_ids=("S1",))[0]
    result = IntegrationPipeline().run_state(stage.loaded).model_copy(deep=True)
    result.routes[0]["policy_check_state"] = "passes_this_explicit_check"
    result.routes[0]["status"] = "candidate"
    runner = OfflineComparisonRunner(stages=[stage])

    state = runner._record_state(stage=stage, result=result, previous=None)

    assert state["execution_status"] == "PASS"
    assert state["validation_status"] == "FAIL"
    assert state["validator"]["runtime_output_validation"]["passed"] is True
    assert state["validator"]["development_evaluator"]["passed"] is False


def test_comparison_persistence_is_explicitly_not_run():
    report = OfflineComparisonRunner().run()

    for method in report["methods"].values():
        for state in method["states"]:
            if state["validator"] is None:
                continue
            assert state["validator"]["persistence"]["status"] == "NOT_RUN"
            assert state["validator"]["development_evaluator"]["sqlite_payload_read_back"] is False
            assert "SQLite route payload/status read-back failed" not in state["validator"]["development_evaluator"]["failures"]


def test_timeout_counts_once_as_failed_attempt_and_failed_state():
    provider = MockProvider({"B1_full_regeneration:S1": "timeout"})
    report = OfflineComparisonRunner(provider=provider).run()
    method = report["methods"]["B1_full_regeneration"]

    assert method["metrics"]["failed_attempt_count"] == 1
    assert method["metrics"]["failed_state_count"] == 1
    assert method["metrics"]["validation_failure_count"] == 0
    assert method["states"][1]["execution_status"] == "FAIL"
    assert method["states"][1]["validation_status"] == "NOT_RUN"
    assert len([call for call in method["provider_calls"] if call["status"] == "FAIL"]) == 1


def test_generator_exception_is_retained_and_report_returns():
    class ThrowingProvider(MockProvider):
        def call(self, **kwargs):
            if kwargs["method_id"] == "B1_full_regeneration" and kwargs["stage"].packet.state_id == "S1":
                def explode():
                    raise RuntimeError("generator boom")

                kwargs = dict(kwargs)
                kwargs["generate"] = explode
            return super().call(**kwargs)

    report = OfflineComparisonRunner(provider=ThrowingProvider()).run()
    method = report["methods"]["B1_full_regeneration"]
    trace = next(item for item in method["failure_traces"] if item["state_id"] == "S1")

    assert report["status"] == "FAIL"
    assert trace["failure_mode"] == "exception"
    assert "generator boom" in trace["error"]


def test_malformed_output_fails_runtime_validation_and_method_status():
    provider = MockProvider({"B1_full_regeneration:S1": "malformed"})
    report = OfflineComparisonRunner(provider=provider).run()
    method = report["methods"]["B1_full_regeneration"]
    state = method["states"][1]

    assert report["status"] == "FAIL"
    assert method["status"] == "FAIL"
    assert state["execution_status"] == "PASS"
    assert state["validation_status"] == "FAIL"
    assert state["validator"]["runtime_output_validation"]["passed"] is False


def test_dependent_revision_state_is_skipped_without_provider_call():
    provider = MockProvider({"B2_direct_revision:S1": "timeout"})
    report = OfflineComparisonRunner(provider=provider).run()
    method = report["methods"]["B2_direct_revision"]
    skipped = method["states"][2]

    assert skipped["execution_status"] == "SKIPPED"
    assert skipped["status"] == "SKIPPED"
    assert skipped["validation_status"] == "NOT_RUN"
    assert method["metrics"]["dependent_skip_count"] == 1
    assert all(call["state_id"] != "S2" for call in method["provider_calls"])


def test_public_profile_changes_input_hash():
    base_stage = stage_public_states(state_ids=("S0",))[0]
    changed_profile = base_stage.loaded.profile.model_copy(update={"status": "CUSTOM_STATUS_FOR_HASH_TEST"})
    changed_loaded = replace(base_stage.loaded, profile=changed_profile)
    changed_stage = stage_loaded_case(changed_loaded, base_stage.schema)

    assert changed_stage.input_sha256 != base_stage.input_sha256
