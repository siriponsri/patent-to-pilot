"""Build the deterministic RunPod pilot sample from a USPTO weekly grant full-text file.

Source: USPTO bulk grant XML (public domain), ``ipg180102.zip`` = grants issued 2 January 2018,
downloaded by the owner (sha256 a8dca2bb...7d35, see audits/ptp-medtech-tm-bigquery-20261107).

Why not PatentsView ``g_patent``: its columns are patent_id/type/date/title/wipo_kind/num_claims/
withdrawn/filename only; there is no abstract or claim text in any downloaded PatentsView table.
The weekly grant XML carries title, abstract and claims, so the pilot uses the full TAC construction
(the same as DAPFAM) instead of a TA-only proxy.

Declared rule (fixed before the run):
- keep utility grants only (kind B1/B2) with non-empty title, abstract and claims;
- order by sha256(f"{SEED}:{patent_id}") ascending; take the first ``--n`` (cap 10,000);
- text = itertext of <invention-title>, <abstract>, and every <claim> in document order,
  whitespace-joined (normalization is applied later by the passage rule, not here).
Standard library only; runs on the remote host (python3.12, no extra packages).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

SEED = 20261116
DOC_START = re.compile(rb"<\?xml[^>]*\?>")
DOCTYPE = re.compile(rb"<!DOCTYPE[^>]*>")


def _text(node) -> str:
    return " ".join(" ".join(node.itertext()).split()) if node is not None else ""


def iter_documents(zip_path: Path):
    with zipfile.ZipFile(zip_path) as archive:
        (name,) = archive.namelist()
        raw = archive.read(name)
    starts = [m.start() for m in DOC_START.finditer(raw)] + [len(raw)]
    for begin, end in zip(starts, starts[1:]):
        chunk = DOCTYPE.sub(b"", raw[begin:end])
        # Drop the XML declaration so ElementTree accepts the bytes; entities are numeric only.
        chunk = DOC_START.sub(b"", chunk, count=1)
        yield chunk


def parse(chunk: bytes):
    try:
        root = ET.fromstring(chunk)
    except ET.ParseError:
        return None, "parse_error"
    if root.tag != "us-patent-grant":
        return None, "not_grant:" + root.tag
    pub = root.find("us-bibliographic-data-grant/publication-reference/document-id")
    if pub is None:
        return None, "no_pubref"
    number = (pub.findtext("doc-number") or "").strip()
    kind = (pub.findtext("kind") or "").strip()
    date = (pub.findtext("date") or "").strip()
    if kind not in {"B1", "B2"}:
        return None, "kind:" + (kind or "none")
    title = _text(root.find("us-bibliographic-data-grant/invention-title"))
    abstract = _text(root.find("abstract"))
    claims = " ".join(_text(c) for c in root.findall("claims/claim"))
    if not (title and abstract and claims):
        return None, "missing_text"
    patent_id = number.lstrip("0")
    return {"doc_id": f"US{patent_id}{kind}", "patent_id": patent_id, "kind": kind, "date": date,
            "title": title, "abstract": abstract, "claims": claims}, "ok"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--n", type=int, default=10000)
    args = parser.parse_args()
    started = time.time()
    cpu0 = time.process_time()
    out = args.out_dir / "sample.jsonl"
    if out.exists():
        print("refusing to overwrite", out, file=sys.stderr)
        return 2
    counts: dict[str, int] = {}
    records = []
    for chunk in iter_documents(args.source):
        record, reason = parse(chunk)
        counts[reason] = counts.get(reason, 0) + 1
        if record:
            record["order_key"] = hashlib.sha256(f"{SEED}:{record['patent_id']}".encode()).hexdigest()
            records.append(record)
    records.sort(key=lambda r: r["order_key"])
    selected = records[:args.n]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as handle:
        for rank, record in enumerate(selected):
            record["rank"] = rank
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    receipt = {
        "source": str(args.source), "source_sha256": sha256_file(args.source),
        "rule": "utility B1/B2 with title+abstract+claims; sha256(f'{seed}:{patent_id}') ascending; first n",
        "seed": SEED, "n_requested": args.n, "n_eligible": len(records), "n_selected": len(selected),
        "parse_counts": counts, "sample_sha256": sha256_file(out), "sample_bytes": out.stat().st_size,
        "text_fields": "title + abstract + claims (TAC, same fields as DAPFAM)",
        "wall_seconds": round(time.time() - started, 3), "cpu_seconds": round(time.process_time() - cpu0, 3),
    }
    (args.out_dir / "sample-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    (args.out_dir / "sample.jsonl.sha256").write_text(f"{receipt['sample_sha256']}  sample.jsonl\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
