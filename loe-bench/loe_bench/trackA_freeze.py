"""Track A: freeze a prospective prediction file from the CURRENT snapshot.
For every NME entity with an Orange Book record and NO first ANDA yet, write for horizons 12/24/36 months:
  model probability (age-table + logistic average), rule baseline, evidence-graph verdict, action.
The output + SHA-256 should be committed/timestamped (e.g. git tag, OSF preregistration) BEFORE outcomes are known.
Usage: python3 -m loe_bench.trackA_freeze --raw data/raw --out data/trackA_S0.csv
"""
import argparse
import csv
import hashlib
from datetime import date

from .baselines import AgeHazardTable, Logistic, exclusivity_rule_score
from .dataset import build_entities, build_samples, features_at, snapshot_features
from .evidence_graph import decide


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--out", default="data/trackA_S0.csv")
    ap.add_argument("--t0", default=date.today().isoformat())
    a = ap.parse_args()
    t0 = date.fromisoformat(a.t0)
    ents = build_entities(a.raw)
    data_end = max(e.anda_first for e in ents.values() if e.anda_first)
    snaps = snapshot_features(a.raw, t0, ents)
    rows_out = []
    for h in (12, 24, 36):
        cutoffs = [date(y, 1, 1) for y in range(1995, t0.year + 1)]
        train = build_samples(ents, cutoffs, h, data_end, only_nme=True)
        m1, m2 = AgeHazardTable().fit(train), Logistic(epochs=200).fit(train)
        for key, s in sorted(snaps.items()):
            e = ents[key]
            if not e.nme or e.nda_first is None:
                continue
            row = {"key": key, "x": features_at(e, t0)}
            p = (m1.predict([row])[0] + m2.predict([row])[0]) / 2
            d = decide(s, t0, h, p)
            rows_out.append({"entity": key, "t0": t0.isoformat(), "horizon_months": h, "p_model": round(p, 4),
                             "rule_baseline": exclusivity_rule_score(s, t0, h), "verdict": d["verdict"],
                             "action": d["action"], "next_evidence": (d["next_evidence"] or {}).get("leaf", "")})
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_out[0]))
        w.writeheader()
        w.writerows(rows_out)
    sha = hashlib.sha256(open(a.out, "rb").read()).hexdigest()
    print(f"wrote {len(rows_out)} rows to {a.out}\nsha256={sha}")


if __name__ == "__main__":
    main()
