# HT-T2 SciFact current-head differential audit

- Run ID: `luna-long-run-20261029-scifact-204abf4`
- Tested source commit: `204abf415fe751c39d8f94684cfc123a7c64ae7a`
- Scope: pinned local SciFact release receipt plus valid-input parity against the pinned upstream evaluator
- Provider calls: `0`
- Paid cost: `$0`
- Verdict: `PASS_COMPONENT_ENGINEERING`; no patent-device or held-out SciFact score claim

The upstream code was reacquired into a temporary local checkout at the exact registry revision `68b98a56d93e0f9da0d2aab4e6c3294699a0f72e`. Only the public evaluator source was used; no raw third-party code or dataset was staged into the repository.

See `receipt.json` for the three-case metric comparison and official source-file hashes, `scifact-release-receipt.json` for local release counts/hashes, and `REPORT.md` for the evidence ledger and limitations.
