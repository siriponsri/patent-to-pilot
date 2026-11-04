# Protocol addendum: PI4PC replication of the PAR4PC ranking comparison

- Protocol ID: `ptp-wpi-pi4pc-protocol-v1`
- Parent: [`PAR4PC_RETRIEVAL_PROTOCOL_20261104_EN.md`](PAR4PC_RETRIEVAL_PROTOCOL_20261104_EN.md) (`ptp-wpi-par4pc-protocol-v1`). Everything not changed here is inherited unchanged: the methods, the validation-only selection rules, τ selection, the endpoint, the bootstrap and Holm adjustment, and the failure rule.
- Written 2026-11-04 (UTC), after the PAR4PC test results were known and before any new PI4PC method was scored on either split. The freeze file is `docs/healthtech/audits/ptp-wpi-research-package-20261104/pi4pc-freeze.json`.

## Why

Replication tests whether the PAR4PC pattern holds on a second, harder examiner-derived task: dense above BM25, fusion below dense, and the cascade matching fusion more cheaply. The hypotheses H1–H4 are carried over unchanged. They are not re-chosen after seeing PAR4PC.

## Task differences

- Source: PANORAMA PI4PC, revision `5c40de5fb1de842d3a44ec4b9f5bb9c44d47a77d`, CC BY-NC 4.0. SHA-256: validation `692032d44a48d352430b9a22abab272f08fd429688402647b5f2180e9aeb35b0`, test `fb3b5928018a0a8016f6d9ac913a00fae30f28042cfe71a9354860fccc41e10c`.
- Row: one rejected claim plus one cited prior-art document. Options are 5 paragraphs from that document. Exactly one paragraph is gold, meaning the paragraph the examiner relied on. Silver paragraphs get graded credit in nDCG only.
- Size: validation 3,937 rows / 308 applications; test 3,402 rows / 306 applications. No application appears in both splits.
- Queries: `full` = title + abstract + all claims of the application; `claim` = target claim + title + abstract. `bm25_full` reproduces the existing baseline, whose query is the raw context JSON string; this keeps the earlier receipt reproducible.
- Options: paragraph text only. Option IDs are row-scoped (`application:claim:paragraph`).
- Prior exposure: the per-row BM25 baseline was previously run on both splits (Hit@1 0.3777 validation, 0.4012 test).
- Recall@3 is computed over 5 options and nDCG@8 over all 5 options.
