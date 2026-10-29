from __future__ import annotations

import json
from pathlib import Path

import pytest

from patent_to_pilot.healthtech.abbott import build_abbott_case_inputs
from patent_to_pilot.healthtech.contracts import content_hash
from scripts.healthtech.migrate_legacy_cohort_rights import (
    CohortRightsMigrationError,
    migrate_legacy_cohort_rights,
)
from test_healthtech_repairs import _write_json, _write_synthetic_abbott_cohort


ROOT = Path(__file__).resolve().parents[1]
RIGHTS_MATRIX = ROOT / "docs/healthtech/audits/luna-patent-dossiers-20261028-rights-cohort/rights-matrix.json"


def _make_legacy_copy(tmp_path: Path) -> Path:
    cohort = _write_synthetic_abbott_cohort(tmp_path)
    registry_path = cohort / "source_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for row in registry["sources"]:
        row.pop("rights_policy_id", None)
        row["rights"] = "legacy fixture rights; local-only"
    _write_json(registry_path, registry)
    manifest_path = cohort / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_registry_sha256"] = content_hash(registry)
    _write_json(manifest_path, manifest)
    return cohort


def test_migration_reseals_only_registry_and_produces_adapter_compatible_copy(tmp_path: Path):
    source = _make_legacy_copy(tmp_path / "source")
    output = tmp_path / "output"
    runtime_before = (source / "runtime.json").read_bytes()
    raw_before = (source / "raw" / "abbott-patents.html").read_bytes()

    report = migrate_legacy_cohort_rights(source, output, rights_matrix_path=RIGHTS_MATRIX)

    assert report["status"] == "PASS_LOCAL_TYPED_RIGHTS_MIGRATION"
    assert report["changed_rows"] == len(
        json.loads((source / "source_registry.json").read_text(encoding="utf-8"))["sources"]
    )
    registry = json.loads((output / "source_registry.json").read_text(encoding="utf-8"))
    assert {row["rights_policy_id"] for row in registry["sources"]} == {
        "openfda-pma-records",
        "google-patents-pages",
        "abbott-product-patent-disclosures",
    }
    assert (output / "runtime.json").read_bytes() == runtime_before
    assert (output / "raw" / "abbott-patents.html").read_bytes() == raw_before
    assert len(build_abbott_case_inputs(output)) == 3


def test_migration_rejects_unreviewed_policy_mapping_without_output(tmp_path: Path):
    source = _make_legacy_copy(tmp_path / "source")
    registry_path = source / "source_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["sources"][0]["source_id"] = "unreviewed-source"
    _write_json(registry_path, registry)
    manifest_path = source / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["source_registry_sha256"] = content_hash(registry)
    _write_json(manifest_path, manifest)

    output = tmp_path / "output"
    with pytest.raises((ValueError, CohortRightsMigrationError), match="no typed rights policy"):
        migrate_legacy_cohort_rights(source, output, rights_matrix_path=RIGHTS_MATRIX)
    assert not output.exists()


def test_migration_enforces_storage_bound_before_copy(tmp_path: Path):
    source = _make_legacy_copy(tmp_path / "source")
    with pytest.raises(CohortRightsMigrationError, match="storage bound"):
        migrate_legacy_cohort_rights(
            source,
            tmp_path / "output",
            rights_matrix_path=RIGHTS_MATRIX,
            max_storage_bytes=1,
        )
