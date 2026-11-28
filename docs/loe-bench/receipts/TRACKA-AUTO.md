# TRACKA-AUTO | Prospective readout continuity

Implementation starts at `82765ec4` on `loe/TRACKA-AUTO`. The 29 November owner decision makes the custodian role best effort and accepts late readouts. The fixed UTC window ends remain 27 November 2027 and 27 November 2028. The two prospective scores are **NOT_RUN**. [Owner decision](../../maintenance/OWNER-DECISIONS-20261122.md) · [Freeze receipt](TRACKA-FREEZE.md) · [Scorer receipt](SCORER.md).

| Layer | Recovery it provides | Dependency |
| --- | --- | --- |
| [Calendar](../reminders/track-a-readouts.ics) | Bangkok reminders one week before, on, and 30 days after each maturity. The 1 November check repeats each year from 2027. | A calendar subscription or import and a client that shows event alerts. |
| [Worker and Actions](../../../ops/tracka-cron/README.md) | Daily dispatch for missing mature readouts, including after GitHub inactivity. The workflow uploads the output, posts the canonical report and retains the first scored result in the issue. `PENDING` and `BLOCKED_SOURCE` never close the retry loop. | The default-branch workflow, repository configuration, matching release pins, valid Worker credentials and eventual FDA coverage. |
| [Public score and publication guide](../HOW-TO-SCORE-TRACK-A.md#if-nobody-runs-this) | Anyone can score from the archived release even after the Worker or repository automation stops. A late result uses the original endpoint dates and records the actual scoring date. | The exact Zenodo release and OSF manifest, plus a covered FDA export or its archived bytes. |

The Worker issues an expiry warning within 45 days, checked monthly. An issues-only fallback secret can file the warning when the primary fails. When both credentials or GitHub Issues are unavailable, Cloudflare records the failed check. The workflow writes no repository files. The issue's result table persists independently of Actions artifact retention.

## Owner setup and open items

1. After Planner review and integration, publish the RELEASE-KIT on Zenodo. Copy its version DOI and the OSF update 4 freeze SHA-256 into Actions and Wrangler. Pin the scorer commit in Actions. Replace the placeholders in the calendar descriptions or point recipients to the published guide. Allow about 5 minutes for configuration once the release is published.
2. Create the two fine-grained, repository-scoped tokens, set their Worker secrets, and deploy the Worker using the [owner recipe](../../../ops/tracka-cron/README.md#owner-setup). Allow 20–25 minutes of operator time for tokens and deployment, with trigger propagation afterward. Add both token renewal dates to the calendar. Import the seven-event calendar and check it in the Bangkok timezone, about 5 minutes.
3. Confirm the first monthly invocation and subscribe to the health issue. Download the first scored 12-month artifact before its 90-day retention runs out and retain it for H3 at 24 months. A 24-month unattended run without the first archive uses the scorer's documented late reconstruction. The canonical issue survives artifact expiry and carries the aggregate report. [GitHub artifact retention](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#configuring-the-retention-period-for-artifacts-and-logs-in-your-repository).

Release placeholders `10.5281/zenodo.VERSION_ID` and `OSF_UPDATE_4_FREEZE_SHA256` deliberately remain until the public record is ready. The parallel RELEASE-KIT branch changes a different paragraph in the shared scoring guide. Planner handoff and lane memory can record these dependencies at integration. Live Worker execution, GitHub dispatch and issue publication, calendar client import, Zenodo access, and prospective outcome data collection are **NOT_RUN** for this card.

## Local verification

| Check | Evidence |
| --- | --- |
| Worker `npm test` on Node 24.19.0 | **PASS**, 11 mocked tests covering maturity, retry, inactive workflow, issue pagination, isolated dispatch failure, canonical result matching and token renewal alerts. |
| Workflow lint and publication | **PASS**, actionlint 1.7.12, Bash syntax for all four shell blocks, and six mocked issue scenarios using jq 1.8.1. The mocks exercised on-time and late scores, both retry statuses, first-result preservation, and non-canonical inputs. |
| Calendar | **PASS**, strict local checks for CRLF, 75-octet folding, component nesting, unique UIDs, Asia/Bangkok UTC+07:00, dates, recurrence, alarms, commands and links. |
| LOE-Bench `py -3.12 -m unittest discover -s loe_bench/tests -t .` | **PASS**, 261 run, 251 passed, 10 skipped. Existing Purple Book resource warnings appeared. All eight tests in `test_score_release` also passed in isolation. |
| `py -3.12 -m pytest tests/test_org_adaptive_terminology.py -q` | **PASS**, 2 tests. |
| Root `py -3.12 -m pytest --tb=short -p no:cacheprovider` | **FAIL (standing only)**, 2,760 passed, 50 skipped, 1 xfailed and the eight known SACR r2/r3 `test_budget_cannot_use_nonfinite_inflated_or_erased_cost` failures. Exit 1. |

Local workflow verification tools were downloaded outside the checkout and verified against their upstream release checksums. actionlint 1.7.12 (MIT), Windows x64 archive SHA-256 `6e7241b51e6817ea6a047693d8e6fed13b31819c9a0dd6c5a726e1592d22f6e9`. jq 1.8.1 (MIT), Windows x64 executable SHA-256 `23cb60a1354eed6bcc8d9b9735e8c7b388cd1fdcb75726b93bc299ef22dd9334`. [actionlint release](https://github.com/rhysd/actionlint/releases/tag/v1.7.12) · [jq release](https://github.com/jqlang/jq/releases/tag/jq-1.8.1).
