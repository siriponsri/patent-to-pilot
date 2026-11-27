"""Fetch public FDA records from openFDA into JSONL files with a provenance manifest.

Verified on 2026-11-27 from the sandbox (HTTP 200): /drug/orangebook.json, /drug/drugsfda.json.
openFDA limits (unverified here, per openFDA docs): skip <= 25000 per query, limit <= 1000,
and a per-IP request quota without an API key. Partitions below keep every query under skip 25000.

Usage:
  python -m loe_bench.openfda_fetch --out data/raw --which orangebook drugsfda
Set OPENFDA_API_KEY to use a key (optional).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Dict, Iterator, List

BASE = "https://api.fda.gov/drug/"

# Partition queries (each result set < 25,000 records as of 2026-11-26/27).
ORANGEBOOK_PARTS: Dict[str, str] = {
    "ob_nda": "products.application_type:N",
    "ob_anda_pre1982": "products.application_type:A+AND+approved_prior_to_1982:true",
    "ob_anda_to2009": "products.application_type:A+AND+approval_date:[19000101+TO+20091231]",
    "ob_anda_2010s": "products.application_type:A+AND+approval_date:[20100101+TO+20191231]",
    "ob_anda_2020plus": "products.application_type:A+AND+approval_date:[20200101+TO+20991231]",
}
DRUGSFDA_PARTS: Dict[str, str] = {
    "df_nda": "application_number:NDA*",
    "df_anda": "application_number:ANDA*",
    "df_bla": "application_number:BLA*",
}


def _get(url: str, retries: int = 3, pause: float = 1.5) -> dict:
    last = None
    for k in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "loe-bench/0.1 (research)"})
            with urllib.request.urlopen(req, timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:  # openFDA uses 404 for "no matches"
                return {"results": [], "meta": {"results": {"total": 0}}}
            last = e
        except Exception as e:  # network hiccup
            last = e
        time.sleep(pause * (k + 1))
    raise RuntimeError(f"GET failed after {retries} tries: {url}: {last}")


def iter_records(endpoint: str, search: str, page: int = 1000, max_skip: int = 25000,
                 sleep: float = 0.35) -> Iterator[dict]:
    key = os.environ.get("OPENFDA_API_KEY")
    skip = 0
    total = None
    while True:
        url = f"{BASE}{endpoint}.json?search={search}&limit={page}&skip={skip}"
        if key:
            url += f"&api_key={key}"
        d = _get(url)
        if total is None:
            total = d.get("meta", {}).get("results", {}).get("total", 0)
            if total > max_skip + page:
                raise RuntimeError(f"partition too large ({total}); split the query: {search}")
        res = d.get("results", [])
        for r in res:
            yield r
        skip += page
        if not res or skip >= total:
            return
        time.sleep(sleep)


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def fetch(which: List[str], out_dir: str) -> dict:
    os.makedirs(out_dir, exist_ok=True)
    manifest = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(), "files": []}
    plan = []
    if "orangebook" in which:
        plan += [("orangebook", n, q) for n, q in ORANGEBOOK_PARTS.items()]
    if "drugsfda" in which:
        plan += [("drugsfda", n, q) for n, q in DRUGSFDA_PARTS.items()]
    for endpoint, name, q in plan:
        path = os.path.join(out_dir, f"{name}.jsonl")
        n = 0
        with open(path, "w", encoding="utf-8") as f:
            for rec in iter_records(endpoint, q):
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
        manifest["files"].append({"name": name, "endpoint": endpoint, "query": q, "records": n,
                                  "sha256": sha256_file(path)})
        print(f"{name}: {n} records")
    with open(os.path.join(out_dir, "MANIFEST.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    return manifest


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="data/raw")
    ap.add_argument("--which", nargs="+", default=["orangebook", "drugsfda"])
    a = ap.parse_args()
    fetch(a.which, a.out)
