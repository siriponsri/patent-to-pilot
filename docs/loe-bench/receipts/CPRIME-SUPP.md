# CPRIME-SUPP | Descriptive C′ metrics

The historical C1 supplement reports pooled native-score ROC AUC and classification accuracy at the frozen threshold of calibrated `p ≥ 0.5` for B1, M1 and M3. All three arms had zero true positives at that threshold. M3 generated one false positive at 24 months. This supplement follows the [analysis note locked at `4ee32b11`](PRIORARMS-CPRIME-NOTE.md) and supersedes the `NOT_RUN` status in the [PRIORARMS receipt](PRIORARMS.md#c-supplement). The registered C1 endpoint is first final original U.S. abbreviated new drug application (ANDA) approval within the stated horizon after each annual cutoff. [Registered C′ results](SCORE.md)

## Inputs and authentication

The CPU runner authenticated both raw exports against the [SCORE receipt](SCORE.md#private-outputs-and-verification) before JSON decoding. It validated the SCORE release and horizon metadata, full roster sizes, registered January 1 cutoffs, unique `(key, cutoff)`, binary labels and finite native probabilities. It took the six original TRAIN sigmoid parameter sets from the public development config and reused SCORE's clipped native logit and logistic prediction operation.

| Input | SHA-256 | Check |
| --- | --- | --- |
| `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/score/C1_scores_12m.json` | `a644f1d40271c9a59a5405b840724906332ce975854d2afedd3d22c4ded80891` | PASS, raw bytes |
| `C:/Users/User/Desktop/myProject/_private_artifacts/loe-bench/score/C1_scores_24m.json` | `c3b9e51891fd8f577dfce9f7fbbfb466f25f29ae50ed4edd9d8b2d0fcbcc84e7` | PASS, raw bytes |
| [FROZEN_CONFIG.json](../../../loe-bench/data/FROZEN_CONFIG.json) | `d40119189b9e3b3b319f16449ac672766d46de2272dd9579eadaa8d23eb27c39` | PASS, LF bytes as specified by SCORE |

The runner fit no model, joined no source, and used no GPU or paid API. The two authenticated score exports were its only private inputs. Its sole output is the [aggregate JSON](../../../loe-bench/data/CPRIME_SUPPLEMENT.json), with SHA-256 `0bdb3e7af2469854f95cbdfd769ac9fe10763cd63722f32b6ac23a9c4ff56451` (LF bytes).

## Results

| Horizon | C1 cutoff years | Rows | Unique drugs | Event rows | Event drugs | Row prevalence |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| 12 months | 2017–2025 | 5,259 | 803 | 202 | 202 | 3.84% |
| 24 months | 2017–2024 | 4,639 | 771 | 368 | 202 | 7.93% |

| Months | Arm | Pooled ROC AUC | Accuracy at p ≥ 0.5 | Always-negative accuracy | TP / FP / TN / FN | Brier from SCORE | C-index | Comparable pairs |
| ---: | --- | ---: | ---: | ---: | --- | ---: | --- | --- |
| 12 | B1 | 0.7095 | 96.16% | 96.16% | 0 / 0 / 5,057 / 202 | 0.0373 | `NOT_ESTIMABLE` | Unavailable |
| 12 | M1 | 0.8027 | 96.16% | 96.16% | 0 / 0 / 5,057 / 202 | 0.0354 | `NOT_ESTIMABLE` | Unavailable |
| 12 | M3 | 0.8125 | 96.16% | 96.16% | 0 / 0 / 5,057 / 202 | 0.0352 | `NOT_ESTIMABLE` | Unavailable |
| 24 | B1 | 0.7262 | 92.07% | 92.07% | 0 / 0 / 4,271 / 368 | 0.0713 | `NOT_ESTIMABLE` | Unavailable |
| 24 | M1 | 0.7955 | 92.07% | 92.07% | 0 / 0 / 4,271 / 368 | 0.0654 | `NOT_ESTIMABLE` | Unavailable |
| 24 | M3 | 0.8045 | 92.05% | 92.07% | 0 / 1 / 4,270 / 368 | 0.0647 | `NOT_ESTIMABLE` | Unavailable |

ROC AUC compares native scores across pooled event and non-event rows and gives half credit to ties. Accuracy is `(TP + TN) / rows`, and always-negative accuracy is the non-event fraction. The planned C-index compares a strictly earlier observed event with a later observed time at the same cutoff, with administrative censoring at the horizon and half credit for tied native risks. The exports omit exact dates, so the pair denominators are unavailable and are recorded as JSON `null`.

## External references

**NOT head-to-head.** The studies and C′ use different endpoints, cohorts, inputs and validation designs. The C′ values refer to the fixed-horizon first final original ANDA approval results and annual rosters above. The open-input Track A adaptations are covered in [PRIORARMS](PRIORARMS.md).

| External study | External endpoint and cohort | Published metric and definition | Historical LOE-Bench C′ | Source |
| --- | --- | --- | --- | --- |
| Hu et al. 2019 and Hu's 2021 presentation | Time from the earliest lawful submission date to the first ANDA submission referencing a U.S. new chemical entity. Inputs include sales, product-specific guidance and complexity. | Random survival forest leave-one-out C-index 0.767, a time-to-submission concordance statistic from the 2021 presentation. The 2019 abstract gives no numerical performance. | Within-cutoff, horizon-restricted C-index `NOT_ESTIMABLE` for all arms at both horizons. | [2019 abstract](https://pubmed.ncbi.nlm.nih.gov/31009066/), [2021 presentation, slides 10–13](https://www.complexgenerics.org/wp-content/uploads/crcg/prsnt-Hu20210921-SBIA.pdf#page=13) |
| Hopefl et al. 2025 | Time to first ANDA submission in separate cohorts of 140 new chemical entity and 97 non-new-chemical-entity orphan drug products, each with its own origin. Inputs include IQVIA sales and FDA complexity classifications. | Random survival forest C-index for concordance on time to submission. New chemical entity / non-new-chemical-entity leave-one-product-out 0.769 / 0.736. Repeated five-fold cross-validation mean ± standard deviation 0.675 ± 0.026 / 0.754 ± 0.044. | Within-cutoff, horizon-restricted C-index `NOT_ESTIMABLE` for all arms at both horizons. | [Primary paper, §§3 and 4.2–4.3](https://ascpt.onlinelibrary.wiley.com/doi/10.1111/cts.70365) |
| Kerr & Glos 2020 | Time from new molecular entity approval to first generic approval for U.S. small-molecule new molecular entities approved in 2001–2012. Inputs include orphan indication and IQVIA sales. | Cox association hazard ratio 0.464 for products with both orphan and non-orphan indications relative to single-indication non-orphan products. | No corresponding association estimate in C′. | [Primary abstract, Methods and Results](https://doi.org/10.1007/s40290-019-00317-9) |
| Beall et al. 2018 | Quarter of first generic prescription in Medicaid for 170 top-selling small-molecule drugs that lost exclusivity during 2000–2012. The rule uses key patents and statutory exclusivities. | 42% (72/170) within one quarter of estimated entry, based on the absolute difference between observed and estimated quarters. | No corresponding quarter-error estimate in C′. Its binary classification accuracy and always-negative accuracy appear above. | [Primary paper, Table 1](https://www.valueinhealthjournal.com/article/S1098301518321545/pdf#page=4) |
| Memedovich et al. 2025 | Paragraph IV challenge in the first year of eligibility for 210 patented small-molecule drugs the FDA approved in 2007–2018. Inputs include drug and patent characteristics and sales. | Held-out test ROC AUC for ranking challenge cases above non-cases, 0.807 for random forest and 0.770 for elastic net. | Pooled ROC AUC at 12 / 24 months. B1 0.7095 / 0.7262, M1 0.8027 / 0.7955, M3 0.8125 / 0.8045. | [Primary paper, Table 2](https://journals.plos.org/plosmedicine/article?id=10.1371/journal.pmed.1004540#pmed.1004540.t002) |

## Verification and handoff

Run from the repository root with CPython 3.12.10 and the existing LOE-Bench dependencies. The `--write` flag writes the committed JSON. Without the flag the runner emits the same aggregate JSON to standard output.

```powershell
rtk proxy py -3.12 -B loe-bench/scripts/score_cprime_supplement.py --write
```

| Check | Outcome |
| --- | --- |
| `py -3.12 -m pytest tests/test_org_adaptive_terminology.py -q` | PASS, 2 tests |
| `py -3.12 -m pytest loe-bench/loe_bench/tests/test_score_cprime_supplement.py -q -p no:cacheprovider` | PASS, 7 synthetic tests covering tied scores, single-class AUC, calibration, threshold equality, confusion counts, Brier transcription, censoring, schema and digest rejection |
| `py -3.12 -m pytest --tb=short -p no:cacheprovider --basetemp <fresh-local-temp>` | FAIL, exit 1. 2,760 passed, 50 skipped, 1 xfailed, 2 warnings and the 8 standing SACR r2/r3 budget failures. |
| Reconcile against committed SCORE aggregates | PASS, both rosters and all six rounded Brier values match. The upper five SCORE calibration bins verify the number of rows called positive in each arm. Confusion counts reconcile to the full rosters. |
| Calibration implementation against the SCORE pin `f683017c` | PASS, exact Git content match for `baselines.py` and `t2.py`. |

The eight standing failures are the `nan`, `inflated`, `erased` and `insufficient` cases of `test_budget_cannot_use_nonfinite_inflated_or_erased_cost` in each SACR supervisor suite.

The stand-alone PowerShell `Get-FileHash` command was unavailable during the output check. Python `hashlib` verified the aggregate file digest shown above.

No deviation from the locked note. The main planner owns independent review, integration and updates to the lane handoff and memory.
