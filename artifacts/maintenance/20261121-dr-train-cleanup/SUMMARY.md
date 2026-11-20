# dr-train artifact archive and cleanup — 21 Nov 2026

Owner request of 21 Nov 2026: pull all patent-to-pilot artifacts from dr-train to local storage, delete what is no longer needed, and repeat after every phase. This folder holds aggregates only: no raw data, no TEST content, no secrets. Procedure: [DR-TRAIN-ARTIFACT-RUNBOOK.md](../../../docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md). Script: `scripts/maintenance/pull_dr_train_artifacts.py`.

## Result

| | Before | After | Freed |
|---|---|---|---|
| `/data/ptp-paper2` (du) | 63 GB | 42 GB | about 21.8 GB |
| `/data` filesystem used (df) | 533.6 GB, estimated before compression | 511.8 GB | about 21.8 GB (10.83 GB from compression + 10.94 GB from deletion and dedup) |
| `/home/chaw/patent-to-pilot-jobs` | 46 GB | 46 GB | 0 (nothing deleted there; see the owner items) |
| Local `%TEMP%\ptp-*` | 104 MB readable | 0.1 MB readable | 100 MB (zipped into the archive first) |
| Local disk C: free | 57.3 GB | 52.2 GB | archive added 3.9 GB |

## What was archived

`C:\Users\User\Desktop\myProject\_private_artifacts\dr-train-archive\20261121\` (outside git), 3.9 GB:

- `files/<remote path>`: 71,541 small result files (logs, eval and summary JSON, per-query results, receipts, manifests, code snapshots). Every file is at most 50 MB, and every file's local sha256 equals the remote sha256 (`pull-manifest.tsv`: 71,541 OK, 0 mismatch, 0 error). [archive-by-directory.tsv](archive-by-directory.tsv) gives the counts per directory.
- `pull-manifest-r2-predelete.tsv`: verification taken before the deletions; it is the evidence for the deleted paths.
- `large-files.tsv`: 73 files over 50 MB (46.8 GB) that were **not copied**, because local free space is below the 100 GB margin. They are vectors, run TSVs, corpora and serialisations, and they stay on dr-train.
- `local-temp/temp-ptp-20261121.zip`: 53 local temp files (code transport tars and probe folders) from before they were removed.

Never copied, left in place untouched: sealed and protected TEST material (`challenge1m/out-v1/sealed/`, `splits/private/`, and every `*-test-*` job folder: 49,439 files), model weights, virtualenvs and caches, and the raw public datasets.

## What changed on dr-train

Full list with sizes and reasons: [deletion-manifest.tsv](deletion-manifest.tsv), written before deleting. Execution logs: [remote-delete-log.tsv](remote-delete-log.tsv) and [remote-compress-log.tsv](remote-compress-log.tsv).

- **Deleted (8.38 GB):**
  - `bridgeret/dryrun`: trainer dry-run, 3.67 GB;
  - `bridgeret/ft-bundle-v1.tar.gz`: verified local copy, sha 4416ddb0;
  - `runpod-pilot`: finished pilot. Its only uncopied file is a public USPTO bulk zip;
  - `bridgeret/failed`;
  - the killed `am7/stage2a-v1`;
  - 8 run TSVs under `runs/ft-{S1,S2-t0.05,S3,S4rule}/`. Each is byte-identical to the `.gz` kept in `ft-grid/` (verified by sha256 after `gunzip`).
- **Hardlinked (2.56 GB, lossless):** `ft-bundle-v1/ser/passages.jsonl` and `ft-bundle-v1/mined-TRAIN.jsonl` were byte-identical to `ser-qwen3-v1/passages.jsonl` and `mined-qwen3-v1/mined-TRAIN.jsonl`.
- **Compressed in place (15.61 GB → 4.78 GB, lossless):** the 17 unique `runs/*/run-*.tsv` files are now `run-*.tsv.gz`. Each original was removed only after the sha256 of `pigz -dc` matched it. Scripts that read these TSVs need `gunzip -c` first.

## Kept on dr-train, and why

- Raw public data that is costly to re-download: `oa2017`, `patentsview` (needed an owner login), `panorama`, `beir`.
- Models the plan still uses:
  - `/data/ptp-paper2/models` (Qwen3-Embedding-0.6B, Qwen3-Reranker-0.6B, Arctic);
  - `research-product-o1-o4-20261031/models` (Qwen3-8B, PatEmbed, bge-reranker-v2-m3, e5);
  - the venv in the same folder.
- The Challenge-1M corpus and manifests, `splits/`, `pairs-dev`, and the sealed P1-TEST gold, left in place.
- Corpus vectors `runs/z-*/passages.f16.npy` (each takes hours of V100 time to re-encode), texts, serialisations, mined TRAIN sets, the extracted `ft-bundle-v1/`, and the S\* checkpoint `ft-grid/S2-t0.02/ckpt-fp16`.
- `b53/`: **B53 Stage 2 is still running** (PID 2137435; 861/905 queries at about 04:30 Bangkok, then BGE). Nothing there was changed. A first copy of its small files was taken by accident while it ran (Git Bash path rewriting defeated `--exclude-path`; this is now fixed). Those copies sit in the local archive but are not part of the final manifest. Its inputs were originally staged from the existing local folder `ptp-b53-inputs-20261119-v1`, so they add no new exposure.
- All `/home/chaw/patent-to-pilot-jobs` job folders, including the dispatch journal `ptp-r6-control`. Their DAPFAM corpus copies are already hardlinked to one another.

## Follow-ups done in this phase

- AM-7 sensitivity (`SENS_EXIT 0`): `sensitivity.json` was copied into `docs/healthtech/research/paper1-bridgeret/am7/stage2a/` (sha 04ca266e matches the remote copy), the tables were re-rendered, and the Thai report was updated.

## Waiting for the owner

1. Large derived files that could be deleted to free more space. They were not deleted because they were not copied locally. **Owner decision, 21 Nov 2026: keep them for now.** Revisit only when dr-train space is needed:

   | Files | Size | Note |
   |---|---|---|
   | `mtm-20261107/out/passage-vectors-f32.npy` | 6.1 GB | MTM study is closed; the vectors can be re-created |
   | `scout-public-demo/raw/hupd-2017.tar.gz` | 4.5 GB | public HUPD archive, re-downloadable; is the Scout demo still needed? |
   | `mtm-20261107/inputs/corpus.jsonl` | 2.0 GB | |
   | `bridgeret/ser-{arctic,patembed}-v1` | 3.2 GB | serialisations; can be rebuilt from `texts-v1` |
   | `runs/*/run-TRAIN.tsv.gz` | 2.9 GB | mining is done (`mined-*` exist) |

2. Run B53 Stage 2 evaluation and rendering when the job finishes, then pull and prune `b53/` (next phase).
3. Local `_private_artifacts/healthtech` (8.6 GB) is listed in [local-private-artifacts-survey.tsv](local-private-artifacts-survey.tsv). Nothing there was deleted. `medtech-time-machine` (4.95 GB) is the largest item.
4. 55 ACL-locked `%TEMP%\ptp-*` folders were left as they are, because changing ACLs is not allowed. pytest temp folders were left too, because another session was running pytest at the time.
