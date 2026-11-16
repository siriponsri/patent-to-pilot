# P2-OA step R1: eligible tasks, temporal splits and corpus size

Status: RULE DECLARED, NOT YET RUN (2026-11-16). Results will be added below the rule.

No retrieval, no model, no text, no new download. CPU only. Script: [`oa_temporal_splits.py`](oa_temporal_splits.py).

## Task definition (merged plan 3.1, made exact)

- One task = one US application. Its office action is the **earliest non-final rejection** (`document_cd = CTNF`) in the OA Research Dataset 2017, ordered by (mail date, ifw number).
  - The dataset only holds application series 12-15, so this is the first non-final rejection the application received, provided it was mailed before the dataset ends (mid-2017).
- It must be mailed 2008-01-01 to 2017-12-31.
- K(q) = the distinct US documents cited **in that action** with `citation_in_oa = 1` and `action_type` 102 or 103.
  - Foreign or unparsed cited art is counted but cannot enter K.
- Eligible if all four hold:
  - |K| ≥ 3;
  - the application has an IPC;
  - at least one K document is OUT under IPC3 (no shared IPC3 with the application; the cited side needs an IPC);
  - a filing date is known.
- If the first non-final rejection does not qualify, the application is not a task. A later action is never searched for, so the task set is not selected on its labels.

## Cut-point rule (declared before the first run; no retrieval number exists)

Facts seen before this rule was written:
- the dataset holds application series 12-15 only;
- office actions per mail year: 2008: 6,837; 2009: 66,926; ... 2016: 748,472; 2017: 178,408 (half year).

The eligible-task histograms below had not been computed when the rule was written.

| # | Rule |
|---|---|
| R1 | Temporal key = application filing date from PatentsView (pre-grant record first, else grant record). |
| R2 | Observation completeness per filing year Y: c(Y) = share of series 12-15 applications filed in Y (known to PatentsView) that have at least one CTNF in the dataset. Y is **complete** if its denominator is ≥ 10,000 and c(Y) ≥ 0.9 × max c. Incomplete years are excluded from every split and reported. They are right-censored by the mid-2017 end of the data, or only partly covered by series 12-15. |
| R2a | Only the contiguous run of complete years ending at the newest complete year is used. |
| R3 | **P3-TEST** = the newest complete year. It is extended backward by whole years until it holds ≥ 1,000 eligible tasks. |
| R4 | **P2-TEST** = the next older block of whole years, built the same way (≥ 1,000). |
| R5 | **DEV** = all remaining older years of that run. |
| R6 | A test window is a pool. The evaluated test sample is the first n tasks of the window, ordered by sha256(`p2-oa-split-v1|` + app_id). n is fixed later by the MDE rule of the pre-declaration. Corpus size is therefore reported per window **and** for n = 1,000 / 2,000 / 5,000. |

Why completeness and not only size:
- A window of ≥ 1,000 tasks is easy to reach; each filing year has tens of thousands.
- The binding problem is right-censoring. Applications filed in 2015-2016 appear only if they got their first action before mid-2017.
- That keeps fast art units and drops slow ones, so a test window made of censored years would not be a fair sample.

## Encoding-cost scale

Measured on DAPFAM (stage 0, 2026-11-05), PatEmbed-large fp32 on the V100:
- 188,944 passages from 45,336 families took **5,182 s (1.44 h)**, i.e. 36.5 passages/s and 4.17 passages per family.
- The merged plan's "well under 1 h" was wrong; the estimates below use the measured rate.
- fp16 has not been measured.
