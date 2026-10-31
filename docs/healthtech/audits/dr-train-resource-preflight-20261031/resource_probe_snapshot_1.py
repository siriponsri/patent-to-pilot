"""Read-only resource and owned embedding-cache metadata; no model imports/jobs."""
import csv
import datetime
import importlib.metadata
import io
import json
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import sys


def command(arguments):
    try:
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=15, check=False)
        return {"exit_code": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()[:2000]}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"error": type(error).__name__ + ": " + str(error)}


def gpu():
    fields = ["index", "uuid", "name", "driver_version", "memory.total", "memory.free", "memory.used", "utilization.gpu", "compute_mode"]
    result = command(["nvidia-smi", "--query-gpu=" + ",".join(fields), "--format=csv,noheader,nounits"])
    rows = []
    if result.get("exit_code") == 0:
        for values in csv.reader(io.StringIO(result["stdout"]), skipinitialspace=True):
            rows.append(dict(zip(fields, [value.strip() for value in values])))
    return {"units": {"memory": "MiB", "utilization.gpu": "percent"}, "gpus": rows, "query": result}


def cpu():
    result = command(["lscpu", "--json"])
    wanted = {"Architecture:", "CPU(s):", "On-line CPU(s) list:", "Model name:", "Thread(s) per core:", "Core(s) per socket:", "Socket(s):", "CPU max MHz:", "CPU min MHz:"}
    selected = {}
    if result.get("exit_code") == 0:
        try:
            selected = {row["field"].rstrip(":"): row["data"] for row in json.loads(result["stdout"])["lscpu"] if row["field"] in wanted}
        except (ValueError, KeyError, TypeError):
            selected = {"parse_error": True}
    try:
        affinity_count = len(os.sched_getaffinity(0))
    except AttributeError:
        affinity_count = None
    return {"lscpu": selected, "logical_cpu_count": os.cpu_count(), "affinity_cpu_count": affinity_count, "load_averages_1_5_15_min": list(os.getloadavg()), "allocation": "UNKNOWN_NOT_GRANTED"}


def memory():
    values = {}
    wanted = {"MemTotal", "MemAvailable", "MemFree", "SwapTotal", "SwapFree"}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, _, value = line.partition(":")
        if key in wanted:
            values[key] = int(value.strip().split()[0])
    return {"units": "KiB", **values}


def storage(home):
    output = []
    for path in [home, Path("/tmp"), home / "patent-to-pilot-jobs"]:
        row = {"path": str(path), "exists": path.exists()}
        if row["exists"]:
            try:
                used = shutil.disk_usage(path)
                row.update({"total_bytes": used.total, "used_bytes": used.used, "free_bytes": used.free, "writable_observed": os.access(path, os.W_OK), "is_directory": path.is_dir()})
            except OSError as error:
                row["error"] = type(error).__name__
        output.append(row)
    return output


def runtimes(home):
    names = ["torch", "onnxruntime", "onnxruntime-gpu", "sentence-transformers", "transformers", "tokenizers", "numpy", "safetensors", "huggingface-hub", "accelerate", "faiss-cpu", "faiss-gpu"]
    packages = {}
    for name in names:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "NOT_INSTALLED_IN_THIS_INTERPRETER"
    environments = []
    for parent in [home / ".venvs", home / "venvs", home / "miniconda3/envs", home / "anaconda3/envs"]:
        if not parent.is_dir():
            continue
        try:
            for path in list(parent.iterdir())[:30]:
                if path.is_dir() and (path / "bin/python").exists():
                    environments.append({"environment": str(path), "python_exists": True, "packages": "NOT_EXECUTED_OR_INSPECTED"})
        except OSError as error:
            environments.append({"parent": str(parent), "error": type(error).__name__})
    return {"python_version": platform.python_version(), "python_executable": sys.executable, "packages": packages, "owned_environment_metadata": environments, "torch_cuda_runtime": "NOT_IMPORTED_OR_TESTED", "cuda_compiler": command(["nvcc", "--version"]) if shutil.which("nvcc") else {"status": "NOT_ON_PATH"}}


def cache(home):
    root = home / ".cache/huggingface/hub"
    result = {"root": str(root), "exists": root.is_dir(), "models": [], "scope": "Owned default HF cache metadata for embedding/patent models only; no weight contents, tokens or arbitrary cache roots read"}
    if not root.is_dir():
        return result
    keywords = ("patembed", "patent", "minilm", "modernbert", "mpnet", "e5", "bge", "embedding", "gte-")
    try:
        models = [path for path in root.iterdir() if path.is_dir() and path.name.startswith("models--") and any(word in path.name.lower() for word in keywords)]
        result["matching_model_count"] = len(models)
        for model in sorted(models)[:30]:
            row = {"cache_name": model.name, "snapshots": []}
            snapshots = model / "snapshots"
            if snapshots.is_dir():
                for snapshot in sorted(snapshots.iterdir())[:3]:
                    if not snapshot.is_dir():
                        continue
                    files = []
                    truncated = False
                    for index, path in enumerate(snapshot.rglob("*")):
                        if index >= 400:
                            truncated = True
                            break
                        if path.is_file():
                            try:
                                resolved = path.resolve()
                                if resolved.is_relative_to(root.resolve()):
                                    files.append({"path": path.relative_to(snapshot).as_posix(), "bytes": path.stat().st_size})
                            except OSError:
                                continue
                    item = {"revision_directory": snapshot.name, "files": files, "metadata_scan_truncated": truncated}
                    config = snapshot / "config.json"
                    if config.is_file() and config.resolve().is_relative_to(root.resolve()) and config.stat().st_size <= 65536:
                        try:
                            content = json.loads(config.read_text())
                            fields = ("model_type", "architectures", "hidden_size", "num_hidden_layers", "max_position_embeddings", "torch_dtype", "transformers_version")
                            item["config_metadata"] = {name: content[name] for name in fields if name in content}
                        except (OSError, ValueError):
                            item["config_metadata"] = "UNREADABLE"
                    row["snapshots"].append(item)
            result["models"].append(row)
    except OSError as error:
        result["error"] = type(error).__name__
    return result


home = Path.home()
output = {
    "format": "dr-train-read-only-resource-preflight-v1",
    "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "host": socket.gethostname(),
    "user_id": os.getuid(),
    "working_directory": os.getcwd(),
    "platform": {"system": platform.system(), "kernel": platform.release(), "machine": platform.machine()},
    "gpu": gpu(), "cpu": cpu(), "memory": memory(), "storage": storage(home),
    "runtimes": runtimes(home), "embedding_cache_metadata": cache(home),
    "allocation": "UNKNOWN_NOT_GRANTED_RESOURCE_OBSERVATION_ONLY",
    "actions": {"compute_or_model_inference": 0, "download": 0, "install": 0, "remote_files_written": 0, "settings_changed": 0, "services_touched": 0, "credential_content_reads": 0},
}
output["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
print(json.dumps(output, ensure_ascii=True))
