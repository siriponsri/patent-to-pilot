# WPI research package — continuation of 4 November 2026

- Run ID: `ptp-wpi-research-package-20261104`
- Plan: [PTP_JOURNAL_LONG_RUN.md](../../long-runs/PTP_JOURNAL_LONG_RUN.md), with the owner amendments of 4 November 2026: E2 allowance USD 10 cumulative, push to `origin/main` allowed after a verified package, dr-train V100 compute.
- Checkout: existing `main`. Start HEAD `85f7b72`, clean. Preregistration commit `ff603bb`. No worktree, reset or ledger change.
- Paid calls this round: **0**. GPU: about 1,204 s of V100 encoding on dr-train (289 s for PAR4PC and 915 s for PI4PC) under the existing approved slot and lock. No jobs remain running.
- Commits: `ff603bb` (PAR4PC freeze), `9325185` (PAR4PC results), `1665075` (PI4PC freeze), then the PI4PC results commit.

## Outcome by work package

| WP | Result | Evidence |
|---|---|---|
| WP0 Reconcile | Current state inventoried; plan merged into GOAL, PLAN and HANDOFF | [EVIDENCE_GAP_MATRIX.md](EVIDENCE_GAP_MATRIX.md) |
| WP1 Canary quality | 9/9 findings literally match the supplied FDA fields; all hashes and generation IDs reconcile; no extra inference, no missing rows; all 3 calls reconciled provider-side | [canary-content-audit.json](canary-content-audit.json) |
| WP2 Research design | Primary contribution narrowed to claim-level prior-art ranking with examiner-cited labels (Track A); device dossier kept as application demonstration (Track B) | [protocol](../../research/PAR4PC_RETRIEVAL_PROTOCOL_20261104_EN.md), [claims matrix](CLAIMS_EVIDENCE_MATRIX.md) |
| WP3 Data and labels | Label provenance and eligibility recorded for every source | [DATASET_QRELS_PROVENANCE.json](DATASET_QRELS_PROVENANCE.json) |
| WP4 Benchmark | Frozen validation selection, then one test run: 8 methods, 2,896 rows, 222 applications, 0 failures | [freeze](par4pc-freeze.json), [results](par4pc-test-results.json) |
| WP5 Robustness | Exploratory subgroups and a top-1 error table, labelled not preregistered | [subgroups](par4pc-exploratory-subgroups.json) |
| WP6 Reproducibility | BM25 test Hit@1 reproduces the earlier receipt exactly (0.7151243); vector hashes match between dr-train and Windows | [EXPERIMENT_REGISTRY.json](EXPERIMENT_REGISTRY.json) |
| WP7 Manuscript | Abstract, RQs, Track A methods/results and limitations rewritten from these artifacts | [manuscript](../../research/MANUSCRIPT_ADAPTIVE_EVIDENCE_ACQUISITION_EN.md) |
| WP8 Readiness | Separate readiness dimensions; Guide for Authors still HTTP 403 | [READINESS.md](READINESS.md) |

## Track A test results (PANORAMA PAR4PC, frozen protocol, application-macro)

| Method | MRR | Hit@1 | Recall@3 | nDCG@8 |
|---|---:|---:|---:|---:|
| BM25-full (existing baseline) | 0.8447 | 0.7292 | 0.8966 | 0.9048 |
| BM25-claim | 0.8692 | 0.7686 | 0.9135 | 0.9176 |
| e5-full | 0.9066 | 0.8322 | 0.9442 | 0.9447 |
| e5-claim | 0.9070 | 0.8359 | 0.9406 | 0.9462 |
| PatEmbed-full | 0.9390 | 0.8871 | 0.9654 | 0.9691 |
| **PatEmbed-claim (selected on validation)** | **0.9329** | 0.8754 | 0.9645 | 0.9668 |
| Hybrid RRF (BM25-claim + PatEmbed-claim) | 0.9129 | 0.8373 | 0.9592 | 0.9492 |
| Cascade (τ = 0.2738, 57.0% escalated) | 0.9109 | 0.8367 | 0.9433 | 0.9450 |

Preregistered paired contrasts on MRR, using an application cluster bootstrap with 10,000 resamples and Holm adjustment over C1–C3:

| Contrast | Δ MRR | 95% CI | Holm p | Hypothesis |
|---|---:|---|---:|---|
| C1 dense − BM25-full | +0.0882 | [+0.0578, +0.1196] | < 0.0001 | H1 supported |
| C2 hybrid − BM25-full | +0.0682 | [+0.0446, +0.0924] | < 0.0001 | H2 supported |
| C3 hybrid − dense | −0.0200 | [−0.0377, −0.0037] | 0.018 | **H3 not supported: fusion hurt** |
| C4 cascade − hybrid | −0.0020 | [−0.0076, +0.0031] | — | H4 met: within −0.01 tolerance; 43% fewer dense query encodings |

**Negative or mixed findings, reported as such.**

- Fixed RRF fusion with the weaker lexical ranker was worse than dense alone.
- The adaptive cascade saved dense query work only relative to the hybrid. It did not beat the strongest fixed policy, dense alone (0.9109 vs 0.9329).
- On test, PatEmbed-full scored slightly above the validation-selected PatEmbed-claim. The selection was not changed.

`p < 0.0001` means no bootstrap resample crossed zero; that is the resolution limit of 10,000 resamples.

## Replication on PI4PC (paragraph level, separate freeze at commit `1665075`)

Same methods and selection rules ([addendum](../../research/PI4PC_REPLICATION_PROTOCOL_20261104_EN.md)). On validation, the rules selected BM25-claim, e5-claim as the dense ranker, and τ = 0.0735. Test: 3,402 rows, 306 applications, 0 failures. BM25-full row-micro Hit@1 0.4012346 reproduces the earlier receipt exactly.

| Method | MRR | Hit@1 | Recall@3 | nDCG |
|---|---:|---:|---:|---:|
| BM25-full | 0.6298 | 0.4080 | 0.8296 | 0.7584 |
| BM25-claim | 0.6252 | 0.3971 | 0.8314 | 0.7527 |
| PatEmbed-full | 0.6074 | 0.3786 | 0.8072 | 0.7424 |
| PatEmbed-claim | 0.6228 | 0.3986 | 0.8120 | 0.7518 |
| e5-full | 0.6017 | 0.3731 | 0.7981 | 0.7375 |
| **e5-claim (selected)** | 0.6327 | 0.4144 | 0.8295 | 0.7564 |
| Hybrid RRF | **0.6467** | 0.4289 | 0.8415 | 0.7675 |
| Cascade (19.1% escalated) | 0.6339 | 0.4091 | 0.8312 | 0.7594 |

| Contrast (MRR) | Δ | 95% CI | raw p | Holm p | Reading |
|---|---:|---|---:|---:|---|
| C1 dense − BM25-full | +0.0028 | [−0.0166, +0.0220] | 0.79 | 0.79 | **H1 not replicated**: no detectable difference |
| C2 hybrid − BM25-full | +0.0169 | [+0.0017, +0.0318] | 0.030 | 0.061 | Small gain; not significant after Holm |
| C3 hybrid − dense | +0.0140 | [+0.0027, +0.0257] | 0.014 | 0.042 | **Opposite direction to PAR4PC**: fusion helped |
| C4 cascade − hybrid | −0.0128 | [−0.0235, −0.0025] | — | — | **H4 failed**: outside the −0.01 tolerance |

**Cross-task reading.** The dense advantage seen when ranking whole candidate documents (PAR4PC) did not carry over to choosing the examiner's paragraph within one cited document (PI4PC). There, lexical evidence stayed competitive and rank fusion was the best fixed policy. Whether fusion helps or hurts depends on the task. The margin cascade traded quality for cost on PI4PC. GPU encoding for PI4PC took about 915 V100-seconds; no paid calls were made.

## Engineering checks

- Full Python suite on the final working tree (preregistration commit `ff603bb` plus this round's docs and analysis script): `python -m pytest -p no:cacheprovider -o addopts="" -q` gave **711 passed, 1 skipped, exit 0**, in 30 s.
- The new fixture tests (`tests/test_par4pc_study.py`, `tests/test_healthtech_content_audit.py`) are part of that run.
- JSON artifacts parse. No raw PANORAMA text, vectors, per-row outputs, generated text or credentials are committed.

## Boundaries

- Examiner citations are incomplete proxy labels. Closed eight-option ranking is not open-corpus search. PatEmbed may have seen USPTO citation data in training (PatenTEB multi-task). Treat C1 as possibly contamination-inflated.
- PANORAMA (CC BY-NC 4.0) and PatEmbed (CC BY-NC-SA 4.0) are used for local non-commercial research only. Raw text, vectors and per-row outputs stay in `%USERPROFILE%/Desktop/myProject/_private_artifacts/healthtech/ptp-wpi-par4pc-20261104/`. Git holds aggregates and hashes.
- Track A says nothing about medical-device linkage, FTO, validity or clinical matters. Track B remains a small descriptive application study (3 effective groups, `NOT_ESTIMABLE` uncertainty).
- E2 allowance raised to USD 10 by the owner. The ledger's epoch code still enforces USD 1 (USD 0.99945484 left). No paid work was needed this round, so the ledger was not changed. See [NEXT_ACTIONS.md](NEXT_ACTIONS.md).
