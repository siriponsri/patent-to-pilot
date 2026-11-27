"""PIPELINE SMOKE RUN on real Track-C data. NOT a research result (no preregistration, no tuning protocol).
Usage: python3 -m loe_bench.run_baselines --raw data/raw --horizon 36
"""
import argparse
from datetime import date

from .baselines import AgeHazardTable, BaseRate, Logistic
from .dataset import build_entities, build_samples, time_split
from .metrics import aurc, auroc, brier, cluster_bootstrap_ci, ece


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="data/raw")
    ap.add_argument("--horizon", type=int, default=36)
    ap.add_argument("--train-last", default="2014-01-01")
    ap.add_argument("--test-first", default="2017-01-01")
    a = ap.parse_args()
    ents = build_entities(a.raw)
    data_end = max(e.anda_first for e in ents.values() if e.anda_first)
    cutoffs = [date(y, 1, 1) for y in range(1995, 2024)]
    rows = build_samples(ents, cutoffs, a.horizon, data_end, only_nme=True)
    train, test, dropped = time_split(rows, date.fromisoformat(a.train_last), date.fromisoformat(a.test_first))
    y = [r["y"] for r in test]
    g = [r["key"] for r in test]
    print(f"train={len(train)} test={len(test)} embargo_dropped={dropped} test_prev={sum(y)/len(y):.3f}")
    for m in (BaseRate(), AgeHazardTable(), Logistic()):
        p = m.fit(train).predict(test)
        lo, hi = cluster_bootstrap_ci(brier, p, y, g, n_boot=100)
        print(f"{m.name:16s} Brier={brier(p,y):.4f} [{lo:.4f},{hi:.4f}] ECE={ece(p,y).ece:.4f} AUROC={auroc(p,y):.3f} AURC={aurc(p,y):.4f}")
    print("NOTE: smoke run only. Not a result. See docs/01 for the preregistered protocol.")


if __name__ == "__main__":
    main()
