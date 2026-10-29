"""Shared offline retrieval and dossier composition for HT-B0a..HT-B3.

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
from patent_to_pilot.healthtech.policies import fixed_hybrid_rerank
from patent_to_pilot.healthtech.rights import (
    ExportPurpose,
    RightsBoundaryError,
    enforce_dossier_rights,
    limit_displayable_payload,
    project_evidence,
    source_rights_summary,
)
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
    policy_id: Literal["HT-B0a", "HT-B0b", "HT-B1", "HT-B2", "HT-B3"] = "HT-B0b"
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
        if self.query.brief.data_class == "public" and any(
            not s.synthetic and s.rights is None for s in all_sources
        ):
            raise ValueError("public runtime sources require a typed rights policy")
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
    if data.policy_id == "HT-B0a":
        company_query = " ".join(value for value in data.query.company_metadata.values() if value.strip())
        schedule = [("company_search", company_query)] if company_query else []
    else:
        schedule = [("technical_search", data.query.technical_description)]
        if data.policy_id in {"HT-B1", "HT-B2"}:
            schedule += [("feature_search", f) for f in data.query.features_of_interest]
    feature_cursor = 0
    if data.policy_id == "HT-B3":
        schedule = [("technical_search", data.query.technical_description)]
    failures = False
    stop_reason = "fixed_schedule_complete"
    index = FTSIndex(source_id="ht-local-corpus", source_version=input_hash)
    corpus_texts = {pid: f"{p.title} {p.source.payload}" for pid, p in corpus.items()}
    try:
        for pid, p in corpus.items():
            index.add(PatentDocument(document_id=pid, source_id="ht-local-corpus", source_version=input_hash,
                publication_id=pid, title=p.title, abstract=p.source.payload, labels="[]",
                source_locator=p.source.source.uri, source_sha256=p.source.source.sha256))
        index.connection.commit()
        cursor = 0
        while cursor < len(schedule):
            action, query = schedule[cursor]
            cursor += 1
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
            if data.policy_id == "HT-B1":
                ranked_hits = fixed_hybrid_rerank(query, hits, corpus_texts, limit=len(hits))
            else:
                ranked_hits = [(hit, 1.0 / (60 + rank), 0.0) for rank, hit in enumerate(hits, 1)]
            returned = [h.document_id for h, _, _ in ranked_hits]
            new = 0
            for rank, (h, fused_score, overlap) in enumerate(ranked_hits, 1):
                p = corpus[h.document_id]
                if h.document_id not in candidates:
                    new += 1
                    scores = {"rrf_fixed_k60": 1 / (60 + rank)}
                    if data.policy_id == "HT-B1":
                        scores["hybrid_fixed"] = fused_score
                        scores["token_overlap"] = overlap
                    candidates[h.document_id] = PatentCandidate(patent_id_raw=p.patent_id,
                        patent_id_canonical=h.document_id, source_id=p.source.source.source_id,
                        source_revision=p.source.source.version_label, retrieval_action_ids=[step_id],
                        scores={**scores, "sqlite_fts5_bm25_lower_is_better":h.rank})
                else:
                    old=candidates[h.document_id]
                    scores = {**old.scores,
                        "rrf_fixed_k60": old.scores["rrf_fixed_k60"] + 1/(60+rank)}
                    if data.policy_id == "HT-B1":
                        scores["hybrid_fixed"] = scores.get("hybrid_fixed", 0.0) + fused_score
                        scores["token_overlap"] = max(scores.get("token_overlap", 0.0), overlap)
                    candidates[h.document_id]=PatentCandidate.model_validate({**old.model_dump(),
                        "retrieval_action_ids":[*old.retrieval_action_ids,step_id],
                        "scores":scores})
            summary = {
                "HT-B0a": "Company/metadata-only control",
                "HT-B0b": "Declared single-query lexical baseline",
                "HT-B1": "Fixed lexical plus token-overlap hybrid approximation",
                "HT-B2": "Declared fixed multi-query reciprocal-rank schedule",
                "HT-B3": "Simple no-new-candidate heuristic",
            }[data.policy_id]
            remaining = AcquisitionBudget(max_search_calls=remaining.max_search_calls,
                max_returned_candidates=before.max_returned_candidates-len(hits))
            events.append(AcquisitionEvent(run_id=run_id, query_id=data.query.query_id, step_id=step_id,
                policy_id=data.policy_id, action_type=action, input_reference_ids=data.query.permitted_inputs,
                returned_candidate_ids=returned, new_candidate_count=new, started_at=timestamp,
                ended_at=datetime.now(timezone.utc), elapsed_seconds=perf_counter()-step_started,
                search_calls=1, returned_candidates=len(hits), errors=errors,
                remaining_budget_before=before, remaining_budget_after=remaining,
                configuration_hash=configuration_hash, decision_summary=summary))
            if data.policy_id == "HT-B3":
                if new > 0:
                    stop_reason = "policy_stop"
                    break
                if feature_cursor < len(data.query.features_of_interest):
                    schedule.append(("feature_search", data.query.features_of_interest[feature_cursor]))
                    feature_cursor += 1
                else:
                    stop_reason = "no_new_candidates_under_policy"
                    break
    finally:
        index.close()
    if failures:
        stop_reason = "run_failure"
    ranked = sorted(candidates.values(), key=lambda c:(-c.scores.get("hybrid_fixed", c.scores["rrf_fixed_k60"]), c.patent_id_canonical))
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
        artifacts={"dossier":"dossier.json","export":"dossier.md","export_en":"dossier.en.md",
                   "export_th":"dossier.th.md","events":"acquisition_events.jsonl","manifest":"manifest.json"},
        limitations=["Offline lexical/fixed-schedule engineering only; no hybrid, adaptive or LLM comparison.",
                     "No scientific benchmark or user evaluation was executed.",
                     "Index construction is included in total elapsed time; action times cover searches only."],
        rights_summary=[source_rights_summary(source) for source in data.sources + [p.source for p in data.patents]])
    return dossier,events,manifest


def export_markdown(dossier: DossierVersion, *, language: Literal["auto", "en", "th"] = "auto",
                    purpose: ExportPurpose = "local_research") -> str:
    """Readable, editable export; literals escape table syntax and raw HTML."""
    import html
    enforce_dossier_rights(dossier, purpose=purpose)
    evidence, evidence_diagnostics = project_evidence(
        dossier.evidence, dossier.sources, purpose=purpose
    )
    def cell(value):
        return html.escape(str(value)).replace("|", "&#124;").replace("\n", " ").replace("\r", " ")
    if language not in {"auto", "en", "th"}:
        raise ValueError("language must be auto, en, or th")
    th = dossier.query.brief.language == "th" if language == "auto" else language == "th"
    parent_version = "(none)" if dossier.parent_version is None else str(dossier.parent_version)
    lines=["# แฟ้มหลักฐาน HealthTech" if th else "# HealthTech evidence dossier",
        "",f"Device/comparator: {cell(dossier.query.device_id_raw)}",f"Run: {cell(dossier.run_id)}",
        f"Dossier version: {dossier.version}", f"Parent version: {parent_version}",
        f"Validation scope: {cell(dossier.validation_scope)}",
        f"Evidence cutoff: {dossier.query.evidence_cutoff}",
        "", "**SYNTHETIC ENGINEERING EXAMPLE**" if dossier.query.brief.data_class=="synthetic" else "**PUBLIC-SOURCE ENGINEERING DRAFT**",
        "", "## หลักฐานจากต้นทาง" if th else "## Source evidence", "",
        "| Statement | Kind | Source / revision | Locator | Integrity check |",
        "|---|---|---|---|---|"]
    for e in evidence:
        lines.append("| "+" | ".join(map(cell,[e.statement,e.evidence_kind,f"{e.source_id} / {e.source_version}",e.locator,e.verification_status]))+" |")
    lines += ["", "## Patent candidates", "", "| Patent document | Association status | Source |", "|---|---|---|"]
    lines += [f"| {cell(c.patent_id_canonical)} | {c.association_status} | {cell(c.source_id)} |" for c in dossier.candidates]
    unresolved = list(dossier.unresolved_items) + evidence_diagnostics
    lines += ["", "## ข้อมูลที่ยังขาด" if th else "## Unresolved", ""]+[f"- {cell(s)}" for s in unresolved]
    lines += ["", "## ข้อมูลที่ควรขอเพิ่ม" if th else "## Next information requests", ""]+[f"- {cell(s)}" for s in dossier.next_information_requests]
    lines += ["", "## การแก้ไขของผู้ใช้" if th else "## User edits", ""]
    if dossier.user_edits:
        lines += ["| Field | Value |", "|---|---|"]
        lines += [f"| {cell(key)} | {cell(value)} |" for key, value in sorted(dossier.user_edits.items())]
    else:
        lines.append("_(none)_" if not th else "_(ไม่มี)_")
    lines += ["", "## Source manifest", ""]
    lines += [f"- {cell(s.source.source_id)}: {cell(s.source.uri)}; type {cell(s.source.source_type)}; revision {cell(s.source.version_label)}; {cell(s.jurisdiction)}; {s.source_date}; synthetic {str(s.synthetic).lower()}; sha256 {s.source.sha256}" for s in dossier.sources]
    lines += ["", "## Rights basis", "", "| Source | Product display | Redistribution | Basis | Limits |", "|---|---|---|---|---|"]
    for source in dossier.sources:
        rights = source.rights
        if rights is None:
            lines.append(f"| {cell(source.source.source_id)} | MISSING_POLICY | MISSING_POLICY |  |  |")
            continue
        lines.append("| " + " | ".join(map(cell, [
            source.source.source_id,
            rights.product_display,
            rights.redistribution,
            f"{rights.basis_url}#{rights.clause_locator} ({rights.checked_date})",
            "; ".join(rights.limits) or "(none)",
        ])) + " |")
    return "\n".join(lines)+"\n"


def serialize_dossier(
    dossier: DossierVersion,
    *,
    purpose: ExportPurpose = "local_research",
) -> dict:
    """Serialize a dossier with an explicit rights-aware export purpose.

    Local research returns the complete dossier. Product-display and
    redistribution projections retain source metadata and hashes, filter source
    payloads to reviewed fields, and omit evidence without a reviewed field basis.
    """
    enforce_dossier_rights(dossier, purpose=purpose)
    if purpose == "local_research":
        return dossier.model_dump(mode="json")

    evidence, evidence_diagnostics = project_evidence(
        dossier.evidence, dossier.sources, purpose=purpose
    )
    payload = dossier.model_dump(mode="json")
    source_diagnostics: list[str] = []
    for source_data, source in zip(payload["sources"], dossier.sources):
        try:
            source_data["payload"] = limit_displayable_payload(
                source, source.payload, purpose=purpose
            )
        except RightsBoundaryError:
            source_data["payload"] = {}
            source_diagnostics.append(
                f"External export omitted payload for source {source.source.source_id}: no reviewed displayable mapping."
            )
    payload["evidence"] = [item.model_dump(mode="json") for item in evidence]
    payload["unresolved_items"] = (
        list(payload["unresolved_items"]) + evidence_diagnostics + source_diagnostics
    )
    return payload
