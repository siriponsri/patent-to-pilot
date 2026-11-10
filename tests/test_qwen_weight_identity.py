import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("qwen_identity", Path(__file__).resolve().parents[1] / "scripts/healthtech/inspect_qwen_weight_identity.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture(root):
    shard = "model-00001-of-00001.safetensors"
    (root / shard).write_bytes(b"synthetic weights")
    for name in ("config.json", "tokenizer.json", "tokenizer_config.json", "generation_config.json"):
        (root / name).write_text('{}')
    (root / "model.safetensors.index.json").write_text(json.dumps({"weight_map": {"a": shard, "b": shard}}))


def test_distinct_shards_hashed_once_and_identity_is_not_authentication(tmp_path):
    fixture(tmp_path)
    result = module.observe(tmp_path)
    assert result["shards"] == 1 and result["weight_bytes"] == len(b"synthetic weights")
    assert not result["weights_loaded"]
    assert result["source_authenticity"] == "NOT_ESTABLISHED_BY_LOCAL_HASHING"


def test_traversal_and_missing_shard_refused(tmp_path):
    fixture(tmp_path)
    index = tmp_path / "model.safetensors.index.json"
    index.write_text('{"weight_map":{"a":"../outside.safetensors"}}')
    with pytest.raises(ValueError):
        module.observe(tmp_path)
    index.write_text('{"weight_map":{"a":"model-00002-of-00002.safetensors"}}')
    with pytest.raises(ValueError):
        module.observe(tmp_path)
