"""Version 2 of the small-molecule triage leaves.

Rule names in the comments refer to docs/loe-bench/REGULATORY-RULES.md.
Each leaf concerns the forecast horizon and the evidence available at cutoff.
"""
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from .common import add_months
from .kleene import T3, k_and

_NCE = {"NCE", "NCE*"}
_SCOPED = {"ODE", "ODE*", "NC", "NDF", "NE", "NP", "NP*", "NPP", "NR", "NS", "RTO", "RTO*", "RTO**"}
_COURT = {"RAI_COURT", "RAI_OB_PATENT"}


def _product(row):
    return row["appl_no"], row["product_no"]


@dataclass(frozen=True)
class _NceWindow:
    early_filing: date
    regular_filing: date
    nce_stay_floor: date


def _nce_window(approval, expiry, gain, ped):
    # NCE and NCE-1 filing; NCE enantiomer election; GAIN extension and waiver;
    # Pediatric exclusivity. Compare the original NDA date with the published date.
    added = 60 * gain + 6 * ped
    if approval is not None and expiry == add_months(approval, 60 + added):
        return _NceWindow(add_months(approval, 48 + added), expiry,
                          add_months(approval, 90 + 6 * ped))
    return None


def _nce_state(expiry, window, piv_dates, end):
    if expiry is not None and expiry <= end:
        return T3.TRUE
    if window is None:
        return T3.UNKNOWN
    if end < window.early_filing:
        return T3.FALSE
    if any(window.early_filing <= when < window.regular_filing and when <= end for when in piv_dates):
        return T3.TRUE
    # A reachable NCE-1 filing window leaves a conditional approval pathway.
    return T3.UNKNOWN


def _exclusivity_state(records, approvals, piv_dates, cutoff, end):
    if records is None:
        return T3.UNKNOWN, []
    products = defaultdict(list)
    for row in records:
        products[_product(row)].append(row)
    states, windows = [], []
    for (application, _), rows in products.items():
        dated_bases = set()
        extensions = defaultdict(set)
        for row in rows:
            code, expiry = row["code"], row["expiry"]
            if code in {"W", "PC", "CGT"}:
                # GAIN extension and waiver; 180-day first-applicant exclusivity; CGT.
                continue
            if code in {"GAIN", "PED"}:
                extensions[code].add(expiry)
                continue
            if code in _NCE:
                scope = "nce"
            elif code in _SCOPED or code.startswith(("D-", "I-", "M-")):
                # Orphan drug exclusivity; Three-year new clinical investigation exclusivity.
                scope = "scoped"
            else:
                scope = "unknown"
            dated_bases.add((scope, expiry, False, False))

        # Match only same-product extensions with one compatible base scope and date.
        # These additions identify companion rows. The end date always comes from the edition.
        for code, months in (("GAIN", 60), ("PED", 6)):
            for expiry in extensions[code]:
                options = {(scope, expiry, gain or code == "GAIN", ped or code == "PED")
                           for scope, base, gain, ped in dated_bases
                           if scope != "unknown" and base is not None and add_months(base, months) == expiry
                           and not ped and (code == "PED" or not gain)}
                if len(options) == 1:
                    dated_bases.update(options)
                else:
                    dated_bases.add(("unknown", expiry, False, False))

        approval = (approvals.get(application) or {}).get("approval_date")
        if approval is not None and approval > cutoff:
            approval = None
        for scope, expiry, gain, ped in dated_bases:
            if scope == "nce":
                window = _nce_window(approval, expiry, gain, ped)
                if window is not None:
                    windows.append(window)
                states.append(_nce_state(expiry, window, piv_dates, end))
            else:
                states.append(T3.TRUE if expiry is not None and expiry <= end else T3.UNKNOWN)
    return k_and(states), windows


def _patent_scope(row):
    if row.get("drug_substance") or row.get("drug_product"):
        return "DS_DP"
    has_flags = row.get("has_scope_flags", all(row.get(flag) is not None
                                             for flag in ("drug_substance", "drug_product")))
    if has_flags and row.get("use_code", "").startswith("U-"):
        return "METHOD_OF_USE"
    return "UNKNOWN"


def _patent_state(records, cutoff, end):
    # Patent relevance, linkage and carve-outs; Pediatric exclusivity; Expiry aggregation.
    if records is None:
        return T3.UNKNOWN
    grants = defaultdict(list)
    for row in records:
        submitted = row.get("submission_date")
        if submitted is None or submitted <= cutoff:
            grant = row["patent_no"].removesuffix("*PED").strip()
            grants[(_product(row), grant)].append(row)
    states = []
    for (_, grant), rows in grants.items():
        if grant and any(row.get("delist") for row in rows):
            continue
        base_scopes = {_patent_scope(row) for row in rows if not row["patent_no"].endswith("*PED")}
        for row in rows:
            expiry = row["expiry"]
            if expiry is not None and expiry <= end:
                continue
            scope = _patent_scope(row)
            if scope == "UNKNOWN" and row["patent_no"].endswith("*PED") and len(base_scopes) == 1:
                scope = next(iter(base_scopes))
            # An active use-code-only grant may be carved out. Unclassified and
            # incompletely dated grants also leave barrier applicability unresolved.
            states.append(T3.FALSE if grant and scope == "DS_DP" and expiry is not None else T3.UNKNOWN)
    return k_and(states)


def _challenge_state(witnesses, observation, nce_windows, end):
    # E7 court evidence and E7b patent relinking; Paragraph IV observation;
    # Conditional 30-month stay. A corroborated court filing is a proxy for notice.
    court = [w for w in witnesses if w.source in _COURT]
    if not court:
        return T3.FALSE if not witnesses and observation == T3.FALSE else T3.UNKNOWN
    corroborated = [w for w in court if w.corroboration and (
        w.source == "RAI_COURT" or w.corroboration.get("case_type") == "ANDA_CORROBORATED"
    )]
    if not corroborated:
        return T3.UNKNOWN
    filed = min(w.date for w in corroborated)
    proxy_end = max([add_months(filed, 30), *(nce.nce_stay_floor for nce in nce_windows
                    if nce.early_filing <= filed < nce.regular_filing)])
    return T3.FALSE if end < proxy_end else T3.TRUE


def build_v2_assignment(snapshot, cutoff, end, challenge_observation):
    evidence = snapshot.get("regulatory", {})
    witnesses = [w for w in snapshot.get("challenge_witnesses", ()) if w.date is not None and w.date <= cutoff]
    piv_dates = [w.date for w in witnesses if w.source == "FDA_PIV"]
    exclusivity, windows = _exclusivity_state(evidence.get("exclusivities"),
                                             evidence.get("original_approvals", {}), piv_dates, cutoff, end)
    return {
        "L_excl": exclusivity,
        "L_pat": _patent_state(evidence.get("patents"), cutoff, end),
        "L_challenge": _challenge_state(witnesses, challenge_observation, windows, end),
    }
