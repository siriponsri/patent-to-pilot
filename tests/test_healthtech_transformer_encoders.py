import json
from pathlib import Path

import pytest

from patent_to_pilot.evaluation.healthtech.transformer_encoders import (
    TransformerEncoderError,
    build_transformer_model_binding,
    prepare_encoder_inputs,
)


def _write_model_tree(root: Path, *, kind: str) -> None:
    (root / "1_Pooling").mkdir(parents=True)
    (root / "2_Dense").mkdir(parents=True) if kind == "patembed" else None
    (root / "modules.json").write_text(json.dumps([
        {"idx": 0, "path": "", "type": "sentence_transformers.models.Transformer"},
        {"idx": 1, "path": "1_Pooling", "type": "sentence_transformers.models.Pooling"},
        {"idx": 2, "path": "2_Dense" if kind == "patembed" else "2_Normalize",
         "type": "sentence_transformers.models.Dense" if kind == "patembed" else "sentence_transformers.models.Normalize"},
    ]), encoding="utf-8")
    (root / "config.json").write_text(json.dumps({"hidden_size": 1024 if kind == "patembed" else 768}), encoding="utf-8")
    (root / "1_Pooling" / "config.json").write_text(json.dumps({
        "word_embedding_dimension": 1024 if kind == "patembed" else 768,
        "pooling_mode_mean_tokens": True,
        "pooling_mode_cls_token": False,
        "pooling_mode_max_tokens": False,
        "pooling_mode_lasttoken": False,
        "include_prompt": kind == "patembed",
    }), encoding="utf-8")
    (root / "tokenizer.json").write_text("{}", encoding="utf-8")
    (root / "model.safetensors").write_bytes(b"model")
    if kind == "patembed":
        (root / "config_sentence_transformers.json").write_text(json.dumps({"prompts": {"retrieval_MIXED": {
            "q_text": "query prompt: ", "pos_text": "passage prompt: "
        }}}), encoding="utf-8")
        (root / "2_Dense" / "config.json").write_text(json.dumps({
            "in_features": 1024, "out_features": 768, "bias": False
        }), encoding="utf-8")
        (root / "2_Dense" / "model.safetensors").write_bytes(b"projection")


def test_e5_and_patembed_namespaces_are_explicit():
    assert prepare_encoder_inputs(["heart valve"], kind="e5", role="query") == ["query: heart valve"]
    assert prepare_encoder_inputs(["heart valve"], kind="e5", role="passage") == ["passage: heart valve"]
    assert prepare_encoder_inputs(
        ["heart valve"],
        kind="patembed",
        role="query",
        prompt_name="retrieval_MIXED",
        prompt_config={"retrieval_MIXED": {"q_text": "Q: ", "pos_text": "P: "}},
    ) == ["Q: heart valve"]


def test_transformer_binding_hashes_required_files(tmp_path: Path):
    _write_model_tree(tmp_path, kind="patembed")
    binding = build_transformer_model_binding(
        tmp_path,
        model_id="datalyes/patembed-base",
        revision="r1",
        kind="patembed",
    )
    assert binding["encoder_kind"] == "patembed"
    assert binding["model_artifact"]["filename"] == "model.safetensors"
    assert binding["artifact_files"]["2_Dense/model.safetensors"]["bytes"] == len(b"projection")


def test_transformer_binding_rejects_raw_1024d_patembed(tmp_path: Path):
    _write_model_tree(tmp_path, kind="patembed")
    dense = json.loads((tmp_path / "2_Dense" / "config.json").read_text(encoding="utf-8"))
    dense["out_features"] = 1024
    (tmp_path / "2_Dense" / "config.json").write_text(json.dumps(dense), encoding="utf-8")
    with pytest.raises(TransformerEncoderError, match="768"):
        build_transformer_model_binding(tmp_path, model_id="fixture", revision="r1", kind="patembed")


def test_transformer_binding_rejects_missing_e5_normalize_layout(tmp_path: Path):
    _write_model_tree(tmp_path, kind="e5")
    (tmp_path / "modules.json").write_text(json.dumps([
        {"idx": 0, "path": "", "type": "sentence_transformers.models.Transformer"},
        {"idx": 1, "path": "1_Pooling", "type": "sentence_transformers.models.Pooling"},
    ]), encoding="utf-8")
    with pytest.raises(TransformerEncoderError, match="Normalize"):
        build_transformer_model_binding(tmp_path, model_id="fixture", revision="r1", kind="e5")
