"""Pinned local Transformer encoders for the HealthTech vector workflow.

The implementation intentionally executes the released SentenceTransformers
module contract directly.  It does not replace PatEmbed's projection with a
raw AutoModel mean pool and it keeps e5 query/passage prefixes explicit.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Literal, Mapping


EncoderKind = Literal["patembed", "e5"]
EncoderRole = Literal["query", "passage"]


class TransformerEncoderError(ValueError):
    """Raised when a local model does not satisfy the frozen encoder contract."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json_value(path: Path) -> Any:
    if not path.is_file():
        raise TransformerEncoderError(f"required model file is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _read_json(path: Path) -> dict[str, Any]:
    value = _read_json_value(path)
    if not isinstance(value, dict):
        raise TransformerEncoderError(f"model JSON must be an object: {path}")
    return value


def _load_modules(model_dir: Path) -> list[dict[str, Any]]:
    value = _read_json_value(model_dir / "modules.json")
    if not isinstance(value, list):
        raise TransformerEncoderError("modules.json must be a list")
    if not all(isinstance(item, dict) for item in value):
        raise TransformerEncoderError("modules.json entries must be objects")
    return [dict(item) for item in value]


def _prompt_text(model_dir: Path, prompt_name: str, role: EncoderRole) -> str:
    config = _read_json(model_dir / "config_sentence_transformers.json")
    prompts = config.get("prompts")
    if not isinstance(prompts, dict) or prompt_name not in prompts:
        raise TransformerEncoderError(f"unknown PatEmbed prompt: {prompt_name}")
    prompt = prompts[prompt_name]
    if not isinstance(prompt, dict):
        raise TransformerEncoderError("PatEmbed prompt must declare query and passage fields")
    key = "q_text" if role == "query" else "pos_text"
    value = prompt.get(key)
    if not isinstance(value, str) or not value:
        raise TransformerEncoderError(f"PatEmbed prompt {prompt_name!r} is missing {key}")
    return value


def prepare_encoder_inputs(
    texts: list[str],
    *,
    kind: EncoderKind,
    role: EncoderRole,
    prompt_name: str | None = None,
    prompt_config: Mapping[str, Mapping[str, str]] | None = None,
) -> list[str]:
    """Apply the frozen input namespace for one encoder role."""
    if kind == "e5":
        prefix = "query: " if role == "query" else "passage: "
        return [prefix + text for text in texts]
    if kind != "patembed":
        raise TransformerEncoderError(f"unsupported encoder kind: {kind}")
    if prompt_name is None:
        return list(texts)
    if prompt_config is None or prompt_name not in prompt_config:
        raise TransformerEncoderError(f"PatEmbed prompt config is missing {prompt_name}")
    field = "q_text" if role == "query" else "pos_text"
    prefix = prompt_config[prompt_name].get(field)
    if not isinstance(prefix, str) or not prefix:
        raise TransformerEncoderError(f"PatEmbed prompt {prompt_name!r} is missing {field}")
    return [prefix + text for text in texts]


def _validate_model_layout(model_dir: Path, *, kind: EncoderKind) -> dict[str, Any]:
    model_dir = model_dir.resolve()
    if not model_dir.is_dir():
        raise TransformerEncoderError(f"model directory is missing: {model_dir}")
    modules = _load_modules(model_dir)
    module_paths = [str(item.get("path", "")) for item in modules]
    module_types = [str(item.get("type", "")) for item in modules]
    expected_prefix = ["", "1_Pooling"]
    if module_paths[:2] != expected_prefix or module_types[:2] != [
        "sentence_transformers.models.Transformer",
        "sentence_transformers.models.Pooling",
    ]:
        raise TransformerEncoderError("model does not use the required Transformer + Pooling modules")
    pooling = _read_json(model_dir / "1_Pooling" / "config.json")
    if not pooling.get("pooling_mode_mean_tokens") or pooling.get("pooling_mode_cls_token"):
        raise TransformerEncoderError("model must use masked mean pooling without CLS pooling")
    if pooling.get("pooling_mode_max_tokens") or pooling.get("pooling_mode_lasttoken"):
        raise TransformerEncoderError("model uses an unsupported pooling mode")
    transformer_config = _read_json(model_dir / "config.json")
    hidden_size = int(transformer_config.get("hidden_size", 0))
    if kind == "patembed":
        if pooling.get("include_prompt") is not True:
            raise TransformerEncoderError("PatEmbed pooling must include prompt tokens")
        if module_paths[2:] != ["2_Dense"] or module_types[2:] != ["sentence_transformers.models.Dense"]:
            raise TransformerEncoderError("PatEmbed must include exactly one Dense projection module")
        dense = _read_json(model_dir / "2_Dense" / "config.json")
        if int(dense.get("in_features", 0)) != hidden_size or int(dense.get("out_features", 0)) != 768:
            raise TransformerEncoderError("PatEmbed Dense projection must be hidden_size x 768")
        if bool(dense.get("bias", True)):
            raise TransformerEncoderError("PatEmbed Dense projection must be bias-free")
        projection = model_dir / "2_Dense" / "model.safetensors"
        if not projection.is_file():
            raise TransformerEncoderError("PatEmbed projection weights are missing")
        if hidden_size != 1024:
            raise TransformerEncoderError("PatEmbed hidden size must be 1024")
    elif kind == "e5":
        if module_paths[2:] != ["2_Normalize"] or module_types[2:] != ["sentence_transformers.models.Normalize"]:
            raise TransformerEncoderError("e5 must include the Normalize module")
        if hidden_size != 768:
            raise TransformerEncoderError("multilingual-e5-base hidden size must be 768")
    else:
        raise TransformerEncoderError(f"unsupported encoder kind: {kind}")
    if int(pooling.get("word_embedding_dimension", 0)) != hidden_size:
        raise TransformerEncoderError("pooling dimension does not match transformer hidden size")
    return {
        "model_dir": str(model_dir),
        "modules": modules,
        "pooling": pooling,
        "transformer_config": transformer_config,
        "hidden_size": hidden_size,
    }


def build_transformer_model_binding(
    model_dir: str | Path,
    *,
    model_id: str,
    revision: str,
    kind: EncoderKind,
) -> dict[str, Any]:
    """Return a portable binding for every model file used by the backend."""
    root = Path(model_dir).resolve()
    _validate_model_layout(root, kind=kind)
    relative_files = [
        "config.json",
        "modules.json",
        "1_Pooling/config.json",
        "tokenizer.json",
        "model.safetensors",
    ]
    if kind == "patembed":
        relative_files.extend(["config_sentence_transformers.json", "2_Dense/config.json", "2_Dense/model.safetensors"])
    artifacts: dict[str, dict[str, Any]] = {}
    for relative in relative_files:
        path = root / relative
        if not path.is_file():
            raise TransformerEncoderError(f"required model file is missing: {path}")
        artifacts[relative] = {"sha256": _sha256_file(path), "bytes": path.stat().st_size}
    return {
        "model_id": model_id,
        "revision": revision,
        "encoder_kind": kind,
        "implementation": "transformer_masked_mean_projection_l2_v1",
        "model_artifact": {"filename": "model.safetensors", **artifacts["model.safetensors"]},
        "tokenizer_artifact": {"filename": "tokenizer.json", **artifacts["tokenizer.json"]},
        "artifact_files": artifacts,
    }


@dataclass(frozen=True)
class EncoderStats:
    rows: int = 0
    token_count: int = 0


class TransformerEncoder:
    """Encode one role with a local, pinned Transformer artifact."""

    def __init__(
        self,
        model_dir: str | Path,
        *,
        kind: EncoderKind,
        role: EncoderRole,
        max_length: int = 512,
        device: str = "auto",
        prompt_name: str | None = None,
    ) -> None:
        if type(max_length) is not int or max_length < 1 or max_length > 512:
            raise ValueError("max_length must be between 1 and 512")
        self.model_dir = Path(model_dir).resolve()
        self.kind = kind
        self.role = role
        self.max_length = max_length
        self.prompt_name = prompt_name if kind == "patembed" else None
        self.layout = _validate_model_layout(self.model_dir, kind=kind)
        prompt_config: dict[str, dict[str, str]] | None = None
        if self.prompt_name is not None:
            prompt_config_raw = _read_json(self.model_dir / "config_sentence_transformers.json").get("prompts")
            if not isinstance(prompt_config_raw, dict):
                raise TransformerEncoderError("PatEmbed prompt configuration is missing")
            prompt_config = {
                str(name): {str(key): str(value) for key, value in value.items()}
                for name, value in prompt_config_raw.items()
                if isinstance(value, dict)
            }
            _prompt_text(self.model_dir, self.prompt_name, role)
        self._prompt_config = prompt_config
        try:
            import torch
            from safetensors.torch import load_file
            from transformers import AutoModel, AutoTokenizer
        except ImportError as exc:  # pragma: no cover - exercised on the remote host
            raise RuntimeError(
                "transformer encoding requires pinned torch, transformers, and safetensors"
            ) from exc
        self.torch = torch
        self.device = self._resolve_device(device)
        self.tokenizer = AutoTokenizer.from_pretrained(
            str(self.model_dir), local_files_only=True, trust_remote_code=False, use_fast=True
        )
        self.model = AutoModel.from_pretrained(
            str(self.model_dir), local_files_only=True, trust_remote_code=False
        ).to(self.device)
        self.model.eval()
        self.projection = None
        if kind == "patembed":
            state = load_file(str(self.model_dir / "2_Dense" / "model.safetensors"), device="cpu")
            weight = state.get("linear.weight")
            if weight is None and len(state) == 1:
                weight = next(iter(state.values()))
            if weight is None or tuple(weight.shape) != (768, 1024):
                raise TransformerEncoderError("PatEmbed projection weight must have shape (768, 1024)")
            self.projection = weight.to(device=self.device, dtype=torch.float32)
        self.stats = EncoderStats()

    def _resolve_device(self, requested: str) -> Any:
        if requested == "auto":
            requested = "cuda" if self.torch.cuda.is_available() else "cpu"
        if requested.startswith("cuda") and not self.torch.cuda.is_available():
            raise RuntimeError("CUDA was requested but is not available")
        return self.torch.device(requested)

    def encode(self, texts: list[str]) -> tuple[Any, int]:
        prepared = prepare_encoder_inputs(
            texts,
            kind=self.kind,
            role=self.role,
            prompt_name=self.prompt_name,
            prompt_config=self._prompt_config,
        )
        encoded = self.tokenizer(
            prepared,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
            return_attention_mask=True,
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with self.torch.inference_mode():
            output = self.model(**encoded)
            hidden = output.last_hidden_state
            mask = encoded["attention_mask"].unsqueeze(-1).to(dtype=hidden.dtype)
            pooled = (hidden * mask).sum(dim=1) / mask.sum(dim=1).clamp_min(1e-9)
            if self.projection is not None:
                pooled = self.torch.nn.functional.linear(pooled, self.projection)
            vectors = self.torch.nn.functional.normalize(pooled, p=2, dim=1)
        token_count = int(encoded["attention_mask"].sum().item())
        self.stats = EncoderStats(rows=self.stats.rows + len(texts), token_count=self.stats.token_count + token_count)
        values = vectors.detach().cpu().numpy().astype("<f4", copy=False)
        if values.ndim != 2 or values.shape[1] != 768:
            raise TransformerEncoderError(f"encoder returned unexpected shape: {values.shape}")
        return values, token_count
