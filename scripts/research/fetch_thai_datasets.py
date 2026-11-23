"""Fetch the owner-approved Thai datasets (decision D18) at pinned revisions.

Stdlib only for the download. Run with ``python -I`` from the repository root. Downloaded files are untrusted data:
nothing under the output directory is executed or imported. Row counts are read from parquet footers only (no labels).

Usage:
    python -I scripts/research/fetch_thai_datasets.py --out ../_private_artifacts/thai-data
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
import urllib.request

HF = "https://huggingface.co"

# Pinned per docs/tracking/owner-note-22112026/receipts/P3-T01_thai_data_contract.md and registry.json.
# role: HELD_OUT (test data, frozen-method evaluation only), CORPUS (retrieval corpus), DEV_TRAIN (train split),
#       QUERIES (evaluation queries, held out with their qrels), CARD (dataset card / git metadata).
ITEMS = [
    {
        "repo": "VISAI-AI/thai-gazette-evidence-retrieval",
        "revision": "87e695ee4951ff34932804431433ac55991ec374",
        "license": "CC-BY-4.0",
        "scoreboard": "thai_gazette_retrieval",
        "files": {
            "README.md": "CARD",
            ".gitattributes": "CARD",
            "corpus/corpus-00000-of-00001.parquet": "CORPUS",
            "queries/queries-00000-of-00001.parquet": "HELD_OUT",
            "default/test-00000-of-00001.parquet": "HELD_OUT",
        },
    },
    {
        "repo": "VISAI-AI/nitibench",
        "revision": "9f75697075e0f5691e3b821037b908c05f1821a7",
        "license": "MIT",
        "scoreboard": "nitibench_original",
        "files": {
            "README.md": "CARD",
            ".gitattributes": "CARD",
            "data/ccl-00000-of-00001.parquet": "HELD_OUT",
            "data/tax-00000-of-00001.parquet": "HELD_OUT",
            "data/nitibench-ccl.parquet": "HELD_OUT",
            "data/nitibench-tax.parquet": "HELD_OUT",
        },
    },
    {
        "repo": "VISAI-AI/nitibench-statute",
        "revision": "069e774f015a50e801dbe2055a29be580c54a83c",
        "license": "MIT",
        "scoreboard": "nitibench_original",
        "files": {
            "README.md": "CARD",
            ".gitattributes": "CARD",
            "data/ccl-00000-of-00001.parquet": "CORPUS",
        },
    },
    {
        "repo": "airesearch/WangchanX-Legal-ThaiCCL-RAG",
        "revision": "654e1a10afc44ecaee36fd739bc90078dcc62388",
        "license": "MIT",
        "scoreboard": "none (related training source)",
        "files": {
            "README.md": "CARD",
            ".gitattributes": "CARD",
            "data/train-00000-of-00001.parquet": "DEV_TRAIN",
        },
        "excluded": {"data/test-00000-of-00001.parquet": "test split not approved (D18: train only)"},
    },
]


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ptp-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def tree(repo: str, rev: str) -> dict[str, dict]:
    data = json.loads(_get(f"{HF}/api/datasets/{repo}/tree/{rev}?recursive=1"))
    if not isinstance(data, list):
        raise RuntimeError(f"tree listing failed for {repo}@{rev}: {data!r}")
    return {x["path"]: x for x in data if x.get("type") == "file"}


def parquet_rows(path: pathlib.Path) -> int | None:
    try:
        import pyarrow.parquet as pq  # footer metadata only
    except ImportError:
        return None
    return pq.ParquetFile(path).metadata.num_rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "decision": "D18 (docs/maintenance/OWNER-DECISIONS-20261122.md)",
        "contract": "docs/tracking/owner-note-22112026/receipts/P3-T01_thai_data_contract.md",
        "role_legend": {
            "HELD_OUT": "test/evaluation data: frozen-method held-out evaluation only; never for development or selection",
            "CORPUS": "retrieval corpus",
            "DEV_TRAIN": "train split: candidate development source",
            "CARD": "dataset card or git metadata",
        },
        "datasets": [],
    }
    ok = True
    for item in ITEMS:
        repo, rev = item["repo"], item["revision"]
        entry = {k: item[k] for k in ("repo", "revision", "license", "scoreboard")}
        entry["excluded"] = item.get("excluded", {})
        try:
            listing = tree(repo, rev)
        except Exception as exc:  # pinned revision must resolve; never fall back
            entry["status"] = f"STOPPED: pinned revision did not resolve ({exc})"
            manifest["datasets"].append(entry)
            ok = False
            print(entry["status"], file=sys.stderr)
            continue
        dest = out / f"{repo.split('/')[1]}@{rev[:8]}"
        if dest.exists() and any(dest.iterdir()):
            raise SystemExit(f"refusing to write into non-empty {dest}")
        dest.mkdir(parents=True, exist_ok=True)
        entry["local_dir"] = str(dest)
        files = []
        for rel, role in item["files"].items():
            meta = listing.get(rel)
            if meta is None:
                raise SystemExit(f"{repo}@{rev}: {rel} not in pinned tree")
            url = f"{HF}/datasets/{repo}/resolve/{rev}/{rel}"
            blob = _get(url)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(blob)
            sha = hashlib.sha256(blob).hexdigest()
            lfs = (meta.get("lfs") or {}).get("oid")
            size_ok = len(blob) == meta.get("size")
            hash_ok = (sha == lfs) if lfs else None
            rec = {
                "path": rel,
                "role": role,
                "size": len(blob),
                "sha256": sha,
                "hub_size": meta.get("size"),
                "hub_lfs_sha256": lfs,
                "size_match": size_ok,
                "lfs_sha256_match": hash_ok,
                "downloaded_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            }
            if rel.endswith(".parquet"):
                rec["num_rows"] = parquet_rows(target)
            if not size_ok or hash_ok is False:
                ok = False
            files.append(rec)
            print(f"{repo} {rel} {len(blob)} {sha[:12]} size_ok={size_ok} lfs_ok={hash_ok} rows={rec.get('num_rows')}")
        entry["files"] = files
        entry["status"] = "OK" if all(f["size_match"] and f["lfs_sha256_match"] is not False for f in files) else "MISMATCH"
        manifest["datasets"].append(entry)
    manifest["completed_utc"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
