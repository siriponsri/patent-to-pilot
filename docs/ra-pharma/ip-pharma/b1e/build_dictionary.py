"""Build the private exact-alias dictionary from pinned public reference releases."""
import csv
import hashlib
import io
import json
import sys
from collections import defaultdict
from pathlib import Path
from zipfile import ZipFile

from selector import norm


def records(stream):
    decoder = json.JSONDecoder()
    buf = ""
    for line in stream:
        if line.rstrip() == '  "results": [':
            break
    else:
        raise ValueError("Missing top-level results array")
    while True:
        buf = buf.lstrip()
        if buf.startswith("]"):
            return
        if buf.startswith(","):
            buf = buf[1:].lstrip()
        try:
            row, end = decoder.raw_decode(buf)
        except json.JSONDecodeError:
            block = stream.read(262144)
            if not block:
                raise ValueError("Truncated substance export")
            buf += block
            continue
        yield row
        buf = buf[end:]


def tsv(path, prefix):
    with ZipFile(path) as z:
        member, = (name for name in z.namelist() if name.startswith(prefix))
        with z.open(member) as f:
            yield from csv.DictReader(io.TextIOWrapper(f, encoding="utf-8-sig"), delimiter="\t")


def build(root):
    ids = set()
    keys = set()
    for path in sorted(root.glob("chembl-page-*.json")):
        page = json.loads(path.read_bytes())
        for r in page["molecules"]:
            assert r["molecule_type"] == "Small molecule"
            ids.add(r["molecule_chembl_id"])
            key = (r.get("molecule_structures") or {}).get("standard_inchi_key")
            if key:
                keys.add(key)
    assert len(ids) == 3475
    small = {r["UNII"] for r in tsv(root/"UNII_Data_20260804.zip","UNII_Records")
             if r["INCHIKEY"] in keys}
    links = defaultdict(set)
    count = 0
    with ZipFile(root/"gsrs-ranged.zip") as z:
        member, = z.namelist()
        with z.open(member) as f:
            for r in records(io.TextIOWrapper(f, encoding="utf8")):
                count += 1
                if r.get("unii"):
                    for rel in r.get("relationships", []):
                        if rel.get("type") == "ACTIVE MOIETY":
                            links[r["unii"]].add(rel.get("related_substance", {}).get("unii") or "")
    assert count == 167385
    aliases = {}
    def register(name, unii):
        term = norm(name)
        if term:
            previous = aliases.setdefault(term, unii)
            if previous != unii:
                aliases[term] = None

    for r in tsv(root/"UNIIs_20260804.zip","UNII_Names"):
        if r["TYPE"].lower() in {"of","cn","sys"}:
            register(r["NAME"], r["UNII"])
        register(r["DISPLAY_NAME"], r["UNII"])
    # Preserve all possible seed entities for exclusions even when identity is ambiguous.
    seed_names = {"APIXABAN", "RIVAROXABAN", "SITAGLIPTIN PHOSPHATE", "SITAGLIPTIN",
                  "OMEPRAZOLE", "METFORMIN HYDROCHLORIDE", "METFORMIN", "EMPAGLIFLOZIN",
                  "MIRDAMETINIB", "TIRATRICOL", "LAMOTRIGINE HEMIFUMARATE", "LAMOTRIGINE"}
    def names():
        return tsv(root/"UNIIs_20260804.zip", "UNII_Names")
    seeds = {r["UNII"] for r in names()
             if norm(r["NAME"]) in seed_names or norm(r["DISPLAY_NAME"]) in seed_names}
    parents = seeds.union(*(links.get(seed, set()) for seed in seeds)) - {""}
    related = parents | {u for u, targets in links.items() if parents & targets}
    denied = set(seed_names)
    for r in names():
        if r["UNII"] in related:
            denied.update([norm(r["NAME"]), norm(r["DISPLAY_NAME"])])
    (root/"exposure-aliases.json").write_bytes(json.dumps(sorted(denied - {""})).encode())
    result = {}
    for name, candidate in aliases.items():
        if candidate is None:
            continue
        parents = links.get(candidate, set())
        if len(parents) == 1 and parents <= small:
            result[name] = next(iter(parents))
    if not result:
        raise ValueError("No verified mappings")
    path = root/"moiety.json"
    path.write_bytes(json.dumps(result, sort_keys=True, ensure_ascii=True).encode())
    print("Mapped aliases", len(result), "distinct moieties", len(set(result.values())),
          "SHA-256", hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    build(Path(sys.argv[1]))
