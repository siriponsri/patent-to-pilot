from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from patent_to_pilot.healthtech.http import HTTPJobError, HealthTechJobService
from patent_to_pilot.healthtech.vector_http import ConfiguredVectorSearch
from patent_to_pilot.evaluation.healthtech.vector_artifacts import (
    VectorArtifactError,
    encode_vector_shards,
    export_runtime_text,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT = json.loads((ROOT / "examples/healthtech/synthetic-device/input.json").read_text(encoding="utf-8"))


class FakeEncoder:
    def __init__(self, values: dict[str, list[float]]):
        self.values = values

    def encode(self, texts: list[str]):
        return np.asarray([self.values[text] for text in texts], dtype="<f4"), 0


def _make_vector_config(tmp_path: Path, *, query_model: dict | None = None) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    corpus_runtime = tmp_path / "corpus.jsonl"
    query_runtime = tmp_path / "queries.jsonl"
    corpus_rows = []
    corpus_values = {}
    for index, patent in enumerate(INPUT["patents"]):
        text = f"{patent['title']} {patent['source']['payload']}"
        corpus_rows.append({
            "item_id": f"fixture-corpus:{index}",
            "document_id": patent["patent_id"],
            "text": text,
            "source_id": patent["source"]["source"]["source_id"],
            "source_revision": patent["source"]["source"]["version_label"],
        })
        corpus_values[text] = [1.0 if index == 0 else 0.0, 0.0 if index == 0 else 1.0]
    query = INPUT["query"]
    query_rows = [{
        "item_id": f"fixture-query:{query['query_id']}",
        "document_id": query["query_id"],
        "text": query["technical_description"],
        "source_id": query["selected_comparator_source_id"],
        "source_revision": "fixture-v1",
    }]
    export_runtime_text(corpus_rows, corpus_runtime, dataset_id="fixture-corpus", source_revision="fixture-v1", representation="text-v1")
    export_runtime_text(query_rows, query_runtime, dataset_id="fixture-queries", source_revision="fixture-v1", representation="query-v1")
    model = {"id": "fixture-model", "revision": "r1"}
    corpus_config = {
        "backend": "fixture",
        "encoder_kind": "fixture",
        "max_length": 32,
        "representation": "fixture-v1",
        "dtype": "<f4",
        "norm_policy": "none",
        "patembed_prompt_name": None,
        "e5_prefix_policy": None,
        "role": "passage",
    }
    query_config = {**corpus_config, "role": "query"}
    encode_vector_shards(
        corpus_runtime,
        tmp_path / "corpus-bundle",
        FakeEncoder(corpus_values),
        model=model,
        config=corpus_config,
        shard_size=2,
    )
    encode_vector_shards(
        query_runtime,
        tmp_path / "query-bundle",
        FakeEncoder({query["technical_description"]: [1.0, 0.0]}),
        model=query_model or model,
        config=query_config,
        shard_size=1,
    )
    config_path = tmp_path / "vector-config.json"
    config_path.write_text(json.dumps({
        "format": "ht-http-vector-config-v1",
        "corpus_bundle": str(tmp_path / "corpus-bundle"),
        "query_bundle": str(tmp_path / "query-bundle"),
        "corpus_runtime": str(corpus_runtime),
        "query_runtime": str(query_runtime),
        "query_ids": [query["query_id"]],
        "model": model,
    }, indent=2), encoding="utf-8")
    return config_path


def test_server_owned_vector_config_binds_http_job_to_exact_input(tmp_path: Path):
    vector_service = ConfiguredVectorSearch.from_config(_make_vector_config(tmp_path))
    service = HealthTechJobService(tmp_path / "jobs", code_commit="test", vector_search=vector_service)
    try:
        submitted = service.submit({"input": INPUT, "provider": {"id": "local-vector"}}, "vector-1")
        for _ in range(100):
            status = service.status(submitted["job_id"])
            if status["state"] in {"succeeded", "failed"}:
                break
        assert status["state"] == "succeeded"
        assert status["provider"]["id"] == "local-vector"
        result = service.result(submitted["job_id"])
        assert any("dense_cosine" in candidate["scores"] for candidate in result["dossier"]["candidates"])
    finally:
        service.close()


def test_vector_http_rejects_wrong_query_text_and_wrong_bundle_binding(tmp_path: Path):
    vector_service = ConfiguredVectorSearch.from_config(_make_vector_config(tmp_path))
    wrong_input = copy.deepcopy(INPUT)
    wrong_input["query"]["technical_description"] = "a different query"
    service = HealthTechJobService(tmp_path / "jobs-1", vector_search=vector_service)
    try:
        with pytest.raises(HTTPJobError, match="vector runtime") as exc_info:
            service.submit({"input": wrong_input, "provider": {"id": "local-vector"}}, "wrong-query")
        assert exc_info.value.code == "vector_input_mismatch"
    finally:
        service.close()

    wrong_model_config = _make_vector_config(tmp_path / "wrong-model", query_model={"id": "fixture-model", "revision": "r2"})
    with pytest.raises(VectorArtifactError, match="different model bindings"):
        ConfiguredVectorSearch.from_config(wrong_model_config)
