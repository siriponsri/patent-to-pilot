"""Parse FDA Purple Book 'Monthly Historical Data Changes Report' CSV text (Track B).

The file has several sections; each section starts with a header row whose first cell is 'N/R/U'.
Dates look like 'July 27, 1970'. Obtain files from
https://www.accessdata.fda.gov/drugsatfda_docs/PurpleBook/<year>/purplebook-search-<month>-data-download.csv
(direct curl may be blocked by an FDA bot page; download in a browser if so).
"""
import csv
import io
from datetime import date, datetime
from typing import List, Optional


def parse_pb_date(s: str) -> Optional[date]:
    s = (s or "").strip()
    for fmt in ("%B %d, %Y", "%b %d, %Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_purplebook(text: str) -> List[dict]:
    rows, header = [], None
    # parse line-by-line: a stray quote must not swallow following rows
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            cells = next(csv.reader([line]))
        except (csv.Error, StopIteration):
            continue
        if not cells:
            continue
        if cells[0].strip() == "N/R/U":
            header = [c.strip() for c in cells]
            continue
        # first cell is N/R/U or blank (blank = 'listed in current release' sections)
        if header is None or cells[0].strip() not in ("N", "R", "U", "") or len(cells) < 20 or not cells[1].strip():
            continue
        cells = cells + [""] * (len(header) - len(cells))
        rec = dict(zip(header, cells))
        rec["_approval_date"] = parse_pb_date(rec.get("Approval Date"))
        rec["_first_licensure"] = parse_pb_date(rec.get("Date of First Licensure"))
        rows.append(rec)
    return rows


def biosimilar_entries(rows: List[dict]) -> List[dict]:
    """351(k) original licensures with reference product names -> ground truth for biosimilar entry."""
    out = []
    for r in rows:
        if (r.get("BLA Type") or "").strip().startswith("351(k)") and (r.get("Submission Type") or "").strip() == "Original":
            out.append({
                "proper_name": r.get("Proper Name", "").strip(),
                "proprietary_name": r.get("Proprietary Name", "").strip(),
                "ref_product": r.get("Ref. Product Proper Name", "").strip(),
                "bla": r.get("BLA Number", "").strip(),
                "approval_date": r["_approval_date"],
                "first_licensure": r["_first_licensure"],
            })
    return out


def reference_exclusivity(rows: List[dict]) -> List[dict]:
    """351(a) reference products with exclusivity-expiry fields (12-year reference product exclusivity etc.)."""
    out = []
    for r in rows:
        if (r.get("BLA Type") or "").strip().startswith("351(a)"):
            out.append({
                "proper_name": r.get("Proper Name", "").strip(),
                "bla": r.get("BLA Number", "").strip(),
                "first_licensure": r["_first_licensure"],
                "excl_exp": parse_pb_date(r.get("Exclusivity Expiration Date")),
                "ref_excl_exp": parse_pb_date(r.get("Ref. Product Exclusivity Exp. Date")),
                "orphan_excl_exp": parse_pb_date(r.get("Orphan Exclusivity Exp. Date")),
            })
    return out


def first_biosimilar_by_reference(entries: List[dict]) -> dict:
    """ref product proper name (lower) -> {'first_approval': date, 'n_distinct_bla': int}.
    Rows are product presentations, so dedupe by BLA number before counting."""
    out = {}
    for e in entries:
        if not e["approval_date"] or not e["ref_product"]:
            continue
        k = e["ref_product"].lower()
        o = out.setdefault(k, {"first_approval": e["approval_date"], "blas": set()})
        o["blas"].add(e["bla"])
        if e["approval_date"] < o["first_approval"]:
            o["first_approval"] = e["approval_date"]
    return {k: {"first_approval": v["first_approval"], "n_distinct_bla": len(v["blas"])} for k, v in out.items()}
