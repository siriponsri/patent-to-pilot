# R1 metadata recovery handoff

Read [AUDIT_TH.md](AUDIT_TH.md), [reconciliation.json](reconciliation.json), [verification.json](verification.json), and [RESUME_GOAL_TH.txt](RESUME_GOAL_TH.txt).

The key metadata request was executed with explicit owner authorization. No model call, budget-ledger mutation, GPU job, push or merge occurred. The local observation is not a signed provider attestation. Preserve the legacy journals and the USD8 authority; use the pending scope/balance facts to finish reconciliation.

Ordinary-key metadata helper (already executed once for this handoff; no need to repeat to inspect history):

```powershell
python -B scripts/healthtech/collect_openrouter_metadata.py --key-file C:/Users/User/Desktop/myProject/patent-to-pilot/.env --output <NEW_PRIVATE_RECEIPT_PATH>
```

This command reads the selected key and makes one GET to the official HTTPS `/api/v1/key` endpoint. It does not produce a live-admission credit snapshot or import R1 history. `--allow-credits-if-management` permits `/credits` only if the same existing key reports `is_management_key=true`; it does not acquire credentials. Do not upload the key or raw account metadata to a chat or public repository.

Sanitized billing observations are retained here for local audit/handoff. Review publication scope before any later public release. Full prompts/outputs and third-party raw sources belong only in the approved private artifact store.
