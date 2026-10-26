# ADR-0001 — Bounded typed core and local lexical retrieval

Status: accepted for the G04/G07/G08 development slice
Date: 2026-10-24

## Decision

Use Python 3.12, Pydantic 2 models, append-only SQLite records, and SQLite FTS5 for the first local retrieval baseline. Ingestion reads G03 PLS CSVs row by row and writes normalized JSONL; retrieval stores only selected normalized records in a local index. Extraction exposes a provider-independent interface with a deterministic lexical component-window implementation and a disabled model adapter.

## Boundaries

- Source IDs, versions, SHA-256 values, and row locators remain on normalized records.
- Missing dates are unknown_not_in_source; family/publication parsing does not invent dates.
- unknown, pending, contradicted, and missing remain distinct from positive support.
- Enterprise evaluator fields (expected_doc_ids, gold_answer, answer_facts) are not accepted by the G08 agent-facing interface.
- No embeddings, external API, GPU, gated source, full corpus, or paid run is part of this ADR.

## Rejected alternatives

- Embeddings/vector indexing: no measured retrieval gap and unnecessary memory/compute for this slice.
- Full Parquet/DAPFAM load: not required for the bounded starter and conflicts with the G03 RAM/data boundary.
- ORM/workflow framework: adds moving parts before SQLite record/version behavior is tested.

## Consequences

The records can be consumed by G05/G06 through stable IDs and JSON-compatible payloads. FTS5 is a lexical candidate-exposure baseline, not semantic relevance or clinical/legal truth. A later provider may implement Provider.complete without changing core record schemas.
