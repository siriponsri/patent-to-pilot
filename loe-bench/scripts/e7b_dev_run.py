"""Replay E7b on the FIX2c development cohort while keeping the test seal closed."""
import argparse
from collections import Counter
from dataclasses import asdict
from datetime import date, timedelta
import json
from pathlib import Path

from e7_dev_run import dated_brands
from t2_dev_run import ROOT, _manifest, _verify
from loe_bench import t2
from loe_bench.challenge import ChallengeHistory, ChallengeIdentity, court_rows
from loe_bench.challenge_patents import FilingPatentIndex, PatentChallengeHistory
from loe_bench.common import add_months
from loe_bench.dataset import build_entities, build_samples
from loe_bench.kleene import T3
from loe_bench.moiety import GSRS_FILE, GSRS_SHA256, ORANGE_FILES
from loe_bench.ob_history import DEFAULT_DIR, OBHistory
from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.piv_history import EntityMatcher, PIVHistory
from loe_bench.seal import TEST_FIRST
from loe_bench.t2_features import AsOfBuilder, CHALLENGE_FEATURES, edition_coverage


def run(raw, ob_dir, piv_dir, challenge_dir):
    cutoffs = t2.DEVELOPMENT_CUTOFFS
    splits = {h: t2.development_split(h) for h in (12, 24)}
    used = {d for split in splits.values() for dates in split for d in dates}
    t2.require_development_cutoffs((*cutoffs, *used))
    for h, (train, validation) in splits.items():
        if (any(add_months(d, h) >= validation[0] for d in train)
                or any(add_months(d, h) >= TEST_FIRST for d in validation)):
            raise ValueError("E7b requires strictly embargoed development windows")

    s0, s0_ref = _manifest(ROOT / "data/S0_INPUT_MANIFEST.json")
    data_end = date.fromisoformat(s0["t0"])
    raw_names = {"df_nda.jsonl", "df_anda.jsonl", *ORANGE_FILES}
    raw_hashes = {item["raw_file"]: item["sha256"] for item in s0["files"] if item["raw_file"] in raw_names}
    if raw_hashes.keys() != raw_names:
        raise ValueError("missing S0 input digest")
    for name, digest in raw_hashes.items():
        _verify(raw / name, digest)
    gsrs = raw.resolve().parent / "moiety" / GSRS_FILE
    _verify(gsrs, GSRS_SHA256)
    entities = build_entities(raw, gsrs_path=gsrs)
    linker = HistoricalMoietyLinker(raw, entities, gsrs_path=gsrs)

    ob_manifest, ob_ref = _manifest(ROOT / "data/OB_EDITIONS.json")
    ob = OBHistory.from_records(ob_manifest, str(ob_dir))
    ob_coverage = {d.isoformat(): dict(edition_coverage(ob, d), used_in_split=d in used) for d in cutoffs}
    for d in sorted(used):
        selected = ob_coverage[d.isoformat()]["source"]
        if selected:
            _verify(ob_dir / selected["file"], selected["sha256"])

    piv_path = ROOT / "data/PIV_EDITIONS.json"
    _, piv_ref = _manifest(piv_path)
    piv = PIVHistory(piv_path, piv_dir, EntityMatcher([]))
    sources, source_ref = _manifest(ROOT / "data/E7_sources.json")
    baseline, baseline_ref = _manifest(ROOT / "data/E7_dev_summary.json")
    rai = sources["rai"]
    documents = sources["corroborating_documents"]
    for source in (rai, rai["metadata"], *documents.values()):
        _verify(challenge_dir / source["file"], source["sha256"])
    corroboration = [{**case, **documents[case["document"]]} for case in sources["corroborated_cases"]]
    identity = ChallengeIdentity(linker, dated_brands(raw, linker))
    # court_rows has an exclusive boundary, so include filings on the final cutoff.
    court = court_rows(challenge_dir / rai["file"], max(cutoffs) + timedelta(days=1))
    challenge = PatentChallengeHistory(piv, identity, court, rai, corroboration, FilingPatentIndex(ob, linker))
    builder = AsOfBuilder(ob, linker=linker, challenge=challenge)

    coverage, audits = {}, {}
    for cutoff in cutoffs:
        tag = cutoff.isoformat()
        before = Counter(dict.fromkeys((value.name for value in T3), 0))
        after = before.copy()
        at_risk_with_patent = 0
        _, linkage = challenge.patent_evidence(cutoff)
        for key, entity in entities.items():
            if (entity.nda_first is None or entity.nda_first > cutoff or not entity.flag_at("nme", cutoff)
                    or (entity.anda_first is not None and entity.anda_first <= cutoff)):
                continue
            prior = ChallengeHistory.lookup(challenge, key, cutoff)
            updated = challenge.lookup(key, cutoff)
            before[prior.state.name] += 1
            after[updated.state.name] += 1
            at_risk_with_patent += any(w.source == "RAI_OB_PATENT" for w in updated.witnesses)
        if before != baseline["challenge_leaf_coverage_by_cutoff"][tag]:
            raise ValueError(f"E7 baseline leaf counts differ at {tag}")
        coverage[tag] = {"before": dict(before), "after": dict(after),
                         "at_risk_drugs_with_patent_witness": at_risk_with_patent}
        audits[tag] = {**challenge.linkage_audit(cutoff), "RAI_OB_PATENT": linkage}

    summary = {
        "status": "DEVELOPMENT_ONLY", "sealed_test_start": TEST_FIRST.isoformat(),
        "key_mode": "moiety", "entities": len(entities), "edgar": sources["edgar"],
        "input_sha256": {"s0_manifest": s0_ref, "s0_files": raw_hashes, "ob_manifest": ob_ref,
                         "gsrs": {"file": gsrs.name, "sha256": GSRS_SHA256},
                         "piv_manifest": piv_ref, "court_manifest": source_ref, "e7_baseline": baseline_ref},
        "orange_book_coverage": ob_coverage, "source_linkage_by_cutoff": audits,
        "challenge_leaf_coverage_by_cutoff": coverage,
        "patent_witnesses_file": "E7b_patent_witnesses.json",
        "secondary_witnesses_file": "E7_witnesses.json",
        "protocol": {**baseline["protocol"], "base": "E7/FIX2c/T2b",
                     "shared_challenge_features": CHALLENGE_FEATURES},
        "horizons": {},
    }
    for h, (train_dates, validation_dates) in splits.items():
        if add_months(validation_dates[-1], h) > data_end:
            raise ValueError("verified inputs do not cover the full validation window")
        verdicts = {}
        partitions = []
        for dates in (train_dates, validation_dates):
            rows = build_samples(entities, dates, h, data_end, only_nme=True)
            verdicts.update({d.isoformat(): dict.fromkeys(t2.VERDICTS, 0) for d in dates})
            for row in rows:
                row["asof"] = builder.build(row["key"], row["t"], h, row["x"])
                verdicts[row["t"].isoformat()][row["asof"].verdict] += 1
            if any(sum(verdicts[d.isoformat()].values()) != sum(coverage[d.isoformat()]["after"].values())
                   for d in dates):
                raise ValueError("challenge coverage and model cohort differ")
            partitions.append(rows)
        train, validation = partitions
        summary["horizons"][str(h)] = {
            "status": "DEVELOPMENT_ONLY", "train_rows": len(train),
            "train_cutoffs": [d.isoformat() for d in train_dates],
            "validation_cutoffs": [d.isoformat() for d in validation_dates],
            "verdicts_by_cutoff": verdicts,
            **t2.evaluate(train, validation, h, with_challenge=True),
        }
    witnesses = {
        key: [dict(asdict(w), date=w.date.isoformat()) for w in records]
        for key, records in challenge.patent_evidence(max(cutoffs))[0].items()
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
    for name, payload in ((summary["patent_witnesses_file"], witnesses), ("E7b_dev_summary.json", summary)):
        output = ROOT / "data" / name
        output.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
                          encoding="utf-8", newline="\n")
        print(output)


if __name__ == "__main__":
    main()
