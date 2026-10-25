import pytest

from patent_to_pilot.core.models import ConstraintRecord, OrganizationProfile, ProviderRequest, SourceRecord
from patent_to_pilot.core.providers import MockProvider
from patent_to_pilot.core.repository import SQLiteRecordRepository


def test_sqlite_round_trip_and_version_history():
    repo = SQLiteRecordRepository()
    first = SourceRecord(record_id="SRC-1", source_id="SRC-1", source_type="csv", uri="https://example.invalid/source", version_label="v1", license_note="test")
    second = first.model_copy(update={"version": 2, "version_label": "v2"})
    repo.save(first)
    repo.save(second)
    latest = repo.read_latest("SourceRecord", "SRC-1", SourceRecord)
    assert latest is not None and latest.version == 2 and latest.version_label == "v2"
    assert [entry["version"] for entry in repo.history("SourceRecord", "SRC-1")] == [1, 2]
    with pytest.raises(ValueError):
        repo.save(second)
    repo.close()


def test_canonical_external_id_cannot_change_across_versions():
    repo = SQLiteRecordRepository()
    first = SourceRecord(record_id="R1", source_id="SOURCE-A", source_type="csv", uri="https://example.invalid/a", version_label="v1", license_note="test")
    changed = SourceRecord(record_id="R1", source_id="SOURCE-B", source_type="csv", uri="https://example.invalid/b", version=2, version_label="v2", license_note="test")
    repo.save(first)
    with pytest.raises(ValueError, match="canonical source_id"):
        repo.save(changed)
    assert repo.read_latest("SourceRecord", "R1", SourceRecord).source_id == "SOURCE-A"
    repo.close()


def test_record_identity_and_external_identity_are_distinct():
    record = SourceRecord(record_id="R1", source_id="SOURCE-A", source_type="csv", uri="https://example.invalid/a", version_label="v1", license_note="test")
    assert record.record_id == "R1" and record.source_id == "SOURCE-A"


def test_source_assertion_capability_requires_provenance_but_stipulation_does_not():
    with pytest.raises(ValueError, match="source_ref and locator"):
        OrganizationProfile.model_validate({
            "record_id": "ORG-A", "profile_id": "ORG-A", "profile_version": "1.0.0",
            "organization_kind": "fictional", "status": "fixture", "organization_label": "A",
            "capabilities": [{"field": "x", "state": "unknown", "basis": "source_assertion", "confirmation_state": "pending"}],
        })
    profile = OrganizationProfile.model_validate({
        "record_id": "ORG-A", "profile_id": "ORG-A", "profile_version": "1.0.0",
        "organization_kind": "fictional", "status": "fixture", "organization_label": "A",
        "capabilities": [{"field": "x", "state": "external", "basis": "stipulation", "confirmation_state": "not_required"}],
    })
    assert profile.capabilities[0].basis.value == "stipulation"


def test_profile_id_and_constraint_dates_are_typed():
    profile = OrganizationProfile.model_validate({"record_id": "PTP-FIC-ORG-A", "profile_id": "PTP-FIC-ORG-A", "profile_version": "1.0.0", "organization_kind": "fictional_benchmark_profile", "status": "fixture", "organization_label": "A"})
    assert profile.profile_id == "PTP-FIC-ORG-A"
    with pytest.raises(ValueError):
        ConstraintRecord(record_id="C-1", constraint_id="C-1", organization_id="ORG-A", scope="route", state="allowed", statement="x", basis="stipulation", effective_date="not-a-date", confirmation_state="not_required")


def test_provider_is_mockable_without_network():
    provider = MockProvider("bounded")
    result = provider.complete(ProviderRequest(prompt="hello"))
    assert result.mock is True and result.text == "bounded"
    assert len(provider.requests) == 1
