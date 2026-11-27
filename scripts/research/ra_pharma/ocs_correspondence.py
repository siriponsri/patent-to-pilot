"""Label-blind bounded reading for the exposed D31 Thai correspondence pilot."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter, process_time

ROOT = Path(__file__).resolve().parents[3]
LOCK = ROOT / "docs/ra-pharma/research/official-correspondence/freeze.json"
ARMS = ("literal_lexical", "exact_conflict", "adaptive_page")
PAGE_CAP = 3
SPAN_CAP = 2
WIDTH = 360
DIGITS = str.maketrans("๐๑๒๓๔๕๖๗๘๙", "0123456789")
CASE_ID = re.compile(r"เรื่องเสร็จที่0*(\d{1,4})[/\-](25\d{2})")
RESPONSE = re.compile(r"(?:คณะกรรมการกฤษฎีกา|กรรมการร่างกฎหมาย).{0,140}?"
                      r"(?:ได้พิจารณา|พิจารณา|พิเคราะห์).{0,240}?"
                      r"(?:มีความเห็นว่า|เห็นว่า)")
DISPOSITION = ("ดังนั้น", "จึงเห็นว่า", "ไม่อาจ", "ย่อม", "จึงไม่", "วินิจฉัย")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verified(path, expected):
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"digest mismatch for {path.name}")
    return data


def normal(text):
    clean = unicodedata.normalize("NFKC", text).casefold().translate(DIGITS)
    return "".join(ch for ch in clean if not ch.isspace() and ch not in "\u200b\ufeff")


def grams(text):
    letters = "".join(ch for ch in text if ch.isalnum() or unicodedata.category(ch).startswith("M"))
    return {letters[i:i + 3] for i in range(len(letters) - 2)}


def binding(header, qry):
    agency, ref = normal(qry["agency"]), normal(qry["reference"])
    if not agency or not ref:
        return False
    matches = re.finditer(r"(?<![0-9])" + re.escape(ref) + r"(?![0-9])", header)
    return any(
        agency in header[max(0, m.start() - 455):m.end()]
        and "หนังสือ" in header[max(0, m.start() - 105):m.start()]
        for m in matches
    )


@dataclass
class Document:
    doc_id: str
    pages: tuple[str, ...]
    opinion: str | None
    header: str
    lexical: set[str]
    windows: dict[int, list[tuple[int, int, set[str], int]]]

    @classmethod
    def index(cls, doc_id, raw_pages):
        pages = tuple(normal(page) for page in raw_pages)
        combined = "".join(pages)
        marker = RESPONSE.search(combined)
        header_end = min(len(pages[0]), 2400, marker.start() if marker else 2400)
        header = pages[0][:header_end]
        case = CASE_ID.search(pages[0][:450])
        opinion = f"{int(case[1])}/{case[2]}" if case else None
        windows = {}
        if marker:
            preceding = 0
            close = combined.find("(ลงชื่อ)", marker.end())
            if close == -1:
                close = len(combined)
            for number, page in enumerate(pages, 1):
                start = max(0, marker.end() - preceding)
                stop = min(len(page), close - preceding)
                preceding += len(page)
                if stop - start < 22:
                    continue
                last = max(start, stop - WIDTH)
                offsets = sorted({*range(start, last + 1, 120), last})
                rows = []
                for offset in offsets:
                    end = min(offset + WIDTH, stop)
                    text = page[offset:end]
                    rows.append((offset, end, grams(text), sum(cue in text for cue in DISPOSITION)))
                windows[number] = rows
        return cls(doc_id, pages, opinion, header, grams(header), windows)


def choose_spans(opened, ranked):
    spans = []
    for value, page, start, text in sorted(ranked, key=lambda v: (-v[0], v[1], v[2])):
        if value <= 0 or page not in opened:
            continue
        end = start + len(text)
        if any(p["page"] == page and min(end, p["end"]) > max(start, p["start"]) for p in spans):
            continue
        spans.append({"page": page, "start": start, "end": end, "quote": text})
        if len(spans) == SPAN_CAP:
            break
    return spans


def run_query(qry, documents, policy):
    selected = None
    actions = []
    key_grams = grams(normal(qry["question"]))
    order = sorted(documents, key=lambda d: (-len(key_grams & d.lexical), d.doc_id))
    exact = [d for d in order if d.opinion and binding(d.header, qry)]
    conflict = len(exact) != 1

    if policy != "literal_lexical" and not conflict:
        selected = exact[0]
    else:
        candidates = order if policy == "literal_lexical" else exact or order
        for d in candidates[:min(2, PAGE_CAP)]:
            actions.append({"source": d.doc_id, "page": 1, "reason": "source-header"})
            if d.opinion and binding(d.header, qry):
                selected = d
                break
        # A checked page confirms a visible header, but cannot resolve duplicate exact headers.
        if policy != "literal_lexical" and len(exact) > 1:
            selected = None

    if selected is None:
        return {"status": "unresolved-header", "actions": actions, "spans": [], "windows_ranked": 0}

    opened = {a["page"] for a in actions if a["source"] == selected.doc_id}
    available = PAGE_CAP - len(actions)
    ranked = []
    cache = {}

    def rank_page(page):
        if page not in cache:
            cache[page] = [
                (len(key_grams & tokens) + cues, page, start, end)
                for start, end, tokens, cues in selected.windows[page]
            ]
        return cache[page]

    next_pages = [p for p in selected.windows if p not in opened]
    if policy == "adaptive_page" and len(next_pages) > available:
        next_pages.sort(key=lambda p: (-max(r[0] for r in rank_page(p)), p))
    for number in next_pages[:available]:
        actions.append({"source": selected.doc_id, "page": number, "reason": "issuer-response"})
        opened.add(number)
    for page in sorted(opened.intersection(selected.windows)):
        text = selected.pages[page - 1]
        ranked.extend((value, number, start, text[start:end])
                      for value, number, start, end in rank_page(page))
    spans = choose_spans(opened, ranked)
    identity = {"source": selected.doc_id, "opinion": selected.opinion,
                "agency": qry["agency"], "reference": qry["reference"],
                "header_page": 1, "header_verified_by": "page-view" if any(
                    a["reason"] == "source-header" and a["source"] == selected.doc_id for a in actions
                ) else "immutable-header-index"}
    return {"status": "issued" if spans else "unresolved-response", "actions": actions,
            "identity": identity, "spans": spans, "windows_ranked": sum(map(len, cache.values()))}


def capture(lock, original, lock_sha):
    import pymupdf

    corpus = Path(lock["source_directory"])
    start, cpu = perf_counter(), process_time()
    sources = json.loads(verified(corpus / "runtime-corpus.json", lock["corpus_sha256"]))
    pages = {}
    for source in sources:
        blob = verified(corpus / source["file"], source["sha256"])
        with pymupdf.open(stream=blob, filetype="pdf") as pdf:
            if len(pdf) != source["pages"]:
                raise ValueError("PDF page count mismatch")
            pages[source["id"]] = [page.get_text("text", sort=True) for page in pdf]
    canonical = json.loads(verified(corpus / "canonical-pages.json", lock["canonical_sha256"]))
    if pages != canonical:
        raise ValueError("extraction differs from pinned canonical pages")
    documents = [Document.index(doc_id, raw) for doc_id, raw in sorted(pages.items())]
    indexing = {"wall_seconds": perf_counter() - start, "cpu_seconds": process_time() - cpu,
                "pdf_bytes": sum(row["bytes"] for row in sources), "pages": sum(map(len, pages.values())),
                "rendered_pages": 0}
    query_bytes = verified(Path(lock["queries"]["path"]), lock["queries"]["sha256"])
    queries = json.loads(query_bytes)
    qfields = {"id", "agency", "reference", "question"}
    if (len({q["id"] for q in queries}) != len(queries) or
            any(set(q) != qfields or not all(isinstance(q[k], str) for k in qfields)
                or not q["question"].strip() for q in queries)):
        raise ValueError("query schema or duplicate ID")
    start, cpu = perf_counter(), process_time()
    traces = {q["id"]: {arm: run_query(q, documents, arm) for arm in ARMS} for q in queries}
    data = {"lock_sha256": lock_sha, "indexing": indexing, "query_bytes": len(query_bytes), "traces": traces,
            "policy_wall_seconds": perf_counter() - start, "policy_cpu_seconds": process_time() - cpu}
    with original.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(data, target, ensure_ascii=False, indent=2, sort_keys=True)
        target.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("released_freeze_sha256")
    parser.add_argument("released_commit")
    args = parser.parse_args()
    lock = json.loads(verified(LOCK, args.released_freeze_sha256))
    import subprocess
    actual = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if actual != args.released_commit:
        raise ValueError("checked-out revision differs from the independent release")
    for path, sha in lock["implementation"].items():
        verified(ROOT / path, sha)
    capture(lock, Path(lock["original"]), args.released_freeze_sha256)


if __name__ == "__main__":
    main()
