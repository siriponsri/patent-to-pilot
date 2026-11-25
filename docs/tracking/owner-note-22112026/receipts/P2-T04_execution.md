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
The dr-train job stopped after the scalar replay. The P2-T04 result is NOT_RUN. Any alternative tied-cutoff rule
needs a separate owner decision and prospective freeze. The current exact gate is still in force.

## Owner-approved historic scikit-learn replay

On 25 Nov the owner chose A and approved the single Linux x86-64 CPython 3.12 scikit-learn 1.7.2 wheel from PyPI
for an isolated dr-train install. The approved wheel is `scikit_learn-1.7.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl`,
SHA-256 `e5bf3d930aee75a65478df91ac1225ff89cd28e9ac7bd1196853a9229b6adb0b`.
[PyPI release file and checksum](https://pypi.org/project/scikit-learn/1.7.2/#scikit_learn-1.7.2-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.whl).
Install the pinned wheel without dependencies to the project-specific `overlay-sklearn172/`. Import from that overlay
only in this replay. Use the original dr-train CPU dispatch and installed NumPy 2.2.6 and SciPy 1.18.1. Verify these
versions and the imported module location before starting. No pod or paid service is in scope.

Keep the frozen manifests, original 2,000-app cohort, reference rankings, all-score exact gate and progression rule.
The isolated launcher SHA-256 is `061a5b36d9d2c1ab5073795e226673289fed0f92ae02eb74cdde13e29e9cdc3c`. It runs one
CPU process group at a time and applies the 30 GiB MemAvailable guard with the same 36 GiB planning estimate. It
writes to `screen-v1-sklearn172/` with `driver-sklearn172.log`. If the gate fails, preserve the attempt and report
NOT_RUN for the matched evaluation. The original pod's CPU dispatch remains unknown.

The initial SSH transfer and install connection timed out during Tailscale startup. After the client reported
Running, the approved local wheel and launcher transferred and both matched their pinned hashes on dr-train. The
offline installation passed a CountVectorizer import and synthetic check under Python 3.12.3, scikit-learn 1.7.2,
NumPy 2.2.6 and SciPy 1.18.1 with AVX2 active. A separate import showed the existing scikit-learn 1.9.1 intact.
The guarded run started at 10:09:21 UTC on 25 Nov with both frozen digests and the launcher reverified. The host
had 123,949,788 KiB MemAvailable and 985 GB free disk. There was no concurrent project process.
