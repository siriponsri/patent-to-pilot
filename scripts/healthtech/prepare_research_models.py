"""Download the declared HealthTech model artifacts into private Windows storage.

The downloader is intentionally allowlist-based. It records the immutable
Hub revision, model-card license, selected files, byte counts, and SHA-256
hashes without staging weights or tokens in the repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from huggingface_hub import HfApi, snapshot_download


MODELS: dict[str, dict[str, Any]] = {
    "patembed-base": {
        "repo_id": "datalyes/patembed-base",
        "revision": "244ba452908a3093be11efb8a44396652317fb14",
        "license": "cc-by-nc-sa-4.0",
        "allow_patterns": [
            ".gitattributes",
            "README.md",
            "config.json",
            "config_sentence_transformers.json",
            "modules.json",
            "sentence_bert_config.json",
            "special_tokens_map.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "vocab.txt",
            "1_Pooling/config.json",
            "2_Dense/config.json",
            "2_Dense/model.safetensors",
            "model.safetensors",
        ],
    },
    "multilingual-e5-base": {
        "repo_id": "intfloat/multilingual-e5-base",
        "revision": "d128750597153bb5987e10b1c3493a34e5a4502a",
        "license": "mit",
        "allow_patterns": [
            ".gitattributes",
            "README.md",
            "config.json",
            "modules.json",
            "sentence_bert_config.json",
            "sentencepiece.bpe.model",
            "special_tokens_map.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "1_Pooling/config.json",
            "model.safetensors",
        ],
    },
    "qwen3-8b": {
        "repo_id": "Qwen/Qwen3-8B",
        "revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "license": "apache-2.0",
        "allow_patterns": [
            ".gitattributes",
            "LICENSE",
            "README.md",
            "config.json",
            "generation_config.json",
            "merges.txt",
            "model-*.safetensors",
            "model.safetensors.index.json",
            "tokenizer.json",
            "tokenizer_config.json",
            "vocab.json",
        ],
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file() and ".cache" not in path.parts
    )


def _model_info(api: HfApi, spec: dict[str, Any]) -> dict[str, Any]:
    info = api.model_info(
        spec["repo_id"],
        revision=spec["revision"],
        files_metadata=True,
        token=False,
    )
    if info.sha != spec["revision"]:
        raise RuntimeError(f"Hub revision drift for {spec['repo_id']}: {info.sha}")
    card_data = info.card_data.to_dict() if info.card_data else {}
    license_value = card_data.get("license")
    if license_value != spec["license"]:
        raise RuntimeError(
            f"license drift for {spec['repo_id']}: expected {spec['license']}, got {license_value}"
        )
    return {
        "repo_id": spec["repo_id"],
        "revision": info.sha,
        "last_modified": info.last_modified.isoformat() if info.last_modified else None,
        "license": license_value,
        "allow_patterns": list(spec["allow_patterns"]),
    }


def download_model(name: str, destination: Path, *, api: HfApi) -> dict[str, Any]:
    spec = MODELS[name]
    metadata = _model_info(api, spec)
    destination.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=spec["repo_id"],
        revision=spec["revision"],
        allow_patterns=spec["allow_patterns"],
        local_dir=str(destination),
        local_dir_use_symlinks=False,
        token=False,
    )
    files = []
    for path in _files(destination):
        relative = path.relative_to(destination).as_posix()
        files.append({
            "path": relative,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        })
    expected = {pattern for pattern in spec["allow_patterns"] if "*" not in pattern}
    actual = {item["path"] for item in files}
    missing = sorted(expected - actual)
    if missing:
        raise RuntimeError(f"missing allowlisted files for {name}: {missing}")
    return {
        **metadata,
        "destination": str(destination.resolve()),
        "files": files,
        "total_bytes": sum(item["bytes"] for item in files),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--models", nargs="+", choices=sorted(MODELS), default=sorted(MODELS))
    args = parser.parse_args()

    api = HfApi()
    records = []
    for name in args.models:
        records.append(download_model(name, args.output / name, api=api))
    manifest = {
        "format": "ht-research-model-artifacts-v1",
        "status": "PASS_IMMUTABLE_HF_ARTIFACTS_DOWNLOADED",
        "storage": "private Windows path; not for repository staging",
        "models": records,
    }
    manifest_path = args.output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": manifest["status"],
        "manifest": str(manifest_path.resolve()),
        "models": [{"repo_id": row["repo_id"], "bytes": row["total_bytes"]} for row in records],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
