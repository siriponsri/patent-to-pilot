"""Serialize the frozen M3 source evidence for the development-only L1e prompt."""
from datetime import date
from math import isfinite
import json

from .llm_arm import SYSTEM, TEMPLATE as L1_TEMPLATE


CROSSWALK = {
    "age_years": "Years since first NDA approval as of cutoff",
    "age_sq": "Squared age in years divided by 10",
    "nme": "Dated new molecular entity flag",
    "orphan": "Dated orphan designation flag",
    "priority": "Dated priority review flag",
    "oral": "Oral route observed by cutoff",
    "injectable": "Injectable route observed by cutoff",
    "n_nda_prior": "Count from the NDA approval dates available by cutoff",
    "nce_remaining_years": "Nonnegative years until the latest NCE exclusivity expiry",
    "other_exclusivity_remaining_years": "Nonnegative years until the latest other exclusivity expiry",
    "listed_patent_count": "Distinct listed patent numbers in the selected edition",
    "years_to_last_patent_expiry": "Signed years until the latest listed patent expiry",
    "years_since_earliest_patent_submission": "Years since the earliest available listed patent submission",
    "nce_remaining_years_missing": "Missingness of the NCE exclusivity value",
    "other_exclusivity_remaining_years_missing": "Missingness of the other exclusivity value",
    "listed_patent_count_missing": "Missingness of the patent count",
    "years_to_last_patent_expiry_missing": "Missingness of the latest patent expiry value",
    "years_since_earliest_patent_submission_missing": "Missingness of the earliest patent submission value",
    "challenge_present": "Dated, admitted challenge witness present as of cutoff",
    "challenge_missing": "Challenge status unknown as of cutoff, including an undated matched filing",
    "strength_count": "Observed distinct normalized form-route and strength presentations",
    "form_route_count": "Observed distinct dosage-form and route pairs",
    "strength_missing": "Incomplete or absent strength coverage",
    "form_route_missing": "Incomplete or absent form-route coverage",
}
GRAPH_SOURCE_FIELDS = {
    "latest_patent_expiry": "Maximum of graph v1 snapshot.patent_exp, or null for an empty clock",
    "latest_exclusivity_expiry": "Maximum of graph v1 snapshot.excl_exp, or null for an empty clock",
    "challenge_witnesses": "Distinct source and date pairs underlying the graph v1 challenge leaf",
}
CHALLENGE_SOURCES = ("FDA_PIV", "RAI_COURT", "RAI_OB_PATENT")
EXCLUDED = ("b1_age_hazard_logit", "verdict_OPEN", "verdict_BLOCKED", "verdict_CONTESTED")
EVIDENCE_FIELDS = CROSSWALK.keys() | GRAPH_SOURCE_FIELDS.keys()
IDENTITY_FIELDS = {"entity", "t0", "horizon_months"}
FIELDS = IDENTITY_FIELDS | {"as_of_evidence"}
EVIDENCE_TEXT = """Evidence available as of t0 (JSON):
{evidence}
An evidence flag of 1 means observed or missing as named. A 0 flag means false under the available records.
Treat values with a matching missing flag of 1 as unknown. The breadth counts still show the observed portion when coverage is incomplete.
An undated challenge cannot establish a dated filing. A dated challenge alone does not establish that entry is permitted.
Patent and exclusivity expiries are dates published by t0 and may be later than t0. A null expiry clock means unknown.
"""
TEMPLATE = L1_TEMPLATE.replace("{features}", EVIDENCE_TEXT).replace(
    "Use only knowledge you hold with confidence about records dated on or before t0.",
    "Use only the as-of evidence above.",
)


def from_m3(row):
    """Project source inputs used by M3 and the underlying graph leaf evidence."""
    asof = row["asof"]
    combined = asof.x | row["breadth"]
    values = {name: combined[name] for name in CROSSWALK}
    patent = max(asof.snapshot.get("patent_exp", ()), default=None)
    exclusivity = max(asof.snapshot.get("excl_exp", ()), default=None)
    witnesses = sorted({(w.source, w.date.isoformat()) for w in asof.challenge.witnesses})
    return dict(values, latest_patent_expiry=patent.isoformat() if patent else None,
                latest_exclusivity_expiry=exclusivity.isoformat() if exclusivity else None,
                challenge_witnesses=[dict(source=source, date=day) for source, day in witnesses])


def _date(value):
    return isinstance(value, str) and date.fromisoformat(value).isoformat() == value


def validate_evidence(evidence, cutoff):
    if not isinstance(evidence, dict) or evidence.keys() != EVIDENCE_FIELDS:
        raise ValueError("forecast evidence must match the frozen allowlist")
    if any(type(evidence[name]) not in (int, float) or not isfinite(evidence[name]) for name in CROSSWALK):
        raise ValueError("expected finite numeric features")
    for field in ("latest_patent_expiry", "latest_exclusivity_expiry"):
        if evidence[field] is not None and not _date(evidence[field]):
            raise ValueError("expected canonical expiry date or null")
    witnesses = evidence["challenge_witnesses"]
    if not isinstance(witnesses, list) or any(
        not isinstance(w, dict) or w.keys() != {"source", "date"}
        or w["source"] not in CHALLENGE_SOURCES or not _date(w["date"]) or w["date"] > cutoff
        for w in witnesses
    ):
        raise ValueError("challenge witnesses must have an admitted source and as-of date")
    if (evidence["challenge_present"] != int(bool(witnesses)) or evidence["challenge_missing"] not in (0, 1)
            or (witnesses and evidence["challenge_missing"])):
        raise ValueError("challenge witnesses and missingness disagree")


def build_prompt(row):
    if row.keys() != FIELDS:
        raise ValueError("forecast must match the frozen L1e allowlist")
    validate_evidence(row["as_of_evidence"], row["t0"])
    evidence = json.dumps(row["as_of_evidence"], ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"), allow_nan=False)
    return SYSTEM, TEMPLATE.format(entity=row["entity"], t0=row["t0"], h=row["horizon_months"], evidence=evidence)
