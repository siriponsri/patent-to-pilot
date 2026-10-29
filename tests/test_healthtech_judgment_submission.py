from __future__ import annotations

import pytest

from patent_to_pilot.evaluation.healthtech.judgment_submission import (
    JudgmentSubmissionError,
    build_relevance_judgment_manifest,
)
from patent_to_pilot.evaluation.healthtech.review_packet import build_relevance_review_packet
from patent_to_pilot.evaluation.healthtech.judgments import validate_relevance_judgment_manifest


def _packet() -> dict:
    runtime = {
        "format": "ht-runtime-v1",
        "status": "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS",
        "runtime_exclusions": ["semantic_judgments", "split_answers", "gold_derived_query_variants", "family_labels"],
        "devices": [
            {"query_id": "Q-DEV", "device_id_raw": "Device D", "device_id_canonical": "D", "company": "Alpha", "trade_name": "Device D", "source_id": "device-source", "evidence_cutoff": "2026-10-29"},
            {"query_id": "Q-HOLD", "device_id_raw": "Device H", "device_id_canonical": "H", "company": "Beta", "trade_name": "Device H", "source_id": "device-source", "evidence_cutoff": "2026-10-29"},
        ],
        "patents": [
            {"patent_id_raw": "1234567", "patent_id_canonical": "US1234567B2", "document_kind": "US-grant", "jurisdiction": "US", "title": "One", "abstract": "a", "claims": "a", "text": "a", "source_id": "patent-source", "source_revision": "r1", "source_url": "fixture://one", "raw_html_sha256": "a" * 64, "normalized_sha256": "b" * 64, "source_date": "2026-10-29"},
            {"patent_id_raw": "7654321", "patent_id_canonical": "US7654321B2", "document_kind": "US-grant", "jurisdiction": "US", "title": "Two", "abstract": "b", "claims": "b", "text": "b", "source_id": "patent-source", "source_revision": "r1", "source_url": "fixture://two", "raw_html_sha256": "c" * 64, "normalized_sha256": "d" * 64, "source_date": "2026-10-29"},
        ],
    }
    split_manifest = {
        "format": "ht-development-final-holdout-split-v1",
        "rows": [
            {"query_id": "Q-DEV", "split": "development", "group_id": "alpha::g1"},
            {"query_id": "Q-HOLD", "split": "final_holdout", "group_id": "beta::g2"},
        ],
    }
    groups = {"company_groups": [
        {"company": "Alpha", "query_ids": ["Q-DEV"]},
        {"company": "Beta", "query_ids": ["Q-HOLD"]},
    ]}
    source_registry = {"sources": [
        {"source_id": "device-source", "source_revision": "device-v1", "source_sha256": "e" * 64, "rights_policy_id": "fixture-device", "intended_use": "semantic_relevance_judgment", "use_decision": "ALLOWED_LOCAL_RESEARCH", "locator": "fixture://device"},
        {"source_id": "patent-source", "source_revision": "patent-v1", "source_sha256": "f" * 64, "rights_policy_id": "fixture-patent", "intended_use": "semantic_relevance_judgment", "use_decision": "ALLOWED_LOCAL_RESEARCH", "locator": "fixture://patent"},
    ]}
    return build_relevance_review_packet(
        runtime,
        split_manifest,
        groups,
        {"sources": [
            {"source_id": "device-source", "source_type": "official_fact", "revision": "device-v1", "rights_policy_id": "fixture-device", "rights": "fixture", "runtime_allowed": True, "url": "fixture://device"},
            {"source_id": "patent-source", "source_type": "patent_document", "revision": "patent-v1", "rights_policy_id": "fixture-patent", "rights": "fixture", "runtime_allowed": True, "url": "fixture://patent"},
        ]},
        runtime_path="runtime.json", runtime_sha256="a" * 64,
        split_manifest_path="split.json", split_manifest_sha256="b" * 64,
        groups_path="groups.json", groups_sha256="c" * 64,
        source_registry_path="sources.json", source_registry_sha256="d" * 64,
    )


def _source_manifest() -> dict:
    return {"sources": [{
        "source_id": "expert-fixture",
        "source_revision": "expert-v1",
        "source_sha256": "1" * 64,
        "rights_policy_id": "fixture-expert-local",
        "intended_use": "semantic_relevance_judgment",
        "use_decision": "ALLOWED_LOCAL_RESEARCH",
        "locator": "fixture://expert-v1",
    }]}


def _authorization_manifest() -> dict:
    return {
        "format": "ht-semantic-source-authorization-v1",
        "status": "APPROVED_LOCAL_RESEARCH_SOURCE",
        "source": {
            "source_id": "expert-fixture",
            "source_revision": "expert-v1",
            "source_sha256": "1" * 64,
            "locator": "fixture://expert-v1",
            "source_class": "licensed_reviewer_export",
        },
        "rights": {
            "rights_policy_id": "fixture-expert-local",
            "rights_basis": "authored fixture authorization",
            "rights_clause": "local research only",
            "intended_use": "semantic_relevance_judgment",
            "use_decision": "ALLOWED_LOCAL_RESEARCH",
            "provider_transfer_allowed": False,
            "public_redistribution_allowed": False,
            "attribution_required": True,
        },
        "acquisition": {
            "retrieval_method": "authorized_local_copy",
            "resumable": True,
            "expected_bytes": 1,
            "max_bytes": 2,
            "expected_files": 1,
            "max_files": 2,
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


def _submission(**overrides) -> list[dict]:
    row = {
        "review_row_id": "Q-DEV::US1234567B2",
        "label": "relevant",
        "basis": "expert_adjudication",
        "source_id": "expert-fixture",
        "source_revision": "expert-v1",
        "source_sha256": "1" * 64,
        "locator": "fixture://expert-v1#row-1",
        "adjudicator_role": "synthetic-test-adjudicator",
        "synthetic": False,
    }
    row.update(overrides)
    return [row]


def test_submission_binds_to_packet_and_preserves_unjudged_pairs():
    manifest = build_relevance_judgment_manifest(
        _packet(),
        _submission(),
        _source_manifest(),
        authorization_manifest=_authorization_manifest(),
        authorization_sha256="2" * 64,
    )
    report = validate_relevance_judgment_manifest(
        manifest,
        runtime_query_ids=["Q-DEV", "Q-HOLD"],
        runtime_universe=["US1234567B2", "US7654321B2"],
        runtime_sha256="a" * 64,
    )
    assert report["judged_pair_count"] == 1
    assert report["unjudged_pair_count"] == 3
    assert report["generalization_status"] == "NOT_ESTIMABLE"
    assert manifest["judgments"][0]["patent_id_runtime_raw"] == "1234567"
    assert manifest["authorization_binding"]["source_id"] == "expert-fixture"
    assert manifest["authorization_binding"]["manifest_sha256"] == "2" * 64


@pytest.mark.parametrize("mutation", ["unknown_row", "product_disclosure", "missing_role", "wrong_source_hash"])
def test_submission_rejects_unsafe_or_unbound_rows(mutation: str):
    submission = _submission()
    if mutation == "unknown_row":
        submission[0]["review_row_id"] = "Q-DEV::US0000000B2"
    elif mutation == "product_disclosure":
        submission[0]["source_class"] = "product_disclosure"
    elif mutation == "missing_role":
        submission[0].pop("adjudicator_role")
    elif mutation == "wrong_source_hash":
        submission[0]["source_sha256"] = "2" * 64
    with pytest.raises(JudgmentSubmissionError):
        build_relevance_judgment_manifest(
            _packet(),
            submission,
            _source_manifest(),
            authorization_manifest=_authorization_manifest(),
            authorization_sha256="2" * 64,
        )


def test_submission_requires_and_binds_authorization_manifest():
    with pytest.raises(TypeError):
        build_relevance_judgment_manifest(_packet(), _submission(), _source_manifest())

    authorization = _authorization_manifest()
    authorization["source"]["source_sha256"] = "3" * 64
    with pytest.raises(JudgmentSubmissionError, match="does not match"):
        build_relevance_judgment_manifest(
            _packet(),
            _submission(),
            _source_manifest(),
            authorization_manifest=authorization,
            authorization_sha256="2" * 64,
        )
