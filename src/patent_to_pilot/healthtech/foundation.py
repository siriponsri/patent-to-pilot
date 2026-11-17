"""P0 evidence foundation helpers (owner product plan, package P0).

Deterministic, offline and label-free. Nothing here downloads, calls a model,
reads evaluator material, or promotes a candidate to a verified association.
Every function is a pure transformation of typed records the engine already
produces (``SourcePayload``, ``EvidenceItem``, ``PatentCandidate``,
``DossierVersion``); stored contract schemas are unchanged.

Covered gaps:
- named-device intake normalization with explicit ambiguity (``resolve_device_intake``);
- typed candidate-link kinds (``CandidateLink``, ``company_link``, ``candidate_links``);
- sourced patent-family grouping (``PatentFamily``, ``group_candidates_by_family``);
- source availability states (``SourceState``, ``source_state_warnings``);
- missing patent dates (``PatentDates``, ``date_gaps``);
- cross-source field conflicts (``detect_field_conflicts``);
- source withdrawal that invalidates only descendants (``withdraw_source``);
- constraint-change revision and diff (``carry_forward``, ``dossier_diff``);
- quantity mentions without unit invention (``quantity_mentions``);
- deterministic replay IDs and fingerprints (``replay_run_id``, ``replay_fingerprint``).
"""
from __future__ import annotations

from datetime import date, datetime
import re
from typing import TYPE_CHECKING, Any, Iterable, Literal, Sequence
import unicodedata

from pydantic import Field, model_validator

from patent_to_pilot.healthtech.contracts import (AcquisitionEvent, Contract, DossierVersion,
    EvidenceItem, PatentCandidate, RunManifest, canonical_patent_id, content_hash)

if TYPE_CHECKING:  # pragma: no cover - typing only; avoids importing the engine at runtime
    from patent_to_pilot.healthtech.engine import DossierInput


# ------------------------------------------------------------------ intake

_TRADEMARKS = dict.fromkeys(map(ord, "®™©℠"), None)


def normalize_device_name(raw: str) -> str:
    """Case-fold, drop trademark signs and collapse separators.

    Hyphens and digits are kept: "Flow-Pump" and "FlowPump" stay different names.
    No fuzzy matching, abbreviation expansion or spelling correction.
    """
    text = unicodedata.normalize("NFKC", raw.translate(_TRADEMARKS)).casefold()
    return " ".join(re.sub(r"[\s,;:()\[\]]+", " ", text).split())


class DeviceRecordRef(Contract):
    """One device record as it appears in a sourced record (no inferred fields)."""

    source_id: str = Field(min_length=1)
    device_name: str = Field(min_length=1)
    manufacturer: str | None = None
    model: str | None = None


class DeviceResolution(Contract):
    raw: str
    normalized: str
    status: Literal["resolved", "unresolved_intake", "not_found"]
    matches: list[DeviceRecordRef]
    manufacturer: str | None = None
    reason: str = ""

    @model_validator(mode="after")
    def consistent(self):
        if self.status == "not_found" and self.matches:
            raise ValueError("not_found has no matches")
        if self.status != "not_found" and not self.matches:
            raise ValueError("resolved/unresolved intake needs matching records")
        if self.status != "resolved" and (self.manufacturer is not None or not self.reason):
            raise ValueError("unresolved intake carries a reason and no manufacturer")
        return self


def resolve_device_intake(raw: str, records: Sequence[DeviceRecordRef]) -> DeviceResolution:
    """Match a typed device name against sourced records by whole-token prefix.

    A record matches when the normalized query tokens are the first tokens of the
    normalized record name. Records sharing a normalized name and manufacturer are one
    device seen in several sources. One device -> ``resolved``; several devices
    (brand vs model, model versions, different manufacturers) -> ``unresolved_intake``
    with every candidate listed; none -> ``not_found``. The manufacturer is copied
    from the record, never guessed.
    """
    normalized = normalize_device_name(raw)
    if not normalized:
        raise ValueError("device name is blank after normalization")
    query = normalized.split()
    matches = sorted((r for r in records
                      if normalize_device_name(r.device_name).split()[:len(query)] == query),
                     key=lambda r: r.source_id)
    devices = {(normalize_device_name(r.device_name),
                normalize_party_name(r.manufacturer) if r.manufacturer else None) for r in matches}
    if not matches:
        return DeviceResolution(raw=raw, normalized=normalized, status="not_found", matches=[],
                                reason="No sourced device record matches this name; request an identifier.")
    if len(devices) > 1:
        return DeviceResolution(raw=raw, normalized=normalized, status="unresolved_intake", matches=matches,
                                reason=f"{len(devices)} distinct devices match; ask the user to choose one.")
    return DeviceResolution(raw=raw, normalized=normalized, status="resolved", matches=matches,
                            manufacturer=matches[0].manufacturer)


# ------------------------------------------------------------ candidate links

_LEGAL_SUFFIXES = {"inc", "incorporated", "llc", "ltd", "limited", "corp", "corporation", "co",
                   "company", "gmbh", "ag", "sa", "plc", "bv", "nv", "kk", "oy", "ab", "spa", "srl",
                   "pty", "lp", "llp"}


def normalize_party_name(name: str) -> str:
    """Case-fold, drop punctuation and trailing legal-form words only."""
    tokens = re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", name).casefold())
    while tokens and tokens[-1] in _LEGAL_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


LinkType = Literal["retrieved_candidate", "company_name_match", "source_disclosed", "reviewer_confirmed"]
VERIFIED_LINK_TYPES = frozenset({"source_disclosed", "reviewer_confirmed"})


class CandidateLink(Contract):
    """Typed device-patent link. Only disclosed or reviewer-confirmed links are associations."""

    device_id: str = Field(min_length=1)
    patent_id_canonical: str
    link_type: LinkType
    basis: str = Field(min_length=1)
    source_ids: list[str] = Field(min_length=1)
    evidence_ids: list[str] = Field(default_factory=list)
    reviewer_decision_id: str | None = None

    @model_validator(mode="after")
    def basis_matches_type(self):
        if canonical_patent_id(self.patent_id_canonical) != self.patent_id_canonical:
            raise ValueError("patent id must be canonical")
        if self.link_type == "source_disclosed" and not self.evidence_ids:
            raise ValueError("source_disclosed needs disclosure evidence")
        if (self.link_type == "reviewer_confirmed") != (self.reviewer_decision_id is not None):
            raise ValueError("reviewer_confirmed needs a reviewer decision, and only it may carry one")
        return self

    @property
    def is_verified_association(self) -> bool:
        return self.link_type in VERIFIED_LINK_TYPES


def company_link(*, device_id: str, manufacturer: str, manufacturer_source_id: str, patent_id: str,
                 assignee: str, assignee_source_id: str) -> CandidateLink | None:
    """Return a ``company_name_match`` candidate when the normalized names agree, else None.

    A shared company name never makes a verified association, and a manufacturer that
    differs from the assignee produces no link at all.
    """
    left, right = normalize_party_name(manufacturer), normalize_party_name(assignee)
    if not left or left != right:
        return None
    return CandidateLink(device_id=device_id, patent_id_canonical=canonical_patent_id(patent_id),
        link_type="company_name_match", source_ids=[manufacturer_source_id, assignee_source_id],
        basis=f"Normalized manufacturer and assignee are both '{left}'. "
              "A company-name match is not evidence that the patent covers the device.")


def candidate_links(dossier: DossierVersion) -> list[CandidateLink]:
    """Typed links for every dossier candidate, in dossier order."""
    evidence = {e.evidence_id: e for e in dossier.evidence}
    links = []
    for c in dossier.candidates:
        if c.association_status == "disclosed_link":
            item = evidence[c.disclosure_evidence_id]
            links.append(CandidateLink(device_id=dossier.query.device_id_canonical,
                patent_id_canonical=c.patent_id_canonical, link_type="source_disclosed",
                source_ids=list(dict.fromkeys([c.source_id, item.source_id])),
                evidence_ids=[item.evidence_id], basis=f"Disclosure evidence {item.evidence_id} ({item.locator})"))
        else:
            links.append(CandidateLink(device_id=dossier.query.device_id_canonical,
                patent_id_canonical=c.patent_id_canonical, link_type="retrieved_candidate",
                source_ids=[c.source_id], basis="Retrieved by actions " + ", ".join(c.retrieval_action_ids)))
    return links


# --------------------------------------------------------------- families

class PatentFamily(Contract):
    family_id: str = Field(min_length=1)
    member_ids: list[str] = Field(min_length=1)
    representative_id: str
    source_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def members(self):
        if any(canonical_patent_id(m) != m for m in self.member_ids):
            raise ValueError("family members must be canonical patent ids")
        if len(set(self.member_ids)) != len(self.member_ids):
            raise ValueError("duplicate family member")
        if self.representative_id not in self.member_ids:
            raise ValueError("representative must be a member")
        return self


class FamilyGroup(Contract):
    family_id: str | None
    family_source_id: str | None
    representative_id: str | None
    member_ids: list[str] = Field(min_length=1)
    best_rank: int = Field(ge=1)


def group_candidates_by_family(candidates: Sequence[PatentCandidate],
                               families: Sequence[PatentFamily]) -> list[FamilyGroup]:
    """Collapse candidates into family rows using only sourced family records.

    Candidates without a family record stay separate rows: different kind codes or
    jurisdictions are never merged by number similarity. A document assigned to two
    different families fails closed.
    """
    owner: dict[str, PatentFamily] = {}
    for family in families:
        for member in family.member_ids:
            if member in owner and owner[member].family_id != family.family_id:
                raise ValueError(f"{member} is assigned to more than one family")
            owner[member] = family
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    for rank, c in enumerate(candidates, 1):
        family = owner.get(c.patent_id_canonical)
        if family and c.family_id and c.family_id != family.family_id:
            raise ValueError(f"{c.patent_id_canonical} carries a different family id")
        key = ("family", family.family_id) if family else ("document", c.patent_id_canonical)
        row = rows.setdefault(key, {"family_id": family.family_id if family else None,
            "family_source_id": family.source_id if family else None,
            "representative_id": family.representative_id if family else None,
            "member_ids": [], "best_rank": rank})
        row["member_ids"].append(c.patent_id_canonical)
    return [FamilyGroup(**row) for row in rows.values()]


# ---------------------------------------------------------- source states

SourceStatus = Literal["current", "archived", "withdrawn", "restricted", "expired",
                       "unknown_date", "fetch_failed"]
_STATUS_TEXT = {
    "archived": "available only as an archived copy; treat it as historical and request a current record",
    "withdrawn": "withdrawn by its publisher; evidence from it must not be reused",
    "restricted": "restricted; it cannot be displayed or exported",
    "expired": "past its declared validity; confirm whether a newer version exists",
    "unknown_date": "undated; cutoff comparisons that depend on it are unknown",
    "fetch_failed": "not retrieved in this snapshot; nothing was substituted for it",
}


class SourceState(Contract):
    """Observed availability of one exact source revision."""

    source_id: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    status: SourceStatus
    observed_at: datetime
    reason: str = Field(min_length=1)
    replacement_source_id: str | None = None


def source_state_warnings(dossier: DossierVersion, states: Iterable[SourceState]) -> list[str]:
    """Readable warnings for non-current sources; states must name exact dossier revisions."""
    sources = {s.source.source_id: s for s in dossier.sources}
    declared: dict[str, SourceState] = {}
    for state in states:
        source = sources.get(state.source_id)
        if source is None or source.source.version_label != state.source_version:
            raise ValueError(f"state does not match a dossier source revision: {state.source_id}")
        if state.source_id in declared:
            raise ValueError(f"duplicate state for {state.source_id}")
        declared[state.source_id] = state
    warnings = [f"Source {s.source_id} ({s.source_version}) is {s.status} as observed "
                f"{s.observed_at.isoformat()}: {_STATUS_TEXT[s.status]}. Reason: {s.reason}"
                for s in declared.values() if s.status != "current"]
    regulatory = [sid for sid, s in sources.items() if s.source.source_type == "regulatory_record"]
    if regulatory and all(sid in declared and declared[sid].status != "current" for sid in regulatory):
        statuses = sorted({declared[sid].status for sid in regulatory})
        warnings.append("No current regulatory record: every regulatory source is "
                        + "/".join(statuses) + ". Regulatory context is historical only.")
    return warnings


# ------------------------------------------------------------ patent dates

class PatentDates(Contract):
    patent_id_canonical: str
    filing_date: date | None = None
    publication_date: date | None = None
    source_id: str = Field(min_length=1)

    @model_validator(mode="after")
    def canonical(self):
        if canonical_patent_id(self.patent_id_canonical) != self.patent_id_canonical:
            raise ValueError("patent id must be canonical")
        return self


DateFlagKind = Literal["missing_filing_date", "missing_publication_date", "cutoff_unknown",
                       "after_cutoff", "filing_after_publication"]


class DateFlag(Contract):
    patent_id_canonical: str
    flag: DateFlagKind
    detail: str


def date_gaps(dates: Sequence[PatentDates], *, cutoff: date) -> list[DateFlag]:
    """Flag missing or inconsistent bibliographic dates. Nothing is imputed.

    The cutoff test uses the publication date only; a filing date never stands in for it.
    """
    flags: list[DateFlag] = []
    for d in dates:
        pid = d.patent_id_canonical
        if d.filing_date is None:
            flags.append(DateFlag(patent_id_canonical=pid, flag="missing_filing_date",
                                  detail=f"No filing date in {d.source_id}; not inferred from other dates."))
        if d.publication_date is None:
            flags.append(DateFlag(patent_id_canonical=pid, flag="missing_publication_date",
                                  detail=f"No publication date in {d.source_id}."))
            flags.append(DateFlag(patent_id_canonical=pid, flag="cutoff_unknown",
                                  detail=f"Cannot tell whether it was public before {cutoff}."))
        elif d.publication_date > cutoff:
            flags.append(DateFlag(patent_id_canonical=pid, flag="after_cutoff",
                                  detail=f"Published {d.publication_date}, after cutoff {cutoff}."))
        if d.filing_date and d.publication_date and d.filing_date > d.publication_date:
            flags.append(DateFlag(patent_id_canonical=pid, flag="filing_after_publication",
                                  detail="Filing date is later than publication date; check the source."))
    return flags


# --------------------------------------------------------------- conflicts

class ConflictValue(Contract):
    evidence_id: str
    source_id: str
    source_version: str
    value: Any


class FieldConflict(Contract):
    field: str
    status: Literal["conflict"] = "conflict"
    values: list[ConflictValue] = Field(min_length=2)


def detect_field_conflicts(evidence: Sequence[EvidenceItem]) -> list[FieldConflict]:
    """Report structured fields whose values differ across evidence items. No winner is chosen.

    Values are compared by canonical JSON (type-sensitive). Only checked source facts
    take part; unresolved or inferred items are excluded.
    """
    groups: dict[str, list[EvidenceItem]] = {}
    for e in evidence:
        if e.extraction_method == "structured_field" and e.evidence_kind not in {"unresolved", "system_inference"}:
            groups.setdefault(e.structured_field, []).append(e)
    conflicts = []
    for field in sorted(groups):
        items = groups[field]
        if len({content_hash(e.structured_value) for e in items}) > 1:
            conflicts.append(FieldConflict(field=field, values=[ConflictValue(evidence_id=e.evidence_id,
                source_id=e.source_id, source_version=e.source_version, value=e.structured_value) for e in items]))
    return conflicts


# --------------------------------------------------------------- withdrawal

class WithdrawalImpact(Contract):
    source_id: str
    reason: str
    observed_at: datetime
    affected_evidence_ids: list[str]
    affected_candidate_ids: list[str]
    preserved_evidence_ids: list[str]
    preserved_candidate_ids: list[str]


def _withdrawal_marker(source_id: str) -> str:
    return f"Source {source_id} withdrawn"


def withdraw_source(dossier: DossierVersion, source_id: str, *, reason: str,
                    observed_at: datetime) -> tuple[DossierVersion, WithdrawalImpact]:
    """Return the next dossier version with one source withdrawn.

    Descendants only: evidence from the source becomes ``unresolved``; a candidate whose
    patent document is the source, or whose disclosure evidence came from it, is marked
    affected and loses any disclosed status. Every other evidence item and candidate is
    carried over unchanged. The source payload stays in the dossier (original immutable);
    the withdrawal is recorded in ``unresolved_items``. ``observed_at`` becomes the new
    version's ``created_at`` so the result is replayable.
    """
    if not reason.strip():
        raise ValueError("withdrawal needs a reason")
    if source_id not in {s.source.source_id for s in dossier.sources}:
        raise ValueError(f"source not in dossier: {source_id}")
    marker = _withdrawal_marker(source_id)
    if any(item.startswith(marker) for item in dossier.unresolved_items):
        raise ValueError(f"source already withdrawn: {source_id}")
    evidence, affected_e = [], []
    for e in dossier.evidence:
        if e.source_id != source_id:
            evidence.append(e)
            continue
        affected_e.append(e.evidence_id)
        evidence.append(EvidenceItem.model_validate({**e.model_dump(), "evidence_kind": "unresolved",
            "verification_status": "not_independently_validated",
            "statement": f"[Withdrawn source {source_id}] {e.statement}",
            "support_basis": f"Source withdrawn: {reason}. Original basis: {e.support_basis}"}))
    withdrawn_evidence = set(affected_e)
    candidates, affected_c = [], []
    for c in dossier.candidates:
        if c.source_id != source_id and c.disclosure_evidence_id not in withdrawn_evidence:
            candidates.append(c)
            continue
        affected_c.append(c.patent_id_canonical)
        candidates.append(PatentCandidate.model_validate({**c.model_dump(),
            "association_status": "retrieved_candidate", "disclosure_evidence_id": None}))
    note = (f"{marker} (observed {observed_at.isoformat()}): {reason}. "
            f"{len(affected_e)} evidence item(s) and {len(affected_c)} candidate(s) that depended on it "
            "are now unresolved; nothing else changed.")
    revised = DossierVersion.model_validate({**dossier.model_dump(), "evidence": evidence,
        "candidates": candidates, "unresolved_items": [*dossier.unresolved_items, note],
        "version": dossier.version + 1, "parent_version": dossier.version, "created_at": observed_at})
    impact = WithdrawalImpact(source_id=source_id, reason=reason, observed_at=observed_at,
        affected_evidence_ids=affected_e, affected_candidate_ids=affected_c,
        preserved_evidence_ids=[e.evidence_id for e in dossier.evidence if e.evidence_id not in withdrawn_evidence],
        preserved_candidate_ids=[c.patent_id_canonical for c in dossier.candidates
                                 if c.patent_id_canonical not in set(affected_c)])
    return revised, impact


# ------------------------------------------------------ revision and diff

def carry_forward(previous: DossierVersion, rerun: DossierVersion) -> DossierVersion:
    """Make a fresh run the next version of ``previous``, keeping the user's edits."""
    if rerun.project_id != previous.project_id:
        raise ValueError("rerun belongs to a different project")
    return DossierVersion.model_validate({**rerun.model_dump(), "dossier_id": previous.dossier_id,
        "version": previous.version + 1, "parent_version": previous.version,
        "user_edits": {**previous.user_edits, **rerun.user_edits}})


class DossierDiff(Contract):
    query_changes: list[str]
    added_sources: list[str]
    removed_sources: list[str]
    changed_sources: list[str]
    added_candidates: list[str]
    removed_candidates: list[str]
    changed_candidates: list[str]
    unchanged_candidates: list[str]
    added_evidence: list[str]
    removed_evidence: list[str]
    changed_evidence: list[str]
    unchanged_evidence: list[str]


# Retrieval trace differs between runs by construction; it is not evidence.
_CANDIDATE_TRACE_FIELDS = {"retrieval_action_ids", "scores"}


def _split(before: dict[str, Any], after: dict[str, Any]) -> tuple[list[str], ...]:
    added = [k for k in after if k not in before]
    removed = [k for k in before if k not in after]
    common = [k for k in before if k in after]
    changed = [k for k in common if before[k] != after[k]]
    return added, removed, changed, [k for k in common if k not in changed]


def dossier_diff(before: DossierVersion, after: DossierVersion) -> DossierDiff:
    """Before/after impact of a revision, keyed by stable IDs, in the original order."""
    q_before, q_after = before.query.model_dump(mode="json"), after.query.model_dump(mode="json")
    sources = _split({s.source.source_id: (s.source.version_label, s.source.sha256) for s in before.sources},
                     {s.source.source_id: (s.source.version_label, s.source.sha256) for s in after.sources})

    def link(c: PatentCandidate) -> dict[str, Any]:
        return {k: v for k, v in c.model_dump(mode="json").items() if k not in _CANDIDATE_TRACE_FIELDS}

    candidates = _split({c.patent_id_canonical: link(c) for c in before.candidates},
                        {c.patent_id_canonical: link(c) for c in after.candidates})
    evidence = _split({e.evidence_id: e.model_dump(mode="json") for e in before.evidence},
                      {e.evidence_id: e.model_dump(mode="json") for e in after.evidence})
    return DossierDiff(query_changes=sorted(k for k in q_before if q_before[k] != q_after.get(k)),
        added_sources=sources[0], removed_sources=sources[1], changed_sources=sources[2],
        added_candidates=candidates[0], removed_candidates=candidates[1],
        changed_candidates=candidates[2], unchanged_candidates=candidates[3],
        added_evidence=evidence[0], removed_evidence=evidence[1],
        changed_evidence=evidence[2], unchanged_evidence=evidence[3])


# --------------------------------------------------------------- quantities

_UNITS = sorted(["mL/h", "mL/min", "mmHg", "cmH2O", "kPa", "psi", "bar", "°C", "°F", "mL", "µL",
                 "uL", "mg", "µg", "kg", "g", "mm", "cm", "µm", "um", "nm", "Hz", "kHz", "mA", "mV",
                 "V", "W", "ms", "s", "min", "h", "%", "Fr", "F", "L", "C", "M"], key=len, reverse=True)
# F: French gauge, Fahrenheit or farad. C: Celsius or coulomb. M: molar, mega or metre.
AMBIGUOUS_UNITS = frozenset({"F", "C", "M"})
_QUANTITY = re.compile(r"(?<![\w.,])(?P<value>\d+(?:[.,]\d+)?)"
                       r"(?:\s?(?P<unit>" + "|".join(map(re.escape, _UNITS)) + r")(?![^\W_]))?")


class QuantityMention(Contract):
    value: str
    unit: str | None
    start: int = Field(ge=0)
    end: int = Field(ge=0)
    status: Literal["unit_stated", "unit_missing", "unit_ambiguous", "number_ambiguous"]


def quantity_mentions(text: str) -> list[QuantityMention]:
    """Numbers as written, with the unit only when it is written next to them.

    No unit conversion and no default unit. A comma inside a number ("1,5") is flagged
    because it can be a decimal comma or a thousands separator.
    """
    found = []
    for m in _QUANTITY.finditer(text):
        value, unit = m.group("value"), m.group("unit")
        status = ("number_ambiguous" if "," in value else "unit_missing" if unit is None
                  else "unit_ambiguous" if unit in AMBIGUOUS_UNITS else "unit_stated")
        found.append(QuantityMention(value=value, unit=unit, start=m.start(), end=m.end(), status=status))
    return found


# -------------------------------------------------------------------- replay

VOLATILE_FIELDS = frozenset({"created_at", "started_at", "ended_at", "elapsed_seconds"})


def strip_volatile(value: Any) -> Any:
    """Drop declared wall-clock fields at every depth; everything else must replay exactly."""
    if isinstance(value, dict):
        return {k: strip_volatile(v) for k, v in value.items() if k not in VOLATILE_FIELDS}
    if isinstance(value, list):
        return [strip_volatile(v) for v in value]
    return value


def replay_run_id(data: "DossierInput", *, prefix: str = "ht") -> str:
    """Run ID derived from the input content (declared volatile fields excluded)."""
    if not re.fullmatch(r"[a-z0-9]{1,16}", prefix):
        raise ValueError("prefix must be short lowercase alphanumeric")
    digest = content_hash({"replay": "ht-replay-v1", "input": strip_volatile(data.model_dump(mode="json"))})
    return f"{prefix}-{digest[:24]}"


def replay_fingerprint(dossier: DossierVersion, events: Sequence[AcquisitionEvent],
                       manifest: RunManifest) -> str:
    """Hash of a run's outputs with only the declared volatile fields removed."""
    return content_hash(strip_volatile({"dossier": dossier.model_dump(mode="json"),
                                        "events": [e.model_dump(mode="json") for e in events],
                                        "manifest": manifest.model_dump(mode="json")}))
