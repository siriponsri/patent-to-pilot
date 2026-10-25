"""Public-input-only development integration for G09/G10.

This module intentionally implements a deterministic, rule-based path. It is
not a semantic evaluator and never reads evaluator-only files or expected
answers. The case packets are development fixtures, not a final benchmark.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from patent_to_pilot.core.models import ChangeRecord, EvidenceRecord, EvidenceState, OrganizationProfile, RouteRecord
from patent_to_pilot.core.repository import SQLiteRecordRepository

ROOT = Path(__file__).resolve().parents[3]
CASES_ROOT = ROOT / "methodology" / "evaluation" / "cases"
ORGS_ROOT = ROOT / "methodology" / "organizations"
PROFILE_BINDINGS = {
    "PTP-0001": ("PTP-FIC-ORG-A", "fictional-profile-a"),
    "PTP-0002": ("PTP-FIC-ORG-B", "fictional-profile-b"),
    "PTP-0003": ("PTP-FIC-ORG-C", "fictional-profile-c"),
}
FORBIDDEN_KEYS = {
    "expected_doc_ids", "expected_documents", "expected_answer", "expected_answers",
    "gold_answer", "answer_facts", "oracle", "oracle_output", "hidden_facts",
    "checked_facts", "evaluator_only", "evaluator-only", "expected_output", "future_events",
}

TOP_LEVEL_KEYS = {
    "PTP-0001": {"case_id", "track", "split", "event_id", "display_name", "organization_brief", "candidate_choices", "change", "active_chunks", "rules", "output_schema"},
    "PTP-0002": {"case_id", "state_id", "classification", "project_display_name", "brief", "organization_ref", "case_stipulations", "change_event", "sources", "history_access", "output_contract"},
    "PTP-0003": {"case_id", "state_id", "classification", "project_display_name", "brief", "organization_ref", "case_stipulations", "change_event", "sources", "history_access", "output_contract"},
}


class TrimmedOffsetMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)
    basis: str = Field(min_length=1)

    @model_validator(mode="after")
    def valid_range(self) -> "TrimmedOffsetMetadata":
        if self.char_end < self.char_start:
            raise ValueError("trimmed offset end must not precede start")
        return self


class LocatorMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    dataset_field: str | None = None
    paragraph_id: str | None = None
    printed_paragraph_num: str | None = None
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)
    offset_unit: Literal["Unicode code points, end-exclusive"] | None = None
    g08_trimmed_component_offsets: TrimmedOffsetMetadata | None = None

    @model_validator(mode="after")
    def valid_range(self) -> "LocatorMetadata":
        if (self.char_start is None) != (self.char_end is None):
            raise ValueError("locator char_start and char_end must be provided together")
        if self.char_start is not None and self.char_end < self.char_start:
            raise ValueError("locator end must not precede start")
        return self


class PublicEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(min_length=1)
    text: str
    source_id: str = Field(min_length=1)
    source_version: str | None = None
    document_id: str | None = None
    family_id: str | None = None
    source_locator: str = Field(min_length=1)
    locator: LocatorMetadata = Field(default_factory=LocatorMetadata)
    origin: Literal["source_assertion", "stipulation", "interpretation", "unknown"] = "source_assertion"
    text_sha256: str | None = None
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def top_level_span_matches_locator(self) -> "PublicEvidence":
        locator_start = self.locator.char_start
        locator_end = self.locator.char_end
        top_level_present = self.char_start is not None or self.char_end is not None
        locator_present = locator_start is not None or locator_end is not None
        if top_level_present and not locator_present:
            raise ValueError("top-level evidence offsets require canonical locator offsets")
        if top_level_present and (self.char_start != locator_start or self.char_end != locator_end):
            raise ValueError("top-level evidence offsets must match locator offsets")
        return self


class PublicEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = Field(min_length=1)
    scope: str | None = None
    event_order: int = Field(ge=0)
    effective_at: str | None = None
    description: str | None = None
    policy_rule_id: str | None = None


class PublicPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rule_id: str | None = None
    origin: str | None = None
    role_scope: str | None = None
    allowed_initial: list[str] = Field(default_factory=list)
    carrier_scope: str | None = None
    real_organization_rule: bool | None = None
    forbidden_inhibitors: list[str] = Field(default_factory=list)
    operator: str | None = None
    normalization: str | None = None
    maximum: int | None = Field(default=None, ge=0)
    count_kind: str | None = None
    component: str | None = None
    permitted_materials: list[str] = Field(default_factory=list)
    forbidden_materials: list[str] = Field(default_factory=list)


class PublicOption(BaseModel):
    model_config = ConfigDict(extra="forbid")
    option_id: str | None = None
    candidate_id: str | None = None
    selected_component: str | None = None
    selected_material: str | None = None
    selection_origin: str | None = None
    selected_carrier: str | None = None
    selected_inhibitor: str | None = None
    selected_route: str | None = None
    basis: str | None = None
    evidence_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def has_identity(self) -> "PublicOption":
        if not (self.option_id or self.candidate_id):
            raise ValueError("option requires option_id or candidate_id")
        return self


class WorkflowInput(BaseModel):
    """Case-independent permitted input for the bounded offline prototype."""
    model_config = ConfigDict(extra="forbid")
    project_id: str = Field(min_length=1)
    brief: str = Field(min_length=1)
    profile: OrganizationProfile
    policy: PublicPolicy
    options: list[PublicOption] = Field(min_length=1)
    evidence: list[PublicEvidence] = Field(default_factory=list)
    event: PublicEvent = Field(default_factory=lambda: PublicEvent(type="initial", event_order=0))
    unknowns: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def reject_evaluator_profile_fields(self) -> "WorkflowInput":
        forbidden = _walk_forbidden(self.profile.public_source_context, "$.profile.public_source_context")
        if forbidden:
            raise ValueError(forbidden)
        if self.event.policy_rule_id and self.event.policy_rule_id != self.policy.rule_id:
            raise ValueError("event/policy conflict: event policy_rule_id does not match declared policy")
        return self


class PublicOrganizationRef(BaseModel):
    model_config = ConfigDict(extra="forbid")
    profile_id: str = Field(min_length=1)
    profile_version: str = Field(min_length=1)
    path: str | None = None
    binding: str | None = None
    integration_status: str | None = None


class PublicCaseStipulations(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: str | None = None
    status: str | None = None
    policy: PublicPolicy
    options: list[PublicOption]
    unmeasured_fields: str | None = None


class PublicSourceRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(min_length=1)
    text: str
    locator: LocatorMetadata
    text_sha256: str | None = None
    origin: str = "source_assertion"
    source_id: str = Field(min_length=1)
    document_id: str | None = None
    source_version: str | None = None
    family_id: str | None = None
    source_locator: str = Field(min_length=1)
    g08_trimmed_component_offsets: TrimmedOffsetMetadata | None = None


class PublicChunkRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    chunk_id: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    paragraph_id: str | None = None
    printed_paragraph_num: str | None = None
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    text: str
    sha256: str | None = None
    locator_basis: str | None = None


class PublicOrganizationBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")
    fictional: bool
    goal: str
    capabilities: dict[str, Any]
    policy: PublicPolicy
    required_unknown_fields: list[str]


class PublicRules(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_scope: str
    policy_scope: str
    claim_boundary: str
    missingness_scope: str
    source_ambiguity: str
    hidden_oracle: str


class PublicOutputContract(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_fact_fields: list[str]
    option_ids: list[str]
    option_states: list[str]
    handoff: str
    ready_for_review_is_not_external_approval: bool


class AgentPacket(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    state_id: str
    event: PublicEvent
    brief: str
    profile_id: str
    profile_version: str
    policy: PublicPolicy
    options: list[PublicOption]
    evidence: list[PublicEvidence]
    unknowns: str | list[str]
    input_boundary: str = "public-input-only"


class IntegrationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    state_id: str
    project_display_name: str
    profile_id: str
    profile_version: str
    brief: str
    fictional_stipulations: dict[str, Any]
    interpretations: list[dict[str, str]]
    allowed_evidence: list[dict[str, Any]]
    source_integrity: dict[str, Any]
    interface_status: dict[str, Any]
    source_facts: list[dict[str, Any]]
    options: list[dict[str, Any]]
    routes: list[dict[str, Any]]
    unknowns: list[str]
    contradictions: list[str] = Field(default_factory=list)
    proposed_next_tests: list[dict[str, Any]]
    handoff: dict[str, Any]
    agent_input_fields: list[str]
    mock_provider_called: bool = False


@dataclass(frozen=True)
class LoadedCase:
    packet: AgentPacket
    raw: dict[str, Any]
    profile: OrganizationProfile


class EvaluationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    passed: bool
    required_changes: bool
    preservation: bool
    unknown_handling: bool
    route_local_status: bool
    sqlite_payload_read_back: bool
    failures: list[str] = Field(default_factory=list)


class DevelopmentEvaluator:
    """Independent invariant checker; it receives no expected-answer material."""

    @staticmethod
    def evaluate(packet: AgentPacket, result: IntegrationResult, previous: IntegrationResult | None = None, sqlite_payload_read_back: bool = True) -> EvaluationResult:
        failures: list[str] = []
        if result.case_id != packet.case_id or result.state_id != packet.state_id:
            failures.append("result identity does not match the evaluated public state")
        routes = {route["route_id"]: route for route in result.routes}
        event_type = packet.event.type
        if event_type in {"forbid_silicon_substrate", "forbid_material_at_role"}:
            if not any(route["policy_check_state"] == "fails_this_explicit_check" for route in routes.values()):
                failures.append("required policy prohibition was not reflected in a route")
            if all(route["policy_check_state"] == "fails_this_explicit_check" for route in routes.values()):
                failures.append("policy prohibition incorrectly blocked every route")
        if event_type in {"sole_support_withdrawal", "support_withdrawal"}:
            if not any(route["policy_check_state"] == "unknown" for route in routes.values()):
                failures.append("support withdrawal did not produce a scoped unknown")
        if event_type == "tighten_bound":
            if not any(route["policy_check_state"] == "fails_this_explicit_check" for route in routes.values()):
                failures.append("tightened bound did not affect the route")
        facts_by_field = {fact["field"]: fact for fact in result.source_facts}
        evidence_by_id = {item.evidence_id: item for item in packet.evidence}
        for required_field in ("measured_production_yield", "reported_intermediate_stage_count", "BTC_stage_use_count", "all_manufacturing_operations", "numeric_total_batch_cost"):
            fact = facts_by_field.get(required_field)
            if fact is None:
                continue
            if fact["state"] == "unknown" and (fact["value"] is not None or fact["evidence_ids"]):
                failures.append(f"unsupported unknown value for required field: {required_field}")
            if fact["state"] != "known" and fact["value"] is not None:
                failures.append(f"unsupported value state for required field: {required_field}")
            if fact["state"] == "known" and fact["value"] is None:
                failures.append(f"known required field has null value: {required_field}")
            if fact["state"] == "known" and not fact["evidence_ids"]:
                failures.append(f"supported required field lacks evidence: {required_field}")
            if fact["state"] == "known":
                unsupported = [
                    evidence_id for evidence_id in fact["evidence_ids"]
                    if not _evidence_supports_field(required_field, fact["value"], evidence_by_id.get(evidence_id))
                ]
                if unsupported:
                    failures.append(f"field-specific evidence mismatch for {required_field}: {', '.join(unsupported)}")
        if packet.case_id == "PTP-0001" and event_type == "forbid_silicon_substrate":
            for option in packet.options:
                route = routes.get(f"{packet.case_id}:{option.option_id or option.candidate_id}")
                expected = "fails_this_explicit_check" if option.selected_material in packet.policy.forbidden_materials else "passes_this_explicit_check"
                if route is None or route["policy_check_state"] != expected:
                    failures.append(f"policy result mismatch for option {option.option_id or option.candidate_id}")
        if packet.case_id == "PTP-0002" and event_type == "forbid_material_at_role":
            for option in packet.options:
                route = routes.get(f"{packet.case_id}:{option.option_id or option.candidate_id}")
                expected = "fails_this_explicit_check" if option.selected_inhibitor in packet.policy.forbidden_inhibitors else "passes_this_explicit_check"
                if route is None or route["policy_check_state"] != expected:
                    failures.append(f"policy result mismatch for option {option.option_id or option.candidate_id}")
        if packet.case_id in {"PTP-0001", "PTP-0002", "PTP-0003"}:
            option_by_id = {(option.option_id or option.candidate_id): option for option in packet.options}
            for option in packet.options:
                option_id = option.option_id or option.candidate_id
                route = routes.get(f"{packet.case_id}:{option_id}")
                if route is None:
                    failures.append(f"missing route for option {option_id}")
                    continue
                if packet.case_id == "PTP-0001":
                    fact = facts_by_field.get(f"substrate_{option.selected_material}")
                    expected = "fails_this_explicit_check" if option.selected_material in packet.policy.forbidden_materials else "passes_this_explicit_check" if fact and fact["state"] == "known" and fact["evidence_ids"] else "unknown"
                elif packet.case_id == "PTP-0002":
                    fact = facts_by_field.get(f"{option.selected_inhibitor}_role")
                    carrier = facts_by_field.get("PEG_role")
                    expected = "fails_this_explicit_check" if option.selected_inhibitor in packet.policy.forbidden_inhibitors else "passes_this_explicit_check" if fact and carrier and fact["state"] == "known" and carrier["state"] == "known" and fact["evidence_ids"] and carrier["evidence_ids"] else "unknown"
                else:
                    fact = facts_by_field.get(packet.policy.count_kind or "")
                    expected = "unknown" if not fact or fact["state"] != "known" or not fact["evidence_ids"] else "fails_this_explicit_check" if packet.policy.maximum is not None and fact["value"] > packet.policy.maximum else "passes_this_explicit_check"
                if route["policy_check_state"] != expected:
                    failures.append(f"route/option state mismatch for {option_id}: expected {expected}")
                route_evidence = [evidence_by_id[evidence_id] for evidence_id in route["evidence_ids"] if evidence_id in evidence_by_id]
                if route["policy_check_state"] == "passes_this_explicit_check" and not _evidence_set_supports_option(option, route_evidence):
                    failures.append(f"route evidence does not support option role/value for {option_id}: {', '.join(item.evidence_id for item in route_evidence)}")
        for fact in result.source_facts:
            if fact["field"] in {"measured_production_yield", "all_manufacturing_operations", "numeric_total_batch_cost"} and fact["value"] is not None:
                if not fact["evidence_ids"]:
                    failures.append(f"unsupported value without evidence: {fact['field']}")
        if event_type == "project_name_only" and previous is not None:
            for field in ("source_facts", "options", "routes", "allowed_evidence", "source_integrity"):
                if result.model_dump(mode="json")[field] != previous.model_dump(mode="json")[field]:
                    failures.append(f"project-name-only event changed {field}")
        yield_facts = [fact for fact in result.source_facts if fact["field"] == "measured_production_yield"]
        if yield_facts and any(fact["state"] != "unknown" or fact["value"] is not None for fact in yield_facts):
            failures.append("production yield was asserted without packet evidence")
        # An unknown route may retain evidence for an unaffected sub-claim
        # (for example PEG carrier evidence after HPMC support withdrawal).
        # Reject only evidence that belongs to an invalidated source, not all
        # evidence on an unknown route.
        invalid_ids = set(result.source_integrity["invalid_evidence_ids"])
        if any(invalid_ids.intersection(route["evidence_ids"]) for route in routes.values()):
            failures.append("route retained evidence whose integrity failed")
        for route in routes.values():
            expected_status = {
                "passes_this_explicit_check": "candidate",
                "fails_this_explicit_check": "draft",
                "unknown": "blocked_by_missing_evidence",
            }[route["policy_check_state"]]
            if route["status"] != expected_status:
                failures.append(f"route-local status mismatch for {route['route_id']}")
        required_changes = not failures or not any(item.startswith("required") for item in failures)
        preservation = not any("changed" in item for item in failures)
        unknown_handling = not any("unknown" in item or "yield" in item for item in failures)
        route_local_status = not any("route-local status mismatch" in item for item in failures)
        passed = not failures
        if not sqlite_payload_read_back:
            failures.append("SQLite route payload/status read-back failed")
            passed = False
        return EvaluationResult(passed=passed, required_changes=required_changes, preservation=preservation, unknown_handling=unknown_handling, route_local_status=route_local_status, sqlite_payload_read_back=sqlite_payload_read_back, failures=failures)


def _walk_forbidden(value: Any, path: str = "$") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            if str(key).lower() in FORBIDDEN_KEYS:
                return f"forbidden evaluator field at {path}.{key}"
            found = _walk_forbidden(child, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _walk_forbidden(child, f"{path}[{index}]")
            if found:
                return found
    return None


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _evidence_supports_field(field: str, value: Any, evidence: PublicEvidence | None) -> bool:
    """Conservative literal support check used only by the independent evaluator."""
    if evidence is None or evidence.origin != "source_assertion":
        return False
    text = evidence.text.casefold()
    if field == "reported_intermediate_stage_count":
        return value == 5 and bool(re.search(r"\bfive\s+intermediate\s+stages\b", text))
    if field == "BTC_stage_use_count":
        return value == 2 and bool(re.search(r"\bbtc\b.*\btwo\s+of\s+the\s+five\s+stages\b", text))
    if field == "numeric_total_batch_cost":
        if value is None:
            return False
        # Only accept a number captured directly by the cost phrase. Other
        # numbers in the same sentence (batch IDs, tablet counts, stages,
        # etc.) are not cost witnesses. Multiple direct cost values are
        # ambiguous and therefore unsupported.
        number = r"\d+(?:,\d{3})*(?:\.\d+)?"
        cost_patterns = (
            rf"\b(?:total\s+)?batch\s+cost\b\s*(?:was|is|equals?|=|:)?\s*(?P<value>{number})(?![\w.])",
            rf"\bcost\s+of\s+the\s+batch\b\s*(?:was|is|equals?|=|:)?\s*(?P<value>{number})(?![\w.])",
        )
        witnesses = [match.group("value") for pattern in cost_patterns for match in re.finditer(pattern, text)]
        if len(witnesses) != 1:
            return False
        cost_match = next(match for pattern in cost_patterns for match in re.finditer(pattern, text))
        clause_tail = text[cost_match.end():]
        clause_tail = re.split(r"[.;!?]", clause_tail, maxsplit=1)[0]
        if re.search(rf"\b(?:revised|updated|changed|increased|decreased|from|to)\s+(?:to\s+)?{number}(?![\w.])", clause_tail):
            return False
        try:
            expected = float(value)
            return float(witnesses[0].replace(",", "")) == expected
        except (TypeError, ValueError):
            return False
    if field == "all_manufacturing_operations":
        return bool(re.search(r"\b(?:all|total)\s+manufacturing\s+operations\b", text)) and bool(re.search(r"\b\d+\b", text))
    if field == "measured_production_yield":
        return bool(re.search(r"\byield\b", text)) and bool(re.search(r"\b\d+(?:[.,]\d+)?\s*%?", text))
    return False


def _evidence_supports_option(option: PublicOption, evidence: PublicEvidence) -> bool:
    if evidence.origin != "source_assertion":
        return False
    text = evidence.text.casefold()
    component = (option.selected_component or "").casefold()
    material = (option.selected_material or "").casefold()
    carrier = (option.selected_carrier or "").casefold()
    inhibitor = (option.selected_inhibitor or "").casefold()
    if component and component not in text and not (component == "substrate" and "substrate" in text):
        if component == "substrate" and "nonconductive material" in text:
            pass
        else:
            return False
    if material:
        if material == "silicon" and re.search(r"\bsilicon\s+(?:carbide|nitride|oxide)\b", text):
            return False
        if not re.search(rf"\b{re.escape(material)}\b", text):
            return False
    if carrier and carrier.casefold() not in text:
        return False
    if inhibitor:
        aliases = {"pvp": ("pvp", "polyvinylpyrrolidone"), "hpmc": ("hpmc", "hydroxypropylmethylcellulose")}
        if not any(alias in text for alias in aliases.get(inhibitor, (inhibitor,))):
            return False
        if "inhibitor" not in text:
            return False
    return True


def _evidence_set_supports_option(option: PublicOption, evidence: list[PublicEvidence]) -> bool:
    if not evidence or any(item.origin != "source_assertion" for item in evidence):
        return False
    combined_text = " ".join(item.text for item in evidence)
    combined = PublicEvidence(evidence_id="combined", text=combined_text, source_id="combined", source_locator="combined")
    return _evidence_supports_option(option, combined)


class PublicCaseAdapter:
    """Load one development state without traversing evaluator/source archives."""

    def __init__(self, cases_root: Path = CASES_ROOT, organizations_root: Path = ORGS_ROOT) -> None:
        self.cases_root = Path(cases_root)
        self.organizations_root = Path(organizations_root)

    def _profile(self, case_id: str) -> OrganizationProfile:
        profile_id, directory = PROFILE_BINDINGS[case_id]
        path = self.organizations_root / directory / "v1" / "profile.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return OrganizationProfile.model_validate({**payload, "record_id": profile_id})

    @staticmethod
    def _closed_validate(case_id: str, raw: dict[str, Any]) -> None:
        unexpected = sorted(set(raw) - TOP_LEVEL_KEYS[case_id])
        if unexpected:
            raise ValueError(f"unsupported public packet field(s): {', '.join(unexpected)}")
        if case_id == "PTP-0001":
            if not isinstance(raw.get("organization_brief"), dict) or not isinstance(raw.get("candidate_choices"), list):
                raise ValueError("PTP-0001 public packet shape is invalid")
            PublicOrganizationBrief.model_validate(raw["organization_brief"])
            [PublicOption.model_validate(item) for item in raw["candidate_choices"]]
            [PublicChunkRow.model_validate(item) for item in raw.get("active_chunks", [])]
            PublicRules.model_validate(raw["rules"])
        else:
            PublicEvent.model_validate(raw.get("change_event", {}))
            PublicOrganizationRef.model_validate(raw.get("organization_ref", {}))
            stipulations = PublicCaseStipulations.model_validate(raw.get("case_stipulations", {}))
            if case_id == "PTP-0002":
                if stipulations.policy.role_scope != "crystallization_inhibitor":
                    raise ValueError("PTP-0002 policy role scope mismatch")
            if case_id == "PTP-0003" and stipulations.policy.count_kind is None:
                raise ValueError("PTP-0003 policy count kind is required")
            [PublicSourceRow.model_validate(item) for item in raw.get("sources", [])]
            PublicOutputContract.model_validate(raw["output_contract"])

    @staticmethod
    def _validate_declared_policy(case_id: str, event: PublicEvent, policy: PublicPolicy) -> None:
        """Reject event/policy contradictions; never infer a policy delta from a name."""
        if case_id == "PTP-0001" and event.type == "forbid_silicon_substrate" and "silicon" not in policy.forbidden_materials:
            raise ValueError("event/policy conflict: silicon prohibition is not declared in policy")
        if case_id == "PTP-0002" and event.type == "forbid_material_at_role" and policy.role_scope != "crystallization_inhibitor":
            raise ValueError("event/policy conflict: role-scoped prohibition is not declared for crystallization_inhibitor")

    def load(self, case_id: str, state_id: str = "S0") -> LoadedCase:
        if case_id not in PROFILE_BINDINGS:
            raise ValueError(f"unsupported development case: {case_id}")
        case_dir = (self.cases_root / case_id).resolve()
        public_dir = (case_dir / "public-input").resolve()
        if public_dir.parent != case_dir or not public_dir.is_dir():
            raise ValueError("case does not have an isolated public-input directory")
        path = (public_dir / f"{state_id}.json").resolve()
        if path.parent != public_dir or path.suffix.lower() != ".json":
            raise ValueError("state path escapes public-input allowlist")
        raw = json.loads(path.read_text(encoding="utf-8"))
        forbidden = _walk_forbidden(raw)
        if forbidden:
            raise ValueError(forbidden)
        if raw.get("case_id") != case_id:
            raise ValueError("case ID mismatch")
        self._closed_validate(case_id, raw)
        evidence = self._evidence(raw)
        org_ref = raw.get("organization_ref", {})
        profile_id = org_ref.get("profile_id", PROFILE_BINDINGS[case_id][0])
        requested_version = org_ref.get("profile_version")
        if requested_version and requested_version != "1.0.0":
            raise ValueError(f"profile version mismatch: requested {requested_version}, available 1.0.0")
        profile = self._profile(case_id)
        if profile.profile_id != profile_id:
            raise ValueError("case/profile binding mismatch")
        if requested_version and profile.profile_version != requested_version:
            raise ValueError(f"profile version mismatch: requested {requested_version}, loaded {profile.profile_version}")
        change = raw.get("change_event")
        if change is None:
            event_types = {
                "S0": "initial",
                "S1": "forbid_silicon_substrate",
                "S2": "project_name_only",
                "S3": "support_withdrawal",
                "S4": "request_yield_without_new_evidence",
            }
            change = {"type": event_types.get(raw.get("event_id"), "state_change"), "event_order": int(str(raw.get("event_id", "S0")).removeprefix("S") or 0), "description": raw.get("change", "")}
        brief = raw.get("brief") or raw.get("organization_brief", {}).get("goal", "")
        options = raw.get("case_stipulations", {}).get("options", []) or raw.get("candidate_choices", [])
        policy = raw.get("case_stipulations", {}).get("policy", {}) or raw.get("organization_brief", {}).get("policy", {})
        packet = AgentPacket(
            case_id=case_id, state_id=state_id, event=PublicEvent.model_validate(change), brief=brief,
            profile_id=profile.profile_id, profile_version=profile.profile_version,
            policy=PublicPolicy.model_validate(policy), options=[PublicOption.model_validate(item) for item in options], evidence=evidence,
            unknowns=raw.get("case_stipulations", {}).get("unmeasured_fields", ""),
        )
        self._validate_declared_policy(case_id, packet.event, packet.policy)
        return LoadedCase(packet=packet, raw=raw, profile=profile)

    def _evidence(self, raw: dict[str, Any]) -> list[PublicEvidence]:
        rows = raw.get("sources") or raw.get("active_chunks") or []
        evidence: list[PublicEvidence] = []
        for row in rows:
            if "evidence_id" in row:
                locator = dict(row.get("locator", {}))
                if row.get("g08_trimmed_component_offsets") is not None:
                    locator["g08_trimmed_component_offsets"] = row["g08_trimmed_component_offsets"]
                evidence.append(PublicEvidence(
                    evidence_id=row["evidence_id"], text=row["text"], source_id=row["source_id"],
                    source_version=row.get("source_version"), document_id=row.get("document_id"),
                    family_id=row.get("family_id"), source_locator=row.get("source_locator", f"{row['source_id']}#{row['evidence_id']}"),
                    locator=locator, origin=row.get("origin", "source_assertion"), text_sha256=row.get("text_sha256"),
                    char_start=locator.get("char_start"), char_end=locator.get("char_end"),
                ))
            else:
                chunk_id = row["chunk_id"]
                evidence.append(PublicEvidence(
                    evidence_id=chunk_id, text=row["text"], source_id=row["source_id"],
                    source_locator=f"{row['source_id']}#{chunk_id}",
                    locator={"paragraph_id": row.get("paragraph_id"), "char_start": row.get("start"), "char_end": row.get("end")},
                    origin="source_assertion", text_sha256=row.get("sha256"), char_start=row.get("start"), char_end=row.get("end"),
                ))
        return evidence


class IntegrationPipeline:
    """Deterministic options, handoff, revision and report generation."""

    def __init__(self, adapter: PublicCaseAdapter | None = None) -> None:
        self.adapter = adapter or PublicCaseAdapter()

    @staticmethod
    def _generic_result(workflow: WorkflowInput) -> IntegrationResult:
        integrity = IntegrationPipeline._integrity(workflow.evidence)
        invalid = set(integrity["invalid_evidence_ids"])
        facts = [
            {"field": f"evidence:{item.evidence_id}", "state": "known" if item.evidence_id not in invalid else "unknown", "value": item.text if item.evidence_id not in invalid else None, "evidence_ids": [item.evidence_id] if item.evidence_id not in invalid else [], "role": "source_fact" if item.evidence_id not in invalid else "unknown"}
            for item in workflow.evidence
        ]
        facts.extend({"field": unknown, "state": "unknown", "value": None, "evidence_ids": [], "role": "unknown"} for unknown in workflow.unknowns)
        routes: list[dict[str, Any]] = []
        options: list[dict[str, Any]] = []
        forbidden_materials = set(workflow.policy.forbidden_materials)
        forbidden_inhibitors = set(workflow.policy.forbidden_inhibitors)
        policy_scope_reasons: list[str] = []
        unsupported_count_form = bool(workflow.policy.count_kind and workflow.policy.operator not in (None, "<=", "<", "maximum"))
        if unsupported_count_form:
            policy_scope_reasons.append(f"unsupported count policy form: {workflow.policy.operator}")
        for option in workflow.options:
            option_id = option.option_id or option.candidate_id or "unknown"
            evidence_ids = [evidence_id for evidence_id in option.evidence_ids if evidence_id not in invalid and any(item.evidence_id == evidence_id for item in workflow.evidence)]
            selected_material = option.selected_material
            selected_inhibitor = option.selected_inhibitor
            component_matches = not workflow.policy.component or option.selected_component == workflow.policy.component
            route_policy_reasons: list[str] = []
            if not component_matches:
                reason = f"policy component {workflow.policy.component!r} does not match option {option_id}"
                policy_scope_reasons.append(reason)
                route_policy_reasons.append(reason)
            if unsupported_count_form:
                route_policy_reasons.append(f"unsupported count policy form: {workflow.policy.operator}")
            prohibited = component_matches and (selected_material in forbidden_materials or selected_inhibitor in forbidden_inhibitors)
            option_evidence = [item for item in workflow.evidence if item.evidence_id in evidence_ids]
            evidence_supports_option = bool(option_evidence) and _evidence_set_supports_option(option, option_evidence)
            if not evidence_supports_option and not prohibited:
                policy_scope_reasons.append(f"evidence does not support option role/value {option_id}")
                route_policy_reasons.append(f"evidence does not support option role/value {option_id}")
            if not component_matches or unsupported_count_form:
                state = "unknown"
            else:
                state = "fails_this_explicit_check" if prohibited else "passes_this_explicit_check" if evidence_supports_option and len(evidence_ids) == len(option.evidence_ids) else "unknown"
            status = {"passes_this_explicit_check": "candidate", "fails_this_explicit_check": "draft", "unknown": "blocked_by_missing_evidence"}[state]
            label = option.selected_route or selected_material or selected_inhibitor or option_id
            route = {"route_id": f"{workflow.project_id}:{option_id}", "label": f"{option_id}: {label}", "status": status, "policy_check_state": state, "evidence_ids": evidence_ids, "constraint_ids": [workflow.policy.rule_id or f"{workflow.project_id}-policy"], "unknowns": list(workflow.unknowns), "contradictions": [], "policy_scope_status": "matched" if component_matches and not unsupported_count_form else "unknown", "policy_reasons": list(route_policy_reasons)}
            routes.append(route)
            options.append({"option_id": option_id, "label": route["label"], "policy_check_state": state, "evidence_ids": evidence_ids, "unknowns": list(workflow.unknowns)})
        handoff = {"kind": "development_integration_handoff", "status": "ready_for_review" if integrity["valid"] and routes else "draft", "global_blocked": False, "ready_reason": "artifact and traceability checks only; reviewer approval is separate", "review_state": "not_reviewed", "facts_are_not_scientific_validation": True, "policy_scope_reasons": sorted(set(policy_scope_reasons))}
        return IntegrationResult(case_id=workflow.project_id, state_id=str(workflow.event.event_order), project_display_name=workflow.project_id, profile_id=workflow.profile.profile_id, profile_version=workflow.profile.profile_version, brief=workflow.brief, fictional_stipulations={"policy": workflow.policy.model_dump(mode="json"), "options": [option.model_dump(mode="json") for option in workflow.options], "basis": "caller-supplied bounded workflow input; not a real-organization fact"}, interpretations=[{"statement": "unsupported or absent evidence remains unknown", "basis": "generic offline workflow rule"}], allowed_evidence=[item.model_dump(mode="json") for item in workflow.evidence], source_integrity=integrity, interface_status={"typed_core": {"status": "used", "records": ["EvidenceRecord", "RouteRecord", "ChangeRecord"]}, "organization_profiles": {"status": "used", "profile_id": workflow.profile.profile_id, "profile_version": workflow.profile.profile_version}, "ingestion": {"status": "not_invoked"}, "retrieval": {"status": "not_invoked"}, "extraction": {"status": "deterministic_packet_rule_adapter", "model_called": False}}, source_facts=facts, options=options, routes=routes, unknowns=sorted(set(workflow.unknowns)), proposed_next_tests=[{"test_id": f"{workflow.project_id}-NEXT-001", "purpose": "verify unresolved route fields with a bounded measurement", "status": "proposed", "inputs": list(workflow.unknowns)}], handoff=handoff, agent_input_fields=sorted(workflow.model_dump().keys()))

    def run_workflow(self, workflow: WorkflowInput) -> IntegrationResult:
        """Run a new permitted packet without case-ID-specific lookup."""
        return self._generic_result(workflow)

    def run_workflow_sequence(self, workflows: list[WorkflowInput]) -> dict[str, Any]:
        """Run caller-supplied revisions and persist/read back typed records."""
        if not workflows:
            raise ValueError("workflow sequence must not be empty")
        repo = SQLiteRecordRepository()
        states: list[dict[str, Any]] = []
        changes: list[dict[str, Any]] = []
        previous: IntegrationResult | None = None
        for workflow in workflows:
            result = self.run_workflow(workflow)
            route_history = repo.history("RouteRecord", f"{workflow.project_id}:{workflow.options[0].option_id or workflow.options[0].candidate_id}")
            version = (route_history[-1]["version"] + 1) if route_history else 1
            previous_version = route_history[-1]["version"] if route_history else None
            for evidence in workflow.evidence:
                if evidence.evidence_id not in set(result.source_integrity["invalid_evidence_ids"]):
                    repo.save(EvidenceRecord(record_id=evidence.evidence_id, evidence_id=evidence.evidence_id, source_id=evidence.source_id, locator=evidence.source_locator, claim=evidence.text, role="source_fact", state=EvidenceState.SUPPORTED, quote=evidence.text, char_start=evidence.char_start, char_end=evidence.char_end, version=version))
            for route in result.routes:
                record = RouteRecord(record_id=route["route_id"], route_id=route["route_id"], project_id=workflow.project_id, label=route["label"], status=route["status"], evidence_ids=route["evidence_ids"], constraint_ids=route["constraint_ids"], unknowns=route["unknowns"], version=version)
                repo.save(record)
                read_back = repo.read_latest("RouteRecord", record.record_id, RouteRecord)
                if read_back is None or read_back.model_dump(mode="json") != record.model_dump(mode="json"):
                    raise RuntimeError(f"workflow route read-back failed: {record.route_id}")
            state = result.model_dump(mode="json")
            states.append(state)
            if previous is not None:
                affected, preserved = self._diff_fields(previous.model_dump(mode="json"), state)
                change = ChangeRecord(record_id=f"{workflow.project_id}:S{workflow.event.event_order}", change_id=f"{workflow.project_id}:S{workflow.event.event_order}", entity_type="integration_result", entity_id=workflow.project_id, before_version=previous_version, after_version=version, affected_fields=affected, preserved_fields=preserved, reason=workflow.event.type, source_refs=[item.evidence_id for item in workflow.evidence])
                repo.save(change)
                read_back = repo.read_latest("ChangeRecord", change.record_id, ChangeRecord)
                if read_back is None or read_back.model_dump(mode="json") != change.model_dump(mode="json"):
                    raise RuntimeError(f"workflow change read-back failed: {change.change_id}")
                changes.append({"state_id": result.state_id, "reason": change.reason, "before_version": change.before_version, "after_version": change.after_version, "affected_fields": affected, "preserved_fields": preserved, "before": previous.model_dump(mode="json"), "after": state, "read_back": True, "route_history_versions": [entry["version"] for entry in repo.history("RouteRecord", result.routes[0]["route_id"]) ]})
            previous = result
        repo.close()
        return {"case_id": workflows[0].project_id, "states": states, "changes": changes, "evaluations": []}

    @staticmethod
    def write_workflow_reports(report: dict[str, Any], output_dir: Path, elapsed_seconds: float) -> None:
        """Export a caller-supplied workflow run without implying benchmark status."""
        output_dir.mkdir(parents=True, exist_ok=True)
        metrics = {
            "state_count": len(report["states"]),
            "change_count": len(report["changes"]),
            "source_integrity": all(state["source_integrity"]["valid"] for state in report["states"]),
            "sqlite_read_back": all(change["read_back"] for change in report["changes"]),
            "elapsed_seconds": elapsed_seconds,
            "benchmark": False,
            "paid_api": False,
        }
        payload = {"kind": "bounded_offline_workflow_prototype", "input_mode": "caller_supplied_schema", "report": report, "metrics": metrics}
        (output_dir / "workflow.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        lines = ["# Bounded offline workflow prototype", "", "This is a caller-supplied development workflow, not a held-out benchmark.", "", f"- States: {metrics['state_count']}", f"- Changes: {metrics['change_count']}", f"- Source integrity: {'PASS' if metrics['source_integrity'] else 'FAIL'}", f"- SQLite read-back: {'PASS' if metrics['sqlite_read_back'] else 'FAIL'}", f"- Elapsed seconds: {elapsed_seconds:.6f}", "- Paid API/model/GPU: NOT_RUN", ""]
        for state in report["states"]:
            lines.append(f"## {state['case_id']} state {state['state_id']}")
            lines.append(f"Brief: {state['brief']}")
            lines.append("Routes:")
            for route in state["routes"]:
                lines.append(f"- {route['route_id']}: {route['status']} / {route['policy_check_state']}; evidence={','.join(route['evidence_ids']) or 'none'}; unknowns={','.join(route['unknowns']) or 'none'}")
            lines.append(f"Handoff: {state['handoff']['status']} (review={state['handoff']['review_state']})")
        if report["changes"]:
            lines.extend(["", "## Before/after changes"])
            for change in report["changes"]:
                lines.append(f"- {change['state_id']}: {change['reason']}; affected={','.join(change['affected_fields']) or 'none'}; preserved={','.join(change['preserved_fields']) or 'none'}; read_back={change['read_back']}")
        (output_dir / "workflow.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        rows = []
        for state in report["states"]:
            routes = "<br>".join(html.escape(f"{route['route_id']}: {route['status']} / {route['policy_check_state']} / evidence={','.join(route['evidence_ids']) or 'none'}") for route in state["routes"])
            evidence = "<br>".join(html.escape(f"{item['evidence_id']}: {item['text']} ({item['source_locator']})") for item in state["allowed_evidence"])
            rows.append(f"<tr><td>{html.escape(state['state_id'])}</td><td>{html.escape(state['brief'])}<br><b>Evidence:</b><br>{evidence or 'none'}</td><td>{routes}</td><td>{html.escape(state['handoff']['status'])}</td></tr>")
        html_doc = "<!doctype html><meta charset='utf-8'><title>Offline workflow prototype</title><style>body{font:16px system-ui;max-width:1200px;margin:2rem auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:.5rem;vertical-align:top}</style><h1>Bounded offline workflow prototype</h1><p>Caller-supplied schema; not a held-out benchmark or scientific result.</p><table><tr><th>State</th><th>Input/evidence</th><th>Routes</th><th>Pack readiness</th></tr>" + "".join(rows) + "</table>"
        (output_dir / "workflow.html").write_text(html_doc, encoding="utf-8")

    @staticmethod
    def _integrity(evidence: list[PublicEvidence]) -> dict[str, Any]:
        invalid: list[str] = []
        reasons: dict[str, list[str]] = {}
        for item in evidence:
            if item.text_sha256 and _sha256_text(item.text) != item.text_sha256:
                invalid.append(item.evidence_id)
                reasons.setdefault(item.evidence_id, []).append("text_sha256_mismatch")
            if item.char_start is not None and item.char_end is not None and item.char_end < item.char_start:
                invalid.append(item.evidence_id)
                reasons.setdefault(item.evidence_id, []).append("reverse_span")
            if item.char_start is not None and item.char_end is not None and item.char_end - item.char_start != len(item.text):
                invalid.append(item.evidence_id)
                reasons.setdefault(item.evidence_id, []).append("span_length_mismatch")
            locator = item.locator.model_dump(mode="json")
            locator_start = locator.get("char_start")
            locator_end = locator.get("char_end")
            if (locator_start is None) != (locator_end is None):
                invalid.append(item.evidence_id)
                reasons.setdefault(item.evidence_id, []).append("incomplete_locator_span")
            elif locator_start is not None and locator_end - locator_start != len(item.text):
                invalid.append(item.evidence_id)
                reasons.setdefault(item.evidence_id, []).append("locator_span_length_mismatch")
            top_level_present = item.char_start is not None or item.char_end is not None
            if top_level_present and (item.char_start, item.char_end) != (locator_start, locator_end):
                invalid.append(item.evidence_id)
                reasons.setdefault(item.evidence_id, []).append("non_canonical_top_level_span")
            if locator.get("offset_unit") not in (None, "Unicode code points, end-exclusive"):
                invalid.append(item.evidence_id)
                reasons.setdefault(item.evidence_id, []).append("unsupported_offset_unit")
            trimmed = locator.get("g08_trimmed_component_offsets")
            if trimmed and trimmed.get("char_end", 0) - trimmed.get("char_start", 0) != len(item.text):
                invalid.append(item.evidence_id)
                reasons.setdefault(item.evidence_id, []).append("trimmed_span_length_mismatch")
        return {"checked": len(evidence), "valid": not invalid, "invalid_evidence_ids": sorted(set(invalid)), "reasons": reasons}

    @staticmethod
    def _evidence_ok(packet: AgentPacket, evidence_ids: list[str], integrity: dict[str, Any]) -> list[str]:
        invalid = set(integrity["invalid_evidence_ids"])
        return [evidence_id for evidence_id in evidence_ids if evidence_id not in invalid and any(item.evidence_id == evidence_id for item in packet.evidence)]

    @staticmethod
    def _facts(packet: AgentPacket, integrity: dict[str, Any]) -> list[dict[str, Any]]:
        invalid = set(integrity["invalid_evidence_ids"])

        def usable(matches: list[PublicEvidence]) -> list[PublicEvidence]:
            return [item for item in matches if item.evidence_id not in invalid]

        facts: list[dict[str, Any]] = []
        if packet.case_id == "PTP-0001":
            for material in ("silicon", "glass"):
                if material == "silicon":
                    # Exact material token plus the substrate role. This does
                    # not allow "silicon carbide" or another compound to stand
                    # in for substrate evidence.
                    matches = [
                        e for e in packet.evidence
                        if re.search(r"\bsubstrate\b.*\bsilicon\b|\bsilicon\b.*\bsubstrate\b", e.text, re.I)
                        and not re.search(r"\bsilicon\s+(?:carbide|nitride|oxide)\b", e.text, re.I)
                    ]
                else:
                    matches = [e for e in packet.evidence if re.search(r"\bnonconductive material such as glass\b", e.text, re.I)]
                matches = usable(matches)
                facts.append({"field": f"substrate_{material}", "state": "known" if matches else "unknown", "value": material if matches else None, "evidence_ids": [e.evidence_id for e in matches], "role": "source_fact"})
            facts.append({"field": "measured_production_yield", "state": "unknown", "value": None, "evidence_ids": [], "role": "unknown"})
        elif packet.case_id == "PTP-0002":
            patterns = {"PEG_role": r"carrier.*polyethylene glycol|polyethylene glycol.*PEG", "PVP_role": r"crystallization inhibitor.*polyvinylpyrrolidone", "HPMC_role": r"crystallization inhibitor.*hydroxypropylmethylcellulose"}
            for field, pattern in patterns.items():
                matches = usable([e for e in packet.evidence if re.search(pattern, e.text, re.IGNORECASE)])
                facts.append({"field": field, "state": "known" if matches else "unknown", "value": field.removesuffix("_role") if matches else None, "evidence_ids": [e.evidence_id for e in matches], "role": "source_fact" if matches else "unknown"})
            facts.append({"field": "measured_production_yield", "state": "unknown", "value": None, "evidence_ids": [], "role": "unknown"})
        else:
            intermediate = usable([e for e in packet.evidence if re.search(r"five intermediate stages", e.text, re.I)])
            btc = usable([e for e in packet.evidence if re.search(r"BTC.*two of the five stages", e.text, re.I)])
            facts.extend([
                {"field": "reported_intermediate_stage_count", "state": "known" if intermediate else "unknown", "value": 5 if intermediate else None, "evidence_ids": [e.evidence_id for e in intermediate], "role": "source_fact" if intermediate else "unknown"},
                {"field": "BTC_stage_use_count", "state": "known" if btc else "unknown", "value": 2 if btc else None, "evidence_ids": [e.evidence_id for e in btc], "role": "source_fact" if btc else "unknown"},
                {"field": "all_manufacturing_operations", "state": "unknown", "value": None, "evidence_ids": [], "role": "unknown"},
                {"field": "numeric_total_batch_cost", "state": "unknown", "value": None, "evidence_ids": [], "role": "unknown"},
            ])
        return facts

    def _policy_state(self, case: str, option: PublicOption, packet: AgentPacket, facts: list[dict[str, Any]], integrity: dict[str, Any]) -> tuple[str, list[str], list[str]]:
        constraint_ids = [packet.policy.rule_id or f"{case}-policy"]
        if case == "PTP-0001":
            material = option.selected_material
            forbidden = set(packet.policy.forbidden_materials)
            fact = next((f for f in facts if f["field"] == f"substrate_{material}"), None)
            evidence_ids = self._evidence_ok(packet, fact["evidence_ids"] if fact else [], integrity)
            matched = bool(fact and fact["state"] == "known")
            return ("fails_this_explicit_check" if material in forbidden else "passes_this_explicit_check" if matched and evidence_ids else "unknown", evidence_ids, constraint_ids)
        if case == "PTP-0002":
            inhibitor = option.selected_inhibitor
            forbidden = set(packet.policy.forbidden_inhibitors)
            fact = next((f for f in facts if f["field"] == f"{inhibitor}_role"), None)
            carrier = next((f for f in facts if f["field"] == "PEG_role"), None)
            raw_evidence_ids = sorted(set((fact["evidence_ids"] if fact else []) + (carrier["evidence_ids"] if carrier else [])))
            evidence_ids = self._evidence_ok(packet, raw_evidence_ids, integrity)
            all_required_facts = bool(fact and carrier and fact["state"] == "known" and carrier["state"] == "known")
            all_required_evidence_valid = len(evidence_ids) == len(raw_evidence_ids)
            return ("fails_this_explicit_check" if inhibitor in forbidden else "passes_this_explicit_check" if all_required_facts and all_required_evidence_valid else "unknown", evidence_ids, constraint_ids)
        count = next((f for f in facts if f["field"] == packet.policy.count_kind), None)
        maximum = packet.policy.maximum
        evidence_ids = self._evidence_ok(packet, count["evidence_ids"] if count else [], integrity)
        if not count or count["state"] != "known":
            return "unknown", evidence_ids, constraint_ids
        if maximum is not None and count["value"] > maximum:
            return "fails_this_explicit_check", evidence_ids, constraint_ids
        return "passes_this_explicit_check", evidence_ids, constraint_ids

    def run_state(self, loaded: LoadedCase) -> IntegrationResult:
        packet = loaded.packet
        integrity = self._integrity(packet.evidence)
        facts = self._facts(packet, integrity)
        options: list[dict[str, Any]] = []
        routes: list[dict[str, Any]] = []
        for option in packet.options:
            option_id = option.option_id or option.candidate_id or "unknown"
            state, evidence_ids, constraint_ids = self._policy_state(packet.case_id, option, packet, facts, integrity)
            if packet.case_id == "PTP-0001":
                label = f"{option_id}: {option.selected_material or 'unknown'} substrate"
            elif packet.case_id == "PTP-0002":
                label = f"{option_id}: {option.selected_inhibitor or 'unknown'} inhibitor with {option.selected_carrier or 'unknown'} carrier"
            else:
                label = f"{option_id}: {option.selected_route or 'document route'}"
            route_status = "candidate" if state == "passes_this_explicit_check" else "blocked_by_missing_evidence" if state == "unknown" else "draft"
            unknowns = ["measured production yield"] if packet.case_id != "PTP-0003" else ["all manufacturing operations", "numeric total batch cost"]
            route = {"route_id": f"{packet.case_id}:{option_id}", "label": label, "status": route_status, "policy_check_state": state, "evidence_ids": evidence_ids, "constraint_ids": constraint_ids, "unknowns": unknowns, "contradictions": []}
            options.append({"option_id": option_id, "label": label, "policy_check_state": state, "evidence_ids": evidence_ids, "unknowns": unknowns})
            routes.append(route)
        all_traceable = all(route["evidence_ids"] or route["status"] == "blocked_by_missing_evidence" for route in routes)
        ready = all_traceable and bool(routes)
        tests = [{"test_id": f"{packet.case_id}-NEXT-001", "purpose": "measure unresolved fields before any feasibility conclusion", "status": "proposed", "inputs": [item["field"] for item in facts if item["state"] == "unknown"]}]
        handoff = {"kind": "development_integration_handoff", "status": "ready_for_review" if ready else "draft", "global_blocked": False, "ready_reason": "artifact and traceability checks only; reviewer approval is separate", "review_state": "not_reviewed", "facts_are_not_scientific_validation": True}
        return IntegrationResult(case_id=packet.case_id, state_id=packet.state_id, project_display_name=loaded.raw.get("project_display_name", loaded.raw.get("display_name", packet.case_id)), profile_id=packet.profile_id, profile_version=packet.profile_version, brief=packet.brief, fictional_stipulations={"policy": packet.policy, "options": packet.options, "basis": "public development case stipulation; not a real-organization fact"}, interpretations=[{"statement": "policy_check_state means only the explicit packet check passed, failed, or lacks current support", "basis": "deterministic integration rule"}, {"statement": "route status does not establish feasibility, efficacy, safety, regulatory approval, patentability, or FTO", "basis": "product authority boundary"}], allowed_evidence=[item.model_dump(mode="json") for item in packet.evidence], source_integrity=integrity, interface_status={"typed_core": {"status": "used", "records": ["EvidenceRecord", "RouteRecord", "ChangeRecord"]}, "organization_profiles": {"status": "used", "profile_id": packet.profile_id, "profile_version": packet.profile_version}, "ingestion": {"status": "not_invoked", "reason": "the current public packet supplies allowlisted spans, not a raw CSV input"}, "retrieval": {"status": "not_invoked", "reason": "fixed-source development packets prohibit corpus expansion or expected-document lookup"}, "extraction": {"status": "deterministic_packet_rule_adapter", "model_called": False, "reason": "case-local role/count rules preserve packet locators without claiming semantic entailment"}}, source_facts=facts, options=options, routes=routes, unknowns=sorted({u for route in routes for u in route["unknowns"]}), proposed_next_tests=tests, handoff=handoff, agent_input_fields=sorted(packet.model_dump().keys()))

    def run_case(self, case_id: str) -> dict[str, Any]:
        states = sorted((self.adapter.cases_root / case_id / "public-input").glob("S*.json"))
        results: list[IntegrationResult] = []
        changes: list[dict[str, Any]] = []
        repo = SQLiteRecordRepository()
        previous: IntegrationResult | None = None
        previous_packet: AgentPacket | None = None
        evaluations: list[dict[str, Any]] = []
        for state_path in states:
            state_id = state_path.stem
            loaded = self.adapter.load(case_id, state_id)
            result = self.run_state(loaded)
            results.append(result)
            evaluation = DevelopmentEvaluator.evaluate(loaded.packet, result, previous, sqlite_payload_read_back=True)
            evaluations.append(evaluation.model_dump(mode="json"))
            first_route_id = result.routes[0]["route_id"]
            first_route_history = repo.history("RouteRecord", first_route_id)
            version = first_route_history[-1]["version"] + 1 if first_route_history else 1
            previous_version = first_route_history[-1]["version"] if first_route_history else None
            for evidence in loaded.packet.evidence:
                if evidence.evidence_id not in set(result.source_integrity["invalid_evidence_ids"]):
                    evidence_history = repo.history("EvidenceRecord", evidence.evidence_id)
                    evidence_version = evidence_history[-1]["version"] + 1 if evidence_history else version
                    repo.save(EvidenceRecord(record_id=evidence.evidence_id, evidence_id=evidence.evidence_id, source_id=evidence.source_id, locator=evidence.source_locator, claim=evidence.text, role="source_fact", state=EvidenceState.SUPPORTED, quote=evidence.text, char_start=evidence.char_start, char_end=evidence.char_end, version=evidence_version))
            for route in result.routes:
                route_history = repo.history("RouteRecord", route["route_id"])
                route_version = route_history[-1]["version"] + 1 if route_history else version
                record = RouteRecord(record_id=route["route_id"], route_id=route["route_id"], project_id=case_id, label=route["label"], status=route["status"], evidence_ids=route["evidence_ids"], constraint_ids=route["constraint_ids"], unknowns=route["unknowns"], version=route_version)
                repo.save(record)
                read_route = repo.read_latest("RouteRecord", route["route_id"], RouteRecord)
                expected_payload = record.model_dump(mode="json")
                actual_payload = read_route.model_dump(mode="json") if read_route else None
                if read_route is None or actual_payload != expected_payload:
                    raise RuntimeError(f"route payload/status read-back failed: {route['route_id']}")
            if previous:
                before = previous.model_dump(mode="json")
                after = result.model_dump(mode="json")
                affected, preserved = self._diff_fields(before, after)
                change = ChangeRecord(record_id=f"{case_id}:{state_id}", change_id=f"{case_id}:{state_id}", entity_type="integration_result", entity_id=case_id, before_version=previous_version, after_version=version, affected_fields=affected, preserved_fields=preserved, reason=loaded.packet.event.type, source_refs=[e.evidence_id for e in loaded.packet.evidence])
                repo.save(change)
                read_back = repo.read_latest("ChangeRecord", change.record_id, ChangeRecord)
                if read_back is None or read_back.change_id != change.change_id:
                    raise RuntimeError(f"change record read-back failed: {change.change_id}")
                changes.append({"state_id": state_id, "reason": change.reason, "affected_fields": affected, "preserved_fields": preserved, "before": before, "after": after, "read_back": True, "evaluation": evaluation.model_dump(mode="json")})
            previous = result
            previous_packet = loaded.packet
        repo.close()
        return {"case_id": case_id, "states": [item.model_dump(mode="json") for item in results], "changes": changes, "evaluations": evaluations}

    @staticmethod
    def _diff_fields(before: dict[str, Any], after: dict[str, Any]) -> tuple[list[str], list[str]]:
        affected: list[str] = []
        preserved: list[str] = []
        for field in sorted(set(before) | set(after)):
            if field in {"state_id", "project_display_name"}:
                continue
            (preserved if before.get(field) == after.get(field) else affected).append(field)
        return affected, preserved

    def run_all(self) -> dict[str, Any]:
        started = time.perf_counter()
        cases = [self.run_case(case_id) for case_id in ("PTP-0001", "PTP-0002", "PTP-0003")]
        elapsed = time.perf_counter() - started
        evaluations = [evaluation for case in cases for evaluation in case["evaluations"]]
        failures = [failure for evaluation in evaluations for failure in evaluation["failures"]]
        return {"kind": "development_integration_evidence", "benchmark": False, "cases": cases, "metrics": {"case_count": len(cases), "state_count": sum(len(c["states"]) for c in cases), "elapsed_seconds": elapsed, "source_integrity": all(s["source_integrity"]["valid"] for c in cases for s in c["states"]), "required_changes_recorded": all(evaluation["required_changes"] for evaluation in evaluations), "revision_read_back": all(change["read_back"] for c in cases for change in c["changes"]), "sqlite_payload_read_back": all(evaluation["sqlite_payload_read_back"] for evaluation in evaluations), "preservation_checked": all(evaluation["preservation"] for evaluation in evaluations), "unknown_handling_checked": all(evaluation["unknown_handling"] for evaluation in evaluations), "route_local_status_checked": all(evaluation["route_local_status"] for evaluation in evaluations), "evaluator_passed": all(evaluation["passed"] for evaluation in evaluations), "failures": failures}, "api_smoke": {"status": "NOT_RUN", "reason": "No paid API/GPU/RunPod call was authorized"}}

    @staticmethod
    def write_reports(report: dict[str, Any], output_dir: Path) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "integration.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        metrics = report["metrics"]
        lines = ["# G09/G10 development integration report", "", "This is deterministic offline development evidence, not a model benchmark.", "", f"- Cases: {metrics['case_count']}", f"- States: {metrics['state_count']}", f"- Elapsed seconds: {metrics['elapsed_seconds']:.6f}", f"- Source integrity: {'PASS' if metrics['source_integrity'] else 'FAIL'}", f"- Required changes: {'PASS' if metrics['required_changes_recorded'] else 'FAIL'}", f"- Preservation: {'PASS' if metrics['preservation_checked'] else 'FAIL'}", f"- Unknown handling: {'PASS' if metrics['unknown_handling_checked'] else 'FAIL'}", f"- Route-local status: {'PASS' if metrics['route_local_status_checked'] else 'FAIL'}", f"- SQLite route payload/status read-back: {'PASS' if metrics['sqlite_payload_read_back'] else 'FAIL'}", f"- Independent evaluator: {'PASS' if metrics['evaluator_passed'] else 'FAIL'}", f"- Failures: {len(metrics['failures'])}", "", "## State summary", ""]
        for case in report["cases"]:
            lines.append(f"### {case['case_id']}")
            for state in case["states"]:
                labels = ", ".join(f"{o['option_id']}={o['policy_check_state']}" for o in state["options"])
                lines.append(f"- {state['state_id']}: {labels}; handoff={state['handoff']['status']}; evidence={state['source_integrity']['checked']}")
            for change in case["changes"]:
                lines.append(f"- {change['state_id']} revision {change['reason']}: affected={', '.join(change['affected_fields']) or 'none'}; preserved={', '.join(change['preserved_fields']) or 'none'}")
        (output_dir / "integration.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        rows = []
        for case in report["cases"]:
            for state in case["states"]:
                input_text = html.escape(state["brief"])
                evidence = "<br>".join(html.escape(str(e["evidence_id"]) + " — " + str(e["text"]) + " (" + str(e["source_locator"]) + ")") for e in state["allowed_evidence"])
                facts = "<br>".join(html.escape(str(e["field"]) + ": " + str(e["value"])) for e in state["source_facts"] if e["value"] is not None)
                outputs = "<br>".join(html.escape(str(route["route_id"]) + ": " + str(route["status"]) + " / " + str(route["policy_check_state"])) for route in state["routes"])
                changes = "<br>".join(html.escape(str(c["state_id"]) + ": " + str(c["reason"]) + " | affected=" + ", ".join(c["affected_fields"]) + " | preserved=" + ", ".join(c["preserved_fields"])) for c in case["changes"])
                rows.append(f"<tr><td>{case['case_id']}</td><td>{state['state_id']}</td><td><b>Brief:</b> {input_text}<br><b>Evidence:</b><br>{evidence or 'none'}<br><b>Facts:</b><br>{facts or 'unknown'}</td><td>{outputs}<br><b>Next test:</b> {html.escape(str(state['proposed_next_tests'][0]['purpose']))}</td><td>{html.escape(state['handoff']['status'])}</td></tr>")
            rows.append(f"<tr><td colspan='5'><b>{case['case_id']} before/after changes:</b><br>{changes or 'none'}</td></tr>")
        html_doc = "<!doctype html><meta charset='utf-8'><title>G09/G10 integration</title><style>body{font:16px system-ui;max-width:1200px;margin:2rem auto}table{border-collapse:collapse;width:100%}td,th{border:1px solid #aaa;padding:.5rem;vertical-align:top}td{max-width:520px}</style><h1>G09/G10 development integration</h1><p>Deterministic offline evidence; not a model benchmark or scientific validation.</p><table><tr><th>Case</th><th>State</th><th>Input/evidence/facts</th><th>Options/routes/next test</th><th>Handoff</th></tr>" + "".join(rows) + "</table>"
        (output_dir / "integration.html").write_text(html_doc, encoding="utf-8")
