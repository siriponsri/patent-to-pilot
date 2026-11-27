"""Reproduce the FIX2 count comparison and the frozen development audit packet."""
import argparse
import csv
import hashlib
import json
import random
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loe_bench.common import ingredient_key, read_jsonl
from loe_bench.dataset import _final_originals, _original_compositions, _original_products
from loe_bench.dataset import build_entities, build_samples
from loe_bench.moiety import fallback_name, orange_products, product_names, registry_for

DATA = ROOT / "data"
CUTOFF = date(2014, 1, 1)
TEST_FIRST = date(2017, 1, 1)
SEED = 20261129


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pinned_inputs(raw):
    manifest = json.loads((DATA / "S0_INPUT_MANIFEST.json").read_text(encoding="utf-8"))
    verified = {}
    for item in manifest["files"]:
        name = item["raw_file"]
        if name == "df_bla.jsonl":
            continue
        if sha256(raw / name) != item["sha256"]:
            raise ValueError(f"S0 digest mismatch: {name}")
        verified[name] = item["sha256"]
    return date.fromisoformat(manifest["t0"]), verified


def evidence(raw, registry):
    orange = orange_products(raw)
    by_app, by_key, by_screen = {}, defaultdict(set), defaultdict(set)
    for source in ("df_nda.jsonl", "df_anda.jsonl"):
        for rec in read_jsonl(raw / source):
            app = rec["application_number"]
            original = min((d for d, _ in _final_originals(rec)), default=None)
            products = _original_products(rec, original)
            if not products:
                continue
            groups = list(_original_compositions(rec, original, registry, orange))
            annotation = rec.get("openfda") or {}
            locators = []
            for product in products:
                number = product.get("product_number") or ""
                lookup = orange.get((app, number))
                locator = dict(product_number=number, names=product_names(product),
                               brand_name=product.get("brand_name"))
                if lookup:
                    p, when = lookup
                    locator["orange_book"] = dict(
                        application_type=p.get("application_type"), application_number=p.get("application_number"),
                        product_number=number, names=product_names(p), approval_date=when)
                locators.append(locator)
                for name in product_names(product):
                    by_screen[fallback_name(name)].add(app)
            for key, _, _ in groups:
                by_key[key].add(app)
            by_app[app] = dict(source=source, application_number=app, old_key=ingredient_key(products),
                               original=original, groups=groups, products=locators,
                               substance_names=annotation.get("substance_name", []),
                               unii=annotation.get("unii", []), generic_names=annotation.get("generic_name", []),
                               spl_set_ids=annotation.get("spl_set_id", []))
    return by_app, by_key, by_screen


def count_rows(entities, data_end):
    cutoffs = [date(year, 1, 1) for year in range(1995, TEST_FIRST.year)]
    return {
        "entity_count": len(entities),
        "nme_cohort_2014_01_01": sum(e.nda_first is not None and e.nda_first <= CUTOFF
                                     and e.flag_at("nme", CUTOFF) for e in entities.values()),
        "development_keys": sum(e.nda_first is not None and e.nda_first <= CUTOFF for e in entities.values()),
        "low_confidence_keys": sum(e.key_confidence == "LOW_CONFIDENCE" for e in entities.values()),
        "row_counts": {
            horizon: {"all_development_cutoffs": len(rows),
                      "window_ends_before_seal": sum(r["t_end"] < TEST_FIRST for r in rows)}
            for horizon in (12, 24, 36)
            for rows in [build_samples(entities, cutoffs, horizon, data_end)]
        },
    }


def dump(path, document):
    with path.open("w", encoding="utf-8", newline="\n") as out:
        json.dump(document, out, indent=2, ensure_ascii=False, default=str)
        out.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--gsrs", type=Path, required=True)
    parser.add_argument("--packet-dir", type=Path, required=True)
    args = parser.parse_args()
    data_end, digests = pinned_inputs(args.raw_dir)
    registry = registry_for(args.raw_dir, args.gsrs)
    legacy = build_entities(args.raw_dir, key_mode="legacy")
    moiety = build_entities(args.raw_dir, key_mode="fix2", gsrs_path=args.gsrs)
    by_app, by_key, by_screen = evidence(args.raw_dir, registry)
    with (DATA / "T7_ingredient_audit.csv").open(encoding="utf-8", newline="") as stream:
        design = list(csv.DictReader(stream))
    t7_apps = {app for row in design for app in json.loads(row["application_numbers"])}
    t7_old_keys = {row["key"] for row in design}
    t7_apps.update(app for app, rec in by_app.items() if rec["old_key"] in t7_old_keys)
    overlap = {key for app in t7_apps & by_app.keys() for key, _, _ in by_app[app]["groups"]}
    eligible = {key for key, e in moiety.items() if e.nda_first is not None and e.nda_first <= CUTOFF}
    frame = sorted(eligible - overlap)
    rng = random.Random(SEED)
    first_draw = rng.sample(frame, 60)
    anchor_apps = {app for row in design for app in json.loads(row["anchors"])}
    anchor_overlap = {key for app in anchor_apps & by_app.keys() for key, _, _ in by_app[app]["groups"]}
    excluded = set(first_draw) & anchor_overlap
    replacements = iter(rng.sample(sorted(set(frame) - set(first_draw) - anchor_overlap), len(excluded)))
    sample = [next(replacements) if key in excluded else key for key in first_draw]

    def packet(key):
        members = by_key[key]
        names = {fallback_name(n) for app in members for p in by_app[app]["products"] for n in p["names"]}
        candidates = set().union(*(by_screen[n] for n in names)) - members
        return dict(key=key, first_nda=moiety[key].nda_first, confidence=moiety[key].key_confidence,
                    members=[by_app[app] for app in sorted(members)],
                    candidates=[by_app[app] for app in sorted(candidates)])

    args.packet_dir.mkdir(parents=True, exist_ok=True)
    dump(args.packet_dir / "FIX2_fresh_packet.json", [packet(key) for key in sample])
    dump(args.packet_dir / "FIX2_design_packet.json", [
        dict(key=row["key"], verdict=row["verdict"], note=row["note"],
             anchors=[by_app[app] for app in json.loads(row["anchors"]) if app in by_app],
             members=[by_app[app] for app in json.loads(row["application_numbers"]) if app in by_app],
             related=[by_app[app] for app, rec in by_app.items()
                      if rec["old_key"] in linked])
        for row in design if row["verdict"] != "UNRESOLVED"
        for linked in [set(json.loads(row["linked_keys"]))]])
    counts = {"input_sha256": digests, "gsrs_sha256": sha256(args.gsrs),
              "legacy": count_rows(legacy, data_end), "moiety": count_rows(moiety, data_end),
              "fresh_seed": SEED, "fresh_frame": len(set(frame) - anchor_overlap),
              "excluded_overlap": len(eligible & (overlap | anchor_overlap)),
              "draw_replacements": {old: new for old, new in zip(first_draw, sample) if old != new},
              "fresh_draw": sample}
    dump(DATA / "FIX2_counts.json", counts)
    print(json.dumps({key: value for key, value in counts.items() if key != "fresh_draw"}, indent=2))


if __name__ == "__main__":
    main()
