# TRACKA-READOUT7 executor receipt

29 November 2026. `loe/TRACKA-READOUT7` starts at `7bc25790c74d6051ac806eb13438b3839dfbb940` on `origin/research/loe-bench`. Protocol commit `6118665af260417a1a6f263f652a1a81c3be3067` was pushed and verified on origin before implementation. [Protocol](TRACKA-READOUT7-PROTOCOL.md) · [Round 6 review](../reviews/EXTERNAL-REVIEW-R6.md).

## Findings

| Finding | Fixture result |
| --- | --- |
| R6-A | **PASS.** Ordinary replay and `--recover` both rediscover the first 12-month result for a published 24-month aggregate. Both reports date the original formal status to the verified release's publication date. They show `VERIFIED_CONSISTENT` with matching witnesses and `CURRENT_DISPUTE` after two trusted 12-month issue pins disagree. The reports identify both issues and flag custodian reconciliation. The recovered assets match the originally published files byte for byte, including the decisions. Additional cases cover `UNRESOLVED_CONTINUITY` when 12-month evidence is unavailable and `CURRENT_DISPUTE` when a currently verified result digest differs from the archived H3 reference. [Custody rule](../TRACKA-READOUT-ADDENDUM.md) · [Scoring guide](../HOW-TO-SCORE-TRACK-A.md) · [Fixtures](../../../loe-bench/loe_bench/tests/test_tracka_readout.py). |
| R6-B | **PASS.** Failed recovery with a verified capture and disputed result pins reports the discovery reason and both issue locators in `missing` and `REPORT.md`. A missing result with a verified capture reports `MISSING_ORIGINAL`. A corrupt capture reports the verification failure alongside the missing result. The missing-capture message identifies a clean lookup with no capture. [Readout](../../../loe-bench/loe_bench/tracka_readout.py) · [Fixtures](../../../loe-bench/loe_bench/tests/test_tracka_readout.py). |

## Verification

Windows runtime was CPython 3.12.10 at `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, NumPy 2.5.4, pytest 8.4.2, Node v24.19.0 and npm 12.1.0. The commands omit the local `rtk proxy` prefix.

| Command | Result |
| --- | --- |
| From `loe-bench/`, `python -m unittest discover -s loe_bench/tests -t .` | **PASS.** 300 ran, 290 passed and 10 skipped in 83.403 seconds, exit 0. The first pass ran the same counts in 88.515 seconds, exit 0. The final run adds the corrupt-capture recovery assertion. Existing Purple Book file-handle warnings appeared. |
| From `ops/tracka-cron/`, `npm test` | **PASS.** 18 passed, exit 0. |
| From the repository root, `python -m pytest -o addopts= -q --tb=short --basetemp "$env:LOCALAPPDATA/Temp/pt-r7-6118665"` | **PASS under the standing exception.** 2,760 passed, 50 skipped, 1 xfailed, 8 failed and 2 warnings in 358.66 seconds, raw exit 1. The eight failures were the SACR r2/r3 supervisor budget cases for `nan`, `inflated`, `erased` and `insufficient` in each supervisor. |
| `git diff --check` and relative Markdown link checks | **PASS.** Both exited 0. All 14 relative links in the receipts and changed guide and addendum lines resolved. |

## Handoff

The tracked freeze manifest and `tracka_statistics.py`, `tracka_release.py` and `tracka_outcomes.py` match the branch base. The `score_release.py` syntax tree matches outside the report rendering functions. The local and remote annotated freeze tag object `cb551bbc3031e7df10cfd676df5cd1de10317def` peels to `6712f32cdfb1252d66e192d770deaa867808a375`. Production readout and deployment are `NOT_RUN`. No protected TEST, sealed or private artifacts were opened. The card made no OSF or Zenodo writes and used no paid API or GPU.

The Planner owns lane handoff and memory at integration. This receipt records the executor handoff for the next external review. The promoted family records its publication-time verification. A later replay records current continuity separately so the custodian can reconcile witness disagreements while preserving the public record.
