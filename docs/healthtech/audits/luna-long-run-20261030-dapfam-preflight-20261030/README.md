# HT M33 DAPFAM retrieval-diagnostic preflight

- Run ID: `luna-long-run-20261030-dapfam-preflight-20261030`
- Date: `2026-10-30`
- Base and candidate commit: `55b5394eaf4c57c0de9b601ecfa8b91b1fc7f80b`
- Status: `PASS_DIAGNOSTIC_PREFLIGHT_BLOCKED_FOR_RETRIEVAL`
- Scope: inspect the existing local DAPFAM release boundary without acquiring the missing corpus or query parquet

## Objective and decision

Determine whether the existing DAPFAM artifacts can support a separately labeled patent-retrieval component package without being misrepresented as HT-T1 medical-device/product-to-patent semantic gold.

Decision: DAPFAM is suitable only as a potential, separate patent-family retrieval diagnostic. It is not admissible as the primary HT-T1 semantic device-patent judgment source because its documented task is citation-based family retrieval with IPC3 IN/OUT partitions, not named medical-device/product relevance adjudication. The current local snapshot is also incomplete for a retrieval run: only qrels, metadata, and five-row query/corpus samples are present.

## Inputs and rights boundary

| Input | Local evidence | Result |
|---|---|---|
| Pinned DAPFAM metadata | `methodology/datasets/metadata/dapfam_repo.json`, `dapfam_tree.json`, `DAPFAM_README.md` | PASS; release revision `a59a74ce31384165065af1823a83c6f94ccafd48` and CC BY-NC-SA 4.0 are recorded |
| Qrels | `methodology/datasets/research-only-nc/qrels_all.parquet` | PASS integrity; 828,375 bytes, SHA-256 `e51ae4e13abee0fc7523560ecddd272bc85dc98befc8ab4466155a0c2d2d4f74`, `PAR1` header/footer |
| Query sample | `methodology/datasets/samples/dapfam_queries_first5.json` | PASS as a five-row API snapshot; revision is not byte-pinned to the release commit |
| Corpus sample | `methodology/datasets/samples/dapfam_corpus_first5.json` | PASS as a five-row API snapshot; revision is not byte-pinned to the release commit |
| Full corpus and queries | Release metadata only; not present locally | NOT_ACQUIRED; do not download merely to make HT-T1 appear complete |

The DAPFAM collection license remains research-only. The underlying public nature of patent documents does not remove the dataset collection terms. No raw DAPFAM payload was copied into this audit directory.

## Claim and evidence ledger

| Claim | Status | Evidence and limit |
|---|---|---|
| The pinned release is a patent-family retrieval benchmark | PASS | Local README describes 1,247 query families, 45,336 target families, family-level full text, citation-based relevance, and IN/OUT IPC3 partitions |
| Existing local qrels are authentic and hash-matched | PASS | Local `PAR1` framing and SHA-256 match the pinned release tree/LFS metadata |
| DAPFAM is HT-T1 semantic device-patent gold | REJECTED | Task mismatch: citation links and domain partitions do not provide named device/product relevance adjudication or clinical/product semantics |
| Qrels schema and row counts are locally verified | NOT_RUN | No parquet reader is installed; an ephemeral DuckDB install attempt failed at DNS/PyPI resolution and installed no package |
| A DAPFAM retrieval metric can be reported now | BLOCKED_LOCAL | Full corpus and query parquet are absent; no ranking/index/model run was performed |
| A future separate component study is feasible in principle | READY_FOR_REVIEW | Requires rights confirmation for the intended use, a reproducible reader, full corpus/query acquisition or an approved alternative, and a frozen retrieval protocol |

## Source matrix

| Source | Supported fact | Limitation |
|---|---|---|
| `DAPFAM_README.md` | Dataset purpose, license, published counts, task views, and metrics | Release description, not an independent semantic adjudication protocol |
| `dapfam_repo.json` | Dataset identity, pinned SHA, license tag, configs, and file names | API metadata, not a local payload parse |
| `dapfam_tree.json` | Release file sizes and LFS hashes | Does not expose row-level schema or judgments |
| `download-manifest.json` | Acquisition scope and qrels hash receipt | Records prior inability to parse parquet in this environment |
| Five-row query/corpus samples | Representative field names and text shape for inspected rows | API samples are not revision-pinned or evidence of medical-device coverage |

## What remains unresolved

- No verified count of biomedical, medical-device, or HealthTech families is available from the local metadata and samples.
- No local qrels schema/row-count parse was completed.
- No full corpus/query payload is present, so no lexical, dense, hybrid, or adaptive retrieval score exists.
- DAPFAM cannot provide the required explicit `relevant` / `not_relevant` semantic labels, adjudicator role, device/product identity, or HT-T1 company/family holdout by itself.
- The primary HealthTech blocker remains an owner-authorized, rights-cleared semantic judgment source with explicit labels, exact locators, source revision/hash, multiple independent company/family groups, and an untouched holdout.

## Verification and resource use

- Metadata, samples, and qrels were inspected locally; the qrels SHA-256 was recomputed.
- Reader availability check: PASS for the check itself; `pyarrow`, `duckdb`, `polars`, `pandas`, and `fastparquet` were absent.
- Ephemeral DuckDB install attempt: FAIL at DNS/PyPI resolution; no package or dataset was installed or retained.
- Provider calls: `0`.
- Paid cost: `USD 0.00`.
- Semantic labels created: `0`.
- Full corpus/query acquisition: `0`.
- No credentials, `.env` files, or private journals were read.

## Next test

Do not block the main HealthTech branch on DAPFAM. First obtain owner authorization and exact rights/schema terms for an admissible semantic source, then run M23, M25, and M24 and rerun frozen HT-B0a/B0b/B1/B2/B3 controls without changing the denominator, holdout membership, family/company grouping, or `UNJUDGED` policy. If a separate patent-retrieval component is later desired, acquire only the full DAPFAM inputs under verified research-use terms and freeze a distinct protocol/evaluator.
