"""Local structural conformance check for one expressly opened EPO development source."""
import argparse
import json
import re
from collections import Counter
from hashlib import sha256
from pathlib import Path
from time import perf_counter, process_time
from xml.etree import ElementTree

SOURCE_ID = "EP2298134 A1"
EDITION = "2011-03-23"
SOURCE_HASH = "e03018f582e9f5dcbb936c38755c6f54250eef73661376d33d4fea420fd95f0b"
URL = "https://data.epo.org/publication-server/rest/v1.2/patents/EP2298134NWA1/document.xml"
TARGETS = (2, 3, 4)
PARENT_MENTION = re.compile(r"\bclaims?\b", re.IGNORECASE)
PARENT_CLAUSE = re.compile(
    r"\bas claimed in claims?\s+(\d+(?:\s+or\s+\d+)*)\s*(?=[,.;]|$)", re.IGNORECASE,
)


def parent_options(text, number):
    mentions = PARENT_MENTION.findall(text)
    if not mentions:
        return ()
    parents = PARENT_CLAUSE.findall(text)
    if len(mentions) != 1 or len(parents) != 1:
        return None
    options = tuple(int(raw) for raw in re.split(r"\s+or\s+", parents[0], flags=re.IGNORECASE))
    if len(options) != len(set(options)) or any(not 0 < parent < number for parent in options):
        return None
    return options


def import_claims(path):
    data = path.read_bytes()
    if sha256(data).hexdigest() != SOURCE_HASH:
        raise ValueError("development source hash mismatch")
    root = ElementTree.fromstring(data)
    identity = tuple(root.get(key) for key in ("country", "doc-number", "kind", "date-publ"))
    if identity != ("EP", "2298134", "A1", "20110323"):
        raise ValueError("development edition mismatch")
    claims = root.findall("./claims[@lang='en']/claim")
    index = {int(node.get("num")): node for node in claims}
    if set(index) != {1, 2, 3, 4} or len(claims) != len(index):
        raise ValueError("unsupported development claim inventory")
    return index


class VersionedClaims:
    def __init__(self, index, cap, unavailable=()):
        self.index = index
        self.cap = cap
        self.unavailable = set(unavailable)
        self.opened = {}
        self.events = []

    def status(self, number):
        if number in self.unavailable or number not in self.index:
            return "passage-unavailable"
        if len(self.opened) >= self.cap:
            return "read-cap"
        return "not-open"

    def open(self, number):
        if number in self.opened:
            return self.opened[number]
        if self.status(number) != "not-open":
            return None
        node = self.index[number]
        text = "".join(node.itertext()).strip()
        encoded = text.encode("utf-8")
        item = {
            "claim": number, "source_id": SOURCE_ID, "edition": EDITION,
            "issuer": "European Patent Office", "source_url": URL, "source_sha256": SOURCE_HASH,
            "locator": f'/ep-patent-document/claims[@lang="en"]/claim[@id="{node.get("id")}"]',
            "decoded_text_sha256": sha256(encoded).hexdigest(), "text": text,
            "parents": parent_options(text, number),
        }
        self.opened[number] = item
        self.events.append({"claim": number, "text_utf8_bytes": len(encoded)})
        return item


def paths(store, number, prefix=()):
    trail = (*prefix, number)
    record = store.opened.get(number)
    if record is None:
        return [{"claims": trail, "status": "missing", "request": {"claim": number,
                 "edition": EDITION, "source_id": SOURCE_ID, "reason": store.status(number)}}]
    options = record["parents"]
    if options is None:
        return [{"claims": trail, "status": "needs_review", "request": {"claim": number,
                 "edition": EDITION, "source_id": SOURCE_ID, "reason": "unresolved-dependency"}}]
    if not options:
        return [{"claims": trail, "status": "supported"}]
    return [row for parent in options for row in paths(store, parent, trail)]


def walk(store, number):
    item = store.open(number)
    if item and item["parents"]:
        for parent in item["parents"]:
            if parent not in store.opened:
                walk(store, parent)


def shared(store):
    for target in TARGETS:
        store.open(target)
    fanout = []
    while True:
        demand = Counter()
        for target in TARGETS:
            requested = {row["request"]["claim"] for row in paths(store, target)
                         if row["status"] == "missing" and row["request"]["reason"] == "not-open"}
            demand.update(requested)
        if not demand:
            return fanout
        number = min(demand, key=lambda candidate: (-demand[candidate], candidate))
        store.open(number)
        fanout.append({"claim": number, "requested_by_distinct_rows": demand[number]})


def packet(index, policy, cap, unavailable=()):
    store = VersionedClaims(index, cap, unavailable)
    fanout = []
    if policy == "cache_walk":
        for target in TARGETS:
            walk(store, target)
    elif policy == "shared":
        fanout = shared(store)
    elif policy == "offline":
        for number in sorted(index):
            store.open(number)
    else:
        raise ValueError(f"unknown policy: {policy}")
    return {
        "source_id": SOURCE_ID, "edition": EDITION, "source_sha256": SOURCE_HASH,
        "role": "claim_limitation", "target_order": TARGETS, "cap": cap,
        "rows": {target: paths(store, target) for target in TARGETS},
        "evidence": store.opened, "reads": store.events, "shared_requests": fanout,
    }


def capture(source, output):
    start, cpu = perf_counter(), process_time()
    claims = import_claims(source)
    indexing = {"wall_seconds": perf_counter() - start, "cpu_seconds": process_time() - cpu}
    start, cpu = perf_counter(), process_time()
    traces = {"full": {policy: packet(claims, policy, 4)
                       for policy in ("shared", "cache_walk", "offline")}}
    for name, cap, unavailable in (("cap_one", 1, ()), ("parent_missing", 4, (1,))):
        traces[name] = {policy: packet(claims, policy, cap, unavailable)
                        for policy in ("shared", "cache_walk")}
    content = {"indexing": indexing, "reading": {"wall_seconds": perf_counter() - start,
               "cpu_seconds": process_time() - cpu}, "traces": traces}
    with output.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(content, f, ensure_ascii=False, indent=2)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path, help="private output path for retained evidence text")
    args = parser.parse_args()
    capture(args.source, args.output)


if __name__ == "__main__":
    main()
