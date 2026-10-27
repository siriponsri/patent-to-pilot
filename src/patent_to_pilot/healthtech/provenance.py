"""Deterministic source integrity. Never a semantic or medical truth evaluator."""
from __future__ import annotations

import re

from patent_to_pilot.healthtech.contracts import EvidenceItem, SourcePayload, content_hash


def check_evidence(item: EvidenceItem, source: SourcePayload) -> EvidenceItem:
    record = source.source
    if (item.source_id != record.source_id or item.source_version != record.version_label
            or item.payload_hash != content_hash(source.payload)
            or item.payload_hash != record.sha256 or item.jurisdiction != source.jurisdiction
            or item.source_date != source.source_date):
        raise ValueError("evidence source identity/version/hash/date/jurisdiction mismatch")
    if item.evidence_kind in {"system_inference", "unresolved"}:
        return item
    if item.extraction_method == "literal_span":
        match = re.fullmatch(r"chars:(\d+):(\d+)", item.locator)
        if not match or not isinstance(source.payload, str):
            raise ValueError("literal evidence needs text and chars:start:end locator")
        start, end = map(int, match.groups())
        if not 0 <= start < end <= len(source.payload) or source.payload[start:end] != item.quoted_span:
            raise ValueError("exact quoted span mismatch")
        status = "exact_span_checked"
    else:
        if item.locator != f"field:{item.structured_field}" or not isinstance(source.payload, dict):
            raise ValueError("structured evidence needs a field locator and object payload")
        value = source.payload
        try:
            for part in item.structured_field.split("."):
                value = value[part]
        except (KeyError, TypeError):
            raise ValueError("structured field not present") from None
        if content_hash(value) != content_hash(item.structured_value):
            raise ValueError("structured field value/type mismatch")
        status = "field_value_checked"
    return EvidenceItem.model_validate({**item.model_dump(), "verification_status": status})
