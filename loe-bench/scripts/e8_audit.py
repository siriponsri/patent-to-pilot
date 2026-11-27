"""Audit annual Orange Book source coverage, identity linkage and ZIP overlap."""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loe_bench.common import add_months
from loe_bench.dataset import build_entities
from loe_bench.moiety import GSRS_FILE, GSRS_SHA256, ORANGE_FILES
from loe_bench.nber_ob import DEFAULT_NBER_DIR, nber_sources
from loe_bench.ob_history import DEFAULT_DIR, OBHistory, load_edition, zip_edition_date
from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.ob_overlap import compare_editions
from loe_bench.seal import TEST_FIRST
from loe_bench.t2 import development_split
from loe_bench.t2_features import AsOfBuilder, edition_coverage
from t2_dev_run import _manifest, _verify


def _cutoff_row(history, baseline, year):
    cutoff = date(year, 1, 1)
    coverage = edition_coverage(history, cutoff)
    source, proof = history.available_source_asof(cutoff)
    current_through = proof.get("edition_context", {}).get("current_through") if proof else None
    return dict(cutoff=cutoff.isoformat(), **coverage,
                documented_content_age_days=(cutoff - date.fromisoformat(current_through)).days
                if current_through else None,
                latest_admissible_source=source.identity if source else None,
                zip_only_status=edition_coverage(baseline, cutoff)["status"])


def _training_opportunities(coverage):
    new_fresh = [
        date.fromisoformat(row["cutoff"]) for row in coverage
        if row["status"] == "FRESH" and row["zip_only_status"] != "FRESH"
        and date.fromisoformat(row["cutoff"]) < TEST_FIRST
    ]
    windows = {}
    for horizon in (12, 24, 36):
        _, validation = development_split(horizon)
        # For 36 months use the latest permissible validation start as a prospective example.
        first = validation[0] if validation else add_months(TEST_FIRST, -horizon - 12)
        windows[str(horizon)] = {
            "validation_start": first.isoformat(),
            "validation_start_basis": "T2b" if validation else "illustrative seal-compatible boundary",
            "added_training_cutoffs": [d.isoformat() for d in new_fresh if add_months(d, horizon) < first],
        }
    return {"new_fresh_development_cutoffs": [d.isoformat() for d in new_fresh], "windows": windows}


def _overlap(annual, zip_manifest, ob_dir, linker):
    records = [(date.fromisoformat(row["edition_date"]), row) for row in zip_manifest["editions"]]
    loaded, result = {}, []
    for year in range(2009, 2017):
        same_year = [(day, row) for day, row in records if day.year == year]
        reference = date(year - 1, 12, 31)
        near = [(day, row) for day, row in records if abs((day - reference).days) <= 120]
        for pairing, candidates in (("same_edition_year", same_year), ("near_prior_year_end", near)):
            if not candidates:
                result.append(dict(year=year, pairing=pairing, status="NOT_RUN", reason="no inventory ZIP"))
                continue
            day, row = (max(candidates, key=lambda item: item[0]) if pairing == "same_edition_year"
                        else min(candidates, key=lambda item: (abs((item[0] - reference).days), item[0])))
            name = row["file"]
            if name not in loaded:
                path = ob_dir / name
                loaded[name] = load_edition(path, day)
            result.append(dict(year=year, pairing=pairing, status="MEASURED", zip_date=day.isoformat(),
                               zip_source={k: row[k] for k in ("file", "source_url", "sha256", "wayback_ts")},
                               **compare_editions(annual[year], loaded[name], linker.application_type)))
    return result


def audit(raw, ob_dir, nber_dir):
    s0, s0_ref = _manifest(ROOT / "data/S0_INPUT_MANIFEST.json")
    zip_manifest, zip_ref = _manifest(ROOT / "data/OB_EDITIONS.json")
    nber, nber_ref = _manifest(ROOT / "data/E8_NBER_MANIFEST.json")
    verified = {}
    for item in s0["files"]:
        name = item["raw_file"]
        if name in ("df_nda.jsonl", "df_anda.jsonl", *ORANGE_FILES):
            _verify(raw / name, item["sha256"])
            verified[name] = item["sha256"]
    gsrs = raw.parent / "moiety" / GSRS_FILE
    _verify(gsrs, GSRS_SHA256)
    for entry in zip_manifest["editions"]:
        path = ob_dir / entry["file"]
        _verify(path, entry["sha256"])
        if zip_edition_date(path).isoformat() != entry["edition_date"]:
            raise ValueError(f"Edition date mismatch for {path.name}")
    entities = build_entities(raw, gsrs_path=gsrs, include_anda_outcomes=False)
    linker = HistoricalMoietyLinker(raw, entities, gsrs_path=gsrs)
    baseline = OBHistory.from_records(zip_manifest, str(ob_dir))
    history = OBHistory.from_records(zip_manifest, str(ob_dir), nber_manifest=nber, nber_dir=nber_dir)
    coverage = [_cutoff_row(history, baseline, year) for year in range(1987, 2026)]
    annual = {source.identity["edition_year"]: history.load_source(source)
              for source in nber_sources(nber, nber_dir)}
    builder = AsOfBuilder(history, linker=linker)
    linkage = {}
    for year, edition in annual.items():
        counts = builder.edition_linkage(edition)
        total = counts["nda_applications"]
        linkage[year] = dict(counts, nda_link_rate=counts["linked_nda_applications"] / total if total else None)
    return {
        "inputs": {"manifest": nber_ref, "zip_manifest": zip_ref, "s0": s0_ref,
                   "identity_files": verified, GSRS_FILE: GSRS_SHA256},
        "scope": "Public source inventory and NDA identity linkage; no outcome derivation or metrics.",
        "coverage": coverage,
        "nda_linkage": linkage,
        "overlap": _overlap(annual, zip_manifest, ob_dir, linker),
        "development_opportunities": _training_opportunities(coverage),
    }


if __name__ == "__main__":
    cmd = argparse.ArgumentParser(description=__doc__)
    cmd.add_argument("--raw", type=Path, default=Path(DEFAULT_DIR).parent / "raw-20261127")
    cmd.add_argument("--ob-dir", type=Path, default=Path(DEFAULT_DIR))
    cmd.add_argument("--nber-dir", type=Path, default=DEFAULT_NBER_DIR)
    cmd.add_argument("--out", type=Path, default=ROOT / "data/E8_AUDIT.json")
    args = cmd.parse_args()
    result = audit(args.raw, args.ob_dir, args.nber_dir)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
