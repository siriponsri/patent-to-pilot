"""Solution-atlas headroom check on dev: does knowing which far IPC3 classes hold the targets change R@20/R@50?

Plan: docs/healthtech/research/SOLUTION_ATLAS_HEADROOM_PLAN_20261106_EN.md (pre-declared).
Every reordering is a stable class-first partition of an IPC3-masked dense Top-200, so R@200 does not change.
  oracle   C = IPC3 classes of the query's own strict-OUT positives (upper bound; uses labels)
  prior-m  C = top-m classes of a class-transition prior learned from the other folds' strict-OUT pairs
Test queries are never read. Output holds aggregates only.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from patent_to_pilot.evaluation.dapfam_acquisition import (  # noqa: E402
    POOL_DEPTH, assign_folds, class_first, class_transition_prior, positive_relations, predict_target_classes)
from patent_to_pilot.evaluation.par4pc_study import paired_cluster_bootstrap  # noqa: E402

SEED = 20261105
FOLDS = 5
MS = (3, 5, 10)
PRIMARY_M = 5
ORACLE_MIN_GAIN = 0.02


def _load(path: Path) -> dict[str, list[str]]:
    return {r["query_id"]: r["families"][:POOL_DEPTH]
            for r in map(json.loads, path.read_text(encoding="utf-8").splitlines()) if r}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ranking", action="append", required=True, metavar="NAME=PATH",
                        help="masked Top-200 rankings; the first one is primary (brief P)")
    parser.add_argument("--records", type=Path, required=True, help="scout dev records with own_ipc3")
    parser.add_argument("--family-ipc3", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, default=ROOT / "methodology/datasets/research-only-nc/qrels_all.parquet")
    parser.add_argument("--split", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import pyarrow.parquet as pq

    split_doc = json.loads(args.split.read_text(encoding="utf-8"))
    dev = sorted(q for q, s in split_doc["assignment"].items() if s == "dev")
    section = split_doc["first_ipc_section"]
    own = {r["id"]: r["own_ipc3"] for r in map(json.loads, args.records.read_text(encoding="utf-8").splitlines()) if r}
    family_ipc3 = {r["id"]: r["ipc3"] for r in map(json.loads, args.family_ipc3.read_text(encoding="utf-8").splitlines())
                   if r}
    positives = positive_relations(pq.read_table(args.qrels).to_pylist())
    out_rel = {q: positives.get(q, {}).get("OUT", set()) for q in dev}
    out_q = [q for q in dev if out_rel[q]]
    ident = {q: q for q in out_q}
    target_classes = {q: sorted({c for t in out_rel[q] for c in family_ipc3.get(t, ())} - set(own[q])) for q in out_q}

    folds = assign_folds({q: section[q] for q in out_q}, k=FOLDS, seed=SEED)
    predicted: dict[int, dict[str, list[str]]] = {m: {} for m in MS}
    for fold in range(FOLDS):
        prior = class_transition_prior((own[q], [c for t in out_rel[q] for c in family_ipc3.get(t, ())])
                                       for q in out_q if folds[q] != fold)
        for q in out_q:
            if folds[q] == fold:
                for m in MS:
                    predicted[m][q] = predict_target_classes(prior, own[q], m)

    def recall(pool: list[str], q: str, k: int) -> float:
        return len(set(pool[:k]) & out_rel[q]) / len(out_rel[q])

    result = {"format": "ptp-solution-atlas-headroom-dev-v1", "split": "dev", "test_split_read": False,
              "queries": {"dev": len(dev), "out_eligible": len(out_q)}, "folds": FOLDS, "seed": SEED,
              "inputs_sha256": {"records": _sha(args.records), "family_ipc3": _sha(args.family_ipc3),
                                "split": _sha(args.split), "qrels": _sha(args.qrels)},
              "rankings": {}}
    for index, spec in enumerate(args.ranking):
        name, path = spec.split("=", 1)
        path = Path(path)
        ranked = _load(path)
        result["inputs_sha256"][name] = _sha(path)
        pools = {"masked": {q: ranked.get(q, []) for q in out_q},
                 "oracle": {q: class_first(ranked.get(q, []), family_ipc3, set(target_classes[q])) for q in out_q}}
        for m in MS:
            pools[f"prior_m{m}"] = {q: class_first(ranked.get(q, []), family_ipc3, set(predicted[m][q])) for q in out_q}
        per = {k: {name_: {q: recall(p[q], q, k) for q in out_q} for name_, p in pools.items()} for k in (20, 50, 200)}
        block = {"primary": index == 0,
                 "recall": {name_: {f"r@{k}": sum(per[k][name_].values()) / len(out_q) for k in (20, 50, 200)}
                            for name_ in pools},
                 "deltas": {}}
        for name_ in pools:
            if name_ == "masked":
                continue
            for k in (20, 50):
                block["deltas"][f"{name_}_minus_masked_r@{k}"] = paired_cluster_bootstrap(
                    per[k][name_], per[k]["masked"], ident, resamples=5000, seed=SEED)
        result["rankings"][name] = block

    primary = result["rankings"][args.ranking[0].split("=", 1)[0]]["deltas"]
    oracle_gain = primary["oracle_minus_masked_r@50"]["delta"]
    prior_low = primary[f"prior_m{PRIMARY_M}_minus_masked_r@50"]["ci95_low"]
    result["gate"] = {"oracle_min_gain": ORACLE_MIN_GAIN, "oracle_gain_r@50": oracle_gain,
                      f"prior_m{PRIMARY_M}_ci95_low_r@50": prior_low,
                      "status": "STOP" if oracle_gain < ORACLE_MIN_GAIN else ("GO" if prior_low > 0 else "GO_ORACLE_ONLY")}

    # Concentration (descriptive)
    sizes = sorted(len(target_classes[q]) for q in out_q)
    by_section: dict[str, Counter] = defaultdict(Counter)
    for q in out_q:
        for t in out_rel[q]:
            for c in set(family_ipc3.get(t, ())) - set(own[q]):
                by_section[section[q]][c] += 1
    concentration = {}
    for sec, counts in sorted(by_section.items()):
        total = sum(counts.values())
        entropy = -sum(n / total * math.log(n / total) for n in counts.values())
        concentration[sec] = {"queries": sum(1 for q in out_q if section[q] == sec), "target_classes": len(counts),
                              "normalized_entropy": entropy / math.log(len(counts)) if len(counts) > 1 else 0.0,
                              "top5_share": sum(n for _, n in counts.most_common(5)) / total}
    hits = {m: sum(len(set(predicted[m][q]) & set(target_classes[q])) > 0 for q in out_q) / len(out_q) for m in MS}
    result["concentration"] = {
        "target_classes_per_query": {"mean": sum(sizes) / len(sizes), "median": sizes[len(sizes) // 2],
                                     "max": sizes[-1]},
        "by_first_section": concentration,
        "prior_hit_any_target_class": {f"m{m}": hits[m] for m in MS},
        "mean_predicted_classes": {f"m{m}": sum(len(predicted[m][q]) for q in out_q) / len(out_q) for m in MS},
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"gate": result["gate"],
                      **{n: b["recall"] for n, b in result["rankings"].items()},
                      "concentration": result["concentration"]["target_classes_per_query"],
                      "prior_hit": result["concentration"]["prior_hit_any_target_class"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
