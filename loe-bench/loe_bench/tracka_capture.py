"""Capture and restore openFDA source bytes without evaluating any outcomes."""

from dataclasses import replace
from datetime import timedelta
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

from . import tracka_custody as custody
from .tracka_outcomes import ENDPOINTS, INDEX_FILE, FdaSnapshot
from .tracka_release import T0, dump, load, require, verify_file

MANIFEST = "outcome-source-manifest.json"
PARTITION = re.compile(r"(?:drugsfda|orangebook)-\d{4}\.zip")
GRACE = timedelta(days=7)


def build(scope, started, target):
    day = started.date()
    require(scope.maturity <= day <= scope.maturity + GRACE, "Outside the declared Track A capture window")
    with TemporaryDirectory() as temporary:
        folder = Path(temporary)
        snapshot = FdaSnapshot(folder)
        index = snapshot.index()
        editions = {}
        for endpoint in ENDPOINTS:
            _, version, _ = snapshot.records(index, endpoint, scope.maturity if endpoint == "drugsfda" else T0, day)
            editions[endpoint] = version.isoformat()
        for item in snapshot.manifest["sources"]:
            item["bytes"] = (folder / item["file"]).stat().st_size
        dump(folder / MANIFEST, {**snapshot.manifest, "schema": 1, "scope": vars(scope),
                                 "capture_started_utc": started.isoformat(), "editions": editions})
        custody.pack(folder, (item.name for item in folder.iterdir()), target)


def restore(scope, bundle, folder):
    """Verify the archived files and expose the unchanged scorer's replay layout."""
    raw = folder / "sources"
    folder.mkdir()
    custody.unpack(bundle, raw, lambda names: {MANIFEST, INDEX_FILE} <= names
                   and all(PARTITION.fullmatch(name) for name in names - {MANIFEST, INDEX_FILE}))
    manifest_path = folder / MANIFEST
    (raw / MANIFEST).rename(manifest_path)
    manifest = load(manifest_path)
    started = custody.utc_time(manifest["capture_started_utc"])
    require(manifest["schema"] == 1 and manifest["scope"] == vars(scope) and not manifest["missing"]
            and scope.maturity <= started.date() <= scope.maturity + GRACE,
            "Invalid Track A capture scope or admission date")
    files = manifest["sources"]
    names = {item["file"] for item in files}
    require(len(names) == len(files) and names == {item.name for item in raw.iterdir()}
            and all(any(name.startswith(endpoint + "-") for name in names) for endpoint in ENDPOINTS),
            "Track A capture manifest and files differ")
    for item in files:
        path = verify_file(raw, item["file"], item["sha256"])
        require(path.stat().st_size == item["bytes"], "Track A source byte count differs")
    require(manifest["editions"]["drugsfda"] >= scope.maturity.isoformat(),
            "Track A capture does not cover maturity")
    return raw, manifest


def discover(scope, folder, *, query=None):
    scope = replace(scope, kind="capture")
    evidence = custody.inspect(scope, folder, query=query)
    if evidence["status"] == "VERIFIED":
        try:
            raw, manifest = restore(scope, folder / scope.archive, folder / "snapshot")
            started = custody.utc_time(manifest["capture_started_utc"])
            signed = custody.utc_time(evidence["provenance"]["signed_at_utc"])
            require(started <= signed, "Track A capture began after attestation")
            published = custody.utc_time(evidence["published_at_utc"]).date()
            return raw, {**evidence, "capture_started_utc": started.isoformat(), "editions": manifest["editions"],
                         "source_sha256": {item["file"]: item["sha256"] for item in manifest["sources"]},
                         "capture_late": started.date() > scope.maturity,
                         "publication_late": published > scope.maturity}
        except (OSError, KeyError, TypeError, ValueError, BadZipFile) as exc:
            evidence.update(status=custody.HOLD, detail=str(exc))
    return None, {**evidence, "status": custody.HOLD}
