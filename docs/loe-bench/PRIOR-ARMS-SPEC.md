# Prior-method arms and external metrics (locked 28 November 2026)

The main planner locked this specification on 28 November 2026, before any of these arms was fitted. It implements the owner's decision of the same day: reproduce prior methods as exploratory Track A arms (route 1) and report our arms in the metrics prior studies use (route 3). A post-hoc rerun of new arms on C′ was not approved. The source is the co-planner memo of 28 November 2026 (GPT-6.2 Astra high with SciSpace), recorded in the [lane memory](MEMORY.md). [Owner decision](../maintenance/OWNER-DECISIONS-20261122.md) · [OSF registration](https://doi.org/10.17605/OSF.IO/P2SMD) · [Track A core](receipts/TRACKA-CORE.md)

## Status of the comparison

Both arms are **untested adaptations** built on open inputs. Their prospective comparison with M3 measures these implementations on the same endpoint, rows, evidence cutoff and queue budget. It does not measure how the original authors' models perform with their proprietary inputs, such as IQVIA sales, internal FDA complexity classes and product-specific guidance. These comparisons are exploratory and sit outside the registered H1–H3 family. Published values from other studies are external references only.

## Arms

| Arm | Precedent | Recipe |
|---|---|---|
| **P1-RSF-OPEN** | Hu et al. 2019 ([doi:10.1002/cpt.1479](https://doi.org/10.1002/cpt.1479)) and Hopefl et al. 2025 ([PMC12497357](https://pmc.ncbi.nlm.nih.gov/articles/PMC12497357/)), both random survival forests for first ANDA submission | Inputs: `age_years`, `oral`, `injectable`, `nce_remaining_years`, `years_to_last_patent_expiry` and the frozen missingness bit for each expiry feature. Settings: `RandomSurvivalForest(n_estimators=500, max_features="sqrt", min_samples_split=10, min_samples_leaf=5, max_depth=None, bootstrap=True, n_jobs=1, random_state=20261127)` with log-rank splits. No tuning and no out-of-bag performance claim. |
| **P2-COX-OPEN** | Kerr & Glos 2020 ([doi:10.1007/s40290-019-00317-9](https://doi.org/10.1007/s40290-019-00317-9)), Cox model of the time from NME approval to first generic approval | Inputs: `age_years`, dated `orphan`, `oral`, `injectable`, `challenge_present`, `challenge_missing`, and first-NDA approval year as one linear term. Age and year are centered and scaled on TRAIN only. Columns with zero TRAIN variance are dropped by rule. Settings: `CoxPHSurvivalAnalysis(alpha=1.0, ties="breslow", n_iter=100, tol=1e-9)` with Breslow baseline survival. No feature selection or tuning. |

Beall et al. 2018 is **not** reproduced. B3 remains the registered "all-listed-expiry rule", which belongs to the same expiry family but uses a different algorithm; never call it a Beall reproduction. Memedovich et al. 2025 ([doi:10.1371/journal.pmed.1004540](https://doi.org/10.1371/journal.pmed.1004540)) and Wittayanukorn et al. are external references only.

**Training clock and native risk.** Fit each horizon separately on exactly the mature TRAIN rows of the corresponding Track A core arm. Measure time as the elapsed days from cutoff to the first final original ANDA approval, divided by the days to that row's calendar horizon end. An event in the window has time in (0, 1]. An event-free row is administratively censored at 1. The native risk is 1 − Ŝ(1 | X) from the predicted survival function. Do not use the forest's generic `.predict()` score. Queues use unrounded native risk with the existing `floor(N/5)` rule and fractional tie credit.

**Runtime.** Use an isolated research environment pinned to CPython 3.12.10, NumPy 2.2.6, scikit-learn 1.7.2 (BSD-3-Clause) and scikit-survival 0.25.0 (GPL-3.0-or-later), with the lock file and hashes recorded. scikit-survival runs only in this environment. It is never vendored into the Apache-2.0 repository and never shipped in the product. Core scoring and paired resampling stay on the registered runtime.

**Admission.** Each arm is admitted on technical checks only, regardless of development performance. The checks are: hand-checkable fixtures for boundaries, missingness, ties and censoring; deterministic repeat fits; convergence; and finite scores for all 651 t0 rows at both horizons. An arm that fails is recorded as failed, and the ready arms freeze on schedule. A failed arm never delays the Track A freeze.

## Metrics

| Measure | Rule |
|---|---|
| Recall at 20% | The registered primary measure. Report P1 − M3 and P2 − M3 descriptively at each horizon, using 2,000 paired whole-drug bootstrap draws (PCG64, seed 20261127) with queues rebuilt in each draw. |
| ROC AUC | Report B1, M1, M3, B3, P1 and P2 at each horizon, pooled by row and computed on native scores. Tied scores get half credit, and a single-class roster is undefined. Report prevalence, rows and drugs. |
| Accuracy and Brier | B1, M1 and M3 use frozen calibrated probabilities; P1 and P2 use native survival probabilities. A row is positive when p ≥ 0.5. Report the confusion counts and the always-negative accuracy. B3 uses its binary call, and its Brier column is labelled "hard-rule Brier". |
| C-index | A horizon-restricted, within-cutoff concordance on exact event times and native horizon scores, pooled across cutoffs and reported with its comparable-pair denominator. Zero comparable pairs gives `NOT_ESTIMABLE`. This is a LOE-Bench definition, not Hu's or Hopefl's origin or follow-up. |

**Datasets.**
- **Development validation** (2012–2015 at 12 months, 2013–2014 at 24 months, trained on 2010): all six arms. Label it as development, because prior project work used these cutoffs.
- **Track A**: all six arms. The 12-month panel matures on 27 November 2027 and the 24-month panel on 27 November 2028.
- **C′ supplement**: aggregate-only AUC and 0.5-threshold accuracy for B1, M1 and M3, from the existing authenticated score exports. A dated analysis note naming every metric, threshold, score field, horizon and output must be committed before the calculation. Brier is reused from SCORE: 0.0373, 0.0354 and 0.0352 at 12 months, and 0.0713, 0.0654 and 0.0647 at 24 months. Omit the C-index on C′ if the exports lack exact event times. B3, P1 and P2 never run on C′. The planner judges this route-3 calculation, a post-hoc descriptive analysis of frozen predictions, to be within the owner's approval.

**Paper wording.** "On the common prospective LOE-Bench roster, we compared two preregistered open-input adaptations with M3 for first final original ANDA approval. These exploratory paired comparisons are outside the registered H1–H3 testing family. Published values from other studies are external references for their stated endpoints, cohorts and validation designs; differences between those values and LOE-Bench estimates do not estimate relative model performance."

## Open items

- The full text and supplement of Hu 2019 are needed to verify its cohort, final feature list and external-validation statistic. Until they are verified, attribute C-index 0.767 to Hu's 2021 presentation only. On 28 Nov 2026 the owner could not obtain the article (paywalled). The owner supplied an FDA presentation (Rantou, 2 Aug 2019, `docs/owner/prior-work/prsnt-Rantou20190802-RP.pdf`, owner-local and untracked). Its slide 1 reproduces the Hu 2019 figures:
  - **Variable importance.** It covers 27 variables, led by sales in the year before the earliest lawful submission date, product-specific guidance in that year, and complex API. It also includes 14 ATC classes, complex dosage form, acute/chronic disease, complex delivery route, days to patent expiration, drug-device combination, oral modified release and REMS.
  - **Validation.** A per-product prediction is shown for 11 products (A–K) on the first day of the earliest lawful submission date; 10 of the 11 are above 50%.
  - **No discrimination statistic.** The slide gives no C-index, so the 0.767 still comes only from Hu's 2021 presentation.
  - **Coverage of P1.** Of the 27 variables, only days to patent expiration (and, partly, route) has an open as-of counterpart in P1. This confirms that P1 adapts the method family and does not reproduce Hu's model.
- The arm list, the C-index definition and the C′ supplement go into the OSF update 4 sheet with the Track A freeze.
