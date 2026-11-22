"""P2-T03: one bounded source-relation search action, as a reusable engine operator.

The operator takes the state after a seed retrieval (the exact query requirements, the current candidate pool and the
runtime relation states produced by a coverage check) and performs exactly one bounded action:

1. keep the original query and its requirement spans exactly as given (frozen, fingerprinted before and after);
2. select one unresolved, search-actionable relation by a named, versioned deterministic policy (``POLICY_V1``);
3. issue exactly one global search for it, inside an explicit action budget and an explicit eligibility mask;
4. merge the eligible returned candidates into the pool, recording before/after membership and the new candidates;
5. re-check coverage on the merged pool (one call of the caller's assessor);
6. rerank the merged pool against the ORIGINAL query/requirements only (the reranker never sees the expansion text);
7. emit one evidence-trace event that must pass the owner schema and the semantic checks of ``trace_slice``;
8. refuse any attempt to cite a generated search hypothesis (type gate, registry gate and trace check).

Two forms share this one implementation:

* ``relation_search_step`` -- a pure function over in-memory inputs (precomputed candidate lists, a caller-supplied
  search backend, assessor and reranker). No Workbench store is needed; this is the form a research harness can call.
* ``RelationSearchSlice`` -- the Workbench adapter: a ``TraceSlice`` subclass that runs the real SQLite FTS5 seed and
  expansion searches over a project store, records the run/actions/assessments/trace events in the existing tables and
  calls ``relation_search_step`` for the bounded action.

Claim boundary: this is an engineering mechanism. Synthetic tests exercise its behaviour; nothing here measures or claims
a retrieval-effectiveness gain. The policy below must be frozen (by name, version and fingerprint) in a research protocol
before any research number is computed with it.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
import base64
import json
import math
from pathlib import Path
from typing import Callable, Iterable, Mapping, Sequence

from patent_to_pilot.workbench.core import CoreError, EvidenceCore, ValidationFailed
from patent_to_pilot.workbench.store import dumps, utc_now
from patent_to_pilot.workbench.trace_slice import (CANDIDATE_ID, FIXTURE_DIR, OFFSET_UNIT, RESULT_LIMIT, ROUTE_ID,
                                                   SYNTHETIC_LABEL, HypothesisNotEvidence, SearchHypothesis,
                                                   SourceEvidence, TraceSlice, _TERM, _or_match, _terms, check_event,
                                                   index_manifest_bytes, require_source_evidence, sha256)

RECORD_SCHEMA = "ptp-relation-search-record/1"
STATUSES = ("supported", "contradicted", "unresolved")
TERM_ORIGINS = ("original_requirement", "source_copy", "generated_hypothesis")
RERANK_BASIS = "original_query_and_requirements_only"
CLAIM_BOUNDARY = ("Engineering mechanism only. Before/after membership, new candidates, coverage re-check and the "
                  "original-query rerank are executed and recorded; no retrieval-effectiveness claim follows.")


class BudgetExhausted(CoreError):
    """A retrieval action was requested after the declared action budget was spent."""
    code = "action_budget_exhausted"

    def __init__(self, message: str) -> None:
        super().__init__(message, self.code)


class IneligibleCandidate(ValidationFailed):
    """A candidate outside the declared eligibility mask was offered as pool membership."""
    code = "ineligible_candidate"


def _fp(obj) -> str:
    return sha256(dumps(obj).encode("utf-8"))


# =========================================================================== exact query requirements
@dataclass(frozen=True)
class Requirement:
    """One requirement: an exact, zero-based, half-open code-point span of the original query text."""
    requirement_id: str
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class QueryRequirements:
    """The original query and its requirement spans. Immutable; every span must equal ``text[start:end]``."""
    query_id: str
    text: str
    requirements: tuple[Requirement, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "requirements", tuple(self.requirements))
        if not self.query_id or not self.text:
            raise ValidationFailed("query id and text are required", "query_missing")
        if not self.requirements:
            raise ValidationFailed("at least one requirement span is required", "requirements_missing")
        ids = [r.requirement_id for r in self.requirements]
        if len(set(ids)) != len(ids):
            raise ValidationFailed("duplicate requirement ids", "requirement_duplicate")
        for r in self.requirements:
            if not isinstance(r, Requirement):
                raise ValidationFailed(f"{r!r} is not a Requirement", "requirement_type")
            if not (0 <= r.start < r.end <= len(self.text)) or self.text[r.start:r.end] != r.text:
                raise ValidationFailed(f"requirement {r.requirement_id} is not the exact query span "
                                       f"[{r.start},{r.end})", "requirement_not_bound")

    @classmethod
    def bind(cls, query_id: str, text: str, spans: Sequence[tuple[str, str]]) -> "QueryRequirements":
        """Bind (requirement_id, exact requirement text) pairs to the query. A text that is absent or occurs more than
        once is refused rather than guessed."""
        reqs = []
        for rid, rtext in spans:
            first = text.find(rtext)
            if first < 0 or not rtext or text.find(rtext, first + 1) >= 0:
                raise ValidationFailed(f"requirement {rid} does not occur exactly once in the query",
                                       "requirement_not_bound")
            reqs.append(Requirement(rid, first, first + len(rtext), rtext))
        return cls(query_id, text, tuple(reqs))

    def ordered(self) -> list[Requirement]:
        return sorted(self.requirements, key=lambda r: (r.start, r.end, r.requirement_id))

    def get(self, rid: str) -> Requirement:
        for r in self.requirements:
            if r.requirement_id == rid:
                return r
        raise ValidationFailed(f"unknown requirement {rid}", "requirement_unknown")

    def as_record(self) -> dict:
        return {"query_id": self.query_id, "text": self.text,
                "requirements": [{"requirement_id": r.requirement_id, "start": r.start, "end": r.end, "text": r.text,
                                  "unit": OFFSET_UNIT} for r in self.requirements]}

    def sha256(self) -> str:
        return _fp(self.as_record())


# =========================================================================== eligibility and budget
@dataclass(frozen=True)
class EligibilityMask:
    """Declared candidate eligibility applied to every route (seed and expansion) and re-checked after merging.

    * ``exclude_ids``: individual candidate ids that are never eligible (e.g. the query document itself);
    * ``exclude_groups``: groups that are never eligible (e.g. the query's own family or source); a candidate's group is
      ``group_of(candidate_id)`` (mapping or callable; ``grouping`` names how it is derived);
    * ``date_cutoff``: when set, a candidate is eligible only if its date is strictly before the cutoff; its date is
      ``dates[candidate_id]`` or else ``dates[group]``; a missing date follows the declared ``missing_date`` rule.
    """
    profile_id: str
    exclude_ids: frozenset = frozenset()
    exclude_groups: frozenset = frozenset()
    grouping: str = "none"
    group_of: Mapping[str, str] | Callable[[str], str | None] | None = field(default=None, compare=False, repr=False)
    dates: Mapping[str, str | None] | None = None
    date_cutoff: str | None = None
    missing_date: str = "exclude"

    def __post_init__(self) -> None:
        object.__setattr__(self, "exclude_ids", frozenset(self.exclude_ids))
        object.__setattr__(self, "exclude_groups", frozenset(self.exclude_groups))
        if not self.profile_id:
            raise ValidationFailed("an eligibility profile needs an id", "eligibility_profile")
        if self.missing_date not in ("exclude", "include"):
            raise ValidationFailed("missing_date must be 'exclude' or 'include'", "eligibility_profile")
        if self.exclude_groups and self.group_of is None:
            raise ValidationFailed("exclude_groups needs a group_of mapping", "eligibility_profile")
        try:
            if self.date_cutoff is not None:
                date.fromisoformat(self.date_cutoff)
            for v in (self.dates or {}).values():
                if v is not None:
                    date.fromisoformat(v)
        except ValueError as exc:
            raise ValidationFailed(f"eligibility dates must be ISO YYYY-MM-DD ({exc})", "eligibility_profile") from exc

    def group(self, cid: str) -> str | None:
        if self.group_of is None:
            return None
        return self.group_of(cid) if callable(self.group_of) else self.group_of.get(cid)

    def reason(self, cid: str) -> str | None:
        """None when eligible, else the declared reason for exclusion."""
        if cid in self.exclude_ids:
            return "excluded_id"
        g = self.group(cid)
        if g is not None and g in self.exclude_groups:
            return f"excluded_group:{g}"
        if self.date_cutoff is not None:
            dates = self.dates or {}
            d = dates[cid] if cid in dates else dates.get(g) if g is not None else None
            if d is None:
                return "missing_date" if self.missing_date == "exclude" else None
            if date.fromisoformat(d) >= date.fromisoformat(self.date_cutoff):
                return "date_not_before_cutoff"
        return None

    def describe(self) -> dict:
        return {"profile_id": self.profile_id, "exclude_ids": sorted(self.exclude_ids),
                "exclude_groups": sorted(self.exclude_groups), "grouping": self.grouping,
                "dates": dict(sorted((self.dates or {}).items())), "date_cutoff": self.date_cutoff,
                "date_rule": "eligible iff date < date_cutoff (strictly before)", "missing_date": self.missing_date}

    def fingerprint(self) -> str:
        return _fp(self.describe())

    @property
    def trace_id(self) -> str:
        return f"{self.profile_id}#{self.fingerprint()[:16]}"


class ActionBudget:
    """A count of retrieval actions (seed and expansion searches). Spending past the limit raises."""

    def __init__(self, limit: int) -> None:
        if not isinstance(limit, int) or limit < 0:
            raise ValidationFailed("budget limit must be a non-negative integer", "budget_invalid")
        self.limit = limit
        self.spent: list[str] = []

    @property
    def used(self) -> int:
        return len(self.spent)

    @property
    def remaining(self) -> int:
        return self.limit - self.used

    def consume(self, kind: str) -> int:
        if self.remaining < 1:
            raise BudgetExhausted(f"action budget of {self.limit} is spent ({self.spent}); '{kind}' refused")
        self.spent.append(kind)
        return self.used

    def describe(self) -> dict:
        return {"limit": self.limit, "used": self.used, "spent": list(self.spent)}


# =========================================================================== relation states and the selection policy
@dataclass(frozen=True)
class RelationState:
    """One runtime relation/binding state for a requirement (a fallible search signal, never gold).

    ``from_id`` is the pool candidate that holds the reference; ``reference_text`` is copied verbatim from source
    evidence ``reference_evidence_id``; ``anchor_terms`` are terms of the relation's own requirement; ``actionable`` is
    False for bindings that a global search cannot resolve (e.g. an in-version footnote closure)."""
    relation_key: str
    requirement_id: str
    kind: str
    status: str
    from_id: str | None = None
    reference_text: str | None = None
    reference_evidence_id: str | None = None
    anchor_terms: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    actionable: bool = True
    note: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "anchor_terms", tuple(self.anchor_terms))
        object.__setattr__(self, "evidence_ids", tuple(self.evidence_ids))
        if self.status not in STATUSES:
            raise ValidationFailed(f"{self.relation_key}: status must be one of {STATUSES}", "relation_status")
        if (self.reference_text is None) != (self.reference_evidence_id is None):
            raise ValidationFailed(f"{self.relation_key}: reference text and its evidence id go together",
                                   "relation_reference")

    def as_record(self) -> dict:
        d = asdict(self)
        d["anchor_terms"], d["evidence_ids"] = list(self.anchor_terms), list(self.evidence_ids)
        return d


@dataclass(frozen=True)
class SelectionPolicy:
    """A named, versioned, deterministic relation-selection and query-construction policy."""
    policy_id: str
    version: str
    max_expansion_searches: int
    selection_rule: tuple[str, ...]
    query_rule: tuple[str, ...]
    rerank_rule: tuple[str, ...]

    @property
    def name(self) -> str:
        return f"{self.policy_id}/{self.version}"

    def describe(self) -> dict:
        return {"policy_id": self.policy_id, "version": self.version,
                "max_expansion_searches": self.max_expansion_searches, "selection_rule": list(self.selection_rule),
                "query_rule": list(self.query_rule), "rerank_rule": list(self.rerank_rule)}

    def fingerprint(self) -> str:
        return _fp(self.describe())


POLICY_V1 = SelectionPolicy(
    policy_id="ptp-relsel-first-unresolved",
    version="1.0.0",
    max_expansion_searches=1,
    selection_rule=(
        "S1 eligible: status == 'unresolved' AND actionable AND relation_key not already attempted AND the relation has "
        "search material (reference_text or at least one anchor term).",
        "S2 order eligible relations by the tuple (a) position of the relation's requirement in the query, by "
        "(span start, span end, requirement_id); (b) 0-based rank of from_id in the pool before the action "
        "(len(pool) if absent or None); (c) start offset of reference_evidence_id's span (2**63 if none); "
        "(d) relation_key, lexicographic.",
        "S3 select the first relation. Input order, scores, evaluator labels, randomness and model calls are not "
        "used.",
    ),
    query_rule=(
        "Q1 terms in order: reference_text (origin source_copy, ref = reference_evidence_id); each anchor term "
        "(origin original_requirement; must be a term of the relation's requirement); each generated hypothesis for "
        "the selected relation (origin generated_hypothesis, ref = hypothesis_id).",
        "Q2 duplicates (case-insensitive) keep the first occurrence; a term without a word token is refused.",
        "Q3 submitted text = OR of quoted phrases (trace_slice._or_match); exactly one search, global over the "
        "backend's corpus (not restricted to the pool), fetch depth fetch_limit, then the eligibility mask, then the "
        "first result_limit eligible candidates.",
    ),
    rerank_rule=(
        "R1 the reranker receives RerankRequest(query_id, original query text, exact requirement texts) and the merged "
        "candidate ids; it never receives the expansion query, its terms or any hypothesis text.",
        "R2 order by score descending; candidates without a score follow; ties by position in the merged pool "
        "(before-pool first, then new candidates in returned order).",
    ),
)
# Frozen fingerprint of POLICY_V1.describe(). Any change to the rule text or parameters changes it and is refused at
# run time: a changed policy needs a new version (and a new pin), never a silent edit.
POLICY_V1_SHA256 = "e4ea084cd572e4fdda37838451c9d2838f7af61bc5c68b7cec4468411265629c"
POLICIES = {POLICY_V1.name: POLICY_V1}
PINNED_POLICY_SHA256 = {POLICY_V1.name: POLICY_V1_SHA256}


def _require_known_policy(policy: SelectionPolicy) -> None:
    if POLICIES.get(policy.name) != policy or PINNED_POLICY_SHA256.get(policy.name) != policy.fingerprint():
        raise ValidationFailed(f"unknown, modified or unpinned selection policy {policy.name}", "policy_unknown")


# =========================================================================== typed query material
@dataclass(frozen=True)
class QueryTerm:
    text: str
    origin: str
    ref_id: str | None = None


@dataclass(frozen=True)
class ExpansionQuery:
    """The one expansion query: typed terms with provenance; ``text`` is the string actually submitted."""
    relation_key: str
    terms: tuple[QueryTerm, ...]

    @property
    def phrases(self) -> list[str]:
        return [t.text for t in self.terms]

    @property
    def text(self) -> str:
        return _or_match(self.phrases)

    @property
    def artifact_ids(self) -> list[str]:
        out: list[str] = []
        for t in self.terms:
            if t.ref_id and t.ref_id not in out:
                out.append(t.ref_id)
        return out

    def as_record(self) -> dict:
        return {"relation_key": self.relation_key, "submitted_text": self.text,
                "terms": [asdict(t) for t in self.terms], "query_artifact_ids": self.artifact_ids}


@dataclass(frozen=True)
class RerankRequest:
    """Everything a reranker may see about the information need: the original query and its exact requirements."""
    query_id: str
    query_text: str
    requirement_texts: tuple[str, ...]
    basis: str = RERANK_BASIS

    @classmethod
    def from_requirements(cls, qr: QueryRequirements) -> "RerankRequest":
        return cls(qr.query_id, qr.text, tuple(r.text for r in qr.ordered()))


# =========================================================================== evidence registry (pure form)
class EvidenceRegistry:
    """In-memory source evidence and generated hypotheses for the pure form. Ids are disjoint across the two types;
    ``resolve`` refuses a hypothesis whatever the caller intended."""

    def __init__(self, evidence: Iterable[SourceEvidence] = (), hypotheses: Iterable[SearchHypothesis] = ()) -> None:
        self._ev: dict[str, SourceEvidence] = {}
        self._hyp: dict[str, SearchHypothesis] = {}
        for e in evidence:
            self.add_evidence(e)
        for h in hypotheses:
            self.register_hypothesis(h)

    def add_evidence(self, item) -> SourceEvidence:
        e = require_source_evidence(item)
        if e.evidence_id in self._hyp:
            raise HypothesisNotEvidence(f"{e.evidence_id} already names a generated search hypothesis")
        old = self._ev.get(e.evidence_id)
        if old is not None and old != e:
            raise ValidationFailed(f"{e.evidence_id} already exists with different content", "evidence_conflict")
        self._ev[e.evidence_id] = e
        return e

    def register_hypothesis(self, h: SearchHypothesis) -> SearchHypothesis:
        if not isinstance(h, SearchHypothesis):
            raise ValidationFailed(f"{type(h).__name__} is not a SearchHypothesis", "hypothesis_type")
        if h.hypothesis_id in self._ev:
            raise ValidationFailed(f"{h.hypothesis_id} already names source evidence", "hypothesis_id_clash")
        self.resolve(h.source_evidence_ids)
        self._hyp[h.hypothesis_id] = h
        return h

    def is_hypothesis(self, i: str) -> bool:
        return i in self._hyp

    def resolve(self, ids: Iterable[str]) -> list[SourceEvidence]:
        out = []
        for i in ids:
            if i in self._hyp:
                raise HypothesisNotEvidence(f"{i} is a generated search hypothesis and cannot be cited")
            if i not in self._ev:
                raise ValidationFailed(f"{i} is not recorded source evidence", "unknown_evidence")
            out.append(require_source_evidence(self._ev[i]))
        return out


# =========================================================================== reference in-memory backends (pure form)
def _tokens(text: str) -> list[str]:
    return [t for t in _TERM.findall(text.lower())]


class InMemoryBM25:
    """Deterministic bag-of-terms BM25 (k1=1.2, b=0.75, Lucene idf) over an in-memory {candidate_id: text} corpus.
    A reference backend for synthetic tests and precomputed candidate texts; it is not FTS5 phrase matching."""

    def __init__(self, docs: Mapping[str, str], k1: float = 1.2, b: float = 0.75) -> None:
        self.k1, self.b = k1, b
        self.docs = {d: _tokens(t) for d, t in sorted(docs.items())}
        self.n = len(self.docs)
        self.avgdl = (sum(len(v) for v in self.docs.values()) / self.n) if self.n else 0.0
        self.df: dict[str, int] = {}
        for toks in self.docs.values():
            for t in set(toks):
                self.df[t] = self.df.get(t, 0) + 1

    def scores(self, terms: Iterable[str], ids: Iterable[str] | None = None) -> dict[str, float]:
        qterms = list(dict.fromkeys(t for term in terms for t in _tokens(term)))
        out = {}
        for d in (sorted(ids) if ids is not None else self.docs):
            toks = self.docs.get(d)
            if not toks:
                continue
            s = 0.0
            for t in qterms:
                tf = toks.count(t)
                if not tf:
                    continue
                n = self.df.get(t, 0)
                idf = math.log(1 + (self.n - n + 0.5) / (n + 0.5))
                s += idf * tf * (self.k1 + 1) / (tf + self.k1 * (1 - self.b + self.b * len(toks) / self.avgdl))
            if s > 0:
                out[d] = round(s, 6)
        return out

    def search(self, query: ExpansionQuery, limit: int, eligibility: EligibilityMask | None = None) -> list[tuple]:
        """Global search over the whole in-memory corpus (eligibility is applied by the operator afterwards)."""
        sc = self.scores(query.phrases)
        return sorted(sc.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]


def bm25_reranker(docs: Mapping[str, str]) -> Callable[[RerankRequest, tuple], dict]:
    """Reference reranker: BM25 of the union of the exact requirement-span terms (``trace_slice._terms``) against the
    candidates' texts. It can only see the RerankRequest, i.e. the original information need."""
    idx = InMemoryBM25(docs)

    def rerank(request: RerankRequest, ids: tuple) -> dict:
        terms = _terms(" ".join(request.requirement_texts))
        return idx.scores(terms, ids=[i for i in ids if i in idx.docs])
    return rerank


# =========================================================================== policy implementation
_NO_OFFSET = 2 ** 63


def _validate_states(states: Iterable, qr: QueryRequirements, evidence, where: str) -> tuple[RelationState, ...]:
    states = tuple(states)
    keys = []
    for s in states:
        if not isinstance(s, RelationState):
            raise ValidationFailed(f"{where}: {type(s).__name__} is not a RelationState", "relation_type")
        qr.get(s.requirement_id)
        keys.append(s.relation_key)
        ids = list(s.evidence_ids) + ([s.reference_evidence_id] if s.reference_evidence_id else [])
        resolved = evidence.resolve(ids)          # a hypothesis id raises HypothesisNotEvidence here
        if s.reference_evidence_id is not None and resolved[-1].quote != s.reference_text:
            raise ValidationFailed(f"{where}: {s.relation_key} reference text is not its evidence quote",
                                   "relation_reference")
        req_terms = set(_terms(qr.get(s.requirement_id).text))
        for t in s.anchor_terms:
            if t.lower() not in req_terms:
                raise ValidationFailed(f"{where}: anchor '{t}' of {s.relation_key} is not a term of requirement "
                                       f"{s.requirement_id}", "anchor_not_original")
    if len(set(keys)) != len(keys):
        raise ValidationFailed(f"{where}: duplicate relation keys", "relation_duplicate")
    return states


def select_relation(policy: SelectionPolicy, qr: QueryRequirements, states: Sequence[RelationState],
                    pool_before: Sequence[str], evidence, attempted: Iterable[str] = ()) -> dict:
    """Apply the named policy. Returns {selected, considered (in policy order with sort keys), skipped (with reason)}."""
    _require_known_policy(policy)
    attempted = set(attempted)
    req_pos = {r.requirement_id: i for i, r in enumerate(qr.ordered())}
    pool_pos = {c: i for i, c in enumerate(pool_before)}
    considered, skipped = [], []
    for s in states:
        if s.status != "unresolved":
            skipped.append({"relation_key": s.relation_key, "reason": f"status_{s.status}"})
        elif not s.actionable:
            skipped.append({"relation_key": s.relation_key, "reason": "not_search_actionable"})
        elif s.relation_key in attempted:
            skipped.append({"relation_key": s.relation_key, "reason": "already_attempted"})
        elif not (s.reference_text or s.anchor_terms):
            skipped.append({"relation_key": s.relation_key, "reason": "no_search_material"})
        else:
            off = evidence.resolve([s.reference_evidence_id])[0].start if s.reference_evidence_id else _NO_OFFSET
            key = (req_pos[s.requirement_id], pool_pos.get(s.from_id, len(pool_before)), off, s.relation_key)
            considered.append((key, s))
    considered.sort(key=lambda ks: ks[0])
    skipped.sort(key=lambda d: d["relation_key"])
    return {"selected": considered[0][1] if considered else None,
            "considered": [{"relation_key": s.relation_key, "sort_key": list(k)} for k, s in considered],
            "skipped": skipped}


def build_query(policy: SelectionPolicy, rel: RelationState, qr: QueryRequirements,
                hypotheses: Sequence[SearchHypothesis], evidence) -> ExpansionQuery:
    """Policy Q1-Q3: typed expansion terms with provenance."""
    _require_known_policy(policy)
    raw: list[QueryTerm] = []
    if rel.reference_text:
        (ev,) = evidence.resolve([rel.reference_evidence_id])
        if ev.quote != rel.reference_text:
            raise ValidationFailed("a source-copied term must equal its evidence quote", "source_copy_mismatch")
        raw.append(QueryTerm(rel.reference_text, "source_copy", rel.reference_evidence_id))
    req_terms = set(_terms(qr.get(rel.requirement_id).text))
    for t in rel.anchor_terms:
        if t.lower() not in req_terms:
            raise ValidationFailed(f"anchor '{t}' is not a term of the original requirement", "anchor_not_original")
        raw.append(QueryTerm(t, "original_requirement", None))
    for h in hypotheses:
        if not isinstance(h, SearchHypothesis) or not evidence.is_hypothesis(h.hypothesis_id):
            raise ValidationFailed("generated query material must be a registered SearchHypothesis", "hypothesis_type")
        raw.append(QueryTerm(h.text, "generated_hypothesis", h.hypothesis_id))
    seen, terms = set(), []
    for t in raw:
        if not _TERM.findall(t.text):
            raise ValidationFailed(f"query term {t.text!r} has no word token", "query_term_empty")
        k = " ".join(_TERM.findall(t.text.lower()))
        if k not in seen:
            seen.add(k)
            terms.append(t)
    if not terms:
        raise ValidationFailed("the selected relation produced no query terms", "query_empty")
    return ExpansionQuery(rel.relation_key, tuple(terms))


def _status_of(states: Sequence[RelationState], rid: str) -> str:
    """Requirement-level status from its relations: contradicted > unresolved > supported (no relations: unresolved)."""
    st = {s.status for s in states if s.requirement_id == rid}
    if "contradicted" in st:
        return "contradicted"
    if "unresolved" in st or not st:
        return "unresolved"
    return "supported"


# =========================================================================== the operator (pure form)
def relation_search_step(*, requirements: QueryRequirements, relations: Sequence[RelationState],
                         pool_before: Sequence[str], search: Callable, assess: Callable, rerank: Callable,
                         budget: ActionBudget, eligibility: EligibilityMask, evidence,
                         hypotheses_for: Callable[[RelationState], Sequence[SearchHypothesis]] | None = None,
                         policy: SelectionPolicy = POLICY_V1, result_limit: int = RESULT_LIMIT,
                         fetch_limit: int | None = None, final_k: int | None = None, attempted: Iterable[str] = (),
                         emit: Callable | None = None, action_id: str | None = None) -> dict:
    """One bounded source-relation search action. See the module docstring and the P2-T03 mechanism spec.

    ``search(query: ExpansionQuery, fetch_limit, eligibility) -> [(candidate_id, score), ...]`` is called at most once.
    ``assess(after_ids: tuple) -> [RelationState, ...]`` is called once after merging (coverage re-check).
    ``rerank(request: RerankRequest, after_ids: tuple) -> {candidate_id: score}`` sees only the original need.
    ``emit(record, query, hypotheses) -> event`` builds the evidence-trace event; it must pass ``check_event``.
    ``evidence`` resolves source evidence ids, refuses hypothesis ids and registers hypotheses."""
    if not isinstance(requirements, QueryRequirements):
        raise ValidationFailed("requirements must be a QueryRequirements", "requirements_type")
    if not isinstance(budget, ActionBudget) or not isinstance(eligibility, EligibilityMask):
        raise ValidationFailed("budget and eligibility must be declared explicitly", "operator_inputs")
    if result_limit < 1 or (fetch_limit is not None and fetch_limit < result_limit):
        raise ValidationFailed("need 1 <= result_limit <= fetch_limit", "operator_inputs")
    req_fp = requirements.sha256()
    pool_before = list(pool_before)
    if len(set(pool_before)) != len(pool_before):
        raise ValidationFailed("pool before the action has duplicate ids", "pool_duplicate")
    bad = [(c, eligibility.reason(c)) for c in pool_before if eligibility.reason(c)]
    if bad:
        raise IneligibleCandidate(f"pool before the action contains ineligible candidates {bad}; apply the same mask "
                                  "to the seed route", IneligibleCandidate.code)
    states_before = _validate_states(relations, requirements, evidence, "coverage_before")
    sel = select_relation(policy, requirements, states_before, pool_before, evidence, attempted)
    action_id = action_id or f"{policy.policy_id}-v{policy.version}:expansion-1"
    record: dict = {
        "record_schema": RECORD_SCHEMA, "claim_boundary": CLAIM_BOUNDARY, "action_id": action_id,
        "policy": {**policy.describe(), "name": policy.name, "sha256": policy.fingerprint()},
        "requirements": requirements.as_record(), "requirements_sha256": req_fp,
        "eligibility": {**eligibility.describe(), "sha256": eligibility.fingerprint(), "trace_id": eligibility.trace_id},
        "budget_before": budget.describe(), "result_limit": result_limit,
        "fetch_limit": fetch_limit or result_limit,
        "selection": {"selected_relation_key": sel["selected"].relation_key if sel["selected"] else None,
                      "considered": sel["considered"], "skipped": sel["skipped"]},
        "coverage": {"before": [s.as_record() for s in sorted(states_before, key=lambda s: s.relation_key)]},
        "search_calls": 0, "query": None, "search": None, "candidate_delta": None, "rerank": None,
        "trace_event": None}
    if sel["selected"] is None:
        record.update(outcome="no_unresolved_relation", budget_after=budget.describe())
        return record
    if budget.remaining < 1:
        record.update(outcome="budget_exhausted", budget_after=budget.describe())
        return record
    rel: RelationState = sel["selected"]
    hyps = tuple(hypotheses_for(rel)) if hypotheses_for else ()
    for h in hyps:
        evidence.register_hypothesis(h)
    query = build_query(policy, rel, requirements, hyps, evidence)
    record["query"] = query.as_record()
    # ---- the single expansion search (the only call site of ``search`` in this module)
    budget.consume("relation_search")
    record["search_calls"] = 1
    raw = list(search(query, fetch_limit or result_limit, eligibility))
    seen, ranked = set(), []
    for item in raw:
        cid, score = item[0], (item[1] if len(item) > 1 else None)
        if not isinstance(cid, str) or not cid:
            raise ValidationFailed("search backend returned a non-string candidate id", "backend_output")
        if cid not in seen:
            seen.add(cid)
            ranked.append((cid, score))
    if len(ranked) > (fetch_limit or result_limit):
        raise ValidationFailed("search backend returned more candidates than requested", "backend_output")
    excluded = [{"candidate_id": c, "reason": eligibility.reason(c)} for c, _ in ranked if eligibility.reason(c)]
    returned = [c for c, _ in ranked if not eligibility.reason(c)][:result_limit]
    before = list(pool_before)
    after = before + [c for c in returned if c not in before]
    new = [c for c in returned if c not in before]
    if any(eligibility.reason(c) for c in after):   # re-check after merging
        raise IneligibleCandidate("merged pool contains an ineligible candidate", IneligibleCandidate.code)
    record["search"] = {"backend_ranked": [{"candidate_id": c, "score": s} for c, s in ranked],
                        "excluded_ineligible": excluded, "eligible_returned": returned}
    record["candidate_delta"] = {"before_ids": before, "returned_ids": returned, "after_ids": after, "new_ids": new}
    # ---- coverage re-check on the merged pool
    states_after = _validate_states(assess(tuple(after)), requirements, evidence, "coverage_after")
    by_key = {s.relation_key: s for s in states_after}
    record["coverage"].update(
        after=[s.as_record() for s in sorted(states_after, key=lambda s: s.relation_key)],
        selected_before=rel.status,
        selected_after=by_key[rel.relation_key].status if rel.relation_key in by_key else "absent_after",
        requirement_before=_status_of(states_before, rel.requirement_id),
        requirement_after=_status_of(states_after, rel.requirement_id))
    # ---- rerank against the original need only
    request = RerankRequest.from_requirements(requirements)
    scores = dict(rerank(request, tuple(after)) or {})
    for c, s in scores.items():
        if c not in after:
            raise ValidationFailed(f"reranker scored {c}, which is not in the merged pool", "rerank_output")
        if not isinstance(s, (int, float)) or isinstance(s, bool) or not math.isfinite(s):
            raise ValidationFailed(f"reranker score for {c} is not a finite number", "rerank_output")
    pos = {c: i for i, c in enumerate(after)}
    order = sorted(after, key=lambda c: (0, -scores[c], pos[c]) if c in scores else (1, 0.0, pos[c]))
    ranking = [{"candidate_id": c, "rerank_position": i + 1, "pool_position": pos[c] + 1,
                "score": scores.get(c), "is_new": c in new} for i, c in enumerate(order)]
    record["rerank"] = {"basis": request.basis,
                        "request": {**asdict(request), "requirement_texts": list(request.requirement_texts)},
                        "ranking": ranking,
                        "final_k": final_k, "final_ids": order[:final_k] if final_k else order}
    if requirements.sha256() != req_fp:
        raise ValidationFailed("query requirements changed during the action", "requirements_mutated")
    record.update(outcome="searched", budget_after=budget.describe())
    if emit is not None:
        event = emit(record, query, hyps)
        chk = check_event(event)
        if chk["schema_errors"] or chk["semantic_errors"]:
            raise ValidationFailed(f"emitted trace failed its checks: {chk}", "trace_invalid")
        if event["candidate_delta"]["after_ids"] != after or event["candidate_delta"]["new_ids"] != new \
                or event["action"]["query_text"] != query.text or event["original_query"]["text"] != requirements.text:
            raise ValidationFailed("emitted trace does not match the executed action", "trace_mismatch")
        record["trace_event"] = event
    return record


# =========================================================================== pure trace emitter
@dataclass(frozen=True)
class TraceSource:
    source_id: str
    version_id: str
    media_type: str
    raw: bytes
    text: str
    parser_id: str
    normalization_id: str
    pages: tuple = ()
    group_id: str | None = None


@dataclass(frozen=True)
class TraceNode:
    node_id: str
    source_id: str
    version_id: str
    kind: str
    start: int
    end: int
    regions: tuple = ()


@dataclass(frozen=True)
class TraceContext:
    """What a caller without a Workbench store supplies so the pure operator can emit a schema-valid event."""
    run_id: str
    mode: str                    # "runtime" or "synthetic_demo"
    index: dict
    identity_unit: str           # "node", "document" or "family"
    sources: tuple
    nodes: tuple
    assessor_id: str
    route_id: str
    event_time: str | None = None
    cost: dict | None = None


def make_index_identity(index_id: str, corpus_revision: str, normalization_id: str, chunker_id: str,
                        lexical_config: dict | None = None, encoder: dict | None = None) -> dict:
    idx = {"corpus_revision": corpus_revision, "encoder": encoder, "lexical_config": lexical_config,
           "normalization_id": normalization_id, "chunker_id": chunker_id}
    return {"index_id": index_id, "manifest_sha256": sha256(index_manifest_bytes(idx)), **idx}


def trace_emitter(ctx: TraceContext, evidence: EvidenceRegistry) -> Callable:
    """Build ``emit`` for the pure form: one ``structural_expansion`` event with before/after requirement assessments."""
    def emit(record: dict, query: ExpansionQuery, hyps: Sequence[SearchHypothesis]) -> dict:
        qr = record["requirements"]
        sel_key = record["selection"]["selected_relation_key"]
        before = {s["relation_key"]: s for s in record["coverage"]["before"]}
        rid = before[sel_key]["requirement_id"]
        req = next(r for r in qr["requirements"] if r["requirement_id"] == rid)

        def ev_of(states):
            out = []
            for s in states:
                if s["requirement_id"] == rid:
                    out += [e for e in s["evidence_ids"] if e not in out]
            return out
        cov = record["coverage"]
        a_before = {"assessment_id": f"asm:{record['action_id']}:before", "status": cov["requirement_before"],
                    "evidence_ids": ev_of(cov["before"]), "timing": "before_action"}
        a_after = {"assessment_id": f"asm:{record['action_id']}:after", "status": cov["requirement_after"],
                   "evidence_ids": ev_of(cov["after"]), "timing": "after_action"}
        ev_ids: list[str] = []
        for i in a_before["evidence_ids"] + a_after["evidence_ids"] + [t.ref_id for t in query.terms
                                                                         if t.origin == "source_copy"] \
                + [e for h in hyps for e in h.source_evidence_ids]:
            if i not in ev_ids:
                ev_ids.append(i)
        evs = evidence.resolve(ev_ids)
        nodes = {n.node_id: n for n in ctx.nodes}
        delta = record["candidate_delta"]
        used = {e.node_id for e in evs}
        if ctx.identity_unit == "node":
            used |= set(delta["before_ids"]) | set(delta["returned_ids"])
        missing = sorted(used - set(nodes))
        if missing:
            raise ValidationFailed(f"trace context lacks nodes {missing}", "trace_context")
        versions = sorted({(nodes[n].source_id, nodes[n].version_id) for n in used})
        srcs = {(s.source_id, s.version_id): s for s in ctx.sources}
        sources = []
        for key in versions:
            s = srcs[key]
            vk = f"{s.source_id}@{s.version_id}"
            d = {"source_id": s.source_id, "version_id": vk,
                 "original_artifact": {"media_type": s.media_type, "storage_ref": f"memory:{vk}",
                                       "sha256": sha256(s.raw),
                                       "content_base64": base64.b64encode(s.raw).decode("ascii")},
                 "canonical_text": {"storage_ref": f"memory:canonical/{s.source_id}@{s.version_id}",
                                    "sha256": sha256(s.text.encode("utf-8")), "normalization_id": s.normalization_id,
                                    "text": s.text},
                 "pages": list(s.pages), "parser_id": s.parser_id}
            if s.group_id:
                d["group_id"] = s.group_id
            sources.append(d)
        node_out = [{"node_id": n.node_id, "source_version_id": f"{n.source_id}@{n.version_id}", "kind": n.kind,
                     "span": {"start": n.start, "end": n.end, "unit": OFFSET_UNIT}, "regions": list(n.regions)}
                    for n in sorted((nodes[x] for x in used), key=lambda n: (n.source_id, n.version_id, n.start))]
        span = {"start": req["start"], "end": req["end"], "unit": OFFSET_UNIT}
        return {
            "schema_version": "ptp-evidence-trace/1", "trace_id": f"trace:{ctx.run_id}:{record['action_id']}",
            "run_id": ctx.run_id, "mode": ctx.mode, "event_time": ctx.event_time or utc_now(),
            "original_query": {"query_id": qr["query_id"], "text": qr["text"]},
            "action": {"action_id": record["action_id"], "kind": "structural_expansion", "query_text": query.text,
                       "query_artifact_ids": query.artifact_ids, "selected_assessment_id": a_before["assessment_id"],
                       "route_id": ctx.route_id, "result_limit": record["result_limit"],
                       "eligibility_profile_id": record["eligibility"]["trace_id"]},
            "index": ctx.index, "sources": sources, "nodes": node_out, "relations": [],
            "evidence": [e.as_trace() for e in evs], "hypotheses": [h.as_trace() for h in hyps],
            "candidate_delta": {"identity_unit": ctx.identity_unit, **{k: list(delta[k]) for k in
                                                                       ("before_ids", "returned_ids", "after_ids",
                                                                        "new_ids")}},
            "runtime_assessments": [{"assessment_id": a["assessment_id"], "requirement_span": span,
                                     "status": a["status"], "evidence_ids": a["evidence_ids"],
                                     "assessor_id": ctx.assessor_id, "basis": "runtime_not_gold", "timing": a["timing"]}
                                    for a in (a_before, a_after)],
            "cost": ctx.cost or {"currency": "USD", "estimate_usd": 0, "provider_reported_usd": None,
                                 "invoiced_usd": None, "invoice_id": None, "state": "not_applicable"}}
    return emit


# =========================================================================== Workbench adapter
PROJECT_ID = "synthetic-p2-t03-relation-search"
WORKBENCH_FETCH_LIMIT = 50
WORKBENCH_BUDGET = 2          # one seed search + one relation search


def workbench_mask(profile_id: str = "synthetic-packet-current-versions-only", exclude_sources: Iterable[str] = (),
                   source_dates: Mapping[str, str | None] | None = None, date_cutoff: str | None = None,
                   missing_date: str = "exclude") -> EligibilityMask:
    """An eligibility mask over Workbench node ids (``source@version#anchor``), grouped by source id."""
    return EligibilityMask(profile_id=profile_id, exclude_groups=frozenset(exclude_sources), grouping="source_id",
                           group_of=lambda nid: nid.split("@", 1)[0], dates=dict(source_dates or {}),
                           date_cutoff=date_cutoff, missing_date=missing_date)


class _StoreEvidence:
    """Evidence registry backed by the Workbench store (the same gates as ``TraceSlice.resolve_evidence``)."""

    def __init__(self, sl: TraceSlice) -> None:
        self.sl = sl

    def resolve(self, ids: Iterable[str]) -> list[SourceEvidence]:
        return self.sl.resolve_evidence(list(ids))

    def is_hypothesis(self, i: str) -> bool:
        with self.sl.store.read() as con:
            return con.execute("SELECT 1 FROM search_hypotheses WHERE project_id=? AND hypothesis_id=?",
                               (self.sl.pid, i)).fetchone() is not None

    def register_hypothesis(self, h: SearchHypothesis) -> SearchHypothesis:
        return self.sl.add_hypothesis(h)


class RelationSearchSlice(TraceSlice):
    """The P0-T06 synthetic packet driven by the general operator: seed search -> coverage -> one relation search
    (``relation_search_step``) -> coverage re-check -> original-query rerank. ``TraceSlice`` itself is unchanged."""

    def __init__(self, core: EvidenceCore, fixture_dir: Path = FIXTURE_DIR, project_id: str = PROJECT_ID) -> None:
        super().__init__(core, fixture_dir, project_id)

    def _eligible(self, hits: list[dict], mask: EligibilityMask) -> tuple[list[str], list[dict]]:
        excluded = [{"candidate_id": h["node_id"], "reason": mask.reason(h["node_id"])} for h in hits
                    if mask.reason(h["node_id"])]
        return [h["node_id"] for h in hits if not mask.reason(h["node_id"])][:RESULT_LIMIT], excluded

    def _states(self, unresolved: list[dict], relations: list[dict], seed_nodes: list[str]) -> list[RelationState]:
        """Map the deterministic reference-coverage assessor's output to relation states. Annex references are
        cross-document (search-actionable); footnote markers bind by in-version closure (not search-actionable)."""
        nodes = self.nodes()
        req = self.requirement()
        rterms = _terms(req["text"])

        def anchors(frm: str) -> tuple[str, ...]:
            other = {t for n in seed_nodes if n != frm for t in _terms(nodes[n]["quote"])}
            own = _terms(nodes[frm]["quote"]) if frm in nodes else []
            return tuple(t for t in rterms if t in own and t not in other)
        out: dict[str, RelationState] = {}
        for u in unresolved:
            kind = "cross_document_reference" if u["kind"] == "annex" else "in_version_footnote"
            key = f"{u['kind']}-reference:{u['evidence_id']}"
            out[key] = RelationState(key, req["requirement_id"], kind, "unresolved", u["from_node_id"], u["reference"],
                                     u["evidence_id"], anchors(u["from_node_id"]), (u["evidence_id"],),
                                     actionable=(u["kind"] == "annex"), note=u["reason"])
        for r in relations:
            ev = r["provenance"]["evidence_ids"]
            if r["kind"] == "incorporates":
                key, ref, frm, kind = f"annex-reference:{ev[0]}", ev[0], r["from_node_id"], "cross_document_reference"
            elif r["kind"] == "qualifies":
                key, ref, frm, kind = f"footnote-reference:{ev[1]}", ev[1], r["to_node_id"], "in_version_footnote"
            else:
                continue
            (rev,) = self.resolve_evidence([ref])
            out[key] = RelationState(key, req["requirement_id"], kind, "supported", frm, rev.quote, ref, anchors(frm),
                                     tuple(ev), actionable=(kind == "cross_document_reference"))
        return [out[k] for k in sorted(out)]

    def run_relation_search(self, eligibility: EligibilityMask | None = None, budget: ActionBudget | None = None,
                            policy: SelectionPolicy = POLICY_V1) -> dict:
        mask = eligibility or workbench_mask()
        budget = budget if budget is not None else ActionBudget(WORKBENCH_BUDGET)
        self._begin_run("relation_search", policy.name)
        try:
            res = self._relation_pipeline(mask, budget, policy)
        except Exception as exc:
            self.core._finish_run(self.run_id, "failed", f"error:{type(exc).__name__}", {})
            raise
        self.core._finish_run(self.run_id, "completed", f"relation_search_{res['record']['outcome']}",
                              {"search_actions": budget.used, "paid_model_calls": 0, "remote_calls": 0,
                               "data_origin": "synthetic_demo", "policy": policy.name})
        self._mark_current(res["relations"])
        self.state = res
        return res

    def _relation_pipeline(self, mask: EligibilityMask, budget: ActionBudget, policy: SelectionPolicy) -> dict:
        req = self.requirement()
        rid = req["requirement_id"]
        qr = QueryRequirements(req["query_id"], req["query_text"],
                               (Requirement(rid, req["start_char"], req["end_char"], req["text"]),))
        # ---- seed: the requirement's own terms, same eligibility mask as the expansion route
        seed_match = _or_match(_terms(req["text"]))
        budget.consume("seed_search")
        self.seq += 1
        seq, t0, index = self.seq, utc_now(), self._index_identity()
        hits = self.search(seed_match, WORKBENCH_FETCH_LIMIT)
        seed_nodes, seed_excluded = self._eligible(hits, mask)
        self.core._action(self.run_id, seq, "trace_search", CANDIDATE_ID, rid,
                          {"trace_id": f"trace:{self.run_id}:{seq}", "action_id": "seed-1", "kind": "seed_search",
                           "fts_match": seed_match, "result_limit": RESULT_LIMIT, "fetch_limit": WORKBENCH_FETCH_LIMIT,
                           "hits": hits, "excluded_ineligible": seed_excluded, "before_ids": [],
                           "new_ids": seed_nodes, "eligibility": mask.trace_id, "policy": policy.name,
                           "corpus_revision": index["corpus_revision"], "data_origin": "synthetic_demo"}, started=t0)
        a1, rel1, unresolved = self.assess(seed_nodes, list(seed_nodes), "seed")
        seed_event = None
        if seed_nodes:
            seed_event = self._event(action_id="seed-1", kind="seed_search", match=seed_match, artifact_ids=[],
                                     selected=None, before=[], returned=seed_nodes,
                                     assessments=[(a1, "after_action")], relations=rel1, hypotheses=[], index=index,
                                     event_time=t0, seq=seq, eligibility_profile_id=mask.trace_id)
        # An empty eligible seed has no source node to show, and the event schema requires at least one source and one
        # node, so no trace event is emitted for it; the action itself is still recorded in the actions table above.
        states_before = self._states(unresolved, rel1, seed_nodes)
        box: dict = {}

        def search(query: ExpansionQuery, limit: int, _mask: EligibilityMask) -> list[tuple]:
            self.seq += 1
            box.update(seq=self.seq, t=utc_now(), index=self._index_identity())
            box["hits"] = self.search(query.text, limit)
            return [(h["node_id"], -h["bm25"]) for h in box["hits"]]

        def assess(after: tuple) -> list[RelationState]:
            a2, rel2, un2 = self.assess(seed_nodes, list(after), "expansion")
            box.update(a2=a2, rel2=rel2, un2=un2)
            return self._states(un2, rel2, seed_nodes)

        def rerank(request: RerankRequest, ids: tuple) -> dict:
            match = _or_match(_terms(" ".join(request.requirement_texts)))
            with self.store.read() as con:
                rows = self.core._lexical(con, self.pid, CANDIDATE_ID, "", 10_000, match=match)
            sc = {f"{h['source_id']}@{h['version_id']}#{h['passage_id']}": -h["score"] for h in rows}
            box["rerank_match"] = match
            return {i: sc[i] for i in ids if i in sc}

        def hypotheses_for(rel: RelationState) -> list[SearchHypothesis]:
            gen = self.packet["hypothesis_generator"]
            gen_sha = sha256(dumps(gen).encode("utf-8"))
            from_ev = self.evidence(rel.from_id).evidence_id
            return [SearchHypothesis(f"hyp:{self.run_id}:{t}->{syn}", syn, gen["generator_id"], gen_sha, (from_ev,))
                    for t in rel.anchor_terms for syn in gen["synonyms"].get(t, [])]

        def emit(record: dict, query: ExpansionQuery, hyps: Sequence[SearchHypothesis]) -> dict:
            d = record["candidate_delta"]
            self.core._action(self.run_id, box["seq"], "trace_search", CANDIDATE_ID, rid,
                              {"trace_id": f"trace:{self.run_id}:{box['seq']}", "action_id": record["action_id"],
                               "kind": "structural_expansion", "policy": record["policy"]["name"],
                               "policy_sha256": record["policy"]["sha256"],
                               "selected_relation_key": record["selection"]["selected_relation_key"],
                               "fts_match": query.text, "query_terms": record["query"]["terms"],
                               "result_limit": RESULT_LIMIT, "fetch_limit": WORKBENCH_FETCH_LIMIT, "hits": box["hits"],
                               "excluded_ineligible": record["search"]["excluded_ineligible"],
                               "before_ids": d["before_ids"], "new_ids": d["new_ids"], "eligibility": mask.trace_id,
                               "corpus_revision": box["index"]["corpus_revision"], "data_origin": "synthetic_demo"},
                              started=box["t"])
            return self._event(action_id=record["action_id"], kind="structural_expansion", match=query.text,
                               artifact_ids=query.artifact_ids, selected=a1["assessment_id"], before=d["before_ids"],
                               returned=d["returned_ids"],
                               assessments=[(a1, "before_action"), (box["a2"], "after_action")],
                               relations=box["rel2"], hypotheses=list(hyps), index=box["index"], event_time=box["t"],
                               seq=box["seq"], eligibility_profile_id=mask.trace_id)

        record = relation_search_step(
            requirements=qr, relations=states_before, pool_before=seed_nodes, search=search, assess=assess,
            rerank=rerank, budget=budget, eligibility=mask, evidence=_StoreEvidence(self),
            hypotheses_for=hypotheses_for, policy=policy, result_limit=RESULT_LIMIT,
            fetch_limit=WORKBENCH_FETCH_LIMIT, emit=emit)
        out = {"label": SYNTHETIC_LABEL, "record": record, "seed_event": seed_event, "seed_nodes": seed_nodes,
               "assessment_before": a1, "states_before": states_before, "expansion_event": record["trace_event"],
               "pool": list(seed_nodes), "assessment": a1, "relations": rel1, "route_id": ROUTE_ID}
        if record["outcome"] == "searched":
            self.seq += 1
            self.core._action(self.run_id, self.seq, "trace_rerank", CANDIDATE_ID, rid,
                              {"basis": record["rerank"]["basis"], "fts_match": box["rerank_match"],
                               "ranking": record["rerank"]["ranking"], "policy": policy.name,
                               "data_origin": "synthetic_demo"})
            out.update(pool=record["candidate_delta"]["after_ids"], assessment=box["a2"], relations=box["rel2"],
                       unresolved_after=box["un2"], final_ids=record["rerank"]["final_ids"])
        return out


def _check_pins() -> None:  # pragma: no cover - development aid: prints the fingerprint to pin
    print(json.dumps({"policy": POLICY_V1.name, "sha256": POLICY_V1.fingerprint()}))


if __name__ == "__main__":  # pragma: no cover
    _check_pins()
