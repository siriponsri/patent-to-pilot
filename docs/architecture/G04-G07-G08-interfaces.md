# G04/G07/G08 interfaces

## Organization input

Each profile lives at methodology/organizations/<profile-id>/v1/ and contains profile.json, policy.json, source-map.json, and confirmation-queue.md. Profile IDs are PTP-FIC-ORG-A, PTP-FIC-ORG-B, and PTP-FIC-ORG-C; all are fictional benchmark fixtures, not validated organization cards.

## Core record IDs

SourceRecord.source_id, OrganizationProfile.profile_id, ConstraintRecord.constraint_id, EvidenceRecord.evidence_id, RouteRecord.route_id, ChangeRecord.change_id, and FeedbackRecord.feedback_id are stable external IDs. SQLite stores (record_type, record_id, version) append-only; consumers read latest or full history.

## G08 document input

PLSIngester.iter_documents() accepts one pinned PLS CSV and yields one PatentDocument at a time. ingest_jsonl() writes normalized records without loading the file into RAM. FTSIndex.add_jsonl() builds a local SQLite FTS5 index from normalized JSONL. search(query, source_id=None, label=None) returns source-linked SearchHit records.

The only supported Enterprise input for this slice is the G03 agent-facing allowlist view. The implementation does not parse or accept evaluator-only expected documents/answers.

## Extraction input/output

ExtractionRequest selects document_id, role, query, and a named component. LexicalExtractor returns a bounded character span with source locator and model_called=false, or unknown when the literal is absent. ModelExtractionAdapter is an explicit disabled seam and raises if called.

These outputs establish traceability and deterministic behavior only. They do not establish entailment, feasibility, clinical safety, regulatory approval, patentability, or FTO.
