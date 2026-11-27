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
    nme: bool = False
    orphan: bool = False
    priority: bool = False
    oral: bool = False
    injectable: bool = False
    n_nda_apps: int = 0
    sponsors: set = field(default_factory=set)
    nda_dates: List[date] = field(default_factory=list)


def _orig_ap_date(sub_list) -> Optional[date]:
    best = None
    for s in sub_list or []:
        if s.get("submission_type") == "ORIG" and s.get("submission_status") == "AP":
            d = parse_yyyymmdd(s.get("submission_status_date"))
            if d and (best is None or d < best):
                best = d
    return best


def build_entities(raw_dir: str) -> Dict[str, Entity]:
    ents: Dict[str, Entity] = {}
    for rec in read_jsonl(os.path.join(raw_dir, "df_nda.jsonl")):
        key = ingredient_key(rec.get("products"))
        if not key:
            continue
        d = _orig_ap_date(rec.get("submissions"))
        e = ents.setdefault(key, Entity(key))
        e.n_nda_apps += 1
        if rec.get("sponsor_name"):
            e.sponsors.add(rec["sponsor_name"])
        if d:
            e.nda_dates.append(d)
            if e.nda_first is None or d < e.nda_first:
                e.nda_first = d
        for s in rec.get("submissions") or []:
            if s.get("submission_type") == "ORIG":
                if s.get("submission_class_code") == "TYPE 1":
                    e.nme = True
                if s.get("review_priority") == "PRIORITY":
                    e.priority = True
                for pt in s.get("submission_property_type") or []:
                    if pt.get("code") == "Orphan":
                        e.orphan = True
        for p in rec.get("products") or []:
            route = (p.get("route") or "").upper()
            if "ORAL" in route:
                e.oral = True
            if "INJECT" in route or "INTRAVENOUS" in route or "SUBCUTANEOUS" in route or "INTRAMUSCULAR" in route:
                e.injectable = True
    for rec in read_jsonl(os.path.join(raw_dir, "df_anda.jsonl")):
        key = ingredient_key(rec.get("products"))
        if not key or key not in ents:
            continue
        d = _orig_ap_date(rec.get("submissions"))
        if d and (ents[key].anda_first is None or d < ents[key].anda_first):
            ents[key].anda_first = d
    return ents


def features_at(e: Entity, t: date) -> Dict[str, float]:
    """Features knowable at cutoff t (no future info). NOTE: nme/orphan/priority/route flags
    are fixed at approval so they are knowable at t >= nda_first."""
    age = years_between(e.nda_first, t)
    n_prior = sum(1 for d in e.nda_dates if d <= t)
    return {
        "age_years": age,
        "age_sq": age * age / 10.0,
        "nme": float(e.nme),
        "orphan": float(e.orphan),
        "priority": float(e.priority),
        "oral": float(e.oral),
        "injectable": float(e.injectable),
        "n_nda_prior": float(n_prior),
    }


FEATURE_NAMES = ["age_years", "age_sq", "nme", "orphan", "priority", "oral", "injectable", "n_nda_prior"]


def build_samples(ents: Dict[str, Entity], cutoffs: List[date], horizon_months: int,
                  data_end: date, only_nme: bool = True) -> List[dict]:
    """One row per (entity, cutoff) where the NDA is approved and no ANDA approved yet at cutoff.
    y=1 iff first ANDA within (t, t+h]. Rows whose window extends past data_end with y=0 are
    right-censored and DROPPED (listed in `censored` counters by run_profile)."""
    rows = []
    for t in cutoffs:
        t_end = add_months(t, horizon_months)
        for e in ents.values():
            if e.nda_first is None or e.nda_first > t:
                continue
            if only_nme and not e.nme:
                continue
            if e.anda_first is not None and e.anda_first <= t:
                continue
            y = int(e.anda_first is not None and e.anda_first <= t_end)
            censored = (y == 0 and t_end > data_end)
            if censored:
                continue
            rows.append({"key": e.key, "t": t, "t_end": t_end, "y": y, "x": features_at(e, t)})
    return rows


def time_split(rows: List[dict], train_last_cutoff: date, test_first_cutoff: date) -> tuple:
    """Temporal split with EMBARGO: every training window must end before the first test cutoff,
    otherwise training labels would be decided by information from the test period."""
    train = [r for r in rows if r["t"] <= train_last_cutoff]
    test = [r for r in rows if r["t"] >= test_first_cutoff]
    bad = [r for r in train if r["t_end"] > test_first_cutoff]
    train = [r for r in train if r["t_end"] <= test_first_cutoff]
    return train, test, len(bad)


def snapshot_features(raw_dir: str, t0: date, ents: Dict[str, Entity]) -> Dict[str, dict]:
    """Track A: from the CURRENT Orange Book snapshot, per entity without any ANDA yet,
    return patent/exclusivity dates (max over non-discontinued NDA RLD records)."""
    out: Dict[str, dict] = {}
    for rec in read_jsonl(os.path.join(raw_dir, "ob_nda.jsonl")):
        prods = rec.get("products") or []
        if not prods or (prods[0].get("marketing_status") or "").upper() == "DISCONTINUED":
            continue
        key = ingredient_key(prods)
        if not key or key not in ents or ents[key].anda_first is not None:
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
