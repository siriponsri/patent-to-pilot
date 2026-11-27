"""Reproduce FIX2b count and audit packets from the pinned open inputs."""
import argparse
import csv
import json
import random
from collections import defaultdict
from datetime import date
from pathlib import Path

from fix2_audit import CUTOFF, DATA, TEST_FIRST, dump, pinned_inputs, sha256
from loe_bench.common import add_months, ingredient_key, read_jsonl
from loe_bench.dataset import (
    _final_originals, _original_products, build_entities, build_moiety_linkage,
)
from loe_bench.moiety import drug_product, fallback_name, orange_products, product_names, registry_for

SEED = 20261130


def read_csv(filename):
    with (DATA / filename).open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def count_rows(entities, data_end):
    counts = {}
    for year in range(1995, TEST_FIRST.year):
        cutoff = date(year, 1, 1)
        counts[cutoff] = sum(
            e.nda_first is not None and e.nda_first <= cutoff and e.flag_at("nme", cutoff)
            and (e.anda_first is None or e.anda_first > cutoff)
            for e in entities.values()
        )
    return dict(
        entities=len(entities),
        nme_2014=sum(e.nda_first is not None and e.nda_first <= CUTOFF and e.flag_at("nme", CUTOFF)
                     for e in entities.values()),
        rows={
            horizon: dict(
                all_development_cutoffs=sum(n for t, n in counts.items() if add_months(t, horizon) <= data_end),
                window_ends_before_seal=sum(n for t, n in counts.items()
                                           if add_months(t, horizon) < TEST_FIRST
                                           and add_months(t, horizon) <= data_end),
            )
            for horizon in (12, 24, 36)
        },
    )


def catalog(raw, registry, orange, linkage):
    by_app, by_key, by_term = defaultdict(list), defaultdict(list), defaultdict(set)
    legacy_apps = defaultdict(set)
    for source in ("df_nda.jsonl", "df_anda.jsonl"):
        for record in read_jsonl(raw / source):
            app = record["application_number"]
            approved = min((d for d, _ in _final_originals(record)), default=None)
            products = _original_products(record, approved)
            legacy_apps[ingredient_key(products)].add(app)
            for product in products:
                number = str(product.get("product_number") or "").zfill(3)
                ob = orange.get((app, number))
                listed = ob[0] if ob else None
                names = product_names(product)
                old = drug_product(registry, record, product, listed).key
                base = drug_product(registry, record, product, listed, reconcile_resin=True).key
                key = linkage.key(base)
                annotation = product.get("openfda") or record.get("openfda") or {}
                unii = annotation.get("unii") or []
                loc = dict(source=source, app=app, product=number, names=names,
                           label_names=annotation.get("substance_name") or [], unii=unii,
                           ob_names=product_names(listed) if listed else (),
                           brand=product.get("brand_name"), key=key, fix2_key=old, base_key=base)
                by_app[app].append(loc)
                if key:
                    by_key[key].append(loc)
                    terms = set(key.split("|"))
                    for name in names:
                        terms.add(fallback_name(name))
                        terms.update(registry.from_ids(registry.ids(name)))
                    for term in terms - {""}:
                        by_term[term].add(key)
    return by_app, by_key, by_term, legacy_apps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--gsrs", type=Path, required=True)
    parser.add_argument("--packet", type=Path, required=True)
    args = parser.parse_args()
    data_end, digests = pinned_inputs(args.raw_dir)
    registry = registry_for(args.raw_dir, args.gsrs)
    orange = orange_products(args.raw_dir)
    linkage = build_moiety_linkage(args.raw_dir, registry, orange)
    by_app, by_key, by_term, legacy_apps = catalog(args.raw_dir, registry, orange, linkage)
    t7 = read_csv("T7_ingredient_audit.csv")
    design = read_csv("FIX2_design_audit.csv")
    prior = read_csv("FIX2_fresh_audit.csv")

    exposed_apps = set()
    for row in t7:
        exposed_apps.update(legacy_apps[row["key"]])
        exposed_apps.update(json.loads(row["application_numbers"]) + json.loads(row["anchors"]))
    for row in design + prior:
        exposed_apps.update(loc["application_number"] for loc in json.loads(row["locators"]))
    for row in prior:
        exposed_apps.update(json.loads(row["member_applications"]))
    exposed_keys = {loc["key"] for app in exposed_apps for loc in by_app[app]}
    variants = {name: build_entities(args.raw_dir, key_mode=mode, gsrs_path=args.gsrs)
                for name, mode in (("legacy", "legacy"), ("fix2", "fix2"), ("fix2b", "moiety"))}
    eligible = {key for key, entity in variants["fix2b"].items()
                if entity.nda_first is not None and entity.nda_first <= CUTOFF}
    frame = sorted(eligible - exposed_keys)
    sample = random.Random(SEED).sample(frame, 60)

    def fresh_packet(key):
        terms = set(key.split("|"))
        for loc in by_key[key]:
            for name in loc["names"]:
                terms.add(fallback_name(name))
                terms.update(registry.from_ids(registry.ids(name)))
        neighbors = set().union(*(by_term[term] for term in terms - {""})) - {key}
        return dict(key=key, first_nda=variants["fix2b"][key].nda_first,
                    members=by_key[key], candidates={k: by_key[k] for k in sorted(neighbors)})

    def prior_packet(row, key_field):
        locators = json.loads(row["locators"])
        anchors = {loc["application_number"] for loc in locators}
        if key_field == "key":
            anchors.update(json.loads(row["member_applications"]))
        return dict(key=row[key_field], previous=row, anchors=[p for app in sorted(anchors) for p in by_app[app]])

    dump(args.packet, dict(
        fresh=[fresh_packet(key) for key in sample],
        t7=[prior_packet(row, "t7_key") for row in design],
        fix2=[prior_packet(row, "key") for row in prior],
    ))
    dump(DATA / "FIX2b_conflicts.json", linkage.conflicts)
    dump(DATA / "FIX2b_counts.json", dict(
        input_sha256=digests, gsrs_sha256=sha256(args.gsrs),
        counts={name: count_rows(table, data_end) for name, table in variants.items()},
        fresh_seed=SEED, eligible=len(eligible), excluded=len(eligible & exposed_keys),
        fresh_frame=len(frame), fresh_draw=sample,
        canonical_alias_count=len(linkage.canonical), conflict_count=len(linkage.conflicts),
    ))


if __name__ == "__main__":
    main()
