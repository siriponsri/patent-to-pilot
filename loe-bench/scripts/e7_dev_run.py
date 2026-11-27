"""Run E7 on FIX2c development splits and export the as-of witness audit."""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import date
import json
from pathlib import Path

from t2_dev_run import ROOT, _manifest, _verify
from loe_bench import t2
from loe_bench.challenge import ChallengeHistory, ChallengeIdentity, court_rows
from loe_bench.common import add_months, parse_yyyymmdd, read_jsonl
from loe_bench.dataset import build_entities, build_samples
from loe_bench.kleene import T3
from loe_bench.moiety import GSRS_FILE, GSRS_SHA256, ORANGE_FILES, orange_products
from loe_bench.ob_history import DEFAULT_DIR, OBHistory, norm_appl_no
from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.piv_history import EntityMatcher, PIVHistory
from loe_bench.seal import TEST_FIRST
from loe_bench.t2_features import AsOfBuilder, CHALLENGE_FEATURES, edition_coverage


def dated_brands(raw, linker):
    """Use dated NDA products anchored to a unique FIX2c composition."""
    orange = orange_products(raw)
    for record in read_jsonl(raw / "df_nda.jsonl"):
        app = record.get("application_number") or ""
        if not app.startswith("NDA") or not app[3:].isdigit():
            continue
        number = norm_appl_no(app[3:])
        for product in record.get("products") or ():
            product_no = str(product.get("product_number") or "").zfill(3)
            name = product.get("brand_name")
            keys = {key for key, _ in linker.nda_products.get((number, product_no), ())
                    if key in linker.entities}
            approved = parse_yyyymmdd(product.get("approval_date"))
            if not approved and (evidence := orange.get(("NDA" + number, product_no))):
                approved = evidence[1]
            if name and approved and len(keys) == 1:
                yield name, next(iter(keys)), approved


def run(raw, ob_dir, piv_dir, challenge_dir):
    splits = {h: t2.development_split(h) for h in (12, 24)}
    t2.require_development_cutoffs(t2.DEVELOPMENT_CUTOFFS)
    used = {d for split in splits.values() for dates in split for d in dates}
    for horizon, (train, validation) in splits.items():
        if (any(add_months(d, horizon) >= validation[0] for d in train)
                or any(add_months(d, horizon) >= TEST_FIRST for d in validation)):
            raise ValueError("E7 requires strictly embargoed development windows")

    s0, s0_ref = _manifest(ROOT / "data/S0_INPUT_MANIFEST.json")
    data_end = date.fromisoformat(s0["t0"])
    names = {"df_nda.jsonl", "df_anda.jsonl", *ORANGE_FILES}
    raw_hashes = {name: next(item["sha256"] for item in s0["files"] if item["raw_file"] == name)
                  for name in sorted(names)}
    for name, digest in raw_hashes.items():
        _verify(raw / name, digest)
    gsrs = raw.resolve().parent / "moiety" / GSRS_FILE
    _verify(gsrs, GSRS_SHA256)
    entities = build_entities(raw, gsrs_path=gsrs)
    linker = HistoricalMoietyLinker(raw, entities, gsrs_path=gsrs)

    ob_manifest, ob_ref = _manifest(ROOT / "data/OB_EDITIONS.json")
    ob = OBHistory.from_records(ob_manifest, str(ob_dir))
    ob_coverage = {d.isoformat(): dict(edition_coverage(ob, d), used_in_split=d in used)
                   for d in t2.DEVELOPMENT_CUTOFFS}
    for d in sorted(used):
        chosen = ob_coverage[d.isoformat()]["source"]
        if chosen:
            _verify(ob_dir / chosen["file"], chosen["sha256"])

    piv_path = ROOT / "data/PIV_EDITIONS.json"
    _, piv_ref = _manifest(piv_path)
    piv = PIVHistory(piv_path, piv_dir, EntityMatcher([]))
    sources, source_ref = _manifest(ROOT / "data/E7_sources.json")
    rai = sources["rai"]
    for source in (rai, rai["metadata"], *sources["corroborating_documents"].values()):
        _verify(challenge_dir / source["file"], source["sha256"])
    identity = ChallengeIdentity(linker, dated_brands(raw, linker))
    corroboration = [
        {**case, **sources["corroborating_documents"][case["document"]]}
        for case in sources["corroborated_cases"]
    ]
    challenge = ChallengeHistory(piv, identity, court_rows(challenge_dir / rai["file"], TEST_FIRST),
                                 rai, corroboration)
    builder = AsOfBuilder(ob, linker=linker, challenge=challenge)
    summary = {
        "status": "DEVELOPMENT_ONLY", "sealed_test_start": TEST_FIRST.isoformat(),
        "key_mode": "moiety", "entities": len(entities), "edgar": sources["edgar"],
        "input_sha256": {"s0_manifest": s0_ref, "s0_files": raw_hashes, "ob_manifest": ob_ref,
                         "gsrs": {"file": gsrs.name, "sha256": GSRS_SHA256},
                         "piv_manifest": piv_ref, "court_manifest": source_ref},
        "orange_book_coverage": ob_coverage,
        "source_linkage_by_cutoff": {d.isoformat(): challenge.linkage_audit(d)
                                     for d in t2.DEVELOPMENT_CUTOFFS},
        "protocol": {"base": "FIX2c/T2b", "shared_challenge_features": CHALLENGE_FEATURES,
                     "coverage_target": t2.COMMON_COVERAGE, "lo": t2.LO, "hi": t2.HI,
                     "l2_grid": t2.L2_GRID, "drug_key_calibration_folds": t2.FOLDS,
                     "bootstrap_draws": t2.BOOTSTRAP_DRAWS, "bootstrap_seed": t2.BOOTSTRAP_SEED},
        "horizons": {},
    }
    leaf_counts = {}
    witnesses = {}
    for cutoff in t2.DEVELOPMENT_CUTOFFS:
        tag = cutoff.isoformat()
        counts = dict.fromkeys((v.name for v in T3), 0)
        witnesses[tag] = {}
        for key, entity in sorted(entities.items()):
            if (entity.nda_first is None or entity.nda_first > cutoff or not entity.flag_at("nme", cutoff)
                    or (entity.anda_first is not None and entity.anda_first <= cutoff)):
                continue
            evidence = challenge.lookup(key, cutoff)
            counts[evidence.state.name] += 1
            if evidence.witnesses:
                witnesses[tag][key] = [dict(asdict(w), date=w.date.isoformat()) for w in evidence.witnesses]
        leaf_counts[tag] = counts
    summary["challenge_leaf_coverage_by_cutoff"] = leaf_counts
    summary["witnesses_file"] = "E7_witnesses.json"

    for horizon, (train_dates, validation_dates) in splits.items():
        if add_months(validation_dates[-1], horizon) > data_end:
            raise ValueError("verified inputs do not cover the full validation window")
        verdicts = {}
        partitions = []
        for dates in (train_dates, validation_dates):
            rows = build_samples(entities, dates, horizon, data_end, only_nme=True)
            verdicts.update({d.isoformat(): dict.fromkeys(t2.VERDICTS, 0) for d in dates})
            counts = Counter()
            for row in rows:
                row["asof"] = builder.build(row["key"], row["t"], horizon, row["x"])
                tag = row["t"].isoformat()
                verdicts[tag][row["asof"].verdict] += 1
                counts[tag] += 1
            if any(counts[d.isoformat()] != sum(leaf_counts[d.isoformat()].values()) for d in dates):
                raise ValueError("challenge coverage and model cohort differ")
            partitions.append(rows)
        train, validation = partitions
        summary["horizons"][str(horizon)] = {
            "status": "DEVELOPMENT_ONLY", "train_rows": len(train),
            "train_cutoffs": [d.isoformat() for d in train_dates],
            "validation_cutoffs": [d.isoformat() for d in validation_dates],
            "verdicts_by_cutoff": verdicts,
            **t2.evaluate(train, validation, horizon, with_challenge=True),
        }
    return summary, witnesses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(DEFAULT_DIR).parent
    parser.add_argument("--raw", type=Path, default=base / "raw-20261127")
    parser.add_argument("--ob-dir", type=Path, default=Path(DEFAULT_DIR))
    parser.add_argument("--piv-dir", type=Path, default=base / "piv")
    parser.add_argument("--challenge-dir", type=Path, default=base / "challenge")
    args = parser.parse_args()
    summary, witnesses = run(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir)
    for name, payload in (("E7_witnesses.json", witnesses), ("E7_dev_summary.json", summary)):
        output = ROOT / "data" / name
        output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
                          encoding="utf-8", newline="\n")
        print(output)


if __name__ == "__main__":
    main()
