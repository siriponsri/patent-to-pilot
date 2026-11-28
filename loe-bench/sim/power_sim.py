"""CPU-only POWER-SIM. The only data input is the pinned T4c aggregate."""

from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from datetime import date
from functools import lru_cache
import hashlib
from itertools import product
import json
from math import sqrt
from pathlib import Path
import platform
from statistics import NormalDist
import sys
from time import perf_counter

import numpy as np

try:
    import numba
except ImportError:
    numba = None

LOE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(LOE))
from loe_bench.power_v3 import AGE_EDGES, decision_rates, interval  # noqa: E402


T4C_BLOB = "569716a98204403f5ef18a124020b385a713bdd3"
N = 651
ARRIVALS = 22 * N / 539
ALPHA = 0.025
Z = NormalDist().inv_cdf(1 - ALPHA)
SEEDS = {"calibration": 2026112801, "screen": 2026112802, "filing": 2026112803,
         "effect_check": 2026112804, "validation": 2026112805}
EFFECTS = tuple((a, b) for a in (.10, .2037) for b in (0., .0136, .02, .05))
PAIRS = ((2, 0), (2, 1))


@dataclass(frozen=True)
class Design:
    name: str
    months: tuple[int, ...]
    horizon: int = 24
    countries: int = 1

    @property
    def start(self):
        return date(2026, 11, 27) if self.name == "A" else date(2027, 4, 1)

    def shifted(self, months):
        year, month = divmod(self.start.month - 1 + months, 12)
        return date(self.start.year + year, month + 1, self.start.day)


def schedule(step, stop=126):
    return (*range(0, stop, step), stop)


DESIGNS = (
    Design("A", (0,)), Design("B", schedule(3)), Design("C", schedule(12)),
    Design("D", schedule(24)), Design("E", schedule(3), 36),
    Design("F", schedule(12), countries=2), Design("monthly", schedule(1)),
    Design("quarterly_4y", schedule(3, 48)), Design("quarterly_8y", schedule(3, 96)),
)


@dataclass(frozen=True)
class Setting:
    us: int = 51
    canada: int = 32
    persistence: float = .8
    shock: float = 0.
    pair: float | None = None
    young: bool = False
    tie_null: bool = False


CENTRAL = Setting()
SENSITIVITIES = {
    "low_incidence": replace(CENTRAL, us=32), "high_incidence": replace(CENTRAL, us=70),
    "lower_persistence": replace(CENTRAL, persistence=.5),
    "higher_persistence": replace(CENTRAL, persistence=.95),
    "calendar_shocks": replace(CENTRAL, shock=.30),
    "lower_cross_arm_correlation": replace(CENTRAL, pair=.90),
    "younger_faster_arrivals": replace(CENTRAL, young=True),
    "within_tie_null": replace(CENTRAL, tie_null=True),
    "low_canada_incidence": replace(CENTRAL, canada=16),
    "high_canada_incidence": replace(CENTRAL, canada=51),
}


@dataclass(frozen=True)
class Stratum:
    drugs: np.ndarray
    event: np.ndarray
    b1: np.ndarray
    regulatory: np.ndarray
    tie_noise: np.ndarray | None

    def scores(self, shifts):
        if self.tie_noise is None:
            reg = self.regulatory + self.event[:, None] * shifts
        else:
            bins = np.floor((self.regulatory.mean(axis=1) + self.event * shifts[0]) / .25)
            reg = bins[:, None] + self.tie_noise
        return np.column_stack((self.b1, reg))


def source():
    payload = (LOE / "data" / "T4c_power.json").read_bytes().replace(b"\r\n", b"\n")
    blob = hashlib.sha1(f"blob {len(payload)}\0".encode() + payload).hexdigest()
    if blob != T4C_BLOB:
        raise ValueError("T4c aggregate differs from protocol pin")
    return json.loads(payload), hashlib.sha256(payload).hexdigest()


def stream(stage, design, setting_id, replicate=None):
    key = (DESIGNS.index(design), setting_id)
    if replicate is not None:
        key = (*key, replicate)
    return np.random.default_rng(np.random.SeedSequence(SEEDS[stage], spawn_key=key))


def initial_ages(young):
    p = 1 / (11 if young else 18)
    masses = p * (1 - p) ** np.arange(31)
    masses[-1] = (1 - p) ** 30
    return masses


@lru_cache(maxsize=None)
def rate_scale(event_count, young, hazards):
    hazards = np.asarray(hazards)
    two_year = hazards + hazards[np.minimum(np.arange(31) + 1, 30)]
    nodes, weights = np.polynomial.hermite.hermgauss(24)
    frailty = np.exp(.5 * sqrt(2) * nodes - .5 * .5**2)
    exposure = two_year[:, None] * frailty
    weights = initial_ages(young)[:, None] * weights / sqrt(np.pi)
    lo, hi = 0., 10.
    for _ in range(50):
        mid = (lo + hi) / 2
        if (-np.expm1(-mid * exposure) * weights).sum() < event_count / N:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def approval_times(entry, birth, years, hazards, scale, frailty, shock_sd, rng):
    starts = np.arange(years)[:, None]
    ages = np.clip(np.floor(starts + .5 - birth), 0, 30).astype(int)
    hazard = scale * hazards[ages] * frailty
    shock = np.exp(rng.normal(0., shock_sd, (years, 1)) - .5 * shock_sd**2)
    hazard *= shock
    observable_start = np.maximum(starts, entry)
    cumulative = np.cumsum(hazard * np.clip(starts + 1 - observable_start, 0., 1.), axis=0)
    clock = rng.exponential(size=len(entry))
    crossed = cumulative >= clock
    columns = np.flatnonzero(crossed.any(axis=0))
    year = crossed[:, columns].argmax(axis=0)
    previous = np.where(year > 0, cumulative[year - 1, columns], 0.)
    times = np.full(len(entry), np.inf)
    times[columns] = observable_start[year, columns] + (clock[columns] - previous) / hazard[year, columns]
    return times


def make_panel(design, settings, fits, rng):
    origins = np.asarray(design.months) / 12
    stop = origins[-1]
    ages = rng.choice(31, N, p=initial_ages(settings.young))
    new = rng.poisson(stop * ARRIVALS * (2 if settings.young else 1))
    arrivals = np.sort(rng.uniform(0., stop, new))
    entry = np.r_[np.zeros(N), arrivals]
    birth = np.r_[-ages, arrivals]
    frailty = np.exp(rng.normal(0., .5, len(entry)) - .5 * .5**2)
    drug_noise = rng.standard_normal((len(entry), 2))
    hazards = -.5 * np.log1p(-np.asarray(fits[24]["b1"]))
    horizons = (24, 12) if design.name == "A" else (design.horizon,)
    panels = {h: [] for h in horizons}
    years = int(np.ceil(stop + design.horizon / 12))
    event_times = []
    for count in (settings.us, settings.canada)[:design.countries]:
        scale = rate_scale(count, settings.young, tuple(hazards))
        times = approval_times(entry, birth, years, hazards, scale, frailty, settings.shock, rng)
        event_times.append(times)
        for origin in origins:
            drugs = np.flatnonzero((entry <= origin) & (origin < times))
            age = np.floor(origin - birth[drugs]).astype(int)
            age_idx = np.minimum(age, 30)
            bins = np.searchsorted(AGE_EDGES, age)
            noise = sqrt(settings.persistence) * drug_noise[drugs]
            noise += sqrt(1 - settings.persistence) * rng.standard_normal((len(drugs), 2))
            tied = rng.random((len(drugs), 2)) if settings.tie_null else None
            for horizon in horizons:
                fit = fits[min(horizon, 24)]
                event = times[drugs] <= origin + horizon / 12
                pair = fit["pair"] if settings.pair is None else settings.pair
                residual = np.column_stack((noise[:, 0], pair * noise[:, 0] + sqrt(1 - pair**2) * noise[:, 1]))
                beta, sigma, b1_rank = fit["pooled"]
                center = beta[0] + beta[1 + bins] + beta[-2] * b1_rank[age_idx] + beta[-1] * event
                model = center[:, None] + sigma[event.astype(int), None] * residual
                panels[horizon].append(Stratum(drugs, event, fit["b1"][age_idx], model, tied))
    return panels, len(entry)


def unpack_fits(doc):
    fits = {}
    for horizon in (12, 24):
        fit = dict(doc["variance"][str(horizon)]["fit"])
        fit["b1"] = np.asarray(fit["b1"])
        fit["pooled"] = (np.mean(fit["beta"], axis=1), np.mean(fit["scale"], axis=1),
                         np.asarray(fit["b1_rank"]))
        fits[horizon] = fit
    return fits


def allocation(scores, sorted_scores, k):
    if k == 0:
        return np.zeros(len(scores))
    boundary = sorted_scores[-k]
    above = scores > boundary
    tied = scores == boundary
    return above + tied * ((k - np.count_nonzero(above)) / np.count_nonzero(tied))


def breakpoints(scores, event):
    positive = np.sort(scores[event])[::-1]
    negative = np.sort(scores[~event])[::-1]
    r = len(event) // 5 - 1 - np.arange(len(positive))
    negative = np.r_[negative, 0.]
    return np.where(r < 0, np.inf, np.where(r >= len(negative) - 1, -np.inf,
                                          negative[np.clip(r, 0, len(negative) - 1)] - positive))


def population(design, settings, setting_id, fits, stage, reps):
    panels0, _ = make_panel(design, settings, fits, stream(stage, design, setting_id, 0))
    totals = {h: np.zeros(2) for h in panels0}
    edges = {h: [] for h in panels0}
    for i in range(reps):
        panels, _ = make_panel(design, settings, fits, stream(stage, design, setting_id, i))
        for horizon, strata in panels.items():
            for s in strata:
                k = len(s.event) // 5
                totals[horizon] += (allocation(s.b1, np.sort(s.b1), k) @ s.event, s.event.sum())
                if settings.tie_null:
                    center = s.regulatory.mean(axis=1)
                    # Integrate the exchangeable order within bins by fractional credit.
                    edges[horizon].append((center, s.event))
                else:
                    edges[horizon].extend(breakpoints(s.regulatory[:, i], s.event) for i in range(2))
    if not settings.tie_null:
        edges = {h: np.sort(np.concatenate(values)) for h, values in edges.items()}
    return {h: (totals[h][0] / totals[h][1], edges[h], totals[h][1]) for h in totals}


def tie_hits(schedule_scores, shift):
    hits = 0.
    for scores, event in schedule_scores:
        bins = np.floor((scores + event * shift) / .25)
        k = len(event) // 5
        hits += allocation(bins, np.sort(bins), k) @ event
    return hits


def tilt(edge, target):
    k = round(target * len(edge))
    if not 0 < k < len(edge) or not np.isfinite(edge[[k - 1, k]]).all():
        raise ValueError(f"Unattainable synthetic recall target {target}")
    return float((edge[k - 1] + edge[k]) / 2)


def calibrate(design, settings, setting_id, fits, effects, counts):
    fit_pop = population(design, settings, setting_id, fits, "calibration", counts[0])
    check = population(design, settings, setting_id, fits, "effect_check", counts[1])
    out = []
    for h1, h2 in effects:
        levels, shifts = {}, {}
        for horizon, (b1, edge, total) in fit_pop.items():
            desired = (b1 + h1 - h2, b1 + h1) if horizon != 12 else (b1 + .10,) * 2
            new_b1, new_edge, new_total = check[horizon]
            if settings.tie_null:
                lo, hi = -5., 5.
                for _ in range(15):
                    mid = (lo + hi) / 2
                    if tie_hits(edge, mid) < desired[1] * total:
                        lo = mid
                    else:
                        hi = mid
                shift = [(lo + hi) / 2] * 2
                level = [tie_hits(new_edge, shift[0]) / new_total] * 2
            else:
                shift = [tilt(edge, target) for target in desired]
                level = [np.searchsorted(new_edge, x) / len(new_edge) for x in shift]
            shifts[horizon] = shift
            levels[horizon] = [new_b1, *level]
        b1, m1, m3 = levels[design.horizon]
        delta = [m3 - b1, m3 - m1]
        intended = [h1, h2]
        if design.name == "A":
            delta.append(levels[12][2] - levels[12][0])
            intended.append(.10)
        out.append({"shifts": shifts, "recall_B1_M1_M3": levels, "target": intended,
                    "verified_delta": delta, "pass": bool(np.max(np.abs(np.subtract(delta, intended))) <= .005)})
    return out


def queue_point(score, event, correction):
    n = len(event)
    k = n // 5
    ordered = np.sort(score)
    weights = allocation(score, ordered, k)
    if not correction:
        return weights, event * weights
    width = int(np.ceil(2 * sqrt(.16 * n)))
    left, right = max(0, k - width), min(n, k + width)
    slope = (allocation(score, ordered, right) - allocation(score, ordered, left)) @ event / (right - left)
    return weights, event * weights + slope * (.2 - weights)


@lru_cache(maxsize=12)
def bootstrap_counts(clusters, draws, seed):
    rng = np.random.default_rng(seed)
    # int64 matches tracka_statistics.panel. Bincount unique indices per draw.
    choices = rng.integers(clusters, size=(draws, clusters))
    choices += (np.arange(draws) * clusters)[:, None]
    return np.bincount(choices.ravel(), minlength=draws * clusters).reshape(draws, clusters).astype(np.int16)


def exact_capture(score, stratum, counts, capacity):
    """Weighted prefix at each event's score block, with a certified short path."""
    rank = np.argsort(-score, kind="stable")
    sorted_score = -score[rank]
    event_pos = np.flatnonzero(stratum.event[rank])
    starts = np.searchsorted(sorted_score, sorted_score[event_pos], side="left")
    ends = np.searchsorted(sorted_score, sorted_score[event_pos], side="right")
    n = len(rank)
    anchor = min(n, n // 5 + int(np.ceil(6 * sqrt(.16 * n))) + 5)
    if anchor < n:
        anchor = np.searchsorted(sorted_score, sorted_score[anchor], side="right")
    drug = stratum.drugs[rank]

    def prefix(draws, cap, width):
        sums = np.cumsum(draws[:, drug[:width]], axis=1, dtype=np.int32)
        used = ends <= width
        a, b = starts[used], ends[used]
        before = np.where(a > 0, sums[:, a - 1], 0)
        size = sums[:, b - 1] - before
        fraction = np.clip(cap[:, None] - before, 0, size) / np.maximum(1, size)
        hits = (fraction * draws[:, drug[event_pos[used]]]).sum(axis=1)
        return hits, sums[:, -1] >= cap

    hits, certified = prefix(counts, capacity, anchor)
    if not certified.all():
        hits[~certified] = prefix(counts[~certified], capacity[~certified], n)[0]
    return hits


def grouped_capture(drugs, group_ends, event, counts, capacity):
    """Scan only as far as the resampled queue boundary in each exact draw."""
    hits = np.zeros(len(counts))
    for draw in range(len(counts)):
        places = capacity[draw]
        begin = 0
        for end in group_ends:
            if places == 0:
                break
            copies = 0
            captured = 0
            for j in range(begin, end):
                weight = counts[draw, drugs[j]]
                copies += weight
                captured += weight * event[j]
            if copies > places:
                hits[draw] += captured * (places / copies)
                break
            hits[draw] += captured
            places -= copies
            begin = end
    return hits


compiled_capture = numba.njit(cache=True)(grouped_capture) if numba is not None else None


def bootstrap_capture(score, stratum, counts, capacity):
    if compiled_capture is None:
        return exact_capture(score, stratum, counts, capacity)
    rank = np.argsort(-score, kind="stable")
    ordered = score[rank]
    ends = np.r_[np.flatnonzero(ordered[1:] != ordered[:-1]) + 1, len(rank)]
    return compiled_capture(stratum.drugs[rank], ends, stratum.event[rank], counts, capacity)


def panel_metrics(strata, clusters, shifts, pairs, *, draws=0, seed=20270401, validate=False,
                  cache=None):
    correction = not draws or validate
    counts = bootstrap_counts(clusters, draws, seed) if draws else None
    events = np.zeros(clusters)
    terms = np.zeros((clusters, 3))
    hits = np.zeros(3)
    discordance = np.zeros(len(pairs))
    overlap = np.zeros(len(pairs))
    sample = np.zeros((draws, 3))
    used = tuple(sorted({a for pair in pairs for a in pair}))
    for index, s in enumerate(strata):
        scores = s.scores(shifts)
        events[s.drugs] += s.event
        k = len(s.event) // 5
        queue = np.zeros_like(scores)
        boundary = None
        if draws and s.event.any():
            if cache is not None and (index, "capacity") in cache:
                boundary = cache[index, "capacity"]
            else:
                boundary = (np.full(draws, k, dtype=np.int32) if len(s.drugs) == clusters
                            else counts[:, s.drugs].sum(axis=1, dtype=np.int32) // 5)
                if cache is not None:
                    cache[index, "capacity"] = boundary
        for a in used:
            key = (index, a, 0. if a == 0 else shifts[0 if s.tie_noise is not None else a - 1])
            cached = cache.get(key) if cache is not None else None
            if cached is None:
                q, term = queue_point(scores[:, a], s.event, correction)
                captured = bootstrap_capture(scores[:, a], s, counts, boundary) if boundary is not None else 0.
                if cache is not None:
                    cache[key] = (q, term, captured)
            else:
                q, term, captured = cached
            queue[:, a] = q
            hits[a] += q @ s.event
            terms[s.drugs, a] += term
            sample[:, a] += captured
        for c, (a, b) in enumerate(pairs):
            discordance[c] += np.abs(queue[:, a] - queue[:, b]) @ s.event
            overlap[c] += np.minimum(queue[:, a], queue[:, b]).sum() / max(1, k)
    total = events.sum()
    point = np.full(len(pairs), np.nan)
    sd = point.copy()
    approx = point.copy()
    full = point.copy()
    reduced = point.copy()
    invalid = 0
    if total:
        point = np.array([(hits[a] - hits[b]) / total for a, b in pairs])
        if correction:
            influence = np.column_stack([terms[:, a] - terms[:, b] for a, b in pairs])
            influence = (influence - events[:, None] * point) / total
            sd = np.sqrt(((influence - influence.mean(axis=0)) ** 2).sum(axis=0))
            # Probability a registered draw excludes every event drug. At very
            # small event counts use the seeded exact evaluability check.
            n_event = np.count_nonzero(events)
            validity = n_event >= 30 or not (bootstrap_counts(clusters, 2000, seed)[:, events > 0].sum(axis=1) == 0).any()
            approx = point - Z * sd if validity else approx
        if draws:
            denominator = counts @ events
            invalid = np.count_nonzero(denominator == 0)
            differences = np.column_stack([sample[:, a] - sample[:, b] for a, b in pairs])
            differences[np.abs(differences) <= 1e-12] = 0.
            valid = np.divide(differences, denominator[:, None], out=np.full_like(differences, np.nan),
                              where=denominator[:, None] > 0)
            if not invalid:
                full = np.quantile(valid, ALPHA, axis=0, method="linear")
            if validate and np.isfinite(valid[:400]).all():
                reduced = np.quantile(valid[:400], ALPHA, axis=0, method="linear")
    elif draws:
        invalid = draws
    return {"point": point, "approx": approx, "full": full, "reduced": reduced, "sd": sd,
            "discordance": discordance, "queue_overlap": overlap / len(strata), "invalid_draws": invalid}


def exposure_summary(strata, design, clusters):
    events = np.zeros(clusters, dtype=int)
    country_events = []
    retention = []
    for start in range(0, len(strata), len(design.months)):
        rows = strata[start:start + len(design.months)]
        ids = np.concatenate([s.drugs[s.event] for s in rows])
        country_events.append(len(np.unique(ids)))
        events += np.bincount(ids, minlength=clusters)
        for a, b in zip(rows[:-1], rows[1:], strict=True):
            retention.append(np.intersect1d(a.drugs, b.drugs, assume_unique=True).size / len(a.drugs))
    n = np.count_nonzero(events)
    return (events.sum(), n, sum(country_events), country_events,
            [s.event.sum() for s in strata], [len(s.event) for s in strata],
            np.mean(retention) if retention else None)


def mc_error(cell):
    p, n = cell["rate"], cell["denominator"]
    return {**cell, "mcse": sqrt(p * (1 - p) / n) if n else None}


def outcome_rates(bounds):
    out = decision_rates(bounds)
    for step in tuple(out):
        out[step] = (mc_error(out[step]) if step == "full_sequence"
                     else {key: mc_error(value) for key, value in out[step].items()})
    return out


def compare(reference, alternative):
    passed, target = alternative > 0., reference > 0.
    difference = passed.mean(axis=0) - target.mean(axis=0)
    disagrees = (passed != target).mean(axis=0)
    same_evaluable = np.isfinite(alternative) == np.isfinite(reference)
    return {"rejection_difference": difference, "decision_disagreement": disagrees,
            "evaluable_match": same_evaluable.all(axis=0),
            "exact": [mc_error(interval(x, len(target))) for x in target.sum(axis=0)],
            "alternative": [mc_error(interval(x, len(passed))) for x in passed.sum(axis=0)],
            "pass": bool(np.all(np.abs(difference) <= .035) and np.all(disagrees <= .10) and same_evaluable.all())}


def simulate(design, settings, setting_id, fits, calibration, stage, reps, method):
    draws = {"approx": 0, "reduced": 400, "full": 2000, "validate": 2000}[method]
    shape = (len(calibration), reps, 3 if design.name == "A" else 2)
    fields = ("full", "reduced", "approx") if method == "validate" else ("approx" if not draws else "full",)
    bounds = {name: np.empty(shape) for name in fields}
    point = np.empty(shape)
    diagnostic_shape = (*shape[:2], 2)
    diagnostic = {name: np.empty(diagnostic_shape) for name in ("discordance", "queue_overlap", "sd")}
    invalid = np.zeros(shape[:2], dtype=int)
    counts = []
    seed = 20261127 if design.name == "A" else 20270401
    horizon = design.horizon
    for i in range(reps):
        panels, n = make_panel(design, settings, fits, stream(stage, design, setting_id, i))
        counts.append(exposure_summary(panels[horizon], design, n))
        queue_cache = {}
        h3 = None
        if design.name == "A":
            h3 = panel_metrics(panels[12], n, calibration[0]["shifts"][12], (PAIRS[0],), draws=draws, seed=seed)
        for j, effect in enumerate(calibration):
            result = panel_metrics(panels[horizon], n, effect["shifts"][horizon], PAIRS, draws=draws, seed=seed,
                                   validate=method == "validate", cache=queue_cache)
            for field in bounds:
                bounds[field][j, i] = result[field] if h3 is None else np.r_[result[field], h3[field]]
            point[j, i] = result["point"] if h3 is None else np.r_[result["point"], h3["point"]]
            for name in diagnostic:
                diagnostic[name][j, i] = result[name]
            invalid[j, i] = result["invalid_draws"] + (0 if h3 is None else h3["invalid_draws"])
    fields = {name: np.mean(np.asarray([c[j] for c in counts]), axis=0)
              for j, name in enumerate(("event_rows", "event_drugs", "jurisdiction_approvals",
                                         "country_approvals", "event_rows_by_country_origin", "roster_by_country_origin",
                                         "successive_roster_retention")) if j != 6 or len(design.months) > 1}
    fields["rows_per_jurisdiction_approval"] = fields["event_rows"] / fields["jurisdiction_approvals"]
    return bounds, point, diagnostic, fields, invalid


def burden(design):
    origins = [design.shifted(m) for m in design.months]
    counts = {year: design.countries * sum(d.year == year for d in origins)
              for year in range(origins[0].year, origins[-1].year + 1)}
    freezes = sum(counts.values())
    years = sum(n > 0 for n in counts.values())
    final = design.shifted(design.months[-1] + design.horizon)
    return {"origins": [d.isoformat() for d in origins],
            "final_maturity": final.isoformat(),
            "total_freezes_and_prediction_runs_each": freezes,
            "active_forecast_years": years, "freezes_and_cpu_runs_per_year_each": counts,
            "owner_actions_per_year": {yr: count + (count > 0) for yr, count in counts.items()},
            "annual_mean_freezes_and_cpu_runs_each": freezes / len(counts),
            "annual_peak_freezes_and_cpu_runs_each": max(counts.values()),
            "annual_mean_owner_actions": (freezes + years) / len(counts),
            "annual_peak_owner_actions": max(counts.values()) + 1,
            "maturity_cpu_runs_and_owner_reviews_by_year_each": ({2027: 1, 2028: 1} if design.name == "A"
                                                                    else {final.year: 1}),
            "completion": {str(p): {str(loss): p**freezes * (1 - loss)**years for loss in (0., .01, .03)}
                           for p in (.95, .99)}, "already_frozen": design.name == "A"}


def run_cell(design, settings, setting_id, fits, effects, reps, method, calibration, stage="screen"):
    bounds, observed, diagnostics, exposure, invalid = simulate(
        design, settings, setting_id, fits, calibration, stage, reps, method)
    cells = []
    operational = burden(design)
    for i, (h1, h2) in enumerate(effects):
        bound = next(iter(bounds.values()))[i]
        rates = outcome_rates(bound)
        if design.name != "A":
            rates["H2"] = {k: rates["H2"][k] for k in ("marginal", "unevaluable")}
            rates["H1"] = {k: rates["H1"][k] for k in ("marginal", "unevaluable")}
            del rates["full_sequence"]
        h2_power = rates["H2"]["sequence" if design.name == "A" else "marginal"]["rate"]
        clears_mid = bound[:, 1] > .05
        if design.name == "A":
            clears_mid &= bound[:, 0] > 0
        cells.append({"h1_effect": h1, "h2_effect": h2, "rates": rates,
                      "mean_point_delta": observed[i].mean(axis=0),
                      "event_approval_equivalent_variance": observed[i].var(axis=0, ddof=1) * exposure["event_drugs"],
                      "discordance_per_event_row": diagnostics["discordance"][i].mean(axis=0) / exposure["event_rows"],
                      "mean_queue_overlap": diagnostics["queue_overlap"][i].mean(axis=0),
                      "h2_lower_bound_above_5pp": mc_error(interval(clears_mid.sum(), reps)),
                      "undefined_bootstrap_draws_across_panels": int(invalid[i].sum()) if method != "approx" else None,
                      "approximate_operational_h2_power": {p: h2_power * value["0.0"]
                                                          for p, value in operational["completion"].items()},
                      "calibration": calibration[i]})
    return {"settings": asdict(settings), "stage": stage, "replicates": reps, "method": method,
            "exposure": exposure, "effects": cells}


def job(design, label, settings, setting_id, fits, effects, reps, calibration_counts, validation_reps, fallback,
        stage="screen"):
    start = perf_counter()
    print(f"Start {design.name}/{label}", flush=True)
    calibration = calibrate(design, settings, setting_id, fits, effects, calibration_counts)
    validation = None
    method = fallback
    if validation_reps:
        checks = [effects.index((.10, h2)) for h2 in (0., .05)]
        selected = [calibration[i] for i in checks]
        bounds, _, _, _, _ = simulate(design, settings, setting_id, fits, selected,
                                     "validation", validation_reps, "validate")
        validation = [{name: compare(bounds["full"][i], values[i])
                       for name, values in bounds.items() if name != "full"} for i in range(2)]
        method = next((name for name in ("approx", "reduced") if all(v[name]["pass"] for v in validation)), "full")
    result = run_cell(design, settings, setting_id, fits, effects, reps, method, calibration, stage)
    result["matched_validation"] = {"panels_each": validation_reps, "h2_effects": [0., .05],
                                    "comparisons": validation} if validation else None
    result["elapsed_seconds"] = perf_counter() - start
    print(f"Done {design.name}/{label} with {method} in {result['elapsed_seconds']:.1f}s", flush=True)
    return design.name, label, result


def json_ready(value):
    if isinstance(value, np.ndarray):
        return json_ready(value.tolist())
    if isinstance(value, np.generic):
        return json_ready(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_ready(x) for x in value]
    return value


def reference_rates(t4c):
    return {n: {h: t4c["scenarios"][f"events_{n}"]["power"]["useful"]["rates"]["0.025"][h]["sequence"]
                for h in ("H1", "H2", "H3")} for n in (50, 75, 150)}


def filing_jobs():
    yield "alternative_no_shock", CENTRAL, .05
    yield "alternative_shock", replace(CENTRAL, shock=.30), .05
    for us, persistence, shock, tie in product((32, 51, 70), (.5, .8, .95), (0., .30), (False, True)):
        yield (f"null_us{us}_rho{persistence}_shock{shock}_tie{tie}",
               replace(CENTRAL, us=us, persistence=persistence, shock=shock, tie_null=tie), 0.)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--pilot-exact-seconds", type=float)
    parser.add_argument("--verification-wall-hours", type=float, default=1.,
                        help="Maximum pilot-projected local wall hours for the independent verification grid")
    parser.add_argument("--output", type=Path, default=LOE / "data" / "POWER_SIM.json")
    args = parser.parse_args()
    start = perf_counter()
    t4c, digest = source()
    fits = unpack_fits(t4c)
    reference = reference_rates(t4c)
    print("Pinned T4c rejection tabulation:", reference, flush=True)
    if args.pilot:
        design = DESIGNS[1]
        calibration = calibrate(design, CENTRAL, 999, fits, ((.10, .05),), (12, 20))
        timers = {}
        for method in ("approx", "reduced", "full"):
            now = perf_counter()
            simulate(design, CENTRAL, 999, fits, calibration, "validation", 6, method)
            timers[method] = (perf_counter() - now) / 6
        print(json.dumps({"seconds_per_B_panel": timers, "estimated_exact_verification_cpu_hours":
                          timers["full"] * 10000 * 38 / 3600}), flush=True)
        return
    if args.pilot_exact_seconds is None:
        parser.error("Run --pilot and supply its measured full seconds per B panel")
    result = {"scope": "SYNTHETIC_FEASIBILITY_ONLY", "seeds": SEEDS, "development_aggregate_sha256_lf": digest,
              "protocol_sha256_lf": hashlib.sha256((LOE.parent / "docs/loe-bench/receipts/POWER-SIM-PROTOCOL.md")
                                                   .read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
              "t4c_historical_reference": reference, "t4c_independent_history_replay": "NOT_RUN",
              "burden": {d.name: burden(d) for d in DESIGNS}, "designs": {d.name: {} for d in DESIGNS}}

    def save():
        temp = args.output.with_suffix(".json.partial")
        temp.write_text(json.dumps(json_ready(result), indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temp.replace(args.output)

    def receive(future):
        name, label, data = future.result()
        result["designs"][name][label] = data
        save()

    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        jobs = []
        for design in DESIGNS:
            effects = EFFECTS if design.name in "ABCDEF" else ((.10, 0.), (.10, .05))
            check = 0 if design.name == "A" else 80 if design.name == "monthly" else 160
            jobs.append(pool.submit(job, design, "central", CENTRAL, 0, fits, effects, 2000, (400, 800),
                                    check, "full"))
        for future in as_completed(jobs):
            receive(future)
        jobs = []
        for design in (DESIGNS[i] for i in (0, 1, 2, 3, 4, 5)):
            method = result["designs"][design.name]["central"]["method"]
            for setting_id, (name, settings) in enumerate(SENSITIVITIES.items(), 1):
                if name.endswith("canada_incidence") and design.name != "F":
                    continue
                if design.name not in ("A", "B", "C", "F") and name not in ("low_incidence", "high_incidence", "calendar_shocks"):
                    continue
                if design.name == "A" and name not in ("low_incidence", "high_incidence", "lower_cross_arm_correlation",
                                                     "within_tie_null"):
                    continue
                effects = ((.10, 0.),) if settings.tie_null else ((.10, 0.), (.10, .05))
                jobs.append(pool.submit(job, design, name, settings, setting_id, fits, effects, 2000, (400, 800), 0, method))
            if design.name in ("B", "C"):
                jobs.append(pool.submit(job, design, "larger_graph_gain", CENTRAL, 20, fits, ((.10, .10),),
                                        2000, (400, 800), 0, method))
        for future in as_completed(jobs):
            receive(future)
        central = result["designs"]["B"]["central"]
        null, _, _, alternative, *_ = central["effects"]
        cost_hours = args.pilot_exact_seconds * 10000 * 38 / 3600
        power = alternative["rates"]["H2"]["marginal"]["rate"]
        error = null["rates"]["H2"]["marginal"]["rate"]
        stop = []
        if power < .80 or error > .030:
            stop.append("Central B screen missed the prespecified power or null threshold")
        if not null["calibration"]["pass"] or not alternative["calibration"]["pass"]:
            stop.append("Central B effect calibration did not qualify")
        if cost_hours / args.workers > args.verification_wall_hours:
            stop.append("Pilot-projected verification runtime exceeds the local run window")
        verification = {"status": "NOT_RUN" if stop else "RUNNING", "estimated_exact_cpu_hours": cost_hours,
                        "local_verification_wall_hours": args.verification_wall_hours,
                        "central_screen_power_at_5pp": power, "central_screen_h2_null": error, "reasons": stop}
        result["filing_verification"] = verification
        save()
        if not stop:
            jobs = [pool.submit(job, DESIGNS[1], label, setting, i + 100, fits, ((.10, g),), 10000,
                                (400, 800), 0, "full", "filing")
                    for i, (label, setting, g) in enumerate(filing_jobs())]
            for future in as_completed(jobs):
                receive(future)
            checks = [cell["effects"][0] for cell in result["designs"]["B"].values() if cell["stage"] == "filing"]
            passed = all(c["calibration"]["pass"] and c["rates"]["H2"]["unevaluable"]["wilson_95"][1] <= .01
                         and (c["rates"]["H2"]["marginal"]["wilson_95"][0] >= .80 if c["h2_effect"]
                              else c["rates"]["H2"]["marginal"]["wilson_95"][1] <= .030) for c in checks)
            verification["status"] = "PASS" if passed else "FAIL"
    result["runtime"] = {"python": platform.python_version(), "numpy": np.__version__,
                         "numba": None if numba is None else numba.__version__,
                         "workers": args.workers, "elapsed_seconds": perf_counter() - start}
    save()


if __name__ == "__main__":
    main()
