# TRACKA-READOUT4 · first published family and issue witnesses

28 November 2026. Executor branch `loe/TRACKA-READOUT4` started at `d998c9335e559442d9e0897b2e289d833c853776` on `origin/research/loe-bench`. Protocol `719ad13cbdde34c56fd36c39d72d2915229e9610` was committed and verified on the remote before implementation. The first maturity is 27 November 2027. The tests use fictional outcomes and publication records. [Protocol](TRACKA-READOUT4-PROTOCOL.md) · [External review](../reviews/EXTERNAL-REVIEW-R3.md).

## Findings

| Finding | Implementation and evidence |
| --- | --- |
| R3-A | **PASS in fixtures.** With a fixed first 12-month publication, the two eligible caller-snapshot inputs flipped the underlying H1 calculation from PASS to FAIL and changed whether H3 was reached. Both families were `PROVISIONAL`, with no formal step reached. With documented 12-month absence, the same two-invocation probe used `REVISED_VINTAGE` and produced different H3 estimates while both families stayed `PROVISIONAL`. The live-fetch fixture prepared the first pinned bundle at each horizon. Once the fixture published that bundle, the next live run and a caller-snapshot run reported `REPLAY`, compared the aggregate, and could not prepare another bundle. The 24-month replay showed the published H1 PASS alongside the replay FAIL. The same FDA bytes produced no hypothesis or source-file differences. A blocked FDA request and a recovery-only run each retained the verified archive and recorded why comparison was unavailable. [Readout](../../../loe-bench/loe_bench/tracka_readout.py) · [Fixtures](../../../loe-bench/loe_bench/tests/test_tracka_readout.py). |
| R3-B | **PASS in fixtures.** With the 12-month release and exact tag absent, agreeing trusted issue pins permitted `REVISED_VINTAGE`. Conflicting result pins, conflicting FDA-manifest pins, a malformed manifest pin and a missing result pin each gave `DISPUTED`, descriptive H3 and ineligibility for first 24-month publication. Each record retained both issue locators and the available validated pins, including the later issue after a malformed earlier pin. Release-notes-only recovery, release-present conflict detection and 24-month recovery remained covered. [Witness reader](../../../loe-bench/loe_bench/tracka_vintage.py) · [Fixtures](../../../loe-bench/loe_bench/tests/test_tracka_readout.py). |

The registered default-branch workflow scores fresh FDA bytes, checks that the current horizon has no surviving publication witness and publishes a separate pinned bundle. The self-service guide describes provisional scoring, replay and recovery. The publication step keeps the verified first aggregate when a later run differs. [Workflow](../../../.github/workflows/score-track-a.yml) · [Guide](../HOW-TO-SCORE-TRACK-A.md) · [Addendum](../TRACKA-READOUT-ADDENDUM.md) · [Worker operations](../../../ops/tracka-cron/README.md).

## Verification

Implementation `095968ac9cd196ef7ce98180f536674ea03ac23d` was verified on the branch remote. Local runtime was CPython 3.12.10 at `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, NumPy 2.5.4, Node v24.19.0 and npm 12.1.0. The workflow syntax check used PyYAML 6.0.3 and Git Bash.

| Check | Result |
| --- | --- |
| From `loe-bench/`, `rtk proxy python -m unittest discover -s loe_bench/tests -t .` | **PASS.** 289 run, 279 passed and 10 skipped in 99.169 seconds, exit 0. Existing Purple Book resource warnings appeared. An earlier full run before adding the scoped-tag rejection regression ran 288 tests with 10 skips in 115.201 seconds, exit 0. |
| `rtk proxy npm --prefix ops/tracka-cron test` | **PASS.** 11 passed, exit 0. |
| `rtk proxy python -m pytest -o addopts= -q --tb=short --basetemp C:\Users\User\AppData\Local\Temp\pt-r4-dd5fe4` | **PASS under the standing exception.** 2,760 passed, 50 skipped, 1 xfailed, 8 failed and 2 warnings in 375.17 seconds, exit 1. All eight failures matched the standing SACR r2/r3 supervisor budget exception. Both files failed the `nan`, `inflated`, `erased` and `insufficient` cases. |
| PyYAML parse, Git Bash `bash -n` and workflow gate assertions | **PASS.** All six Bash blocks parsed, exit 0. The assertions checked synthetic isolation, default-branch publication, live-only score arguments, the eligibility gate and verification before an issue write. |
| `rtk proxy gh workflow run score-track-a.yml --repo siriponsri/patent-to-pilot --ref loe/TRACKA-READOUT4 -f synthetic=true`, followed by `gh run watch 46165897749 --exit-status` | **PASS.** Dispatch and watch each exited 0. The Ubuntu runner used the workflow's pinned CPython 3.12.10 and ran `python -m unittest -v loe_bench.tests.test_tracka_readout loe_bench.tests.test_tracka_secondary`. All 20 tests passed in 52.147 seconds at the implementation SHA. GitHub marked `select` and `readout` skipped. [Actions run](https://github.com/siriponsri/patent-to-pilot/actions/runs/46165897749). |

## Limits and handoff

Production release creation, issue writes, mature FDA scoring and Worker deployment are `NOT_RUN`. The four primary scorer modules and freeze manifest matched the branch base. The remote freeze tag object `cb551bbc3031e7df10cfd676df5cd1de10317def` still peeled to `6712f32cdfb1252d66e192d770deaa867808a375`. This card opened no protected TEST, sealed or private data and made no OSF write, paid API call or GPU allocation.

The Planner owns the lane handoff and memory. Use this receipt to record the implementation at integration and route the card to the external reviewer. Production permissions and the first live publication still require verification after owner deployment and maturity.
