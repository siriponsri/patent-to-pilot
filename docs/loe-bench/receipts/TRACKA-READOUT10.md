# TRACKA-READOUT10 executor receipt

29 November 2026. Branch `loe/TRACKA-READOUT10` starts at `3d5cba8583f17e28f61cd25ac34376e0f4dbfc1f` on `origin/research/loe-bench`. Origin confirmed protocol commit `6273e24659e0a64debd8c0c8851e988bc54d0252` before any implementation or test edits. [Protocol](TRACKA-READOUT10-PROTOCOL.md) · [External review findings](../reviews/EXTERNAL-REVIEW-R9.md#new-findings-table).

## R9-A

**PASS in executor fixtures.** At both horizons, the scored replay's `REPORT.md` gives the retained H3 estimate, 95% interval and first publication link beside the decision table. The table is labelled “current recomputation (not used for inference).” The two-edition fixtures produced the following signed contrasts in percentage points.

| Replay horizon | Changed estimate | First publication | Revised FDA edition | Retained H3 |
| --- | --- | ---: | ---: | --- |
| 12 months | H3 (M3 minus B1) | +33.33 | −3.70 | +33.33 [+20.00, +57.14], from the first 12-month panel |
| 24 months | H1 (M3 minus B1) and H2 (M3 minus M1) | +33.33 each | +2.63 each | +33.33 [+20.00, +57.14], from the first 24-month family |

The H3 estimate at 24 months still uses the 12-month panel carried by the first 24-month family. The test verified that H3 stayed the same when the revised snapshot changed the 24-month panel. At each horizon the final report matched its `run-manifest.json` SHA-256. The existing recovery tests verified the original archive bytes, and a direct fixture check confirmed that recovery names the retained H3 value without giving a recomputation table. Scoring and archive verification use the existing pinned sources. [Renderer](../../../loe-bench/loe_bench/tracka_readout.py) · [Regression](../../../loe-bench/loe_bench/tests/test_tracka_readout.py).

## R9-B

**PASS in executor verification.** The scoring guide defines `family_status` as publication and custody status. Its first-publication 12-month example records `FORMAL`, `horizon_months: 12` and `reached: false` for all three hypotheses, with H3 `DESCRIPTIVE_PENDING`. The example matched the corresponding fields from a staged synthetic 12-month publication. Structured consumers read the horizon and each hypothesis's `reached` and `decision` for inference. This guidance uses the existing JSON schema. [Scoring guide](../HOW-TO-SCORE-TRACK-A.md#read-the-outputs).

## Verification

Local Windows runtime used CPython 3.12.10 at `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe` with NumPy 2.5.4 and pytest 8.4.2. The cron suite used Node v24.19.0 and npm 12.1.0. Commands below omit the local `rtk proxy` prefix.

The targeted command was `python -m unittest -v` from `loe-bench/`, with `loe_bench.tests.test_tracka_readout.ReadoutTest.` prefixed to each method below. The pre-fix command used the first method only.

- `test_replay_report_attributes_revised_estimates_to_the_correct_edition`
- `test_cli_accepts_current_tree_with_published_source_pins`
- `test_published_source_pins_reject_a_change_to_each_file`

| Check | Result |
| --- | --- |
| Two-edition regression before implementation | **FAIL as expected.** One test ran with two failing horizon subtests on the missing table label, exit 1. A preliminary fixture run identified a rounded negative zero for the 24-month contrast. The final regression fixture uses seven added approvals at 24 months to give a nonzero changed estimate. |
| Targeted replay and source-pin tests after implementation | **PASS.** Three ran and passed in 11.592 seconds, exit 0. The installed scorer accepted all 25 published source hashes and rejected an isolated mutation to each file. |
| `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` | **PASS.** 303 ran, 293 passed and 10 skipped in 105.933 seconds, exit 0. Existing Purple Book file-handle warnings appeared. |
| `npm test` from `ops/tracka-cron/` | **PASS.** 18 ran and passed, exit 0. |
| `python -m pytest -o addopts= -q --tb=short --basetemp "$env:LOCALAPPDATA/Temp/pt-r10-6273e24"` from the repository root | **PASS under the standing exception.** 2,760 passed, 50 skipped, 1 xfailed, 8 failed and 2 warnings in 358.40 seconds, raw exit 1. The failures were `test_budget_cannot_use_nonfinite_inflated_or_erased_cost` for `nan`, `inflated`, `erased` and `insufficient` in each of `test_sacr_r2_smoke_supervisor.py` and `test_sacr_r3_smoke_supervisor.py`. |
| Source and freeze diff | **PASS.** All 25 installed source files matched the published LF-normalized SHA-256 pins. The 25 mapped paths and `loe-bench/data/` had an empty diff against the branch base. Local and origin freeze tag object `cb551bbc3031e7df10cfd676df5cd1de10317def` both peel to `6712f32cdfb1252d66e192d770deaa867808a375`. |

## Handoff

The branch is ready for Planner review and integration. The executor receipt is the record for the Planner's lane handoff and memory updates. The review can reproduce the attribution through the linked fixture and independently hash each replay's final report. Production readout, publication and deployment were `NOT_RUN`. The executor used synthetic local fixtures and accessed no protected TEST data, private artifacts or credentials. This card made no OSF or Zenodo writes and used no paid APIs or GPUs. [Published source-pin fixture](../../../loe-bench/loe_bench/tests/fixtures/zenodo-24629100-scorer-version.json).
