"""Offline development inventory/calibration; never a provider dispatcher."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from patent_to_pilot.evaluation.comparison import (
    OfflineComparisonRunner, _forbidden_paths, _runtime_output, stage_public_states,
    validate_public_packet, validate_public_profile, validate_runtime_output,
)
from patent_to_pilot.integration.pipeline import IntegrationPipeline, PublicCaseAdapter

ROOT = Path(__file__).resolve().parents[3]
CASE_IDS = ("PTP-0001", "PTP-0002", "PTP-0003")
STATE_IDS = ("S0", "S1", "S2", "S3", "S4")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def split_violations(rows: list[dict[str, Any]], *, cross_org_claim: bool = False) -> list[str]:
    """Check declared identities before variants; never inspect held-out answers."""
    failures: list[str] = []
    fields = ["case_id", "family_id", "source_publication", "template_cluster", "component_id"]
    if cross_org_claim:
        fields.append("organization_id")
    for field in fields:
        seen: dict[str, set[str]] = {}
        for row in rows:
            value = row.get(field)
            if value is not None:
                seen.setdefault(str(value), set()).add(row["split"])
        failures += [f"{field} crosses splits: {value}" for value, splits in seen.items() if len(splits) > 1]
    for row in rows:
        if row.get("already_exposed") and row["split"] != "development":
            failures.append(f"exposed case cannot become held-out: {row['case_id']}")
        if row["split"] != "development" and not row.get("family_id"):
            failures.append(f"unverified family cannot establish family-disjoint holdout: {row['case_id']}")
    return failures


def current_stage(case_id: str, state_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Materialize only the requested public packet/profile, not a source archive."""
    if case_id not in CASE_IDS or state_id not in STATE_IDS:
        raise ValueError("unsupported development case/state")
    loaded = PublicCaseAdapter().load(case_id, state_id)
    packet = loaded.packet.model_dump(mode="json")
    profile = loaded.profile.model_dump(mode="json")
    validate_public_packet(packet)
    validate_public_profile(profile)
    return {"packet": packet, "profile": profile}, loaded.raw


def validate_output_contract(schema: Any) -> None:
    if not isinstance(schema, dict):
        raise ValueError("output contract must be an object")
    forbidden = _forbidden_paths(schema, "$.output_contract")
    if forbidden:
        raise ValueError("evaluator-only schema field(s): " + ", ".join(forbidden))


def calibrate() -> list[dict[str, Any]]:
    """Supported positives plus deliberate errors; not independent scientific gold."""
    records: list[dict[str, Any]] = []
    pipeline = IntegrationPipeline()
    for case in CASE_IDS:
        loaded = PublicCaseAdapter().load(case, "S0")
        result = pipeline.run_state(loaded)
        positive = bool(result.source_integrity["valid"]) and any(
            option["policy_check_state"] == "passes_this_explicit_check" for option in result.options
        )
        records.append({"control": f"{case}:supported_positive", "expected": True, "observed": positive, "passed": positive})

    stage = stage_public_states(state_ids=("S0",))[0]
    base = _runtime_output(stage, pipeline.run_state(stage.loaded))
    mutations = [
        ("missing_event_id", lambda o: o.pop("event_id")),
        ("wrong_case_id", lambda o: o.update(case_id="OTHER")),
        ("wrong_option_id", lambda o: o["options"][0].update(candidate_id="OTHER")),
        ("invalid_policy_state", lambda o: o["options"][0].update(policy_check_state="approved")),
        ("unknown_evidence_id", lambda o: o["options"][0].update(current_support_ids=["NOT_IN_PACKET"])),
        ("invented_yield", lambda o: o["options"][0].update(measured_production_yield={"state": "unknown", "value": 99})),
    ]
    for name, mutate in mutations:
        output = copy.deepcopy(base)
        mutate(output)
        validation = validate_runtime_output(stage, output)
        records.append({"control": name, "expected": False, "observed": validation["passed"], "passed": not validation["passed"], "failures": validation["failures"]})

    policy_stage = stage_public_states(state_ids=("S1",))[0]
    result = pipeline.run_state(policy_stage.loaded).model_copy(deep=True)
    result.routes[0].update(policy_check_state="passes_this_explicit_check", status="candidate")
    state = OfflineComparisonRunner(stages=[policy_stage])._record_state(stage=policy_stage, result=result, previous=None)
    records.append({"control": "shape_valid_false_policy_pass", "expected": False, "observed": state["validator"]["passed"], "passed": not state["validator"]["passed"]})
    return records


def build_preflight(plan: dict[str, Any], output: Path) -> dict[str, Any]:
    # This API has no live switch and does not import a provider transport.
    if plan.get("mode") != "offline-preflight" or plan.get("live_enabled") is not False:
        raise ValueError("offline-only plan required; credentials/live execution are unsupported")
    if plan.get("case_ids") != list(CASE_IDS) or plan.get("state_ids") != list(STATE_IDS):
        raise ValueError("this preflight inventories exactly the existing development fixtures")
    if not isinstance(plan.get("split_rows"), list) or {r.get("case_id") for r in plan["split_rows"]} != set(CASE_IDS):
        raise ValueError("explicit current-case split rows required")
    if len(plan["split_rows"]) != len(CASE_IDS) or any(not r.get("already_exposed") for r in plan["split_rows"]):
        raise ValueError("all three current cases must remain explicitly exposed development")
    if any(plan.get(field) for field in ("validation", "final_test", "held_out_organizations")):
        raise ValueError("no held-out panel exists for this development preflight")
    registry = json.loads((ROOT/"methodology/evaluation/splits/g06-dev-assignments.json").read_text(encoding="utf-8"))
    authoritative = {row["case_id"]: row for row in registry["assignments"]}
    for row in plan["split_rows"]:
        known = authoritative[row["case_id"]]
        publication = known.get("source_publication") or known.get("source_publication_crosscheck")
        if (row.get("family_id"), row.get("source_publication"), row.get("template_cluster")) != (known.get("family_id"), publication, known["template_cluster"]):
            raise ValueError("split provenance differs from existing development registry")
    failures = split_violations(plan["split_rows"])
    if failures:
        raise ValueError("; ".join(failures))
    output = Path(output)
    if output.exists():
        raise FileExistsError("choose a fresh output directory; retained evidence is never overwritten")
    # Validate every input before creating output files.
    inputs = []
    for case in CASE_IDS:
        for state in STATE_IDS:
            payload, _ = current_stage(case, state)
            integrity = IntegrationPipeline._integrity(PublicCaseAdapter().load(case, state).packet.evidence)
            if not integrity["valid"]:
                raise ValueError(f"invalid public evidence: {case}/{state}")
            schema = ROOT/"methodology/evaluation/cases"/case/"public-input/output-schema.json"
            contract = json.loads(schema.read_text(encoding="utf-8"))
            validate_output_contract(contract)
            inputs.append((case, state, payload, schema, contract))
    calibration = calibrate()
    if not all(r["passed"] for r in calibration):
        raise ValueError("evaluator calibration failed")
    output.mkdir(parents=True)
    staged = []
    for case, state, payload, schema_source, schema in inputs:
        directory = output/"curator-staged-current-inputs"/case/state
        directory.mkdir(parents=True)
        for name, obj in [("runtime-input.json", payload), ("output-contract.json", schema)]:
            (directory/name).write_text(json.dumps(obj, indent=2), encoding="utf-8")
        staged.append({"case_id": case, "state_id": state, "files": {p.name: sha256(p) for p in directory.iterdir()}, "source_packet_sha256": sha256(ROOT/"methodology/evaluation/cases"/case/"public-input"/(state+".json")), "source_schema_sha256": sha256(schema_source)})
    comparison = OfflineComparisonRunner(run_id=plan["plan_id"]+"-mechanics").run()
    (output/"comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    report = {
        "status": "PASS" if comparison["status"] == "PASS" else "FAIL",
        "scope": "offline development readiness, not scientific execution",
        "scientific_live_ready": False,
        "plan_id": plan["plan_id"], "plan_sha256": hashlib.sha256(json.dumps(plan, sort_keys=True).encode()).hexdigest(),
        "public_case_count": len(CASE_IDS), "public_state_count": len(staged),
        "independent_sample_claim": False, "held_out_case_count": 0,
        "staged_inputs": staged, "calibration": calibration,
        "split_violations": failures,
        "comparison_methods": list(comparison["methods"]), "comparison_case_ids": ["PTP-0001"],
        "comparison_states": comparison["state_ids"],
        "mock_call_records": sum(len(m["provider_calls"]) for m in comparison["methods"].values()),
        "provider_calls": 0, "api_cost_usd": 0,
        "generation": "DETERMINISTIC_AND_MOCK_ONLY",
        "scientific_blockers": [
            "No common live generation/response adapter for B1/B2/B3/P in this runner",
            "PTP-0002/0003 do not have the current PTP-0001 common comparison output adapter",
            "No process/filesystem-isolated evaluated worker; staged folders alone are not a security boundary",
            "All three current cases are exposed dev; no held-out family/template panel",
            "B4-RG/DR NOT_IMPLEMENTED; verified shared distractor/recovery pool absent",
            "Input tokenizer/framing upper bound and fresh endpoint/pricing snapshot not verified",
            "No new scientific payload/matrix/budget approval; old echo approval is not reusable",
        ],
    }
    (output/"preflight.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report
