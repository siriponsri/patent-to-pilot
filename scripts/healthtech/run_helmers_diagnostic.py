#!/usr/bin/env python3
"""Run a post-freeze lexical feature diagnostic on the Helmers judged pool."""

from __future__ import annotations

import argparse
import io
import json
import math
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np


def load_npy_member(archive: zipfile.ZipFile, name: str):
    with archive.open(name) as handle:
        return np.load(io.BytesIO(handle.read()), allow_pickle=True, encoding="latin1")


def cosine(left: dict[str, float], right: dict[str, float]) -> float:
    shared = set(left) & set(right)
    numerator = sum(float(left[key]) * float(right[key]) for key in shared)
    left_norm = math.sqrt(sum(float(value) ** 2 for value in left.values()))
    right_norm = math.sqrt(sum(float(value) ** 2 for value in right.values()))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return numerator / (left_norm * right_norm)


def average_precision(labels: list[int], scores: list[float]) -> float:
    ranked = sorted(zip(scores, labels), key=lambda pair: (-pair[0], -pair[1]))
    positives = sum(labels)
    if not positives:
        return 0.0
    hits = 0
    total = 0.0
    for rank, (_, label) in enumerate(ranked, start=1):
        if label:
            hits += 1
            total += hits / rank
    return total / positives


def auc(labels: list[int], scores: list[float]) -> float:
    positives = [(score, label) for score, label in zip(scores, labels) if label == 1]
    negatives = [(score, label) for score, label in zip(scores, labels) if label == 0]
    if not positives or not negatives:
        return 0.0
    wins = 0.0
    for positive, _ in positives:
        for negative, _ in negatives:
            if positive > negative:
                wins += 1.0
            elif positive == negative:
                wins += 0.5
    return wins / (len(positives) * len(negatives))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--summary-out", type=Path, required=True)
    args = parser.parse_args()

    with zipfile.ZipFile(args.archive) as archive:
        labels = load_npy_member(archive, "human_eval/corpus_info/human_label_pairs.npy").item()
        features = load_npy_member(archive, "human_eval/corpus_info/patfeats_human_eval.npy").item()
        targets = [value.decode("ascii") for value in load_npy_member(archive, "human_eval/corpus_info/combis.npy")[:, 0]]
        per_target: dict[str, dict[str, object]] = {}
        grouped: dict[str, list[tuple[int, float]]] = defaultdict(list)
        for (target, candidate), label in labels.items():
            score = cosine(features[target], features[candidate])
            grouped[target].append((int(label > 0), score))
        for target in sorted(set(targets)):
            pairs = grouped[target]
            target_labels = [label for label, _ in pairs]
            target_scores = [score for _, score in pairs]
            per_target[target] = {
                "pair_count": len(pairs),
                "positive_count": sum(target_labels),
                "average_precision": average_precision(target_labels, target_scores),
                "auc": auc(target_labels, target_scores),
            }

    macro_ap = sum(value["average_precision"] for value in per_target.values()) / max(len(per_target), 1)
    macro_auc = sum(value["auc"] for value in per_target.values()) / max(len(per_target), 1)
    summary = {
        "run_version": "helmers-post-freeze-diagnostic-v1",
        "status": "PASS_DESCRIPTIVE_DIAGNOSTIC",
        "archive": str(args.archive),
        "targets": len(per_target),
        "judged_pairs": sum(value["pair_count"] for value in per_target.values()),
        "positive_pairs": sum(value["positive_count"] for value in per_target.values()),
        "macro_average_precision": macro_ap,
        "macro_auc": macro_auc,
        "method": "cosine similarity over pinned patfeats_human_eval term-count features",
        "selection_bias": "judged pool selected by the source authors; target/pair rows are not independent global samples",
        "not_claimed": ["exhaustive recall", "semantic device-patent gold", "adaptive superiority", "business validation"],
        "per_target": per_target,
    }
    args.summary_out.parent.mkdir(parents=True, exist_ok=True)
    args.summary_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": summary["status"], "targets": summary["targets"], "judged_pairs": summary["judged_pairs"], "macro_average_precision": summary["macro_average_precision"], "macro_auc": summary["macro_auc"], "summary": str(args.summary_out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
