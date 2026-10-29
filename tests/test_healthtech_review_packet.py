from __future__ import annotations

import copy

import pytest

from patent_to_pilot.evaluation.healthtech.review_packet import (
    ReviewPacketValidationError,
    build_relevance_review_packet,
    validate_relevance_review_packet,
)


def _inputs() -> tuple[dict, dict, dict, dict]:
    runtime = {
        "format": "ht-runtime-v1",
        "status": "RUNTIME_INPUTS_ONLY_NO_EVALUATOR_LABELS",
        "runtime_exclusions": ["semantic_judgments", "split_answers", "gold_derived_query_variants", "family_labels"],
        "devices": [
            {"query_id": "Q-DEV", "device_id_raw": "Device D", "device_id_canonical": "D", "company": "Alpha", "trade_name": "Device D", "pma_number": "P1", "source_id": "device-source", "evidence_cutoff": "2026-10-29"},
            {"query_id": "Q-HOLD", "device_id_raw": "Device H", "device_id_canonical": "H", "company": "Beta", "trade_name": "Device H", "pma_number": "P2", "source_id": "device-source", "evidence_cutoff": "2026-10-29"},
        ],
        "patents": [
            {"patent_id_raw": "1234567", "patent_id_canonical": "US1234567B2", "document_kind": "US-grant", "jurisdiction": "US", "title": "One", "abstract": "a", "claims": "a", "text": "a", "source_id": "patent-source", "source_revision": "r1", "source_url": "https://example.test/one", "raw_html_sha256": "a" * 64, "normalized_sha256": "b" * 64, "source_date": "2026-10-29"},
            {"patent_id_raw": "7654321", "patent_id_canonical": "US7654321B2", "document_kind": "US-grant", "jurisdiction": "US", "title": "Two", "abstract": "b", "claims": "b", "text": "b", "source_id": "patent-source", "source_revision": "r1", "source_url": "https://example.test/two", "raw_html_sha256": "c" * 64, "normalized_sha256": "d" * 64, "source_date": "2026-10-29"},
        ],
    }
    split_manifest = {
        "format": "ht-development-final-holdout-split-v1",
        "family_group_count": 2,
        "family_split_overlap_count": 0,
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
        {"source_id": "device-source", "source_type": "official_fact", "revision": "r1", "rights_policy_id": "fixture-device", "rights": "fixture", "runtime_allowed": True, "url": "fixture://device"},
        {"source_id": "patent-source", "source_type": "patent_document", "revision": "r1", "rights_policy_id": "fixture-patent", "rights": "fixture", "runtime_allowed": True, "url": "fixture://patents"},
    ]}
    return runtime, split_manifest, groups, source_registry


def _build() -> dict:
    runtime, split_manifest, groups, source_registry = _inputs()
    return build_relevance_review_packet(
        runtime,
        split_manifest,
        groups,
        source_registry,
        runtime_path="runtime.json",
        runtime_sha256="a" * 64,
        split_manifest_path="split.json",
        split_manifest_sha256="b" * 64,
        groups_path="groups.json",
        groups_sha256="c" * 64,
        source_registry_path="sources.json",
        source_registry_sha256="d" * 64,
    )


def test_packet_freezes_full_cartesian_denominator_without_labels():
    packet = _build()
    report = validate_relevance_review_packet(packet)
    assert report["status"] == "PASS"
    assert packet["counts"] == {
        "query_count": 2,
        "patent_count": 2,
        "pair_denominator": 4,
        "unjudged_pair_count": 4,
        "semantic_label_count": 0,
    }
    assert all(row["judgment_state"] == "UNJUDGED" for row in packet["review_rows"])
    assert packet["semantic_gold_created"] is False


@pytest.mark.parametrize("mutation", ["label", "disclosure", "duplicate", "company_overlap", "missing_exclusion"])
def test_packet_rejects_label_shortcuts_and_split_leakage(mutation: str):
    packet = _build()
    if mutation == "label":
        packet["review_rows"][0]["label"] = "relevant"
    elif mutation == "disclosure":
        packet["review_rows"][0]["product_disclosure_used"] = True
    elif mutation == "duplicate":
        packet["review_rows"].append(copy.deepcopy(packet["review_rows"][0]))
    elif mutation == "company_overlap":
        packet["queries"][1]["company_group_id"] = packet["queries"][0]["company_group_id"]
    elif mutation == "missing_exclusion":
        packet["runtime"]["runtime_exclusions"].remove("family_labels")
    with pytest.raises(ReviewPacketValidationError):
        validate_relevance_review_packet(packet)


def test_builder_rejects_company_overlap_before_writing_packet():
    runtime, split_manifest, groups, source_registry = _inputs()
    groups["company_groups"][1]["company"] = "Alpha"
    with pytest.raises(ReviewPacketValidationError, match="company groups cross splits"):
        build_relevance_review_packet(
            runtime,
            split_manifest,
            groups,
            source_registry,
            runtime_path="runtime.json",
            runtime_sha256="a" * 64,
            split_manifest_path="split.json",
            split_manifest_sha256="b" * 64,
            groups_path="groups.json",
            groups_sha256="c" * 64,
            source_registry_path="sources.json",
            source_registry_sha256="d" * 64,
        )
