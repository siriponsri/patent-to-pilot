# Local Qwen guided pack binding — 2026-11-03

This additive audit continues the original Patent-to-Pilot O1–O4 goal. It
binds an owner-supplied private FDA-only canary receipt to the current
acceptance record without copying raw prompts, outputs, or restricted source
payloads into Git.

## Outcome

- Guided local `Qwen/Qwen3-8B`: `3/3` schema-valid cases.
- Unguided local `Qwen/Qwen3-8B`: `0/3` schema-valid cases; all three failed
  because `unresolved` was emitted as a string instead of the required string
  array.
- OpenRouter API dry-run: `FAIL_CLOSED` before dispatch because the exact
  model-visible fields require a source-backed transfer review that is absent
  from the pack.
- Provider calls: `0`.
- Paid cost: `USD0.00`.

The local receipts are prior private artifacts captured on the approved V100
and are not a new inference run on current source HEAD
`88dc40471cb9078f929c02bb893cfa1e364da841`. They are evidence for the local
generation contract and failure analysis, not a current-head O3 rerun and not
a local-versus-API comparison.

## Bound artifacts

The source pack, exact-message file, and two sanitized receipts remain in the
owner-private artifact store. This repository records only file hashes,
configuration, per-case metrics, and claim boundaries in `verification.json`.

The pack is FDA-only and intentionally excludes patents, disclosures, raw
source text, and evaluator labels. It is a smoke test of the generation
contract; it is not the main device–patent scientific study.

## Verification

- Pack/model contract was loaded offline.
- API preflight was attempted in dry-run mode only.
- The dry-run failed closed before writing an API receipt or reading a key.
- No ledger, budget, GPU allocation, dataset, or 24-hour window was created
  or changed.

See `verification.json` and `CHECKPOINT.json` for machine-readable details.
