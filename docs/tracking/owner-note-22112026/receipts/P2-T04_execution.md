# P2-T04 execution, 25 Nov 2026

The screen was frozen and published in `d46ac2aa`. Attempt 1 started at 00:40:48 UTC on dr-train, with one guarded
CPU process. It stopped at 00:53:13 UTC when the archived BM25-full reproduction differed on the first frozen app,
`13200810`. No matched ranking was written and the evaluator did not start. Wall time was 12 min 25 s and peak RSS
was 6,101,628 KiB. The 30 GiB MemAvailable guard did not trigger. Spend was USD 0.

The original lexical run used NumPy 2.2.6, SciPy 1.18.1 and scikit-learn 1.7.2. The first attempt used the same
NumPy and SciPy versions and scikit-learn 1.9.1. The exact archive gate is still required. The difference's cause
remains unverified. Keep the original cohort, reference rankings and progression rule frozen.

Attempt evidence is in `driver.log` and `screen-v1/` under `/data/ptp-paper2/p2t04-run-prep-20261124`.
