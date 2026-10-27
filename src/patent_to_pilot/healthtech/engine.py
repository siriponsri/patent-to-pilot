"""Shared offline retrieval and dossier composition (HT-B0b / fixed HT-B2).

No labels, inference provider, network, secret loader or paid budget entry point.
Action limits are measured local counts, not a claim of monetary savings.
"""
from __future__ import annotations

from datetime import datetime, timezone
from time import perf_counter
from typing import Literal

from pydantic import Field, model_validator

from patent_to_pilot.healthtech.contracts import (AcquisitionBudget, AcquisitionEvent,
    Contract, DeviceQuery, DossierVersion, EvidenceItem, PatentCandidate, RunManifest,
    SourcePayload, canonical_patent_id, content_hash)
from patent_to_pilot.healthtech.provenance import check_evidence
from patent_to_pilot.ingestion.pls import PatentDocument
from patent_to_pilot.retrieval.fts import FTSIndex


class PatentInput(Contract):
    patent_id: str
    title: str = Field(min_length=1)
    source: SourcePayload

    @model_validator(mode="after")
    def text_source(self):
        canonical_patent_id(self.patent_id)
        if not isinstance(self.source.payload, str) or not self.source.payload.strip():
            raise ValueError("patent corpus requires nonempty text")
        return self


class DossierInput(Contract):
    query: DeviceQuery
    sources: list[SourcePayload] = Field(min_length=1)
    patents: list[PatentInput]
    evidence: list[EvidenceItem] = Field(default_factory=list)
    policy_id: Literal["HT-B0b", "HT-B2"] = "HT-B0b"
    per_search_limit: int = Field(default=20, ge=1, le=1000)

    @model_validator(mode="after")
    def scope(self):
        all_sources = self.sources + [p.source for p in self.patents]
        ids = [s.source.source_id for s in all_sources]
        if len(ids) != len(set(ids)):
            raise ValueError("each corpus/source payload needs a unique source ID")
        by_id = {s.source.source_id:s for s in self.sources}
        if not set(self.query.permitted_inputs) <= set(by_id):
            raise ValueError("missing permitted input sources")
        if any(s.source_date > self.query.evidence_cutoff for s in all_sources):
            raise ValueError("source is newer than query evidence cutoff")
        if self.query.brief.data_class == "public" and any(s.synthetic for s in all_sources):
            raise ValueError("synthetic sources cannot be presented as a public case")
        for s in all_sources:
            if s.source.source_type not in {"product_record", "patent_document", "regulatory_record",
                    "literature", "independent_disclosure", "synthetic_record"}:
                raise ValueError("runtime source type is not permitted; evaluator material is excluded")
            if "evaluator-only" in s.source.uri.lower():
                raise ValueError("evaluator-only sources are not runtime inputs")
        canonical = [canonical_patent_id(p.patent_id) for p in self.patents]
        if len(canonical) != len(set(canonical)):
            raise ValueError("duplicate canonical patent documents")
        if any(e.source_id not in set(self.query.permitted_inputs) for e in self.evidence):
            raise ValueError("input evidence is outside permitted brief sources")
        return self


def run_dossier(data: DossierInput, *, run_id: str, code_commit: str) -> tuple[DossierVersion, list[AcquisitionEvent], RunManifest]:
    started = perf_counter()
    input_hash = content_hash(data.model_dump(mode="json"))
    configuration_hash = content_hash({"policy_id": data.policy_id, "limit":data.per_search_limit,
                                      "budget":data.query.acquisition_budget.model_dump()})
    remaining = data.query.acquisition_budget
    by_id = {s.source.source_id:s for s in data.sources}
    evidence = [check_evidence(e, by_id[e.source_id]) for e in data.evidence]
    events: list[AcquisitionEvent] = []
    candidates: dict[str, PatentCandidate] = {}
    corpus = {canonical_patent_id(p.patent_id):p for p in data.patents}
    schedule = [("technical_search", data.query.technical_description)]
    if data.policy_id == "HT-B2":
        schedule += [("feature_search", f) for f in data.query.features_of_interest]
    failures = False
    stop_reason = "fixed_schedule_complete"
    index = FTSIndex(source_id="ht-local-corpus", source_version=input_hash)
    try:
        for pid, p in corpus.items():
            index.add(PatentDocument(document_id=pid, source_id="ht-local-corpus", source_version=input_hash,
                publication_id=pid, title=p.title, abstract=p.source.payload, labels="[]",
                source_locator=p.source.source.uri, source_sha256=p.source.source.sha256))
        index.connection.commit()
        for action, query in schedule:
            if remaining.max_search_calls == 0 or remaining.max_returned_candidates == 0:
                stop_reason = "budget_exhausted"
                break
            before = remaining
            step_id = f"{run_id}-step-{len(events)+1}"
            # Reserve a full call before search. No retry is implicit.
            remaining = AcquisitionBudget(max_search_calls=before.max_search_calls-1,
                max_returned_candidates=before.max_returned_candidates)
            timestamp = datetime.now(timezone.utc)
            step_started = perf_counter()
            errors: list[str] = []
            try:
                hits = index.search(query, limit=min(data.per_search_limit, before.max_returned_candidates))
            except (ValueError, RuntimeError):
                hits = []
                errors = ["local_search_failed"]
                failures = True
            returned = [h.document_id for h in hits]
            new = 0
            for rank, h in enumerate(hits, 1):
                p = corpus[h.document_id]
                if h.document_id not in candidates:
                    new += 1
                    candidates[h.document_id] = PatentCandidate(patent_id_raw=p.patent_id,
                        patent_id_canonical=h.document_id, source_id=p.source.source.source_id,
                        source_revision=p.source.source.version_label, retrieval_action_ids=[step_id],
                        scores={"rrf_fixed_k60":1/(60+rank), "sqlite_fts5_bm25_lower_is_better":h.rank})
                else:
                    old=candidates[h.document_id]
                    candidates[h.document_id]=PatentCandidate.model_validate({**old.model_dump(),
                        "retrieval_action_ids":[*old.retrieval_action_ids,step_id],
                        "scores":{**old.scores,"rrf_fixed_k60":old.scores["rrf_fixed_k60"]+1/(60+rank)}})
            remaining = AcquisitionBudget(max_search_calls=remaining.max_search_calls,
                max_returned_candidates=before.max_returned_candidates-len(hits))
            events.append(AcquisitionEvent(run_id=run_id, query_id=data.query.query_id, step_id=step_id,
                policy_id=data.policy_id, action_type=action, input_reference_ids=data.query.permitted_inputs,
                returned_candidate_ids=returned, new_candidate_count=new, started_at=timestamp,
                ended_at=datetime.now(timezone.utc), elapsed_seconds=perf_counter()-step_started,
                search_calls=1, returned_candidates=len(hits), errors=errors,
                remaining_budget_before=before, remaining_budget_after=remaining,
                configuration_hash=configuration_hash, decision_summary="Declared fixed query schedule"))
    finally:
        index.close()
    if failures:
        stop_reason = "run_failure"
    ranked = sorted(candidates.values(), key=lambda c:(-c.scores["rrf_fixed_k60"], c.patent_id_canonical))
    events.append(AcquisitionEvent(run_id=run_id, query_id=data.query.query_id, step_id=f"{run_id}-stop",
        policy_id=data.policy_id, action_type="stop", input_reference_ids=[], returned_candidate_ids=[],
        new_candidate_count=0, started_at=datetime.now(timezone.utc), ended_at=datetime.now(timezone.utc),
        elapsed_seconds=0, search_calls=0, returned_candidates=0, remaining_budget_before=remaining,
        remaining_budget_after=remaining, configuration_hash=configuration_hash,
        decision_summary="End of bounded local search; completeness is unknown", stop_reason=stop_reason))
    unresolved=["Retrieved candidates have no independently checked device–patent disclosure.",
                "Source integrity checks do not establish semantic support, clinical suitability or FTO."]
    if not ranked:
        unresolved.append("No candidates returned under this local policy and budget.")
    dossier=DossierVersion(project_id=data.query.brief.project_id,dossier_id=f"{run_id}-dossier",version=1,
        query=data.query,input_hash=input_hash,sources=data.sources+[p.source for p in data.patents],
        evidence=evidence,candidates=ranked,unresolved_items=unresolved,
        next_information_requests=["Request source-backed device–patent disclosures for candidate review.",
                                   *data.query.user_questions],run_id=run_id,created_at=datetime.now(timezone.utc))
    manifest=RunManifest(run_id=run_id,evidence_level="synthetic_engineering" if data.query.brief.data_class=="synthetic" else "public_source_engineering",
        code_commit=code_commit,input_hash=input_hash,policy_id=data.policy_id,configuration_hash=configuration_hash,
        data_revision="local-input-sha256",corpus_hash=content_hash([p.model_dump(mode="json") for p in data.patents]),
        expected_query_ids=[data.query.query_id],completed_query_ids=[] if failures else [data.query.query_id],
        failed_query_ids=[data.query.query_id] if failures else [],budget=data.query.acquisition_budget,
        actual_search_calls=sum(e.search_calls for e in events),actual_returned_candidates=sum(e.returned_candidates for e in events),
        elapsed_seconds=perf_counter()-started,stop_reason=stop_reason,
        artifacts={"dossier":"dossier.json","export":"dossier.md","events":"acquisition_events.jsonl","manifest":"manifest.json"},
        limitations=["Offline lexical/fixed-schedule engineering only; no hybrid, adaptive or LLM comparison.",
                     "No scientific benchmark or user evaluation was executed.",
                     "Index construction is included in total elapsed time; action times cover searches only."])
    return dossier,events,manifest


def export_markdown(dossier: DossierVersion) -> str:
    """Readable, editable export; literals escape table syntax and raw HTML."""
    import html
    def cell(value):
        return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ")
    th = dossier.query.brief.language == "th"
    lines=["# แฟ้มหลักฐาน HealthTech" if th else "# HealthTech evidence dossier",
        "",f"Device/comparator: {cell(dossier.query.device_id_raw)}",f"Run: {cell(dossier.run_id)}",
        f"Evidence cutoff: {dossier.query.evidence_cutoff}",
        "", "**SYNTHETIC ENGINEERING EXAMPLE**" if dossier.query.brief.data_class=="synthetic" else "**PUBLIC-SOURCE ENGINEERING DRAFT**",
        "", "## หลักฐานจากต้นทาง" if th else "## Source evidence", "",
        "| Statement | Kind | Source / revision | Locator | Integrity check |",
        "|---|---|---|---|---|"]
    for e in dossier.evidence:
        lines.append("| "+" | ".join(map(cell,[e.statement,e.evidence_kind,f"{e.source_id} / {e.source_version}",e.locator,e.verification_status]))+" |")
    lines += ["", "## Patent candidates", "", "| Patent document | Association status | Source |", "|---|---|---|"]
    lines += [f"| {cell(c.patent_id_canonical)} | {c.association_status} | {cell(c.source_id)} |" for c in dossier.candidates]
    lines += ["", "## ข้อมูลที่ยังขาด" if th else "## Unresolved", ""]+[f"- {cell(s)}" for s in dossier.unresolved_items]
    lines += ["", "## ข้อมูลที่ควรขอเพิ่ม" if th else "## Next information requests", ""]+[f"- {cell(s)}" for s in dossier.next_information_requests]
    lines += ["", "## Source manifest", ""]
    lines += [f"- {cell(s.source.source_id)}: {cell(s.source.uri)}; revision {cell(s.source.version_label)}; {cell(s.jurisdiction)}; {s.source_date}; sha256 {s.source.sha256}" for s in dossier.sources]
    return "\n".join(lines)+"\n"
