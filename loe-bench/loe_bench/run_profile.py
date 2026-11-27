"""Data-quality profile of the fetched real data. OBSERVATION ONLY - not a research result.
Usage: python3 -m loe_bench.run_profile --raw data/raw --out data/profile.json
"""
import argparse
import json
from collections import Counter
from datetime import date

from .dataset import build_entities, build_samples, snapshot_features, time_split


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/profile.json")
    ap.add_argument("--data-end", default=None, help="YYYY-MM-DD; default = max ANDA approval date seen")
    a = ap.parse_args()
    ents = build_entities(a.raw)
    with_nda = [e for e in ents.values() if e.nda_first]
    nme = [e for e in with_nda if e.nme]
    nme_anda = [e for e in nme if e.anda_first]
    anda_dates = [e.anda_first for e in ents.values() if e.anda_first]
    data_end = date.fromisoformat(a.data_end) if a.data_end else max(anda_dates)
    prof = {
        "entities_total": len(ents),
        "entities_with_nda_orig_date": len(with_nda),
        "nme_entities": len(nme),
        "nme_with_any_anda": len(nme_anda),
        "nme_nda_year_counts": dict(sorted(Counter(e.nda_first.year for e in nme).items())),
        "data_end_used": data_end.isoformat(),
    }
    horizons = {}
    for h in (24, 36):
        cutoffs = [date(y, 1, 1) for y in range(2005, 2024)]
        rows = build_samples(ents, cutoffs, h, data_end, only_nme=True)
        train, test, dropped = time_split(rows, date(2014, 1, 1), date(2017, 1, 1))
        horizons[str(h)] = {
            "rows": len(rows), "prevalence": round(sum(r["y"] for r in rows) / max(1, len(rows)), 4),
            "train": len(train), "test": len(test), "dropped_by_embargo": dropped,
            "test_prevalence": round(sum(r["y"] for r in test) / max(1, len(test)), 4),
        }
    prof["horizons"] = horizons
    snap = snapshot_features(a.raw, date.today(), ents)
    prof["trackA_entities_without_anda_with_ob_record"] = len(snap)
    prof["trackA_with_patent_dates"] = sum(1 for s in snap.values() if s["patent_exp"])
    json.dump(prof, open(a.out, "w"), indent=2, ensure_ascii=False)
    print(json.dumps(prof, indent=2))


if __name__ == "__main__":
    main()
