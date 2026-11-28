"""Count descriptive Canadian events from public authority records."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import date, datetime
from hashlib import file_digest
import json
from pathlib import Path
import re
import sys
from zipfile import ZipFile

from bs4 import BeautifulSoup
from openpyxl import load_workbook
from openpyxl.utils.datetime import from_excel

LOE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOE_ROOT))
from loe_bench.common import read_jsonl
from loe_bench.dataset import _final_originals, build_entities
from loe_bench.moiety import GSRS_FILE, ORANGE_FILES, name_form, registry_for

YEARS = (2023, 2024, 2025)
PHARMA = {"Prescription Pharmaceutical", "Nonprescription Pharmaceutical"}
NAS = {"New Active Substance", "Priority-NAS"}
RAW_FILES = {"df_nda.jsonl", "df_anda.jsonl", *ORANGE_FILES}
CARD = LOE_ROOT / "data/JURIS-COUNT"
LOCAL_INPUTS = {
    "ca-noc-curl.zip", "ca-rid-curl.html", "ca-patent-complete.zip",
    *(f"ca-dpd-allfiles{suffix}.zip" for suffix in ("", "_ap", "_ia", "_dr")),
    *(f"jp-pmda-fy{year}.xlsx" for year in range(2022, 2026)),
    *(f"jp-nhi-r{era:02}.zip" for era in range(4, 8)),
}


def csv_member(archive, name):
    return csv.reader(archive.read(name).decode("utf-8-sig").splitlines())


def noc_date(raw):
    year, month, day = map(int, raw.split("-"))
    return date(1900 + year if year >= 94 else 2000 + year, month, day)


def verify_local_inputs(root):
    manifest = json.loads((CARD / "sources.json").read_text(encoding="utf-8"))
    source_rows = {r["file"]: r for r in manifest["public_sources"] if not r.get("error")}
    for name in sorted(LOCAL_INPUTS):
        with (root / name).open("rb") as source:
            if file_digest(source, "sha256").hexdigest() != source_rows[name]["sha256"]:
                raise ValueError(f"Authority source digest differs for {name}")


def us_comparator(path):
    manifest = json.loads((LOE_ROOT / "data/S0_INPUT_MANIFEST.json").read_text())
    for item in manifest["files"]:
        name = item["raw_file"]
        if name in RAW_FILES:
            with (path / name).open("rb") as source:
                if file_digest(source, "sha256").hexdigest() != item["sha256"]:
                    raise ValueError(f"Public S0 source digest differs for {name}")
    entities = build_entities(str(path))
    aliases = {alias: entity.key for entity in entities.values() for alias in entity.key_aliases}
    return entities, aliases, audited_us_singletons(path)


def audited_us_singletons(path):
    # Product-specific SPL active-moiety UNIIs resolve ambiguous GSRS text.
    # Require an exact complete singleton on both sides of the public FDA join.
    keys = {"POMALIDOMIDE": "U:D2UX06XLB5", "RIVAROXABAN": "U:9NDF7JZ4M3"}
    first = {"nda": defaultdict(list), "anda": defaultdict(list)}
    for kind in first:
        for record in read_jsonl(path / f"df_{kind}.jsonl"):
            names = {
                tuple(a.get("name") for a in product.get("active_ingredients") or [])
                for product in record.get("products") or []
            }
            if len(names) != 1:
                continue
            names = next(iter(names))
            if len(names) == 1 and names[0] in keys:
                for when, submission in _final_originals(record):
                    if kind == "anda" or submission.get("submission_class_code") == "TYPE 1":
                        first[kind][names[0]].append(when)
    results = {}
    for name, key in keys.items():
        origin = min(first["nda"][name])
        generic = min(first["anda"][name])
        if origin >= generic:
            raise ValueError(f"US singleton date order is invalid for {key}")
        results[key] = generic.isoformat()
    return results


def us_outcome(key, confident, entities, aliases, audited):
    if key in audited:
        return audited[key]
    if not confident:
        return "UNKNOWN"
    entity = entities.get(aliases.get(key, key))
    if entity is None or not entity.nme:
        return "NO_ELIGIBLE_US_NME_MATCH"
    if entity.key_confidence == "LOW_CONFIDENCE":
        return "UNKNOWN"
    first = entity.anda_first
    if first and entity.flag_at("nme", first) and entity.nda_first < first:
        return first.isoformat()
    return "NO_ELIGIBLE_US_EVENT_OBSERVED"


def audited_notices(root, registry):
    with ZipFile(root / "ca-noc-curl.zip") as archive:
        forms = defaultdict(set)
        dins = defaultdict(set)
        brands = defaultdict(set)
        for notice, product, ingredient, *_ in csv_member(archive, "noc_product_ingredient.txt"):
            forms[notice, product].add(ingredient)
        for notice, product, _, din in csv_member(archive, "noc_din_product.txt"):
            dins[notice, product].add(din)
        for notice, _, brand, *_ in csv_member(archive, "noc_brand.txt"):
            brands[notice].add(brand)
        notices = list(csv_member(archive, "noc_main.txt"))

    products = defaultdict(list)
    for (notice, product), ingredients in forms.items():
        composition = registry.composition(sorted(ingredients))
        products[notice].append((composition, sorted(ingredients), sorted(dins[notice, product])))
    for row in notices:
        if len(row) != 22:
            raise ValueError(f"NOC schema mismatch at {row[:2]}")
        notice, raw_date, sponsor, conditional, kind, _, supplement, category, _, scope = row[:10]
        reference = row[11].strip()
        when = noc_date(raw_date)
        for composition, names, product_dins in products.get(notice, [(None, [], [])]):
            yield {
                "date": when.isoformat(),
                "notice": notice,
                "key": composition.key if composition else "",
                "identity": "GSRS" if composition and not composition.low_confidence else "UNRESOLVED",
                "ingredients": names,
                "dins": product_dins,
                "brand": sorted(brands[notice]),
                "sponsor": sponsor,
                "reference": reference,
                "conditional": conditional,
                "type": kind.strip(),
                "supplement": supplement,
                "class": category,
                "scope": scope,
                "comment": row[20],
            }


def disposition(row):
    if row["scope"] not in PHARMA:
        return "outside_human_pharmaceutical"
    if row["supplement"] == "Y":
        return "supplement"
    if row["class"] in {"Administrative", "Labelling Only"}:
        return "administrative_or_labelling"
    if row["conditional"] == "Y":
        return "conditional"
    if row["comment"].strip():
        return "administrative_comment_review"
    if not row["key"]:
        return "ingredient_missing"
    return "original"


def rid_records(root, registry, aliases):
    soup = BeautifulSoup((root / "ca-rid-curl.html").read_bytes(), "html.parser")
    by_key = defaultdict(list)
    for table in soup.find_all("table"):
        for tr in table.select("tr"):
            cells = [cell.get_text(" ", strip=True) for cell in tr.find_all("td")]
            if len(cells) < 8 or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", cells[5]):
                continue
            ingredient = re.split(r"\s+\(supplied as ", cells[0], flags=re.I)[0]
            name = registry.composition([ingredient])
            if name.key:
                key = aliases.get(name.key, name.key)
                by_key[key].append(dict(submission=cells[1], brand=cells[2],
                                        noc=cells[5], no_file=cells[6], ends=cells[-1]))
    return by_key


def canonical_rows(rows, aliases):
    by_key = defaultdict(list)
    for row in rows:
        row["key"] = aliases.get(row["key"], row["key"])
        by_key[row["key"]].append(row)
    return by_key


def dpd_dins(root):
    dins = set()
    for suffix in ("", "_ap", "_ia", "_dr"):
        with ZipFile(root / f"ca-dpd-allfiles{suffix}.zip") as archive:
            dins.update(row[3] for row in csv_member(archive, f"drug{suffix}.txt") if row[2] == "Human")
    return dins


def patent_records(root):
    with ZipFile(root / "ca-patent-complete.zip") as archive:
        drug_dins = {row[0]: row[8] for row in csv_member(archive, "drugs_e.txt")
                     if row[5] == "Human" and row[8]}
        service = {(row[0], row[1]): (row[2], row[6])
                   for row in csv_member(archive, "patent-service_e.txt") if row[2].isdigit()}
        dated = defaultdict(list)
        for row in csv_member(archive, "submission-certif_e.txt"):
            link = row[1], row[2]
            if link not in service or row[1] not in drug_dins or not row[9]:
                continue
            number, expiry = service[link]
            dated[drug_dins[row[1]]].append(dict(
                patent=number, form=row[2], first_added=patent_date(row[9]),
                expiry=patent_date(expiry), amended=patent_date(row[24]),
                removed=patent_date(row[27]),
            ))
    return dated


def patent_date(value):
    return datetime.strptime(value, "%m/%d/%Y").date().isoformat() if value.strip() else ""


def screen(root, registry, entities, aliases, audited):
    rows = list(audited_notices(root, registry))
    initial = [row for row in rows if disposition(row) == "original"]
    nas = canonical_rows(
        [r for r in initial if r["type"] == "New Drug Submission" and r["class"] in NAS], aliases
    )
    generic = canonical_rows([r for r in initial if r["type"] == "Abbreviated New Drug"], aliases)
    rid = rid_records(root, registry, aliases)
    dpd = dpd_dins(root)
    patents = patent_records(root)

    candidates, checked = [], Counter()
    for key, group in generic.items():
        first = min(row["date"] for row in group)
        if int(first[:4]) not in YEARS:
            continue
        first_rows = [row for row in group if row["date"] == first]
        origin = min((row["date"] for row in nas.get(key, [])), default="")
        origin_rows = [row for row in nas.get(key, []) if row["date"] == origin]
        origin_brands = {name_form(brand) for row in origin_rows for brand in row["brand"]}
        refs = {name_form(row["reference"]) for row in first_rows if row["reference"]}
        reasons = []
        if not origin or origin >= first:
            reasons.append("no_prior_qualifying_NAS")
        if any(row["identity"] != "GSRS" for row in first_rows + origin_rows):
            reasons.append("ingredient_identity_unresolved")
        if origin and not refs:
            reasons.append("reference_missing")
        if origin and refs and refs.isdisjoint(origin_brands):
            reasons.append("reference_requires_review")
        dp = [row for row in rid.get(key, []) if row["noc"] == origin]
        if not dp and origin:
            # RID sometimes lists the newly protected component only. Keep
            # evidence for that product when both approval day and brand agree.
            dp = [row for group in rid.values() for row in group
                  if row["noc"] == origin and name_form(row["brand"]) in origin_brands]
        confident = "ingredient_identity_unresolved" not in reasons
        origin_dins = sorted({din for r in origin_rows for din in r["dins"]})
        candidate = dict(
            key=key, first=first, origin=origin, reasons=reasons,
            origin_notices=sorted({r["notice"] for r in origin_rows}),
            origin_brands=sorted({b for r in origin_rows for b in r["brand"]}),
            origin_dins=origin_dins,
            generic_dins=sorted({din for r in first_rows for din in r["dins"]}),
            dpd_generic_dins=sorted({din for r in first_rows for din in r["dins"] if din in dpd}),
            patent_register=[dict(din=din, **patent) for din in origin_dins
                             for patent in patents[din]],
            candidate_notices=sorted({r["notice"] for r in first_rows}),
            ingredients=sorted({n for r in first_rows for n in r["ingredients"]}),
            references=sorted({r["reference"] for r in first_rows if r["reference"]}),
            data_protection=dp, us_first=us_outcome(key, confident, entities, aliases, audited),
        )
        candidates.append(candidate)
        if not reasons:
            checked[first[:4]] += 1

    audit = {}
    for year in YEARS:
        in_year = [r for r in rows if r["date"].startswith(str(year))]
        ands = [r for r in in_year if r["type"] == "Abbreviated New Drug"]
        audit[year] = {
            "ANDS_notice_product_dispositions": dict(Counter(map(disposition, ands))),
            "eligible_NAS_originals_new_keys": sum(
                min(row["date"] for row in group).startswith(str(year)) for group in nas.values()
            ),
            "at_risk_at_Jan1_observed_NAS_keys": sum(
                min(r["date"] for r in group) < f"{year}-01-01" and
                min((r["date"] for r in generic.get(key, [])), default="9999") >= f"{year}-01-01"
                for key, group in nas.items()
            ),
            "strict_events_before_manual_review": checked[str(year)],
        }
    return {"audit": audit, "canada": sorted(candidates, key=lambda r: (r["first"], r["key"]))}


def apply_canada_review(candidates):
    with (CARD / "canada-adjudications.csv").open(encoding="utf-8", newline="") as file:
        reviews = {row["first_notice"]: row for row in csv.DictReader(file)}
    observed = set()
    for row in candidates:
        matched = reviews.keys() & set(row["candidate_notices"])
        if len(matched) > 1:
            raise ValueError(f"Conflicting reviews for {row['key']}")
        if matched:
            notice = next(iter(matched))
            observed.add(notice)
            row["review"] = reviews[notice]
            decision = reviews[notice]["disposition"]
            expected = {
                "include": ["reference_requires_review"],
                "include_local_identity": ["ingredient_identity_unresolved"],
                "exclude_modality": [],
            }[decision]
            if row["reasons"] != expected:
                raise ValueError(f"Candidate evidence changed for NOC {notice}")
            row["included"] = decision != "exclude_modality"
        else:
            row["included"] = not row["reasons"]
    if observed != reviews.keys():
        raise ValueError(f"Some reviewed NOCs are absent: {reviews.keys() - observed}")


def annual_canada(report):
    for year, audit in report["audit"].items():
        candidates = [row for row in report["canada"] if row["first"].startswith(str(year))]
        admitted = [row for row in candidates if row["included"]]
        audit.update(
            unique_recent_candidates=len(candidates),
            included=len(admitted),
            same_calendar_year_us_duplicate=sum(row["us_first"].startswith(str(year)) for row in admitted),
            pooled_2023_2025_us_duplicate=sum(row["us_first"][:4] in {"2023", "2024", "2025"}
                                              for row in admitted),
            us_overlap_unknown=sum(row["us_first"] == "UNKNOWN" for row in admitted),
            dated_data_protection=sum(any(r["no_file"] and r["ends"] for r in row["data_protection"])
                                      for row in admitted),
            dated_patent_register=sum(any(p["expiry"] for p in row["patent_register"])
                                      for row in admitted),
        )
        for scope in ("same_calendar_year", "pooled_2023_2025"):
            audit[f"{scope}_us_distinct"] = (
                len(admitted) - audit[f"{scope}_us_duplicate"] - audit["us_overlap_unknown"]
            )


def pmda_date(value, epoch):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, (int, float)):
        result = from_excel(value, epoch)
        if isinstance(result, datetime):
            return result.date()
    match = re.fullmatch(r"(R\s*)?(\d+)\.(\d+)\.(\d+)", str(value).strip())
    if match:
        year, month, day = map(int, match.groups()[1:])
        return date(year + 2018 if match[1] else year, month, day)
    raise ValueError(f"Unexpected PMDA date: {value!r}")


def pmda_recent_approvals(root):
    results = []
    for fiscal_year in range(2022, 2026):
        source = root / f"jp-pmda-fy{fiscal_year}.xlsx"
        with source.open("rb") as file:
            book = load_workbook(file, read_only=True, data_only=True)
            for sheet in book:
                for number, row in enumerate(sheet.values, start=1):
                    if len(row) < 7 or not row[5] or not row[6]:
                        continue
                    indication = re.sub(r"\s+", "", str(row[6]))
                    if "新有効成分含有医薬品" not in indication or "承認" not in re.sub(r"\s+", "", str(row[4])):
                        continue
                    when = pmda_date(row[1], book.epoch)
                    if when.year in YEARS:
                        results.append(dict(
                            source=source.name, row=number, date=when.isoformat(),
                            ingredient=" ".join(str(row[5]).split()),
                            modality_screen=("biologic_marker" if any(
                                marker in str(row[5]) for marker in ("遺伝子組換え", "ワクチン", "免疫グロブリン")
                            ) else "requires_manual_small_molecule_classification"),
                        ))
            book.close()
    return sorted(results, key=lambda row: (row["date"], row["source"], row["row"]))


def japan_witnesses(registry, entities, aliases, audited):
    source = CARD / "japan-witnesses.csv"
    with source.open(encoding="utf-8", newline="") as file:
        results = list(csv.DictReader(file))
    for row in results:
        composition = registry.composition(row["ingredient_en"].split(";"))
        row["key"] = aliases.get(composition.key, composition.key)
        row["us_first"] = us_outcome(row["key"], not composition.low_confidence, entities, aliases, audited)
    return results


def japan_master_screen(root):
    """Audit dated listings at NHI code-family grain, before moiety adjudication."""
    editions = {}
    groups = defaultdict(lambda: defaultdict(set))
    for era in range(4, 8):
        source = root / f"jp-nhi-r{era:02}.zip"
        with ZipFile(source) as archive:
            member, = [name for name in archive.namelist() if name.endswith(".csv")]
            records = list(csv.reader(archive.read(member).decode("cp932").splitlines()))
        editions[source.name] = {"member": member, "records": len(records)}
        for row in records:
            if len(row) != (35 if era < 6 else 42) or row[1] != "Y":
                raise ValueError(f"NHI record layout differs in {source.name}")
            if row[16] != "1" or row[15] == "1" or not re.fullmatch(r"[0-9A-Z]{12}", row[31]):
                continue
            code = row[31]
            listing = row[35] if era >= 6 else ""
            if re.fullmatch(r"20\d{6}", listing):
                groups[code[:7]][code].add(date.fromisoformat(listing).isoformat())
            else:
                groups[code[:7]][code].add("UNDATED")

    candidates = []
    for family, code_dates in groups.items():
        dated = {code: sorted(dates - {"UNDATED"}) for code, dates in code_dates.items()}
        known = [value for values in dated.values() for value in values]
        if not known or int(min(known)[:4]) not in YEARS:
            continue
        first = min(known)
        candidates.append(dict(
            code_family=family,
            first_dated_listing=first,
            first_dated_YJ_codes=sorted(code for code, dates in dated.items() if first in dates),
            undated_generic_codes=sorted(code for code, dates in dated.items() if not dates),
            conflicting_date_codes=sorted(code for code, dates in dated.items() if len(dates) > 1),
        ))
    return {"editions": editions,
            "dated_generic_code_families": sorted(candidates, key=lambda row: (
                row["first_dated_listing"], row["code_family"]))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--us-public-s0", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    options = parser.parse_args()
    verify_local_inputs(options.raw)
    recent_approvals = pmda_recent_approvals(options.raw)
    master_screen = japan_master_screen(options.raw)
    registry = registry_for(options.us_public_s0, options.us_public_s0.parent / "moiety" / GSRS_FILE)
    entities, aliases, audited = us_comparator(options.us_public_s0)
    report = screen(options.raw, registry, entities, aliases, audited)
    apply_canada_review(report["canada"])
    annual_canada(report)
    report["japan_recent_NAS_approval_class_rows"] = recent_approvals
    report["japan_witnesses"] = japan_witnesses(registry, entities, aliases, audited)
    report["japan_NHI_code_family_screen"] = master_screen
    options.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
