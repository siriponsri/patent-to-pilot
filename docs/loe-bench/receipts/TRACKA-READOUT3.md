# TRACKA-READOUT3 · publication custody and H3 vintage

28 November 2026. Executor branch `loe/TRACKA-READOUT3` started at `d021b72ff0de7564b671bd8eb309699d2a8d8036` on `origin/research/loe-bench`. Protocol `9e1f7136b0f00cebedfc8860842050678ff81dbf` was committed and verified on the remote before implementation. The first maturity is 27 November 2027. All outcome and publication examples in the tests are fictional. [Protocol](TRACKA-READOUT3-PROTOCOL.md) · [External review R2](../reviews/EXTERNAL-REVIEW-R2.md).

## Decision and evidence

Use `loe_bench.tracka_readout` v`1.1.0` for the prospective readout after Planner review. Its canonical scope is the registered repository, version DOI and OSF freeze digest. Canonical discovery also checks for a previously published 24-month aggregate before fetching new FDA sources.

| Finding | Result and evidence |
| --- | --- |
| N1, R3 | **PASS, fixture.** The supplied, omitted and wrong-pin archive invocations used identical FDA bytes. Their H3 estimates were +33.33, +25.76 and +25.76 percentage points. All three were `UNVERIFIED_INPUT` and `DESCRIPTIVE_ONLY`, with `reached=false`. The canonical call reached H3 at the original +33.33 points with its original 95% interval of +20.00 to +57.14. The tests also covered a missing local directory, another repository, an absent canonical release and tag, a surviving tag and access errors. The 24-month JSON records any canonical absence under `h3_input.discovery`, with the scope, locations, UTC query times and observations. The 24-month publication pins that record as part of the aggregate. [Readout](../../../loe-bench/loe_bench/tracka_readout.py) · [Fixtures](../../../loe-bench/loe_bench/tests/test_tracka_readout.py). |
| N2, R3 | **PASS, fixture.** Release notes verified the first 12-month result when the issue was missing. Conflicting release and issue pins, a second issue with a conflicting pin, a manifest pin that disagreed with the bound asset, missing publication pins and altered asset bytes were each refused. A publication disagreement or invalid archive leaves H3 descriptive and records the disposition. [Discovery and checks](../../../loe-bench/loe_bench/tracka_vintage.py). |
| N3 | **PASS, implementation and fixture.** The workflow uses scoped first-result tags at both horizons and writes the four content digests to the release notes and issue. The fixture deleted the transient 24-month directory, restored the 12-month release and retrieved the exact original 24-month JSON, checksum, FDA manifest, report and draws without another FDA request. The result retained its H3 vintage and M3 safety finding of 12 missed clears with the original numeric upper bound and `FAIL` disposition. [Workflow](../../../.github/workflows/score-track-a.yml) · [Scoring guide](../HOW-TO-SCORE-TRACK-A.md) · [Addendum](../TRACKA-READOUT-ADDENDUM.md) · [Operations](../../../ops/tracka-cron/README.md). |

## Verification

Implementation `9faaaec45cb637d3c9f9844ce4c1473435f71108` was verified on the branch remote. Local CPython was 3.12.10 at `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, with NumPy 2.5.4. Node was v24.19.0 and npm was 12.1.0.

| Command or check | Result |
| --- | --- |
| From `loe-bench/`, `rtk proxy python -m unittest discover -s loe_bench/tests -t .` | **PASS.** 284 run, 274 passed, 10 skipped in 58.00 seconds, exit 0. The existing Purple Book fixtures emitted resource warnings. |
| From `loe-bench/`, `rtk proxy python -m unittest -v loe_bench.tests.test_tracka_readout loe_bench.tests.test_tracka_secondary loe_bench.tests.test_score_release` | **PASS.** 24 passed in 43.13 seconds, exit 0. The complete LOE-Bench suite was repeated after the final readout edits. |
| `rtk proxy npm --prefix ops/tracka-cron test` | **PASS.** 11 passed, exit 0. |
| `rtk proxy python -m pytest -o addopts= -q --tb=short --basetemp "$env:LOCALAPPDATA\Temp\ptr3-root"` | **PASS under the standing exception.** 2,760 passed, 50 skipped, 1 xfailed, 8 failed, 2 warnings in 359.59 seconds, exit 1. The eight failures were the four registered budget cases in each of `test_sacr_r2_smoke_supervisor.py` and `test_sacr_r3_smoke_supervisor.py` (`nan`, `inflated`, `erased`, `insufficient`). |
| PyYAML 6.0.3, Git Bash `bash -n` and workflow gate assertions | **PASS.** Six Bash blocks parsed. Static assertions verified the synthetic gate, default-branch and input guards, horizon-scoped tags and publication verification before issue creation. The first checker invocation indexed an unnamed step and exited 1. Using an optional step name in the checker fixed it. |
| `rtk proxy gh workflow run score-track-a.yml --repo siriponsri/patent-to-pilot --ref loe/TRACKA-READOUT3 -f synthetic=true` | **PASS.** Dispatch and `gh run watch --exit-status` returned 0. GitHub confirmed the implementation SHA, CPython 3.12.10 and 15 passing tests in 13.755 seconds. Both `select` and `readout` were skipped. [Actions run](https://github.com/siriponsri/patent-to-pilot/actions/runs/46163617027). |

## Limits and handoff

A standalone local disposition has no independent authenticator. A formal revised-vintage calculation uses a negative record produced and checked during canonical discovery. The published 24-month digest lets a custodian later authenticate and inspect that record with the original result. Ambiguous or invalid publication evidence requires recovery. A recovered aggregate is sufficient for aggregate inspection. Source-to-result replay also requires the archived FDA bytes.

Production release creation, scored issue writes, mature FDA scoring and Worker deployment are `NOT_RUN`. The protected scorer files and freeze manifest matched the branch base. The remote annotated freeze tag `cb551bbc3031e7df10cfd676df5cd1de10317def` still peeled to `6712f32cdfb1252d66e192d770deaa867808a375`. The card opened no protected TEST, sealed or private data and made no OSF write, paid API call or GPU allocation.

The next action is Planner review and integration, then the R3 external check. The Planner owns the LOE-Bench lane handoff and memory updates. This receipt provides the executor's handoff and records the operating limitation that production release and issue permissions still need verification at deployment.
