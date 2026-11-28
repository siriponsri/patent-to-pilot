"""Check source resolution and source dates for every dossier claim."""

import argparse
from datetime import date
from pathlib import Path
import re
from urllib.parse import urlsplit

from .contract import DEMO, read_json, write_json

REF_SCENARIO = ("price-scenario", "market", "assumption", {"fda-amp-2019"})
REF_DEMAND = ("demand", "market", "observed", {"sdud", "sdud-ndc"})
TRACK_A_STATUSES = {"TRACK_A_PENDING", "TRACK_A_FROZEN"}


def dated(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("Expected ISO date")
    return date.fromisoformat(value)


def web_url(value):
    if not isinstance(value, str):
        return False
    try:
        url = urlsplit(value)
        return url.scheme in {"http", "https"} and bool(url.hostname)
    except ValueError:
        return False


def identifiable(source):
    return bool(source and all(isinstance(source.get(field), str) and source[field].strip()
                               for field in ("id", "version", "locator"))
                and (re.fullmatch(r"[a-f0-9]{64}", source.get("sha256") or "")
                     or web_url(source.get("url"))))


def hash_backed(source):
    return bool(source and re.fullmatch(r"[a-f0-9]{64}", source.get("sha256") or ""))


def context_claim(claim, refs):
    context = claim.get("time_basis")
    signature = (claim["id"], claim["section"], claim["kind"], set(refs))
    return (
        (context == "retrospective_scenario" and signature == REF_SCENARIO)
        or (context == "retrospective_demand" and signature == REF_DEMAND)
        or (context == "current_lookup" and claim["section"] == "thai_asean"
            and "current lookup" in claim["text_en"].casefold()
            and ("ปัจจุบัน" in claim["text_th"] or "ล่าสุด" in claim["text_th"]))
    )


def audit_dossier(dossier):
    cutoff = dated(dossier["as_of"])
    track_a = dossier["forecast"]["status"] in TRACK_A_STATUSES
    sources = {source["id"]: source for source in dossier["sources"]}
    errors = []
    if len(sources) != len(dossier["sources"]):
        errors.append("Duplicate source ID")
    days = {}
    for id, source in sources.items():
        try:
            days[id] = dated(source["public_date"]) if source["public_date"] is not None else None
            if track_a:
                if not days[id] and source.get("evidence_cutoff"):
                    days[id] = dated(source["evidence_cutoff"])
                if not days[id] or days[id] > cutoff or not hash_backed(source):
                    errors.append(f"{id}: Track A source requires a hash and a date at or before cutoff")
        except (ValueError, KeyError):
            errors.append(f"{id}: invalid public date")
    claims = dossier["claims"]
    if not claims:
        errors.append("No claims to audit")
    for items in (claims, dossier["checklist"]):
        if len({item["id"] for item in items}) != len(items):
            errors.append("Duplicate claim or checklist ID")
    covered = 0
    sha256_covered = 0
    for claim in claims:
        refs = claim["source_ids"]
        valid = [sources[ref] for ref in refs if ref in sources and identifiable(sources[ref])]
        covered += bool(valid)
        sha256_covered += any(hash_backed(source) for source in valid)
        if not valid or len(valid) != len(refs):
            errors.append(f"{claim['id']}: unresolved source reference")
        contextual = not track_a and context_claim(claim, refs)
        if claim.get("time_basis") and not contextual:
            errors.append(f"{claim['id']}: invalid context label")
        for ref in refs:
            if days.get(ref) and days[ref] > cutoff and not contextual:
                errors.append(f"{claim['id']}: future-dated as-of source {ref} ({days[ref]})")
    for task in dossier["checklist"]:
        if not task["source_ids"] or not all(identifiable(sources.get(ref)) for ref in task["source_ids"]):
            errors.append(f"{task['id']}: unresolved checklist reference")
    reveal = dossier.get("outcome_reveal")
    if track_a and "outcome_reveal" in dossier:
        errors.append("Track A outcome reveal must be absent")
    if reveal:
        end = dated(reveal["window_end"])
        outcome = reveal["first_final_anda_date"]
        refs = reveal.get("source_ids", [])
        if (dossier["forecast"]["status"] != "DEVELOPMENT_ONLY" or cutoff >= date(2017, 1, 1)
                or not cutoff < end < date(2017, 1, 1)
                or (outcome and (not cutoff < dated(outcome) <= end or not refs))
                or any(not identifiable(sources.get(ref)) for ref in refs)):
            errors.append("Invalid development outcome reveal")
    return dict(key=dossier["molecule"]["key"], as_of=dossier["as_of"],
                horizon_months=dossier["forecast"]["horizon_months"], covered=covered,
                claims=len(claims), sha256_covered=sha256_covered, errors=errors)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEMO / "data")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    reports = [audit_dossier(read_json(path)) for path in sorted(args.data_dir.glob("dossier-*.json"))]
    if not reports:
        parser.error("No dossier JSON files found")
    result = dict(dossiers=len(reports), covered=sum(row["covered"] for row in reports),
                  claims=sum(row["claims"] for row in reports),
                  sha256_covered=sum(row["sha256_covered"] for row in reports), results=reports)
    if args.output:
        write_json(args.output, result)
    print(f"{result['covered']}/{result['claims']} claims traceable across {len(reports)} dossiers; "
          f"{result['sha256_covered']} with a source hash.")
    for row in reports:
        for message in row["errors"]:
            print(f"{row['key']} {row['as_of']} {row['horizon_months']}m: {message}")
    return int(any(row["errors"] for row in reports))


if __name__ == "__main__":
    raise SystemExit(main())
