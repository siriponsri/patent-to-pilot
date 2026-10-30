from __future__ import annotations

import hashlib

import pytest

from patent_to_pilot.evaluation.healthtech.judgments import (
    JudgmentValidationError,
    validate_relevance_judgment_manifest,
)


RUNTIME_SHA = "a" * 64
SOURCE_SHA = "b" * 64


def _manifest() -> dict:
    return {
        "format": "ht-relevance-judgment-cohort-v1",
        "status": "DRAFT_VALIDATED_RELEVANCE_JUDGMENT_COHORT",
        "runtime_sha256": RUNTIME_SHA,
        "runtime_exclusions": [
            "semantic_judgments",
            "split_answers",
            "gold_derived_query_variants",
            "family_labels",
        ],
        "sources": [{
            "source_id": "fixture-judgment-source",
            "source_revision": "fixture-v1",
            "source_sha256": SOURCE_SHA,
            "rights_policy_id": "authored-fixture-local",
            "intended_use": "semantic_relevance_judgment",
            "use_decision": "ALLOWED_LOCAL_RESEARCH",
            "locator": "fixture://judgments/v1",
        }],
        "judgments": [
            {
                "judgment_id": "J1",
                "query_id": "Q1",
                "patent_id_raw": "US1234567B2",
                "patent_id_canonical": "US1234567B2",
                "label": "relevant",
                "basis": "authored_fixture",
                "synthetic": True,
                "source_id": "fixture-judgment-source",
                "source_revision": "fixture-v1",
                "source_sha256": SOURCE_SHA,
                "locator": "fixture://judgments/v1#J1",
            },
            {
                "judgment_id": "J2",
                "query_id": "Q2",
                "patent_id_raw": "US7654321B2",
                "patent_id_canonical": "US7654321B2",
                "label": "not_relevant",
                "basis": "authored_fixture",
                "synthetic": True,
                "source_id": "fixture-judgment-source",
                "source_revision": "fixture-v1",
                "source_sha256": SOURCE_SHA,
                "locator": "fixture://judgments/v1#J2",
            },
        ],
        "split_rows": [
            {"query_id": "Q1", "split": "development", "company_group_id": "COMP-A", "family_group_id": "FAM-A"},
            {"query_id": "Q2", "split": "final_holdout", "company_group_id": "COMP-B", "family_group_id": "FAM-B"},
        ],
        "holdout_policy": {
            "company_disjoint": True,
            "family_disjoint": True,
            "require_family_mapping_for_final_holdout": True,
        },
    }


def test_valid_manifest_reports_open_world_counts_and_holdout_readiness():
    report = validate_relevance_judgment_manifest(
        _manifest(),
        runtime_query_ids=["Q1", "Q2"],
        runtime_universe=["US1234567B2", "US7654321B2", "US9999999B2"],
        runtime_sha256=RUNTIME_SHA,
    )
    assert report["status"] == "PASS"
    assert report["judged_pair_count"] == 2
    assert report["unjudged_pair_count"] == 4
    assert report["label_counts"] == {"not_relevant": 1, "relevant": 1}
    assert report["generalization_status"] == "DESCRIPTIVE_HOLDOUT_READY"


@pytest.mark.parametrize("mutation", [
    "duplicate_pair",
    "product_disclosure_basis",
    "cross_split_company",
    "cross_split_family",
    "source_hash_mismatch",
    "missing_runtime_exclusion",
])
def test_invalid_judgment_manifests_fail_closed(mutation: str):
    payload = _manifest()
    if mutation == "duplicate_pair":
        payload["judgments"].append(dict(payload["judgments"][0], judgment_id="J3"))
    elif mutation == "product_disclosure_basis":
        payload["judgments"][0]["basis"] = "product_disclosure"
    elif mutation == "cross_split_company":
        payload["split_rows"][1]["company_group_id"] = "COMP-A"
    elif mutation == "cross_split_family":
        payload["split_rows"][1]["family_group_id"] = "FAM-A"
    elif mutation == "source_hash_mismatch":
        payload["judgments"][0]["source_sha256"] = "c" * 64
    elif mutation == "missing_runtime_exclusion":
        payload["runtime_exclusions"].remove("family_labels")
    with pytest.raises(JudgmentValidationError):
        validate_relevance_judgment_manifest(
            payload,
            runtime_query_ids=["Q1", "Q2"],
            runtime_universe=["US1234567B2", "US7654321B2", "US9999999B2"],
            runtime_sha256=RUNTIME_SHA,
        )


def test_runtime_hash_mismatch_is_rejected():
    with pytest.raises(JudgmentValidationError, match="runtime SHA"):
        validate_relevance_judgment_manifest(
            _manifest(),
            runtime_query_ids=["Q1", "Q2"],
            runtime_universe=["US1234567B2", "US7654321B2"],
            runtime_sha256="d" * 64,
        )


@pytest.mark.parametrize("mutation", ["unknown_query", "unknown_patent"])
def test_judgments_reject_runtime_boundary_escapes(mutation: str):
    payload = _manifest()
    if mutation == "unknown_query":
        payload["judgments"][0]["query_id"] = "Q-UNKNOWN"
    else:
        payload["judgments"][0]["patent_id_raw"] = "US0000000B2"
        payload["judgments"][0]["patent_id_canonical"] = "US0000000B2"
    with pytest.raises(JudgmentValidationError):
        validate_relevance_judgment_manifest(
            payload,
            runtime_query_ids=["Q1", "Q2"],
            runtime_universe=["US1234567B2", "US7654321B2", "US9999999B2"],
            runtime_sha256=RUNTIME_SHA,
        )
