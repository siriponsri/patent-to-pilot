#!/usr/bin/env python3
"""Fetch small source/license metadata snapshots for the G03 batch only."""
from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "metadata"
CHUNK = 1024 * 1024
ITEMS = [
    ("pls", "README.md", "https://raw.githubusercontent.com/boschresearch/pls_benchmark_emnlp2022/0a035ce46815b2aae5b7e49031c2975ba91fb0d1/Readme.md", "0a035ce46815b2aae5b7e49031c2975ba91fb0d1", "CC BY 4.0 for patent_ls data; repository code terms are separate"),
    ("pls", "LICENSE", "https://raw.githubusercontent.com/boschresearch/pls_benchmark_emnlp2022/0a035ce46815b2aae5b7e49031c2975ba91fb0d1/LICENSE", "0a035ce46815b2aae5b7e49031c2975ba91fb0d1", "repository license snapshot; data-specific terms remain as documented"),
    ("enterprise", "README.md", "https://raw.githubusercontent.com/onyx-dot-app/EnterpriseRAG-Bench/main/README.md", "v1.0.0 release; README source branch main", "README badge identifies the repository code license as MIT; it does not establish a separate data/release-asset license"),
    ("enterprise", "LICENSE", "https://raw.githubusercontent.com/onyx-dot-app/EnterpriseRAG-Bench/main/LICENSE", "v1.0.0 release; LICENSE source branch main", "MIT License text for the repository/code; data terms are not separately asserted by this file"),
    ("enterprise", "release-v1.0.0.json", "https://api.github.com/repos/onyx-dot-app/EnterpriseRAG-Bench/releases/tags/v1.0.0", "v1.0.0", "release asset metadata only; contains no independent data-license grant"),
]

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    for group, name, url, revision, license_note in ITEMS:
        target = OUT / group / name
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".partial")
        digest = hashlib.sha256(); total = 0
        req = urllib.request.Request(url, headers={"User-Agent": "patent-to-pilot-g03/1.0", "Accept": "*/*"})
        with urllib.request.urlopen(req, timeout=120) as response, partial.open("wb") as output:
            for block in iter(lambda: response.read(CHUNK), b""):
                output.write(block); digest.update(block); total += len(block)
        partial.replace(target)
        records.append({"path": str(target.relative_to(ROOT)), "url": url, "revision": revision, "license_note": license_note, "bytes": total, "sha256": digest.hexdigest()})
    receipt = {"record": "G03-METADATA-001", "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files": records}
    (ROOT / "data" / "manifests").mkdir(parents=True, exist_ok=True)
    (ROOT / "data" / "manifests" / "g03-metadata-receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
