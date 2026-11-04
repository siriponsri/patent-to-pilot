# Fresh GPU three-device encoder diagnostic — 2026-11-03

Status: `PASS_FRESH_GPU_DEVICE_RETRIEVAL_DIAGNOSTIC_NOT_DOSSIER_BINDING`.

This audit binds an already completed, current-head GPU run to the original
Patent-to-Pilot goal. It is not a new compute launch. The run encoded the
three-device development corpus with the pinned PatEmbed-base and
multilingual-e5-base snapshots on `dr-train`, returned the vectors to Windows,
and recomputed a frozen-query retrieval diagnostic from the saved artifacts.

## Candidate and run

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- Candidate HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Run ID: `20261103-pepo-patent-current`
- GPU: `GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089` / Tesla V100-SXM2-32GB
- GPU window: `2026-11-03T12:35:56.270398Z` to `2026-11-03T12:36:12.122034Z`
- Concurrency: `1`; CPU threads: `8`
- Worker wall time: `15.851646784925833` seconds
- Provider calls: `0`; paid cost: `USD0.00`
- Shared lock released: `true`; transient remote files removed: `true`
- Evaluator labels transferred to `dr-train`: `false`

## Encoder bindings and outputs

| Encoder | Revision | Passage rows | Query rows | Passage vector SHA-256 | Query vector SHA-256 |
|---|---|---:|---:|---|---|
| PatEmbed-base | `datalyes/patembed-base@244ba452908a3093be11efb8a44396652317fb14` | 41 | 3 | `ea941b035abc7e276e50c71025f10e43880c3acf08cd0143d47d90e1696cdfa1` | `e4eea689bd6074b1fc6651a517c69de6b8e16ccbb7c1839879b8cf312771b4aa` |
| multilingual-e5-base | `intfloat/multilingual-e5-base@d128750597153bb5987e10b1c3493a34e5a4502a` | 41 | 3 | `5dbc074e7bd2e50eac2debce590894700c58e12550cd6bc18db1f712bbaf4c52` | `216c5da38ff4e93e450f9c1c7e26a38cf50b2300ccbf844181aa0f9d65de7d9d` |

The Windows evidence root is private and ignored:
`%LOCALAPPDATA%/PatentToPilot/healthtech/evidence/20261103-pepo-patent-current/`.
The audit stores hashes and aggregate results only; it does not stage vectors,
raw source text, evaluator labels, credentials, or restricted payloads.

## Frozen-query diagnostic

The input contains 41 patent documents, 3 device queries, and 61
source-backed product-level disclosed links. MitraClip and Tendyne share one
query text, so there are only two unique query texts. This is a development
diagnostic; unlisted patents remain unjudged and are not treated as negatives.

| Method | Hits / 61 | Macro Recall@20 | Micro Recall@20 | Macro nDCG@20 |
|---|---:|---:|---:|---:|
| Frozen-query BM25 | 21 / 61 | 0.392685 | 0.344262 | 0.430022 |
| PatEmbed dense | 24 / 61 | 0.430073 | 0.393443 | 0.409533 |
| multilingual E5 dense | 27 / 61 | 0.481021 | 0.442623 | 0.455981 |

Independent verification recomputed rankings and metrics from the saved vectors
with maximum absolute delta `0.0` at tolerance `1e-12`.

## Boundary

This run proves current-head remote encoding, Windows vector retention, and a
reproducible three-device retrieval diagnostic. It does not prove semantic
device-patent gold, exhaustive recall, adaptive superiority, or final-holdout
performance. The current three-case HTTP dossier receipt uses a separate
MiniLM ONNX bundle; these PatEmbed/E5 vectors have not been silently promoted
to the dossier provider. O2 therefore remains partial for the full outcome
until the dossier path is explicitly bound to an imported encoder bundle.

## Source receipts

- Private GPU receipt: `gpu-compute-receipt.json`
- Private retrieval receipt: `fresh-retrieval-evaluation.json`
- Private independent recheck: `independent-fresh-verification.json`
- Private input/model manifest: `input-source-manifest.json`
- Handoff binding: `docs/healthtech/audits/pepo-blocked-goal-repair-20261103/LOCAL_ACCOUNTING_AND_GPU_FOLLOWUP.json`

No paid ledger, budget, 24-hour window, API history, or goal status was reset.
