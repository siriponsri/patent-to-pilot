"""Run on local metadata only, after publication and validation of lock.json."""
import argparse
import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent


def norm(value):
    return " ".join(value.upper().split())


def table(path, name, delimiter):
    with ZipFile(path) as archive, archive.open(name) as raw:
        reader = csv.DictReader(io.TextIOWrapper(raw, encoding="latin1"),
                                delimiter=delimiter, quoting=csv.QUOTE_NONE)
        yield from reader


def classify(rows, info, dictionary, exclusions, forms):
    if len(rows) != 1 or len(info) != 1:
        return "CONFLICT_OR_MISSING_PRODUCT", ()
    (ingredient, dosage, strength, market, rld), = rows
    if market != "RX" or rld not in {"YES", "RLD"}:
        return "OUTSIDE_RX_RLD", ()
    parts = dosage.rsplit(";", 1)
    if len(parts) != 2 or parts[1].strip() != "ORAL" or parts[0].strip() not in forms:
        return "OUTSIDE_FORM_ROUTE", ()
    if not strength:
        return "UNKNOWN_STRENGTH", ()
    names = [norm(v) for v in ingredient.split(";")]
    if any(n in exclusions for n in names):
        return "KNOWN_INGREDIENT", ()
    values = [dictionary.get(n) for n in names]
    if any(v is None for v in values):
        return "UNKNOWN_MOIETY_OR_CLASS", ()
    return "ELIGIBLE", tuple(sorted(set(values)))


def original_date(records):
    if not records:
        return None
    try:
        dates = [(date.fromisoformat(d[:10]).isoformat(), int(n)) for d, n in records]
    except (ValueError, TypeError):
        return None
    first = min(d for d, _ in dates)
    ids = {n for d, n in dates if d == first}
    if len(ids) != 1 or len({d for d, n in dates if n in ids}) != 1:
        return None
    return first, ids.pop()


def prefix(rows):
    representatives = {}
    for r in sorted(rows, key=lambda r: (r["date"], int(r["nda"]), int(r["product"]))):
        representatives.setdefault((r["moieties"], r["nda"]), r)
    return len(representatives), list(representatives.values())[:24]


def run(root, lock):
    paths = {}
    for key, entry in lock["files"].items():
        path = root / entry["path"]
        with path.open("rb") as f:
            digest = hashlib.file_digest(f, "sha256").hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"Input hash mismatch for {key}")
        paths[key] = path
    dictionary = json.loads(paths["dictionary"].read_bytes())
    forms = set(lock["forms"])
    ndas = {r["ApplNo"] for r in table(paths["fda"], "Applications.txt", "\t")
            if norm(r["ApplType"]) == "NDA"}
    originals = defaultdict(set)
    for r in table(paths["fda"], "Submissions.txt", "\t"):
        if r["ApplNo"] in ndas and norm(r["SubmissionType"]) == "ORIG" and norm(r["SubmissionStatus"]) == "AP":
            originals[r["ApplNo"]].add((r["SubmissionStatusDate"], r["SubmissionNo"]))
    dates = {k: original_date(v) for k, v in originals.items()}
    frame = {k:v for k, v in dates.items() if v and "2020-01-01" <= v[0] <= "2024-12-31"}
    info = defaultdict(set)
    for r in table(paths["fda"], "Products.txt", "\t"):
        if r["ApplNo"] in frame:
            info[r["ApplNo"],r["ProductNo"]].add(tuple(norm(r[k]) for k in ("ActiveIngredient","Form","Strength")))
    products = defaultdict(set)
    grants = defaultdict(set)
    excluded_names = set(lock["excluded_names"])
    excluded_names.update(json.loads(paths["exposure_aliases"].read_bytes()))
    excluded_moieties = {dictionary[n] for n in excluded_names if n in dictionary}
    excluded_names.update(n for n,v in dictionary.items() if v in excluded_moieties)
    exposed_keys = set()
    for r in table(paths["orange"], "products.txt", "~"):
        if r["Appl_Type"].strip() != "N":
            continue
        key = (r["Appl_No"].strip(), r["Product_No"].strip())
        if key[0] in lock["excluded_ndas"] or any(norm(v) in excluded_names for v in r["Ingredient"].split(";")):
            exposed_keys.add(key)
        if key[0] in frame:
            products[key].add(tuple(norm(r[k]) for k in ("Ingredient","DF;Route","Strength","Type","RLD")))
    excluded_grants = set(lock["excluded_us_grants"])
    for r in table(paths["orange"], "patent.txt", "~"):
        if r["Appl_Type"].strip() != "N":
            continue
        key = (r["Appl_No"].strip(), r["Product_No"].strip())
        grant = r["Patent_No"].strip().removesuffix("*PED")
        if grant and key in exposed_keys:
            excluded_grants.add(grant)
        if grant and key in products:
            grants[key].add(grant)
    reasons = Counter()
    eligible = []
    for key, rows in products.items():
        nda, product = key
        reason, moieties = classify(rows, info[key], dictionary, excluded_names, forms)
        if key in exposed_keys or grants[key] & excluded_grants:
            reason = "KNOWN_OVERLAP"
        elif reason == "ELIGIBLE" and not grants[key]:
            reason = "NO_LISTED_GRANT"
        reasons[reason] += 1
        if reason == "ELIGIBLE":
            ingredient, dosage, strength, _, _ = next(iter(rows))
            eligible.append(dict(nda=nda,product=product,date=frame[nda][0],orig=frame[nda][1],
                                 ingredient=ingredient,dosage=dosage,strength=strength,moieties=moieties,
                                 grants=sorted(grants[key]), exposure="EXPOSURE_UNKNOWN"))
    groups, selected = prefix(eligible)
    return dict(original_nda_count=len(originals),unknown_original=sum(v is None for v in dates.values()),
                original_ndas_in_period=len(frame),orange_product_keys=len(products),
                fda_only_product_keys=len(set(info)-set(products)),product_dispositions=dict(sorted(reasons.items())),
                eligible_groups=groups, selected_groups=len(selected), prefix=selected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("private_root", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    config = json.loads((HERE / "lock.json").read_bytes())
    if hashlib.sha256(Path(__file__).read_bytes().replace(b"\r\n", b"\n")).hexdigest() != config["selector_sha256"]:
        raise ValueError("Selector revision mismatch")
    result = run(args.private_root, config)
    with args.output.open("x", encoding="utf8", newline="\n") as out:
        json.dump(result, out, indent=2)
        out.write("\n")
