from __future__ import annotations

import json
from pathlib import Path

import pytest

from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs
from patent_to_pilot.healthtech.engine import export_markdown, run_dossier, serialize_dossier
from patent_to_pilot.healthtech.history import select_version, save_version, source_view
from patent_to_pilot.healthtech.rights import RightsBoundaryError
from patent_to_pilot.healthtech.sources import field_evidence
from test_healthtech_repairs import _write_json, _write_synthetic_abbott_cohort


ROOT = Path(__file__).resolve().parents[1]
RIGHTS_MATRIX = ROOT / "docs/healthtech/audits/luna-patent-dossiers-20261028-rights-cohort/rights-matrix.json"


def test_external_boundary_matrix_rebuilds_evidence_after_history_reload(tmp_path: Path):
    cohort = _write_synthetic_abbott_cohort(tmp_path)
    rights = json.loads(RIGHTS_MATRIX.read_text(encoding="utf-8"))
    for policy in rights["sources"]:
        policy["intended_use"]["product_display"] = "ALLOWED"
        policy["intended_use"]["redistribution"] = "ALLOWED"
        policy["displayable_fields"] = ["trade_name"] if policy["source_id"] == "openfda-pma-records" else []
    rights_path = tmp_path / "rights-matrix.json"
    _write_json(rights_path, rights)

    input_data = next(iter(build_abbott_case_inputs(cohort, rights_matrix_path=rights_path).values()))
    pma = next(source for source in input_data.sources if source.source.source_type == "regulatory_record")
    dossier, _, _ = run_dossier(input_data, run_id="boundary-matrix", code_commit="test")
    dossier = dossier.model_copy(update={
        "evidence": dossier.evidence + [
            field_evidence(pma, "trade_name", "MATRIX-STRUCTURED").model_copy(update={
                "statement": "restricted-structured-value",
                "structured_value": "restricted-structured-value",
            }),
            field_evidence(pma, "trade_name", "MATRIX-LITERAL").model_copy(update={
                "locator": "chars:0:12",
                "quoted_span": "restricted-literal-value",
                "structured_field": None,
                "structured_value": None,
                "extraction_method": "literal_span",
                "statement": "restricted-literal-value",
            }),
        ]
    })
    history = tmp_path / "history"
    save_version(history, dossier)
    reloaded = select_version(history)

    for purpose in ("product_display", "redistribution"):
        for language in ("en", "th"):
            markdown = export_markdown(reloaded, language=language, purpose=purpose)
            assert "restricted-structured-value" not in markdown
            assert "restricted-literal-value" not in markdown
            assert "trade_name: MitraClip" in markdown
        serialized = serialize_dossier(reloaded, purpose=purpose)
        encoded = json.dumps(serialized, ensure_ascii=False)
        assert "restricted-structured-value" not in encoded
        assert "restricted-literal-value" not in encoded
        assert serialized["sources"][0]["payload"] == {"trade_name": "MitraClip"}
        assert source_view(reloaded, pma.source.source_id, field="trade_name", purpose=purpose)["payload"] == {
            "trade_name": "MitraClip"
        }
        with pytest.raises(RightsBoundaryError, match="displayable_fields"):
            source_view(reloaded, pma.source.source_id, field="openfda", purpose=purpose)
