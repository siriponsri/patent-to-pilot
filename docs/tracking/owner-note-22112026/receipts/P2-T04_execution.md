# P2-T04 execution, 25 Nov 2026

The screen was frozen and published in `d46ac2aa`. Attempt 1 started at 00:40:48 UTC on dr-train, with one guarded
CPU process. It stopped at 00:53:13 UTC on the first archived BM25-full mismatch, at position 214 of the frozen
order (`13200810`). The first 213 apps matched. No matched ranking was written and the evaluator did not start.
Wall time was 12 min 25 s and peak RSS
was 6,101,628 KiB. The 30 GiB MemAvailable guard did not trigger. Spend was USD 0.

The original lexical run used NumPy 2.2.6, SciPy 1.18.1 and scikit-learn 1.7.2. The first attempt used the same
NumPy and SciPy versions and scikit-learn 1.9.1. The exact archive gate is still required. The difference's cause
remains unverified. Keep the original cohort, reference rankings and progression rule frozen.

Attempt evidence is in `driver.log` and `screen-v1/` under `/data/ptp-paper2/p2t04-run-prep-20261124`. The driver
log, runtime log and time receipt were pulled and independently hash-verified under
`../_private_artifacts/p2t04-preflight-20261124/screen-v1-attempt-1/`. A gate-only diagnostic was restarted at
01:00:12 UTC to target the first failing app. It runs one guarded CPU process and does not read evaluator inputs.

## Cutoff diagnosis and bounded replay

The diagnostic completed at 01:10:22 UTC. Its logs are hash-verified locally in
`../_private_artifacts/p2t04-preflight-20261124/diagnostics-v2/`. The index contained the original 552,405 terms and 1,000,000 units.
The archived and rebuilt top 999 were identical in order and displayed score. At rank 1,000 the displayed score
was 231.1284 on both runs and the selected unit differed. The result was the same with single-query scoring and
with the original 64-query batch shape. A synthetic cutoff tie on this host produced different selected sets
with and without AVX2 at the same cutoff. [NumPy's 2.2.6 build defines AVX2 and AVX512 paths for argselect](https://github.com/numpy/numpy/blob/v2.2.6/numpy/_core/meson.build#L755-L767).
The earlier RunPod CPU instruction set was not recorded.

Use one CPU-only replay on the same dr-train installation with `NPY_DISABLE_CPU_FEATURES=AVX2` to test the scalar
argpartition path, leaving the data, runtime/evaluator digests, gate and progression criteria as frozen. The replay
must match all 2,000 archived BM25 lists and scores before matched retrieval and evaluation. Preserve prior artifacts
and use `screen-v1-scalar/` and `driver-scalar.log`. Launcher SHA-256 is
`090718e5842d93d10913303336b4a2cf4906c781c7c2db638441674f5e08a5ca`. One CPU process group at a time, with the same
30 GiB memory floor and 36 GiB upper planning estimate. This replay does not require downloading a dependency.

The replay ran from 01:13:41 to 01:26:02 UTC and failed the same exact gate at app `13200810`. Runtime was 12 min
20 s, with peak RSS 6,098,120 KiB and no memory abort. No matched rankings or metrics were produced. The driver,
runtime log and time receipt were pulled and hash-verified in `../_private_artifacts/p2t04-preflight-20261124/screen-v1-scalar/`.
The dr-train job is stopped. The P2-T04 result is NOT_RUN. An exact retry with the historic scikit-learn 1.7.2
wheel requires explicit download approval. Any alternative tied-cutoff rule needs a separate owner decision and
prospective freeze. The current exact gate is still in force.
