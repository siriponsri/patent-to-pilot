"""Build shared C-prime features and graph inputs from a single as-of edition."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

from .common import add_months, years_between
from .dataset import FEATURE_NAMES
from .evidence_graph import build_assignment, verdict_label
from .challenge import ChallengeEvidence
from .kleene import T3
from .moiety import registry_for
from .ob_history import OBHistory

OB_FEATURES = (
    "nce_remaining_years", "other_exclusivity_remaining_years", "listed_patent_count",
    "years_to_last_patent_expiry", "years_since_earliest_patent_submission",
)
MODEL_FEATURES = (*FEATURE_NAMES, *OB_FEATURES, *(f"{name}_missing" for name in OB_FEATURES))
CHALLENGE_FEATURES = ("challenge_present", "challenge_missing")


@dataclass(frozen=True)
class AsOfFeatures:
    x: dict
    snapshot: dict
    verdict: str
    edition_status: str
    challenge: ChallengeEvidence | None = None


def edition_coverage(history: OBHistory, cutoff: date) -> dict:
    return _edition_selection(history, cutoff)[1]


def _edition_selection(history, cutoff):
    source, proof = history.available_source_asof(cutoff)
    earliest = add_months(cutoff, -6)
    latest = source.edition_date if source else None
    status = "MISSING" if latest is None else "STALE" if latest < earliest else "FRESH"
    chosen = source if status == "FRESH" else None
    return chosen, {
        "status": status,
        "chosen_edition": latest.isoformat() if chosen else None,
        "age_days": (cutoff - latest).days if chosen else None,
        "availability_proof": proof if chosen else None,
        "source": chosen.identity if chosen else None,
        "freshness_floor": earliest.isoformat(),
        "latest_proven_edition": latest.isoformat() if latest else None,
        "latest_proven_age_days": (cutoff - latest).days if latest else None,
        "latest_proven_availability": proof,
    }


def _product_id(row):
    return row["appl_no"], row["product_no"]


class _EditionIndex:
    def __init__(self, edition, registry=None, linker=None):
        self.by_key = defaultdict(set)
        self.linked_products = defaultdict(list)
        self.patents = defaultdict(list)
        self.exclusivities = defaultdict(list)
        self.linkage_counts = Counter()
        self.unmatched_examples = {}
        if linker is not None:
            self._link_products(edition, linker)
        else:
            for product in edition.products:
                approved = product["approval_date"]
                if product["appl_type"] in ("N", "") and (approved is None or approved <= edition.edition_date):
                    ingredient = product["ingredient_key"]
                    key = (registry.composition(product.get("ingredient", ingredient.replace("|", ";"))
                                                .split(";")).key if registry is not None else ingredient)
                    self.by_key[key].add(_product_id(product))
        for patent in edition.patents:
            submitted = patent["submission_date"]
            if submitted is None or submitted <= edition.edition_date:
                self.patents[_product_id(patent)].append(patent)
        for exclusivity in edition.exclusivity:
            self.exclusivities[_product_id(exclusivity)].append(exclusivity)

    def _link_products(self, edition, linker):
        candidates = []
        keys_by_product = defaultdict(set)
        for position, row in enumerate(edition.products, 1):
            kind = linker.application_type(row)
            if kind != "N":
                self.linkage_counts["unknown_application_type" if kind is None else "non_nda"] += 1
                continue
            self.linkage_counts["total_nda"] += 1
            approved = row["approval_date"]
            if approved is not None and approved > edition.edition_date:
                key, method = None, "approval_after_edition"
            else:
                key, method = linker.match(row)
            product_id = _product_id(row)
            if key is not None:
                keys_by_product[product_id].add(key)
            candidates.append((position, row, product_id, key, method))
        for position, row, product_id, key, method in candidates:
            if len(keys_by_product.get(product_id, ())) > 1:
                key, method = None, "conflicting_edition_product"
            self.linkage_counts[method] += 1
            if key is not None:
                self.by_key[key].add(product_id)
                self.linked_products[key].append(row)
                self.linkage_counts["matched"] += 1
            else:
                self.unmatched_examples.setdefault(method, dict(
                    products_data_row=position, appl_no=product_id[0], product_no=product_id[1],
                    ingredient=row.get("ingredient"), trade_name=row.get("trade_name"),
                ))

    def records(self, key):
        ids = self.by_key.get(key)
        if not ids:
            return None, None
        return ([p for product_id in sorted(ids) for p in self.patents.get(product_id, ())],
                [e for product_id in sorted(ids) for e in self.exclusivities.get(product_id, ())])


def _complete_dates(records):
    dates = [row["expiry"] for row in records]
    return dates if all(dates) else []


def _remaining(records, cutoff):
    dates = _complete_dates(records)
    if records and not dates:
        return None
    return max(0.0, years_between(cutoff, max(dates, default=cutoff)))


class AsOfBuilder:
    def __init__(self, history: OBHistory, *, key_mode=None, gsrs_path=None, linker=None, challenge=None):
        self.history = history
        self.challenge = challenge
        self._indexes = {}
        if key_mode is None:
            key_mode = "moiety" if linker or history.data_dir is not None or gsrs_path else "legacy"
        if key_mode not in {"moiety", "legacy"}:
            raise ValueError(f"unsupported entity key mode: {key_mode}")
        if linker is not None and key_mode != "moiety":
            raise ValueError("historical moiety linkage requires moiety key mode")
        self.linker = linker
        self.registry = (registry_for(history.data_dir or ".", gsrs_path)
                         if key_mode == "moiety" and linker is None else None)

    def edition_linkage(self, edition):
        """Count NDA product links using the same index rules as feature lookup."""
        if self.linker is None:
            raise ValueError("linkage reporting requires the entity crosswalk")
        index = _EditionIndex(edition, linker=self.linker)
        counts = index.linkage_counts
        total = counts["total_nda"]
        return dict(counts, total_nda=total, matched=counts["matched"],
                    link_rate=counts["matched"] / total if total else None,
                    unmatched_examples=index.unmatched_examples)

    def build(self, key: str, cutoff: date, horizon: int, base_features: dict) -> AsOfFeatures:
        source, coverage = _edition_selection(self.history, cutoff)
        status = coverage["status"]
        values = dict.fromkeys(OB_FEATURES)
        snapshot = {}
        if self.linker is not None:
            key = self.linker.canonical(key)
        if source is not None:
            if source not in self._indexes:
                self._indexes[source] = _EditionIndex(self.history.load_source(source), self.registry, self.linker)
            patents, exclusivities = self._indexes[source].records(key)
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
        challenge = self.challenge.lookup(key, cutoff) if self.challenge is not None else None
        state = challenge.state if challenge is not None else None
        if challenge is not None:
            x.update(challenge_present=float(state == T3.TRUE), challenge_missing=float(state == T3.UNKNOWN))
        verdict = verdict_label(build_assignment(snapshot, cutoff, horizon, challenge_evidence=state))
        return AsOfFeatures(x, snapshot, verdict, status, challenge)
