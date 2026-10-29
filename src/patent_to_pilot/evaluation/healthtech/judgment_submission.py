"""Convert an authorized review submission into the relevance contract."""
from __future__ import annotations

from typing import Any, Mapping

from patent_to_pilot.evaluation.healthtech.judgments import (
    ALLOWED_BASES,
    JudgmentValidationError,
    validate_relevance_judgment_manifest,
)
from patent_to_pilot.evaluation.healthtech.review_packet import (
    ReviewPacketValidationError,
    validate_relevance_review_packet,
)


class JudgmentSubmissionError(ValueError):
    """Raised when a reviewer submission cannot bind to a frozen packet."""


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JudgmentSubmissionError(f"{field} must be a nonempty string")
    return value.strip()


def _bool(value: Any, field: str) -> bool:
    if not isinstance(value, bool):
        raise JudgmentSubmissionError(f"{field} must be boolean")
    return value


def build_relevance_judgment_manifest(
    packet: Mapping[str, Any],
    submissions: list[Mapping[str, Any]],
    source_manifest: Mapping[str, Any],
    *,
    packet_path: str | None = None,
    packet_sha256: str | None = None,
    holdout_policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Bind explicit review rows to the existing semantic-judgment contract.

    The adapter accepts partial submissions: omitted packet rows remain
    unjudged. It never infers a label from product disclosure or ranking.
    """
    try:
        validate_relevance_review_packet(packet)
    except ReviewPacketValidationError as exc:
        raise JudgmentSubmissionError(str(exc)) from exc
    if not isinstance(source_manifest, dict):
        raise JudgmentSubmissionError("source manifest must be an object")
    source_rows = source_manifest.get("sources")
    if not isinstance(source_rows, list) or not source_rows:
        raise JudgmentSubmissionError("source manifest must contain sources")
    source_by_id: dict[str, Mapping[str, Any]] = {}
    for source in source_rows:
        if not isinstance(source, dict):
            raise JudgmentSubmissionError("source rows must be objects")
        source_id = _text(source.get("source_id"), "source_id")
        if source_id in source_by_id:
            raise JudgmentSubmissionError(f"duplicate source_id: {source_id}")
        source_by_id[source_id] = source

    review_by_id = {
        row["review_row_id"]: row
        for row in packet["review_rows"]
        if isinstance(row, dict)
    }
    patent_by_id = {
        row["patent_id_canonical"]: row
        for row in packet["patents"]
        if isinstance(row, dict)
    }
    judgments: list[dict[str, Any]] = []
    seen_review_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    for index, submission in enumerate(submissions, 1):
        if not isinstance(submission, dict):
            raise JudgmentSubmissionError("submission rows must be objects")
        review_row_id = _text(submission.get("review_row_id"), "review_row_id")
        if review_row_id in seen_review_ids:
            raise JudgmentSubmissionError(f"duplicate review_row_id: {review_row_id}")
        seen_review_ids.add(review_row_id)
        packet_row = review_by_id.get(review_row_id)
        if packet_row is None:
            raise JudgmentSubmissionError(f"submission row is absent from packet: {review_row_id}")
        if packet_row.get("judgment_state") != "UNJUDGED":
            raise JudgmentSubmissionError(f"packet row is not available for labeling: {review_row_id}")
        if packet_row.get("product_disclosure_used") is not False:
            raise JudgmentSubmissionError(f"packet row carries product-disclosure evidence: {review_row_id}")

        query_id = packet_row["query_id"]
        patent_id = packet_row["patent_id_canonical"]
        pair = (query_id, patent_id)
        if pair in seen_pairs:
            raise JudgmentSubmissionError(f"duplicate submission pair: {query_id}::{patent_id}")
        seen_pairs.add(pair)
        patent = patent_by_id[patent_id]
        label = _text(submission.get("label"), f"{review_row_id}.label")
        basis = _text(submission.get("basis"), f"{review_row_id}.basis")
        if basis not in ALLOWED_BASES:
            raise JudgmentSubmissionError(f"unsupported judgment basis: {basis}")
        source_id = _text(submission.get("source_id"), f"{review_row_id}.source_id")
        source = source_by_id.get(source_id)
        if source is None:
            raise JudgmentSubmissionError(f"submission source is not registered: {source_id}")
        synthetic = submission.get("synthetic", False)
        _bool(synthetic, f"{review_row_id}.synthetic")
        if basis == "authored_fixture" and synthetic is not True:
            raise JudgmentSubmissionError("authored_fixture submissions must set synthetic=true")
        if basis != "authored_fixture" and synthetic is True:
            raise JudgmentSubmissionError("non-fixture submissions cannot set synthetic=true")
        judgment = {
            "judgment_id": _text(submission.get("judgment_id", f"J-{index:06d}"), f"{review_row_id}.judgment_id"),
            "query_id": query_id,
            # The runtime preserves the source's numeric publication token,
            # while the judgment contract requires a canonicalizable ID. Keep
            # both values explicit instead of silently discarding provenance.
            "patent_id_raw": patent_id,
            "patent_id_runtime_raw": patent["patent_id_raw"],
            "patent_id_canonical": patent_id,
            "label": label,
            "basis": basis,
            "synthetic": synthetic,
            "source_id": source_id,
            "source_revision": _text(submission.get("source_revision", source.get("source_revision")), f"{review_row_id}.source_revision"),
            "source_sha256": _text(submission.get("source_sha256", source.get("source_sha256")), f"{review_row_id}.source_sha256"),
            "locator": _text(submission.get("locator"), f"{review_row_id}.locator"),
        }
        if "adjudicator_role" in submission:
            judgment["adjudicator_role"] = _text(submission["adjudicator_role"], f"{review_row_id}.adjudicator_role")
        if "source_class" in submission:
            judgment["source_class"] = _text(submission["source_class"], f"{review_row_id}.source_class")
        judgments.append(judgment)

    split_rows = []
    for query in packet["queries"]:
        if not isinstance(query, dict):
            raise JudgmentSubmissionError("packet query rows must be objects")
        split_rows.append({
            "query_id": query["query_id"],
            "split": query["split"],
            "company_group_id": query["company_group_id"],
            "family_group_id": query.get("family_group_id"),
        })
    manifest = {
        "format": "ht-relevance-judgment-cohort-v1",
        "status": "DRAFT_VALIDATED_RELEVANCE_JUDGMENT_COHORT",
        "runtime_sha256": packet["runtime"]["sha256"],
        "runtime_exclusions": [
            "semantic_judgments",
            "split_answers",
            "gold_derived_query_variants",
            "family_labels",
        ],
        "runtime_exclusion_binding": packet["runtime"].get("runtime_exclusion_evidence", {}),
        "packet_binding": {
            "format": packet["format"],
            "path": packet_path,
            "sha256": packet_sha256,
        },
        "sources": [dict(source) for source in source_rows],
        "judgments": judgments,
        "split_rows": split_rows,
        "holdout_policy": dict(holdout_policy or {
            "company_disjoint": True,
            "family_disjoint": False,
            "require_family_mapping_for_final_holdout": False,
        }),
    }
    try:
        validate_relevance_judgment_manifest(
            manifest,
            runtime_query_ids=[row["query_id"] for row in packet["queries"]],
            runtime_universe=[row["patent_id_canonical"] for row in packet["patents"]],
            runtime_sha256=packet["runtime"]["sha256"],
        )
    except JudgmentValidationError as exc:
        raise JudgmentSubmissionError(str(exc)) from exc
    return manifest
