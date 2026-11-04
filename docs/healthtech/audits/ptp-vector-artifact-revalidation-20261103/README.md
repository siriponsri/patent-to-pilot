# Vector artifact revalidation — 2026-11-03

This additive audit continues the existing Patent-to-Pilot O1–O4 goal. It
revalidates owner-private PatEmbed and multilingual-e5 vector bundles against
the frozen device runtime manifest without copying raw text, vectors, labels,
weights, or credentials into the repository.

## Outcome

- Status: `PASS_VECTOR_BUNDLE_INTEGRITY_PRIOR_ARTIFACT`.
- Runtime manifest hash: `89e5b86cc21d9f3466cc3236416f4873840622a56e7aad767bbbfe173bc0484c`.
- Cases: `HT-DEV-MITRACLIP`, `HT-DEV-TENDYNE`, `HT-DEV-TRICLIP`.
- Corpus/query rows: `41` / `3`; vector dimension: `768`.
- PatEmbed and multilingual-e5 corpus/query bundles loaded successfully.
- Shard hashes, shapes, finite little-endian float32 values, unique IDs,
  runtime input bindings, and cross-encoder ordering bindings passed.
- No dataset download, model encode, retrieval evaluation, API call, ledger
  mutation, budget reset, or time-window reset occurred.

## Reproduction

From the candidate worktree, with the repository source path available:

```powershell
$env:PYTHONPATH='src'
rtk proxy python -B scripts/healthtech/verify_vector_bundle_pair.py `
  --artifact-root "C:\Users\User\Desktop\myProject\patent-to-pilot-local-artifacts\ht-o4-http-device-vectors-20261031" `
  --output "docs\healthtech\audits\ptp-vector-artifact-revalidation-20261103\verification.json"
```

Candidate tested: `88dc40471cb9078f929c02bb893cfa1e364da841`.

Focused vector tests passed `10/10`; the full Python suite recorded `613`
tests with `612` passed, `0` failed, `0` errors, and `1` existing optional
tokenizer-artifact skip. `compileall`, JSON readback, and `git diff --check`
passed.

## Claim limits

This is integrity revalidation of existing private artifacts, not a new encode
or retrieval experiment. The receipt records model IDs, revisions, and model
hashes carried by the manifests, but this check did not reverify matching
PatEmbed or multilingual-e5 weight files in the known local model root. The
result therefore supports artifact binding and integrity only; it does not
establish semantic retrieval quality, gold-label validity, or publication
readiness.

The paid OpenRouter branch remains separate and is still blocked before
reservation by the canonical R1 history and current scoped credit gates.

