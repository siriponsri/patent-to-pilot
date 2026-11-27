"""Matched on-page extract selectors for the D31 page-2 follow-up."""
from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from itertools import combinations
from pathlib import Path
from time import perf_counter, process_time

from ocs_correspondence import ROOT, Document, grams, normal, run_query, verified

LOCK = ROOT / "docs/ra-pharma/research/official-correspondence/page2/freeze.json"
ARMS = ("issue_conditioned", "lexical_diversity", "d31_fixed")
WINDOW_CAP = 128
QUALIFICATION = (
    "เว้นแต่", "เฉพาะกรณี", "ทั้งนี้", "ภายใต้", "ในกรณีที่",
    "หาก", "ถ้า", "แต่ต้อง", "โดยมีเงื่อนไข",
)


@dataclass(frozen=True)
class Window:
    page: int
    start: int
    end: int
    tokens: frozenset[str]
    conclusion: bool
    qualification: bool

    def locator(self):
        return self.page, self.start

    def as_span(self, pages):
        return {"page": self.page, "start": self.start, "end": self.end,
                "quote": pages[self.page - 1][self.start:self.end]}


def compatible(left, right):
    return left.page != right.page or max(left.start, right.start) >= min(left.end, right.end)


def select_pair(query, windows, role_bonus):
    if not query:
        return (), 0
    relevance = {window: Fraction(len(query & window.tokens), len(query)) for window in windows}
    ranked = sorted((w for w in windows if relevance[w] > 0), key=Window.locator)
    options = ((w,) for w in ranked)
    pairs = (pair for pair in combinations(ranked, 2) if compatible(*pair))
    best = None
    option_count = 0

    def value(option):
        first = option[0]
        if len(option) == 1:
            return 2 * relevance[first] + role_bonus * max(first.conclusion, first.qualification)
        second = option[1]
        merged = first.tokens | second.tokens
        coverage = Fraction(len(query & merged), len(query))
        redundancy = Fraction(len(first.tokens & second.tokens), len(merged))
        roles = max(first.conclusion + second.qualification, second.conclusion + first.qualification)
        return relevance[first] + relevance[second] + coverage - redundancy / 4 + role_bonus * roles

    for candidates in (options, pairs):
        for option in candidates:
            option_count += 1
            rank = (-value(option), len(option), tuple(w.locator() for w in option))
            if best is None or rank < best[0]:
                best = (rank, option)
    return (() if best is None else best[1]), option_count


def compare(query, documents, fixed):
    """Keep the exact verification and opened-page actions from one fixed trace."""
    identity = fixed.get("identity")
    source = documents.get(identity["source"]) if identity else None
    window_descriptors = []
    if source:
        for action in fixed["actions"]:
            if action["source"] == source.doc_id:
                page = action["page"]
                window_descriptors.extend((page, *w) for w in source.windows.get(page, ()))

    common = len(window_descriptors)
    if common > WINDOW_CAP:
        status = {**fixed, "status": "unresolved-window-cap", "spans": [], "windows_ranked": common,
                  "options_evaluated": 0, "window_cap_stop": True}
        return {name: status for name in ARMS}
    unchanged = {**fixed, "options_evaluated": 0, "window_cap_stop": False}
    if not window_descriptors:
        return {name: unchanged for name in ARMS}

    windows = []
    for page, start, end, tokens, cues in window_descriptors:
        quote = source.pages[page - 1][start:end]
        windows.append(Window(page, start, end, frozenset(tokens), bool(cues),
                              any(cue in quote for cue in QUALIFICATION)))
    query_grams = grams(normal(query["question"]))
    results = {"d31_fixed": unchanged}
    for name, bonus in (("issue_conditioned", Fraction(1, 5)), ("lexical_diversity", Fraction(0))):
        spans, evaluated = select_pair(query_grams, windows, bonus)
        results[name] = {
            **fixed, "status": "issued" if spans else "unresolved-response",
            "spans": [w.as_span(source.pages) for w in spans], "windows_ranked": common,
            "options_evaluated": evaluated, "window_cap_stop": False,
        }
    return results


def read_queries(blob):
    queries = json.loads(blob)
    fields = {"id", "agency", "reference", "question"}
    if (not isinstance(queries, list) or not queries or any(
        not isinstance(q, dict) or set(q) != fields or not all(isinstance(q[k], str) for k in fields)
        or not q["question"].strip() for q in queries
    ) or len({q["id"] for q in queries}) != len(queries)):
        raise ValueError("invalid query rows or repeated query ID")
    return queries


def locked_pages(lock):
    import pymupdf

    root = Path(lock["source_directory"])
    sources = json.loads(verified(root / "runtime-corpus.json", lock["corpus_sha256"]))
    pinned = json.loads(verified(root / "canonical-pages.json", lock["canonical_sha256"]))
    allowed = set(lock["source_ids"])
    if not allowed <= {s["id"] for s in sources} or len(allowed) < 3:
        raise ValueError("admitted family roster does not match corpus or minimum")
    pages = {}
    total_bytes = 0
    for source in sources:
        identifier = source["id"]
        if identifier not in allowed:
            continue
        blob = verified(root / source["file"], source["sha256"])
        with pymupdf.open(stream=blob, filetype="pdf") as pdf:
            if len(pdf) != source["pages"]:
                raise ValueError("PDF page count mismatch")
            pages[identifier] = [page.get_text("text", sort=True) for page in pdf]
        if pages[identifier] != pinned[identifier]:
            raise ValueError("PDF differs from canonical extraction")
        total_bytes += len(blob)
    return pages, total_bytes


def write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as target:
        json.dump(data, target, ensure_ascii=False, indent=2, sort_keys=True)
        target.write("\n")


def capture(lock, lock_sha):
    start, cpu = perf_counter(), process_time()
    pages, total_bytes = locked_pages(lock)
    documents = {name: Document.index(name, raw) for name, raw in sorted(pages.items())}
    indexing = {"wall_seconds": perf_counter() - start, "cpu_seconds": process_time() - cpu,
                "pdf_bytes": total_bytes, "pages": sum(map(len, pages.values())), "rendered_pages": 0}
    query_bytes = verified(Path(lock["queries"]["path"]), lock["queries"]["sha256"])
    queries = read_queries(query_bytes)
    start, cpu = perf_counter(), process_time()
    traces = {}
    for query in queries:
        fixed = run_query(query, list(documents.values()), "exact_conflict")
        traces[query["id"]] = compare(query, documents, fixed)
    result = {"lock_sha256": lock_sha, "traces": traces, "indexing": indexing, "query_bytes": len(query_bytes),
              "policy_wall_seconds": perf_counter() - start, "policy_cpu_seconds": process_time() - cpu}
    write_json(Path(lock["original"]), result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("released_freeze_sha256")
    parser.add_argument("released_commit")
    args = parser.parse_args()
    lock = json.loads(verified(LOCK, args.released_freeze_sha256))
    actual = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    if actual != args.released_commit:
        raise ValueError("checkout differs from the independent release")
    for path, sha in lock["implementation"].items():
        verified(ROOT / path, sha)
    if Path(lock["original"]).exists():
        raise ValueError("one-time original already exists")
    capture(lock, args.released_freeze_sha256)


if __name__ == "__main__":
    main()
