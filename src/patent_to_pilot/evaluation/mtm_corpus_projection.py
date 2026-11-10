"""Trusted curator corpus projection; never imported by retrieval runtime.

Unlike mixed query metadata, corpus construction roles are not test qrels.
Nevertheless only the curator should prepare this input, with a pinned receipt.
No real projection has been authorized by the mere existence of this helper.
"""
from __future__ import annotations

import json
from pathlib import Path

from patent_to_pilot.research.mtm_preflight import CORPUS_FIELDS, validate_corpus_row
from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json
from patent_to_pilot.research.vector_identity import corpus_identity


def project_corpus(source: Path, destination: Path, trusted_corpus: dict) -> dict:
    """Exclusive new directory; preserve failures; receipt written last.

    Source must be immutable during staging. Only main view is supported here;
    sensitivity views need separately declared, curator-supplied opaque masks.
    """
    if destination.exists() or destination.resolve() == source.resolve():
        raise InputBoundaryError("projection destination already exists")
    original = corpus_identity(source)
    if original != trusted_corpus:
        raise InputBoundaryError("source corpus differs from trusted identity")
    destination.mkdir(parents=True, exist_ok=False)
    output = destination / "corpus.jsonl"
    with source.open("rb") as incoming, output.open("xb") as outgoing:
        for line in incoming:
            row = decode_json(line)
            if not CORPUS_FIELDS.issubset(row):
                raise InputBoundaryError("source missing runtime corpus fields")
            clean = validate_corpus_row({key: row[key] for key in sorted(CORPUS_FIELDS)})
            outgoing.write((json.dumps(clean, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8"))
    projected = corpus_identity(output)
    if any(projected[key] != original[key] for key in original if key != "sha256"):
        raise InputBoundaryError("projection changed passage identity")
    # Detect ordinary source modification while staging, including mask fields.
    if corpus_identity(source) != original:
        raise InputBoundaryError("source changed during projection")
    receipt = {"format": "ptp-mtm-corpus-projection-v1", "view": "main",
               "original_corpus": original, "projected_corpus": projected}
    with (destination / "projection.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    return receipt
