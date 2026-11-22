# B53 phase close: pull and prune `/data/ptp-paper2/b53` (22 Nov 2026)

This is the phase-end step of the owner rule of 21 Nov
([runbook](../../../docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md)). The B53 Stage 2 scoring and evaluation have both
finished, and no B53 job is running.

| Step | Result |
|---|---|
| Compress run TSVs in place (`pigz -k`, sha256 of `pigz -dc` must equal the original before the original is removed) | 8/8 OK; `runs/` went from 590 MB to 153 MB. Log on dr-train: `b53/logs/compress-runs-20261122.tsv` (also in the archive). Read with `gunzip -c F0.tsv.gz`. |
| Pull `b53/` (excluding `inputs/`) to `../_private_artifacts/dr-train-archive/20261122-b53/` | 63 files, 211.9 MB, **63 OK, 0 mismatch, 0 error** (`pull-manifest.tsv`, `pull-summary.json`). |
| Delete `b53/failed/` (8 OOM timing logs, all pulled OK) | Done. |
| Delete `b53/inputs/` (byte-identical to `_private_artifacts/healthtech/ptp-b53-inputs-20261119-v1/`, all 4 sha256 equal) | **Not done.** The folder and its files are read-only (`dr-xr-sr-x`), set when the inputs were frozen on 19 Nov. I did not change permissions to get around this. Removing it frees 341 MB. Ask the owner, or run `chmod -R u+w` on it then `rm` the 4 listed files. |

The deletion manifest is [deletion-manifest.tsv](deletion-manifest.tsv). Only the `failed/` rows were executed.

**Size on dr-train:** `b53/` went from 882 MB to 528 MB. That leaves 341 MB of read-only inputs, 153 MB of compressed runs,
about 50 MB of Stage 2 scores, plus small results, code and logs.

**Kept on dr-train:** the compressed runs, Stage 2 scores and results files stay as a second copy. They are small, and
G04 may rebuild the Paper 53/B53 bridge table from them.
