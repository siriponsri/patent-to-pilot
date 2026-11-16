"""Paper 2 (P2-OA) prototype: evaluator-only funnel metrics and grounding checks.

Evaluator only. Runtime modules never import this module, and this module never
imports runtime code: it reads plain funnel records (dicts) plus reference labels
passed in as metadata.

Per query and per stratum, for each funnel stage (search, visit, select):
``R = |K ∩ stage set| / |K|``. ``K = 0`` gives NA (``K_EMPTY``); a stage the arm did
not run gives NA (``STAGE_NOT_RUN``); a query without labels gives NA (``NO_LABELS``).
Documents outside K are *unjudged*: they are counted for description and are
never negatives.

Grounding is mechanical only (no LLM judge): the source id exists, the recorded
version matches, the byte locator is valid (field exists, in range, on UTF-8
character boundaries), and an optional quote matches the located span after the
declared normalisation.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Protocol, Sequence

SCHEMA_VERSION = "ptp-paper2-funnel-eval-v0"
NORMALISATION_ID = "nfc-collapse-whitespace-strip-v1"

STAGES = ("search", "visit", "select")
DOMAINS = ("IN", "OUT")
BASES = ("102", "103", "both")
DEFAULT_STRATA = ("ALL", "IN", "OUT", "102", "103", "OUT-102", "OUT-103", "IN-102", "IN-103")

NA_STAGE_NOT_RUN = "STAGE_NOT_RUN"
NA_K_EMPTY = "K_EMPTY"
NA_NO_LABELS = "NO_LABELS"


@dataclass(frozen=True)
class ReferenceLabel:
    """One known reference of a query: domain (IN/OUT) and legal basis (102/103/both)."""

    doc_id: str
    domain: str
    basis: str

    def __post_init__(self) -> None:
        if not isinstance(self.doc_id, str) or not self.doc_id:
            raise ValueError("doc_id must be a non-empty string")
        if self.domain not in DOMAINS:
            raise ValueError(f"domain must be one of {DOMAINS}")
        if self.basis not in BASES:
            raise ValueError(f"basis must be one of {BASES}")

    def bases(self) -> frozenset[str]:
        return frozenset({"102", "103"}) if self.basis == "both" else frozenset({self.basis})


def in_stratum(label: ReferenceLabel, stratum: str) -> bool:
    if stratum == "ALL":
        return True
    if stratum in DOMAINS:
        return label.domain == stratum
    if stratum in ("102", "103"):
        return stratum in label.bases()
    domain, _, basis = stratum.partition("-")
    if domain in DOMAINS and basis in ("102", "103"):
        return label.domain == domain and basis in label.bases()
    raise ValueError(f"unknown stratum {stratum}")


def stage_sets(record: Mapping[str, Any]) -> dict[str, set[str] | None]:
    """Stage -> id set, or None if the arm did not run that stage."""

    run = set(record["stages_run"])
    raw = {"search": record["searched"], "visit": record["visited"],
           "select": [s["doc_id"] for s in record["selections"]]}
    return {st: (set(raw[st]) if st in run else None) for st in STAGES}


def _labels_map(labels: Sequence[ReferenceLabel]) -> dict[str, ReferenceLabel]:
    out: dict[str, ReferenceLabel] = {}
    for lab in labels:
        if lab.doc_id in out:
            raise ValueError(f"duplicate label for {lab.doc_id}")
        out[lab.doc_id] = lab
    return out


def query_funnel(record: Mapping[str, Any], labels: Sequence[ReferenceLabel] | None, *,
                 strata: Sequence[str] = DEFAULT_STRATA,
                 other_citations: Iterable[str] = ()) -> dict[str, Any]:
    sets = stage_sets(record)
    lab = None if labels is None else _labels_map(labels)
    other = set(other_citations)
    cells: dict[str, dict[str, Any]] = {}
    for stratum in strata:
        k = None if lab is None else {d for d, l in lab.items() if in_stratum(l, stratum)}
        row = {}
        for st in STAGES:
            ids = sets[st]
            if lab is None:
                row[st] = {"recall": None, "na": NA_NO_LABELS, "k": None, "hits": None}
            elif ids is None:
                row[st] = {"recall": None, "na": NA_STAGE_NOT_RUN, "k": len(k), "hits": None}
            elif not k:
                row[st] = {"recall": None, "na": NA_K_EMPTY, "k": 0, "hits": None}
            else:
                hits = len(k & ids)
                row[st] = {"recall": hits / len(k), "na": None, "k": len(k), "hits": hits}
        cells[stratum] = row
    describe = {}
    for st in STAGES:
        ids = sets[st]
        if ids is None:
            describe[st] = None
            continue
        known = set() if lab is None else set(lab)
        describe[st] = {"size": len(ids), "judged": len(ids & known), "unjudged": len(ids - known),
                        "other_citation": len((ids - known) & other)}
    return {"query_id": record["query_id"], "arm": record["arm"], "strata": cells, "stage_sizes": describe}


def evaluate(records: Sequence[Mapping[str, Any]], labels_by_query: Mapping[str, Sequence[ReferenceLabel]], *,
             strata: Sequence[str] = DEFAULT_STRATA,
             other_citations: Mapping[str, Iterable[str]] | None = None) -> dict[str, Any]:
    """Per-query cells plus query-macro (eligible queries only) and micro recall per arm."""

    other_citations = other_citations or {}
    per_query = [query_funnel(r, labels_by_query.get(r["query_id"]), strata=strata,
                              other_citations=other_citations.get(r["query_id"], ())) for r in records]
    arms: dict[str, Any] = {}
    for arm in sorted({r["arm"] for r in records}):
        rows = [p for p in per_query if p["arm"] == arm]
        agg: dict[str, dict[str, Any]] = {}
        for stratum in strata:
            agg[stratum] = {}
            for st in STAGES:
                cells = [p["strata"][stratum][st] for p in rows]
                ok = [c for c in cells if c["na"] is None]
                na: dict[str, int] = {}
                for c in cells:
                    if c["na"] is not None:
                        na[c["na"]] = na.get(c["na"], 0) + 1
                hits, k = sum(c["hits"] for c in ok), sum(c["k"] for c in ok)
                agg[stratum][st] = {
                    "macro_recall": (sum(c["recall"] for c in ok) / len(ok)) if ok else None,
                    "micro_recall": (hits / k) if k else None,
                    "n_eligible": len(ok), "n_na": dict(sorted(na.items())), "hits": hits, "k": k,
                }
        arms[arm] = {"queries": len(rows), "strata": agg}
    return {"schema": SCHEMA_VERSION, "strata": list(strata), "per_query": per_query, "arms": arms}


# ---------------------------------------------------------------------------
# Mechanical grounding
# ---------------------------------------------------------------------------


class GroundingSource(Protocol):
    def version(self, doc_id: str) -> str | None: ...

    def field_text(self, doc_id: str, field_name: str) -> str | None: ...


_WS = re.compile(r"\s+")


def normalise(text: str) -> str:
    """Declared normalisation ``NORMALISATION_ID``: NFC, collapse whitespace, strip."""

    return _WS.sub(" ", unicodedata.normalize("NFC", text)).strip()


def check_locator(source: GroundingSource, doc_id: str, loc: Mapping[str, Any]) -> dict[str, Any]:
    text = source.field_text(doc_id, loc.get("field")) if isinstance(loc.get("field"), str) else None
    start, end = loc.get("start"), loc.get("end")
    valid, span = False, None
    if text is not None and all(isinstance(x, int) and not isinstance(x, bool) for x in (start, end)):
        data = text.encode("utf-8")
        if 0 <= start < end <= len(data):
            try:
                span = data[start:end].decode("utf-8")  # strict: fails off a character boundary
                valid = True
            except UnicodeDecodeError:
                valid = False
    quote = loc.get("quote")
    if quote is None:
        quote_match = None
    else:
        quote_match = bool(valid and normalise(span) == normalise(quote))
    return {"field": loc.get("field"), "locator_valid": valid, "quote_checked": quote is not None,
            "quote_match": quote_match}


def check_selection(source: GroundingSource, selection: Mapping[str, Any]) -> dict[str, Any]:
    doc_id = selection["doc_id"]
    version = source.version(doc_id)
    exists = version is not None
    locs = [check_locator(source, doc_id, l) if exists else
            {"field": l.get("field"), "locator_valid": False, "quote_checked": "quote" in l,
             "quote_match": False if "quote" in l else None}
            for l in selection["locations"]]
    version_match = exists and selection.get("version") == version
    grounded = (exists and version_match and bool(locs) and all(l["locator_valid"] for l in locs)
                and all(l["quote_match"] is not False for l in locs))
    return {"doc_id": doc_id, "source_exists": exists, "version_match": version_match,
            "locators": locs, "grounded": grounded}


def grounding_report(records: Sequence[Mapping[str, Any]], source: GroundingSource) -> dict[str, Any]:
    arms: dict[str, Any] = {}
    for rec in records:
        a = arms.setdefault(rec["arm"], {"selections": 0, "source_exists": 0, "version_match": 0,
                                         "locators": 0, "locator_valid": 0, "quote_checked": 0,
                                         "quote_match": 0, "grounded": 0})
        for sel in rec["selections"]:
            c = check_selection(source, sel)
            a["selections"] += 1
            a["source_exists"] += c["source_exists"]
            a["version_match"] += c["version_match"]
            a["grounded"] += c["grounded"]
            for l in c["locators"]:
                a["locators"] += 1
                a["locator_valid"] += l["locator_valid"]
                a["quote_checked"] += l["quote_checked"]
                a["quote_match"] += bool(l["quote_match"])
    return {"schema": SCHEMA_VERSION, "normalisation": NORMALISATION_ID, "arms": dict(sorted(arms.items()))}
