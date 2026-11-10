import copy
import json

import numpy as np
import pytest

from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.vector_identity import observe_identity, verify_historical_receipts, verify_identity


def fixtures(tmp_path):
    corpus = tmp_path / "corpus.jsonl"
    corpus.write_text(''.join(json.dumps({"id": name, "title": text, "abstract": "", "claims": ""}) + '\n'
                              for name, text in (("f1", "first passage"), ("f2", "second passage"))), encoding="utf-8")
    vectors = tmp_path / "vectors.npy"
    np.save(vectors, np.array([[1., 0.], [0., 1.]], dtype=np.float32))
    model = tmp_path / "model"
    (model / "1_Pooling").mkdir(parents=True)
    for name, data in {"config.json": {"hidden_size": 2}, "sentence_bert_config.json": {"max_seq_length": 512},
                       "tokenizer.json": {}, "tokenizer_config.json": {}, "modules.json": [],
                       "1_Pooling/config.json": {}}.items():
        (model / name).write_text(json.dumps(data))
    (model / "model.safetensors").write_bytes(b"synthetic weights; never loaded")
    encoder = tmp_path / "encoder.py"
    encoder.write_text("# synthetic encoder identity\n")
    return corpus, vectors, model, encoder


def test_identical_snapshot_passes_and_contains_no_text(tmp_path):
    paths = fixtures(tmp_path)
    observed = observe_identity(*paths)
    verify_identity(observed, observe_identity(*paths))
    assert observed["corpus"]["families"] == observed["corpus"]["passages"] == 2
    assert "first passage" not in json.dumps(observed)


@pytest.mark.parametrize("change", ["corpus_order", "vector_order", "text", "tokenizer", "weights", "encoder"])
def test_same_shape_changes_fail_binding(tmp_path, change):
    corpus, vectors, model, encoder = fixtures(tmp_path)
    expected = observe_identity(corpus, vectors, model, encoder)
    if change == "corpus_order":
        corpus.write_text('\n'.join(reversed(corpus.read_text().splitlines())) + '\n')
    elif change == "vector_order":
        np.save(vectors, np.load(vectors)[::-1])
    elif change == "text":
        corpus.write_text(corpus.read_text().replace("first passage", "other passage"))
    elif change == "tokenizer":
        (model / "tokenizer.json").write_text('{"changed":true}')
    elif change == "weights":
        (model / "model.safetensors").write_bytes(b"different synthetic weights")
    else:
        encoder.write_text("# changed synthetic implementation\n")
    actual = observe_identity(corpus, vectors, model, encoder)
    assert actual["vectors"]["shape"] == expected["vectors"]["shape"]
    with pytest.raises(InputBoundaryError, match="trusted binding"):
        verify_identity(expected, actual)


@pytest.mark.parametrize("bad", [np.zeros((3, 2), dtype=np.float32), np.zeros((2, 2), dtype=np.float64),
                                 np.array([[np.nan, 0], [0, 1]], dtype=np.float32)])
def test_bad_matrix_fails(tmp_path, bad):
    paths = fixtures(tmp_path)
    np.save(paths[1], bad)
    with pytest.raises(InputBoundaryError):
        observe_identity(*paths)


def test_historical_chain_binds_hashes_but_does_not_claim_parity(tmp_path):
    observed = observe_identity(*fixtures(tmp_path))
    base = {"status": "PASS", "inputs_sha256": {"corpus.jsonl": observed["corpus"]["sha256"]},
            "families": 2, "passages": 2,
            "model_safetensors_sha256": observed["model"]["files_sha256"]["model.safetensors"]}
    encoding = {**base, "timings": {"passage_encode_seconds": 1}}
    reuse = {**base, "timings": {"passage_vectors_reused_sha256": observed["vectors"]["sha256"]}}
    result = verify_historical_receipts(observed, encoding, reuse)
    assert result["ranking_parity"] == "NOT_RUN"
    assert result["original_tokenizer_attestation"] == "NOT_IN_HISTORICAL_RECEIPTS"
    changed = copy.deepcopy(reuse)
    changed["inputs_sha256"]["corpus.jsonl"] = "0" * 64
    with pytest.raises(InputBoundaryError):
        verify_historical_receipts(observed, encoding, changed)
    changed = copy.deepcopy(reuse)
    changed["timings"]["passage_vectors_reused_sha256"] = "0" * 64
    with pytest.raises(InputBoundaryError):
        verify_historical_receipts(observed, encoding, changed)


def test_duplicate_families_fail(tmp_path):
    paths = fixtures(tmp_path)
    paths[0].write_text(paths[0].read_text().replace('"f2"', '"f1"'))
    with pytest.raises(InputBoundaryError, match="duplicate"):
        observe_identity(*paths)
