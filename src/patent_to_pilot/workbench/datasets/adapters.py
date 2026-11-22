"""Runtime adapters: native dataset rows -> small typed engine records (stdlib only).

Structural guarantees:
* Each native row is first projected onto the registry's ``runtime_fields`` allowlist (plus withheld
  fields the caller explicitly releases). Evaluator and dropped fields never pass the projection.
* Asking for an evaluator or dropped field (``include=``) raises ``EvaluatorFieldRequested``.
* Evaluator-only configs (qrels, relations, gold sections) cannot be adapted here, except the
  NitiBench+ gold sections under the explicitly named oracle setting.
* Stored text is never normalized, stripped or re-encoded; missing identifiers stay missing.
This module does not import the evaluator-side reader.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .registry import get_config, get_dataset, load_registry

DAPFAM = "datalyes/DAPFAM_patent"
GAZETTE = "VISAI-AI/thai-gazette-evidence-retrieval"
NITIBENCH_PLUS = "VISAI-AI/nitibench-plus"
NITIBENCH = "VISAI-AI/nitibench"
NITIBENCH_STATUTE = "VISAI-AI/nitibench-statute"


class EvaluatorFieldRequested(PermissionError):
    """A runtime caller asked for an evaluator-only, withheld or dropped field."""


class MissingIdentifier(ValueError):
    """A native row lacks the identifier an engine record needs; no identifier is fabricated."""


@dataclass(frozen=True)
class SourceRecord:
    dataset_id: str
    source_id: str | None
    version_id: str | None
    title: str | None
    text: str
    locator: str
    language: str
    valid_from: str | None = None
    valid_to: str | None = None
    observed_at: str | None = None
    attributes: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class RequestRecord:
    dataset_id: str
    request_id: str
    text: str
    as_of: str | None = None
    context: str | None = None
    attributes: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class Span:
    """Half-open span in Unicode code points (Python ``str`` indices), never bytes."""
    source_id: str
    start: int
    end: int

    def slice(self, text: str) -> str:
        if not (0 <= self.start <= self.end <= len(text)):
            raise ValueError(f"span [{self.start}, {self.end}) outside text of {len(text)} code points")
        return text[self.start:self.end]

    def utf8_byte_range(self, text: str) -> tuple[int, int]:
        self.slice(text)
        return len(text[:self.start].encode("utf-8")), len(text[:self.end].encode("utf-8"))


def _freeze(value):
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze(v)) for k, v in value.items()))
    return value


class _RuntimeAdapter:
    dataset_id = ""

    def __init__(self, registry: dict | None = None):
        self._registry = registry or load_registry()
        self._ds = get_dataset(self.dataset_id, self._registry)
        self.revision = self._ds.get("revision")
        self.language = self._ds.get("language", "und")

    def _config(self, config: str) -> dict:
        return get_config(self.dataset_id, config, self._registry)

    def _project(self, row: dict, config: str, include: Iterable[str] = (), release_withheld: Iterable[str] = ()) -> dict:
        cfg = self._config(config)
        if cfg.get("evaluator_only"):
            raise EvaluatorFieldRequested(f"{self.dataset_id}:{config} is evaluator-only; use the evaluator-side reader")
        runtime = set(cfg.get("runtime_fields", []))
        withheld = set(cfg.get("withheld_fields", []))
        # Evaluator/dropped fields of ANY config of this dataset are blocked (e.g. Gazette evidence_text
        # asked for on a query), except identifiers that this config declares as runtime.
        blocked = {f for c in self._ds["native_configs"] for f in c.get("evaluator_fields", []) + c.get("dropped_fields", [])}
        blocked -= runtime
        released = set(release_withheld)
        bad_release = released - withheld
        if bad_release:
            raise EvaluatorFieldRequested(f"cannot release non-withheld fields {sorted(bad_release)}")
        for name in include:
            if name in blocked:
                raise EvaluatorFieldRequested(f"{name!r} is evaluator-only or dropped in {self.dataset_id}:{config}")
            if name in withheld and name not in released:
                raise EvaluatorFieldRequested(f"{name!r} is withheld from runtime by default; release it explicitly (predeclared)")
            if name not in runtime and name not in withheld:
                raise KeyError(f"{name!r} is not a declared runtime field of {self.dataset_id}:{config}")
        allowed = runtime | released
        return {k: v for k, v in row.items() if k in allowed}

    @staticmethod
    def _attrs(projected: dict, include: Iterable[str]) -> tuple:
        return tuple((name, _freeze(projected.get(name))) for name in include)


class DapfamAdapter(_RuntimeAdapter):
    """Patent family -> SourceRecord / RequestRecord with a TA, TAC or FULL text view."""
    dataset_id = DAPFAM

    def view_text(self, row: dict, view: str) -> str:
        views = self._ds["text_views"]
        if view not in views:
            raise ValueError(f"unknown DAPFAM view {view!r}; declared: {sorted(views)}")
        # Same join as B53 tac(): non-empty fields separated by a newline; components are not altered.
        return "\n".join(row.get(f) for f in views[view] if row.get(f))

    def _id(self, row: dict, key: str) -> str:
        value = row.get(key)
        if value in (None, ""):
            raise MissingIdentifier(f"DAPFAM row has no {key}")
        return str(value)

    def source_from_corpus(self, row: dict, *, view: str | None = None, observed_at: str | None = None,
                           include: Iterable[str] = ()) -> SourceRecord:
        include = tuple(include)
        view = view or self._ds["default_corpus_view"]
        p = self._project(row, "corpus", include)
        sid = self._id(p, "relevant_id")
        return SourceRecord(self.dataset_id, sid, self.revision, p.get("title_en"), self.view_text(p, view),
                            f"{self.dataset_id}@{self.revision}:corpus/{sid}#view={view}", self.language,
                            None, None, observed_at, self._attrs(p, include))

    def request_from_query(self, row: dict, *, view: str | None = None, include: Iterable[str] = ()) -> RequestRecord:
        include = tuple(include)
        view = view or self._ds["default_query_view"]
        p = self._project(row, "queries", include)
        return RequestRecord(self.dataset_id, self._id(p, "query_id"), self.view_text(p, view), None, None,
                             self._attrs(p, include))


class GazetteAdapter(_RuntimeAdapter):
    """Gazette notice -> SourceRecord (verbatim Thai text, code-point spans); question -> RequestRecord."""
    dataset_id = GAZETTE

    def source_from_corpus(self, row: dict, *, observed_at: str | None = None, include: Iterable[str] = ()) -> SourceRecord:
        include = tuple(include)
        p = self._project(row, "corpus", include)
        sid = p.get("_id")
        if sid in (None, ""):
            raise MissingIdentifier("Gazette notice has no _id")
        text = p.get("text")
        if not isinstance(text, str):
            raise ValueError(f"Gazette notice {sid} has no text")
        return SourceRecord(self.dataset_id, str(sid), self.revision, p.get("title"), text,
                            f"{self.dataset_id}@{self.revision}:corpus/{sid}", self.language,
                            None, None, observed_at, self._attrs(p, include))

    def request_from_query(self, row: dict, *, include: Iterable[str] = (), release_withheld: Iterable[str] = ()) -> RequestRecord:
        include = tuple(include)
        p = self._project(row, "queries", include, release_withheld)
        rid = p.get("_id")
        if rid in (None, ""):
            raise MissingIdentifier("Gazette question has no _id")
        return RequestRecord(self.dataset_id, str(rid), p.get("text"), None, None, self._attrs(p, include))


class NitiBenchPlusAdapter(_RuntimeAdapter):
    """Case + sub-questions -> RequestRecords (as_of = decision date); gold section -> versioned SourceRecord
    only under the named oracle setting. Field names come from the registry ``field_map``."""
    dataset_id = NITIBENCH_PLUS

    def __init__(self, registry: dict | None = None):
        super().__init__(registry)
        self.fm = dict(self._ds["field_map"])

    def requests_from_case(self, row: dict, *, include: Iterable[str] = (), release_withheld: Iterable[str] = ()) -> list[RequestRecord]:
        include = tuple(include)
        release_withheld = tuple(release_withheld)
        case = self._project(row, "validation_split", include, release_withheld)
        case_id = case.get(self.fm["case_id"])
        if case_id in (None, ""):
            raise MissingIdentifier("NitiBench+ case has no identifier")
        out = []
        subs = case.get(self.fm["sub_questions"]) or []
        for i, sub in enumerate(subs):
            sp = self._project(sub, "validation_split", (), release_withheld)
            native_sub_id = sp.get(self.fm["case_id"])
            if native_sub_id not in (None, ""):
                rid, kind = f"{case_id}/{native_sub_id}", "native"
            else:
                rid, kind = f"{case_id}/{self.fm['sub_questions']}[{i}]", "positional_locator"
            attrs = self._attrs(case, include) + (("request_id_kind", kind),)
            attrs += tuple((n, sp.get(n)) for n in release_withheld if n in sp)
            out.append(RequestRecord(self.dataset_id, rid, sp.get(self.fm["question"]),
                                     case.get(self.fm["decision_date"]), case.get("fact_pattern"), attrs))
        return out

    def source_from_gold_section(self, row: dict, *, setting: str, observed_at: str | None = None) -> SourceRecord:
        cfg = self._config("gold_sections")
        if setting != cfg.get("oracle_runtime_setting"):
            raise EvaluatorFieldRequested("gold sections are oracle evidence; only the named setting "
                                          f"{cfg.get('oracle_runtime_setting')!r} may pass them to runtime")
        dropped = set(cfg.get("dropped_fields", []))
        r = {k: v for k, v in row.items() if k not in dropped}
        version = r.get("version_uri")
        if version in (None, ""):
            raise MissingIdentifier("gold section has no version_uri (join key)")
        text = r.get(self.fm["section_text"])
        if not isinstance(text, str):
            raise ValueError(f"gold section {version} has no text field {self.fm['section_text']!r}")
        attrs = (("law", r.get(self.fm["law"])), ("section", r.get(self.fm["section"])), ("setting", setting))
        return SourceRecord(self.dataset_id, r.get("current_uri"), version, None, text,
                            f"{self.dataset_id}@{self.revision}:gold_sections/{version}", self.language,
                            r.get("valid_from"), r.get("valid_to"), observed_at, attrs)


class NitiBenchAdapter(_RuntimeAdapter):
    """Original NitiBench (public CCL/Tax TEST sets, P3-T01) question -> RequestRecord.

    Native rows carry no identifier, so the request id is the positional locator ``<split>[<index>]``,
    stable only at the pinned revision. Answers and relevant/reference laws are evaluator-only."""
    dataset_id = NITIBENCH

    def request_from_question(self, row: dict, *, split: str, index: int, include: Iterable[str] = ()) -> RequestRecord:
        include = tuple(include)
        p = self._project(row, split, include)  # registry config names equal the native split names
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            raise MissingIdentifier(f"NitiBench {split} row needs a non-negative positional index")
        text = p.get("question")
        if not isinstance(text, str):
            raise ValueError(f"NitiBench {split}[{index}] has no question text")
        attrs = self._attrs(p, include) + (("request_id_kind", "positional_locator"),)
        return RequestRecord(self.dataset_id, f"{split}[{index}]", text, None, None, attrs)


class NitiBenchStatuteAdapter(_RuntimeAdapter):
    """NitiBench statute section -> SourceRecord keyed by (law_code, section_num); text kept verbatim."""
    dataset_id = NITIBENCH_STATUTE

    def source_from_section(self, row: dict, *, observed_at: str | None = None, include: Iterable[str] = ()) -> SourceRecord:
        include = tuple(include)
        p = self._project(row, "statute_ccl", include)
        code, num = p.get("law_code"), p.get("section_num")
        if code in (None, "") or num in (None, ""):
            raise MissingIdentifier("statute section lacks law_code or section_num")
        text = p.get("section_content")
        if not isinstance(text, str):
            raise ValueError(f"statute section {code}/{num} has no section_content")
        sid = f"{code}/{num}"
        return SourceRecord(self.dataset_id, sid, self.revision, p.get("law_name"), text,
                            f"{self.dataset_id}@{self.revision}:statute_ccl/{sid}", self.language,
                            None, None, observed_at, self._attrs(p, include))
