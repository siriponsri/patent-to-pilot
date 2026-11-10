"""CPU-only local Qwen shard/config observation. No model loading or benchmark IO."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time


def observe(root: Path) -> dict:
    root = root.resolve(strict=True)
    index_path = root / "model.safetensors.index.json"
    index = json.loads(index_path.read_bytes())
    names = sorted(set(index["weight_map"].values()))
    if not names or any(type(name) is not str or re.fullmatch(r"model-\d+-of-\d+\.safetensors", name) is None for name in names):
        raise ValueError("unexpected shard inventory")
    required = names + ["model.safetensors.index.json", "config.json", "tokenizer.json", "tokenizer_config.json", "generation_config.json"]
    files = {}
    for name in required:
        path = root / name
        if path.is_symlink() or path.resolve().parent != root or not path.is_file():
            raise ValueError("model identity file missing or outside declared root")
        before = path.stat()
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(8 << 20), b""):
                digest.update(block)
        after = path.stat()
        if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise ValueError("identity file changed during observation")
        files[name] = {"sha256": digest.hexdigest(), "bytes": after.st_size}
        print(json.dumps({"event": "file_hashed", "file": name, "bytes": after.st_size}), flush=True)
    if hashlib.sha256(index_path.read_bytes()).hexdigest() != files[index_path.name]["sha256"]:
        raise ValueError("index changed during observation")
    generation = json.loads((root / "generation_config.json").read_bytes())
    keys = ("bos_token_id", "eos_token_id", "pad_token_id", "do_sample", "temperature", "top_k", "top_p",
            "repetition_penalty", "num_beams", "max_length", "max_new_tokens")
    return {"format": "ptp-qwen-local-identity-v1", "status": "OBSERVED_NOT_EXTERNAL_AUTHENTICATION",
            "observed_utc": datetime.now(timezone.utc).isoformat(), "shards": len(names),
            "weight_bytes": sum(files[name]["bytes"] for name in names), "files": files,
            "generation_file_settings": {key: generation[key] for key in keys if key in generation},
            "effective_library_defaults": "NOT_RESOLVED", "weights_loaded": False,
            "benchmark_accessed": False, "source_authenticity": "NOT_ESTABLISHED_BY_LOCAL_HASHING"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--status-log", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists; preserve previous attempt")
    started = time.monotonic()
    with args.status_log.open("x", encoding="utf-8", buffering=1) as status:
        status.write(datetime.now(timezone.utc).isoformat() + " START CPU_IDENTITY\n")
        try:
            report = observe(args.model_root)
            report["seconds"] = round(time.monotonic() - started, 3)
            with args.output.open("x", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2)
                handle.write("\n")
        except BaseException:
            status.write(datetime.now(timezone.utc).isoformat() + " EXIT 1\n")
            raise
        status.write(datetime.now(timezone.utc).isoformat() + " EXIT 0\n")
    print(json.dumps({key: report[key] for key in ("status", "shards", "weight_bytes", "seconds")}), flush=True)


if __name__ == "__main__":
    main()
