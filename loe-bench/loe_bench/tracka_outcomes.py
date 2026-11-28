"""Capture and validate dated FDA bulk exports and derive original ANDA outcomes."""

from collections import Counter, defaultdict
from datetime import date, datetime, timezone
import io
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import BadZipFile, ZipFile

from .common import parse_yyyymmdd
from .dataset import _final_originals, _original_compositions, _original_products
from .moiety import Registry, orange_products
from .moiety_linkage import MoietyLinkage
from .tracka_release import IDENTITY, T0, digest, load, require, verify_file

INDEX_URL = "https://api.fda.gov/download.json"
INDEX_FILE = "fda-download-index.json"
ENDPOINTS = ("drugsfda", "orangebook")
APP = re.compile(r"ANDA\d{6}")


def fetch_bytes(url, limit, expected_host):
    with urlopen(url, timeout=60) as response:
        require(response.url.startswith(f"https://{expected_host}/"), "Unexpected download host")
        data = response.read(limit + 1)
    require(len(data) <= limit, "Download exceeded size limit")
    return data


class FdaSnapshot:
    def __init__(self, folder, replay=None):
        self.folder = folder
        self.replay = replay
        self.manifest = {"sources": [], "missing": []}

    def capture(self, name, url, limit, host):
        path = self.folder / name
        if self.replay is None:
            started = datetime.now(timezone.utc).isoformat()
            path.write_bytes(fetch_bytes(url, limit, host))
        else:
            matches = [item for item in self.previous["sources"] if item["file"] == name and item["url"] == url]
            require(len(matches) == 1, f"Missing archived file entry: {name}")
            original = verify_file(self.replay, name, matches[0]["sha256"])
            require(original.stat().st_size <= limit, f"Archived file exceeds limit: {name}")
            started = matches[0]["fetched_at_utc"]
            path.write_bytes(original.read_bytes())
        entry = {"file": name, "url": url, "fetched_at_utc": started, "sha256": digest(path)}
        self.manifest["sources"].append(entry)
        return path, entry

    def index(self):
        if self.replay is not None:
            self.previous = load(self.replay.parent / "outcome-source-manifest.json")
        path, entry = self.capture(INDEX_FILE, INDEX_URL, 16 * 1024**2, "api.fda.gov")
        index = load(path)
        entry["version"] = {name: index["results"]["drug"][name]["export_date"] for name in ENDPOINTS
                            if name in index["results"]["drug"]}
        return index["results"]["drug"]

    def records(self, index, endpoint, required_through, today):
        source = index[endpoint]
        version = date.fromisoformat(source["export_date"])
        require(required_through <= version <= today,
                f"{endpoint} edition {version} does not establish coverage through {required_through}")
        partitions = source["partitions"]
        total = source["total_records"]
        require(partitions and total > 0 and sum(part["records"] for part in partitions) == total,
                f"{endpoint} index is missing partitions or counts")
        records, names, locators = [], set(), {}
        for i, part in enumerate(partitions, start=1):
            url = part["file"]
            prefix = f"https://download.open.fda.gov/drug/{endpoint}/"
            require(url.startswith(prefix) and re.fullmatch(r"[A-Za-z0-9_.-]+\.json\.zip", url[len(prefix):])
                    and url not in names, f"Unexpected or duplicate {endpoint} partition")
            names.add(url)
            path, entry = self.capture(f"{endpoint}-{i:04d}.zip", url, 128 * 1024**2, "download.open.fda.gov")
            with ZipFile(path) as archive:
                member, = archive.infolist()
                require(member.filename.endswith(".json") and member.file_size <= 512 * 1024**2,
                        f"Unexpected {endpoint} ZIP member")
                with archive.open(member) as stream:
                    payload = json.load(io.TextIOWrapper(stream, encoding="utf-8"))
            meta = payload["meta"]
            entry.update(version=meta["last_updated"], records=len(payload["results"]), member=member.filename)
            require(date.fromisoformat(meta["last_updated"]) == version
                    and meta["results"]["total"] == total and meta["results"]["skip"] == len(records)
                    and len(payload["results"]) == part["records"],
                    f"{endpoint} partition date, order or record count disagrees with the index")
            if endpoint == "drugsfda":
                for row in payload["results"]:
                    locators[row["application_number"]] = {k: entry[k] for k in ("file", "member", "version", "sha256")}
            records.extend(payload["results"])
        return records, version, locators


def resolve_first_approvals(records, identities, keys, end, orange=None):
    registry = Registry()
    registry.aliases = {name: set(codes) for name, codes in identities["registry_aliases"].items()}
    registry.targets = identities["registry_targets"]
    linkage = MoietyLinkage(identities["fix2c_aliases"], ())
    first, witnesses, missing = {}, {}, []
    counts = Counter()
    seen = set()
    s0_final = set(identities["s0_final_anda_apps"])
    orange = orange or {}
    orange_by_app = defaultdict(list)
    for (application, number), (product, day) in orange.items():
        if day is not None:
            orange_by_app[application].append((product, day))
    for record in records:
        app = record["application_number"]
        if not app.startswith("ANDA"):
            continue
        require(APP.fullmatch(app) and app not in seen, f"Missing or duplicate Drugs@FDA ANDA identifier: {app}")
        seen.add(app)
        originals = list(_final_originals(record))
        approved = min((day for day, _ in originals), default=None)
        undated = any(s.get("submission_type") == "ORIG" and s.get("submission_status") == "AP"
                      and parse_yyyymmdd(s.get("submission_status_date")) is None
                      for s in record.get("submissions") or [])
        if app in s0_final:
            counts["frozen_pre_t0_anda"] += 1
            if approved is not None and T0 < approved <= end:
                counts["post_t0_date_for_known_s0_anda"] += 1
            continue
        if undated and (approved is None or approved > T0):
            missing.append(f"{app}: undated final original approval")
        if approved is None or approved > end:
            continue
        products = _original_products(record, approved)
        if not products and approved > T0:
            # A dated Orange Book product can supply missing product identity.
            # The event date and the required final original action come from Drugs@FDA.
            proxies = [dict(product, approval_date=day.strftime("%Y%m%d"))
                       for product, day in orange_by_app[app] if day <= approved]
            if proxies:
                record = dict(record, products=proxies)
                products = _original_products(record, approved)
        compositions = list(_original_compositions(record, approved, registry, orange, linkage))
        if approved > T0:
            counts["in_window_original_anda"] += 1
            if not compositions or any(predate is None for _, predate, _ in compositions):
                missing.append(f"{app}: missing or ambiguous original composition")
            elif any(not p.get("active_ingredients") and
                     (app, str(p.get("product_number") or "").zfill(3)) not in orange
                     for p in products):
                missing.append(f"{app}: missing active ingredients for an original product")
        matched = False
        for key, day, low in compositions:
            if key not in keys or day is None:
                continue
            matched = True
            counts["low_confidence_matches"] += int(low)
            if day <= T0:
                missing.append(f"{app}: later snapshot places an original approval at or before t0 for a frozen key")
            elif key not in first or (day, app) < (first[key], witnesses[key]["locator"]):
                first[key] = day
                witnesses[key] = {"source": "drugsfda", "locator": app, "approval_date": day.isoformat()}
        if approved > T0:
            counts["linked_anda" if matched else "unmatched_anda"] += 1
    require(bool(seen), "Drugs@FDA export contains no ANDA records")
    return first, witnesses, dict(counts), missing


def fetch_outcomes(release, end, today, folder, replay=None):
    snapshot = FdaSnapshot(folder, replay)
    missing = snapshot.manifest["missing"]
    endpoint = "openFDA index"
    try:
        index = snapshot.index()
        endpoint = "Drugs@FDA"
        records, version, locators = snapshot.records(index, "drugsfda", end, today)
        identities = load(release.folder / IDENTITY)
        require(set(identities["roster_nda_ids"]) == set(release.keys), "Frozen outcome identity roster differs")
        first, witnesses, counts, gaps = resolve_first_approvals(records, identities, set(release.keys), end)
        if any("composition" in gap or "ingredients" in gap for gap in gaps):
            endpoint = "Orange Book"
            # Orange Book supplies product identity and dates. The event remains
            # the Drugs@FDA original final action, even when identity needs help.
            orange_rows, _, _ = snapshot.records(index, "orangebook", end, today)
            with TemporaryDirectory() as temporary:
                path = Path(temporary) / "ob_anda_2020plus.jsonl"
                with path.open("w", encoding="utf-8") as stream:
                    for row in orange_rows:
                        stream.write(json.dumps(row) + "\n")
                orange = orange_products(temporary)
            first, witnesses, counts, gaps = resolve_first_approvals(records, identities, set(release.keys), end, orange)
        missing.extend(gaps)
        snapshot.manifest.update(covered_from_exclusive=T0.isoformat(), covered_through=version.isoformat(),
                                 identity_audit=counts)
        if not missing:
            for witness in witnesses.values():
                witness.update(locators[witness["locator"]])
            return snapshot.manifest, first, witnesses
    except (OSError, KeyError, TypeError, ValueError, BadZipFile) as exc:
        missing.append(f"{endpoint}: {exc}")
    return snapshot.manifest, None, None
