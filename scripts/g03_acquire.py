#!/usr/bin/env python3
"""Acquire the bounded G03 starter batch with streaming integrity checks.

No third-party packages, parallel downloads, indexing, embeddings, or model calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
RECEIPTS = DATA / "manifests"
CHUNK = 1024 * 1024
USER_AGENT = "patent-to-pilot-g03/1.0"

PLS_POINTERS = {
    "atazanavir.csv": {
        "oid": "c5460ff1c1e96af7098c2bb54fe9d7a957cca11c05229edfd4d65abefbf22b49",
        "size": 137145663,
    },
    "ritonavir.csv": {
        "oid": "4a65eb23472a7f631f0f5af12af6d9e6a89993f62e5439b876a5c0072d80d319",
        "size": 121948387,
    },
}

FILES = [
    {
        "id": "pls_atazanavir",
        "dataset": "PLS EMNLP2022",
        "license": "CC BY 4.0 for patent_ls data; repository code is separate AGPL-3.0",
        "kind": "git-lfs",
        "name": "atazanavir.csv",
        "path": "pls/atazanavir.csv",
        "size": 137145663,
        "sha256": "c5460ff1c1e96af7098c2bb54fe9d7a957cca11c05229edfd4d65abefbf22b49",
        "source": "https://github.com/boschresearch/pls_benchmark_emnlp2022",
        "revision": "0a035ce46815b2aae5b7e49031c2975ba91fb0d1",
        "pointer_url": "https://raw.githubusercontent.com/boschresearch/pls_benchmark_emnlp2022/0a035ce46815b2aae5b7e49031c2975ba91fb0d1/patent_ls/atazanavir.csv",
    },
    {
        "id": "pls_ritonavir",
        "dataset": "PLS EMNLP2022",
        "license": "CC BY 4.0 for patent_ls data; repository code is separate AGPL-3.0",
        "kind": "git-lfs",
        "name": "ritonavir.csv",
        "path": "pls/ritonavir.csv",
        "size": 121948387,
        "sha256": "4a65eb23472a7f631f0f5af12af6d9e6a89993f62e5439b876a5c0072d80d319",
        "source": "https://github.com/boschresearch/pls_benchmark_emnlp2022",
        "revision": "0a035ce46815b2aae5b7e49031c2975ba91fb0d1",
        "pointer_url": "https://raw.githubusercontent.com/boschresearch/pls_benchmark_emnlp2022/0a035ce46815b2aae5b7e49031c2975ba91fb0d1/patent_ls/ritonavir.csv",
    },
    {
        "id": "enterpriserag_github_0001",
        "dataset": "EnterpriseRAG-Bench",
        "license": "Repository LICENSE snapshot is MIT for code; no separate data/release-asset license is asserted here",
        "kind": "http",
        "name": "github_slice_0001.zip",
        "path": "enterprise/github_slice_0001.zip",
        "size": 12246702,
        "sha256": "4e6d2f445ce56b98ba3ebf41de29f80f63d5eed87dd1c246aacfefb1c942303a",
        "source": "https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/tag/v1.0.0",
        "revision": "v1.0.0",
        "url": "https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/v1.0.0/github_slice_0001.zip",
    },
    {
        "id": "enterpriserag_github_0002",
        "dataset": "EnterpriseRAG-Bench",
        "license": "Repository LICENSE snapshot is MIT for code; no separate data/release-asset license is asserted here",
        "kind": "http",
        "name": "github_slice_0002.zip",
        "path": "enterprise/github_slice_0002.zip",
        "size": 7431363,
        "sha256": "34e039f2359b36fee11ab212c981de567a7b21eee5bbe10af43c2d41960d1a12",
        "source": "https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/tag/v1.0.0",
        "revision": "v1.0.0",
        "url": "https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/v1.0.0/github_slice_0002.zip",
    },
    {
        "id": "enterpriserag_questions",
        "dataset": "EnterpriseRAG-Bench",
        "license": "Repository LICENSE snapshot is MIT for code; no separate data/release-asset license is asserted here",
        "kind": "http",
        "name": "questions.jsonl",
        "path": "enterprise/questions.jsonl",
        "size": 764927,
        "sha256": "f9524b9157cd43aae36b99333a124738804306ea6d07f332d49faa6d3d147905",
        "source": "https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/tag/v1.0.0",
        "revision": "v1.0.0",
        "url": "https://github.com/onyx-dot-app/EnterpriseRAG-Bench/releases/download/v1.0.0/questions.jsonl",
    },
]


def request(
    url: str,
    data: bytes | None = None,
    content_type: str | None = None,
    accept: str = "*/*",
):
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if content_type:
        headers["Content-Type"] = content_type
    return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=120)


def lfs_url(item: dict) -> str:
    payload = {
        "operation": "download",
        "transfers": ["basic"],
        "objects": [{"oid": item["sha256"], "size": item["size"]}],
    }
    with request(
        "https://github.com/boschresearch/pls_benchmark_emnlp2022.git/info/lfs/objects/batch",
        json.dumps(payload).encode(),
        "application/json",
        "application/vnd.git-lfs+json",
    ) as response:
        result = json.load(response)
    obj = result["objects"][0]
    if "error" in obj or "actions" not in obj:
        raise RuntimeError(f"LFS object unavailable: {obj}")
    return obj["actions"]["download"]["href"]


def assert_not_pointer(first: bytes, name: str) -> None:
    text = first[:200].decode("utf-8", errors="ignore")
    if text.startswith("version https://git-lfs.github.com/spec/v1"):
        raise RuntimeError(f"{name}: received Git LFS pointer, not payload")
    if b"<!DOCTYPE html" in first[:4096].lower() or b"<html" in first[:4096].lower():
        raise RuntimeError(f"{name}: received HTML/error page, not payload")


def download(item: dict, force: bool = False) -> dict:
    destination = DATA / "raw" / item["path"]
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not force:
        size = destination.stat().st_size
        digest = sha256(destination)
        if size == item["size"] and digest == item["sha256"]:
            return {**item, "status": "already_verified", "actual_bytes": size, "actual_sha256": digest}
        raise RuntimeError(f"existing file failed integrity; use --force to replace: {destination}")
    url = lfs_url(item) if item["kind"] == "git-lfs" else item["url"]
    partial = destination.with_name(destination.name + ".partial")
    if partial.exists():
        partial.unlink()
    started = time.time()
    total = 0
    digest = hashlib.sha256()
    with request(url) as response, partial.open("wb") as output:
        first = response.read(CHUNK)
        assert_not_pointer(first, item["name"])
        while first:
            output.write(first)
            digest.update(first)
            total += len(first)
            first = response.read(CHUNK)
    actual = digest.hexdigest()
    if total != item["size"] or actual != item["sha256"]:
        partial.unlink(missing_ok=True)
        raise RuntimeError(f"integrity failure for {item['name']}: bytes={total} sha256={actual}")
    partial.replace(destination)
    return {**item, "status": "downloaded", "actual_bytes": total, "actual_sha256": actual, "seconds": round(time.time() - started, 2)}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=[x["id"] for x in FILES], action="append")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    selected = [x for x in FILES if not args.only or x["id"] in args.only]
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    receipt_path = RECEIPTS / "g03-acquisition-receipt.json"
    receipt = {
        "record": "G03-ACQUISITION-001",
        "status": "IN_PROGRESS",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "python": platform.python_version(),
        "host": platform.platform(),
        "chunk_bytes": CHUNK,
        "sequential": True,
        "files": [],
    }
    if receipt_path.exists():
        prior = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["files"] = prior.get("files", [])
        receipt["started_utc"] = prior.get("started_utc", receipt["started_utc"])
    for item in selected:
        print(f"ACQUIRE {item['name']} -> data/raw/{item['path']}", flush=True)
        result = download(item, args.force)
        receipt["files"] = [x for x in receipt["files"] if x.get("id") != result.get("id")]
        receipt["files"].append(result)
        print(f"OK {item['name']} {result['actual_bytes']} bytes {result['actual_sha256']}", flush=True)
    receipt["status"] = "DATA_RAW_VERIFIED"
    receipt["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
