"""Explicit provider-transfer bindings for bounded HealthTech requests.

Local research rights do not imply permission to send source material to a
remote provider. This module keeps that decision separate and fail-closed.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ProviderTransferDecision = Literal["ALLOWED", "ALLOWED_WITH_ATTRIBUTION", "BLOCKED_LOCAL", "UNRESOLVED"]


class ProviderVisibleSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    source_type: str = Field(min_length=1)
    synthetic: bool = False


class ProviderTransferBinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    decision: ProviderTransferDecision
    basis_url: str = Field(min_length=1)
    basis_locator: str = Field(min_length=1)
    intended_use: Literal["ht-b4-controller"] = "ht-b4-controller"
    note: str = Field(min_length=1)


class ProviderTransferManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    format: Literal["ht-provider-transfer-manifest-v1"] = "ht-provider-transfer-manifest-v1"
    run_id: str = Field(min_length=1)
    sources: list[ProviderTransferBinding] = Field(default_factory=list)

    @model_validator(mode="after")
    def unique_sources(self):
        ids = [item.source_id for item in self.sources]
        if len(ids) != len(set(ids)):
            raise ValueError("provider-transfer source IDs must be unique")
        return self


class ProviderTransferError(ValueError):
    """Raised when a remote-provider input is not explicitly cleared."""


def validate_provider_transfer(
    visible_sources: Iterable[ProviderVisibleSource],
    manifest: ProviderTransferManifest | None,
) -> list[dict[str, object]]:
    """Bind exact source revision/hash to an explicit remote-use decision."""
    sources = list(visible_sources)
    source_ids = [source.source_id for source in sources]
    if len(source_ids) != len(set(source_ids)):
        raise ProviderTransferError("provider-visible source IDs must be unique")
    bindings = {} if manifest is None else {item.source_id: item for item in manifest.sources}
    summary: list[dict[str, object]] = []
    for source in sources:
        if source.synthetic:
            summary.append({"source_id": source.source_id, "status": "SYNTHETIC"})
            continue
        if manifest is None:
            raise ProviderTransferError(
                f"remote provider blocked: no transfer manifest for {source.source_id}"
            )
        binding = bindings.get(source.source_id)
        if binding is None:
            raise ProviderTransferError(
                f"remote provider blocked: source {source.source_id} is not listed"
            )
        if binding.source_revision != source.source_revision:
            raise ProviderTransferError(
                f"remote provider blocked: revision mismatch for {source.source_id}"
            )
        if binding.source_sha256 != source.source_sha256:
            raise ProviderTransferError(
                f"remote provider blocked: source hash mismatch for {source.source_id}"
            )
        if binding.decision not in {"ALLOWED", "ALLOWED_WITH_ATTRIBUTION"}:
            raise ProviderTransferError(
                f"remote provider blocked: {source.source_id} is {binding.decision}"
            )
        summary.append({
            "source_id": source.source_id,
            "source_revision": source.source_revision,
            "source_sha256": source.source_sha256,
            "decision": binding.decision,
            "basis_url": binding.basis_url,
            "basis_locator": binding.basis_locator,
            "status": "ALLOWED",
        })
    return summary
