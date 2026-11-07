"""Stream a USPTO weekly grant full-text zip (ipgYYMMDD.zip) and write, per grant, its US patent citations with the
USPTO citation category ("cited by examiner", "cited by applicant", ...). No text is kept.

The weekly XML is a concatenation of documents, each starting with an XML declaration; documents are parsed one by
one with xml.etree (no DTD or external entity loading). Numbers are normalised to the Google Patents form
(US-<number>-<kind>; pre-grant publications drop the zero after the year: 20050205750 -> 2005205750).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile


def google_number(doc: str) -> str:
    """'2012/0323474' or '20120323474' -> '2012323474'; '07774896' -> '7774896'."""
    doc = doc.strip().replace("/", "")
    if len(doc) == 11 and doc.isdigit() and doc[:2] in ("19", "20") and doc[4] == "0":
        return doc[:4] + doc[5:]
    return doc.lstrip("0") if doc.isdigit() else doc


def grant_records(lines):
    buf: list[str] = []
    for line in lines:
        if line.startswith("<?xml") and buf:
            yield "".join(buf)
            buf = []
        buf.append(line)
    if buf:
        yield "".join(buf)


def parse_doc(text: str) -> dict | None:
    start = text.find("<us-patent-grant")
    if start < 0:
        return None
    root = ET.fromstring(text[start:])
    pub = root.find("us-bibliographic-data-grant/publication-reference/document-id")
    if pub is None:
        return None
    number, kind = pub.findtext("doc-number", ""), pub.findtext("kind", "")
    cites = []
    for cit in root.iterfind("us-bibliographic-data-grant/us-references-cited/us-citation"):
        pat = cit.find("patcit/document-id")
        if pat is None or pat.findtext("country", "") != "US":
            continue
        cites.append({"number": google_number(pat.findtext("doc-number", "")), "kind": pat.findtext("kind", ""),
                      "category": (cit.findtext("category") or "").strip()})
    return {"publication_number": f"US-{google_number(number)}-{kind}", "us_citations": cites}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists")
    grants = parsed = 0
    with zipfile.ZipFile(args.zip) as z, args.output.open("w", encoding="utf-8") as out:
        name = z.namelist()[0]
        with z.open(name) as raw:
            for doc in grant_records(io.TextIOWrapper(raw, encoding="utf-8", errors="replace")):
                grants += 1
                record = parse_doc(doc)
                if record:
                    parsed += 1
                    out.write(json.dumps(record) + "\n")
    print(json.dumps({"documents": grants, "grants_parsed": parsed,
                      "zip_sha256": hashlib.sha256(args.zip.read_bytes()).hexdigest(),
                      "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
