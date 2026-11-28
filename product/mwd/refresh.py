"""Acquire a dated openFDA inventory snapshot for an unregistered forecast."""

import argparse
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile
from zlib import error as ZlibError

from .contract import BENCH, CURRENT, ROOT, read_json, write_json
from .inputs import PRIVATE, verify

LABEL = "unregistered forecast"


def canonical(row):
    return json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":"))


def fetch_partition(fetcher, endpoint, query, path):
    version = None
    total = None

    def observe(meta):
        nonlocal version, total
        observed = meta.get("last_updated")
        count = meta.get("results", {}).get("total")
        if (not isinstance(observed, str) or not observed or type(count) is not int or count < 0
                or (version is not None and (observed, count) != (version, total))):
            raise ValueError("Missing or inconsistent openFDA edition metadata")
        version, total = observed, count

    rows = Counter()
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        for row in fetcher.iter_records(endpoint, query, use_api_key=False, observe_meta=observe):
            line = canonical(row)
            rows[line] += 1
            stream.write(line + "\n")
    if total != rows.total():
        raise ValueError("Incomplete openFDA partition")
    return version, rows


def record_delta(rows, previous):
    return dict(records=rows.total(), rows_added=(rows - previous).total(), rows_removed=(previous - rows).total())


def orange_archive(private, staged, collector):
    from loe_bench.ob_history import read_zip_tables, zip_edition_date

    day = "2026-11-27"
    pin = read_json(BENCH / "TRACKA_CORE_MANIFEST.json")["edition_audit"][day]["orange_book"]["source"]
    baseline = private / "ob_editions" / pin["file"]
    verify(baseline, pin["sha256"])
    previous = read_zip_tables(baseline)
    body, _ = collector.request(pin["source_url"])
    payload = BytesIO(body)
    version = zip_edition_date(payload).isoformat()
    tables = read_zip_tables(payload)
    deltas = {table: record_delta(Counter(rows.splitlines()[1:]), Counter(previous[table].splitlines()[1:]))
              for table, rows in tables.items()}
    path = staged / "orange-book.zip"
    path.write_bytes(body)
    return dict(filename=path.name, source_url=pin["source_url"], source_version=version,
                sha256=sha256(body).hexdigest(),
                baseline_sha256=pin["sha256"], table_deltas=deltas,
                **{field: sum(delta[field] for delta in deltas.values())
                   for field in ("records", "rows_added", "rows_removed")})


def piv_inventory(private, collector, piv_fetch):
    # Compare the live list with the same-format t0 inventory, which was not admitted by Track A.
    def rows(data, fmt):
        return Counter(canonical({**asdict(entry), "locator": None,
                                  "first_submission": entry.first_submission and entry.first_submission.isoformat()})
                       for entry in piv_fetch.parse_entries(data, fmt))

    links = collector.retrieve(piv_fetch.PAGE, page=True)
    candidates = [(day, url) for url, label in links or () if (day := piv_fetch.edition_date(label))]
    if not candidates:
        raise ValueError("No dated FDA Paragraph IV download was found")
    latest = max(day for day, _ in candidates)
    for url in sorted({url for day, url in candidates if day == latest}):
        collector.retrieve(url, version=latest)
    editions = sorted(collector.files.values(), key=lambda row: (row["format"] != "xlsx", row["source_url"]))
    if not editions:
        raise ValueError("The latest FDA Paragraph IV list could not be downloaded")
    source = editions[0]
    fmt = source["format"]
    old = max((row for row in read_json(BENCH / "PIV_EDITIONS.json")["editions"]
               if row["format"] == fmt and row["parse_status"] == "PASS"
               and row["version_date"] and row["version_date"] <= "2026-11-27"),
              key=lambda row: row["version_date"])
    pin = private / "piv" / old["file"]
    verify(pin, old["sha256"])
    live = collector.raw / source["file"]
    current_rows = rows(live.read_bytes(), fmt)
    previous_rows = rows(pin.read_bytes(), fmt)
    if not current_rows or not previous_rows:
        raise ValueError("An FDA Paragraph IV edition did not yield inventory rows")
    diff = record_delta(current_rows, previous_rows)
    return dict(filename=f"piv/{live.name}", source_url=source["source_url"], source_version=source["version_date"],
                sha256=source["sha256"], baseline_sha256=old["sha256"],
                baseline_version=old["version_date"], baseline_role="FDA list inventory only", **diff)


def fetch_archives(private, staged, manifest, piv_fetch):
    collector = piv_fetch.Collector(staged / "piv")
    for endpoint, acquire in (
        ("fda_orange_book_zip", lambda: orange_archive(private, staged, collector)),
        ("fda_paragraph_iv", lambda: piv_inventory(private, collector, piv_fetch)),
    ):
        try:
            manifest["files"].append(dict(endpoint=endpoint, **acquire()))
        except (RuntimeError, ValueError, OSError, BadZipFile, ParseError, ZlibError,
                TypeError, KeyError, IndexError) as error:
            manifest["failed_sources"].append(dict(endpoint=endpoint, error_type=type(error).__name__,
                                                   message=str(error)))
    write_json(collector.raw / "acquisition.json", collector.log)


def refresh(private, out, fetcher, fetched_at, *, archive_fetch=None):
    baseline = private / "raw-20261127"
    for reserved in (baseline, private / "trackA", private / "ob_editions", private / "piv", CURRENT):
        if out.resolve().is_relative_to(reserved.resolve()):
            raise ValueError("Refresh output must be outside the Track A t0 inputs and outputs")
    s0 = read_json(BENCH / "S0_INPUT_MANIFEST.json")
    pins = {entry["raw_file"]: entry["sha256"] for entry in s0["files"]}
    plan = [(endpoint, name, query) for endpoint, parts in (
        ("orangebook", fetcher.ORANGEBOOK_PARTS), ("drugsfda", fetcher.DRUGSFDA_PARTS),
    ) for name, query in parts.items()]
    for _, name, _ in plan:
        filename = f"{name}.jsonl"
        verify(baseline / filename, pins[filename])
    out.mkdir(parents=True, exist_ok=True)
    fetched_at = fetched_at.astimezone(timezone.utc)
    target = out / fetched_at.strftime("snapshot-%Y%m%dT%H%M%S%fZ")
    if target.exists():
        raise FileExistsError(f"Snapshot already exists: {target}")
    manifest = dict(schema_version="mwd.refresh.v1", label=LABEL,
                    fetched_at_utc=fetched_at.isoformat(), baseline_t0=s0["t0"],
                    files=[], failed_sources=[])
    with TemporaryDirectory(prefix=".refresh-", dir=out) as stage:
        staged = Path(stage) / "snapshot"
        staged.mkdir()
        for endpoint, name, query in plan:
            filename = f"{name}.jsonl"
            path = staged / filename
            source = dict(endpoint=endpoint, query=query, filename=filename)
            try:
                version, rows = fetch_partition(fetcher, endpoint, query, path)
            except (RuntimeError, ValueError, OSError) as error:
                path.unlink(missing_ok=True)
                manifest["failed_sources"].append(dict(source, error_type=type(error).__name__,
                                                       message=str(error)))
                continue
            with (baseline / filename).open(encoding="utf-8") as stream:
                previous = Counter(canonical(json.loads(line)) for line in stream)
            manifest["files"].append(dict(source, source_version=version, sha256=fetcher.sha256_file(path),
                                          baseline_sha256=pins[filename], **record_delta(rows, previous)))
        if archive_fetch is not None:
            archive_fetch(private, staged, manifest)
        manifest["status"] = "INCOMPLETE" if manifest["failed_sources"] else "COMPLETE"
        write_json(staged / "manifest.json", manifest)
        if target.exists():
            raise FileExistsError(f"Concurrent snapshot already exists: {target}")
        staged.rename(target)
    return target, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="Parent directory for dated snapshots")
    parser.add_argument("--private-root", type=Path, default=PRIVATE)
    args = parser.parse_args()
    sys.path[:0] = [str(ROOT / "loe-bench"), str(ROOT / "loe-bench" / "scripts")]
    from loe_bench import openfda_fetch
    import piv_fetch

    path, manifest = refresh(args.private_root, args.out, openfda_fetch, datetime.now(timezone.utc),
                             archive_fetch=lambda private, staged, receipt:
                             fetch_archives(private, staged, receipt, piv_fetch))
    print(f"{LABEL}: {manifest['status']} · {path}")
    return int(bool(manifest["failed_sources"]))


if __name__ == "__main__":
    raise SystemExit(main())
