"""Synthetic cluster power for the sealed LOE-Bench fixed sequence."""
from dataclasses import dataclass
from math import ceil, sqrt

import numpy as np


ALPHA = 0.025
COVERAGE = 0.8
CONTRASTS = ("H1", "H2", "H3")
LEVELS = 12
EFFECT = 0.010


@dataclass(frozen=True)
class Profile:
    # Rows are age at first observed cutoff, its zero-based index, and event lag.
    non_events: np.ndarray
    events: np.ndarray
    extra_arrivals: np.ndarray
    years: int
    age_edges: np.ndarray
    age_means: np.ndarray
    skill: np.ndarray
    arm_correlations: np.ndarray
    cluster_correlation: np.ndarray
    abstention: np.ndarray
    call_entry: np.ndarray


@dataclass(frozen=True)
class Scenario:
    name: str
    clusters: int
    extra_clusters: int
    years: int
    event_clusters: int
    correlation: float | None = None
    young: bool = False
    coverage_stress: bool = False


def histories(profile, scenario, rng, multiplier=1):
    """Resample development templates and emit synthetic annual at-risk rows."""
    events = profile.events
    non_events = profile.non_events
    if scenario.young:
        events = events[(events[:, 0] <= 5) & (events[:, 0] + events[:, 2] >= 5)]
        non_events = non_events[non_events[:, 0] <= 5]
    n_events = scenario.event_clusters * multiplier
    n_main = scenario.clusters * multiplier
    n_extra = scenario.extra_clusters * multiplier
    event = events[rng.integers(len(events), size=n_events)]
    other = non_events[rng.integers(len(non_events), size=n_main - n_events)]
    extra = profile.extra_arrivals[rng.integers(len(profile.extra_arrivals), size=n_extra)]
    templates = np.concatenate((event, other, extra))
    latest = scenario.years - 1
    start = np.rint(templates[:, 1] * latest / (profile.years - 1)).astype(int)
    start[n_main:] = scenario.years
    end = np.full(n_main + n_extra, scenario.years + 2)
    lag = event[:, 2].astype(int) + rng.integers(0, 2, size=n_events)
    if scenario.young:
        # Age is evaluated during the event interval, allowing a conservative
        # lower bound at the interval's end without introducing new events.
        start[:n_events] = np.minimum(start[:n_events], latest + 2 - lag)
    end[:n_events] = np.minimum(start[:n_events] + lag, latest + 2)
    year = np.arange(scenario.years + 1)
    cluster, cutoff = np.nonzero((start[:, None] <= year) & (year < end[:, None]))
    age = templates[cluster, 0] + cutoff - start[cluster]
    band = np.searchsorted(profile.age_edges, age)
    distance = end[cluster] - cutoff
    event_mask = cluster < n_events
    outcomes = np.column_stack((event_mask & (distance <= 2), event_mask & (distance <= 1)))
    return cluster, cutoff, band, outcomes


def synthetic(profile, scenario, rng, multiplier=1):
    """Keep one shared event process and share latent drug/row noise across horizons."""
    cluster, cutoff, band, outcomes = histories(profile, scenario, rng, multiplier)
    cluster_noise = rng.standard_normal(((scenario.clusters + scenario.extra_clusters) * multiplier, 3))
    row_noise = rng.standard_normal((len(cluster), 3))
    common_call = rng.random(len(cluster))
    result = []
    for index, mask in enumerate((cutoff < scenario.years, np.ones(len(cutoff), dtype=bool))):
        ids, labels = cluster[mask], outcomes[mask, index]
        corr = profile.arm_correlations[index]
        if scenario.correlation is not None:
            corr = np.full((3, 3), scenario.correlation)
            np.fill_diagonal(corr, 1)
        factor = np.linalg.cholesky(corr)
        dependence = profile.cluster_correlation[index]
        noise = (sqrt(dependence) * cluster_noise[ids] +
                 sqrt(1 - dependence) * row_noise[mask]) @ factor.T
        baseline = profile.age_means[index, band[mask], None] + noise
        error = (common_call[mask] < profile.call_entry[index, labels.astype(int)]) != labels
        result.append((ids, error, baseline, labels))
    return result


def confidence(score, skill, errors):
    return score - skill * errors


def score_bins(cutpoint):
    """Rank high to low, with a separate bin for the abstention boundary."""
    edges = np.linspace(-2.4, 2.4, LEVELS - 2)
    replace = np.argmin(np.abs(edges - cutpoint))
    edges[replace] = cutpoint
    return np.sort(edges)


def bins(score, edges):
    return len(edges) - np.searchsorted(edges, score, side="right")


def area(count, errors, total, harmonic):
    """FIX1 right-step AURC80, integrated over all row prefixes within a tie.

    At prefix j of a tie with error fraction p, risk is
    p + (previous_errors - previous_count * p) / (previous_count + j).
    """
    count = np.asarray(count, dtype=np.int32)
    cumulative = np.cumsum(count, axis=-1, dtype=np.int32)
    previous = cumulative - count
    target = COVERAGE * np.asarray(total)[..., None]
    stop = np.minimum(cumulative, np.floor(target).astype(np.int32))
    width = np.maximum(stop - previous, 0)
    rate = np.divide(errors, count, out=np.zeros_like(errors, dtype=float), where=count != 0)
    prior_errors = np.cumsum(errors, axis=-1) - errors
    residual = prior_errors - previous * rate
    integral = width * rate + residual * (harmonic[previous + width] - harmonic[previous])
    last = (previous <= np.floor(target)) & (cumulative > np.floor(target))
    fractional = (target - np.floor(target)) * (
        rate + residual / (np.floor(target) + 1)) * last
    return np.where(cumulative[..., -1] >= target[..., 0],
                    (integral + fractional).sum(axis=-1) / target[..., 0], np.nan)


def harmonic_numbers(size):
    return np.r_[0.0, np.cumsum(1 / np.arange(1, size + 1))]


def population_area(score, error, skill, edges, threshold, harmonic):
    adjusted = confidence(score, skill, error)
    selected = adjusted >= threshold
    ranks = bins(adjusted[selected], edges)
    k = len(edges) + 1
    counts = np.bincount(ranks, minlength=k)
    errors = np.bincount(ranks, weights=error[selected], minlength=k)
    return float(area(counts, errors, len(score), harmonic))


def calibration(profile, scenario, rng, multiplier, effect=EFFECT):
    """Find a common comparator skill and improve M3's error ranking."""
    settings = []
    for h, (_, error, scores, _) in enumerate(synthetic(profile, scenario, rng, multiplier)):
        # Pool identically distributed latent margins to stabilize calibration.
        score = scores.ravel()
        error = np.repeat(error, scores.shape[1])
        harmonic = harmonic_numbers(len(score))

        def rating(skill, edges):
            return population_area(score, error, skill, edges, -np.inf, harmonic)

        base = float(profile.skill[h])
        probe = score_bins(-1.5)
        if rating(base, probe) < effect + 0.003:
            left, right = -6.0, base
            for _ in range(18):
                mid = (left + right) / 2
                if rating(mid, probe) >= effect + 0.003:
                    left = mid
                else:
                    right = mid
            base = left
        coverage = (0.177, 0.188) if scenario.coverage_stress else profile.abstention[h]
        cutpoints = [float(np.quantile(confidence(score, base, error), rate)) if rate else -np.inf
                     for rate in coverage]
        edges = score_bins(max(value for value in cutpoints if np.isfinite(value))
                           if any(np.isfinite(cutpoints)) else -1.5)
        # Partition at both abstention thresholds, keeping all ties intact.
        edges = np.unique(np.r_[edges, [value for value in cutpoints if np.isfinite(value)]])
        target = rating(base, edges) - effect
        left, right = base, 8.0
        if rating(right, edges) > target:
            improved = None
        else:
            for _ in range(22):
                mid = (left + right) / 2
                if rating(mid, edges) > target:
                    left = mid
                else:
                    right = mid
            improved = (left + right) / 2
        settings.append({
            "base_skill": base,
            "development_skill": float(profile.skill[h]),
            "useful_skill": improved,
            "edges": edges.tolist(),
            "cutpoints": [value if np.isfinite(value) else None for value in cutpoints],
        })
    return settings


def skills_for(settings, configuration, horizon):
    base, useful = settings["base_skill"], settings["useful_skill"]
    if configuration == "null" or (configuration == "H3_null" and horizon == 1):
        return base, base, base
    if useful is None:
        raise ValueError("calibration could not support the useful effect")
    return base, useful if configuration == "H2_null" and horizon == 0 else base, useful


def arm_table(ids, error, score, settings, configuration, horizon, clusters):
    """Compress all rows from a drug into counts by confidence bin and arm."""
    edges = np.asarray(settings["edges"])
    k = len(edges) + 1
    table = [np.bincount(ids, minlength=clusters)]
    cutpoints = [-np.inf, *[x if x is not None else -np.inf for x in settings["cutpoints"]]]
    for i, (skill, cutpoint) in enumerate(zip(skills_for(settings, configuration, horizon), cutpoints)):
        adjusted = confidence(score[:, i], skill, error)
        selected = adjusted >= cutpoint
        index = ids[selected] * k + bins(adjusted[selected], edges)
        for weights in (None, error[selected]):
            counts = np.bincount(index, weights=weights, minlength=clusters * k)
            table.extend(counts.reshape(clusters, k).T)
    return np.asarray(table, dtype=np.float32).T.copy()


def areas_from_totals(totals, harmonic):
    total = totals[..., 0]
    counts = totals[..., 1:].reshape((*total.shape, 3, 2, -1))
    return area(counts[..., 0, :], counts[..., 1, :], total[..., None], harmonic)


def weights(rng, draws, clusters):
    """Multinomial counts from exactly N draws of whole drugs with replacement."""
    choices = rng.integers(clusters, size=(draws, clusters), dtype=np.int32)
    choices += (np.arange(draws, dtype=np.int32) * clusters)[:, None]
    return np.bincount(choices.ravel(), minlength=draws * clusters).reshape(draws, clusters).astype(np.float32)


def upper_percentiles(deltas):
    upper, invalid = [], []
    for values in deltas.T:
        finite = values[np.isfinite(values)]
        invalid.append(len(values) - len(finite))
        if len(finite):
            k = int((1 - ALPHA) * len(finite))
            upper.append(float(np.partition(finite, k)[k]))
        else:
            upper.append(np.nan)
    return upper, invalid


def verify_population(profile, scenario, settings, rng, multiplier, configuration):
    deltas, prevalence, coverage, rows, correlations = [], [], [], [], []
    for h, ((ids, error, score, labels), setting) in enumerate(
        zip(synthetic(profile, scenario, rng, multiplier), settings)
    ):
        table = arm_table(ids, error, score, setting, configuration, h, int(ids.max()) + 1)
        totals = table.sum(axis=0, dtype=np.float64)
        areas = areas_from_totals(totals, harmonic_numbers(len(ids)))
        coverage.append((totals[1:].reshape(3, 2, -1)[:, 0].sum(axis=1) / len(ids)).tolist())
        prevalence.append(float(labels.mean()))
        rows.append(len(ids))
        adjusted = score - error[:, None] * skills_for(setting, configuration, h)
        correlations.append(np.corrcoef(adjusted.T).tolist())
        deltas.extend((areas[2] - areas[0], areas[2] - areas[1]) if h == 0 else (areas[2] - areas[0],))
    return {"delta": deltas, "prevalence": prevalence, "coverage": coverage,
            "rows": rows, "clusters_24": scenario.clusters * multiplier,
            "events_24": scenario.event_clusters * multiplier, "confidence_correlation": correlations}


def single_dataset(profile, scenario, settings, rng, bootstrap_rng, draws, configuration, check_draws=0):
    upper = np.full(3, np.nan)
    full_upper = upper.copy()
    invalid = np.zeros(3, dtype=int)
    coverage_failure = np.zeros(3, dtype=bool)
    max_draws = max(draws, check_draws)
    for h, ((ids, error, score, _), setting) in enumerate(zip(synthetic(profile, scenario, rng), settings)):
        n_clusters = scenario.clusters + (scenario.extra_clusters if h else 0)
        # Each synthetic cluster contains at most one row per annual cutoff.
        harmonic = harmonic_numbers(n_clusters * (scenario.years + h))
        table = arm_table(ids, error, score, setting, configuration, h, n_clusters)
        observed = areas_from_totals(table.sum(axis=0), harmonic)
        right = [0, 1] if h == 0 else [0]
        at = slice(0, 2) if h == 0 else slice(2, 3)
        coverage_failure[at] = ~(np.isfinite(observed[2]) & np.isfinite(observed[right]))
        # Always advance each horizon's seed so a coverage failure cannot re-key
        # the other horizon or change the matched verification stream.
        horizon_rng = np.random.default_rng(bootstrap_rng.integers(2**63))
        if coverage_failure[at].all():
            continue
        sampled = weights(horizon_rng, max_draws, n_clusters) @ table
        areas = areas_from_totals(sampled, harmonic)
        delta = areas[:, 2, None] - areas[:, right]
        upper[at], invalid[at] = upper_percentiles(delta[:draws])
        if check_draws:
            full_upper[at], _ = upper_percentiles(delta[:check_draws])
    upper[coverage_failure] = np.nan
    full_upper[coverage_failure] = np.nan
    return upper, coverage_failure, invalid, full_upper


def proportion(count, total):
    """Wilson Monte Carlo interval, with a missing conditional denominator."""
    if not total:
        return {"n": int(count), "denominator": 0, "rate": None, "ci95": None}
    z = 1.959963984540054
    p = count / total
    scale = 1 + z * z / total
    center = (p + z * z / (2 * total)) / scale
    half_width = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / scale
    return {"n": int(count), "denominator": total, "rate": float(p),
            "ci95": [max(0., center - half_width), min(1., center + half_width)]}


def fixed_sequence(upper):
    marginal = upper < 0
    return marginal, np.logical_and.accumulate(marginal, axis=1)


def operating_rates(upper):
    marginal, sequence = fixed_sequence(upper)
    n = len(upper)
    reached = [n, int(sequence[:, 0].sum()), int(sequence[:, 1].sum())]
    return {label: {
        "marginal": proportion(marginal[:, i].sum(), n),
        "overall": proportion(sequence[:, i].sum(), n),
        "conditional": proportion(sequence[:, i].sum(), reached[i]),
    } for i, label in enumerate(CONTRASTS)}


def estimate_mde(upper, reference_effect):
    """Location-shift approximation with unevaluable runs counted as failures."""
    residual = np.where(np.isfinite(upper), upper + reference_effect, np.inf)
    rank = ceil(0.8 * len(residual)) - 1
    threshold = np.partition(residual, rank)[rank]
    return max(0., float(threshold)) if np.isfinite(threshold) else None


def simulate(profile, scenario, settings, seed, repetitions, draws, configuration,
             check_repetitions=0, check_draws=2000):
    rng = np.random.default_rng(seed)
    upper = np.empty((repetitions, 3))
    full = np.empty((check_repetitions, 3))
    coverage_failures = np.zeros((repetitions, 3), dtype=bool)
    invalid_draws = np.zeros(3, dtype=int)
    for i in range(repetitions):
        data_rng, boot_rng = (np.random.default_rng(key) for key in rng.integers(2**63, size=2))
        upper[i], coverage_failures[i], invalid, checked = single_dataset(
            profile, scenario, settings, data_rng, boot_rng, draws, configuration,
            check_draws if i < check_repetitions else 0,
        )
        invalid_draws += invalid
        if i < check_repetitions:
            full[i] = checked
    result = {
        "repetitions": repetitions,
        "draws": draws,
        "rates": operating_rates(upper),
        "coverage_failure": {label: proportion(coverage_failures[:, i].sum(), repetitions)
                             for i, label in enumerate(CONTRASTS)},
        "no_finite_draws_after_coverage_gate": ((~np.isfinite(upper)) & ~coverage_failures).sum(axis=0).tolist(),
        "invalid_draws": invalid_draws.tolist(),
    }
    if configuration == "useful":
        result["H1_mde80_magnitude_location_shift"] = estimate_mde(upper[:, 0], EFFECT)
    if check_repetitions:
        reduced = upper[:check_repetitions]
        a, b = fixed_sequence(reduced)[1], fixed_sequence(full)[1]
        result["full_draw_check"] = {
            "repetitions": check_repetitions, "draws": check_draws,
            "reduced_rates": operating_rates(reduced), "full_rates": operating_rates(full),
            "sequence_disagreements": np.count_nonzero(a != b, axis=0).tolist(),
        }
    return result
