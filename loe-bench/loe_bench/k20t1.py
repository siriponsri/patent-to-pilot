"""Development-only annual-edition training and fixed selective policies."""
from bisect import bisect_left, bisect_right
from collections import Counter
from dataclasses import replace
from datetime import date
from fractions import Fraction
from math import isfinite, nextafter

from . import devx, evidence_graph as graph, t2
from .t2_features import AsOfBuilder


EDITION_FEATURES = ("edition_staleness_days", "edition_nber", "edition_missing")
TARGETS = (50, 70, 90)
TOLERANCE = 3
MIDPOINT_ABOVE = nextafter(0.5, 1.0)


class AnnualTrainingBuilder(AsOfBuilder):
    """Keep the ZIP-only challenge path and extend only protection features."""

    def __init__(self, zip_builder, annual_history):
        super().__init__(zip_builder.history, linker=zip_builder.linker,
                         challenge=zip_builder.challenge)
        self.annual_history = annual_history

    def select_edition(self, cutoff):
        source, coverage = super().select_edition(cutoff)
        if source is not None:
            return source, coverage
        source, proof = self.annual_history.available_source_asof(cutoff)
        if source is None:
            return None, coverage
        return source, dict(coverage, status="ANNUAL_TRAINING", source=source.identity,
                            chosen_edition=source.edition_date.isoformat(), availability_proof=proof)


def edition_features(source, cutoff):
    if source is None:
        return dict(zip(EDITION_FEATURES, (0.0, 0.0, 1.0), strict=True))
    annual = source.identity["kind"] == "nber_annual"
    reference = date(source.identity["edition_year"] - 1, 12, 31) if annual else source.edition_date
    return dict(zip(EDITION_FEATURES, (float((cutoff - reference).days), float(annual), 0.0),
                    strict=True))


def with_edition_features(row, source):
    asof = row["asof"]
    return dict(row, asof=replace(asof, x={**asof.x, **edition_features(source, row["t"])}))


def m3_policy(row, horizon, probability, hi):
    asof = row["asof"]
    return graph.decide(asof.snapshot, row["t"], horizon, probability, lo=1 - hi, hi=hi,
                        challenge_evidence=asof.challenge.state if asof.challenge else None)


def apply_policy(arm, rows, probabilities, horizon, threshold):
    predictions, conflicts = [], 0
    for row, p in zip(rows, probabilities, strict=True):
        if arm == "M3":
            decision = m3_policy(row, horizon, p, threshold)
            action = decision["action"]
            conflicts += int(decision["conflict"])
        elif max(p, 1 - p) < threshold:
            action = graph.ABSTAIN
        else:
            action = graph.PREDICT_ENTRY if p > 0.5 else graph.PREDICT_NO_ENTRY
        predictions.append(t2.Prediction(p, action))
    return predictions, conflicts


def coverage_options(arm, probabilities, verdicts):
    """Enumerate every attainable answered count with intact probability ties."""
    if arm == "M1":
        scores = sorted(max(p, 1 - p) for p in probabilities)
        return [(threshold, len(scores) - bisect_left(scores, threshold))
                for threshold in sorted({0.5, 1.0, *scores})]

    blocked, other = [], []
    for p, v in zip(probabilities, verdicts, strict=True):
        (blocked if v == "BLOCKED" else other).append(p)
    blocked.sort()
    other.sort()
    edges = {MIDPOINT_ABOVE, 1.0}
    edges.update(p for p in (*blocked, *other) if p > 0.5)
    for p in other:
        if p < 0.5:
            edge = 1 - p
            # Subtraction at 1-hi is exact in this range. Correct an upward-rounded edge.
            edges.add(edge if 1 - edge >= p else nextafter(edge, 0.0))
    edges.update(nextafter(edge, 1.0) for edge in tuple(edges))
    return [(hi, bisect_left(blocked, hi) + bisect_right(other, 1 - hi)
             + len(other) - bisect_left(other, hi))
            for hi in sorted(edges) if MIDPOINT_ABOVE <= hi <= 1.0]


def choose_operating_points(arm, probabilities, verdicts):
    n = len(probabilities)
    if arm not in devx.ARMS or n == 0 or len(verdicts) != n or any(
            not 0 <= p <= 1 for p in probabilities):
        raise ValueError("threshold selection requires an arm and aligned nonempty probabilities")
    options = coverage_options(arm, probabilities, verdicts)
    maximum = max(count for _, count in options)
    points = []
    for target in TARGETS:
        threshold, count = min(options, key=lambda pair: (
            abs(100 * pair[1] - target * n), 100 * pair[1] < target * n, -pair[0]))
        point = {"target": target / 100, "threshold": threshold, "inner_answered": count,
                 "inner_coverage": count / n, "inner_max_coverage": maximum / n,
                 "inner_target_reachable": 100 * maximum >= target * n,
                 "inner_within_tolerance": abs(100 * count - target * n) <= TOLERANCE * n}
        if arm == "M3":
            point.update(lo=1 - threshold, hi=threshold)
        points.append(point)
    return points


def policy_metrics(predictions, labels, target, conflicts):
    counts = {y: Counter() for y in (0, 1)}
    for item, y in zip(predictions, labels, strict=True):
        by_class = counts[y]
        by_class["rows"] += 1
        if item.action == graph.ABSTAIN:
            by_class["referrals"] += 1
        else:
            by_class["answered"] += 1
            by_class["errors"] += int((item.action == graph.PREDICT_ENTRY) != bool(y))
    answered = sum(c["answered"] for c in counts.values())
    errors = sum(c["errors"] for c in counts.values())
    n = len(labels)
    area = t2._aurc80(predictions, labels)
    return {"rows": n, "coverage": answered / n, "answered": answered, "errors": errors,
            "within_tolerance": abs(Fraction(answered, n) - Fraction(str(target)))
            <= Fraction(TOLERANCE, 100), "selective_risk": errors / answered if answered else None,
            "referrals": n - answered, "blocked_conflict_referrals": conflicts,
            "aurc80_reachable": isfinite(area), "aurc80": area if isfinite(area) else None,
            "class_wise": {str(y): {**dict.fromkeys(("rows", "answered", "errors", "referrals"), 0),
                                     **c, "error_rate": c["errors"] / c["answered"] if c["answered"] else None}
                           for y, c in counts.items()}}
