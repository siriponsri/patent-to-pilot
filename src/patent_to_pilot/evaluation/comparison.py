"""Bounded offline comparison slice for the public PTP-0001 packet.

The runner compares deterministic and mock-provider mechanics only. It never
opens evaluator-only files, calls a network provider, or treats this slice as
a scientific benchmark.
"""

from __future__ import annotations

import copy
import hashlib
import html
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from patent_to_pilot.integration.pipeline import (
    AgentPacket,
    DevelopmentEvaluator,
    IntegrationPipeline,
    IntegrationResult,
    LoadedCase,
    PublicCaseAdapter,
    WorkflowInput,
)


ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CASE_ID = "PTP-0001"
DEFAULT_STATE_IDS = ("S0", "S1", "S2")
COMPARISON_METHODS = (
    "B0_rules_only",
    "B1_full_regeneration",
    "B2_direct_revision",
    "B3_invalidation_same_generator",
    "P_existing_workflow",
)
FORBIDDEN_INPUT_KEYS = {
    "expected_doc_ids",
    "expected_documents",
    "expected_answer",
    "expected_answers",
    "gold_answer",
    "answer_facts",
    "oracle",
    "oracle_output",
    "hidden_facts",
    "checked_facts",
    "evaluator_only",
    "evaluator-only",
    "expected_output",
    "future_events",
}
METADATA_FIELDS = {"case_id", "state_id", "project_display_name", "brief", "profile_id", "profile_version"}
RUNTIME_OUTPUT_CONTRACT = {
    "name": "ptp-0001-comparison-view-v1",
    "source_schema_version": "PTP-0001-output-v1",
    "required_top_level": [
        "case_id",
        "event_id",
        "display_name",
        "options",
        "source_ambiguity_status",
        "interpretation_limits",
    ],
    "required_option_fields": [
        "candidate_id",
        "component",
        "selected_material",
        "policy_check_state",
        "current_support_ids",
        "historical_support_ids",
        "measured_production_yield",
        "final_needle_material",
        "next_action_code",
    ],
    "policy_states": ["passes_this_explicit_check", "fails_this_explicit_check", "unknown"],
    "unknown_measurement": {"state": "unknown", "value": None},
    "historical_support_status": "not_supplied_in_public_packet",
}
VALIDATOR_CONTRACT = {
    "name": "ptp-development-evaluator",
    "version": "comparison-v1",
    "checks": [
        "public state identity",
        "required policy change",
        "unchanged-field preservation",
        "unknown handling",
        "route-local status",
        "source integrity and field-specific evidence",
        "typed state transition read-back where available",
    ],
    "evaluator_material_excluded_from_method_input": True,
    "runtime_output_contract": RUNTIME_OUTPUT_CONTRACT,
}


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_json(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _forbidden_paths(value: Any, path: str = "$") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).casefold() in {item.casefold() for item in FORBIDDEN_INPUT_KEYS}:
                found.append(f"{path}.{key}")
            found.extend(_forbidden_paths(nested, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            found.extend(_forbidden_paths(nested, f"{path}[{index}]"))
    return found


def validate_public_packet(packet_payload: Mapping[str, Any]) -> None:
    """Fail closed when evaluator-only keys appear in a method packet."""

    forbidden = _forbidden_paths(dict(packet_payload))
    if forbidden:
        raise ValueError(f"evaluator-only input field(s) are not permitted: {', '.join(forbidden)}")
    if packet_payload.get("input_boundary") != "public-input-only":
        raise ValueError("comparison packets must declare the public-input-only boundary")


def validate_public_profile(profile_payload: Mapping[str, Any]) -> None:
    """Reject evaluator-only content in the organization profile contract."""

    forbidden = _forbidden_paths(dict(profile_payload), "$.profile")
    if forbidden:
        raise ValueError(f"evaluator-only profile field(s) are not permitted: {', '.join(forbidden)}")


def validate_public_schema(schema: Mapping[str, Any]) -> None:
    """Reject incomplete output schemas before staging a comparison."""

    if not isinstance(schema, Mapping):
        raise ValueError("public output schema must be an object")
    required_top_level = schema.get("required_top_level")
    required_option_fields = schema.get("required_option_fields")
    policy_states = schema.get("policy_states")
    if not schema.get("schema_version"):
        raise ValueError("public output schema must declare schema_version")
    if not isinstance(required_top_level, list) or not required_top_level:
        raise ValueError("public output schema must declare required_top_level")
    if not isinstance(required_option_fields, list) or not required_option_fields:
        raise ValueError("public output schema must declare required_option_fields")
    if not isinstance(policy_states, list) or not policy_states:
        raise ValueError("public output schema must declare policy_states")


@dataclass(frozen=True)
class StagedInput:
    """Public packet plus identical schema and validator contracts."""

    loaded: LoadedCase
    schema: dict[str, Any]
    validator_contract: dict[str, Any]
    input_payload: dict[str, Any]
    input_sha256: str
    schema_sha256: str
    runtime_contract: dict[str, Any]
    runtime_contract_sha256: str
    validator_sha256: str

    @property
    def packet(self) -> AgentPacket:
        return self.loaded.packet


@dataclass(frozen=True)
class ProviderCall:
    call_id: str
    method_id: str
    state_id: str
    operation: str
    input_sha256: str
    schema_sha256: str
    runtime_contract_sha256: str
    validator_sha256: str
    status: str
    failure_mode: str | None
    error: str | None
    retry_count: int
    cost_usd: float
    elapsed_ms: float
    metadata: dict[str, Any]


class MockProviderFailure(RuntimeError):
    """Controlled provider failure used only for offline failure-path tests."""

    def __init__(self, message: str, trace: ProviderCall) -> None:
        super().__init__(message)
        self.trace = trace


class MockProvider:
    """Deterministic provider seam with explicit call and failure records."""

    def __init__(self, failure_plan: Mapping[str, str] | None = None) -> None:
        self.failure_plan = dict(failure_plan or {})
        self.calls: list[ProviderCall] = []

    def call(
        self,
        *,
        method_id: str,
        stage: StagedInput,
        operation: str,
        generate: Callable[[], IntegrationResult],
        metadata: Mapping[str, Any] | None = None,
    ) -> IntegrationResult:
        started = time.perf_counter()
        key = f"{method_id}:{stage.packet.state_id}"
        failure_mode = self.failure_plan.get(key)
        call_id = f"{method_id}:{stage.packet.state_id}:{len(self.calls) + 1}"
        if failure_mode is not None and failure_mode not in {"error", "timeout", "malformed"}:
            raise ValueError(f"unsupported mock failure mode: {failure_mode}")
        if failure_mode in {"error", "timeout"}:
            elapsed_ms = (time.perf_counter() - started) * 1000
            trace = ProviderCall(
                call_id=call_id,
                method_id=method_id,
                state_id=stage.packet.state_id,
                operation=operation,
                input_sha256=stage.input_sha256,
                schema_sha256=stage.schema_sha256,
                runtime_contract_sha256=stage.runtime_contract_sha256,
                validator_sha256=stage.validator_sha256,
                status="FAIL",
                failure_mode=failure_mode,
                error=f"mock provider {failure_mode}",
                retry_count=0,
                cost_usd=0.0,
                elapsed_ms=elapsed_ms,
                metadata=dict(metadata or {}),
            )
            self.calls.append(trace)
            raise MockProviderFailure(trace.error or "mock provider failure", trace)
        try:
            result = generate()
        except Exception as exc:  # noqa: BLE001 - retain a safe, bounded trace for the offline seam
            elapsed_ms = (time.perf_counter() - started) * 1000
            trace = ProviderCall(
                call_id=call_id,
                method_id=method_id,
                state_id=stage.packet.state_id,
                operation=operation,
                input_sha256=stage.input_sha256,
                schema_sha256=stage.schema_sha256,
                runtime_contract_sha256=stage.runtime_contract_sha256,
                validator_sha256=stage.validator_sha256,
                status="FAIL",
                failure_mode="exception",
                error=f"{type(exc).__name__}: {str(exc)[:240]}",
                retry_count=0,
                cost_usd=0.0,
                elapsed_ms=elapsed_ms,
                metadata=dict(metadata or {}),
            )
            self.calls.append(trace)
            raise MockProviderFailure(trace.error or "mock generator exception", trace) from exc
        call_metadata = dict(metadata or {})
        if failure_mode == "malformed":
            result = result.model_copy(deep=True)
            if result.routes:
                result.routes[0]["policy_check_state"] = "invalid_policy_state"
            call_metadata["output_mutation"] = "invalid_policy_state"
        elapsed_ms = (time.perf_counter() - started) * 1000
        self.calls.append(
            ProviderCall(
                call_id=call_id,
                method_id=method_id,
                state_id=stage.packet.state_id,
                operation=operation,
                input_sha256=stage.input_sha256,
                schema_sha256=stage.schema_sha256,
                runtime_contract_sha256=stage.runtime_contract_sha256,
                validator_sha256=stage.validator_sha256,
                status="PASS",
                failure_mode=None,
                error=None,
                retry_count=0,
                cost_usd=0.0,
                elapsed_ms=elapsed_ms,
                metadata=call_metadata,
            )
        )
        return result


def _schema_for(adapter: PublicCaseAdapter, case_id: str) -> dict[str, Any]:
    path = (adapter.cases_root / case_id / "public-input" / "output-schema.json").resolve()
    expected_parent = (adapter.cases_root / case_id / "public-input").resolve()
    if path.parent != expected_parent or not path.is_file():
        raise ValueError("public output schema is missing or outside the public-input directory")
    schema = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError("public output schema is incomplete")
    validate_public_schema(schema)
    return schema


def stage_loaded_case(loaded: LoadedCase, schema: dict[str, Any]) -> StagedInput:
    """Stage one already-loaded public case without consulting other states."""

    validate_public_schema(schema)
    packet_payload = loaded.packet.model_dump(mode="json")
    profile_payload = loaded.profile.model_dump(mode="json")
    validate_public_packet(packet_payload)
    validate_public_profile(profile_payload)
    runtime_contract = copy.deepcopy(RUNTIME_OUTPUT_CONTRACT)
    validator_contract = copy.deepcopy(VALIDATOR_CONTRACT)
    input_payload = {"packet": packet_payload, "profile": profile_payload}
    return StagedInput(
        loaded=loaded,
        schema=copy.deepcopy(schema),
        validator_contract=validator_contract,
        input_payload=input_payload,
        input_sha256=_sha256_json(input_payload),
        schema_sha256=_sha256_json(schema),
        runtime_contract=runtime_contract,
        runtime_contract_sha256=_sha256_json(runtime_contract),
        validator_sha256=_sha256_json(validator_contract),
    )


def stage_public_states(
    case_id: str = DEFAULT_CASE_ID,
    state_ids: tuple[str, ...] = DEFAULT_STATE_IDS,
    adapter: PublicCaseAdapter | None = None,
) -> list[StagedInput]:
    """Load only the requested public states and stage identical contracts."""

    if not state_ids:
        raise ValueError("at least one public state is required")
    adapter = adapter or PublicCaseAdapter()
    schema = _schema_for(adapter, case_id)
    return [stage_loaded_case(adapter.load(case_id, state_id), schema) for state_id in state_ids]


def _workflow_from_stage(stage: StagedInput) -> WorkflowInput:
    packet = stage.packet
    return WorkflowInput(
        project_id=packet.case_id,
        brief=packet.brief,
        profile=stage.loaded.profile,
        policy=packet.policy,
        options=packet.options,
        evidence=packet.evidence,
        event=packet.event,
        unknowns=packet.unknowns if isinstance(packet.unknowns, list) else [packet.unknowns],
    )


def _unknown_measurement() -> dict[str, Any]:
    return copy.deepcopy(RUNTIME_OUTPUT_CONTRACT["unknown_measurement"])


def _runtime_output(stage: StagedInput, result: IntegrationResult) -> dict[str, Any]:
    packet = stage.packet
    routes_by_option = {
        route["route_id"].rsplit(":", 1)[-1]: route
        for route in result.routes
    }
    options: list[dict[str, Any]] = []
    for option in packet.options:
        candidate_id = option.option_id or option.candidate_id or "unknown"
        route = routes_by_option.get(candidate_id, {})
        options.append(
            {
                "candidate_id": candidate_id,
                "component": option.selected_component or packet.policy.component or "unknown",
                "selected_material": option.selected_material or "unknown",
                "policy_check_state": route.get("policy_check_state", "unknown"),
                "current_support_ids": list(route.get("evidence_ids", [])),
                "historical_support_ids": [],
                "measured_production_yield": _unknown_measurement(),
                "final_needle_material": _unknown_measurement(),
                "next_action_code": "measure_unresolved_fields",
            }
        )
    return {
        "case_id": result.case_id,
        "event_id": packet.state_id,
        "display_name": result.project_display_name,
        "options": options,
        "source_ambiguity_status": "not_evaluated_in_bounded_runtime_contract",
        "interpretation_limits": [
            item["statement"] for item in result.interpretations
        ] + ["This mapping validates structure and explicit states only."],
    }


def validate_runtime_output(stage: StagedInput, output: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the actual comparison view mapped from IntegrationResult."""

    failures: list[str] = []
    required_top_level = stage.runtime_contract["required_top_level"]
    required_option_fields = stage.runtime_contract["required_option_fields"]
    policy_states = set(stage.runtime_contract["policy_states"])
    unknown_measurement = stage.runtime_contract["unknown_measurement"]
    for field in required_top_level:
        if field not in output:
            failures.append(f"$ missing required field: {field}")
    if output.get("case_id") != stage.packet.case_id:
        failures.append("$.case_id does not match staged packet")
    if output.get("event_id") != stage.packet.state_id:
        failures.append("$.event_id does not match staged packet")
    for field in ("case_id", "event_id", "display_name", "source_ambiguity_status"):
        if field in output and not isinstance(output[field], str):
            failures.append(f"$.{field} must be a string")
    if not isinstance(output.get("interpretation_limits"), list) or not all(isinstance(item, str) and item for item in output.get("interpretation_limits", [])):
        failures.append("$.interpretation_limits must be a non-empty string list")
    raw_options = output.get("options")
    if not isinstance(raw_options, list) or not raw_options:
        failures.append("$.options must be a non-empty list")
        raw_options = []
    expected_ids = [option.option_id or option.candidate_id or "unknown" for option in stage.packet.options]
    actual_ids = [item.get("candidate_id") for item in raw_options if isinstance(item, dict)]
    if actual_ids != expected_ids:
        failures.append(f"$.options candidate IDs do not match staged packet: expected {expected_ids}, got {actual_ids}")
    evidence_ids = {item.evidence_id for item in stage.packet.evidence}
    for index, option in enumerate(raw_options):
        path = f"$.options[{index}]"
        if not isinstance(option, dict):
            failures.append(f"{path} must be an object")
            continue
        for field in required_option_fields:
            if field not in option:
                failures.append(f"{path}.{field} is required")
        for field in ("candidate_id", "component", "selected_material", "next_action_code"):
            if field in option and (not isinstance(option[field], str) or not option[field]):
                failures.append(f"{path}.{field} must be a non-empty string")
        if option.get("policy_check_state") not in policy_states:
            failures.append(f"{path}.policy_check_state is not a declared policy state")
        for field in ("current_support_ids", "historical_support_ids"):
            values = option.get(field)
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                failures.append(f"{path}.{field} must be a string list")
            elif field == "current_support_ids" and not set(values).issubset(evidence_ids):
                failures.append(f"{path}.{field} contains an unknown evidence ID")
        for field in ("measured_production_yield", "final_needle_material"):
            if option.get(field) != unknown_measurement:
                failures.append(f"{path}.{field} must remain the explicit unknown measurement shape")
    return {
        "passed": not failures,
        "failures": failures,
        "output_sha256": _sha256_json(dict(output)),
        "contract_name": stage.runtime_contract["name"],
        "contract_sha256": stage.runtime_contract_sha256,
    }


def _diff_results(before: IntegrationResult, after: IntegrationResult) -> dict[str, Any]:
    before_payload = before.model_dump(mode="json")
    after_payload = after.model_dump(mode="json")
    affected: list[str] = []
    preserved: list[str] = []
    fields: dict[str, dict[str, Any]] = {}
    for field in sorted(set(before_payload) | set(after_payload)):
        if field in {"state_id", "project_display_name"}:
            continue
        before_value = before_payload.get(field)
        after_value = after_payload.get(field)
        if before_value == after_value:
            preserved.append(field)
        else:
            affected.append(field)
            fields[field] = {"before": before_value, "after": after_value}
    return {"affected_fields": affected, "preserved_fields": preserved, "fields": fields}


def _allowed_changed_fields(event_type: str) -> set[str]:
    if event_type == "project_name_only":
        return set()
    if event_type == "forbid_silicon_substrate":
        return {"fictional_stipulations", "options", "routes"}
    return {"fictional_stipulations", "options", "routes", "source_facts", "unknowns", "handoff"}


def _merge_revision(previous: IntegrationResult, regenerated: IntegrationResult, fields: set[str]) -> IntegrationResult:
    updates = {field: copy.deepcopy(getattr(regenerated, field)) for field in fields | METADATA_FIELDS}
    return previous.model_copy(update=updates, deep=True)


def _invalidation_fields(stage: StagedInput, previous: IntegrationResult | None) -> set[str]:
    if previous is None:
        return set(IntegrationResult.model_fields) - {"mock_provider_called"}
    return _allowed_changed_fields(stage.packet.event.type)


def _validator_record(stage: StagedInput, result: IntegrationResult, previous: IntegrationResult | None) -> dict[str, Any]:
    runtime_output = _runtime_output(stage, result)
    runtime_validation = validate_runtime_output(stage, runtime_output)
    try:
        evaluation = DevelopmentEvaluator.evaluate(
            stage.packet,
            result,
            previous,
            sqlite_payload_read_back=False,
        )
        evaluation_payload = evaluation.model_dump(mode="json")
    except Exception as exc:  # noqa: BLE001 - malformed outputs must become validation failures
        evaluation_payload = {
            "passed": False,
            "required_changes": False,
            "preservation": False,
            "unknown_handling": False,
            "route_local_status": False,
            "sqlite_payload_read_back": False,
            "failures": [f"domain validator exception: {type(exc).__name__}: {str(exc)[:240]}"],
        }
    synthetic_persistence_failure = "SQLite route payload/status read-back failed"
    domain_failures = [
        failure
        for failure in evaluation_payload.get("failures", [])
        if failure != synthetic_persistence_failure
    ]
    domain_evaluation = {
        **evaluation_payload,
        "passed": not domain_failures,
        "failures": domain_failures,
    }
    diff = _diff_results(previous, result) if previous is not None else None
    allowed = _allowed_changed_fields(stage.packet.event.type) if previous is not None else set()
    unexpected = [] if diff is None else sorted(set(diff["affected_fields"]) - allowed)
    before_after_passed = diff is None or not unexpected
    return {
        "passed": runtime_validation["passed"] and domain_evaluation["passed"] and before_after_passed,
        "development_evaluator": domain_evaluation,
        "runtime_output": runtime_output,
        "runtime_output_validation": runtime_validation,
        "persistence": {
            "status": "NOT_RUN",
            "reason": "comparison methods do not persist IntegrationResult",
            "durability": "NOT_APPLICABLE",
        },
        "before_after_contract": {
            "allowed_changed_fields": sorted(allowed),
            "unexpected_changed_fields": unexpected,
            "preservation_checked": before_after_passed,
            "diff": diff,
        },
        "public_schema": {
            "schema_version": stage.schema["schema_version"],
            "schema_sha256": stage.schema_sha256,
            "available_to_method": True,
        },
        "same_validator_contract": stage.validator_sha256,
    }


class OfflineComparisonRunner:
    """Run the bounded comparison without network or paid model calls."""

    def __init__(
        self,
        stages: list[StagedInput] | None = None,
        pipeline: IntegrationPipeline | None = None,
        provider: MockProvider | None = None,
        run_id: str = "g10-correctness-search-2026-10-27-r1",
    ) -> None:
        self.stages = stages or stage_public_states()
        if len(self.stages) < 1:
            raise ValueError("comparison requires at least one staged state")
        self.pipeline = pipeline or IntegrationPipeline()
        self.provider = provider or MockProvider()
        self.run_id = run_id

    def _record_state(
        self,
        *,
        stage: StagedInput,
        result: IntegrationResult | None,
        previous: IntegrationResult | None,
        failure: str | None = None,
        execution_status: str = "PASS",
    ) -> dict[str, Any]:
        state: dict[str, Any] = {
            "state_id": stage.packet.state_id,
            "event_type": stage.packet.event.type,
            "input_sha256": stage.input_sha256,
            "schema_sha256": stage.schema_sha256,
            "runtime_contract_sha256": stage.runtime_contract_sha256,
            "validator_sha256": stage.validator_sha256,
            "execution_status": execution_status,
            "validation_status": "NOT_RUN",
            "status": execution_status,
            "failure": failure,
            "output": result.model_dump(mode="json") if result is not None else None,
        }
        if result is not None:
            state["validator"] = _validator_record(stage, result, previous)
            state["before_after_diff"] = state["validator"]["before_after_contract"]["diff"]
            state["validation_status"] = "PASS" if state["validator"]["passed"] else "FAIL"
            state["status"] = "PASS" if execution_status == "PASS" and state["validation_status"] == "PASS" else "FAIL"
        else:
            state["validator"] = None
            state["before_after_diff"] = None
        return state

    def _method_summary(self, method_id: str, states: list[dict[str, Any]], started: float) -> dict[str, Any]:
        calls = [call for call in self.provider.calls if call.method_id == method_id]
        execution_failures = [state for state in states if state["execution_status"] == "FAIL"]
        validation_failures = [
            state
            for state in states
            if state["validation_status"] == "FAIL"
        ]
        dependent_skips = [state for state in states if state["execution_status"] == "SKIPPED"]
        status = "FAIL" if execution_failures or validation_failures else "BLOCKED" if dependent_skips else "PASS"
        unrepresented_failures = [
            {
                "method_id": method_id,
                "state_id": state["state_id"],
                "status": state["execution_status"],
                "error": state["failure"],
            }
            for state in execution_failures
            if not any(call.state_id == state["state_id"] and call.status == "FAIL" for call in calls)
        ]
        return {
            "status": status,
            "states": states,
            "provider_calls": [asdict(call) for call in calls],
            "failure_traces": [asdict(call) for call in calls if call.status != "PASS"]
            + unrepresented_failures,
            "metrics": {
                "state_count": len(states),
                "valid_state_count": sum(
                    state["execution_status"] == "PASS" and state["validation_status"] == "PASS"
                    for state in states
                ),
                "revision_count": max(len(states) - 1, 0),
                "valid_revision_count": sum(
                    state["execution_status"] == "PASS" and state["validation_status"] == "PASS"
                    for state in states[1:]
                ),
                "provider_call_count": len(calls),
                "failed_attempt_count": sum(call.status == "FAIL" for call in calls),
                "failed_state_count": len(execution_failures),
                "validation_failure_count": len(validation_failures),
                "dependent_skip_count": len(dependent_skips),
                "retry_count": sum(call.retry_count for call in calls),
                "cost_usd": sum(call.cost_usd for call in calls),
                "provider_wall_time_ms": sum(call.elapsed_ms for call in calls),
                "elapsed_seconds": time.perf_counter() - started,
                "paid_api": False,
                "network_calls_declared": 0,
                "network_observation": "NOT_MEASURED",
            },
        }

    def _run_rules_only(self) -> dict[str, Any]:
        method_id = "B0_rules_only"
        started = time.perf_counter()
        states: list[dict[str, Any]] = []
        previous: IntegrationResult | None = None
        for stage in self.stages:
            result = self.pipeline.run_state(stage.loaded).model_copy(deep=True)
            states.append(self._record_state(stage=stage, result=result, previous=previous))
            previous = result
        return self._method_summary(method_id, states, started)

    def _run_full_regeneration(self) -> dict[str, Any]:
        method_id = "B1_full_regeneration"
        started = time.perf_counter()
        states: list[dict[str, Any]] = []
        previous: IntegrationResult | None = None
        for stage in self.stages:
            try:
                result = self.provider.call(
                    method_id=method_id,
                    stage=stage,
                    operation="full_regeneration",
                    generate=lambda stage=stage: self.pipeline.run_state(stage.loaded).model_copy(deep=True),
                    metadata={"input_mode": "full_public_packet", "generation_scope": "full"},
                )
            except MockProviderFailure as exc:
                states.append(self._record_state(stage=stage, result=None, previous=previous, failure=str(exc), execution_status="FAIL"))
                previous = None
                continue
            states.append(self._record_state(stage=stage, result=result, previous=previous))
            previous = result
        return self._method_summary(method_id, states, started)

    def _direct_revision_target(self, stage: StagedInput, previous: IntegrationResult) -> IntegrationResult:
        """Apply the public PTP-0001 change to the prior output only."""

        packet = stage.packet
        if packet.case_id != DEFAULT_CASE_ID:
            raise ValueError("the bounded direct-revision adapter currently supports PTP-0001 only")
        integrity = self.pipeline._integrity(packet.evidence)
        facts = self.pipeline._facts(packet, integrity)
        options: list[dict[str, Any]] = []
        routes: list[dict[str, Any]] = []
        for option in packet.options:
            option_id = option.option_id or option.candidate_id or "unknown"
            state, evidence_ids, constraint_ids = self.pipeline._policy_state(packet.case_id, option, packet, facts, integrity)
            label = f"{option_id}: {option.selected_material or 'unknown'} substrate"
            route_status = "candidate" if state == "passes_this_explicit_check" else "blocked_by_missing_evidence" if state == "unknown" else "draft"
            unknowns = ["measured production yield"]
            route = {
                "route_id": f"{packet.case_id}:{option_id}",
                "label": label,
                "status": route_status,
                "policy_check_state": state,
                "evidence_ids": evidence_ids,
                "constraint_ids": constraint_ids,
                "unknowns": unknowns,
                "contradictions": [],
            }
            routes.append(route)
            options.append({"option_id": option_id, "label": label, "policy_check_state": state, "evidence_ids": evidence_ids, "unknowns": unknowns})
        updates = {
            "case_id": packet.case_id,
            "state_id": packet.state_id,
            "project_display_name": stage.loaded.raw.get("project_display_name", stage.loaded.raw.get("display_name", packet.case_id)),
            "profile_id": packet.profile_id,
            "profile_version": packet.profile_version,
            "brief": packet.brief,
            "fictional_stipulations": {"policy": packet.policy, "options": packet.options, "basis": "public development case stipulation; not a real-organization fact"},
            "allowed_evidence": [item.model_dump(mode="json") for item in packet.evidence],
            "source_integrity": integrity,
            "options": options,
            "routes": routes,
            "unknowns": sorted({unknown for route in routes for unknown in route["unknowns"]}),
        }
        return previous.model_copy(update=updates, deep=True)

    def _run_revision(self, method_id: str, operation: str, invalidation: bool) -> dict[str, Any]:
        started = time.perf_counter()
        states: list[dict[str, Any]] = []
        previous: IntegrationResult | None = None
        for stage in self.stages:
            if previous is None and states:
                states.append(
                    self._record_state(
                        stage=stage,
                        result=None,
                        previous=None,
                        failure="previous revision state failed; dependent revision was not attempted",
                        execution_status="SKIPPED",
                    )
                )
                continue
            try:
                if method_id == "B2_direct_revision" and previous is not None:
                    generate = lambda stage=stage, previous=previous: self._direct_revision_target(stage, previous)
                    generation_scope = "direct_revision"
                else:
                    generate = lambda stage=stage: self.pipeline.run_state(stage.loaded).model_copy(deep=True)
                    generation_scope = "full_then_scoped_merge" if invalidation else "full_generation_for_initial_state"
                generated = self.provider.call(
                    method_id=method_id,
                    stage=stage,
                    operation=operation,
                    generate=generate,
                    metadata={
                        "input_mode": "previous_output_plus_public_change" if previous is not None else "full_public_packet",
                        "generation_scope": generation_scope,
                        "invalidated_fields": sorted(_invalidation_fields(stage, previous)) if invalidation else None,
                    },
                )
                if previous is None:
                    result = generated
                else:
                    fields = _invalidation_fields(stage, previous) if invalidation else _allowed_changed_fields(stage.packet.event.type)
                    result = _merge_revision(previous, generated, fields)
            except MockProviderFailure as exc:
                states.append(self._record_state(stage=stage, result=None, previous=previous, failure=str(exc), execution_status="FAIL"))
                previous = None
                continue
            states.append(self._record_state(stage=stage, result=result, previous=previous))
            previous = result
        return self._method_summary(method_id, states, started)

    def _run_existing_workflow(self) -> dict[str, Any]:
        method_id = "P_existing_workflow"
        started = time.perf_counter()
        states: list[dict[str, Any]] = []
        previous: IntegrationResult | None = None
        for stage in self.stages:
            try:
                result = self.pipeline.run_state(stage.loaded).model_copy(deep=True)
            except Exception as exc:  # noqa: BLE001 - bounded wrapper records execution failure
                states.append(
                    self._record_state(
                        stage=stage,
                        result=None,
                        previous=previous,
                        failure=f"{type(exc).__name__}: {str(exc)[:240]}",
                        execution_status="FAIL",
                    )
                )
                previous = None
                continue
            states.append(self._record_state(stage=stage, result=result, previous=previous))
            previous = result
        summary = self._method_summary(method_id, states, started)
        summary["existing_workflow_evidence"] = {
            "staged_state_ids": [stage.packet.state_id for stage in self.stages],
            "staged_state_count": len(self.stages),
            "loaded_from_public_stages": True,
            "run_case_called": False,
            "persistence": "NOT_RUN",
        }
        return summary

    def run(self) -> dict[str, Any]:
        started = time.perf_counter()
        method_reports = {
            "B0_rules_only": self._run_rules_only(),
            "B1_full_regeneration": self._run_full_regeneration(),
            "B2_direct_revision": self._run_revision("B2_direct_revision", "direct_revision", False),
            "B3_invalidation_same_generator": self._run_revision("B3_invalidation_same_generator", "same_generator_scoped_merge", True),
            "P_existing_workflow": self._run_existing_workflow(),
        }
        staging = [
            {
                "run_id": self.run_id,
                "case_id": stage.packet.case_id,
                "state_id": stage.packet.state_id,
                "event_type": stage.packet.event.type,
                "input_sha256": stage.input_sha256,
                "schema_sha256": stage.schema_sha256,
                "runtime_contract_sha256": stage.runtime_contract_sha256,
                "validator_sha256": stage.validator_sha256,
                "input_fields": sorted(stage.input_payload),
            }
            for stage in self.stages
        ]
        pass_methods = [method_id for method_id, report in method_reports.items() if report["status"] == "PASS"]
        fail_methods = [method_id for method_id, report in method_reports.items() if report["status"] == "FAIL"]
        blocked_methods = [method_id for method_id, report in method_reports.items() if report["status"] == "BLOCKED"]
        return {
            "kind": "g10_bounded_offline_comparison",
            "run_id": self.run_id,
            "status": "FAIL" if fail_methods else "BLOCKED" if blocked_methods else "PASS",
            "benchmark": False,
            "scientific_claim": False,
            "case_id": self.stages[0].packet.case_id,
            "state_ids": [stage.packet.state_id for stage in self.stages],
            "staging": staging,
            "methods": method_reports,
            "b4_rg": {
                "implementation": "NOT_IMPLEMENTED",
                "readiness": "POOL_NOT_READY",
                "execution": "NOT_RUN",
                "reason": "This public case has no verified distractor/recoverable-evidence pool for adaptive-search comparison.",
            },
            "status_register": {
                "PASS": ["offline comparison mechanics", *pass_methods],
                "FAIL": fail_methods,
                "BLOCKED": blocked_methods,
                "NOT_RUN": ["B4-RG adaptive-search plus regeneration", "B4-DR adaptive-search plus direct revision", "scientific pilot", "provider/model quality comparison", "full G10 completion"],
            },
            "search_readiness": {
                "status": "POOL_NOT_READY",
                "initial_active_evidence_ids": sorted({item.evidence_id for item in self.stages[0].packet.evidence}),
                "recoverable_evidence_ids": [],
                "distractor_ids": [],
                "reason": "No verified recoverable-evidence pool is available outside the current public packet.",
            },
            "accounting": {
                "mock_provider_calls": len(self.provider.calls),
                "mock_cost_usd": sum(call.cost_usd for call in self.provider.calls),
                "network_calls_declared": 0,
                "network_observation": "NOT_MEASURED",
                "network_guard": "mock seam has no HTTP transport; process-wide egress was not observed",
                "paid_compute": False,
                "retries": sum(call.retry_count for call in self.provider.calls),
                "failed_attempts": sum(call.status == "FAIL" for call in self.provider.calls),
                "failure_traces": [asdict(call) for call in self.provider.calls if call.status != "PASS"],
            },
            "elapsed_seconds": time.perf_counter() - started,
            "limits": [
                "PTP-0001 is one development smoke-test case.",
                "The mock provider tests mechanics and failure accounting, not model quality.",
                "No semantic, clinical, legal, patentability, FTO, or scientific utility claim is made.",
                "The existing workflow wrapper is bounded public-input integration, not full dependency-guided G10 P.",
            ],
        }

    @staticmethod
    def write_reports(report: dict[str, Any], output_dir: Path) -> None:
        output_dir = output_dir.resolve()
        protected_output = (ROOT / "results" / "development" / "g10-offline-comparison").resolve()
        if output_dir == protected_output:
            raise ValueError("refusing to overwrite protected prior G10 evidence directory")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "comparison.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        diffs = {
            method_id: [
                {
                    "state_id": state["state_id"],
                    "event_type": state["event_type"],
                    "execution_status": state["execution_status"],
                    "validation_status": state["validation_status"],
                    "status": state["status"],
                    "before_after_diff": state["before_after_diff"],
                }
                for state in method_report["states"]
            ]
            for method_id, method_report in report["methods"].items()
        }
        (output_dir / "before-after-diff.json").write_text(json.dumps(diffs, indent=2, ensure_ascii=False), encoding="utf-8")

        validators = {
            method_id: [
                {
                    "state_id": state["state_id"],
                    "execution_status": state["execution_status"],
                    "validation_status": state["validation_status"],
                    "status": state["status"],
                    "validator": state["validator"],
                    "failure": state["failure"],
                }
                for state in method_report["states"]
            ]
            for method_id, method_report in report["methods"].items()
        }
        (output_dir / "validator-results.json").write_text(json.dumps(validators, indent=2, ensure_ascii=False), encoding="utf-8")

        traces = {
            method_id: {
                "status": method_report["status"],
                "metrics": method_report["metrics"],
                "provider_calls": method_report["provider_calls"],
                "failure_traces": method_report["failure_traces"],
            }
            for method_id, method_report in report["methods"].items()
        }
        (output_dir / "method-traces.json").write_text(json.dumps(traces, indent=2, ensure_ascii=False), encoding="utf-8")

        search_pool_path = output_dir / "search-pool-readiness.json"
        search_pool_path.write_text(json.dumps(report["search_readiness"], indent=2, ensure_ascii=False), encoding="utf-8")

        lines = [
            "# G10 bounded offline comparison",
            "",
            "Mechanics-only development evidence from the public PTP-0001 packet; not a scientific benchmark.",
            "",
            f"- Status: **{report['status']}**",
            f"- Case: `{report['case_id']}`",
            f"- States: `{', '.join(report['state_ids'])}`",
            f"- Network calls declared: `{report['accounting']['network_calls_declared']}`",
            f"- Network observation: `{report['accounting']['network_observation']}`",
            f"- Mock provider cost: USD {report['accounting']['mock_cost_usd']:.7f}",
            "",
            "## Method status",
            "",
            "| Method | Status | Provider calls | Failed attempts | Failed states | Validation failures | Cost |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
        for method_id, method_report in report["methods"].items():
            metrics = method_report["metrics"]
            lines.append(
                f"| {method_id} | {method_report['status']} | {metrics['provider_call_count']} | "
                f"{metrics['failed_attempt_count']} | {metrics['failed_state_count']} | "
                f"{metrics['validation_failure_count']} | USD {metrics['cost_usd']:.7f} |"
            )
        lines.extend([
            "",
            "## Before/after checks",
            "",
        ])
        for method_id, method_report in report["methods"].items():
            lines.append(f"### {method_id}")
            for state in method_report["states"]:
                diff = state.get("before_after_diff")
                changed = ", ".join(diff["affected_fields"]) if diff else "initial state"
                preserved = ", ".join(diff["preserved_fields"]) if diff else "n/a"
                lines.append(
                    f"- `{state['state_id']}` `{state['status']}` "
                    f"(execution={state['execution_status']}, validation={state['validation_status']}); "
                    f"changed={changed or 'none'}; preserved={preserved or 'none'}"
                )
        lines.extend([
            "",
            "## B4-RG boundary",
            "",
            "B4-RG and B4-DR are `NOT_IMPLEMENTED`/`NOT_RUN`; the current public case does not contain a verified adaptive-search distractor/recovery pool.",
            "",
            "## Limits",
            "",
            "- No provider network, paid compute, model-quality, scientific-utility, clinical, legal, patentability, or FTO claim.",
            "- The existing workflow wrapper is bounded public-input integration, not full G10 dependency-guided repair.",
        ])
        (output_dir / "comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

        rows = []
        for method_id, method_report in report["methods"].items():
            for state in method_report["states"]:
                diff = state.get("before_after_diff") or {}
                rows.append(
                    "<tr>"
                    f"<td>{html.escape(method_id)}</td>"
                    f"<td>{html.escape(state['state_id'])}</td>"
                    f"<td>{html.escape(state['status'])}</td>"
                    f"<td>{html.escape(', '.join(diff.get('affected_fields', [])) or 'none')}</td>"
                    f"<td>{html.escape(', '.join(diff.get('preserved_fields', [])) or 'none')}</td>"
                    "</tr>"
                )
        html_doc = (
            "<!doctype html><meta charset='utf-8'><title>G10 offline comparison</title>"
            "<style>body{font:16px system-ui;max-width:1200px;margin:2rem auto}"
            "table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:.5rem;vertical-align:top}"
            "</style><h1>G10 bounded offline comparison</h1>"
            "<p>Mechanics-only evidence from public PTP-0001 input; not a scientific benchmark.</p>"
            "<table><tr><th>Method</th><th>State</th><th>Status</th><th>Changed</th><th>Preserved</th></tr>"
            + "".join(rows)
            + "</table>"
        )
        (output_dir / "comparison.html").write_text(html_doc, encoding="utf-8")

        def optional_hash(path: Path) -> str | None:
            return _sha256_file(path) if path.is_file() else None

        source_paths = {
            "comparison": ROOT / "src" / "patent_to_pilot" / "evaluation" / "comparison.py",
            "runner_script": ROOT / "scripts" / "run_g10_offline_comparison.py",
            "g10_tests": ROOT / "tests" / "test_g10_offline_comparison.py",
            "integration_pipeline": ROOT / "src" / "patent_to_pilot" / "integration" / "pipeline.py",
            "public_output_schema": ROOT / "methodology" / "evaluation" / "cases" / report["case_id"] / "public-input" / "output-schema.json",
        }
        protected_dir = ROOT / "results" / "development" / "g10-offline-comparison"
        protected_files = {
            str(path.relative_to(ROOT)): _sha256_file(path)
            for path in sorted(protected_dir.glob("*"))
            if path.is_file()
        }
        journal_path = ROOT / "results" / "development" / "provider-pilot" / "live.sqlite3"
        if journal_path.is_file():
            protected_files[str(journal_path.relative_to(ROOT))] = _sha256_file(journal_path)
        candidate_manifest = {
            "kind": "g10_correctness_search_candidate_source_manifest",
            "run_id": report["run_id"],
            "changed_source_hashes": {name: optional_hash(path) for name, path in source_paths.items()},
            "dependency_hashes": {
                "integration_pipeline": optional_hash(source_paths["integration_pipeline"]),
                "public_output_schema": optional_hash(source_paths["public_output_schema"]),
            },
            "frozen_input_hashes": {
                item["state_id"]: item["input_sha256"] for item in report["staging"]
            },
            "documentation_schema_sha256": report["staging"][0]["schema_sha256"],
            "runtime_contract_sha256": report["staging"][0]["runtime_contract_sha256"],
            "validator_sha256": report["staging"][0]["validator_sha256"],
            "output_hashes": {
                name: _sha256_file(output_dir / name)
                for name in (
                    "comparison.json",
                    "comparison.md",
                    "comparison.html",
                    "before-after-diff.json",
                    "validator-results.json",
                    "method-traces.json",
                    "search-pool-readiness.json",
                )
            },
            "protected_old_evidence_and_journal_hashes": protected_files,
        }
        (output_dir / "candidate-source-manifest.json").write_text(
            json.dumps(candidate_manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        artifact_names = [
            "comparison.json",
            "comparison.md",
            "comparison.html",
            "before-after-diff.json",
            "validator-results.json",
            "method-traces.json",
            "search-pool-readiness.json",
            "candidate-source-manifest.json",
        ]
        manifest = {
            "kind": "g10_offline_comparison_evidence_manifest",
            "status": report["status"],
            "case_id": report["case_id"],
            "state_ids": report["state_ids"],
            "files": {name: _sha256_file(output_dir / name) for name in artifact_names},
        }
        (output_dir / "evidence-manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
