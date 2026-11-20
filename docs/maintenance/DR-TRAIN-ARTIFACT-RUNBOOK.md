# dr-train artifact pull and cleanup runbook

Owner rule (21 Nov 2026): after every phase, copy this project's artifacts from dr-train to local storage, then delete what is no longer needed on dr-train. This covers patent-to-pilot paths only.

## Scope

| Side | Paths in scope | Never touch |
|---|---|---|
| dr-train (`ssh chaw@100.77.149.83`) | `/data/ptp-paper2/**`, `/home/chaw/patent-to-pilot-jobs/**` | every other project, user or shared path |
| local | `C:\Users\User\Desktop\myProject\_private_artifacts\` (patent-to-pilot material), `%TEMP%\ptp-*` | repo files and git branches (another session owns cleanup there) |

## Steps

1. **Check running jobs.** Run `pgrep -af python`, `nvidia-smi` and read the queue logs, for example `b53/queue_b53_stage2.log` (ends `B53_STAGE2_SCORES_DONE`) and `bridgeret/am7/queue.log` (ends `SENS_EXIT`). Exclude the directory of any running job with `--exclude-path` and do not delete anything inside it.
2. **Dry run.** Under Git Bash, prefix the command with `MSYS_NO_PATHCONV=1`. Otherwise Git Bash rewrites `/data/...` into `C:/Program Files/Git/data/...`; the script now refuses such paths.
   ```bash
   MSYS_NO_PATHCONV=1 python scripts/maintenance/pull_dr_train_artifacts.py --dest ../_private_artifacts/dr-train-archive/<YYYYMMDD> --exclude-path /data/ptp-paper2/b53 --dry-run
   ```
   The script resumes: a re-run skips files already copied with the same size, but still hash-checks every file. A full pass over about 72k small files takes about 25 minutes on this PC.
   Check local free space. Small result files are always copied. Files larger than `--max-file-mb` (default 50) are only listed in `large-files.tsv`: run TSVs, vectors, checkpoints and big inputs. Copy those only while at least 100 GB stays free locally; otherwise ask the owner.
3. **Pull.** Run the same command without `--dry-run`. The script streams a tar over SSH, then compares the remote and local SHA256 of every file. It writes these files:
   - `pull-manifest.tsv` (status `OK`, `MISMATCH` or `COPY_ERROR`);
   - `large-files.tsv`;
   - `excluded-summary.json`;
   - `pull-summary.json`.
4. **Decide what to delete.** Delete only derived files that can be re-created, and only once every file under the path is either `OK` in the manifest or is a dry-run, failed or duplicate output with no scientific value. Good candidates:
   - dry-run, failed, killed and pilot directories;
   - transport tarballs that already have a verified local copy;
   - superseded intermediates.
   For large unique files that may still be needed, compress in place instead of deleting. Use `pigz -k`, compare the sha256 of `pigz -dc` against the original, and only then remove the original. Example: `/data/ptp-paper2/code/maint_compress_runs_20261121.sh`. Read the result with `gunzip -c run-X.tsv.gz`.
   To deduplicate byte-identical copies on the same filesystem, run `cmp` and then `ln -f canonical duplicate`.
5. **Write the deletion manifest first.** Put it at `artifacts/maintenance/<YYYYMMDD>-dr-train-cleanup/deletion-manifest.tsv`, with columns path, bytes, reason and local copy. Delete path by path; never run `rm -rf` on a root. Record the bytes freed in the summary.
6. **Clean local temp.** Zip `%TEMP%\ptp-*` folders older than 2 days into the dated archive, then remove them. Leave pytest temp alone: it may belong to a test run in progress, and pytest rotates it by itself.
7. **Commit only the maintenance files.** These are the aggregate summary and the deletion manifest. Never commit raw data, TEST material or secrets.

## Always keep on dr-train

These are needed by upcoming goals (`docs/owner/owner-note-21112026/02`, `04`) or costly to re-create:

- public raw data: `oa2017`, `patentsview` (the continuity tables needed an owner login), `panorama`, `beir`;
- model weights:
  - `/data/ptp-paper2/models/*` (Qwen3-Embedding-0.6B, Qwen3-Reranker-0.6B, Arctic);
  - `research-product-o1-o4-20261031/models/*` (Qwen3-8B, PatEmbed, bge-reranker-v2-m3, e5);
  - the venv at `research-product-o1-o4-20261031/venv`;
- the Challenge-1M corpus, manifests, `splits/`, `pairs-dev`, and the sealed P1-TEST gold left in place (`challenge1m/out-v1/sealed/`: never copied, never opened);
- corpus vectors (`runs/z-*/passages.f16.npy`), which take hours of V100 time to re-encode;
- the dispatch journals (`ptp-r6-control`).

## Hard exclusions in the pull script

The script never copies these: anything sealed or TEST-related (`sealed/`, `pairs.tsv`, test qrels, `-test-` job folders, `splits/private`), model weights and checkpoints, venvs and caches, and the raw public datasets above. TEST job folders stay on dr-train untouched.
