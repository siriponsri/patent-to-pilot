"""Build shared C-prime features and graph inputs from a single as-of edition."""
from bisect import bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from .common import add_months, years_between
from .dataset import FEATURE_NAMES
from .evidence_graph import build_assignment, verdict_label
from .ob_history import OBHistory

OB_FEATURES = (
    "nce_remaining_years", "other_exclusivity_remaining_years", "listed_patent_count",
    "years_to_last_patent_expiry", "years_since_earliest_patent_submission",
)
MODEL_FEATURES = (*FEATURE_NAMES, *OB_FEATURES, *(f"{name}_missing" for name in OB_FEATURES))


@dataclass(frozen=True)
class AsOfFeatures:
    x: dict
    snapshot: dict
    verdict: str
    edition_status: str


def edition_coverage(history: OBHistory, cutoff: date) -> dict:
    dates = history.edition_dates()
    index = bisect_right(dates, cutoff) - 1
    chosen = dates[index] if index >= 0 else None
    earliest = add_months(cutoff, -6)
    status = "MISSING" if chosen is None else "STALE" if chosen < earliest else "FRESH"
    return {
        "status": status,
        "latest_edition": chosen.isoformat() if chosen else None,
        "age_days": (cutoff - chosen).days if chosen else None,
        "freshness_floor": earliest.isoformat(),
    }


def _product_id(row):
    return row["appl_no"], row["product_no"]


class _EditionIndex:
    def __init__(self, edition):
        self.by_key = defaultdict(set)
        self.patents = defaultdict(list)
        self.exclusivities = defaultdict(list)
        for product in edition.products:
            approved = product["approval_date"]
            if product["appl_type"] in ("N", "") and (approved is None or approved <= edition.edition_date):
                self.by_key[product["ingredient_key"]].add(_product_id(product))
        for patent in edition.patents:
            submitted = patent["submission_date"]
            if submitted is None or submitted <= edition.edition_date:
                self.patents[_product_id(patent)].append(patent)
        for exclusivity in edition.exclusivity:
            self.exclusivities[_product_id(exclusivity)].append(exclusivity)

    def records(self, key):
        ids = self.by_key.get(key)
        if not ids:
            return None, None
        return ([p for product_id in ids for p in self.patents.get(product_id, ())],
                [e for product_id in ids for e in self.exclusivities.get(product_id, ())])


def _complete_dates(records):
    dates = [row["expiry"] for row in records]
    return dates if all(dates) else []


def _remaining(records, cutoff):
    dates = _complete_dates(records)
    if records and not dates:
        return None
    return max(0.0, years_between(cutoff, max(dates, default=cutoff)))


class AsOfBuilder:
    def __init__(self, history: OBHistory):
        self.history = history
        self._indexes = {}

    def build(self, key: str, cutoff: date, horizon: int, base_features: dict) -> AsOfFeatures:
        coverage = edition_coverage(self.history, cutoff)
        status = coverage["status"]
        values = dict.fromkeys(OB_FEATURES)
        snapshot = {}
        if status == "FRESH":
            edition_date = coverage["latest_edition"]
            if edition_date not in self._indexes:
                self._indexes[edition_date] = _EditionIndex(self.history.edition_asof(cutoff))
            patents, exclusivities = self._indexes[edition_date].records(key)
            if patents is None:
                status = "NOT_LISTED"
            else:
                nce = [row for row in exclusivities if row["code"] == "NCE"]
                other = [row for row in exclusivities if row["code"] != "NCE"]
                patent_ids = {row["patent_no"] for row in patents}
                patent_dates = _complete_dates(patents)
                submitted = [row["submission_date"] for row in patents if row["submission_date"]]
                values.update(
                    nce_remaining_years=_remaining(nce, cutoff),
                    other_exclusivity_remaining_years=_remaining(other, cutoff),
                    listed_patent_count=None if "" in patent_ids else len(patent_ids),
                    years_to_last_patent_expiry=years_between(cutoff, max(patent_dates)) if patent_dates else None,
                    years_since_earliest_patent_submission=years_between(min(submitted), cutoff) if submitted else None,
                )
                snapshot = {"patent_exp": patent_dates, "excl_exp": _complete_dates(exclusivities)}
        x = dict(base_features)
        for name, value in values.items():
            x[name] = 0.0 if value is None else float(value)
            x[f"{name}_missing"] = float(value is None)
        verdict = verdict_label(build_assignment(snapshot, cutoff, horizon))
        return AsOfFeatures(x, snapshot, verdict, status)
