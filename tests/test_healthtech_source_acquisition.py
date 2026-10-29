from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from patent_to_pilot.evaluation.healthtech.source_acquisition import (
    SourceAcquisitionError,
    source_snapshot_sha256,
    stage_authorized_semantic_source,
)


def _manifest(snapshot_sha256: str, *, expected_bytes: int = 12, expected_files: int = 2) -> dict:
    return {
        "format": "ht-semantic-source-authorization-v1",
        "status": "APPROVED_LOCAL_RESEARCH_SOURCE",
        "source": {
            "source_id": "fixture-semantic-source",
            "source_revision": "fixture-v1",
            "source_sha256": snapshot_sha256,
            "locator": "fixture://semantic-source/v1",
            "source_class": "licensed_reviewer_export",
        },
        "rights": {
            "rights_policy_id": "fixture-semantic-rights",
            "rights_basis": "authored fixture authorization",
            "rights_clause": "local research only; no provider transfer or redistribution",
            "intended_use": "semantic_relevance_judgment",
            "use_decision": "ALLOWED_LOCAL_RESEARCH",
            "provider_transfer_allowed": False,
            "public_redistribution_allowed": False,
            "attribution_required": True,
        },
        "acquisition": {
            "retrieval_method": "authorized_local_copy",
            "resumable": True,
            "expected_bytes": expected_bytes,
            "max_bytes": expected_bytes + 10,
            "expected_files": expected_files,
            "max_files": expected_files + 2,
            "storage_relpath": "fixture/semantic-source",
            "raw_relpath": "fixture/semantic-source/raw.jsonl",
            "normalized_relpath": "fixture/semantic-source/normalized.jsonl",
        },
        "judgment_contract": {
            "allowed_labels": ["relevant", "not_relevant"],
            "absent_pair_policy": "unjudged_not_negative",
            "exact_locator_required": True,
            "adjudicator_role_required": True,
        },
        "cohort_requirements": {
            "minimum_independent_company_groups": 2,
            "minimum_independent_family_groups": 2,
            "final_holdout_predeclared": True,
            "cross_split_leakage_policy": "reject",
        },
    }


def _auth_sha256(manifest: dict) -> str:
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode("utf-8")).hexdigest()


def test_stages_authorized_snapshot_and_reuses_verified_files(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "raw.jsonl").write_text("raw-data", encoding="utf-8")
    (source / "normalized.jsonl").write_text("norm", encoding="utf-8")
    manifest = _manifest(source_snapshot_sha256(source), expected_bytes=12)
    destination = tmp_path / "destination"
    receipt_path = tmp_path / "receipt.json"

    receipt = stage_authorized_semantic_source(
        source,
        destination,
        manifest,
        authorization_sha256=_auth_sha256(manifest),
        receipt_path=receipt_path,
    )
    assert receipt["status"] == "PASS"
    assert receipt["completed_files"] == 2
    assert all(item["status"] == "staged" for item in receipt["files"])
    assert (destination / "fixture/semantic-source/raw.jsonl").read_text(encoding="utf-8") == "raw-data"
    assert (destination / "fixture/semantic-source/normalized.jsonl").read_text(encoding="utf-8") == "norm"

    resumed = stage_authorized_semantic_source(
        source,
        destination,
        manifest,
        authorization_sha256=_auth_sha256(manifest),
        receipt_path=receipt_path,
    )
    assert resumed["status"] == "PASS"
    assert all(item["status"] == "reused" for item in resumed["files"])


def test_cli_stages_local_fixture(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "raw.jsonl").write_text("raw-data", encoding="utf-8")
    (source / "normalized.jsonl").write_text("norm", encoding="utf-8")
    manifest = _manifest(source_snapshot_sha256(source), expected_bytes=12)
    authorization_path = tmp_path / "authorization.json"
    authorization_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    receipt_path = tmp_path / "receipt.json"
    result = subprocess.run(
        [
            sys.executable,
            "scripts/healthtech/acquire_semantic_source.py",
            "--authorization-manifest",
            str(authorization_path),
            "--source-root",
            str(source),
            "--destination-root",
            str(tmp_path / "destination"),
            "--receipt",
            str(receipt_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "PASS"
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["status"] == "PASS"


def test_resumes_matching_partial_file(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "raw.jsonl").write_text("raw-data", encoding="utf-8")
    (source / "normalized.jsonl").write_text("norm", encoding="utf-8")
    manifest = _manifest(source_snapshot_sha256(source), expected_bytes=12)
    destination = tmp_path / "destination"
    partial = destination / "fixture/semantic-source/raw.jsonl.partial"
    partial.parent.mkdir(parents=True)
    partial.write_text("raw-", encoding="utf-8")

    receipt = stage_authorized_semantic_source(
        source,
        destination,
        manifest,
        authorization_sha256=_auth_sha256(manifest),
        receipt_path=tmp_path / "receipt.json",
    )
    assert receipt["status"] == "PASS"
    assert not partial.exists()
    assert (destination / "fixture/semantic-source/raw.jsonl").read_text(encoding="utf-8") == "raw-data"


@pytest.mark.parametrize("mutation", ["wrong_hash", "wrong_bytes", "wrong_files", "overlap", "stale_receipt"])
def test_acquisition_fails_closed(tmp_path: Path, mutation: str):
    source = tmp_path / "source"
    source.mkdir()
    (source / "raw.jsonl").write_text("raw-data", encoding="utf-8")
    (source / "normalized.jsonl").write_text("norm", encoding="utf-8")
    manifest = _manifest(source_snapshot_sha256(source), expected_bytes=12)
    destination = tmp_path / "destination"
    receipt_path = tmp_path / "receipt.json"
    if mutation == "wrong_hash":
        manifest["source"]["source_sha256"] = "a" * 64
    elif mutation == "wrong_bytes":
        manifest["acquisition"]["expected_bytes"] = 11
    elif mutation == "wrong_files":
        manifest["acquisition"]["expected_files"] = 3
    elif mutation == "overlap":
        destination = source / "nested-destination"
    elif mutation == "stale_receipt":
        stage_authorized_semantic_source(
            source,
            destination,
            manifest,
            authorization_sha256=_auth_sha256(manifest),
            receipt_path=receipt_path,
        )
        manifest["source"]["source_revision"] = "fixture-v2"

    with pytest.raises(SourceAcquisitionError):
        stage_authorized_semantic_source(
            source,
            destination,
            manifest,
            authorization_sha256=_auth_sha256(manifest),
            receipt_path=receipt_path,
        )
