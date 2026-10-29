"""Build reviewer-visible task rows from an unlabeled review packet.

The task export is local-review metadata only. It deliberately excludes patent
text, evaluator split/family metadata, product-disclosure labels, and any
semantic response so that task preparation cannot create gold by accident.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from patent_to_pilot.evaluation.healthtech.review_packet import (
    validate_relevance_review_packet,
)


FORMAT = "ht-relevance-review-task-pack-v1"
STATUS = "READY_FOR_AUTHORIZED_LOCAL_REVIEW_NOT_GOLD"
REVIEW_STATE = "UNJUDGED"
RESPONSE_FIELDS = (
    "label",
    "basis",
    "source_id",
    "source_revision",
    "source_sha256",
    "locator",
    "adjudicator_role",
    "notes",
)
FORBIDDEN_TASK_KEYS = {
    "abstract",
    "claims",
    "content",
    "family_id",
    "frozen_group_id",
    "gold",
    "known_link",
    "label",
    "product_disclosure_used",
    "split",
    "text",
}


class ReviewTaskPackError(ValueError):
    """Raised when a reviewer task pack cannot remain unlabeled and local-only."""


def _require_mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ReviewTaskPackError(f"{field} must be an object")
    return value


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewTaskPackError(f"{field} must be a nonempty string")
    return value.strip()


def _assert_no_forbidden_keys(value: Any, *, path: str = "task") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if key in FORBIDDEN_TASK_KEYS and not path.endswith(".response"):
                raise ReviewTaskPackError(f"reviewer task exposes forbidden field: {path}.{key}")
            _assert_no_forbidden_keys(child, path=f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _assert_no_forbidden_keys(child, path=f"{path}[{index}]")


def _source_metadata(packet: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    registry = _require_mapping(packet.get("source_registry"), "packet.source_registry")
    bindings = registry.get("bindings")
    if not isinstance(bindings, list):
        raise ReviewTaskPackError("packet.source_registry.bindings must be a list")
    result: dict[str, Mapping[str, Any]] = {}
    for row in bindings:
        row = _require_mapping(row, "source binding")
        source_id = _require_text(row.get("source_id"), "source binding source_id")
        if source_id in result:
            raise ReviewTaskPackError(f"duplicate source binding: {source_id}")
        result[source_id] = row
    return result


def build_review_task_pack(
    packet: Mapping[str, Any],
    *,
    packet_path: str,
    packet_sha256: str,
) -> dict[str, Any]:
    """Build deterministic reviewer-visible rows without creating labels."""
    validate_relevance_review_packet(packet)
    if packet.get("semantic_gold_created") is not False:
        raise ReviewTaskPackError("review packet must not claim semantic gold")
    counts = _require_mapping(packet.get("counts"), "packet.counts")
    if counts.get("semantic_label_count") != 0 or counts.get("unjudged_pair_count") != counts.get("pair_denominator"):
        raise ReviewTaskPackError("task export requires an entirely unjudged packet")

    queries = {
        _require_text(row.get("query_id"), "query_id"): _require_mapping(row, "query row")
        for row in packet.get("queries", [])
    }
    patents = {
        _require_text(row.get("patent_id_canonical"), "patent_id_canonical"): _require_mapping(row, "patent row")
        for row in packet.get("patents", [])
    }
    sources = _source_metadata(packet)
    tasks: list[dict[str, Any]] = []
    review_rows = sorted(
        packet.get("review_rows", []),
        key=lambda row: (_require_text(row.get("query_id"), "review query_id"), _require_text(row.get("patent_id_canonical"), "review patent ID")),
    )
    for index, raw_row in enumerate(review_rows, start=1):
        row = _require_mapping(raw_row, "review row")
        query_id = _require_text(row.get("query_id"), "review query_id")
        patent_id = _require_text(row.get("patent_id_canonical"), "review patent ID")
        query = queries.get(query_id)
        patent = patents.get(patent_id)
        if query is None or patent is None:
            raise ReviewTaskPackError(f"review row references unknown pair: {query_id}::{patent_id}")
        if row.get("judgment_state") != REVIEW_STATE:
            raise ReviewTaskPackError(f"review row is not unjudged: {query_id}::{patent_id}")
        source_id = _require_text(patent.get("source_id"), f"{patent_id}.source_id")
        source = sources.get(source_id)
        if source is None:
            raise ReviewTaskPackError(f"patent source is absent from packet registry: {source_id}")

        task = {
            "task_id": f"HT-REVIEW-{index:06d}",
            "review_row_id": _require_text(row.get("review_row_id"), "review_row_id"),
            "review_state": REVIEW_STATE,
            "instructions": [
                "Use only the separately authorized source material and the fields shown here.",
                "Do not infer a semantic label from a product-marking disclosure or from absence in this packet.",
                "Leave the response empty until an authorized judgment source and adjudicator role are available.",
            ],
            "query": {
                "query_id": query_id,
                "device_id_raw": _require_text(query.get("device_id_raw"), f"{query_id}.device_id_raw"),
                "trade_name": query.get("trade_name", ""),
                "company": query.get("company", ""),
                "evidence_cutoff": _require_text(query.get("evidence_cutoff"), f"{query_id}.evidence_cutoff"),
            },
            "patent": {
                "patent_id_raw": _require_text(patent.get("patent_id_raw"), f"{patent_id}.patent_id_raw"),
                "patent_id_canonical": patent_id,
                "document_kind": _require_text(patent.get("document_kind"), f"{patent_id}.document_kind"),
                "jurisdiction": _require_text(patent.get("jurisdiction"), f"{patent_id}.jurisdiction"),
                "title": _require_text(patent.get("title"), f"{patent_id}.title"),
                "source_id": source_id,
                "source_revision": _require_text(patent.get("source_revision"), f"{patent_id}.source_revision"),
                "source_date": _require_text(patent.get("source_date"), f"{patent_id}.source_date"),
                "source_url": _require_text(patent.get("source_url"), f"{patent_id}.source_url"),
                "raw_html_sha256": _require_text(patent.get("raw_html_sha256"), f"{patent_id}.raw_html_sha256"),
                "normalized_sha256": _require_text(patent.get("normalized_sha256"), f"{patent_id}.normalized_sha256"),
            },
            "response": {field: None for field in RESPONSE_FIELDS},
        }
        _assert_no_forbidden_keys(task)
        tasks.append(task)

    if len(tasks) != counts.get("pair_denominator"):
        raise ReviewTaskPackError("task count does not match packet denominator")
    task_ids = [task["task_id"] for task in tasks]
    if len(task_ids) != len(set(task_ids)):
        raise ReviewTaskPackError("task IDs must be unique")

    pack = {
        "format": FORMAT,
        "status": STATUS,
        "semantic_gold_created": False,
        "distribution": "LOCAL_REVIEW_ONLY",
        "packet": {
            "path": packet_path,
            "sha256": packet_sha256,
            "query_count": counts.get("query_count"),
            "patent_count": counts.get("patent_count"),
            "pair_denominator": counts.get("pair_denominator"),
        },
        "policy": {
            "unlisted_pair_policy": "UNJUDGED_NOT_NEGATIVE",
            "product_disclosure_used": False,
            "evaluator_split_metadata_exposed": False,
            "evaluator_family_metadata_exposed": False,
            "patent_text_copied": False,
            "response_fields_empty": True,
        },
        "response_schema": {
            "label": "relevant | not_relevant | null until authorized judgment",
            "basis": "expert_adjudication | benchmark_gold | authored_fixture | null",
            "source_id": "source registry ID supporting the explicit label | null",
            "source_revision": "exact supporting source revision | null",
            "source_sha256": "exact supporting source hash | null",
            "locator": "exact supporting locator | null",
            "adjudicator_role": "required for expert_adjudication | null",
            "notes": "optional reviewer note | null",
        },
        "counts": {
            "task_count": len(tasks),
            "response_count": 0,
            "semantic_label_count": 0,
        },
        "tasks": tasks,
    }
    _assert_no_forbidden_keys(pack["tasks"], path="tasks")
    return pack


def validate_review_task_pack(pack: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the safe, unlabeled shape of a generated task pack."""
    if pack.get("format") != FORMAT:
        raise ReviewTaskPackError(f"pack format must be {FORMAT}")
    if pack.get("status") != STATUS:
        raise ReviewTaskPackError(f"pack status must be {STATUS}")
    if pack.get("semantic_gold_created") is not False:
        raise ReviewTaskPackError("task pack cannot claim semantic gold")
    if pack.get("distribution") != "LOCAL_REVIEW_ONLY":
        raise ReviewTaskPackError("task pack distribution must remain LOCAL_REVIEW_ONLY")
    tasks = pack.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        raise ReviewTaskPackError("task pack must contain tasks")
    seen_rows: set[str] = set()
    for task in tasks:
        task = _require_mapping(task, "task")
        task_id = _require_text(task.get("task_id"), "task_id")
        row_id = _require_text(task.get("review_row_id"), f"{task_id}.review_row_id")
        if row_id in seen_rows:
            raise ReviewTaskPackError(f"duplicate review row: {row_id}")
        seen_rows.add(row_id)
        if task.get("review_state") != REVIEW_STATE:
            raise ReviewTaskPackError(f"task is not unjudged: {task_id}")
        response = task.get("response")
        if not isinstance(response, Mapping) or set(response) != set(RESPONSE_FIELDS):
            raise ReviewTaskPackError(f"response schema mismatch: {task_id}")
        if any(value is not None for value in response.values()):
            raise ReviewTaskPackError(f"task response is prefilled: {task_id}")
        _assert_no_forbidden_keys(task, path=task_id)
    counts = _require_mapping(pack.get("counts"), "pack.counts")
    if counts.get("task_count") != len(tasks) or counts.get("response_count") != 0 or counts.get("semantic_label_count") != 0:
        raise ReviewTaskPackError("task pack counts are inconsistent")
    return {
        "status": "PASS",
        "task_count": len(tasks),
        "response_count": 0,
        "semantic_label_count": 0,
    }
