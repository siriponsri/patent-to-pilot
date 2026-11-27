"""Reproduce the T2 development summary using verified local FDA source files."""
import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from loe_bench import t2
from loe_bench.common import add_months
from loe_bench.dataset import build_entities, build_samples
from loe_bench.ob_history import DEFAULT_DIR, OBHistory
from loe_bench.seal import TEST_FIRST, require_cutoffs
from loe_bench.t2_features import AsOfBuilder, edition_coverage


def _verify(path, expected):
    with path.open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f"SHA-256 mismatch for {path.name}")


def _manifest(path):
    content = path.read_bytes()
    return json.loads(content), {"file": path.name, "sha256": hashlib.sha256(content).hexdigest()}


def run(raw, ob_dir, ob_manifest):
    splits = {h: t2.development_split(h) for h in t2.HORIZONS}
    cutoffs = sorted({d for train, validation in splits.values() for d in (*train, *validation)})
    require_cutoffs(cutoffs)
    source_manifest, s0_ref = _manifest(ROOT / "data" / "S0_INPUT_MANIFEST.json")
    data_end = date.fromisoformat(source_manifest["t0"])
    source_files = {item["raw_file"]: item["sha256"] for item in source_manifest["files"]}
    raw_hashes = {name: source_files[name] for name in ("df_nda.jsonl", "df_anda.jsonl")}
    for name, sha in raw_hashes.items():
        _verify(raw / name, sha)

    editions, ob_ref = _manifest(ob_manifest)
    history = OBHistory.from_manifest(str(ob_manifest), str(ob_dir))
    coverage = {cutoff.isoformat(): edition_coverage(history, cutoff) for cutoff in cutoffs}
    by_date = {entry["edition_date"]: entry for entry in editions["editions"]}
    selected = sorted({item["latest_edition"] for item in coverage.values() if item["status"] == "FRESH"})
    edition_hashes = {}
    for when in selected:
        entry = by_date[when]
        _verify(ob_dir / entry["file"], entry["sha256"])
        edition_hashes[when] = {field: entry[field] for field in ("file", "sha256", "source_url")}

    builder = AsOfBuilder(history)
    entities = build_entities(str(raw))
    results = {}
    for horizon, (train_cutoffs, val_cutoffs) in splits.items():
        result = {
            "train_cutoffs": [d.isoformat() for d in train_cutoffs],
            "validation_cutoffs": [d.isoformat() for d in val_cutoffs],
            "sealed_test_start": TEST_FIRST.isoformat(),
        }
        results[str(horizon)] = result
        if not train_cutoffs:
            result.update(status="NOT_RUN", reason="No non-empty train/validation split satisfies strict embargo.")
            continue
        if add_months(val_cutoffs[-1], horizon) > data_end:
            raise ValueError("Verified source does not observe the entire validation window")
        partitions = []
        for dates in (train_cutoffs, val_cutoffs):
            rows = build_samples(entities, dates, horizon, data_end, only_nme=True)
            counts = {cutoff.isoformat(): Counter() for cutoff in dates}
            for row in rows:
                row["asof"] = builder.build(row["key"], row["t"], horizon, row["x"])
                counts[row["t"].isoformat()][row["asof"].edition_status] += 1
            partitions.append((rows, counts))
        (train, train_counts), (validation, val_counts) = partitions
        result.update(status="DEVELOPMENT_ONLY", train_rows=len(train),
                      row_coverage_by_cutoff={**train_counts, **val_counts},
                      **t2.evaluate(train, validation, horizon))

    return {
        "scope": "T2 development only. No protected cutoffs built or scored.",
        "input_sha256": {"s0_manifest": s0_ref, "drugs_fda": raw_hashes,
                         "ob_manifest": ob_ref, "used_edition_zips_by_date": edition_hashes},
        "edition_coverage": coverage,
        "protocol": {"coverage_target": t2.COMMON_COVERAGE, "lo": t2.LO, "hi": t2.HI,
                     "drug_key_calibration_folds": t2.FOLDS, "bootstrap_draws": t2.BOOTSTRAP_DRAWS,
                     "bootstrap_seed": t2.BOOTSTRAP_SEED, "useful_delta_at_most": -0.01},
        "horizons": results,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True, help="Directory with S0 Drugs@FDA JSONL files")
    parser.add_argument("--ob-dir", type=Path, default=Path(DEFAULT_DIR))
    parser.add_argument("--ob-manifest", type=Path, default=ROOT / "data" / "OB_EDITIONS.json")
    args = parser.parse_args()
    summary = run(args.raw, args.ob_dir, args.ob_manifest)
    output = ROOT / "data" / "T2_dev_summary.json"
    output.write_text(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
