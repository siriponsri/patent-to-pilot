# G03 data area

Current repository publication status: the project now has a local Git checkout. The root and data ignore rules exclude raw/processed/derived payloads and evaluator-only material; only the small G03 provenance receipts listed below are intended for Git retention. The historical note below records the pre-initialization state and is not the current repository status.

This directory is the local data boundary for the Patent-to-Pilot G03 acquisition work package. It is intentionally separate from the existing `methodology/datasets/` historical/preflight inventory. Raw downloads are kept under `data/raw/`; extracted, bounded samples and reports are under `data/processed/` and `data/derived/`; provenance and integrity receipts are under `data/manifests/`.

This workspace currently has no `.git` repository. `data/.gitignore` records a future repository policy to exclude raw/processed/derived payloads and evaluator-only material; it is not effective Git protection yet. The small provenance receipts listed below are intended for retention if a repository is initialized. Do not move, delete, or replace the existing DAPFAM files under `methodology/datasets/`; G03 checked those files before deciding not to download the large DAPFAM corpus again.

## Current G03 mapping

| Area | Contents | Status |
|---|---|---|
| `raw/pls/` | PLS Atazanavir and Ritonavir CSV payloads retrieved through Git LFS | verified raw payloads; CC BY 4.0 data note |
| `raw/enterprise/` | EnterpriseRAG v1.0.0 questions and two GitHub source slices | verified raw payloads; repository/code MIT LICENSE snapshot only; data/release-asset terms not separately established; not full benchmark |
| `raw/metadata/` | README/license/release snapshots for the acquired sources | provenance snapshots |
| `processed/enterprise/github_closed_sample/` | evaluator-only selected questions/documents plus allowlisted agent view | closed bounded sample; not full benchmark |
| `derived/` | streaming analysis report | derived, reproducible from raw files |
| `manifests/` | acquisition, metadata, and analysis receipts | provenance/integrity records; intended Git-retained receipts if a repository is initialized |

DAPFAM remains at the pre-existing `methodology/datasets/research-only-nc/` qrels plus `methodology/datasets/samples/` first-five API rows and metadata snapshots. Its CC BY-NC-SA 4.0 research-only restriction remains applicable. No DAPFAM corpus/queries parquet was copied into this G03 data area.
