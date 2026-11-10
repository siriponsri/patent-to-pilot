import hashlib
import json

import numpy as np
import pytest

from patent_to_pilot.evaluation.mtm_corpus_projection import project_corpus
from patent_to_pilot.research.mtm_preflight import preflight_dev
from patent_to_pilot.research.mtm_runtime import InputBoundaryError
from patent_to_pilot.research.vector_identity import observe_identity, sha256


def setup_inputs(tmp_path):
    corpus = tmp_path / "original.jsonl"
    rows = [{"id": f"f{i}", "title": text, "abstract": "", "claims": "",
             "visible_from": 20000101, "c3": ["A61"], "sets": [role]}
            for i, text, role in ((1, "first", "target"), (2, "second", "uniform"))]
    corpus.write_text(''.join(json.dumps(row) + '\n' for row in rows), encoding="utf-8")
    model = tmp_path / "model"
    (model / "1_Pooling").mkdir(parents=True)
    for name, data in {"config.json": {"hidden_size": 2}, "sentence_bert_config.json": {"max_seq_length": 512},
                       "tokenizer.json": {}, "tokenizer_config.json": {}, "modules.json": [],
                       "1_Pooling/config.json": {}}.items():
        (model / name).write_text(json.dumps(data))
    (model / "model.safetensors").write_bytes(b"synthetic only")
    encoder = tmp_path / "encoder.py"
    encoder.write_text("raise RuntimeError('must never execute encoder')\n")
    vectors = tmp_path / "vectors.npy"
    np.save(vectors, np.eye(2, dtype=np.float32))
    trusted = observe_identity(corpus, vectors, model, encoder)
    bundle = tmp_path / "runtime"
    bundle.mkdir()
    raw = (json.dumps({"id": "q1", "family_id": "qf1", "priority": 20100101, "c3": ["G06"]}) + '\n').encode()
    (bundle / "metadata.jsonl").write_bytes(raw)
    (bundle / "manifest.json").write_text(json.dumps({"format": "ptp-mtm-runtime-v1", "split": "dev",
                                                     "queries": 1, "sha256": hashlib.sha256(raw).hexdigest()}))
    projected = tmp_path / "projected"
    project_corpus(corpus, projected, trusted["corpus"])
    return {"metadata_root": bundle, "corpus": projected / "corpus.jsonl", "vectors": vectors,
            "model_root": model, "encoder_source": encoder, "projection_receipt": projected / "projection.json",
            "trusted_receipt_sha256": sha256(projected / "projection.json"), "trusted_original": trusted}


def test_projection_preserves_text_order_and_preflight_never_loads_encoder(tmp_path):
    args = setup_inputs(tmp_path)
    result = preflight_dev(**args)
    assert result["status"] == "INPUT_PREFLIGHT_PASS"
    assert result["ranking_parity"] == "NOT_RUN"
    clean = args["corpus"].read_text()
    assert '"sets"' not in clean and '"target"' not in clean
    original = args["trusted_original"]["corpus"]
    projected = result["identity"]["corpus"]
    assert original["sha256"] != projected["sha256"]
    assert {k: v for k, v in original.items() if k != "sha256"} == {
        k: v for k, v in projected.items() if k != "sha256"}


@pytest.mark.parametrize("mutation", ["roles", "labels", "date", "cpc", "text", "order", "vectors", "model", "receipt"])
def test_preflight_rejects_tampering(tmp_path, mutation):
    args = setup_inputs(tmp_path)
    rows = [json.loads(line) for line in args["corpus"].read_text().splitlines()]
    if mutation in {"roles", "labels", "date", "cpc", "text", "order"}:
        if mutation == "roles":
            rows[0]["sets"] = ["target"]
        elif mutation == "labels":
            rows[0]["targets"] = ["hidden"]
        elif mutation == "date":
            rows[0]["visible_from"] = 19990101  # valid date, but not curator-bound
        elif mutation == "cpc":
            rows[0]["c3"] = ["G06"]  # valid code, but changes eligibility
        elif mutation == "text":
            rows[0]["title"] = "changed"
        else:
            rows.reverse()
        args["corpus"].write_text(''.join(json.dumps(row) + '\n' for row in rows))
    elif mutation == "vectors":
        np.save(args["vectors"], np.eye(2, dtype=np.float32)[::-1])
    elif mutation == "model":
        (args["model_root"] / "tokenizer.json").write_text('{"changed":true}')
    else:
        receipt = json.loads(args["projection_receipt"].read_text())
        receipt["view"] = "small"
        args["projection_receipt"].write_text(json.dumps(receipt))
    with pytest.raises(InputBoundaryError):
        preflight_dev(**args)


def test_protected_manifest_rejected_before_corpus_or_model_access(tmp_path):
    args = setup_inputs(tmp_path)
    manifest = args["metadata_root"] / "manifest.json"
    value = json.loads(manifest.read_text())
    value["split"] = "test"
    manifest.write_text(json.dumps(value))
    args["corpus"] = tmp_path / "does-not-exist"
    args["projection_receipt"] = tmp_path / "also-missing"
    with pytest.raises(InputBoundaryError, match="development bundle"):
        preflight_dev(**args)


def test_projection_refuses_existing_output_and_wrong_source(tmp_path):
    args = setup_inputs(tmp_path)
    with pytest.raises(InputBoundaryError, match="already exists"):
        project_corpus(tmp_path / "original.jsonl", args["corpus"].parent, args["trusted_original"]["corpus"])
    wrong = {**args["trusted_original"]["corpus"], "sha256": "0" * 64}
    destination = tmp_path / "new"
    with pytest.raises(InputBoundaryError, match="trusted identity"):
        project_corpus(tmp_path / "original.jsonl", destination, wrong)
    assert not destination.exists()
