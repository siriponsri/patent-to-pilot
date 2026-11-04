# HealthTech O1-O4 HTTP/vector package audit - 2026-10-31

Status: `READY_FOR_REVIEW_PARTIAL_O4_O3_API_BLOCKED_LOCAL`.

This run records the bounded O1-O4 package after the loopback HTTP/vector
implementation was committed at `928729ee1381280cc11d85439e63a71dff91432f`.
It stores only authored code provenance, sanitized receipts, hashes, command
outcomes, and continuation state. Raw corpus/source payloads, vector bundles,
model weights, evaluator-only labels, credentials, and private absolute paths
remain outside Git.

## Outcomes

- O1: `COMPLETE`. Loopback HTTP jobs, cancellation/resume, source inspection,
  versioned history, selected-version export, provider selection, and the real
  Chrome acceptance flow pass. The browser remains loopback-only.
- O2: `COMPLETE`. PatEmbed-base and multilingual-e5-base bundles are bound to
  server-owned runtime inputs. Three Abbott device cases pass through HTTP,
  dense retrieval, source inspection, history edit, and JSON/Thai/English
  export for each model. No provider call or paid cost occurred.
- O3: `BLOCKED_LOCAL`. The frozen local Qwen3-8B generation branch passes 3/3
  schema-valid cases, but the qwen/qwen3-32b API comparison remains closed by
  unresolved ledger identity, account-credit, authorization, and prompt-rights
  gates.
- O4: `PARTIAL`. Real named-device HTTP/vector/history/export runs pass. The
  adaptive report remains descriptive offline evidence; the deterministic
  controller is not Qwen3, the HT-B4 row is mock-only, and local generation
  is not yet an HTTP provider action.

## Canonical artifacts

- `CHECKPOINT.json`: resumable package state and scoped blockers.
- `REPORT.md`: English evidence report and limitations.
- `REPORT_TH.md`: Thai handoff summary.
- `verification.json`: commands, statuses, and evidence boundaries.
- `manifest.json`: sanitized file/source hash manifest; self-excluded.
- `patembed-http-receipt.json`: real three-case PatEmbed HTTP/vector receipt.
- `e5-http-receipt.json`: real three-case multilingual-e5 HTTP/vector receipt.
- `adaptive-acquisition-report.json`: fixed, multi-query, heuristic,
  controller/mock, local-generation, and API-generation separation.
- `NEXT_ACTIONS.md`: exact next gates and discriminating test.

Parent evidence is linked by repository-relative paths:

- `../ht-o1-local-http-20261031/`
- `../ht-research-product-20261031/`
- `../ht-research-product-continuation-20261031/`
- `../ht-o3-local-model-preflight-20261031/`

## Limits

The device cases are public-source product-disclosure engineering cases, not
semantic claim-relevance gold. Unlisted links remain unjudged. DAPFAM is a
separate citation-based retrieval diagnostic. Nothing in this package proves
clinical suitability, regulatory approval, FTO, patent validity, exhaustive
recall, investment merit, commercial adoption, publication readiness, or live
provider quality.
