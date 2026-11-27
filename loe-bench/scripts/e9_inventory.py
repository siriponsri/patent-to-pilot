"""Verify pinned PSG sources and produce a dated inventory and continuity audit."""

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import re

from e9_fetch import RAW
from t2_dev_run import ROOT, _verify
from loe_bench.psg import Capture, PSGHistory, link_key, parse_listing
from loe_bench.seal import TEST_FIRST


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False, default=str) + "\n",
                    encoding="utf-8", newline="\n")


def load_sources(raw, pinned):
    ledger = {item["file"]: item for item in pinned}
    for name, item in ledger.items():
        if item.get("sha256"):
            _verify(raw / name, item["sha256"])

    def body(name):
        if ledger[name]["status"] != 200:
            raise ValueError(f"source could not be retrieved: {name}")
        return (raw / name).read_text(encoding="utf-8-sig", errors="replace")

    landing = body("fda-current.html")
    expected = int(re.search(r"Total number of currently published PSGs:\s*(\d+)", landing)[1])
    letters = sorted(set(re.findall(r"searchLetter=([A-Z])#", landing)))
    current = []
    for letter in letters:
        name = f"fda-letter-{letter}.html"
        html = body(name)
        if f"Total number of currently published PSGs: {expected}" not in html:
            raise ValueError(f"FDA total changed during collection: {name}")
        current.extend(row for row in parse_listing(html, name, ledger[name]["final_url"]) if row.kind == "latest")
    if len(current) != expected:
        raise ValueError(f"FDA published total {expected} differs from {len(current)} extracted rows")
    updates = parse_listing(landing, "fda-current.html", ledger["fda-current.html"]["final_url"])

    archived = {}
    skipped = []
    for cdx, prefix in (("cdx-early.json", "wayback-early"), ("cdx-old-drugs.json", "wayback")):
        for _, timestamp, original, *_ in json.loads(body(cdx))[1:]:
            name = f"{prefix}-{timestamp}.html"
            item = ledger[name]
            replay = f"https://web.archive.org/web/{timestamp}id_/{original}"
            if item["status"] != 200 or item["final_url"] != replay:
                skipped.append({"file": name, "status": item["status"], "final_url": item.get("final_url")})
                continue
            captured = datetime.strptime(timestamp, "%Y%m%d%H%M%S").date()
            if captured >= TEST_FIRST:
                raise ValueError("archive outside E9 observation window")
            rows = parse_listing(body(name), name, original, archived=True)
            if rows:
                archived[name] = captured, rows
            else:
                skipped.append({"file": name, "status": "NO_PSG_TABLE"})
    return current, updates, archived, skipped


def _serial(row):
    return asdict(row)


def _month(row):
    return row.recommended_by.strftime("%Y-%m") if row.recommended_by else None


class Continuity:
    def __init__(self, current):
        self.by_document = defaultdict(set)
        self.by_formulation = defaultdict(set)
        for row in current:
            self.by_document[row.document].add(row)
            self.by_formulation[row.formulation].add(row)

    def find(self, historical):
        documents = self.by_document.get(historical.document, set())
        formulations = {row for row in self.by_formulation.get(historical.formulation, ())
                        if set(row.applications).intersection(historical.applications)}
        candidates = documents & formulations or (documents | formulations)
        if len(candidates) == 1:
            return next(iter(candidates)), "unique"
        if candidates:
            return None, "ambiguous"
        return None, "no_match"


def build_inventory(current, updates, archived, linker):
    crosswalk = Continuity(current)
    posting = defaultdict(set)
    revisions = defaultdict(set)
    audits, captures = {}, []
    for name, (captured, rows) in archived.items():
        valid = {row for row in rows if row.recommended_from and row.recommended_from <= captured}
        linked, missing_keys, uncertain_dates = [], [], []
        for row in rows:
            key = link_key(row, linker)
            if key is not None:
                linked.append((key, row))
            else:
                missing_keys.append(row)
            if row not in valid:
                uncertain_dates.append(row)
        captures.append(Capture(captured, tuple(linked)))
        status = Counter()
        comparisons = Counter()
        unresolved = []
        for row in rows:
            match, reason = crosswalk.find(row)
            status[reason] += 1
            if not match:
                unresolved.append(dict(_serial(row), continuity=reason))
                continue
            if _month(row) and _month(match):
                comparisons["dated_pairs"] += 1
                comparisons["same_month"] += _month(row) == _month(match)
                comparisons["current_later"] += _month(row) < _month(match)
                comparisons["current_earlier"] += _month(row) > _month(match)
                if row.kind == "new":
                    comparisons["dated_new_pairs"] += 1
                    comparisons["new_same_month"] += _month(row) == _month(match)
            if row in valid:
                (posting if row.kind == "new" else revisions)[match].add(row)
        totals = dict.fromkeys(("dated_pairs", "same_month", "current_later", "current_earlier",
                                "dated_new_pairs", "new_same_month"), 0)
        totals.update(comparisons)
        audits[name] = {
            "captured": captured, "source_scope": "RECENT_UPDATES_ONLY",
            "rows": len(rows), "kinds": dict(Counter(row.kind for row in rows)),
            "continuity_counts": {label: status[label] for label in ("unique", "ambiguous", "no_match")},
            "no_current_match_rate": status["no_match"] / len(rows),
            "version_month_counts": totals,
            "version_month_agreement_rate": comparisons["same_month"] / comparisons["dated_pairs"]
            if comparisons["dated_pairs"] else None,
            "new_vs_current_month_agreement_rate": comparisons["new_same_month"] / comparisons["dated_new_pairs"]
            if comparisons["dated_new_pairs"] else None,
            "moiety_rows_matched": len(linked), "moiety_match_rate": len(linked) / len(rows),
            "unmatched_moiety_examples": [_serial(row) for row in missing_keys[:5]],
            "unresolved_continuity_examples": unresolved[:5],
            "unusable_recommendation_dates": [_serial(row) for row in uncertain_dates],
        }
    for row in updates:
        match, _ = crosswalk.find(row)
        if match:
            (posting if row.kind == "new" else revisions)[match].add(row)
    inventory = []
    for row in current:
        observed_new = sorted(posting[row], key=lambda row: (row.recommended_by, row.source, row.row))
        known_revisions = sorted(revisions[row], key=lambda row: (row.recommended_by, row.source, row.row))
        inventory.append({
            **_serial(row), "moiety_key": link_key(row, linker),
            "first_posting_observed": observed_new[0].recommended_by if observed_new else None,
            "first_posting_evidence": _serial(observed_new[0]) if observed_new else None,
            "observed_revisions": [_serial(obs) for obs in known_revisions],
        })
    matched = sum(item["moiety_key"] is not None for item in inventory)
    return PSGHistory(captures), inventory, {
        "current": {
            "rows": len(inventory), "moiety_rows_matched": matched, "moiety_match_rate": matched / len(inventory),
            "row_first_posting_observed": sum(bool(item["first_posting_observed"]) for item in inventory),
            "row_revision_observed": sum(bool(item["observed_revisions"]) for item in inventory),
            "unmatched_moiety_examples": [item for item in inventory if item["moiety_key"] is None][:8],
        },
        "archive": audits,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--psg-dir", type=Path, default=RAW)
    args = parser.parse_args()
    pinned = [json.loads(path.read_text(encoding="utf-8")) for path in sorted(args.psg_dir.glob("*.fetch.json"))]
    load_sources(args.psg_dir, pinned)
    write_json(ROOT / "data/E9_sources.json", pinned)


if __name__ == "__main__":
    main()
