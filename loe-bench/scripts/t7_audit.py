"""Generate a T7 review packet or reproduce the audit from recorded judgments."""
import argparse
from collections import Counter, defaultdict
import csv
from dataclasses import dataclass
from datetime import date
import hashlib
import json
from pathlib import Path
import random
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from loe_bench.common import SALT_WORDS, ingredient_key, norm_ingredient, read_jsonl
from loe_bench.dataset import _final_originals, _original_products, build_entities

CUTOFF = date(2014, 1, 1)
SEED = 20261128
QUOTAS = {
    "POSSIBLE_FALSE_MERGE": 25,
    "POSSIBLE_FALSE_SPLIT": 25,
    "COMBINATION": 20,
    "RANDOM": 30,
}
VERDICTS = ("CORRECT", "FALSE_MERGE", "FALSE_SPLIT", "UNRESOLVED")
FILES = ("df_nda.jsonl", "df_anda.jsonl")
AUDIT = "T7_ingredient_audit.csv"
OVERRIDES = "T7_ingredient_overrides_proposed.csv"
SUMMARY = "T7_summary.json"
SUFFIXES = SALT_WORDS | {
    "ACETONIDE", "BENZOATE", "DECANOATE", "DIPROPIONATE", "DIHYDROCHLORIDE",
    "DIMEGLUMINE", "DIOLAMINE", "DITOSYLATE", "ENANTHATE", "ESYLATE",
    "ESTOLATE", "HYDRATE", "ISETHIONATE", "MEGLUMINE", "MONOSODIUM", "NAPSYLATE",
    "PAMOATE", "PIVALATE", "PROPIONATE", "SESQUIHYDRATE", "TOSYLATE", "TRIHYDRATE", "VALERATE",
}


def normalized_substance(name):
    return " ".join(re.findall(r"[A-Z0-9]+", name.upper()))


def suffix_base(name):
    """Screen familiar suffix variation while preserving suffix-only names."""
    words = normalized_substance(name).split()
    end = len(words)
    while end > 1 and words[end - 1] in SUFFIXES:
        end -= 1
    if all(word in SUFFIXES for word in words[:end]):
        return " ".join(words)
    return " ".join(words[:end])


@dataclass
class Application:
    source: str
    number: str
    approved: date | None
    key: str
    products: tuple
    substances: tuple
    uniis: tuple
    generic_names: tuple

    @property
    def names(self):
        return {name for _, names, _, _ in self.products for name in names}


def load_applications(raw_dir):
    grouped = defaultdict(list)
    for source in FILES:
        for record in read_jsonl(raw_dir / source):
            approved = min((when for when, _ in _final_originals(record)), default=None)
            products = _original_products(record, approved)
            key = ingredient_key(products)
            if not key:
                continue
            openfda = record.get("openfda") or {}
            rows = tuple(sorted({
                (p.get("product_number") or "", tuple(sorted({
                    a["name"] for a in p.get("active_ingredients") or [] if a.get("name")
                })), p.get("route") or "", p.get("dosage_form") or "")
                for p in products
            }))
            grouped[key].append(Application(
                source, record["application_number"], approved, key, rows,
                tuple(sorted(set(openfda.get("substance_name") or []))),
                tuple(sorted(set(openfda.get("unii") or []))),
                tuple(sorted(set(openfda.get("generic_name") or []))),
            ))
    return grouped


def reverse_indexes(grouped):
    unii_keys = defaultdict(set)
    substance_keys = defaultdict(set)
    for key, apps in grouped.items():
        for app in apps:
            for unii in app.uniis:
                unii_keys[unii].add(key)
            for name in app.substances:
                substance_keys[normalized_substance(name)].add(key)
    return unii_keys, substance_keys


def flag_key(key, apps, indexes):
    unii_keys, substance_keys = indexes
    neighbors = set()
    substance_sets = set()
    product_sets = set()
    for app in apps:
        if app.substances:
            substance_sets.add(frozenset(map(suffix_base, app.substances)))
        for _, names, _, _ in app.products:
            if names:
                product_sets.add(frozenset(map(suffix_base, names)))
        for unii in app.uniis:
            neighbors.update(unii_keys[unii])
        for name in app.substances:
            neighbors.update(substance_keys[normalized_substance(name)])
    neighbors.discard(key)
    flags = []
    if len(substance_sets) > 1 or len(product_sets) > 1:
        flags.append("POSSIBLE_FALSE_MERGE")
    if neighbors:
        flags.append("POSSIBLE_FALSE_SPLIT")
    if any(len(names) > 1 for names in product_sets) or "|" in key:
        flags.append("COMBINATION")
    return flags, sorted(neighbors)


def sample_keys(entities, grouped):
    indexes = reverse_indexes(grouped)
    strata = {name: [] for name in QUOTAS}
    flags = {}
    for key, entity in sorted(entities.items()):
        if entity.nda_first is not None and entity.nda_first <= CUTOFF:
            flags[key] = flag_key(key, grouped[key], indexes)
            labels, _ = flags[key]
            strata[(labels or ["RANDOM"])[0]].append(key)

    rng = random.Random(SEED)
    selected = {}
    for stratum, quota in QUOTAS.items():
        if stratum == "RANDOM":
            quota = sum(QUOTAS.values()) - len(selected)
        for key in rng.sample(strata[stratum], min(quota, len(strata[stratum]))):
            selected[key] = stratum
    shortfall = sum(QUOTAS.values()) - len(selected)
    if shortfall:
        remaining = sorted(flags.keys() - selected.keys())
        for key in rng.sample(remaining, min(shortfall, len(remaining))):
            selected[key] = "RANDOM_FILL"
    return selected, {s: len(keys) for s, keys in strata.items()}, flags


def describe(app):
    return {
        "source": app.source,
        "application_number": app.number,
        "earliest_ORIG_AP_submission_status_date": app.approved.strftime("%Y%m%d") if app.approved else None,
        "products": [
            {"product_number": number, "active_ingredients.name": names,
             "route": route, "dosage_form": form}
            for number, names, route, form in app.products
        ],
        "openfda.substance_name": app.substances,
        "openfda.unii": app.uniis,
        "openfda.generic_name": app.generic_names,
    }


def compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def proposal_map(overrides):
    mapping = {}
    for row in overrides:
        raw, corrected = row["raw_ingredient"], row["corrected_key"]
        scope = (row.get("application_number", ""), raw)
        if scope in mapping or not corrected or not row["reason"] or not row["locator"]:
            raise ValueError(f"Duplicate or incomplete override for {raw!r}")
        mapping[scope] = corrected
    return mapping


def amended_key(app, mapping):
    if not any((app.number, name) in mapping or ("", name) in mapping for name in app.names):
        return app.key
    parts = set()
    for name in app.names:
        corrected = mapping.get((app.number, name), mapping.get(("", name), norm_ingredient(name)))
        parts.update(part for part in corrected.split("|") if part)
    return "|".join(sorted(parts))


def first_dates(grouped, overrides):
    mapping = proposal_map(overrides)
    seen = {(app.number, name) for apps in grouped.values() for app in apps for name in app.names}
    seen.update(("", name) for _, name in list(seen))
    if mapping.keys() - seen:
        raise ValueError("An override references a raw string absent from its application scope")
    dates = {}
    destinations = defaultdict(set)
    for apps in grouped.values():
        for app in apps:
            new = amended_key(app, mapping)
            destinations[app.key].add(new)
            if app.approved is not None:
                at = (new, app.source)
                dates[at] = min(dates.get(at, app.approved), app.approved)
    return dates, destinations


def date_impacts(rows, entities, grouped, overrides):
    dates, destinations = first_dates(grouped, overrides)
    result = dict(cases=0, evaluated=0, unavailable=0, first_nda_changed=0,
                  first_anda_changed=0, either_changed=0)
    for row in rows:
        if row["verdict"] not in {"FALSE_MERGE", "FALSE_SPLIT"}:
            continue
        result["cases"] += 1
        key = row["key"]
        targets = row["date_targets"]
        if not targets:
            result["unavailable"] += 1
            continue
        if set(targets) != destinations[key]:
            raise ValueError(f"Proposed targets do not follow the overrides for {key}")
        result["evaluated"] += 1
        entity = entities[key]
        nda = any(dates.get((target, FILES[0])) != entity.nda_first for target in targets)
        anda = any(dates.get((target, FILES[1])) != entity.anda_first for target in targets)
        result["first_nda_changed"] += nda
        result["first_anda_changed"] += anda
        result["either_changed"] += nda or anda
    return result


def counts_and_rates(rows):
    counts = Counter(row["verdict"] for row in rows)
    total = len(rows)
    resolved = total - counts["UNRESOLVED"]
    return {
        "sampled": total, "resolved": resolved,
        "counts": {v: counts[v] for v in VERDICTS},
        "sample_rates": {v: counts[v] / total if total else None for v in VERDICTS},
        "resolved_rates": {
            v: counts[v] / resolved if resolved else None for v in VERDICTS[:-1]
        },
    }


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def apply_reviews(selected, flags, grouped, reviews):
    apps_by_number = {app.number: app for apps in grouped.values() for app in apps}
    if len(reviews) != len(selected) or {row["key"] for row in reviews} != selected.keys():
        raise ValueError("Provide exactly one review for each sampled key")
    by_key = {row["key"]: row for row in reviews}
    rows = []
    for key, stratum in selected.items():
        review = by_key[key]
        anchors = [apps_by_number[number] for number in review["anchors"]]
        if (review["verdict"] not in VERDICTS or not review["note"].strip()
                or not any(app.key == key for app in anchors)):
            raise ValueError(f"Incomplete review for {key}")
        apps = grouped[key]
        labels, neighbors = flags[key]
        rows.append({
            "key": key, "stratum": stratum, "verdict": review["verdict"],
            "flags": compact(labels), "linked_keys": compact(neighbors),
            "raw_ingredients": compact(sorted({name for app in apps for name in app.names})),
            "application_numbers": compact(sorted({app.number for app in apps})),
            "routes_dosage_forms": compact(sorted({
                (route, form) for app in apps for _, _, route, form in app.products
            })),
            "substance_name_sets": compact(sorted({app.substances for app in apps if app.substances})),
            "unii_sets": compact(sorted({app.uniis for app in apps if app.uniis})),
            "anchors": compact(review["anchors"]),
            "locator": compact([describe(app) for app in anchors]),
            "supplemental_locator": review.get("supplemental_locator", ""),
            "note": review["note"], "date_targets": review.get("date_targets", []),
        })
    return rows


def verified_hashes(raw_dir, entries):
    expected = {row["raw_file"]: row["sha256"] for row in entries}
    hashes = {}
    for filename in FILES:
        with (raw_dir / filename).open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if expected.get(filename) != digest:
            raise ValueError(f"S0 hash mismatch for {filename}")
        hashes[filename] = digest
    return hashes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--packet", action="store_true", help="Print the sample and linked application evidence")
    mode.add_argument("--reviews-stdin", action="store_true", help="Load manual reviews and overrides as JSON")
    args = parser.parse_args()
    manifest_path = Path(__file__).resolve().parents[1] / "data" / "S0_INPUT_MANIFEST.json"
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    hashes = verified_hashes(args.raw_dir, manifest["files"])
    entities = build_entities(args.raw_dir)
    grouped = load_applications(args.raw_dir)
    selected, sizes, flags = sample_keys(entities, grouped)
    if args.packet:
        keys = set(selected)
        keys.update(neighbor for key in selected for neighbor in flags[key][1])
        packet = {
            "population_by_stratum": sizes, "sample": list(selected.items()),
            "flags": {key: flags[key] for key in selected},
            "evidence": {key: [describe(app) for app in grouped[key]] for key in sorted(keys)},
        }
        print(compact(packet))
        return
    if args.reviews_stdin:
        reviewed = json.load(sys.stdin)
        reviews, overrides = reviewed["reviews"], reviewed["overrides"]
    else:
        reviews = read_csv(args.output_dir / AUDIT)
        for review in reviews:
            for field in ("anchors", "date_targets"):
                review[field] = json.loads(review[field])
        overrides = read_csv(args.output_dir / OVERRIDES)

    rows = apply_reviews(selected, flags, grouped, reviews)
    summary = {
        "snapshot": manifest["t0"],
        "input_sha256": hashes,
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "first_nda_cutoff_inclusive": CUTOFF.isoformat(),
        "seed": SEED, "quotas": QUOTAS,
        "population": sum(sizes.values()), "population_by_stratum": sizes,
        "flag_population_counts": {
            flag: sum(flag in labels for labels, _ in flags.values()) for flag in tuple(QUOTAS)[:-1]
        },
        "overall": counts_and_rates(rows),
        "by_stratum": {
            stratum: counts_and_rates([row for row in rows if row["stratum"] == stratum])
            for stratum in (*QUOTAS, "RANDOM_FILL")
        },
        "date_impact_counts": date_impacts(rows, entities, grouped, overrides),
    }
    for row in rows:
        row["date_targets"] = compact(row["date_targets"])
    write_csv(args.output_dir / AUDIT, rows, list(rows[0]))
    write_csv(args.output_dir / OVERRIDES, overrides, ("raw_ingredient", "corrected_key", "application_number", "reason", "locator"))
    (args.output_dir / SUMMARY).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
