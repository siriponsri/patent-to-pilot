"""Read only frozen development scores and the benchmark's guarded evidence projections."""

from collections import Counter, defaultdict
from datetime import date
import gzip
from hashlib import file_digest
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

from .contract import BENCH, ROOT, SCHEDULE, read_json

PRIVATE = Path("C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench")
SCORE_FILES = {12: "FREEZE_dev_scores_12m.json", 24: "FREEZE_dev_scores.json"}


def verify(path, expected):
    with path.open("rb") as stream:
        if file_digest(stream, "sha256").hexdigest() != expected:
            raise ValueError(f"SHA-256 mismatch: {path.name}")


def scores(root):
    manifest = read_json(BENCH / "FREEZE_DEV_SCORES_MANIFEST.json")
    result = {}
    for horizon, dates in SCHEDULE.items():
        pin = manifest["exports"][str(horizon)]
        path = root / SCORE_FILES[horizon]
        verify(path, pin["sha256"])
        data = read_json(path)
        rows = data["rows"]
        if (data["status"] != "DEVELOPMENT_ONLY" or data["prediction_horizon_months"] != horizon
                or data["frozen_config_sha256"] != manifest["frozen_config_sha256"]
                or set(pin["cutoff_rows"]) != set(dates)
                or Counter(row["cutoff"] for row in rows) != pin["cutoff_rows"]
                or len({(row["cutoff"], row["key"]) for row in rows}) != len(rows)
                or any(not 0 <= row[arm] <= 1 for row in rows for arm in ("M3", "B1"))):
            raise ValueError(f"Invalid frozen {horizon}-month development export")
        for day in dates:
            result[day, horizon] = sorted((row for row in rows if row["cutoff"] == day),
                                           key=lambda row: (-row["M3"], row["key"]))
    return result, manifest


def gsrs_names(path, keys):
    required = {part[2:] for key in keys for part in key.split("|") if part.startswith("U:")}
    names = {}
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            record = json.loads(line.split("\t", 2)[-1])
            code = record.get("approvalID")
            if code not in required:
                continue
            candidates = [(not item.get("displayName"), not item.get("preferred"), name)
                          for item in record.get("names", [])
                          if (name := " ".join((item.get("name") or "").split()))]
            if not candidates or code in names:
                raise ValueError(f"Missing or ambiguous GSRS name for {code}")
            names[code] = min(candidates)[2]
    return {key: " + ".join(names[part[2:]] if part.startswith("U:") else part.removeprefix("E:")
                             for part in key.split("|")) for key in keys}


class Evidence:
    def __init__(self, root, keys):
        # C3 supplies an audited byte projection that leaves later ANDA actions out.
        sys.path[:0] = [str(ROOT / "loe-bench"), str(ROOT / "loe-bench" / "scripts")]
        import c3_dev_run
        from devx_run import OB_HISTORICAL, application_identity_reader, historical_orange_reader
        from loe_bench import moiety, ob_linkage
        from loe_bench.ob_history import OBHistory
        from loe_bench.t2_features import _EditionIndex

        if "LOE_PREREG_SHA256" in os.environ:
            raise ValueError("The dossier builder requires a development-only process")
        raw = root / "raw-20261127"
        gsrs = root / "moiety" / moiety.GSRS_FILE
        verify(gsrs, moiety.GSRS_SHA256)
        self.root = root
        self.gsrs_pin = moiety.GSRS_SHA256
        self.names = gsrs_names(gsrs, keys)
        self.entities, approvals, _, _, _, _ = c3_dev_run._inputs(raw)
        self.approvals = defaultdict(list)
        for approval in sorted(approvals, key=lambda item: (item.approved, item.application)):
            self.approvals[approval.group].append(approval)
        def projected(path, fallback):
            return c3_dev_run.nda_reader(path, fallback, projector=c3_dev_run.t4_power,
                                         redact_dates=c3_dev_run.without_later_approvals)

        with (patch.object(moiety, "ORANGE_FILES", OB_HISTORICAL),
              patch.object(moiety, "read_jsonl", lambda path: projected(path, historical_orange_reader)),
              patch.object(ob_linkage, "read_jsonl", lambda path: projected(path, application_identity_reader))):
            self.linker = ob_linkage.HistoricalMoietyLinker(raw, self.entities, gsrs_path=gsrs)

        archive = read_json(BENCH / "OB_EDITIONS.json")
        self.ob_entries = {item["sha256"]: item for item in archive["editions"]}
        history = OBHistory.from_records(archive, str(root / "ob_editions"))
        self.editions = {}
        loaded = {}
        for day in sorted({day for dates in SCHEDULE.values() for day in dates}):
            entry, proof = history.available_source_asof(date.fromisoformat(day))
            if entry is None:
                continue
            digest = entry.identity["sha256"]
            if digest not in loaded:
                verify(root / "ob_editions" / entry.identity["file"], digest)
                loaded[digest] = _EditionIndex(history.load_source(entry), linker=self.linker)
            self.editions[day] = (entry.identity, proof, loaded[digest])

        self.piv_entries = {item["sha256"]: item for item in read_json(BENCH / "PIV_EDITIONS.json")["editions"]}
        self.witnesses = read_json(BENCH / "E7_witnesses.json")
        self.patent_witnesses = read_json(BENCH / "E7b_patent_witnesses.json")
        self.s0 = read_json(BENCH / "S0_INPUT_MANIFEST.json")
        self.development_anda_pin = next(row["sha256"] for row in self.s0["files"]
                                         if row["raw_file"] == "df_anda.jsonl")

    def listing(self, cutoff, key):
        edition = self.editions.get(cutoff)
        if edition is None:
            return None, [], [], []
        identity, proof, index = edition
        key = self.linker.canonical(key)
        patents, exclusivities = index.records(key)
        return (identity, proof, index.edition.edition_date.isoformat()), (
            index.linked_products[key]), patents or [], exclusivities or []

    def challenges(self, cutoff, key):
        # The development receipts preserve exact rows and point-in-time admissions.
        fda = [w for w in self.witnesses.get(cutoff, {}).get(key, ()) if w["source"] == "FDA_PIV"
               and w["date"] <= cutoff and self.piv_date(w) <= cutoff]
        court = [w for w in self.patent_witnesses.get(key, ()) if w["date"] <= cutoff
                 and any(m["orange_book"]["availability_proof"]["date"] <= w["date"]
                         for m in w["corroboration"]["matches"])]
        return fda + court

    def piv_date(self, witness):
        stamp = self.piv_entries[witness["sha256"]]["wayback_timestamp"]
        return f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:8]}"
