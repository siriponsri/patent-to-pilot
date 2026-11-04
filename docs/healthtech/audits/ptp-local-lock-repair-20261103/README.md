# Local lock repair checkpoint

- Candidate worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Candidate HEAD inspected: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Status: `PASS_LOCAL_SHARED_GPU_LOCK_REPAIR_API_BLOCKED`
- Scope: close the concurrency-1 gap between transformer embedding/query evaluation and local Qwen generation; refresh only read-only OpenRouter metadata; do not dispatch paid inference.

## Implemented

The existing `local_gpu_slot()` now protects the actual model lifetime in:

- `scripts/healthtech/encode_transformer_shards.py`
- `scripts/healthtech/run_transformer_vector_retrieval_eval.py` when a local query encoder is used
- `scripts/healthtech/remote_encoder_self_check.py`
- the existing `scripts/healthtech/run_qwen_generation_evidence_pack.py` path

The regression test holds the shared slot during the embedding call and proves a second process cannot acquire it. Existing receipt-preservation, cross-process release, GPU UUID, expiry, and API/local isolation tests remain green.

## Verification

- Focused lock/generation/API/vector suite: `37 passed, 0 failed, 0 skipped`.
- Full Python suite: `613 passed, 1 skipped, 2 warnings`, exit `0`.
- `compileall`: pass.
- `git diff --check`: pass.
- New paid provider calls: `0`.
- New paid reservations/attempt IDs: `0`.
- Ledger mutations, budget reset, and 24-hour window reset: `0/false/false`.

## API gate

Read-only metadata refresh is stored at `metadata-observation-r2.json`. It returned HTTP 200 for the named key, lifetime usage `USD0.0001464`, daily/weekly/monthly usage `USD0`, `is_management_key=false`, no account-credit response, `account_scope_binding=NOT_RECONCILED`, and `history_completeness=NOT_PROVEN`. This is not an account-credit attestation and does not satisfy the live gate.

Paid dispatch remains `BLOCKED_BEFORE_RESERVATION` because the existing canonical R1 journal or sanitized all-attempt export and the current scoped v2 account/key credit snapshot are still absent. No replacement or zero ledger was created.

## Next action

Continue local/offline and manuscript work independently. If the owner supplies those two non-secret evidence items once, reconcile them with `inspect_r1_history_export.py`, recheck route/pricing/writer quiescence, and reserve exactly one paired canary only if every gate passes.
