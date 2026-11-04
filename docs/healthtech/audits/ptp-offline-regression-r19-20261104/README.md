# Patent-to-Pilot offline regression and MCP-limit checkpoint r19

Recorded: 4 November 2026 (Asia/Bangkok), `2026-11-04T07:18:49.2349681+07:00`

This checkpoint continues the existing Patent-to-Pilot O1–O4 goal on the
current candidate. It records the owner's new first-round OpenRouter MCP
limit and a fresh offline regression on the same candidate HEAD. It does not
start a new goal, reset the ledger or runtime window, retry an unknown call,
launch GPU work, or dispatch paid inference.

## Owner limit amendment

The owner set the initial OpenRouter MCP/provider limit to **USD30.00**.
This is recorded as provider-side limit metadata only. It is not treated as
the project cumulative USD100 ceiling, the E2 prospective USD1 allowance, an
account-credit receipt, or proof that the `.env` dispatch key can spend
USD30.00. The existing four legacy settled receipts and unknown-history
boundary remain unchanged.

The paid branch remains before reservation because the exact `.env` dispatch
key scope/limit binding and a fresh route-pricing observation are still not
present in the permitted evidence. The account-level MCP receipt remains
historical evidence only: `total_credits=10` and `total_usage=0.0001464`.

## Offline regression

- Candidate: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- Command: `python -m pytest -q`
- Collected: `657`
- Result: `655 passed, 2 skipped, 0 failed`
- Exit code: `0`
- Raw log: `full-tests.txt`
- Raw log SHA-256: `5e25721855787c0e09833ac434375451d7196ee5e35b38f6e6ab1105d5ec7e90`
- Warning: one existing `fitz` deprecation warning and one expected Pydantic
  serializer warning were emitted; neither changed the exit status.

The regression is engineering evidence for this candidate only. It does not
upgrade local schema validity into semantic quality, paid API comparison,
final-holdout evidence, user validation, revenue, ROI, or publication
acceptance.

## Resource and accounting boundary

This checkpoint made zero paid calls, zero reservations, zero ledger writes,
zero retries, zero GPU jobs, zero dataset downloads, and zero external
messages. No secrets or restricted payloads were added to the repository.

Next: preserve the same goal and continue only with a paid admission check if
new permitted evidence binds the exact dispatch key and current route price;
otherwise keep the paid branch separate and use this checkpoint as the
current offline verification record.
