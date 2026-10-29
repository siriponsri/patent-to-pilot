from __future__ import annotations

import pytest

from patent_to_pilot.evaluation.healthtech.review_packet import (
    ReviewPacketValidationError,
    build_relevance_review_packet,
)
from patent_to_pilot.evaluation.healthtech.review_tasks import (
    ReviewTaskPackError,
    build_review_task_pack,
    validate_review_task_pack,
)


def _packet() -> dict:
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


def test_task_pack_is_deterministic_unlabeled_and_hides_evaluator_metadata():
    packet = _packet()
    task_pack = build_review_task_pack(packet, packet_path="packet.json", packet_sha256="e" * 64)
    report = validate_review_task_pack(task_pack)
    assert report == {"status": "PASS", "task_count": 4, "response_count": 0, "semantic_label_count": 0}
    assert [task["task_id"] for task in task_pack["tasks"]] == [
        "HT-REVIEW-000001",
        "HT-REVIEW-000002",
        "HT-REVIEW-000003",
        "HT-REVIEW-000004",
    ]
    assert all(task["review_state"] == "UNJUDGED" for task in task_pack["tasks"])
    assert all(all(value is None for value in task["response"].values()) for task in task_pack["tasks"])
    assert all("split" not in task and "family_id" not in task and "frozen_group_id" not in task for task in task_pack["tasks"])
    assert all("abstract" not in task["patent"] and "claims" not in task["patent"] and "text" not in task["patent"] for task in task_pack["tasks"])


@pytest.mark.parametrize("mutation", ["label", "response", "distribution"])
def test_task_pack_rejects_gold_or_prefilled_response_shortcuts(mutation: str):
    packet = _packet()
    if mutation == "label":
        packet["review_rows"][0]["label"] = "relevant"
    if mutation == "label":
        with pytest.raises(ReviewPacketValidationError):
            build_review_task_pack(packet, packet_path="packet.json", packet_sha256="e" * 64)
        return
    task_pack = build_review_task_pack(packet, packet_path="packet.json", packet_sha256="e" * 64)
    if mutation == "response":
        task_pack["tasks"][0]["response"]["label"] = "relevant"
    else:
        task_pack["distribution"] = "PUBLIC"
    with pytest.raises(ReviewTaskPackError):
        validate_review_task_pack(task_pack)
