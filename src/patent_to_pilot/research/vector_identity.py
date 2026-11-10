"""Content/order bindings for existing passage vectors; no encoding or labels.

A snapshot is a co-observation, not proof of how vectors were produced. A
trusted prior snapshot/receipt chain and ranking parity remain separate gates.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path

import numpy as np

from patent_to_pilot.evaluation.dapfam_acquisition import dense_passages
from patent_to_pilot.research.mtm_runtime import InputBoundaryError, decode_json, identifier


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _feed(digest, value) -> None:
    # Length-prefixed canonical JSON avoids delimiter/concatenation collisions.
    raw = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    digest.update(len(raw).to_bytes(8, "big"))
    digest.update(raw)


def corpus_identity(path: Path) -> dict:
    content, order, passages = (hashlib.sha256() for _ in range(3))
    families, count, seen = 0, 0, set()
    with path.open("rb") as handle:
        for line in handle:
            content.update(line)
            row = decode_json(line)
            if type(row) is not dict:
                raise InputBoundaryError("invalid corpus record")
            identifier(row.get("id"))
            if row["id"] in seen:
                raise InputBoundaryError("duplicate corpus family")
            seen.add(row["id"])
            for key in ("title", "abstract", "claims"):
                if key not in row or (row[key] is not None and type(row[key]) is not str):
                    raise InputBoundaryError("invalid corpus text fields")
            _feed(order, [families, row["id"]])
            for ordinal, text in enumerate(dense_passages(row["title"], row["abstract"], row["claims"])):
                _feed(passages, [count, families, row["id"], ordinal, text])
                count += 1
            families += 1
    if not families or not count:
        raise InputBoundaryError("empty corpus or passages")
    return {"sha256": content.hexdigest(), "family_order_sha256": order.hexdigest(),
            "passage_owner_text_sha256": passages.hexdigest(), "families": families, "passages": count,
            "passage_builder_source_sha256": sha256(Path(inspect.getfile(dense_passages)))}


def model_identity(root: Path, encoder_source: Path) -> dict:
    required = ("model.safetensors", "config.json", "tokenizer.json", "tokenizer_config.json",
                "sentence_bert_config.json", "modules.json", "1_Pooling/config.json")
    optional = ("special_tokens_map.json", "vocab.txt", "added_tokens.json", "merges.txt", "vocab.json",
                "config_sentence_transformers.json")
    if any(not (root / name).is_file() for name in required):
        raise InputBoundaryError("missing model identity file")
    files = {name: sha256(root / name) for name in required + optional if (root / name).is_file()}
    config = decode_json((root / "config.json").read_bytes())
    settings = decode_json((root / "sentence_bert_config.json").read_bytes())
    dimension, max_length = config.get("hidden_size"), settings.get("max_seq_length")
    if type(dimension) is not int or dimension <= 0 or type(max_length) is not int or max_length <= 0:
        raise InputBoundaryError("invalid encoder dimensions")
    return {"files_sha256": files, "encoder_source_sha256": sha256(encoder_source),
            "hidden_size": dimension, "max_length": max_length,
            "encoding_contract": "fp32-attention-mask-mean-include-prompt-l2-v1"}


def observe_identity(corpus: Path, vectors: Path, model_root: Path, encoder_source: Path) -> dict:
    corpus_bound = corpus_identity(corpus)
    model_bound = model_identity(model_root, encoder_source)
    matrix = np.load(vectors, mmap_mode="r", allow_pickle=False)
    expected = (corpus_bound["passages"], model_bound["hidden_size"])
    if matrix.shape != expected or matrix.dtype != np.dtype("float32"):
        raise InputBoundaryError("vector shape or dtype mismatch")
    for start in range(0, len(matrix), 8192):
        if not np.isfinite(matrix[start:start + 8192]).all():
            raise InputBoundaryError("nonfinite vectors")
    shape = list(matrix.shape)
    del matrix
    return {"format": "ptp-passage-vector-identity-v1", "corpus": corpus_bound, "model": model_bound,
            "vectors": {"sha256": sha256(vectors), "bytes": vectors.stat().st_size,
                        "shape": shape, "dtype": "float32"}}


def verify_identity(expected: dict, observed: dict) -> None:
    """Compare to an independently trusted manifest; never bless a new snapshot."""
    if (set(expected) != {"format", "corpus", "model", "vectors"} or
            expected.get("format") != "ptp-passage-vector-identity-v1" or expected != observed):
        raise InputBoundaryError("vector identity differs from trusted binding")


def verify_historical_receipts(observed: dict, encoding: dict, reuse: dict) -> dict:
    """Check an existing encode/reuse chain, without claiming re-encoding parity."""
    for receipt in (encoding, reuse):
        if (receipt.get("status") != "PASS" or
                receipt.get("inputs_sha256", {}).get("corpus.jsonl") != observed["corpus"]["sha256"] or
                receipt.get("model_safetensors_sha256") != observed["model"]["files_sha256"]["model.safetensors"] or
                receipt.get("families") != observed["corpus"]["families"] or
                receipt.get("passages") != observed["corpus"]["passages"]):
            raise InputBoundaryError("historical receipt binding mismatch")
    if "passage_encode_seconds" not in encoding.get("timings", {}):
        raise InputBoundaryError("encoding receipt missing generation evidence")
    if reuse.get("timings", {}).get("passage_vectors_reused_sha256") != observed["vectors"]["sha256"]:
        raise InputBoundaryError("historical reused vector hash mismatch")
    return {"status": "HISTORICAL_RECEIPTS_MATCHED", "reencoding_parity": "NOT_RUN",
            "original_passage_order_attestation": "NOT_IN_HISTORICAL_RECEIPTS",
            "original_tokenizer_attestation": "NOT_IN_HISTORICAL_RECEIPTS",
            "ranking_parity": "NOT_RUN"}
