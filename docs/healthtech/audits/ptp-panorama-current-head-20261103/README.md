# Current-head PANORAMA component baseline

วันที่รัน: 3 พฤศจิกายน 2026 (Asia/Bangkok)

## Scope

นี่เป็น fresh deterministic CPU scoring run ของ PANORAMA PAR4PC/PI4PC ภายใต้ frozen protocol เดิมจาก benchmark-expansion continuation โดยผูกผลกับ candidate ปัจจุบัน `88dc40471cb9078f929c02bb893cfa1e364da841` ไม่รวมผลจาก candidate เก่าหรือเปลี่ยน endpoint หลังเห็น test

- Protocol: `docs/healthtech/research/DATASET_BENCHMARK_EXPANSION_PROTOCOL_20261101_TH_EN.md`
- Protocol SHA-256: `256a8b7033cb3fb1857337811fd201d063f760723dc64d11f1e2addc9505c0d7`
- Frozen source files: PANORAMA PAR4PC/PI4PC validation/test ที่มี manifest checksum เดิมผ่านครบ
- Ranking code SHA-256: `e99dbbc83edd1383df5bdef27692775a0abd69d4896f768842034b48b2f0197a`

## Results

| Task | Split | Rows | Macro hit@1 | Macro hit@8 | Singleton exact top-1 | Wall seconds | Failed rows |
|---|---:|---:|---:|---:|---:|---:|---:|
| PAR4PC | validation | 3,029 | 0.733575 | 1.000000 | 0.681583 | 19.2277 | 0 |
| PAR4PC | test | 2,896 | 0.715124 | 1.000000 | 0.697702 | 18.0915 | 0 |
| PI4PC | validation | 3,937 | 0.377699 | 1.000000 | 0.377699 | 7.9967 | 0 |
| PI4PC | test | 3,402 | 0.401235 | 1.000000 | 0.401235 | 6.4792 | 0 |

All row-level metrics keep every row in the denominator. The lexical ranker did not read `gold_answers`, `silver_answers`, or `negative_answers` while selecting an option/paragraph. Raw predictions remain in the private artifact root and are not staged in Git.

The same current-head receipt also reran the post-freeze Helmers diagnostic from the verified CC BY 4.0 archive: 10 selected targets, 450 judged pairs, 258 positive pairs, macro AP `0.8854504326`, and macro AUC `0.8800118443`. This is a selected-pool diagnostic and is not independent global gold.

## Artifact binding

The private artifact root is `healthtech/benchmark-expansion-20261101/current-head-baseline-20261103`. The machine-readable receipt records source hashes, summary hashes, prediction hashes, row counts, timings and commands without copying restricted payloads into the repository.

Current-candidate verification also passed the focused benchmark/report suite (`12 tests, 0 failures, 0 skipped`) and the full Python suite (`615 tests, 0 failures, 1 skipped`). Raw JUnit receipts are stored in this audit package.

## Claim boundary

PANORAMA test is an official component holdout for the closed-candidate option/paragraph task. It is not a final holdout for the main device-patent adaptive dossier study, not semantic device-patent gold, and not evidence of adaptive superiority, user validation, revenue, ROI or willingness-to-pay. Shared candidate IDs across official splits remain the documented diagnostic. No new dataset download, provider call, GPU job, ledger mutation, budget reset or time-window reset occurred.
