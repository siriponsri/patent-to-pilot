from __future__ import annotations

import pytest

from patent_to_pilot.evaluation.healthtech.source_authorization import (
    SourceAuthorizationError,
    validate_semantic_source_authorization,
)


def _manifest() -> dict:
    return {
        "format": "ht-semantic-source-authorization-v1",
        "status": "APPROVED_LOCAL_RESEARCH_SOURCE",
        "source": {
            "source_id": "fixture-semantic-source",
            "source_revision": "fixture-v1",
            "source_sha256": "a" * 64,
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
            "expected_bytes": 1000,
            "max_bytes": 2000,
            "expected_files": 2,
            "max_files": 4,
            "storage_relpath": "permitted/semantic-source",
            "raw_relpath": "permitted/semantic-source/raw.jsonl",
            "normalized_relpath": "permitted/semantic-source/normalized.jsonl",
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


def test_valid_authorization_reports_bounds_and_label_contract():
    report = validate_semantic_source_authorization(_manifest())
    assert report["status"] == "PASS"
    assert report["source_id"] == "fixture-semantic-source"
    assert report["storage_bounds"]["max_bytes"] == 2000
    assert report["allowed_labels"] == ["not_relevant", "relevant"]
    assert report["absent_pair_policy"] == "unjudged_not_negative"
    assert report["final_holdout_predeclared"] is True


@pytest.mark.parametrize("mutation", [
    "provider_transfer",
    "oversized_bytes",
    "not_resumable",
    "unsafe_path",
    "wrong_labels",
    "missing_holdout",
    "too_few_groups",
    "wrong_intended_use",
])
def test_authorization_fails_closed(mutation: str):
    payload = _manifest()
    if mutation == "provider_transfer":
        payload["rights"]["provider_transfer_allowed"] = True
    elif mutation == "oversized_bytes":
        payload["acquisition"]["expected_bytes"] = 3000
    elif mutation == "not_resumable":
        payload["acquisition"]["resumable"] = False
    elif mutation == "unsafe_path":
        payload["acquisition"]["raw_relpath"] = "../outside.jsonl"
    elif mutation == "wrong_labels":
        payload["judgment_contract"]["allowed_labels"] = ["relevant", "maybe"]
    elif mutation == "missing_holdout":
        payload["cohort_requirements"]["final_holdout_predeclared"] = False
    elif mutation == "too_few_groups":
        payload["cohort_requirements"]["minimum_independent_company_groups"] = 1
    elif mutation == "wrong_intended_use":
        payload["rights"]["intended_use"] = "product_disclosure"
    with pytest.raises(SourceAuthorizationError):
        validate_semantic_source_authorization(payload)
