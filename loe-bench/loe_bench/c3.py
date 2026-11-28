"""Applicant-at-approval labels and frozen-queue scoring for C3."""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from math import isclose
import re
import unicodedata

import numpy as np

from .common import add_months
from .review_metrics import ReviewQueue
from .seal import TEST_FIRST, require_cutoffs


HORIZON = 36
THRESHOLD = 3
DEVELOPMENT_END = date(2016, 1, 1)
FIRST_TEST = TEST_FIRST
LAST_TEST = date(2023, 1, 1)
ARMS = ("M3", "B1")
DRAWS = 2_000
SEED = 20261127
ANDA = re.compile(r"ANDA[0-9]{6}")


def window_ends(cutoffs, observed_through):
    """Gate the full requested windows before any caller reads outcome records."""
    cutoffs = tuple(cutoffs)
    ends = {day: add_months(day, HORIZON) for day in cutoffs}
    if not ends or len(ends) != len(cutoffs):
        raise ValueError("C3 requires distinct cutoffs")
    for day, end in ends.items():
        if end > observed_through:
            raise ValueError("C3 requires mature 36-month follow-up")
        if day < TEST_FIRST:
            if end > DEVELOPMENT_END:
                raise ValueError("C3 development windows must end by 2016-01-01")
        elif day > LAST_TEST or (day.month, day.day) != (1, 1):
            raise ValueError("C3 test admits only annual January cutoffs in 2017–2023")
    if any(day < TEST_FIRST for day in cutoffs) and any(day >= TEST_FIRST for day in cutoffs):
        raise ValueError("C3 cannot pool development and test windows")
    require_cutoffs(cutoffs)
    return ends


def name_key(name):
    """Normalize case, canonical Unicode and whitespace only."""
    key = " ".join(unicodedata.normalize("NFC", name).casefold().split())
    if not key:
        raise ValueError("Applicant name cannot be empty")
    return key


@dataclass(frozen=True)
class Evidence:
    source: str
    version: str
    sha256: str
    locator: str

    def __post_init__(self):
        if (not all((self.source, self.version, self.locator))
                or not re.fullmatch(r"[0-9a-f]{64}", self.sha256)):
            raise ValueError("Evidence requires source, version, SHA-256 and locator")


@dataclass(frozen=True)
class ApplicantHistory:
    application: str
    name: str
    start: date
    end: date
    evidence: Evidence


@dataclass(frozen=True)
class NameAlias:
    name: str
    canonical_name: str
    start: date
    end: date
    evidence: Evidence


@dataclass(frozen=True)
class Approval:
    group: str
    application: str
    approved: date
    evidence: Evidence
    action: str = "ORIG/AP"
    authorized_generic: bool = False


@dataclass(frozen=True)
class Label:
    confirmed_applicants: tuple[str, ...]
    unresolved_applications: tuple[str, ...]
    applications: tuple[str, ...]

    @property
    def lower(self):
        # At least one entity owns a final application, even when all names are missing.
        return max(int(bool(self.applications)), len(self.confirmed_applicants))

    @property
    def upper(self):
        return len(self.confirmed_applicants) + len(self.unresolved_applications)

    @property
    def event(self):
        if self.lower >= THRESHOLD:
            return True
        if self.upper < THRESHOLD:
            return False
        return None


class ApplicantIndex:
    """Use only history covering the exact approval day and evidence-backed aliases."""

    def __init__(self, history=(), aliases=()):
        self.history = defaultdict(list)
        self.aliases = defaultdict(list)
        for record in history:
            if record.start > record.end or not ANDA.fullmatch(record.application):
                raise ValueError("Invalid ANDA applicant history")
            name_key(record.name)
            self.history[record.application].append(record)
        for alias in aliases:
            if alias.start > alias.end:
                raise ValueError("Invalid applicant alias dates")
            name_key(alias.canonical_name)
            self.aliases[name_key(alias.name)].append(alias)
        if any(name_key(alias.canonical_name) in self.aliases
               for records in self.aliases.values() for alias in records):
            raise ValueError("Use a single-hop applicant alias table")

    def at_approval(self, approval):
        names = set()
        for record in self.history.get(approval.application, ()):
            if record.start <= approval.approved <= record.end:
                raw = name_key(record.name)
                targets = {name_key(alias.canonical_name) for alias in self.aliases.get(raw, ())
                           if alias.start <= approval.approved <= alias.end}
                names.update(targets or (raw,))
        return next(iter(names)) if len(names) == 1 else None


def build_labels(roster, approvals, applicants, *, observed_through):
    """Label the complete, already at-risk C1 roster without redefining eligibility."""
    roster = tuple(roster)
    ends = window_ends(sorted({day for _, day in roster}), observed_through)
    if len(set(roster)) != len(roster):
        raise ValueError("C3 requires one eligible row per group and cutoff")

    first = {}
    last_end = max(ends.values())
    for item in approvals:
        if not ANDA.fullmatch(item.application) or item.action != "ORIG/AP" or item.authorized_generic:
            continue
        if item.approved > last_end:
            raise ValueError("C3 received an approval outside its admitted outcome period")
        key = (item.group, item.application)
        if key not in first or item.approved < first[key].approved:
            first[key] = item
    by_group = defaultdict(list)
    for item in first.values():
        by_group[item.group].append((item, applicants.at_approval(item)))

    result = {}
    for group, day in roster:
        known, unknown, in_window = set(), [], []
        for item, name in by_group[group]:
            if item.approved <= day:
                raise ValueError("C3 roster includes a group with a pre-cutoff final ANDA")
            if item.approved > ends[day]:
                continue
            in_window.append(item.application)
            if name is None:
                unknown.append(item.application)
            else:
                known.add(name)
        result[group, day] = Label(tuple(sorted(known)), tuple(sorted(unknown)), tuple(sorted(in_window)))
    return result


def _ratio(hits, events):
    return float(hits / events) if events else None


def _bounds(values, positive, unknown):
    """Outer bounds over common independent assignments to ambiguous rows."""
    base = float(values[positive].sum())
    n = int(positive.sum())
    ambiguous = np.sort(values[unknown])
    count = n + np.arange(1, len(ambiguous) + 1)
    low = (base + ambiguous.cumsum()) / count
    high = (base + ambiguous[::-1].cumsum()) / count
    if n:
        low = np.append(low, base / n)
        high = np.append(high, base / n)
    return {
        "all_unknown_negative": _ratio(base, n),
        "all_unknown_positive": _ratio(base + ambiguous.sum(), n + len(ambiguous)),
        "range_given_nonzero_events": [float(low.min()), float(high.max())] if low.size else None,
    }


def score(labels, scores, *, observed_through, history_irrecoverable):
    """Score frozen native probabilities by row ID with unchanged label-blind capacity."""
    roster = sorted(labels)
    windows = window_ends(sorted({day for _, day in roster}), observed_through)
    if set(scores) != set(ARMS):
        raise ValueError("C3 requires the two frozen 24-month arms")
    cutoffs = np.asarray([day for _, day in roster], dtype=object)
    positives = np.asarray([labels[row] is True for row in roster])
    unknowns = np.asarray([labels[row] is None for row in roster])
    if any(label is not True and label is not False and label is not None for label in labels.values()):
        raise ValueError("C3 labels must be true, false or unknown")
    keys, groups = np.unique([key for key, _ in roster], return_inverse=True)
    queues = {}
    for arm in ARMS:
        if scores[arm].keys() != labels.keys():
            raise ValueError("Frozen queue and C3 roster must match exactly")
        values = np.asarray([scores[arm][row] for row in roster], dtype=float)
        if not np.isfinite(values).all() or ((values < 0) | (values > 1)).any():
            raise ValueError("C3 requires finite frozen native probabilities")
        queues[arm] = ReviewQueue(values, cutoffs)

    capacity = {day.isoformat(): int((cutoffs == day).sum()) // 5 for day in windows}
    fractions = {}
    for arm, queue in queues.items():
        fractions[arm], slots = queue.allocation(np.ones(len(roster), dtype=int))
        if (slots != sum(capacity.values()) or any(
                not isclose(fractions[arm][cutoffs == day].sum(), capacity[day.isoformat()],
                            rel_tol=0, abs_tol=1e-9) for day in windows)):
            raise ValueError("Frozen queue violated cutoff capacity")

    events = int(positives.sum())
    difference = fractions["M3"] - fractions["B1"]
    result = {
        "status": ("DESCRIPTIVE_BOUNDS_ONLY" if history_irrecoverable else
                   "UNDEFINED_NO_KNOWN_EVENTS" if not events else "EVALUATED"),
        "rows": len(roster),
        "event_rows": events,
        "event_drugs": int(np.unique(groups[positives]).size),
        "unknown_rows": int(unknowns.sum()),
        "unknown_drugs": int(np.unique(groups[unknowns]).size),
        "slots_by_cutoff": capacity,
        "arms": {arm: {"recall": None if history_irrecoverable else _ratio(
            fractions[arm][positives].sum(), events),
            "bounds": _bounds(fractions[arm], positives, unknowns)} for arm in ARMS},
        "M3_minus_B1": {"delta": None if history_irrecoverable else _ratio(
            difference[positives].sum(), events), "bounds": _bounds(difference, positives, unknowns),
            "ci95": None, "draws_run": 0, "undefined_draws": None},
    }
    if history_irrecoverable or not events:
        return result

    rng = np.random.default_rng(SEED)
    samples = []
    undefined = 0
    for _ in range(DRAWS):
        copies = np.bincount(rng.integers(len(keys), size=len(keys)), minlength=len(keys))[groups]
        event_weights = copies * positives
        if not event_weights.sum():
            undefined += 1
            continue
        left, right = (queues[arm].allocation(copies)[0] for arm in ARMS)
        samples.append(_ratio((left - right) @ event_weights, event_weights.sum()))
    result["M3_minus_B1"].update(draws_run=DRAWS, undefined_draws=undefined, ci95=(
        None if undefined else np.quantile(samples, (0.025, 0.975), method="linear").tolist()))
    return result
