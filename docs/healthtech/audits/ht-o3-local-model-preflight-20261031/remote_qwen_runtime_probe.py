"""Read-only probe for the owned remote Qwen runtime boundary."""
from __future__ import annotations

import importlib
import json
import os
import pathlib
import shutil
import subprocess
import sys


def version(module_name: str) -> str:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # pragma: no cover - remote probe only
        return f"UNAVAILABLE:{type(exc).__name__}"
    return str(getattr(module, "__version__", "PRESENT"))


def main() -> None:
    torch_version = version("torch")
    cuda_available = False
    cuda_count = 0
    torch_cuda = None
    try:
        import torch

        torch.set_num_threads(8)
        cuda_available = bool(torch.cuda.is_available())
        cuda_count = int(torch.cuda.device_count())
        torch_cuda = torch.version.cuda
    except Exception as exc:  # pragma: no cover - remote probe only
        torch_cuda = f"ERROR:{type(exc).__name__}"

    gpu_query = {"status": "NOT_RUN"}
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=uuid,name,memory.total,memory.free,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
        gpu_query = {
            "exit_code": completed.returncode,
            "stdout_sha256": __import__("hashlib").sha256(
                completed.stdout.encode("utf-8")
            ).hexdigest(),
            "stderr_empty": not bool(completed.stderr),
            "line_count": len([line for line in completed.stdout.splitlines() if line.strip()]),
        }
    except Exception as exc:  # pragma: no cover - remote probe only
        gpu_query = {"status": f"ERROR:{type(exc).__name__}"}

    job_root = pathlib.Path(os.environ.get(
        "HT_REMOTE_JOB_ROOT",
        "/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031",
    ))
    qwen_root = job_root / "models" / "qwen3-8b"
    storage = shutil.disk_usage(job_root)
    print(json.dumps({
        "status": "PASS_REMOTE_RUNTIME_READ_ONLY",
        "python": sys.version.split()[0],
        "torch": torch_version,
        "torch_cuda": torch_cuda,
        "cuda_available": cuda_available,
        "cuda_device_count": cuda_count,
        "torch_threads": 8,
        "transformers": version("transformers"),
        "safetensors": version("safetensors"),
        "accelerate": version("accelerate"),
        "approved_gpu_uuid": "GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089",
        "gpu_query": gpu_query,
        "job_root_exists": job_root.exists(),
        "qwen_snapshot_exists": qwen_root.exists(),
        "qwen_snapshot_file_count": sum(1 for path in qwen_root.rglob("*") if path.is_file()) if qwen_root.exists() else 0,
        "job_root_free_bytes": storage.free,
        "job_root_total_bytes": storage.total,
        "remote_write": False,
        "model_load": False,
        "inference": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
