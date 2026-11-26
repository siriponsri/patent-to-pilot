# Research lane verification

The retained engineering case and the sealed-trace verification passed using CPython 3.12.10. The read-only verification recomputed the fixture summary from its original trace. The Git index independently matched the ten frozen input and capture hashes. A link check resolved the lane's relative links.

The full suite ran before committing code. Both attempts used the existing S4 CPython 3.12.10 validation interpreter, `python -m pytest -o addopts= -q --tb=short --basetemp <fresh-short-temp>`, and wrote logs outside Git under `C:/Users/User/Desktop/myProject/_private_artifacts/ptp-ra-research-20261126/`.

| Attempt | Python overlay and basetemp | Outcome | Log and SHA-256 |
|---|---|---|---|
| 1 | S4 launcher-only `airgap`, `ptp-rap-26-r1` | 2,781 passed, 11 failed, 12 skipped, 1 xfailed, 2 warnings, 307.40 s, exit 1. Three BM25 tests failed through missing dependencies. | `pytest.log`, `6efde175b44a2156ab9874a24ef8df2701ea224910b2cb6045f0bccac522813e` |
| 2 | S4 `qa-sites`, `ptp-rap-26-r2` | 2,793 passed, 8 failed, 10 skipped, 1 xfailed, 2 warnings, 252.68 s, exit 1. | `pytest-qa.log`, `544381e2d16499c09c66cfea2de02ec9582e5253e576bc09e2e8d47ccbab17e7` |

The second run resolved all three BM25 failures. Its eight failing test IDs exactly match the standing SACR r2/r3 budget exceptions in the [S4 integrated receipt](../../evidence-scope/receipts/S4-integrated-verification.md). The code gate satisfies that exception policy. The historical S4 suite had fewer skips. These aggregate counts describe the reported profiles separately. The final full suite exercised this lane's new test, and the targeted test also passed on its own. Test and artifact verification are engineering evidence. The evidence contract's natural transfer and legal adjudication remain unmeasured.
