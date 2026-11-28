from datetime import date, datetime, timezone
from hashlib import sha256
from io import BytesIO
import json
from math import fsum
from types import SimpleNamespace
from zipfile import ZipFile, ZipInfo

import pytest

from product.mwd import current, refresh
from product.mwd.contract import CURRENT, ROOT, read_json


def test_native_score_tie_shares_boundary_without_lexical_selection():
    native = (0.4, 0.4, 0.4, 0.2, 0.1)
    rows = [dict(key=key, arms={"M3": dict(native=m3, queue_inclusion_probability=1 / 3 if m3 == 0.4 else 0),
                                "B1": {"native": 0.25}, "M1": {"native": 0.5}})
            for key, m3 in zip("cbade", native, strict=True)]
    names = {row["key"]: row["key"].upper() for row in rows}
    priors = {key: {arm: {"native": 0.75} for arm in current.PRIOR_ARMS} for key in names}
    ranked, boundary = current.ranked_rows(rows, priors, names)
    assert [row["key"] for row in ranked] == list("abcde")
    assert [row["m3_rank"] for row in ranked] == [1, 1, 1, 4, 5]
    assert [row["queue_inclusion_probability"] for row in ranked] == [1 / 3] * 3 + [0, 0]
    assert not any(row["in_queue"] for row in ranked)
    assert boundary == dict(capacity=1, boundary_native_score=0.4, above_boundary=0,
                            boundary_rows=3, slots_at_boundary=1, boundary_inclusion_probability=1 / 3)
    rows[0]["arms"]["M3"]["queue_inclusion_probability"] = 1
    with pytest.raises(ValueError, match="inclusion probability"):
        current.ranked_rows(rows, priors, names)


def test_aligned_rows_reject_wrong_cutoff_roster_and_outcome():
    row = dict(key="test", t0="2026-11-27", horizon_months=12)
    assert current.aligned_rows([row], 12, ["test"]) == [row]
    for bad in ({**row, "t0": "2026-11-28"}, {**row, "key": "wrong"}, {**row, "event": False}):
        with pytest.raises(ValueError, match="Invalid"):
            current.aligned_rows([bad], 12, ["test"])


def test_verify_checksums_before_parsing_package(tmp_path):
    (tmp_path / "SHA256SUMS").write_text(f"{'0' * 64}  {current.CORE}\n", encoding="ascii")
    (tmp_path / current.CORE).write_text("invalid JSON", encoding="ascii")
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        current.verified_package(tmp_path)


def test_release_version_requires_tagged_manifest_binding_inputs(monkeypatch, tmp_path):
    prior = tmp_path / "PRIORARMS_MANIFEST.json"
    prior.write_text('{"files_sha256": {"prior.jsonl": "' + "1" * 64 + '"}}', encoding="ascii")
    monkeypatch.setattr(current, "BENCH", tmp_path)
    pins = {current.CORE: "0" * 64}
    release = json.dumps({"inputs": {current.CORE: "0" * 64, "prior.jsonl": "1" * 64}}).encode()
    tag = "track-a-fixture"
    path = "loe-bench/data/TRACKA_RELEASE.json"

    def git(*args):
        assert args == ("show", f"refs/tags/{tag}:{path}")
        return release

    core = SimpleNamespace(git=git)
    assert current.freeze_version(core, pins)["freeze"] == "pending"
    assert current.freeze_version(core, pins, tag, path) == {
        "freeze": "verified", "tag": tag, "manifest_sha256": sha256(release).hexdigest(),
        "core_manifest_sha256": pins[current.CORE],
    }
    with pytest.raises(ValueError, match="does not bind"):
        current.freeze_version(core, {current.CORE: "2" * 64}, tag, path)


def test_refresh_labels_versions_diffs_and_failed_partition(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "loe-bench"))
    from loe_bench import openfda_fetch

    monkeypatch.setattr(openfda_fetch, "ORANGEBOOK_PARTS", {"ob_nda": "example"})
    monkeypatch.setattr(openfda_fetch, "DRUGSFDA_PARTS", {"df_nda": "example"})
    raw = tmp_path / "raw-20261127"
    raw.mkdir()
    old = b'{"id": 1}\n{"id": 2}\n'
    pins = []
    for name in ("ob_nda.jsonl", "df_nda.jsonl"):
        (raw / name).write_bytes(old)
        pins.append(dict(raw_file=name, sha256=sha256(old).hexdigest()))
    monkeypatch.setattr(refresh, "read_json", lambda path: {"files": pins, "t0": "2026-11-27"})

    def get(url):
        assert "api_key=" not in url
        if "drugsfda" in url:
            raise RuntimeError("Fixture source unavailable")
        return {"meta": {"last_updated": "2026-11-28", "results": {"total": 3}},
                "results": [{"id": 2}, {"id": 3}, {"id": 3}]}

    monkeypatch.setattr(openfda_fetch, "_get", get)
    stamp = datetime(2026, 11, 28, tzinfo=timezone.utc)
    path, manifest = refresh.refresh(tmp_path, tmp_path / "snapshots", openfda_fetch, stamp)
    assert manifest["label"] == "unregistered forecast" and manifest["status"] == "INCOMPLETE"
    assert manifest["fetched_at_utc"] == stamp.isoformat()
    observed, = manifest["files"]
    assert observed["source_version"] == "2026-11-28"
    assert (observed["rows_added"], observed["rows_removed"]) == (2, 1)
    assert observed["sha256"] == sha256((path / "ob_nda.jsonl").read_bytes()).hexdigest()
    failure, = manifest["failed_sources"]
    assert failure["filename"] == "df_nda.jsonl" and not (path / "df_nda.jsonl").exists()
    assert (raw / "ob_nda.jsonl").read_bytes() == old
    assert read_json(path / "manifest.json") == manifest
    with pytest.raises(FileExistsError):
        refresh.refresh(tmp_path, tmp_path / "snapshots", openfda_fetch, stamp)
    with pytest.raises(ValueError, match="outside"):
        refresh.refresh(tmp_path, raw, openfda_fetch, stamp)


def test_refresh_rejects_incomplete_results(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "loe-bench"))
    from loe_bench import openfda_fetch

    monkeypatch.setattr(openfda_fetch, "_get", lambda url: {
        "meta": {"last_updated": "2026-11-28", "results": {"total": 2}}, "results": [{"id": 1}]})
    with pytest.raises(ValueError, match="Incomplete"):
        refresh.fetch_partition(openfda_fetch, "orangebook", "example", tmp_path / "rows.jsonl")


def test_refresh_archive_inventory_deltas_are_fenced_from_t0(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "loe-bench"))
    monkeypatch.syspath_prepend(str(ROOT / "loe-bench" / "scripts"))
    from loe_bench.piv_history import PIVEntry
    import piv_fetch

    def orange(day, name):
        output = BytesIO()
        with ZipFile(output, "w") as zipped:
            for table in ("products", "patent", "exclusivity"):
                zipped.writestr(ZipInfo(f"{table}.txt", (*day, 0, 0, 0)), f"header\n{name}\n")
        return output.getvalue()

    old_ob = orange((2026, 7, 10), "old")
    new_ob = orange((2026, 11, 28), "new")
    old_piv = b"old"
    for directory, filename, data in (
        ("ob_editions", "baseline.zip", old_ob), ("piv", "baseline.xlsx", old_piv),
    ):
        (tmp_path / directory).mkdir()
        (tmp_path / directory / filename).write_bytes(data)

    manifests = {
        "TRACKA_CORE_MANIFEST.json": {"edition_audit": {"2026-11-27": {"orange_book": {"source": {
            "file": "baseline.zip", "sha256": sha256(old_ob).hexdigest(), "source_url": "https://example.com/ob",
        }}}}},
        "PIV_EDITIONS.json": {"editions": [dict(file="baseline.xlsx", format="xlsx", parse_status="PASS",
                                               version_date="2026-10-27", sha256=sha256(old_piv).hexdigest())]},
    }
    monkeypatch.setattr(refresh, "read_json", lambda path: manifests[path.name])

    class FixtureCollector(piv_fetch.Collector):
        def request(self, url):
            if url == "https://example.com/ob":
                return new_ob, {}
            if url == piv_fetch.PAGE:
                return (b'<html><a href="/media/123/download">Paragraph IV November 28, 2026</a>', {})
            assert url == "https://www.fda.gov/media/123/download"
            return b"PK\x03\x04new", {}

    monkeypatch.setattr(piv_fetch, "Collector", FixtureCollector)
    monkeypatch.setattr(piv_fetch, "parse_entries", lambda data, fmt: [
        PIVEntry(data.removeprefix(b"PK\x03\x04").decode(), "tablet", "", None, date(2026, 11, 27), "row 1"),
    ])
    staged = tmp_path / "snapshot"
    staged.mkdir()
    result = {"files": [], "failed_sources": []}
    refresh.fetch_archives(tmp_path, staged, result, piv_fetch)
    assert not result["failed_sources"]
    ob, piv = result["files"]
    assert ob["source_version"] == piv["source_version"] == "2026-11-28"
    assert (ob["rows_added"], ob["rows_removed"]) == (3, 3)
    assert (piv["rows_added"], piv["rows_removed"]) == (1, 1)
    assert piv["baseline_role"] == "FDA list inventory only"
    assert (tmp_path / "ob_editions" / "baseline.zip").read_bytes() == old_ob
    assert (tmp_path / "piv" / "baseline.xlsx").read_bytes() == old_piv


@pytest.mark.skipif(not CURRENT.is_dir(), reason="Private Track A output is generated locally")
def test_current_index_queues_and_dossiers_agree():
    index = read_json(CURRENT / "index.json")
    assert len(index["dossiers"]) == 651 and len(index["queues"]) == 2
    paths = {entry["key"]: entry["path"] for entry in index["dossiers"]}
    dossiers = {key: read_json(CURRENT / path) for key, path in paths.items()}
    assert len(paths) == 651
    assert sum(d["challenge_state"] == "UNKNOWN" for d in dossiers.values()) == 628
    for file in index["queues"]:
        queue = read_json(CURRENT / file["path"])
        assert len(queue["ranked_rows"]) == len(paths)
        assert fsum(r["queue_inclusion_probability"] for r in queue["ranked_rows"]) == 130
        for row in queue["ranked_rows"]:
            key = row["key"]
            dossier = dossiers[key]
            forecast = dossier["forecast" if file["horizon_months"] == 24 else "forecast_12m"]
            assert "event" not in row and "outcome_reveal" not in dossier
            assert row["dossier_path"] == paths[key]
            assert row["m3_p"] == forecast["m3_p_entry"]
            assert row["m3_rank"] == forecast["m3_rank"]
            assert row["queue_inclusion_probability"] == forecast["queue_inclusion_probability"]
            assert index["version"] == queue["version"] == dossier["version"]
