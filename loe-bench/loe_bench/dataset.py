"""Build entity table + (cutoff, horizon) labelled samples from openFDA JSONL files.

Entity = normalised active-ingredient set (key).
Label  = first final ANDA approval (Drugs@FDA ORIG, status AP) within `horizon_months` after cutoff t.
Caveats (also in docs/04): ANDA approval != market launch; Drugs@FDA keeps only latest submission
status; Orange Book patents/exclusivity are a CURRENT snapshot (cannot be rebuilt for past cutoffs).
"""
import os
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from .common import (add_months, ingredient_key, parse_yyyymmdd, read_jsonl, years_between)


@dataclass
class Entity:
    key: str
    nda_first: Optional[date] = None
    anda_first: Optional[date] = None
    flag_dates: Dict[str, date] = field(default_factory=dict)
    n_nda_apps: int = 0
    sponsors: set = field(default_factory=set)
    nda_dates: List[date] = field(default_factory=list)

    @property
    def nme(self) -> bool:
        """Whole-snapshot descriptive flag. Use `flag_at` for dated cohorts."""
        return "nme" in self.flag_dates

    def flag_at(self, name: str, t: date) -> bool:
        first = self.flag_dates.get(name)
        return first is not None and first <= t

    def record_flag(self, name: str, first: date) -> None:
        self.flag_dates[name] = min(self.flag_dates.get(name, first), first)


def _final_originals(rec: dict):
    """Yield dated original approvals. Drugs@FDA uses TA for tentative approvals."""
    for sub in rec.get("submissions") or []:
        if sub.get("submission_type") == "ORIG" and sub.get("submission_status") == "AP":
            approved = parse_yyyymmdd(sub.get("submission_status_date"))
            if approved:
                yield approved, sub


def _original_products(rec: dict, approved: Optional[date]) -> list:
    """Use the application-level ingredient proxy for undated products.

    Explicit product dates can exclude later variants from the original key.
    Undated products can supply the key, but cannot establish dated route flags.
    """
    products = []
    for product in rec.get("products") or []:
        raw_date = product.get("approval_date")
        when = parse_yyyymmdd(raw_date)
        if raw_date is None or (when is not None and approved is not None and when <= approved):
            products.append(product)
    return products


def build_entities(raw_dir: str) -> Dict[str, Entity]:
    ents: Dict[str, Entity] = {}
    for rec in read_jsonl(os.path.join(raw_dir, "df_nda.jsonl")):
        originals = list(_final_originals(rec))
        d = min((when for when, _ in originals), default=None)
        products = _original_products(rec, d)
        key = ingredient_key(products)
        if not key:
            continue
        e = ents.setdefault(key, Entity(key))
        e.n_nda_apps += 1
        if rec.get("sponsor_name"):
            e.sponsors.add(rec["sponsor_name"])
        if d is None:
            continue
        e.nda_dates.append(d)
        e.nda_first = min(e.nda_first or d, d)
        for when, sub in originals:
            if sub.get("submission_class_code") == "TYPE 1":
                e.record_flag("nme", when)
            if sub.get("review_priority") == "PRIORITY":
                e.record_flag("priority", when)
            if any(pt.get("code") == "Orphan" for pt in sub.get("submission_property_type") or []):
                e.record_flag("orphan", when)
        original_keys = {ingredient_key([p]) for p in products}
        for product in rec.get("products") or []:
            when = parse_yyyymmdd(product.get("approval_date"))
            if when is None or ingredient_key([product]) not in original_keys:
                continue
            when = max(d, when)
            route = (product.get("route") or "").upper()
            if "ORAL" in route:
                e.record_flag("oral", when)
            if any(term in route for term in ("INJECT", "INTRAVENOUS", "SUBCUTANEOUS", "INTRAMUSCULAR")):
                e.record_flag("injectable", when)
    for rec in read_jsonl(os.path.join(raw_dir, "df_anda.jsonl")):
        d = min((when for when, _ in _final_originals(rec)), default=None)
        if d is None:
            continue
        key = ingredient_key(_original_products(rec, d))
        if key in ents:
            ents[key].anda_first = min(ents[key].anda_first or d, d)
    return ents


def features_at(e: Entity, t: date) -> Dict[str, float]:
    """Return dated approval and flag evidence available at cutoff t."""
    if e.nda_first is None or e.nda_first > t:
        raise ValueError("features require an NDA approval on or before the cutoff")
    age = years_between(e.nda_first, t)
    n_prior = sum(1 for d in e.nda_dates if d <= t)
    return {
        "age_years": age,
        "age_sq": age * age / 10.0,
        "nme": float(e.flag_at("nme", t)),
        "orphan": float(e.flag_at("orphan", t)),
        "priority": float(e.flag_at("priority", t)),
        "oral": float(e.flag_at("oral", t)),
        "injectable": float(e.flag_at("injectable", t)),
        "n_nda_prior": float(n_prior),
    }


FEATURE_NAMES = ["age_years", "age_sq", "nme", "orphan", "priority", "oral", "injectable", "n_nda_prior"]


def build_samples(ents: Dict[str, Entity], cutoffs: List[date], horizon_months: int,
                  data_end: date, only_nme: bool = True) -> List[dict]:
    """Sample approved NDA entities at risk at t, with complete follow-up for both classes.

    The first final original ANDA approval in (t, t+h] is the event.
    """
    if horizon_months <= 0:
        raise ValueError("horizon_months must be positive")
    rows = []
    for t in cutoffs:
        t_end = add_months(t, horizon_months)
        if t_end > data_end:
            continue
        for e in ents.values():
            if e.nda_first is None or e.nda_first > t:
                continue
            if only_nme and not e.flag_at("nme", t):
                continue
            if e.anda_first is not None and e.anda_first <= t:
                continue
            y = int(e.anda_first is not None and t < e.anda_first <= t_end)
            rows.append({"key": e.key, "t": t, "t_end": t_end, "y": y, "x": features_at(e, t)})
    return rows


def time_split(rows: List[dict], train_last_cutoff: date, test_first_cutoff: date, *,
               validation_first_cutoff: Optional[date] = None,
               validation_last_cutoff: Optional[date] = None) -> tuple:
    """Return (train, test, dropped) or (train, validation, test, dropped).

    Cutoff bounds are inclusive. The earlier partition's label windows must end
    strictly before the next partition's stated first cutoff. Count embargoed
    rows from both earlier partitions. Rows in gaps belong to neither partition.
    """
    if train_last_cutoff >= test_first_cutoff:
        raise ValueError("train cutoff must end before the test cutoff starts")
    has_validation = validation_first_cutoff is not None or validation_last_cutoff is not None
    if has_validation and (
        validation_first_cutoff is None or validation_last_cutoff is None
        or not train_last_cutoff < validation_first_cutoff <= validation_last_cutoff < test_first_cutoff
    ):
        raise ValueError("validation cutoffs must be ordered between train and test")
    train = [r for r in rows if r["t"] <= train_last_cutoff]
    test = [r for r in rows if r["t"] >= test_first_cutoff]
    train_limit = validation_first_cutoff if has_validation else test_first_cutoff
    eligible_train = [r for r in train if r["t_end"] < train_limit]
    dropped = len(train) - len(eligible_train)
    if not has_validation:
        return eligible_train, test, dropped
    validation = [r for r in rows if validation_first_cutoff <= r["t"] <= validation_last_cutoff]
    eligible_validation = [r for r in validation if r["t_end"] < test_first_cutoff]
    return eligible_train, eligible_validation, test, dropped + len(validation) - len(eligible_validation)


def snapshot_features(raw_dir: str, t0: date, ents: Dict[str, Entity]) -> Dict[str, dict]:
    """Use Orange Book products approved by t0, for entities still at risk then.

    The caller supplies an edition available by t0. Expiration dates can extend
    beyond t0 because the snapshot records them at publication.
    """
    out: Dict[str, dict] = {}
    for rec in read_jsonl(os.path.join(raw_dir, "ob_nda.jsonl")):
        approved = parse_yyyymmdd(rec.get("approval_date"))
        if approved is None and rec.get("approved_prior_to_1982") is True:
            approved = date(1981, 12, 31)
        if approved is None or approved > t0:
            continue
        prods = []
        for p in rec.get("products") or []:
            product_date = parse_yyyymmdd(p.get("approval_date")) if "approval_date" in p else approved
            if (product_date is not None and product_date <= t0
                and (p.get("marketing_status") or "").upper() != "DISCONTINUED"):
                prods.append(p)
        key = ingredient_key(prods)
        e = ents.get(key)
        if e is None or e.nda_first is None or e.nda_first > t0:
            continue
        if e.anda_first is not None and e.anda_first <= t0:
            continue
        o = out.setdefault(key, {"patent_exp": [], "excl_exp": [], "excl_codes": set(), "n_patents": 0})
        for p in rec.get("patents") or []:
            d = parse_yyyymmdd(p.get("expiration_date"))
            if d:
                o["patent_exp"].append(d)
                o["n_patents"] += 1
        for x in rec.get("exclusivity") or []:
            d = parse_yyyymmdd(x.get("exclusivity_expiration_date"))
            if d:
                o["excl_exp"].append(d)
                o["excl_codes"].add(x.get("exclusivity_code"))
    return out
