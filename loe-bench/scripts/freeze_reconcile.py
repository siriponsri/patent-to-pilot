"""Reconcile published H2 values with a development-only REG crossover."""
import sys
from collections import Counter
from dataclasses import replace
from datetime import timedelta
from math import isclose

import numpy as np

import freeze_run as freeze
import k22_dev_run as k22
import t1v3_run as t1
from loe_bench.kleene import T3
from loe_bench.review_metrics import ReviewQueue
from loe_bench.t2_features import AsOfBuilder


class PreRegChallenge:
    """Replay the exact pre-REG fallback while preserving all E7b witnesses."""

    def __init__(self, merged):
        self.merged = merged

    def lookup(self, key, cutoff):
        current = self.merged.lookup(key, cutoff)
        _, coverage, undated = self.merged._piv(cutoff)
        if current.state == T3.UNKNOWN and coverage["status"] == "FRESH" and key in undated:
            return replace(current, state=T3.FALSE)
        return current


def decompose(entities, merged):
    horizon = 24
    train_days, validation_days = t1.replay.PRIMARY[horizon]
    observed = min(validation_days) - timedelta(days=1)
    old = AsOfBuilder(merged.history, linker=merged.linker, challenge=PreRegChallenge(merged.challenge))
    new_v2 = AsOfBuilder(merged.history, linker=merged.linker, challenge=merged.challenge, graph_version="v2")
    train_old, train_new = (t1.replay.partition(entities, b, train_days, horizon, training=True)
                            for b in (old, merged))
    val_old, val_new = (t1.replay.partition(entities, b, validation_days, horizon) for b in (old, merged))
    train_v2, val_v2 = (k22.v2_rows(rows, new_v2, horizon) for rows in (train_new, val_new))
    publication_t1 = freeze.read_json("T1v3_results.json")["horizons"]["24"]["queue"]
    publication_k22 = freeze.read_json("K22_trial.json")["horizons"]["24"]
    change_counts = {}
    for name, before, after in (("training", train_old, train_new), ("validation", val_old, val_new)):
        changes = Counter()
        for a, b in zip(before, after, strict=True):
            for field in ("key", "t", "y", "x", "breadth"):
                if a[field] != b[field]:
                    raise ValueError(f"REG comparison changed matched {name} {field}")
            for field in ("challenge_missing", "challenge_present"):
                changes[field] += a["asof"].x[field] != b["asof"].x[field]
            changes["verdict"] += a["asof"].verdict != b["asof"].verdict
        change_counts[name] = {"rows": len(before), **changes}

    calibrators, _, _ = t1.fit_inner(train_new, horizon, observed)
    k22_calibrators = k22.calibrate(train_new, train_v2, horizon, observed)
    new_native = t1.native(train_new, val_new, horizon, observed)
    k22_native = k22.predict(train_new, val_new, train_v2, val_v2, horizon, observed)
    for old_name, new_name in (("M1", "M1"), ("M3", "M3_v1")):
        a, b = calibrators[old_name], k22_calibrators[new_name]
        if (a.mu, a.sd, a.w, a.b) != (b.mu, b.sd, b.w, b.b) or new_native[old_name] != k22_native[new_name]:
            raise ValueError("Two entrypoints disagree on model scores or OOF sigmoid")

    stages = []
    for name, scores in (
        ("pre_REG_TRAIN_and_validation", t1.native(train_old, val_old, horizon, observed)),
        ("REG_TRAIN_only", t1.native(train_new, val_old, horizon, observed)),
        ("REG_validation_only", t1.native(train_old, val_new, horizon, observed)),
        ("REG_TRAIN_and_validation", new_native),
    ):
        panel = t1.t1v3.QueuePanel(val_new, validation_days, scores)
        queues = {arm: ReviewQueue(scores[arm], [row["t"] for row in val_new]) for arm in ("M1", "M3")}
        n = len(panel.keys)
        rng = np.random.default_rng(t1.t2.BOOTSTRAP_SEED)
        point = panel.evaluate(np.ones(n, dtype=int))
        recalls = {arm: point["arms"][arm]["recall"] for arm in queues}
        samples = []
        for i in range(t1.t2.BOOTSTRAP_DRAWS + 1):
            copies = np.ones(n, dtype=int) if not i else np.bincount(rng.integers(n, size=n), minlength=n)
            row_weights = copies[panel.groups]
            result = panel.evaluate(copies)
            for arm, queue in queues.items():
                fractions, slots = queue.allocation(row_weights)
                captured = (row_weights * panel.labels) @ fractions
                expected = result["arms"][arm]
                if (slots != result["queue_slots"]
                        or not isclose(expected["expected_queued_events"], captured, rel_tol=0, abs_tol=1e-12)):
                    raise ValueError("Two queue scorers disagree on matched draw")
            if i:
                samples.append(result["arms"]["M3"]["recall"] - result["arms"]["M1"]["recall"])
        delta = recalls["M3"] - recalls["M1"]
        stages.append({"stage": name, "recall": recalls, "event_rows": point["event_rows"],
                       "hits": {arm: point["arms"][arm]["expected_queued_events"] for arm in queues},
                       "H2": t1.t1v3.interval(delta, np.asarray(samples))})

    historical = (publication_t1["contrasts"]["M3-M1"]["recall"],
                  publication_k22["contrasts"]["M3_v1_minus_M1"]["recall20"])
    for stage, evidence in zip((stages[0], stages[-1]), historical, strict=True):
        estimate = evidence.get("estimate", evidence.get("point"))
        if not np.allclose([stage["H2"]["estimate"], *stage["H2"]["ci95"]],
                           [estimate, *evidence["ci95"]], rtol=0, atol=1e-12):
            raise ValueError(f"Historical H2 failed to reproduce for {stage['stage']}")
    return {"status": "DEVELOPMENT_ONLY", "horizon": horizon, "stages": stages,
            "changed_rows": change_counts, "native_and_calibration_matched": True,
            "paired_queue_draws_matched_per_stage": t1.t2.BOOTSTRAP_DRAWS}


if __name__ == "__main__":
    t1.require_closed_seal()
    args = freeze.parser(__doc__).parse_args()
    entities, builder, _ = t1.replay.inputs(args.raw, args.ob_dir, args.piv_dir, args.challenge_dir)
    result = decompose(entities, builder)
    t1.require_closed_seal()
    freeze.write_json("FREEZE_reconciliation.json", result)
