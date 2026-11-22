# G03 phase close (v1, amendments 1 and 2): dr-train pull and prune, 22 Nov 2026

Runbook: [docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md](../../../docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md) (CLAUDE.md rule 8).

## Pull

- Root `/data/ptp-paper2/g03-dev`, excluding `a3/` (amendment 3, active).
- Destination `../_private_artifacts/dr-train-archive/20261122-g03/` (outside Git).
- **826 files copied, all `OK`** (remote and local sha256 equal); 0 mismatches, 0 copy errors; 4.11 GB.
  - That covers results, logs, code, the gate, evaluations (`evals*`, per-query JSON) and the small VAL run files.
- 184 files over 50 MB were not copied, because local free space (57.6 GB) is below the 100 GB rule. They are:
  - the arm run TSVs `runs/P1-DEV`, `runs-a1/P1-DEV` and `runs-a2/TRAIN`;
  - the GPU-built routes `routes/z-patembed-ta`, `routes/z-patembed-claim` and `a2/z-patembed-train`.
  They are listed in `large-files.tsv` of the archive.

## Prune (nothing deleted; lossless compression in place)

- The owner rule of 21 Nov keeps large derived files on dr-train. The arm run TSVs can be re-created with the CPU harness,
  but they were **compressed in place**, not deleted.
- Script `/data/ptp-paper2/code/maint_compress_g03_20261122.sh`: `pigz -6 -k`, then the sha256 of `pigz -dc` is compared
  with the original, and only then is the original removed.
- **327 files, all `OK`** (no gzip or verify failures). 34.95 GB became 10.51 GB, so **24.44 GB was freed**. The
  `g03-dev` folder went from 36 GB to 13 GB.
- Per-file record (path, bytes before/after, original sha256):
  [compressed-in-place.tsv](compressed-in-place.tsv).
- Read the files with `gunzip -c run.tsv.gz`. The G03 harness reads route runs (`run-*.tsv.gz`), not arm files.
- Kept as is:
  - the GPU-built route runs, which amendment 2 and possibly later work need;
  - `a3/` (amendment 3 inputs).
- No other user's or service's path was touched.
