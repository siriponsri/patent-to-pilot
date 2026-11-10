"""Prospective main-view input gate; no model/GPU initialization or scoring.

Receipts must be pinned by a trusted curator outside this runtime. Hashes do
not establish physical isolation. Inputs must remain immutable after checking.
"""
from __future__ import annotations

from pathlib import Path
import re

from patent_to_pilot.research.mtm_runtime import (
    InputBoundaryError, calendar_date, decode_json, exact_fields, identifier,
    load_dev_metadata,
)
from patent_to_pilot.research.vector_identity import observe_identity, sha256, verify_identity

CORPUS_FIELDS = {"id", "title", "abstract", "claims", "visible_from", "c3"}


def validate_corpus_row(row: dict) -> dict:
    exact_fields(row, CORPUS_FIELDS)
    identifier(row["id"])
    calendar_date(row["visible_from"])
    for key in ("title", "abstract", "claims"):
        if row[key] is not None and type(row[key]) is not str:
            raise InputBoundaryError("invalid corpus text fields")
    codes = row["c3"]
    if (type(codes) is not list or
            any(type(c) is not str or re.fullmatch(r"[A-HY][0-9]{2}", c) is None for c in codes) or
            len(set(codes)) != len(codes)):
        raise InputBoundaryError("invalid corpus CPC3")
    return {**row, "c3": list(codes)}


def preflight_dev(*, metadata_root: Path, corpus: Path, vectors: Path,
                  model_root: Path, encoder_source: Path, projection_receipt: Path,
                  trusted_receipt_sha256: str, trusted_original: dict) -> dict:
    """Verify metadata, projected schema and all identities before model load.

    This gate deliberately has no query-text, ranking or model-loader callback.
    The eventual runner must call it first and keep the checked files immutable.
    """
    metadata = load_dev_metadata(metadata_root)
    if sha256(projection_receipt) != trusted_receipt_sha256:
        raise InputBoundaryError("projection receipt differs from trusted digest")
    receipt = decode_json(projection_receipt.read_bytes())
    exact_fields(receipt, {"format", "view", "original_corpus", "projected_corpus"})
    if receipt["format"] != "ptp-mtm-corpus-projection-v1" or receipt["view"] != "main":
        raise InputBoundaryError("unsupported corpus projection")
    if receipt["original_corpus"] != trusted_original["corpus"]:
        raise InputBoundaryError("projection source differs from trusted corpus")
    for key in trusted_original["corpus"]:
        if key != "sha256" and receipt["projected_corpus"].get(key) != trusted_original["corpus"][key]:
            raise InputBoundaryError("projection changed passage identity")
    with corpus.open("rb") as handle:
        for line in handle:
            validate_corpus_row(decode_json(line))
    observed = observe_identity(corpus, vectors, model_root, encoder_source)
    expected = {**trusted_original, "corpus": receipt["projected_corpus"]}
    verify_identity(expected, observed)
    return {"status": "INPUT_PREFLIGHT_PASS", "view": "main", "queries": len(metadata),
            "identity": observed, "projection_receipt_sha256": trusted_receipt_sha256,
            "metadata_manifest_sha256": sha256(metadata_root / "manifest.json"),
            "physical_isolation": "EXTERNAL_CURATOR_REQUIREMENT", "ranking_parity": "NOT_RUN"}
