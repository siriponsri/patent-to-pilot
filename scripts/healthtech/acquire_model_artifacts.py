"""Acquire pinned public ONNX encoder and reranker artifacts for local HT runs."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import os
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class ModelSpec:
    model_id: str
    revision: str
    license: str
    files: tuple[str, ...]


SPECS = (
    ModelSpec(
        model_id="sentence-transformers/all-MiniLM-L6-v2",
        revision="1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        license="Apache-2.0",
        files=(
            "tokenizer.json",
            "tokenizer_config.json",
            "config.json",
            "sentence_bert_config.json",
            "1_Pooling/config.json",
            "onnx/model_quint8_avx2.onnx",
            "README.md",
        ),
    ),
    ModelSpec(
        model_id="cross-encoder/ms-marco-MiniLM-L-6-v2",
        revision="233902d25c440f23af6f7d6e94d2946bac0bee0a",
        license="Apache-2.0",
        files=(
            "tokenizer.json",
            "tokenizer_config.json",
            "config.json",
            "onnx/model_quint8_avx2.onnx",
            "README.md",
        ),
    ),
)


def _fetch(url: str, destination: Path, max_bytes: int) -> tuple[int, str]:
    part = destination.with_name(destination.name + ".part")
    part.unlink(missing_ok=True)
    total = 0
    digest = hashlib.sha256()
    request = Request(url, headers={"User-Agent": "patent-to-pilot-public-case-prep"})
    try:
        with urlopen(request, timeout=120) as response, part.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise ValueError(f"model file exceeds cap: {url}")
                handle.write(chunk)
                digest.update(chunk)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(part, destination)
    except Exception:
        part.unlink(missing_ok=True)
        raise
    return total, digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/raw/healthtech/models"))
    parser.add_argument("--max-file-bytes", type=int, default=50_000_000)
    parser.add_argument("--max-total-bytes", type=int, default=70_000_000)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    total_bytes = 0
    files: list[dict[str, object]] = []
    for spec in SPECS:
        model_root = args.output / spec.model_id.replace("/", "-")
        model_root.mkdir(parents=True, exist_ok=True)
        for relative in spec.files:
            destination = model_root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            url = f"https://huggingface.co/{spec.model_id}/resolve/{spec.revision}/{relative}"
            size, sha256 = _fetch(url, destination, args.max_file_bytes)
            total_bytes += size
            if total_bytes > args.max_total_bytes:
                raise ValueError("model acquisition exceeds cumulative byte cap")
            files.append({
                "model_id": spec.model_id,
                "revision": spec.revision,
                "license": spec.license,
                "relative_path": destination.relative_to(args.output).as_posix(),
                "source_url": url,
                "bytes": size,
                "sha256": sha256,
            })
    manifest = {
        "status": "LOCAL_MODEL_SNAPSHOT_ACQUIRED",
        "retrieved_files": files,
        "total_bytes": total_bytes,
        "rights": "Model cards declare Apache-2.0; weights remain local-only and are excluded from Git.",
        "limitations": [
            "The encoder and reranker were trained on general web/MS MARCO data, not medical-device patent data.",
            "Short-context ONNX quantized variants are pinned for reproducible offline development diagnostics only.",
        ],
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "files": len(files), "total_bytes": total_bytes}))


if __name__ == "__main__":
    main()
