"""Solution Scout contracts and lane logic (M0).

A problem brief and the user's own IPC3 classes go in. Two lanes come out of one dense ranking:
families sharing any own class ("own_field") and families sharing none ("other_fields"). The
LLM never ranks; it only writes transfer rationales whose quotes are checked for a literal match.
A literal match is not semantic support. Spec: docs/healthtech/research/SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md.
"""
from __future__ import annotations

from datetime import date
import re
from typing import Literal, Mapping, Sequence

from pydantic import Field, field_validator, model_validator

from patent_to_pilot.healthtech.contracts import Contract, canonical_patent_id

IPC3_PATTERN = r"^[A-H][0-9]{2}$"
QUOTE_MIN_WORDS = 5
QUOTE_MAX_WORDS = 60
LITERAL_MATCH_LABEL = "literal match is not semantic support"
Lane = Literal["own_field", "other_fields"]


def normalize_ipc3(codes: Sequence[str]) -> tuple[str, ...]:
    """Upper-case, validate and deduplicate IPC3 codes (e.g. 'a61' -> 'A61'); unknown syntax fails closed."""
    out = sorted({code.strip().upper() for code in codes})
    bad = [code for code in out if not re.fullmatch(IPC3_PATTERN, code)]
    if bad:
        raise ValueError(f"unsupported IPC3 code(s): {bad}")
    return tuple(out)


def class_member_indices(codes: Sequence[str], class_members: Mapping[str, Sequence[int]]) -> list[int]:
    """Sorted corpus positions of families carrying any of ``codes`` (the lane mask for a dense runner)."""
    return sorted({i for code in codes for i in class_members.get(code, ())})


def partition_by_field(ranked: Sequence[str], family_ipc3: Mapping[str, Sequence[str]],
                       own_ipc3: Sequence[str]) -> tuple[list[str], list[str]]:
    """Split one ranking into own-field and other-field lanes, keeping order.

    A family without IPC3 codes shares no own class, so it falls in the other-fields lane, as in the
    dense runner's ``excluded_ipc3`` mask.
    """
    own = set(own_ipc3)
    own_lane, other_lane = [], []
    for family in dict.fromkeys(ranked):
        (own_lane if own.intersection(family_ipc3.get(family, ())) else other_lane).append(family)
    return own_lane, other_lane


def two_lane_shortlist(own_lane: Sequence[str], other_lane: Sequence[str], n_own: int,
                       n_other: int) -> list[tuple[Lane, int, str]]:
    """(lane, rank_in_lane, family) rows: the first ``n_own`` of the own lane, then the first ``n_other`` of the other."""
    rows: list[tuple[Lane, int, str]] = [("own_field", i + 1, f) for i, f in enumerate(own_lane[:n_own])]
    rows += [("other_fields", i + 1, f) for i, f in enumerate(other_lane[:n_other])]
    return rows


class QuoteCheck(Contract):
    quote: str = Field(min_length=1, max_length=2000)
    status: Literal["matched", "not_found", "too_short", "too_long"]
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def offsets(self):
        if (self.status == "matched") != (self.start is not None and self.end is not None):
            raise ValueError("matched quotes need offsets; other statuses must not have them")
        if self.start is not None and self.end is not None and self.end <= self.start:
            raise ValueError("quote end must follow start")
        return self


def check_quote(quote: str, source_text: str) -> QuoteCheck:
    """Literal check: the quote's words in order, any whitespace between them, case and punctuation exact.

    Offsets index ``source_text`` as given, so they are an exact source locator.
    """
    words = quote.split()
    if len(words) < QUOTE_MIN_WORDS:
        return QuoteCheck(quote=quote, status="too_short")
    if len(words) > QUOTE_MAX_WORDS:
        return QuoteCheck(quote=quote, status="too_long")
    match = re.search(r"\s+".join(re.escape(w) for w in words), source_text)
    if match is None:
        return QuoteCheck(quote=quote, status="not_found")
    return QuoteCheck(quote=quote, status="matched", start=match.start(), end=match.end())


class ScoutBrief(Contract):
    brief_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    text: str = Field(min_length=1, max_length=4000)
    own_ipc3: list[str] = Field(min_length=1, max_length=50)
    own_ipc3_basis: Literal["typed", "reference_patent"]
    reference_patent_raw: str | None = None
    reference_patent_canonical: str | None = None
    language: Literal["en", "th"] = "en"
    data_class: Literal["synthetic", "public"]

    @field_validator("own_ipc3")
    @classmethod
    def codes(cls, value: list[str]) -> list[str]:
        normalized = list(normalize_ipc3(value))
        if normalized != value:
            raise ValueError("own_ipc3 must be normalized: upper-case, sorted, unique")
        return value

    @model_validator(mode="after")
    def reference(self):
        has_raw = self.reference_patent_raw is not None
        if (self.own_ipc3_basis == "reference_patent") != has_raw:
            raise ValueError("reference_patent basis requires the raw reference identifier, and only then")
        if has_raw and self.reference_patent_canonical != canonical_patent_id(self.reference_patent_raw):
            raise ValueError("reference_patent_canonical must be canonical_patent_id(reference_patent_raw)")
        if not has_raw and self.reference_patent_canonical is not None:
            raise ValueError("canonical reference without a raw reference")
        if not self.text.strip():
            raise ValueError("brief text must not be blank")
        return self


class LaneSplit(Contract):
    n_own: int = Field(ge=0, le=200)
    n_other: int = Field(ge=0, le=200)

    @model_validator(mode="after")
    def budget(self):
        if not 1 <= self.n_own + self.n_other <= 200:
            raise ValueError("shortlist length must be between 1 and 200")
        return self


class ScoutCandidate(Contract):
    family_id: str = Field(min_length=1)
    lane: Lane
    rank_in_lane: int = Field(ge=1)
    score: float
    ipc3: list[str] = Field(default_factory=list)
    title: str | None = Field(default=None, max_length=1000)
    representative_raw: str | None = None
    representative_canonical: str | None = None
    jurisdiction: str | None = None
    publication_date: date | None = None
    judgment: Literal["not_judged", "relevant", "not_relevant", "unsure"] = "not_judged"

    @model_validator(mode="after")
    def identifiers(self):
        if (self.representative_raw is None) != (self.representative_canonical is None):
            raise ValueError("raw and canonical representative identifiers go together")
        if self.representative_raw is not None and \
                self.representative_canonical != canonical_patent_id(self.representative_raw):
            raise ValueError("representative_canonical must be canonical_patent_id(representative_raw)")
        normalize_ipc3(self.ipc3)
        return self


class ScoutReceipt(Contract):
    mode: Literal["replay", "live"]
    corpus_bundle_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    encoder: str = Field(min_length=1)
    encoder_revision: str = Field(min_length=1)
    input_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    output_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    encode_ms: float = Field(ge=0)
    search_ms: float = Field(ge=0)
    llm_calls: int = Field(default=0, ge=0)
    prompt_tokens: int = Field(default=0, ge=0)
    output_tokens: int = Field(default=0, ge=0)
    gpu_seconds: float = Field(default=0, ge=0)
    paid_calls: Literal[0] = 0


class ScoutSession(Contract):
    session_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,80}$")
    brief: ScoutBrief
    split: LaneSplit
    candidates: list[ScoutCandidate]
    receipt: ScoutReceipt

    @model_validator(mode="after")
    def lanes(self):
        own = set(self.brief.own_ipc3)
        seen: set[str] = set()
        for lane, limit in (("own_field", self.split.n_own), ("other_fields", self.split.n_other)):
            rows = [c for c in self.candidates if c.lane == lane]
            if len(rows) > limit:
                raise ValueError(f"{lane} has more candidates than the split allows")
            if [c.rank_in_lane for c in rows] != list(range(1, len(rows) + 1)):
                raise ValueError(f"{lane} ranks must run 1..n in order")
            for c in rows:
                if (lane == "own_field") != bool(own.intersection(c.ipc3)):
                    raise ValueError(f"{c.family_id} is in {lane} but its IPC3 codes say otherwise")
        for c in self.candidates:
            if c.family_id in seen:
                raise ValueError(f"duplicate family {c.family_id}")
            seen.add(c.family_id)
        return self


class TransferRationale(Contract):
    session_id: str = Field(min_length=1)
    family_id: str = Field(min_length=1)
    source_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    model: str = Field(min_length=1)
    model_revision: str = Field(min_length=1)
    prompt_version: str = Field(min_length=1)
    what_it_does: str = Field(min_length=1, max_length=600)
    transferable_mechanism: str = Field(min_length=1, max_length=600)
    quotes: list[QuoteCheck] = Field(min_length=1, max_length=3)
    quote_status: Literal["all_matched", "some_unmatched"]
    label: Literal["literal match is not semantic support"] = LITERAL_MATCH_LABEL
    basis: Literal["system_inference"] = "system_inference"
    decision: Literal["pending", "accepted", "rejected"] = "pending"
    note: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def status(self):
        expected = "all_matched" if all(q.status == "matched" for q in self.quotes) else "some_unmatched"
        if self.quote_status != expected:
            raise ValueError("quote_status must follow the quote checks")
        return self
