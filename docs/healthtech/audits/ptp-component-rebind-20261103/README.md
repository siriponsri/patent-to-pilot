# Component-results current-head rebind — 2026-11-03

Status: `PASS_CURRENT_HEAD_COMPONENT_RECEIPTS_REUSED_NO_RERUN`.

This addendum binds the previously executed PANORAMA/Helmers component
receipt and the previously executed local Qwen receipt to the current source
candidate `bd7f7ad7238fad052a24b1b878a7fedfba490404` by checking that the
result-producing runtime paths are unchanged. It is a provenance check, not a
new scientific run and not a promotion of component results to the main
adaptive dossier study.

## Rebind checks

- PANORAMA/Helmers runtime paths unchanged from `ab7ad348` (exit `0`).
- Qwen runtime paths unchanged from `a3bf4ff` (exit `0`).
- The dataset protocol diff since the component run changes only status and
  next-action narrative; endpoint, freeze, split, budget, and source identity
  are unchanged.
- Existing component result SHA-256:
  `956aaa9266322f0bfe749729a326c86d237c574673d3bef90eed5be80a632425`.
- Existing Qwen rebind checkpoint SHA-256:
  `c3406a25365cebba22b9d24b4d9dc8bfcb24c9138f42efce651323d39a278dd2`.

## Reused results

- PAR4PC validation: 3,029 rows, macro gold option hit@1 `0.733575`.
- PAR4PC test: 2,896 rows, macro gold option hit@1 `0.715124`.
- PI4PC validation: 3,937 rows, macro gold paragraph hit@1 `0.377699`.
- PI4PC test: 3,402 rows, macro gold paragraph hit@1 `0.401235`.
- Helmers diagnostic: 10 targets, 450 judged pairs, macro AP `0.885450`,
  macro AUC `0.880012`.
- Local Qwen3-8B receipt: 3 guided schema-valid cases, inference reused,
  paid cost `USD 0.00`.

All rows, failures, hashes, rights boundaries, and private-artifact pointers
remain in the original receipts. No raw payloads, secrets, or model weights
were copied into this package.

## Interpretation boundary

These are component benchmark and local-generation engineering results. They
do not establish semantic device-patent gold, adaptive superiority, a live
API comparison, external business validation, willingness-to-pay, revenue,
ROI, or journal acceptance. The main adaptive dossier study remains partial.

Machine-readable details are in [`verification.json`](verification.json).
