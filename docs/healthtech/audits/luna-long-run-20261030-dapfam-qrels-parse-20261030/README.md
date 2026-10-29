# HT M34 DAPFAM qrels parse revalidation

- Run ID: `luna-long-run-20261030-dapfam-qrels-parse-20261030`
- Date: `2026-10-30`
- Parent audit: `docs/healthtech/audits/luna-long-run-20261030-dapfam-preflight-20261030/README.md`
- Base and candidate commit: `a1a187c`
- Status: `PASS_QRELS_PARSE_RETRIEVAL_BLOCKED`

## Objective

Revalidate the M33 DAPFAM preflight after a local DuckDB CLI became available. Inspect the existing qrels schema and row-level aggregate structure without acquiring the missing full corpus or query parquet.

## Result

The qrels parquet parses successfully and is structurally coherent:

- Schema: `query_id VARCHAR`, `relevant_id VARCHAR`, `relevance_score DOUBLE`, `domain_rel VARCHAR`.
- Rows: `49,869`.
- Unique query IDs: `1,247`; unique target IDs: `45,336`.
- Relevance score range: `0.0` to `1.0`.
- Null query IDs: `0`; null target IDs: `0`.
- Duplicate `(query_id, relevant_id)` groups: `0`.
- Each query has 29–40 qrel rows, with a mean of `39.991`.

| Domain relation | Rows | Queries | Target IDs |
|---|---:|---:|---:|
| `IN` | 19,736 | 1,217 | 17,580 |
| `NC` | 24,940 | 1,247 | 24,918 |
| `OUT` | 5,193 | 905 | 3,653 |

The exact `IN` and `OUT` positive-row counts match the published dataset metadata. This strengthens the case for a separate DAPFAM patent-retrieval component preflight, but it does not change the task-fit decision: citation-based family retrieval is not named medical-device/product semantic relevance gold.

## Scope and limits

- The full DAPFAM `corpus.parquet` and `queries.parquet` remain absent locally.
- No index, ranking model, retrieval run, or NDCG/Recall result was produced.
- The qrels are evaluator relations under the recorded CC BY-NC-SA 4.0 research-only boundary; they are not HT-T1 device/product labels.
- The qrels parse does not verify biomedical or medical-device coverage, temporal independence, family leakage, or a HealthTech holdout.
- No raw qrels rows were copied into this audit directory; only aggregate counts and the existing source hash are recorded.

## Verification

- DuckDB `DESCRIBE` over the local parquet: PASS.
- DuckDB aggregate counts and duplicate/null checks: PASS.
- Existing qrels SHA-256 and `PAR1` framing: unchanged from M33 and pinned release metadata.
- Full corpus/query acquisition: `0`.
- Provider calls: `0`.
- Paid cost: `USD 0.00`.
- Semantic labels created: `0`.

## Decision and next action

Retain DAPFAM as a separate patent-retrieval diagnostic candidate. Do not use it to satisfy HT-T1 semantic device–patent evidence. The primary next action remains owner-authorized intake of a rights-cleared semantic judgment source with explicit labels, exact locators, revision/hash, adjudicator role, multiple independent company/family groups, and an untouched holdout; then run M23, M25, and M24 before frozen-control reruns.
