# Dataset Benchmark Expansion Protocol — 2026-11-01

Status: `ACTIVE / STAGED / SOLO COMPUTATIONAL STUDY`

This document continues the existing Patent-to-Pilot goal. It does not create a new goal, reset the R1 ledger, or reopen the participant route.

## Objective

Test whether adaptive evidence acquisition improves dossier-support quality or resource efficiency relative to fixed and simple adaptive controls when every method receives the same eligible corpus, initial evidence, action library, and accounting budget. The study is computational and reproducible; real device dossiers remain application examples, not a substitute for a benchmark, user study, or market validation.

## Source and authorization basis

- Source pack: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-o3-safety-repair-20261031/docs/healthtech/audits/pepo-dataset-benchmark-expansion-20261101/`
- Parent audit basis: `f826069dddb74d4df9ca820a33c07355bec8b357`
- Current candidate: `cd7e5d364d529a001fc51f78c217c10d7d9c8945`
- Existing DAPFAM, PatEmbed and multilingual-e5 vectors/rankings are reused. No re-download or re-embedding is allowed unless a later receipt proves the existing artifact is unavailable or invalid.
- New resource authorization: cumulative API ceiling USD100 across providers, historical ledger preserved; existing V100, concurrency 1, 8 CPU, 32 GiB RAM, and 40 GiB incremental disk; deadline 2026-11-15 23:59 Asia/Bangkok.
- Paid/API execution still requires the existing canonical ledger, current credit, route, pricing, rights-cleared outbound manifest, and writer-quiescence gates. This protocol alone is not a paid-run receipt.

## Stages

### Stage 0 — inventory and identity

Record current candidate, source/config hashes, existing vector/ranking artifact IDs, and the manifest hash. Any artifact from a different candidate or protocol is kept as historical evidence and excluded from the final PASS surface.

### Stage 1 — rights-cleared core acquisition

Acquire only these manifest entries first:

| Dataset | Use in this round | Expected file bytes | Rights boundary |
|---|---|---:|---|
| Helmers expert human-evaluation | Post-freeze relevance diagnostic | 13,962,880 | CC BY 4.0; retain attribution and source identifiers |
| PANORAMA PAR4PC/PI4PC validation+test | Development/final retrieval benchmark | 166,093,884 total | CC BY-NC 4.0; local research/evaluation only unless separately cleared |

Store raw payloads outside Git. Write acquisition timestamp, URL, response metadata, byte count, checksum, source revision, and local path to the private receipt. Do not download DAPFAM or existing vector assets again.

### Stage 2 — integrity and schema gate

Reject or quarantine a file when the expected size or checksum fails. Inspect archive members without extracting the full corpus. For Parquet, record row count, column names, logical types, nullability where available, and a small non-sensitive sample summary. Do not use labels, qrels, or answer-derived fields to select a method before the development/final freeze.

### Stage 3 — development protocol freeze

Before final scoring, write `FINAL_EVALUATION_FREEZE.json` containing:

- eligible queries/applications/entities and exclusion reasons;
- canonical group key and family/application overlap rules;
- validation/development and final test assignments;
- primary endpoint, K, secondary endpoints, uncertainty unit, and missing/failure denominator;
- fixed, fixed multi-query, simple adaptive, and bounded LLM control definitions;
- equal evidence/action/query/retry budget and cost accounting;
- seed, software/model revisions, tokenizer/config hashes, and stop conditions.

For PANORAMA, use the official validation split for development and the official test split as untouched final holdout. If canonical application/patent-family overlap is detected across splits, freeze the documented group-level reassignment or exclude the contaminated unit before scoring. Do not invent negatives from unjudged candidates.

### Stage 4 — offline baselines and calibration

Run existing CPU/BM25 and ranking analysis first. Then measure only the new representation or controller factors required by the frozen question. Preserve failed queries, duplicate IDs, missing text, truncation, retries, and cost. The first comparison should reuse existing vectors/rankings wherever the task permits.

### Stage 5 — final evaluation and paired generation

Run final holdout only after Stage 3 is frozen. Use the same candidate universe, evidence order, generator schema and accounting for all policies. Local/API comparisons are system-configuration comparisons, not causal claims about model size or deployment. A paid branch remains separate until canonical journal, credit, price, route, rights, and ledger gates all pass.

### Stage 6 — manuscript and WPI package

Bind every table and figure to the final candidate and freeze manifest. Report positive and negative runs, uncertainty limits, rights, machine versus human time, external business validation as `NOT_VALIDATED`, and the exact data/code availability route. Do not claim revenue, willingness-to-pay, ROI, independent user validation, or journal acceptance.

## Primary analysis rule

The primary comparison is quality at a fixed resource budget. Cost-quality frontier and machine time are secondary. If the number of independent groups is too small or labels are incomplete, report descriptive results and `NOT_ESTIMABLE`; do not manufacture significance or treat agent/model-judge scores as semantic gold.

## Current status and next action

- Stage 0: `READY`
- Stage 1: `READY_FOR_CORE_DOWNLOAD`
- Stage 2: `NOT_RUN`
- Stage 3: `NOT_FROZEN`
- Stage 4: `NOT_RUN`
- Stage 5: `BLOCKED_UNTIL_FREEZE_AND_LIVE_GATES`
- Stage 6: `PARTIAL / OWNER REVIEW`

Next action: acquire and verify Helmers human subset and the four pinned PANORAMA validation/test files, then write the acquisition receipt and schema report before touching final evaluation.
