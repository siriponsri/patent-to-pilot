"""Build the Solution Scout public demo corpus from one HUPD year archive (CC BY-SA 4.0).

Streams a HUPD ``<year>.tar.gz`` and keeps, per application:
- the publication number (raw, plus canonical without the date suffix);
- title, abstract and the first claim;
- IPC3 codes from ``ipcr_labels``;
- publication date and decision.
Personal names (inventors, examiners) are dropped. Applications without a title, abstract or valid
IPC label are skipped. Sampling is stratified by the section of ``main_ipcr_label``, taking up to
``--per-section`` applications per section A–H, ordered by sha256(seed:application_number).
The output corpus.jsonl uses the dense runner's {id, title, abstract, claims} fields.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import tarfile

SEED = 20261106
IPC3 = re.compile(r"^[A-H][0-9]{2}")


def first_claim(claims: str | None, limit: int = 2000) -> str:
    text = " ".join((claims or "").split())
    match = re.search(r"\s2\s*\.\s", text)
    return (text[:match.start()] if match else text)[:limit]


def record(raw: dict) -> dict | None:
    title, abstract = (raw.get("title") or "").strip(), (raw.get("abstract") or "").strip()
    publication = (raw.get("publication_number") or "").split("-")[0]
    labels = raw.get("ipcr_labels") or []
    if isinstance(labels, str):  # some records hold a Python-style list as a string
        try:
            labels = json.loads(labels.replace("'", '"'))
        except json.JSONDecodeError:
            return None
    ipc3 = sorted({m.group(0) for label in labels if (m := IPC3.match(str(label)))})
    main = IPC3.match(str(raw.get("main_ipcr_label") or ""))
    if not title or not abstract or not publication or not ipc3 or main is None:
        return None
    return {"id": publication, "application_number": raw["application_number"], "title": title,
            "abstract": abstract, "claims": first_claim(raw.get("claims")), "ipc3": ipc3,
            "section": main.group(0)[0], "date_published": raw.get("date_published") or None,
            "decision": raw.get("decision") or None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--per-section", type=int, default=8000)
    args = parser.parse_args()

    kept: dict[str, list[tuple[str, dict]]] = {s: [] for s in "ABCDEFGH"}
    seen = Counter()
    with tarfile.open(args.archive, "r:gz") as archive:
        for member in archive:
            if not member.isfile() or not member.name.endswith(".json"):
                continue
            seen["files"] += 1
            row = record(json.load(archive.extractfile(member)))
            if row is None:
                seen["skipped"] += 1
                continue
            key = hashlib.sha256(f"{SEED}:{row['application_number']}".encode()).hexdigest()
            kept[row["section"]].append((key, row))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rows = [row for s in "ABCDEFGH" for _, row in sorted(kept[s])[:args.per_section]]
    ids = Counter(row["id"] for row in rows)
    rows = [row for row in rows if ids[row["id"]] == 1]
    corpus = args.output_dir / "corpus.jsonl"
    corpus.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    (args.output_dir / "family-ipc3.jsonl").write_text(
        "".join(json.dumps({"id": r["id"], "ipc3": r["ipc3"]}) + "\n" for r in rows), encoding="utf-8")
    manifest = {
        "format": "ptp-scout-hupd-subset-v1", "source": "HUPD/hupd (Hugging Face)", "licence": "CC BY-SA 4.0",
        "archive": args.archive.name, "archive_sha256": hashlib.sha256(args.archive.read_bytes()).hexdigest(),
        "seed": SEED, "per_section": args.per_section, "files_read": seen["files"], "skipped": seen["skipped"],
        "eligible_by_section": {s: len(v) for s, v in kept.items()},
        "kept_by_section": dict(Counter(r["section"] for r in rows)), "kept": len(rows),
        "dropped_duplicate_ids": sum(n for n in ids.values() if n > 1),
        "fields": ["id", "application_number", "title", "abstract", "claims (first claim)", "ipc3", "section",
                   "date_published", "decision"],
        "personal_names_dropped": True,
        "corpus_sha256": hashlib.sha256(corpus.read_bytes()).hexdigest(),
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
