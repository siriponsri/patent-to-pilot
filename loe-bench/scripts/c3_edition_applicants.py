"""Extract applicant listings for admitted ANDAs from verified historical editions."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
import re
from pathlib import Path
from zipfile import ZipFile

from loe_bench.c3 import DEVELOPMENT_END, FIRST_TEST, Evidence
from loe_bench.common import add_months
from loe_bench.nber_ob import nber_sources

from freeze_run import read_json
from t2_dev_run import _verify


MONTH = set(b"Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())
DATE = re.compile(rb"([A-Z][a-z]{2}) +(\d{1,2}), +(\d{4})")
PRODUCT_LIST = re.compile(r"(?:PRESCRIPTION|OTC|DISCONTINUED) DRUG PRODUCT LIST")


@dataclass(frozen=True)
class Listing:
    application: str
    date: date
    name: str | None
    kind: str
    evidence: Evidence


def _zip_rows(path, admitted):
    """Filter typed application and product approval date before decoding names."""
    with ZipFile(path) as archive:
        names = [name for name in archive.namelist() if Path(name).stem.lower() == "products"]
        member, = names
        with archive.open(member) as stream:
            columns = stream.readline().rstrip(b"\r\n").lower().split(b"~")
            kind, number, approved, name = (columns.index(column) for column in (
                b"appl_type", b"appl_no", b"approval_date", b"applicant"))
            for i, line in enumerate(stream, 1):
                fields = line.rstrip(b"\r\n").split(b"~")
                if len(fields) != len(columns) or fields[kind].strip() != b"A":
                    continue
                application = admitted.get(fields[number].strip().zfill(6))
                if application is None:
                    continue
                match = DATE.fullmatch(fields[approved].strip())
                if fields[approved].strip() and (not match or match[1] not in MONTH):
                    continue
                if match and int(match[3]) >= FIRST_TEST.year:
                    continue
                yield application, fields[name].decode("latin-1").strip() or None, f"{member} data row {i}"


def _pdf_rows(path, admitted, year):
    """Read product sections only after verifying the annual book's coverage statement."""
    import pymupdf

    with pymupdf.open(path) as document:
        cover = " ".join(" ".join(document[i].get_text().split()) for i in (1, 2))
        if not re.search(rf"current through December 31, {year - 1}\b", cover, re.IGNORECASE):
            raise ValueError(f"Cannot establish the development coverage of {path.name}")
        for page in document:
            words = page.get_text("words")
            header = " ".join(word[4] for word in words if word[1] < 65).upper()
            if not PRODUCT_LIST.search(header):
                continue
            applicant_left = 100 if page.rect.width < 600 else 106
            for x, y, _, _, token, *_ in words:
                if not 399 <= x <= 430 or not re.fullmatch(r"A[0-9]{6}", token):
                    continue
                application = admitted.get(token[1:].encode("ascii"))
                if application is None:
                    continue
                aligned = sorted(word for word in words if abs(word[1] - y) < 1.6)
                products = [word[4] for word in aligned if 450 <= word[0] < 471
                            and re.fullmatch(r"[0-9]{3}", word[4])]
                if len(products) != 1:
                    raise ValueError(f"Cannot locate the product number for {token} on {path.name} page {page.number + 1}")
                name = " ".join(word[4] for word in aligned if applicant_left <= word[0] < 211).strip()
                locator = f"PDF page {page.number + 1}, {token}/{products[0]}, applicant column"
                yield application, name or None, locator


def collect_listings(approvals, ob_dir, nber_dir):
    """Load only editions within a possible applicant's window, prior to TEST."""
    windows = {app: (day, add_months(day, 12)) for app, day in approvals.items()}
    if not windows or any(start > DEVELOPMENT_END for start, _ in windows.values()):
        raise ValueError("Historical applicant lookup requires admitted development approvals")

    def targets(day):
        return {app[4:].encode("ascii"): app for app, (start, end) in windows.items() if start <= day <= end}

    listings = defaultdict(list)
    inventory = []

    def collect(day, source, digest, kind, rows):
        matched = set()
        for app, name, locator in rows:
            matched.add(app)
            listings[app].append(Listing(app, day, name, kind, Evidence(source, day.isoformat(), digest, locator)))
        inventory.append({"kind": kind, "edition": day.isoformat(), "source": source,
                          "sha256": digest, "matching_applications": len(matched)})

    for entry in read_json("OB_EDITIONS.json")["editions"]:
        day = date.fromisoformat(entry["edition_date"])
        if day >= FIRST_TEST or not (numbers := targets(day)):
            continue
        path = ob_dir / entry["file"]
        _verify(path, entry["sha256"])
        collect(day, entry.get("wayback_url") or entry["source_url"], entry["sha256"],
                "fda_zip", _zip_rows(path, numbers))

    annual = read_json("E8_NBER_MANIFEST.json")
    dates = {source.identity["edition_year"]: source.edition_date for source in nber_sources(annual, nber_dir)}
    for entry in annual["editions"]:
        year = entry["year"]
        day = dates[year]
        if day >= FIRST_TEST or not (numbers := targets(day)):
            continue
        context = entry.get("edition_context")
        if context is None:
            raise ValueError(f"Missing product-list PDF provenance for annual Orange Book {year}")
        path = nber_dir / context["file"]
        _verify(path, context["sha256"])
        collect(day, context["url"], context["sha256"], "nber_annual", _pdf_rows(path, numbers, year))
    return listings, sorted(inventory, key=lambda item: (item["edition"], item["kind"]))
