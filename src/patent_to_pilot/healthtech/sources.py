"""Local snapshot normalization; this module never downloads or loads credentials."""
from __future__ import annotations

from datetime import date
from typing import Any

from patent_to_pilot.core.models import SourceRecord
from patent_to_pilot.healthtech.contracts import EvidenceItem, SourcePayload, SourceRights, content_hash


def source_payload(source_id: str, payload: str | dict[str, Any], *, uri: str,
                   revision: str, source_date: date, jurisdiction: str,
                   source_type: str, license_note: str, synthetic: bool,
                   rights: SourceRights | None = None) -> SourcePayload:
    return SourcePayload(source=SourceRecord(record_id=source_id, source_id=source_id,
        source_type=source_type, uri=uri, version_label=revision, license_note=license_note,
        sha256=content_hash(payload)), payload=payload, source_date=source_date,
        jurisdiction=jurisdiction, synthetic=synthetic, rights=rights)


def normalize_510k_record(record: dict[str, Any], *, source_id: str, snapshot_revision: str,
                          retrieved_date: date, synthetic: bool = False,
                          rights: SourceRights | None = None) -> SourcePayload:
    """Normalize one supplied openFDA 510(k) object without inventing approval.

    Only the declared device/decision fields are retained. Third-party GMDN/D&B
    enrichments and unknown fields are excluded, not inherited under a blanket
    public-data license. 510(k) decision codes remain codes;
    they are not PMA approvals, clinical endorsements, or device-patent links.
    The caller pins the snapshot and intended-use rights separately.
    """
    import re
    identifier = record.get("k_number")
    if not isinstance(identifier, str) or not re.fullmatch(r"K\d{6}", identifier):
        raise ValueError("510(k) record requires a canonical K plus six digits")
    if not isinstance(record.get("device_name"), str) or not record["device_name"].strip():
        raise ValueError("510(k) record needs device_name")
    if not snapshot_revision.strip():
        raise ValueError("snapshot revision must be pinned")
    allowed = {"k_number", "device_name", "applicant", "product_code", "decision_code",
               "decision_date", "date_received", "statement_or_summary", "clearance_type",
               "review_advisory_committee"}
    normalized = {key:value for key,value in record.items() if key in allowed}
    uri = (f"urn:synthetic:openfda-510k:{identifier}" if synthetic else
           f"https://api.fda.gov/device/510k.json?search=k_number:{identifier}")
    return source_payload(source_id, normalized, uri=uri,
        revision=snapshot_revision, source_date=retrieved_date, jurisdiction="US",
        source_type="regulatory_record", license_note="openFDA/FDA terms and field-specific rights apply; preserve attribution",
        synthetic=synthetic, rights=rights)


def field_evidence(source: SourcePayload, field: str, evidence_id: str) -> EvidenceItem:
    if not isinstance(source.payload, dict) or field not in source.payload:
        raise ValueError("field not available in this source record")
    return EvidenceItem(evidence_id=evidence_id, source_id=source.source.source_id,
        source_version=source.source.version_label, payload_hash=source.source.sha256,
        locator=f"field:{field}", structured_field=field, structured_value=source.payload[field],
        evidence_kind="regulatory_record", statement=f"{field}: {source.payload[field]}",
        support_basis="Supplied source field; no interpretation of regulatory status",
        jurisdiction=source.jurisdiction, source_date=source.source_date, extraction_method="structured_field")
