# TRACKA-READOUT6 executor receipt

29 November 2026. Branch `loe/TRACKA-READOUT6` starts at `58f10f15d32f1bc5ec97c81cf9f2daaebc3654c8` on `origin/research/loe-bench`. The protocol commit `829276e949ac5134696df689a14898ae5e987609` was verified on the remote before implementation. The implementation commit `4191886beeef5adcf369cddcd531aeebf8ce5026` was verified on the branch remote before the synthetic dispatch. [Protocol](TRACKA-READOUT6-PROTOCOL.md) · [Round 5 review](../reviews/EXTERNAL-REVIEW-R5.md).

## Findings

| Finding | Result |
| --- | --- |
| R5-A | **PASS in fictional custody fixtures.** Two trusted 12-month issue pins disagree. A fresh calculation leaves the family `UNRESOLVED_CONTINUITY` and ineligible for publication. Restored draft staging and the final promotion step emit `publish=false` while the conflict persists. The final step also stops when the conflict appears after staging. After correction, the original signed 24-month ZIP is promoted without rescoring or replacing its bytes. A mismatch in either embedded H3 digest stops promotion. Fresh staging now passes the registered repository and version DOI to the scorer, which enables canonical discovery through the production entry point. [Publisher](../../../loe-bench/loe_bench/tracka_publish.py) · [Fixtures](../../../loe-bench/loe_bench/tests/test_tracka_readout.py). |
| R5-B | **PASS in Worker and reader fixtures.** Both suites use the same guide example. The Python reader verifies the two pins against a fictional attested release, with the local fixture scope and digests substituted. The Worker requires both digest lines and logs the number of a trusted scoped issue with missing, malformed or conflicting pins. An incomplete acknowledgement leaves dispatch due when it is the only acknowledgement. The Python reader retains its existing treatment of earlier result-only pins and holds on a marker that lacks the result digest. [Scoring guide](../HOW-TO-SCORE-TRACK-A.md#maintainer-scored-issue) · [Worker guide](../../../ops/tracka-cron/README.md#maintainer-scored-issue). |

## Verification

Local runtime was CPython 3.12.10 at `C:\Users\User\AppData\Local\Programs\Python\Python312\python.exe`, NumPy 2.5.4, pytest 8.4.2, Node v24.19.0, npm 12.1.0 and GitHub CLI 2.101.0. Commands below omit the local `rtk proxy` prefix.

| Command | Result |
| --- | --- |
| From `loe-bench/`, `python -m unittest discover -s loe_bench/tests -t .` | **PASS.** 297 run, 287 passed and 10 skipped in 76.139 seconds, exit 0. Existing Purple Book file-handle warnings appeared. The initial focused run reached both mismatch cases, but their fixture reused a ZIP opened in exclusive-create mode. Distinct fixture paths fixed both errors. |
| From `loe-bench/`, `python -m unittest loe_bench.tests.test_tracka_readout loe_bench.tests.test_tracka_secondary` | **PASS.** 28 passed in 50.806 seconds, exit 0. |
| From `ops/tracka-cron/`, `npm test` | **PASS.** 18 passed, exit 0. |
| From the repository root, `python -m pytest -o addopts= -q --tb=short --basetemp "$env:LOCALAPPDATA/Temp/pt-r6-829276e"` | **PASS under the standing exception.** 2,760 passed, 50 skipped, 1 xfailed, 8 failed and 2 warnings in 355.97 seconds, raw exit 1. All eight failures were the recorded SACR r2/r3 supervisor budget cases with `nan`, `inflated`, `erased` and `insufficient` parameters for each supervisor. |
| `gh workflow run score-track-a.yml --repo siriponsri/patent-to-pilot --ref loe/TRACKA-READOUT6 -f synthetic=true` and `gh run watch 46171932244 --repo siriponsri/patent-to-pilot --interval 10 --exit-status` | **PASS.** Dispatch and watch both exited 0. On `4191886b`, hosted CPython 3.12.10 ran 28 tests in 22.834 seconds. Both synthetic subjects passed attestation verification. The `select` and `readout` jobs were skipped. [GitHub Actions run](https://github.com/siriponsri/patent-to-pilot/actions/runs/46171932244). |
| `git diff --check` and a relative Markdown link and anchor check | **PASS.** Both exited 0. |

## Handoff

The tracked freeze manifest and all four primary scorer modules match the branch base. The local and remote freeze tag object `cb551bbc3031e7df10cfd676df5cd1de10317def` peels to `6712f32cdfb1252d66e192d770deaa867808a375`. Production capture, result writes, Worker deployment and mature readout are `NOT_RUN`. No protected TEST, sealed or private artifacts were opened. The card made no OSF or Zenodo writes and used no paid API or GPU.

The Planner owns the lane handoff and memory at integration and can send this branch for the next external review.
