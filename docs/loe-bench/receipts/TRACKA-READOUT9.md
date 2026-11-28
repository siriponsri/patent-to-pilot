# TRACKA-READOUT9 executor receipt

29 November 2026. Branch `loe/TRACKA-READOUT9` starts at `0bebf6ce9f7039073f70e4535b48cde960fed129` on `origin/research/loe-bench`. The protocol commit `fbc03f99ea0016a41209d689f3615be04f30028c` was confirmed on origin before the implementation and regression edits. [Protocol](TRACKA-READOUT9-PROTOCOL.md) · [Finding R8-A](../reviews/EXTERNAL-REVIEW-R8.md#new-findings-table).

## R8-A

**PASS in executor verification.** The first published 12-month report, ordinary replay and recovery identify the verified first panel as descriptive only and retained for later H3 use. They state that H3 can be tested at the 24-month readout, on or after 27 November 2028, only if both H1 and H2 pass. The synthetic first publication reproduced the pre-fix wording and kept the expected `PENDING`, `PENDING`, `DESCRIPTIVE_PENDING` decisions after the fix. At 24 months, first publication retains the formal decision wording and replay and recovery retain the original UTC publication date and the current 12-month witness check. The fixtures covered `VERIFIED_CONSISTENT`, `CURRENT_DISPUTE` and `UNRESOLVED_CONTINUITY`.

The change is in the unpinned integrated renderer. The archive readers still use the existing `family_status` field in `results.json` as their custody marker. Scoring, replay and recovery reports match their run manifests. The published report is a member of the attested result bundle and recovery preserves its exact bytes. The addendum now describes each horizon's role. The scoring guide already places formal decisions at 24 months. [Renderer](../../../loe-bench/loe_bench/tracka_readout.py) · [Regression tests](../../../loe-bench/loe_bench/tests/test_tracka_readout.py) · [Addendum](../TRACKA-READOUT-ADDENDUM.md) · [Scoring guide](../HOW-TO-SCORE-TRACK-A.md#read-the-outputs).

## Verification

Local Windows runtime used CPython 3.12.10 at `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, NumPy 2.5.4, pytest 8.4.2, Node v24.19.0 and npm 12.1.0. Commands omit the local `rtk proxy` prefix.

The targeted command ran from `loe-bench/` with the following methods of `loe_bench.tests.test_tracka_readout.ReadoutTest` passed by fully qualified name to `python -m unittest -v`.

- `test_cli_accepts_current_tree_with_published_source_pins`
- `test_published_source_pins_reject_a_change_to_each_file`
- `test_12_month_publication_replay_and_recovery_are_descriptive`
- `test_fresh_24_month_publication_stages_with_registered_scope`
- `test_24_month_replay_and_recovery_report_current_witnesses`

| Check | Result |
| --- | --- |
| Targeted 12-month regression before implementation | **FAIL as expected.** One ran, one failed on the first publication's use of “formal,” exit 1. |
| Targeted verification after implementation | **PASS.** Five ran and passed in 25.243 seconds, exit 0. The published-pin tests accepted all 25 installed sources and rejected a mutation to each isolated copy. |
| `python -m unittest discover -s loe_bench/tests -t .` from `loe-bench/` | **PASS.** 302 ran, 292 passed and 10 skipped in 99.559 seconds, exit 0. The existing Purple Book file-handle warnings appeared. |
| `npm test` from `ops/tracka-cron/` | **PASS.** 18 ran and passed, exit 0. |
| `python -m pytest -o addopts= -q --tb=short --basetemp "$env:LOCALAPPDATA/Temp/pt-r9-fbc03f9"` from the repository root | **PASS under the standing exception.** 2,760 passed, 50 skipped, 1 xfailed, 8 failed and 2 warnings in 362.12 seconds, raw exit 1. The failures were `test_budget_cannot_use_nonfinite_inflated_or_erased_cost` for `nan`, `inflated`, `erased` and `insufficient` in each of `test_sacr_r2_smoke_supervisor.py` and `test_sacr_r3_smoke_supervisor.py`. |
| `git diff --check 0bebf6ce` and relative Markdown link check | **PASS.** The diff check exited 0 and all 14 relative file targets resolved. |

## Handoff

All 25 paths in the published source map have an empty diff from the branch base. The branch diff contains only the card's renderer, test and documentation paths. The local and remote freeze tag object `cb551bbc3031e7df10cfd676df5cd1de10317def` both peel to `6712f32cdfb1252d66e192d770deaa867808a375`. Tests used local fixtures. Live publication, deployment and DOI access were `NOT_RUN`. The card accessed no protected TEST data, private artifacts or credentials. It made no OSF or Zenodo writes and used no paid API or GPU.

Planner review and integration are pending. Use this receipt for the lane handoff and memory update. Keep publication prose specific to the horizon when changing the shared renderer, and verify report digests after rendering. [Published metadata fixture](../../../loe-bench/loe_bench/tests/fixtures/zenodo-24629100-scorer-version.json).
