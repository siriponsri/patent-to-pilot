"""Backfill CP2 annual Orange Book windows using the public Wayback CDX API."""

import argparse
import hashlib
import io
import json
import sys
import time
import zipfile
from base64 import b32encode
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loe_bench.ob_history import (DEFAULT_DIR, parse_exclusivity, parse_patents, parse_products,
                                  read_zip_tables, zip_edition_date)

ARCHIVE = "https://web.archive.org"
SOURCES = (
    "www.fda.gov/downloads/Drugs/InformationOnDrugs/UCM163762.zip",
    "www.fda.gov/media/76860/download",
    "www.fda.gov/media/76860/download?attachment",
    "www.fda.gov/media/76860/download?attachment=",
    "www.accessdata.fda.gov/cder/ob/docs/obdata.zip",
    "www.fda.gov/cder/ob/eobzip.zip",
    "www.fda.gov/cder/ob/docs/eobzip.zip",
    "www.accessdata.fda.gov/cder/ob/eobzip.zip",
    "www.accessdata.fda.gov/cder/ob/docs/eobzip.zip",
)
PRIORITY = (2009, 2010, 2011, 2013, 2014, 2015, 2016, 2017,
            2018, 2019, 2020, 2022, 2023, 2024, 2012, 2021)
CDX_FIELDS = ("timestamp", "original", "statuscode", "digest", "mimetype")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Use the exact CDX locator. A redirected replay may be a different edition.
        return None


class Wayback:
    def __init__(self):
        self.opener = build_opener(NoRedirect())
        self.last_request = 0.0

    def get(self, url):
        time.sleep(max(0.0, 1.0 - (time.monotonic() - self.last_request)))
        self.last_request = time.monotonic()
        request = Request(url, headers={"User-Agent": "LOE-Bench public Orange Book archival research"})
        with self.opener.open(request, timeout=30) as response:
            return response.read(), response.headers

    def captures(self, source, first_year, last_year):
        url = ARCHIVE + "/cdx/search/cdx?" + urlencode({
            "url": source, "from": first_year, "to": last_year,
            "output": "json", "fl": ",".join(CDX_FIELDS),
            "filter": "statuscode:200|\\-",
        })
        log = {"query": url}
        try:
            body, _ = self.get(url)
            rows = json.loads(body) if body.strip() else []
            if rows and tuple(rows[0]) != CDX_FIELDS:
                raise ValueError("unexpected CDX response header")
            captures = [tuple(row) for row in rows[1:] if len(row) == len(CDX_FIELDS)]
            captures = [row for row in captures if fda_url(row[1]) and
                        (row[2] == "200" or row[4] == "warc/revisit")]
            log.update(http_status=200, candidate_rows=len(captures))
        except (URLError, OSError, ValueError) as exc:
            captures = []
            log.update(http_status=getattr(exc, "code", None), error=str(exc))
        return captures, log


def fda_url(url):
    parsed = urlsplit(url)
    return (parsed.scheme in ("http", "https") and parsed.hostname and
            (parsed.hostname == "fda.gov" or parsed.hostname.endswith(".fda.gov")))


def capture_times(manifest, edition):
    extra = manifest.get("e2b", {}).get("additional_captures", {}).get(edition["sha256"], [])
    return sorted(ts for ts in [edition.get("wayback_ts"), *(c["wayback_ts"] for c in extra)] if ts)


def fresh(edition_date, year):
    return f"{year}-07-01" <= edition_date <= f"{year}-12-31"


def timely(manifest, edition, year):
    return any(ts[:8] <= f"{year + 1}0101" for ts in capture_times(manifest, edition))


def ingest(wayback, capture, data_dir, manifest, year, scheme=None):
    ts, source, _, digest, _ = capture
    replay_source = source if scheme is None else urlsplit(source)._replace(scheme=scheme).geturl()
    replay = f"{ARCHIVE}/web/{ts}id_/{replay_source}"
    log = {"wayback_ts": ts, "wayback_url": replay, "cdx_digest": digest}
    try:
        body, headers = wayback.get(replay)
        retrieved = datetime.now(timezone.utc).isoformat()
        log.update(http_status=200, bytes=len(body), retrieved_utc=retrieved)
        # A replay dated differently cannot establish availability at this locator.
        memento = headers.get("Memento-Datetime")
        if memento and parsedate_to_datetime(memento).strftime("%Y%m%d%H%M%S") != ts:
            raise ValueError("Memento-Datetime differs from the requested capture")
        if digest != "-" and b32encode(hashlib.sha1(body).digest()).decode("ascii") != digest:
            raise ValueError("body differs from the CDX payload digest")
        stream = io.BytesIO(body)
        edition_date = zip_edition_date(stream).isoformat()
        tables = read_zip_tables(stream)
        sha = hashlib.sha256(body).hexdigest()
        log.update(edition_date=edition_date, sha256=sha)
        if not fresh(edition_date, year) or edition_date > date(
                int(ts[:4]), int(ts[4:6]), int(ts[6:8])).isoformat():
            log["result"] = "outside target edition window or dated after capture"
            return log

        previous = next((e for e in manifest["editions"] if e["sha256"] == sha), None)
        evidence = {"wayback_ts": ts, "wayback_url": replay, "source_url": source,
                    "retrieved_utc": retrieved, "cdx_digest": digest}
        if previous:
            if ts not in capture_times(manifest, previous):
                manifest["e2b"]["additional_captures"].setdefault(sha, []).append(evidence)
            log["result"] = "SHA-256 duplicate"
        else:
            filename = f"ob_{ts}.zip"
            target = data_dir / filename
            if target.exists():
                if hashlib.sha256(target.read_bytes()).hexdigest() != sha:
                    raise ValueError(f"existing artifact has different SHA-256: {target}")
            else:
                target.write_bytes(body)
            patents = parse_patents(tables["patent"])
            entry = dict(evidence, file=filename, bytes=len(body), sha256=sha,
                         http_status=200, origin="wayback_download", edition_date=edition_date,
                         edition_date_basis="max ZIP member modification date",
                         rows=dict(products=len(parse_products(tables["products"])),
                                   patent=len(patents),
                                   exclusivity=len(parse_exclusivity(tables["exclusivity"]))),
                         has_submission_date=any(p["has_submission_col"] for p in patents))
            manifest["editions"].append(entry)
            log["result"] = "added"
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        log.update(error=str(exc), result="rejected")
        if getattr(exc, "code", None) is not None:
            log["http_status"] = exc.code
    return log


def ordered_captures(rows, year, late):
    start, stop = (f"{year + 1}0102", f"{year + 1}0229") if late else (
        f"{year}0701", f"{year + 1}0101")
    return sorted({r for r in rows if start <= r[0][:8] <= stop}, reverse=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=ROOT / "data" / "OB_EDITIONS.json")
    parser.add_argument("--data-dir", type=Path, default=Path(DEFAULT_DIR))
    parser.add_argument("--source", action="append", help="Override CDX sources with FDA paths")
    parser.add_argument("--year", action="append", type=int, choices=PRIORITY)
    parser.add_argument("--replay-scheme", choices=("http", "https"),
                        help="Replay the CDX timestamp using an alternate FDA URL scheme")
    args = parser.parse_args()
    years = [year for year in PRIORITY if not args.year or year in args.year]
    sources = args.source or SOURCES
    if any(not fda_url("https://" + source) for source in sources):
        parser.error("--source must be an FDA host and path without a scheme")
    args.data_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    ledger = manifest.setdefault("e2b", {"cdx_queries": [], "replays": [], "additional_captures": {}})
    wayback = Wayback()
    rows = []
    for source in sources:
        captures, log = wayback.captures(source, min(years), max(years) + 1)
        rows.extend(captures)
        ledger["cdx_queries"].append(log)
        print(json.dumps(log), flush=True)

    for late in (False, True):
        for year in years:
            def covered():
                return any(fresh(e["edition_date"], year) and (late or timely(manifest, e, year))
                           for e in manifest["editions"])

            replayed_digests = set()
            for capture in ordered_captures(rows, year, late):
                if covered():
                    break
                digest = capture[3]
                if digest in replayed_digests:
                    continue
                log = ingest(wayback, capture, args.data_dir, manifest, year, args.replay_scheme)
                ledger["replays"].append(dict(log, target_year=year))
                print(json.dumps(log), flush=True)
                if digest != "-" and log.get("sha256"):
                    replayed_digests.add(digest)

    args.manifest.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
