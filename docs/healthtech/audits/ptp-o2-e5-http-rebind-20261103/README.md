# Current-head multilingual-e5 HTTP dossier rebind - 2026-11-03

This audit continues the existing Patent-to-Pilot O1-O4 goal at candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. It binds the already completed,
revalidated multilingual-e5 vectors to the current HTTP dossier provider and
runs the three named Abbott application cases. It does not create a GPU job,
paid API call, ledger entry, budget window, or new scientific holdout.

## Result

`PASS_CURRENT_HEAD_E5_HTTP_DOSSIER_BINDING_3_OF_3_ENGINEERING`

All three cases completed through the current worktree HTTP path with the
server-owned `intfloat/multilingual-e5-base` vector bundle:

- MitraClip: succeeded; 33 candidates, 33 dense candidates, 5 evidence items.
- Tendyne: succeeded; 33 candidates, 33 dense candidates, 5 evidence items.
- TriClip: succeeded; 41 candidates, 41 dense candidates, 5 evidence items.

Each case passed source inspection (`200`), version `1 -> 2` edit/history,
history readback, and JSON/Thai/English export. Vector errors were zero in all
cases. Provider calls and paid cost were zero because this is a local vector
provider run.

## Binding and inputs

- Cohort: `ht-public-cohort-20261029-frozen-r2-typed`, 3 devices and 41 patents.
- Cohort runtime SHA-256:
  `3abd5cc308b7e69fc3b6055dd6744b0049341164adf9f95e9fa806ff35d0f121`.
- Corpus runtime SHA-256:
  `5965b7b51006d9d64d05250848300dee68d80a0b69324213a5ccac25a1c44e9d`.
- Query runtime SHA-256:
  `7e0e29b6b7e8f19dcbd28c775e8b518255b5fdcfa0846307acb5dd7f5b1381a8`.
- Provider: `intfloat/multilingual-e5-base`, revision
  `d128750597153bb5987e10b1c3493a34e5a4502a`, encoder kind `e5`.
- Corpus bundle manifest SHA-256:
  `643ab8856a1bcd72d2c2e4745d02bdfe46bed0190f16ab8834c3870249fdcc7b`.
- Query bundle manifest SHA-256:
  `8e0a933f34c26a7f1370809c5220911cf6ed1b318bd02e7b4b60cc25ce76494c`.
- Reviewed rights matrix SHA-256:
  `48bd51b8ce9d85bde9d1d64f235026c70aa6ba4f1374331f6d08434fb8e613ec`.
- The raw cohort, runtime JSONL, vectors, and model files remain outside Git.

The private machine-readable receipt is retained at the local Windows artifact
root and is represented in sanitized form by [`verification.json`](verification.json); its
SHA-256 is
`bcdc364344b7c3503a1927a6d678d2d1bc16c143de87764daa508c1cdec32834`.

## Verification

The vector bundle revalidator passed all existing bundle, shard, shape,
finite-float, input-binding, and cross-encoder ordering checks. The focused
current-head regression set passed `11` tests with zero failures, errors, or
skips. `compileall` passed for `src` and `scripts/healthtech`.

## Scope limits

This proves current-head engineering/provider binding and the end-to-end HTTP
dossier lifecycle for multilingual-e5. It does not establish semantic patent
relevance, exhaustive recall, adaptive superiority, final-holdout validity,
paid API equivalence, user validation, revenue, ROI, willingness-to-pay,
clinical validity, FTO, patent validity, or journal acceptance. The prior
MiniLM and PatEmbed HTTP receipts remain separate protocols/results and are not
pooled into a single scientific claim. The E5 bundle is now bound to the
dossier path, but O2 scientific comparison remains partial.

## Reproduction boundary

Reproduction uses the existing `run_http_device_cases.py` with the typed
cohort, reviewed rights matrix, private device runtime JSONL files, and the
E5 corpus/query bundles. The exact private paths are intentionally omitted
from this repository receipt. No raw source payload, vector, model weight, or
credential was copied into Git.

## Next action

Keep the goal active. Preserve the E2 journal and unknown legacy history, keep
paid O3 fail-closed until current scoped credit/limit evidence is available,
and keep the O2 scientific claim at descriptive/partial scope. Owner review
and release verification remain required before merge or submission.
