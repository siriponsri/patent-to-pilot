from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import socket

import pytest

from patent_to_pilot.healthtech.contracts import (
    AcquisitionBudget,
    DeviceQuery,
    EvidenceItem,
    PatentCandidate,
    SourceRights,
)
from patent_to_pilot.healthtech.engine import DossierInput, PatentInput, run_dossier
from patent_to_pilot.healthtech.sources import source_payload
from scripts.healthtech.run_pilot_task import run_pilot_task


def _rights(
    *,
    rights_id: str,
    source_prefix: str,
    source_type: str,
    product_display: str,
    displayable_fields: list[str],
) -> SourceRights:
    return SourceRights(
        rights_id=rights_id,
        source_id_prefixes=[source_prefix],
        source_types=[source_type],
        basis_url="https://example.invalid/terms",
        checked_date=date(2026, 10, 29),
        basis_revision="fixture-v1",
        basis_sha256="a" * 64,
        clause_locator="fixture-terms",
        clause="Fixture source-use clause",
        interpretation="Fixture rights basis for local engineering tests",
        acquisition="ALLOWED",
        local_evaluation="ALLOWED_LOCAL_RESEARCH",
        product_display=product_display,
        redistribution=product_display,
        displayable_fields=displayable_fields,
    )


def _public_dossier() -> object:
    regulatory = source_payload(
        "regulatory-source",
        {"device_name": "Fixture device", "pma_number": "P000001"},
        uri="https://example.invalid/regulatory",
        revision="reg-v1",
        source_date=date(2026, 10, 29),
        jurisdiction="US",
        source_type="regulatory_record",
        license_note="Fixture public record",
        synthetic=False,
        rights=_rights(
            rights_id="regulatory-rights",
            source_prefix="regulatory-source",
            source_type="regulatory_record",
            product_display="ALLOWED_WITH_ATTRIBUTION",
            displayable_fields=["device_name", "pma_number"],
        ),
    )
    disclosure = source_payload(
        "disclosure-source",
        {"patents": ["1234567"]},
        uri="https://example.invalid/marking",
        revision="disclosure-v1",
        source_date=date(2026, 10, 29),
        jurisdiction="US",
        source_type="independent_disclosure",
        license_note="Fixture disclosure, local-only",
        synthetic=False,
        rights=_rights(
            rights_id="disclosure-rights",
            source_prefix="disclosure-source",
            source_type="independent_disclosure",
            product_display="BLOCKED_LOCAL",
            displayable_fields=[],
        ),
    )
    patent_source = source_payload(
        "patent-source",
        "A fixture patent document body.",
        uri="https://example.invalid/patent",
        revision="patent-v1",
        source_date=date(2026, 10, 29),
        jurisdiction="US",
        source_type="patent_document",
        license_note="Fixture patent text, local-only",
        synthetic=False,
        rights=_rights(
            rights_id="patent-rights",
            source_prefix="patent-source",
            source_type="patent_document",
            product_display="BLOCKED_LOCAL",
            displayable_fields=[],
        ),
    )
    query = DeviceQuery(
        query_id="HT-TEST-PILOT",
        brief={
            "project_id": "healthtech-pilot-test",
            "version": 1,
            "objective": "Test a public dossier workflow",
            "audience": "entrepreneur",
            "data_class": "public",
            "language": "en",
            "theme": "formal-light",
        },
        device_id_raw="Fixture device (P000001)",
        device_id_canonical="P000001",
        selected_comparator_source_id="regulatory-source",
        technical_description="fixture device patent",
        features_of_interest=["fixture"],
        user_questions=["Which link needs review?"],
        jurisdiction="US",
        evidence_cutoff=date(2026, 10, 29),
        permitted_inputs=["regulatory-source", "disclosure-source"],
        acquisition_budget=AcquisitionBudget(max_search_calls=1, max_returned_candidates=5),
    )
    evidence = EvidenceItem(
        evidence_id="FACT-DEVICE",
        source_id="regulatory-source",
        source_version="reg-v1",
        payload_hash=regulatory.source.sha256,
        locator="field:device_name",
        structured_field="device_name",
        structured_value="Fixture device",
        evidence_kind="regulatory_record",
        statement="device_name: Fixture device",
        support_basis="Supplied source field",
        jurisdiction="US",
        source_date=date(2026, 10, 29),
        extraction_method="structured_field",
    )
    disclosure_evidence = EvidenceItem(
        evidence_id="DISC-DEVICE",
        source_id="disclosure-source",
        source_version="disclosure-v1",
        payload_hash=disclosure.source.sha256,
        locator="field:patents",
        structured_field="patents",
        structured_value=["1234567"],
        evidence_kind="patent_disclosure",
        statement="The fixture disclosure lists one patent.",
        support_basis="Independent disclosure fixture",
        jurisdiction="US",
        source_date=date(2026, 10, 29),
        extraction_method="structured_field",
    )
    data = DossierInput(
        query=query,
        sources=[regulatory, disclosure],
        patents=[
            PatentInput(patent_id="US1234567A1", title="Fixture patent", source=patent_source),
            PatentInput(patent_id="US7654321A1", title="Fixture distractor", source=patent_source.model_copy(update={
                "source": patent_source.source.model_copy(update={"source_id": "patent-source-2", "record_id": "patent-source-2"})
            })),
        ],
        evidence=[evidence, disclosure_evidence],
        policy_id="HT-B0b",
    )
    dossier, _, _ = run_dossier(data, run_id="pilot-fixture", code_commit="test")
    linked = PatentCandidate(
        patent_id_raw="US1234567A1",
        patent_id_canonical="US1234567A1",
        source_id="patent-source",
        source_revision="patent-v1",
        retrieval_action_ids=["fixture-step-1"],
        scores={"fixture": 1.0},
        association_status="disclosed_link",
        disclosure_evidence_id="DISC-DEVICE",
    )
    retrieved = PatentCandidate(
        patent_id_raw="US7654321A1",
        patent_id_canonical="US7654321A1",
        source_id="patent-source-2",
        source_revision="patent-v1",
        retrieval_action_ids=["fixture-step-1"],
        scores={"fixture": 0.5},
    )
    return type(dossier).model_validate(
        dossier.model_dump(mode="json")
        | {"candidates": [linked.model_dump(mode="json"), retrieved.model_dump(mode="json")]}
    )


def test_pilot_task_runs_real_history_and_rights_aware_export(tmp_path, monkeypatch):
    dossier_path = tmp_path / "dossier.json"
    dossier_path.write_text(_public_dossier().model_dump_json(indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(socket, "create_connection", lambda *args, **kwargs: pytest.fail("network used"))
    monkeypatch.setattr(socket.socket, "connect", lambda *args, **kwargs: pytest.fail("network used"))

    receipt = run_pilot_task(
        dossier_path,
        tmp_path / "run",
        source_id="regulatory-source",
        field="pma_number",
    )

    assert receipt["status"] == "PASS_OFFLINE_ENGINEERING_TASK"
    assert receipt["provider_calls"] == receipt["network_calls"] == 0
    assert receipt["paid_cost_usd"] == 0.0
    assert receipt["candidate_counts"]["disclosed_link"] == 1
    assert receipt["candidate_counts"]["retrieved_candidate"] == 1
    assert receipt["history"]["versions"] == [1, 2]
    assert receipt["export"]["purpose"] == "local_research"
    assert receipt["external_projection"]["status"] == "BLOCKED_LOCAL"
    assert receipt["external_projection"]["payload_written"] is False

    exported = json.loads((tmp_path / "run" / "export-v2" / "dossier.json").read_text(encoding="utf-8"))
    assert exported["version"] == 2
    assert exported["user_edits"]["readiness-decision"].startswith("Corrected:")
    blocked = {
        item["source"]["source_id"]: item["payload"]
        for item in exported["sources"]
        if item["source"]["source_id"] in {"disclosure-source", "patent-source", "patent-source-2"}
    }
    assert blocked["patent-source"] == "A fixture patent document body."
    assert blocked["patent-source-2"] == "A fixture patent document body."
    assert "Fixture patent document body" not in (tmp_path / "run" / "export-v2" / "dossier.en.md").read_text(encoding="utf-8")


def test_pilot_task_records_sanitized_failure_for_blocked_source(tmp_path):
    dossier_path = tmp_path / "dossier.json"
    dossier_path.write_text(_public_dossier().model_dump_json(indent=2) + "\n", encoding="utf-8")
    output = tmp_path / "failed"
    with pytest.raises(Exception):
        run_pilot_task(
            dossier_path,
            output,
            source_id="patent-source",
            field="claims",
            purpose="product_display",
        )
    receipt = json.loads((output / "task_receipt.json").read_text(encoding="utf-8"))
    assert receipt["status"] == "FAILED_OFFLINE_ENGINEERING_TASK"
    assert receipt["failure_type"] in {"RightsBoundaryError", "DossierHistoryError", "ValueError"}
    assert "Fixture patent document body" not in (output / "task_receipt.json").read_text(encoding="utf-8")
