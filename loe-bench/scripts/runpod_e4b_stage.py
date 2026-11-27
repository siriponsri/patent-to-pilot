"""Stage the pinned public E4b snapshot and verify every file against Hugging Face."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import time


def stage_file(root, base, file):
    name = file["path"]
    if Path(name).name != name or name in {".", ".."}:
        raise ValueError(f"invalid snapshot filename: {name}")
    target = root / name
    partial = root / (name + ".partial")
    start = time.monotonic()
    subprocess.run([
        "curl", "--fail", "--location", "--silent", "--show-error", "--connect-timeout", "15",
        "--max-time", "300", "--retry", "2", "--retry-max-time", "600", "--output", str(partial),
        f"{base}/{name}?download=true",
    ], check=True)
    size = partial.stat().st_size
    if size != file["size"]:
        raise ValueError(f"size mismatch: {name}")
    sha256 = hashlib.sha256()
    blob = hashlib.sha1(f"blob {size}\0".encode(), usedforsecurity=False)
    with partial.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            sha256.update(chunk)
            if "lfs" not in file:
                blob.update(chunk)
    expected = file["lfs"]["oid"] if "lfs" in file else file["oid"]
    observed = sha256.hexdigest() if "lfs" in file else blob.hexdigest()
    if expected != observed:
        raise ValueError(f"digest mismatch: {name}")
    partial.replace(target)
    print(f"verified {name} ({size} bytes)", flush=True)
    return {"name": name, "bytes": size, "sha256": sha256.hexdigest(),
            "download_and_verify_s": time.monotonic() - start}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    model = manifest["model_id"]
    revision = manifest["revision"]
    base = f"https://huggingface.co/{model}/resolve/{revision}"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    with ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(lambda item: stage_file(args.output_dir, base, item), manifest["files"]))
    summary = {"model_id": model, "revision": revision, "files": files,
               "download_and_verify_wall_s": time.monotonic() - started}
    with (args.output_dir / "verified_files.json").open("w", encoding="utf-8") as output:
        json.dump(summary, output, indent=2)


if __name__ == "__main__":
    main()
