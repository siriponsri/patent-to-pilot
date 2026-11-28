"""Stage immutable checkpoint files and verify them before offline use."""

import argparse
import hashlib
import shutil
from pathlib import Path
from urllib.request import urlopen

from .inputs import digest, file_digest, specification, strict_json, write_json

TINY_ID = "yujiepan/qwen2.5-tiny-random"
TINY_REVISION = "0354728bb14944308c3134cf48d29302030a72c0"
TINY_EXTRAS = ("added_tokens.json", "special_tokens_map.json")
BASE_BLOBS = {
    "LICENSE": "6634c8cc3133b3848ec74b9f275acaaa1ea618ab",
    "config.json": "f81ead14ab072d65a07817f83a3ee0e5a1890d10",
    "generation_config.json": "dfc11073787daf1b0f9c0f1499487ab5f4c93738",
    "merges.txt": "20024bfe7c83998e9aeaf98a0cd6a2ce6306c2f0",
    "tokenizer.json": "443909a61d429dff23010e5bddd28ff530edda00",
    "tokenizer_config.json": "07bfe0640cb5a0037f9322287fbfc682806cf672",
    "vocab.json": "4783fe10ac3adce15ac8f358ef5462739852c569",
}
BASE_WEIGHT_SHA = "dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee"
WEIGHTS = "model.safetensors"


def model_identity(dry):
    base = specification()["checkpoint"]
    return (TINY_ID, TINY_REVISION) if dry else (base["repo_id"], base["revision"])


def model_files(dry):
    files = set(BASE_BLOBS) | {WEIGHTS}
    return (files - {"LICENSE"}) | set(TINY_EXTRAS) if dry else files


def model_manifest(directory, *, dry):
    repo, revision = model_identity(dry)
    files = model_files(dry)
    if any(not p.is_file() or p.is_symlink() for p in directory.iterdir()):
        raise ValueError("checkpoint directory requires regular, flat files")
    if {p.name for p in directory.iterdir()} != files | {"checkpoint.json"}:
        raise ValueError("checkpoint directory does not match the pinned file allowlist")
    payload = strict_json((directory / "checkpoint.json").read_bytes())
    if payload["repo"] != repo or payload["revision"] != revision or payload["files"].keys() != files:
        raise ValueError("checkpoint identity or file list mismatch")
    for name, expected in payload["files"].items():
        if file_digest(directory / name) != expected:
            raise ValueError(f"checkpoint file changed: {name}")
        if not dry:
            verify_upstream(directory / name, expected)
    return payload


def verify_upstream(path, sha256):
    if path.name == WEIGHTS:
        if sha256 != BASE_WEIGHT_SHA:
            raise ValueError("base weights differ from the pinned checkpoint")
        return
    raw = path.read_bytes()
    blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    if blob != BASE_BLOBS[path.name]:
        raise ValueError(f"pinned Hugging Face Git blob mismatch: {path.name}")


def stage(directory, *, dry):
    repo, revision = model_identity(dry)
    directory.mkdir(parents=True)
    hashes = {}
    for name in sorted(model_files(dry)):
        path = directory / name
        url = f"https://huggingface.co/{repo}/resolve/{revision}/{name}"
        with urlopen(url, timeout=90) as source, path.open("xb") as target:
            shutil.copyfileobj(source, target)
        sha256 = file_digest(path)
        if not dry:
            verify_upstream(path, sha256)
        hashes[name] = sha256
        print(f"{name} {sha256}", flush=True)
    write_json(directory / "checkpoint.json", {"repo": repo, "revision": revision, "files": hashes})
    print(f"checkpoint manifest {digest((directory / 'checkpoint.json').read_bytes())}", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    stage(args.directory, dry=args.dry_run)


if __name__ == "__main__":
    main()
