"""Collect FDA PIV lists and exact Wayback captures. Run from any directory."""
import argparse
import base64
from collections import defaultdict
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from hashlib import sha1, sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import time
from urllib.error import URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile
from zlib import error as ZlibError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from loe_bench.common import add_months
from loe_bench.ob_history import (
    DEFAULT_DIR as OB_DIR, OBHistory, PRODUCT_COLS_NOTYPE, _read_table, ingredient_key_ob,
    parse_ob_date, read_zip_tables,
)
from loe_bench.piv_history import EntityMatcher, EntityProduct, PIVHistory, _pdf_objects, parse_entries

RAW = Path("C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/piv")
MANIFEST = ROOT / "data/PIV_EDITIONS.json"
PAGE = "https://www.fda.gov/drugs/abbreviated-new-drug-application-anda/patent-certifications-and-suitability-petitions"
LEGACY = "/Drugs/DevelopmentApprovalProcess/HowDrugsareDevelopedandApproved/ApprovalApplications/AbbreviatedNewDrugApplicationANDAGenerics/"
OLD_PAGES = [
    "http://www.fda.gov" + LEGACY + "ucm047676.htm",
    "http://www.fda.gov/cder/ogd/ppiv.htm",
]
ARCHIVE = "https://web.archive.org"
CDX_FIELDS = ["timestamp", "original", "statuscode", "digest", "mimetype"]
DATE_PATTERN = r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}"


def edition_date(label):
    match = re.search(DATE_PATTERN, label, re.I)
    if match:
        return datetime.strptime(" ".join(match[0].split()), "%B %d, %Y").date()
    return None


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.label = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label = []

    def handle_data(self, data):
        if self.href:
            self.label.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            label = " ".join("".join(self.label).split())
            self.links.append((self.href, label))
            self.href = None


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Collector:
    def __init__(self, raw):
        self.raw = raw
        raw.mkdir(parents=True, exist_ok=True)
        self.last_request = None
        self.log = []
        self.files = {}
        self.opener = build_opener(NoRedirect())

    def request(self, url):
        if self.last_request is not None:
            time.sleep(max(0, 1.1 - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        with self.opener.open(Request(url, headers={"User-Agent": "LOE-Bench PIV research"}), timeout=20) as response:
            return response.read(), response.headers

    def cached(self, url):
        for row in reversed(self.log):
            if row["url"] == url and row["status"] == "PASS":
                path = self.raw / row["file"]
                if path.is_file():
                    data = path.read_bytes()
                    if sha256(data).hexdigest() == row["sha256"]:
                        return data
        return None

    def note(self, url, status, **fields):
        self.log.append({"url": url, "status": status, **fields})
        print(status, url, fields.get("error", ""), flush=True)

    def save(self, data, suffix):
        digest = sha256(data).hexdigest()
        name = f"{digest}.{suffix}"
        (self.raw / name).write_bytes(data)
        return {"file": name, "bytes": len(data), "sha256": digest}

    def cdx(self, source):
        params = {
            "url": source, "from": "200907", "to": "20250101",
            "output": "json", "fl": ",".join(CDX_FIELDS), "filter": "statuscode:200",
        }
        url = f"{ARCHIVE}/cdx/search/cdx?{urlencode(params)}"
        try:
            data = self.cached(url)
            cached = data is not None
            if not cached:
                data, _ = self.request(url)
            rows = json.loads(data) if data.strip() else []
            if rows and rows[0] != CDX_FIELDS:
                raise ValueError("unexpected CDX fields")
            captures = [dict(zip(CDX_FIELDS, row, strict=True)) for row in rows[1:]]
            if not cached:
                self.note(url, "PASS", captures=len(captures), **self.save(data, "json"))
            return captures
        except (URLError, OSError, ValueError) as exc:
            self.note(url, "FAIL", error=str(exc))
            return []

    def retrieve(self, source, *, capture=None, page=False, version=None):
        timestamp = capture["timestamp"] if capture else None
        url = f"{ARCHIVE}/web/{timestamp}id_/{source}" if capture else source
        try:
            data = self.cached(url) if capture else None
            cached = data is not None
            headers = {}
            if not cached:
                data, headers = self.request(url)
            if capture:
                digest = base64.b32encode(sha1(data).digest()).decode()
                if digest != capture["digest"]:
                    raise ValueError("raw bytes differ from the CDX digest")
                memento = headers.get("Memento-Datetime")
                if memento and parsedate_to_datetime(memento).strftime("%Y%m%d%H%M%S") != timestamp:
                    raise ValueError("replay timestamp differs from the CDX timestamp")
            if data.startswith(b"%PDF-"):
                fmt = "pdf"
            elif data.startswith(b"PK\x03\x04"):
                fmt = "xlsx"
            elif page and b"<html" in data[:4096].lower():
                fmt = "html"
            else:
                raise ValueError("unexpected payload format")
            if page and fmt != "html":
                raise ValueError("expected an FDA listing page")
            artifact = self.save(data, fmt)
            if not cached:
                self.note(url, "PASS", **artifact)
            if page:
                parser = Links()
                parser.feed(data.decode("utf-8", errors="replace"))
                return [
                    (urljoin(source, href), label)
                    for href, label in parser.links
                    if urlsplit(urljoin(source, href)).hostname in {"www.fda.gov", "fda.gov"}
                    and re.search(r"paragraph\s*iv|\bppiv\b", label, re.I)
                    and re.search(r"/download|\.(?:pdf|xlsx?)$", href, re.I)
                ]
            self.files.setdefault((source, timestamp, artifact["sha256"]), {
                "source_url": source, "wayback_timestamp": timestamp,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "format": fmt,
                "version_date": version.isoformat() if version else None,
                "cdx_sha1_base32": capture["digest"] if capture else None,
                **artifact,
            })
        except (URLError, OSError, ValueError) as exc:
            self.note(url, "FAIL", error=str(exc))
        return []


def per_window(captures, limit):
    """Prioritize distinct payloads, newest capture first in each annual window."""
    windows = defaultdict(list)
    for capture in sorted(captures, key=lambda row: row["timestamp"], reverse=True):
        day = datetime.strptime(capture["timestamp"], "%Y%m%d%H%M%S").date()
        year = day.year if day == date(day.year, 1, 1) else day.year + 1
        if not 2010 <= year <= 2025 or day < date(year - 1, 7, 1):
            continue
        group = windows[year]
        if len(group) < limit and all(row["digest"] != capture["digest"] for row in group):
            group.append(capture)
    for year in sorted(windows):
        yield from windows[year]


def acquire(raw):
    collector = Collector(raw)
    journal = raw / "acquisition.json"
    if journal.is_file():
        previous = json.loads(journal.read_text(encoding="utf-8"))
        collector.log = previous["attempts"]
        collector.files = {(row["source_url"], row["wayback_timestamp"], row["sha256"]): row
                           for row in previous["files"]}
    sources = {
        "http://www.fda.gov/downloads" + LEGACY + "UCM293268.pdf",
        "http://www.fda.gov/cder/ogd/ppiv.pdf",
        "https://www.fda.gov/media/166048/download",
        "https://www.fda.gov/media/194880/download",
    }
    try:
        for url, label in collector.retrieve(PAGE, page=True):
            collector.retrieve(url, version=edition_date(label))
            sources.add(url)
        for source in [PAGE, *OLD_PAGES]:
            for capture in per_window(collector.cdx(source), 2):
                for url, _ in collector.retrieve(capture["original"], capture=capture, page=True):
                    sources.add(url)
        captures = []
        for source in sorted({re.sub(r"^https?://|:80(?=/)", "", url) for url in sources}):
            captures.extend(collector.cdx(source))
        for capture in per_window(captures, 4):
            collector.retrieve(capture["original"], capture=capture)
    finally:
        journal.write_text(
            json.dumps({"attempts": collector.log, "files": list(collector.files.values())}, indent=2) + "\n",
            encoding="utf-8",
        )


def identify_pdf_date(data):
    objects, _ = _pdf_objects(data)
    info = b"\n".join(obj for obj in objects.values() if re.search(rb"/(?:CreationDate|ModDate)\b", obj))
    titles = re.findall(rb"/Title\s*\(([^)]+)\)", info)
    dates = {when for title in titles if (when := edition_date(title.decode("latin1")))}
    if len(dates) == 1:
        return dates.pop().isoformat(), "FDA PDF title"
    metadata = re.findall(rb"/(?:CreationDate|ModDate)\s*\(D:(\d{8})", info)
    if metadata:
        return max(datetime.strptime(when.decode(), "%Y%m%d").date() for when in metadata).isoformat(), (
            "latest embedded FDA PDF creation or modification date")
    return None, None


def build_manifest(raw, target):
    journal = json.loads((raw / "acquisition.json").read_text(encoding="utf-8"))
    cdx_digests = defaultdict(set)
    for attempt in journal["attempts"]:
        if attempt["status"] == "PASS" and "captures" in attempt:
            payload = (raw / attempt["file"]).read_bytes()
            if sha256(payload).hexdigest() != attempt["sha256"]:
                raise ValueError("saved CDX response differs from its acquisition SHA-256")
            for timestamp, url, _, digest, _ in (json.loads(payload)[1:] if payload.strip() else []):
                cdx_digests[url, timestamp].add(digest)
    editions = []
    parsed = {}
    for source in journal["files"]:
        digest = source["sha256"]
        row = {**source, "rows": None, "parse_status": "FAIL", "version_date_basis": None}
        try:
            data = (raw / row["file"]).read_bytes()
            if sha256(data).hexdigest() != digest:
                raise ValueError("saved bytes differ from the acquisition SHA-256")
            if timestamp := row["wayback_timestamp"]:
                row["wayback_url"] = f"{ARCHIVE}/web/{timestamp}id_/{row['source_url']}"
                cdx_digest = base64.b32encode(sha1(data).digest()).decode()
                if cdx_digest not in cdx_digests[row["source_url"], timestamp]:
                    raise ValueError("saved bytes lack an exact CDX digest match")
                row["cdx_sha1_base32"] = cdx_digest
            if row["version_date"]:
                row["version_date_basis"] = "FDA listing link text"
            elif row["format"] == "pdf":
                row["version_date"], row["version_date_basis"] = identify_pdf_date(data)
            if digest not in parsed:
                parsed[digest] = parse_entries(data, row["format"])
            entries = parsed[digest]
            row.update(rows=len(entries), dated_rows=sum(e.first_submission is not None for e in entries),
                       parse_status="PASS")
        except (OSError, ValueError, IndexError, KeyError, TypeError, BadZipFile, ParseError, ZlibError) as exc:
            row["parse_error"] = f"{type(exc).__name__}: {exc}"
        editions.append(row)
    editions.sort(key=lambda row: (row["version_date"] or "", row["wayback_timestamp"] or "", row["source_url"]))
    target.write_text(json.dumps({"schema_version": 1, "source_page": PAGE, "editions": editions,
                                  "acquisition_attempts": journal["attempts"]}, indent=2) + "\n",
                      encoding="utf-8")


def audit_ob(raw, manifest, ob_dir):
    """Measure row linkage on public, contemporaneous NDA product catalogs in DEV."""
    ob = OBHistory.from_manifest(str(ROOT / "data/OB_EDITIONS.json"), str(ob_dir))
    piv = PIVHistory(manifest, raw, EntityMatcher([]))
    for year in range(2010, 2017):
        cutoff = date(year, 1, 1)
        edition = piv.edition_asof(cutoff)
        source, proof = ob.available_source_asof(cutoff)
        if not edition or not source or source.edition_date < add_months(cutoff, -6):
            continue
        path = ob_dir / source.identity["file"]
        if sha256(path.read_bytes()).hexdigest() != source.identity["sha256"]:
            raise ValueError(f"Orange Book SHA-256 mismatch for {year}")
        catalog = []
        for row in _read_table(read_zip_tables(str(path))["products"], PRODUCT_COLS_NOTYPE):
            # The earliest exports have no Appl_Type. Require an explicit RLD flag there.
            if row.get("appl_type") != "N" and not (not row.get("appl_type") and row.get("rld") == "Yes"):
                continue
            when = parse_ob_date(row["approval_date"])
            if row["approval_date"].lower().startswith("approved prior to jan 1, 1982"):
                when = date(1982, 1, 1)
            if not when or when > cutoff:
                continue
            catalog.append(EntityProduct(ingredient_key_ob(row["ingredient"]), row["ingredient"],
                                         row["df;route"], when))
        matcher = EntityMatcher(catalog)
        rows = piv.entries(edition)
        unresolved = [entry for entry in rows if matcher.match(entry, cutoff) is None]
        print(json.dumps({
            "cutoff": cutoff.isoformat(), "piv_sha256": edition.sha256,
            "ob_sha256": source.identity["sha256"], "ob_availability": proof,
            "rows": len(rows), "matched": len(rows) - len(unresolved),
            "unmatched_examples": [
                {"ingredient": entry.ingredient, "form": entry.dosage_form, "locator": entry.locator}
                for entry in unresolved[:5]
            ],
        }))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=RAW)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--offline", action="store_true", help="Build from saved raw files and acquisition journal")
    parser.add_argument("--audit-ob", type=Path, nargs="?", const=Path(OB_DIR),
                        help="Audit legacy keys against public development Orange Book editions")
    args = parser.parse_args()
    if not args.offline:
        acquire(args.raw)
    build_manifest(args.raw, args.manifest)
    if args.audit_ob:
        audit_ob(args.raw, args.manifest, args.audit_ob)


if __name__ == "__main__":
    main()
