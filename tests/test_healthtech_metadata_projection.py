"""Company query fields must respect the same external policy as source fields."""
import json
from pathlib import Path

import pytest

from patent_to_pilot.healthtech.engine import DossierInput, run_dossier, serialize_dossier
from patent_to_pilot.healthtech.contracts import SourceRights


@pytest.mark.parametrize("purpose", ["product_display", "redistribution"])
def test_company_metadata_projection_preserves_authored_edits_and_local_record(purpose):
    root = Path(__file__).resolve().parents[1]
    data = DossierInput.model_validate_json(
        (root / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8")
    )
    dossier, _, _ = run_dossier(data, run_id="metadata-projection", code_commit="test")
    source = dossier.sources[0]
    payload = {"reviewed": "visible", "restricted": "private-copy"}
    from patent_to_pilot.healthtech.sources import source_payload
    policy = SourceRights(
        rights_id="authored-policy", basis_url="https://example.invalid/rights",
        checked_date="2026-10-30", basis_revision="r1", basis_sha256="a" * 64,
        clause_locator="authored-fixture", clause="Authored test fields only",
        interpretation="Positive and negative fixture", acquisition="ALLOWED",
        local_evaluation="ALLOWED", product_display="ALLOWED", redistribution="ALLOWED",
        displayable_fields=["reviewed"], limits=[],
    )
    source = source_payload(
        source.source.source_id, payload, uri="https://example.invalid/source",
        revision="r1", source_date=source.source_date, jurisdiction="US",
        source_type="regulatory_record", license_note="Authored fixture", synthetic=False, rights=policy,
    )
    query = dossier.query.model_copy(update={
        "company_source_id": source.source.source_id,
        "company_metadata": {"reviewed": "visible", "restricted": "private-copy", "unmapped": "missing"},
    })
    dossier = dossier.model_copy(update={"query": query, "sources": [source], "evidence": [], "candidates": [], "user_edits": {"note": "authored note"}})
    local = serialize_dossier(dossier)
    external = serialize_dossier(dossier, purpose=purpose)
    assert external["query"]["company_metadata"] == {"reviewed": "visible"}
    assert external["user_edits"] == {"note": "authored note"}
    assert "private-copy" not in json.dumps(external)
    assert local["query"]["company_metadata"]["restricted"] == "private-copy"
    assert serialize_dossier(dossier) == local
    changed = dossier.model_copy(update={"query": query.model_copy(update={"company_metadata": {"reviewed": "forged"}})})
    assert serialize_dossier(changed, purpose=purpose)["query"]["company_metadata"] == {}
