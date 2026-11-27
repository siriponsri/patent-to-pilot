"""Replay E7b with shared historical PSG features on validation only."""

import argparse
from collections import Counter
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path

from e7_dev_run import dated_brands
from e9_fetch import RAW
from e9_inventory import build_inventory, load_sources, write_json
from t2_dev_run import ROOT, _manifest, _verify
from loe_bench import t2
from loe_bench.challenge import ChallengeIdentity, court_rows
from loe_bench.challenge_patents import FilingPatentIndex, PatentChallengeHistory
from loe_bench.common import add_months
from loe_bench.dataset import build_entities, build_samples
from loe_bench.moiety import GSRS_FILE, GSRS_SHA256
from loe_bench.ob_history import DEFAULT_DIR, OBHistory
from loe_bench.ob_linkage import HistoricalMoietyLinker
from loe_bench.piv_history import EntityMatcher, PIVHistory
from loe_bench.psg import PSG_FIELDS, PSG_FEATURES
from loe_bench.seal import TEST_FIRST
from loe_bench.t2_features import AsOfBuilder, edition_coverage

E7B_SHA256 = "9826261061c0e1118ef0eb1cec4d878bf8192290511b763966bf5b4dcb4a0808"
HORIZONS = (12, 24)


def _pinned_input(name, reference):
    path = ROOT / "data" / name
    content = path.read_bytes()
    lf = content.replace(b"\r\n", b"\n")
    # E7b pinned some manifests from a CRLF checkout and its own output as LF.
    if reference["sha256"] not in {sha256(value).hexdigest()
                                   for value in (lf, lf.replace(b"\n", b"\r\n"))}:
        raise ValueError(f"pinned repository JSON changed: {name}")
    return json.loads(content)


def _builder(raw, ob_dir, piv_dir, challenge_dir, baseline, used):
    refs = baseline["input_sha256"]
    s0 = _pinned_input("S0_INPUT_MANIFEST.json", refs["s0_manifest"])
    data_end = date.fromisoformat(s0["t0"])
    for name, digest in refs["s0_files"].items():
        _verify(raw / name, digest)
    gsrs = raw.resolve().parent / "moiety" / GSRS_FILE
    _verify(gsrs, GSRS_SHA256)
    entities = build_entities(raw, gsrs_path=gsrs)
    if len(entities) != baseline["entities"]:
        raise ValueError("E7b entity count changed")
    linker = HistoricalMoietyLinker(raw, entities, gsrs_path=gsrs)
    ob_manifest = _pinned_input("OB_EDITIONS.json", refs["ob_manifest"])
    ob = OBHistory.from_records(ob_manifest, str(ob_dir))
    for cutoff in used:
        coverage = edition_coverage(ob, cutoff)
        if dict(coverage, used_in_split=True) != baseline["orange_book_coverage"][cutoff.isoformat()]:
            raise ValueError(f"E7b Orange Book edition changed at {cutoff}")
        if coverage["source"]:
            _verify(ob_dir / coverage["source"]["file"], coverage["source"]["sha256"])

    piv_path = ROOT / "data/PIV_EDITIONS.json"
    _pinned_input(piv_path.name, refs["piv_manifest"])
    piv = PIVHistory(piv_path, piv_dir, EntityMatcher([]))
    sources = _pinned_input("E7_sources.json", refs["court_manifest"])
    rai = sources["rai"]
    documents = sources["corroborating_documents"]
    for source in (rai, rai["metadata"], *documents.values()):
        _verify(challenge_dir / source["file"], source["sha256"])
    corroboration = [{**case, **documents[case["document"]]} for case in sources["corroborated_cases"]]
    identity = ChallengeIdentity(linker, dated_brands(raw, linker))
    court = court_rows(challenge_dir / rai["file"], max(used) + timedelta(days=1))
    challenge = PatentChallengeHistory(piv, identity, court, rai, corroboration, FilingPatentIndex(ob, linker))
    return entities, data_end, AsOfBuilder(ob, linker=linker, challenge=challenge)


def _delta(result, baseline):
    def subtract(after, before):
        return after - before if after is not None and before is not None else None

    return {
        "arm_metrics": {
            arm: {metric: subtract(values[metric], baseline["arms"][arm][metric])
                  for metric in ("aurc80", "brier", "ece", "coverage")}
            for arm, values in result["arms"].items()
        },
        "paired_aurc80_point_differences": {
            comparison: subtract(values["delta"], baseline["paired_aurc80"][comparison]["delta"])
            for comparison, values in result["paired_aurc80"].items()
        },
    }


def run(raw, ob_dir, piv_dir, challenge_dir, psg_dir):
    splits = {h: t2.development_split(h) for h in HORIZONS}
    used = {d for split in splits.values() for dates in split for d in dates}
    t2.require_development_cutoffs(used)
    for h, (train, validation) in splits.items():
        if (any(add_months(d, h) >= validation[0] for d in train)
                or any(add_months(d, h) >= TEST_FIRST for d in validation)):
            raise ValueError("E9 requires strictly embargoed development windows")

    e7b_ref = {"file": "E7b_dev_summary.json", "sha256": E7B_SHA256}
    baseline = _pinned_input(e7b_ref["file"], e7b_ref)
    sources, sources_ref = _manifest(ROOT / "data/E9_sources.json")
    current, updates, archived, skipped = load_sources(psg_dir, sources)
    entities, data_end, builder = _builder(raw, ob_dir, piv_dir, challenge_dir, baseline, used)
    builder.psg, inventory, audit = build_inventory(current, updates, archived, builder.linker)
    audit["skipped_archives"] = skipped
    inventory_path = psg_dir / "E9_psg_inventory.json"
    write_json(inventory_path, {"current": inventory, "sources": sources, "audit": audit})
    audit["inventory"] = {"file": inventory_path.name, "sha256": sha256(inventory_path.read_bytes()).hexdigest()}
    write_json(ROOT / "data/E9_psg_audit.json", audit)

    summary = {
        "status": "DEVELOPMENT_ONLY", "sealed_test_start": TEST_FIRST.isoformat(), "key_mode": "moiety",
        "input_sha256": {"e7b_summary": e7b_ref, "psg_sources": sources_ref},
        "protocol": {**baseline["protocol"], "base": "E7b/FIX2c/T2b", "shared_psg_features": PSG_FEATURES,
                     "psg_history": "ARCHIVED_POSITIVE_WITNESSES_ONLY",
                     "comparison_to_e7b": "PINNED_PUBLISHED_POINT_DIFFERENCES"},
        "horizons": {},
    }
    for h, (train_dates, validation_dates) in splits.items():
        if add_months(validation_dates[-1], h) > data_end:
            raise ValueError("verified inputs do not cover the full validation window")
        prior = baseline["horizons"][str(h)]
        counts = {}
        verdicts = {}
        partitions = []
        for dates in (train_dates, validation_dates):
            rows = build_samples(entities, dates, h, data_end, only_nme=True)
            for cutoff in dates:
                tag = cutoff.isoformat()
                counts[tag] = Counter(dict.fromkeys(("rows", *PSG_FIELDS), 0))
                verdicts[tag] = dict.fromkeys(t2.VERDICTS, 0)
            for row in rows:
                cutoff = row["t"]
                asof = builder.build(row["key"], cutoff, h, row["x"])
                row["asof"] = asof
                tag = cutoff.isoformat()
                verdicts[tag][asof.verdict] += 1
                counts[tag]["rows"] += 1
                for field in PSG_FIELDS:
                    counts[tag][field] += int(not asof.x[field + "_missing"])
            partitions.append(rows)
        train, validation = partitions
        cohort = {
            "train_rows": len(train), "train_cutoffs": [d.isoformat() for d in train_dates],
            "validation_cutoffs": [d.isoformat() for d in validation_dates],
            "validation_rows": len(validation), "verdicts_by_cutoff": verdicts,
            "validation_drug_clusters": len({row["key"] for row in validation}),
            "validation_event_clusters": len({row["key"] for row in validation if row["y"]}),
        }
        if any(prior[key] != value for key, value in cohort.items()):
            raise ValueError(f"E7b validation protocol or cohort differs at {h} months")
        if not any(counts[d.isoformat()]["has_psg"] for d in train_dates):
            raise ValueError("PSG history supplies no usable training observations")
        print(f"E9 {h} months: {len(train)} training rows, {len(validation)} validation rows", flush=True)
        result = t2.evaluate(train, validation, h, with_challenge=True, with_psg=True)
        for arm in ("B1", "M2"):
            actual = result["arms"][arm]
            # The metric returns tuple bin counts, which JSON stores as a list.
            serialized = dict(actual, ece_bin_counts=list(actual["ece_bin_counts"]))
            changed = [name for name, value in serialized.items() if prior["arms"][arm][name] != value]
            if changed:
                raise ValueError(f"E7b {arm} control changed at {h} months: {', '.join(changed)}")
        summary["horizons"][str(h)] = {
            "status": "DEVELOPMENT_ONLY", **cohort, **result,
            "known_psg_feature_rows_by_cutoff": {tag: dict(count) for tag, count in counts.items()},
            "delta_vs_e7b": _delta(result, prior),
        }
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    base = Path(DEFAULT_DIR).parent
    parser.add_argument("--raw", type=Path, default=base / "raw-20261127")
    parser.add_argument("--ob-dir", type=Path, default=Path(DEFAULT_DIR))
    parser.add_argument("--piv-dir", type=Path, default=base / "piv")
    parser.add_argument("--challenge-dir", type=Path, default=base / "challenge")
    parser.add_argument("--psg-dir", type=Path, default=RAW)
    args = parser.parse_args()
    summary = run(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir, args.psg_dir)
    write_json(ROOT / "data/E9_dev_summary.json", summary)


if __name__ == "__main__":
    main()
