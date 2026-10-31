"""Server-owned local generation providers for HealthTech HTTP jobs."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable, Protocol

from patent_to_pilot.healthtech.engine import serialize_dossier
from patent_to_pilot.healthtech.contracts import DossierVersion


class GenerationProviderError(RuntimeError):
    """Raised when a configured local generation action cannot complete."""


class GenerationProvider(Protocol):
    def describe(self) -> dict[str, Any]: ...

    def generate(self, dossier: DossierVersion) -> dict[str, Any]: ...


class CallableGenerationProvider:
    """Small injected provider used by offline tests and controlled harnesses."""

    def __init__(self, metadata: dict[str, Any], generator: Callable[[DossierVersion], dict[str, Any]]):
        self._metadata = dict(metadata)
        self._generator = generator

    def describe(self) -> dict[str, Any]:
        return dict(self._metadata)

    def generate(self, dossier: DossierVersion) -> dict[str, Any]:
        result = self._generator(dossier)
        if not isinstance(result, dict):
            raise GenerationProviderError("local generation returned an invalid object")
        return result


class LocalQwenGenerationProvider:
    """Run the pinned local Qwen evidence-pack contract in a child process.

    The HTTP service never imports torch or transformers. The configured runner
    owns model loading, GPU checks, prompt construction, and schema validation.
    """

    CONFIG_FORMAT = "ht-http-local-generation-config-v1"
    RESULT_FORMAT = "ht-http-local-generation-result-v1"

    def __init__(
        self,
        *,
        model_root: Path,
        pack_builder_script: Path,
        generation_script: Path,
        model_id: str = "Qwen/Qwen3-8B",
        model_revision: str = "b968826d9c46dd6066d109eabc6255188de91218",
        python_executable: str | None = None,
        max_new_tokens: int = 512,
        max_findings: int = 4,
    ):
        if not model_root.is_dir():
            raise GenerationProviderError("local generation model root is unavailable")
        for path in (pack_builder_script, generation_script):
            if not path.is_file():
                raise GenerationProviderError("local generation runner script is unavailable")
        if max_new_tokens < 1 or max_new_tokens > 4096:
            raise ValueError("max_new_tokens must be between 1 and 4096")
        if max_findings < 1 or max_findings > 6:
            raise ValueError("max_findings must be between 1 and 6")
        self.model_root = model_root.resolve()
        self.pack_builder_script = pack_builder_script.resolve()
        self.generation_script = generation_script.resolve()
        self.model_id = model_id
        self.model_revision = model_revision
        self.python_executable = python_executable or sys.executable
        self.max_new_tokens = max_new_tokens
        self.max_findings = max_findings

    @classmethod
    def from_config(cls, config_path: str | Path) -> "LocalQwenGenerationProvider":
        path = Path(config_path)
        try:
            config = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise GenerationProviderError("local generation config is unreadable") from exc
        if not isinstance(config, dict) or config.get("format") != cls.CONFIG_FORMAT:
            raise GenerationProviderError("unsupported local generation config format")
        required = ("model_root", "pack_builder_script", "generation_script")
        if any(not isinstance(config.get(key), str) or not config[key].strip() for key in required):
            raise GenerationProviderError("local generation config is incomplete")
        return cls(
            model_root=Path(config["model_root"]),
            pack_builder_script=Path(config["pack_builder_script"]),
            generation_script=Path(config["generation_script"]),
            model_id=str(config.get("model_id", "Qwen/Qwen3-8B")),
            model_revision=str(config.get("model_revision", "b968826d9c46dd6066d109eabc6255188de91218")),
            python_executable=config.get("python_executable"),
            max_new_tokens=int(config.get("max_new_tokens", 512)),
            max_findings=int(config.get("max_findings", 4)),
        )

    def describe(self) -> dict[str, Any]:
        return {
            "id": "local-generation",
            "label": "Local Qwen evidence generator",
            "available": True,
            "model": self.model_id,
            "model_revision": self.model_revision,
            "billing_status": "not_billable_local",
            "actual_usd": 0.0,
            "reserved_usd": 0.0,
            "unknown_usd": 0.0,
            "resource_usage": "measured_local_resources",
            "generation_contract": "ht-o3-qwen3-frozen-evidence-pack-v1",
            "thinking": False,
        }

    @staticmethod
    def _run(command: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                command,
                cwd=cwd,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except OSError as exc:
            raise GenerationProviderError("local generation process could not start") from exc

    def generate(self, dossier: DossierVersion) -> dict[str, Any]:
        case_id = dossier.query.query_id
        with tempfile.TemporaryDirectory(prefix="ht-local-generation-") as temp_dir:
            root = Path(temp_dir)
            dossier_path = root / "dossier.json"
            pack_path = root / "pack.json"
            receipt_path = root / "receipt.json"
            dossier_path.write_text(
                json.dumps(serialize_dossier(dossier), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            build = self._run([
                self.python_executable,
                "-B",
                str(self.pack_builder_script),
                "--dossier",
                str(dossier_path),
                "--case-id",
                case_id,
                "--output",
                str(pack_path),
            ], cwd=self.pack_builder_script.parents[2])
            if build.returncode != 0:
                raise GenerationProviderError("local generation evidence-pack build failed")
            run = self._run([
                self.python_executable,
                "-B",
                str(self.generation_script),
                "--pack",
                str(pack_path),
                "--model-root",
                str(self.model_root),
                "--output",
                str(receipt_path),
                "--max-new-tokens",
                str(self.max_new_tokens),
                "--max-findings",
                str(self.max_findings),
            ], cwd=self.generation_script.parents[2])
            if run.returncode != 0 or not receipt_path.is_file():
                raise GenerationProviderError("local generation runner failed")
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise GenerationProviderError("local generation receipt is unreadable") from exc
            cases = receipt.get("cases") if isinstance(receipt, dict) else None
            if not isinstance(cases, list) or len(cases) != 1 or not isinstance(cases[0], dict):
                raise GenerationProviderError("local generation receipt has an invalid case count")
            case = cases[0]
            if case.get("case_id") != case_id or case.get("schema_valid") is not True:
                raise GenerationProviderError("local generation returned a schema-invalid result")
            return {
                "format": self.RESULT_FORMAT,
                "status": receipt.get("status"),
                "case_id": case_id,
                "model_id": receipt.get("model_id", self.model_id),
                "model_revision": receipt.get("model_revision", self.model_revision),
                "pack_sha256": receipt.get("pack_sha256"),
                "schema_valid": True,
                "prompt_tokens": case.get("prompt_tokens"),
                "output_tokens": case.get("output_tokens"),
                "generation_latency_seconds": case.get("generation_latency_seconds"),
                "output_sha256": case.get("output_sha256"),
                "parsed_output": case.get("parsed_output"),
                "provider_calls": 0,
                "paid_cost_usd": 0.0,
                "billing_status": "not_billable_local",
            }
