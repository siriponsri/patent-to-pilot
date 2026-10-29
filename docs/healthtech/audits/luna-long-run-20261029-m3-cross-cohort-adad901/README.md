# HealthTech M3 cross-cohort frontier audit

- Run ID: `luna-long-run-20261029-m3-cross-cohort-adad901`
- Base commit: `adad9017f86e995abd2b943d50a00718961f4627`
- Candidate commit: `37a3b2df25cf05bbffc2b5800c2458f20726c613`
- Scope: deterministic offline comparison of the Abbott and Boston Scientific WATCHMAN development frontiers
- Verdict: `PASS_OFFLINE_ANALYSIS`
- Provider calls: `0`
- Paid cost: `$0`
- Working-tree rule: unrelated owner and paused Claude artifacts were preserved

## Implemented

- Added `scripts/healthtech/compare_cross_cohort.py`, which validates the shared HT-B0a/B0b/B1/B2/B3 method set and fixed-prefix contract, records source hashes, computes per-method recall/resource deltas, and flags cohort-specific ceiling/group limitations.
- Added `tests/test_healthtech_cross_cohort.py` with real-artifact regression coverage and a method-set drift failure case.
- Generated `comparison.json`, `REPORT.md`, and `verification.json` from the current local Abbott and Boston artifacts.

## Findings

- Abbott: 3 devices, 41 patents, 61 disclosed pairs, 62 unjudged distractor pairs, 2 exact-patent groups, 1 company group, no final holdout.
- Boston Scientific WATCHMAN: 2 devices, 7 patents, 13 disclosed pairs, 1 unjudged distractor pair, 1 exact-patent group, 1 company group, no final holdout.
- The same five offline methods and fixed-prefix alignment contract are present in both frontiers; all source frontiers report zero failures.
- Boston reports `1.0` recall@20 for every method, but `K=20` exceeds its seven-patent candidate universe. This is ceiling-limited development evidence, not method superiority.
- Abbott has the more informative within-cohort spread at `K=20`; HT-B0b is highest at `0.6622417082775139` in this slice. Cross-cohort score deltas are descriptive only and are not pooled or treated as generalization estimates.

## Verification

- `rtk proxy python -m pytest -q tests/test_healthtech_cross_cohort.py` -> `2 passed`.
- `rtk proxy powershell -NoProfile -Command '$env:PYTHONPATH="src"; python -m pytest -q'` -> full suite passed.
- `rtk proxy python -m compileall -q scripts/healthtech/compare_cross_cohort.py tests/test_healthtech_cross_cohort.py` -> completed successfully.
- Real comparison command -> `PASS` with zero validation issues; see `verification.json`.
- Input SHA-256 values for both cohorts, frontiers, splits, distractors, and receipts are recorded in `comparison.json`.
- No provider calls, paid inference, credential reads, dataset transfer, or external publication occurred.

## Limits

- Both cohorts are development-only with no final holdout; confidence intervals, significance testing, company-held-out sensitivity, and family-held-out sensitivity are not estimable.
- Product-level disclosed links are not expert semantic claim relevance and do not establish clinical suitability, FTO, patent validity, or investment merit.
- Unjudged distractors are not negative labels; family identity is unknown and was not inferred from overlap.
- Resource values are realized local units, not dollars.

See `REPORT.md` for the research synthesis, `comparison.json` for machine-readable results, and `verification.json` for the execution boundary.
