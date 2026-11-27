"""Native-rank queues and paired whole-drug inference for criteria v3."""
from dataclasses import dataclass
from math import ceil, sqrt
from statistics import NormalDist

import numpy as np

from .power import ARM_PAIRS, PAIR_NAMES, histories, variance_report, weights


ARMS = ("B1", "M1", "M3")
ALPHAS = (.025, .020)
AGE_EDGES = np.array([3, 5, 7, 10, 15, 22, 30])


@dataclass(frozen=True)
class Panel:
    drug: np.ndarray
    cutoff: np.ndarray
    age: np.ndarray
    event: np.ndarray
    clusters: int


def panels(history, scenario, rng):
    drug, cutoff, age, event = histories(history, scenario, rng)
    for h in range(2):
        keep = cutoff < scenario.years + h
        yield Panel(drug[keep], cutoff[keep], age[keep], event[keep, h],
                    scenario.clusters + h * scenario.extra_clusters)


def point_queue(scores, event):
    """Expected inclusion per row under the uniform lottery in an exact tie."""
    _, inverse, sizes = np.unique(-scores, return_inverse=True, return_counts=True)
    fraction = np.clip(len(scores) // 5 - (np.cumsum(sizes) - sizes), 0, sizes) / sizes
    selected = fraction[inverse]
    boundary = np.flatnonzero((fraction > 0) & (fraction < 1))
    tie = int(sizes[boundary[0]]) if len(boundary) else 0
    return selected[event].sum(), selected, tie


def diagnostics(panel, score):
    result = []
    for t in np.unique(panel.cutoff):
        idx = panel.cutoff == t
        y = panel.event[idx]
        queues = [point_queue(column, y) for column in score[idx].T]
        q = np.stack([item[1][y] for item in queues], axis=1)
        slots = int(idx.sum()) // 5
        result.append(np.array([[idx.sum(), y.sum(), slots],
                                [item[0] for item in queues],
                                [item[2] for item in queues],
                                [np.abs(q[:, a] - q[:, b]).sum() for a, b in ARM_PAIRS]]))
    return np.array(result)


@dataclass(frozen=True)
class Queue:
    cutoff: int
    arm: int
    ordered_drugs: np.ndarray
    event_drugs: np.ndarray
    event_start: np.ndarray
    event_end: np.ndarray
    anchor_columns: tuple[int, int]
    before: np.ndarray
    inside: np.ndarray
    start_columns: np.ndarray
    end_columns: np.ndarray


def queue_layout(panel, score):
    """Encode prefixes at relevant event ties and certify the rest by two anchors."""
    prefixes, queues = [panel.drug[panel.event]], []
    cutoff_columns = []
    for t in np.unique(panel.cutoff):
        idx = np.flatnonzero(panel.cutoff == t)
        cutoff_column = len(prefixes)
        cutoff_columns.append(cutoff_column)
        prefixes.append(panel.drug[idx])
        if not panel.event[idx].any():
            continue
        n = len(idx)
        margin = max(16, ceil(4 * sqrt(.16 * n)))
        for arm, column in enumerate(score.T):
            rank = idx[np.argsort(-column[idx], kind="stable")]
            drug = panel.drug[rank]
            positions = np.flatnonzero(panel.event[rank])
            values = -column[rank]
            start = np.searchsorted(values, values[positions], side="left")
            end = np.searchsorted(values, values[positions], side="right")
            lo = np.searchsorted(values, values[max(0, n // 5 - margin)], side="left")
            hi = np.searchsorted(values, values[min(n - 1, n // 5 + margin)], side="right")
            middle = np.flatnonzero((end > lo) & (start < hi))
            # For continuous ranks the tie width is the event row's weight.
            tied_end = np.where(end[middle] - start[middle] > 1, end[middle], start[middle])
            edges, mapped = np.unique(np.r_[lo, hi, start[middle], tied_end], return_inverse=True)
            cols = mapped + len(prefixes)
            prefixes.extend(drug[:edge] for edge in edges)
            queues.append(Queue(cutoff_column, arm, drug, drug[positions], start, end,
                                tuple(cols[:2]), np.flatnonzero(end <= lo), middle,
                                cols[2:2 + len(middle)], cols[2 + len(middle):]))
    design = np.zeros((len(prefixes), panel.clusters), dtype=np.float32)
    for col, drug in enumerate(prefixes):
        np.add.at(design[col], drug, 1)
    return design.T, queues, cutoff_columns


def queued_events(layout, counts):
    """Exact resampled capture, including fallback for draws beyond the anchors."""
    design, queues, cutoff_columns = layout
    totals = counts @ design
    capture = np.zeros((len(counts), max((q.arm for q in queues), default=-1) + 1))
    for q in queues:
        k = totals[:, q.cutoff] // 5
        good = (totals[:, q.anchor_columns[0]] <= k) & (k <= totals[:, q.anchor_columns[1]])
        inside_weights = counts[:, q.event_drugs[q.inside]]
        a = totals[:, q.start_columns].astype(np.float64)
        width = np.where(q.end_columns != q.start_columns,
                         totals[:, q.end_columns] - a, inside_weights)
        fraction = np.clip(k[:, None] - a, 0, width) / np.maximum(width, 1)
        hit = counts[:, q.event_drugs[q.before]].sum(axis=1) + (fraction * inside_weights).sum(axis=1)
        # Float64 for the same fractional arithmetic on both paths and arms.
        if np.any(~good):
            rare = counts[~good]
            prefix = np.column_stack((np.zeros(len(rare)), rare[:, q.ordered_drugs].cumsum(axis=1)))
            width = prefix[:, q.event_end] - prefix[:, q.event_start]
            f = np.clip(k[~good, None] - prefix[:, q.event_start], 0, width) / np.maximum(width, 1)
            capture[~good, q.arm] += (f * rare[:, q.event_drugs]).sum(axis=1)
        capture[good, q.arm] += hit[good]
    return capture, totals[:, 0], (totals[:, cutoff_columns] // 5).sum(axis=1)


def recalls(panel, score, counts):
    if not panel.event.any():
        return np.full((len(counts), score.shape[1]), np.nan)
    hits, events, _ = queued_events(queue_layout(panel, score), counts)
    return np.divide(hits, events[:, None], out=np.full_like(hits, np.nan), where=events[:, None] > 0)


def contrasts(recall):
    return np.stack([recall[..., a] - recall[..., b] for a, b in ARM_PAIRS], axis=-1)


def lower_bounds(deltas, alpha):
    """Use the empirical lower order statistic and fail on any undefined draw."""
    k = int(len(deltas) * alpha)
    return np.where(np.isfinite(deltas).all(axis=0), np.partition(deltas, k, axis=0)[k], np.nan)


def paired_draws(panel, scores, rng, draws, comparisons):
    if not panel.event.any():
        return np.full((draws, len(comparisons)), np.nan)
    hits, events, _ = queued_events(queue_layout(panel, scores), weights(rng, draws, panel.clusters))
    delta = np.column_stack([hits[:, a] - hits[:, b] for a, b in comparisons])
    # Fractionally tied queue totals can differ through summation order alone.
    delta[np.abs(delta) <= 1e-12] = 0
    return np.divide(delta, events[:, None], out=np.full_like(delta, np.nan), where=events[:, None] > 0)


def interval(success, total):
    if not total:
        return {"count": int(success), "denominator": int(total), "rate": None, "wilson_95": None}
    z = NormalDist().inv_cdf(.975)
    p = success / total
    denom = 1 + z**2 / total
    mid = (p + z**2 / (2 * total)) / denom
    half = z * sqrt(p * (1 - p) / total + z**2 / (4 * total**2)) / denom
    return {"count": int(success), "denominator": int(total), "rate": float(p),
            "wilson_95": [max(0., mid - half), min(1., mid + half)]}


def decision_rates(bounds, true_nulls=()):
    valid = np.isfinite(bounds)
    passed = bounds > 0
    reached = np.column_stack((np.ones(len(bounds), dtype=bool), np.logical_and.accumulate(passed, axis=1)[:, :-1]))
    reject = passed & reached
    result = {}
    for h in range(bounds.shape[1]):
        at_step = reached[:, h]
        result[f"H{h + 1}"] = {"marginal": interval(passed[:, h].sum(), len(bounds)),
                              "conditional": interval(reject[:, h].sum(), at_step.sum()),
                              "sequence": interval(reject[:, h].sum(), len(bounds)),
                              "unevaluable": interval((~valid[:, h]).sum(), len(bounds))}
    result["full_sequence"] = interval(reject[:, -1].sum(), len(bounds))
    if true_nulls:
        result["familywise_error"] = interval(reject[:, list(true_nulls)].any(axis=1).sum(), len(bounds))
    return result


def age_index(age):
    return np.clip(age, 0, 30).astype(int)


def centered_year(cutoff):
    return (cutoff - (cutoff.min() + cutoff.max()) / 2) / max(1, (cutoff.max() - cutoff.min()) / 2)


def features(panel, b1):
    age = np.searchsorted(AGE_EDGES, panel.age)
    return np.column_stack((np.ones(len(age)), np.eye(len(AGE_EDGES) + 1)[age],
                            centered_year(panel.cutoff), b1[age_index(panel.age)], panel.event))


@dataclass(frozen=True)
class RankFit:
    b1: np.ndarray
    b1_rank: np.ndarray
    beta: np.ndarray
    scale: np.ndarray
    pair: float
    persistence: float


def fit_ranks(panel, scores, b1):
    _, index, count = np.unique(b1, return_inverse=True, return_counts=True)
    b1_rank = (np.cumsum(count) - count / 2)[index] / len(b1) - .5
    normal = NormalDist()
    rank = np.empty_like(scores[:, 1:])
    for i, column in enumerate(scores[:, 1:].T):
        _, index, count = np.unique(column, return_inverse=True, return_counts=True)
        rank[:, i] = [normal.inv_cdf(x) for x in (np.cumsum(count) - count / 2)[index] / len(column)]
    x = features(panel, b1_rank)
    penalty = np.diag([.01, *([10.] * (len(AGE_EDGES) + 1)), 10., 10., .1])
    beta = np.linalg.solve(x.T @ x + penalty, x.T @ rank)
    residual = rank - x @ beta
    scale = np.array([residual[panel.event == y].std(axis=0, ddof=1) for y in (False, True)])
    standardized = residual / scale[panel.event.astype(int)]
    order = np.lexsort((panel.cutoff, panel.drug))
    a, b = order[:-1], order[1:]
    consecutive = (panel.drug[a] == panel.drug[b]) & (panel.cutoff[b] - panel.cutoff[a] == 1)
    persistence = np.corrcoef(standardized[a[consecutive]].ravel(), standardized[b[consecutive]].ravel())[0, 1]
    pair = np.corrcoef(standardized.T)[0, 1]
    return RankFit(b1, b1_rank, beta, scale, float(np.clip(pair, 0, .999)),
                   float(np.clip(persistence, 0, .98)))


def native_scores(panel, fit, drug_z, row_z, *, exchangeable=False, pair=None, clock_weight=0.):
    """Keep B1's fitted age-clock scores and share Gaussian drug and row effects."""
    pair = fit.pair if pair is None else pair
    z = sqrt(fit.persistence) * drug_z[panel.drug] + sqrt(1 - fit.persistence) * row_z
    z[:, 1] = pair * z[:, 0] + sqrt(1 - pair**2) * z[:, 1]
    beta = fit.beta.mean(axis=1, keepdims=True) if exchangeable else fit.beta
    scale = fit.scale.mean(axis=1, keepdims=True) if exchangeable else fit.scale
    x = features(panel, fit.b1_rank)
    regulatory = x @ beta + scale[panel.event.astype(int)] * z + clock_weight * x[:, -2, None]
    return np.column_stack((fit.b1[age_index(panel.age)], regulatory))


def breakpoints(panel, score):
    """Exact event-score shifts where top-fifth inclusion changes, per cutoff."""
    thresholds = []
    for t in np.unique(panel.cutoff):
        mask = panel.cutoff == t
        event = panel.event[mask]
        positive = np.sort(score[mask][event])[::-1]
        negative = np.sort(score[mask][~event])[::-1]
        r = len(event) // 5 - 1 - np.arange(len(positive))
        cut = np.clip(r, 0, max(0, len(negative) - 1))
        if len(negative):
            middle = negative[cut] - positive
        else:
            middle = np.zeros(len(positive))
        thresholds.append(np.where(r < 0, np.inf, np.where(r >= len(negative), -np.inf, middle)))
    return np.concatenate(thresholds)


def tilt_for(thresholds, target):
    ordered = np.sort(thresholds)
    k = round(target * len(ordered))
    if not 0 < k < len(ordered) or not np.isfinite(ordered[[k - 1, k]]).all():
        raise ValueError(f"Cannot calibrate requested recall {target:.4f}")
    return float((ordered[k - 1] + ordered[k]) / 2)


def tied_null(score, noise):
    """Exchangeable re-orderings within real B1 ties have exact null expected recall."""
    _, blocks = np.unique(score, return_inverse=True)
    return blocks[:, None] + (np.arctan(noise) / np.pi + .5) * .9
