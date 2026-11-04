# Current-head PatEmbed HTTP dossier rebind — 2026-11-03

This audit continues the existing Patent-to-Pilot O1-O4 goal at candidate
`88dc40471cb9078f929c02bb893cfa1e364da841`. It binds the already completed,
revalidated PatEmbed vectors to the current HTTP dossier provider and runs the
three named Abbott application cases. It does not create a GPU job, paid API
call, ledger, budget window, or new scientific holdout.

## Result

`PASS_CURRENT_HEAD_PATEMBED_HTTP_DOSSIER_BINDING_3_OF_3_ENGINEERING`

All three cases completed through the current worktree HTTP path with the
server-owned PatEmbed vector bundle:

- MitraClip: succeeded; 35 candidates, 33 dense candidates, 5 evidence items.
- Tendyne: succeeded; 35 candidates, 33 dense candidates, 5 evidence items.
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
- Provider: `datalyes/patembed-base`, revision
  `244ba452908a3093be11efb8a44396652317fb14`, encoder kind `patembed`.
- Corpus bundle manifest SHA-256:
  `75348afa4fede2535c09970d70353ecf9477f306a48fa46c71a445677f2302f1`.
- Query bundle manifest SHA-256:
  `45da46ee7dbd755f8ca8dd4c244ff6b9063f16253c27907e92ff0291c61c7e54`.
- The reviewed rights matrix was used; raw source payloads and private vector
  files remain outside Git.

The private machine-readable receipt is retained at the local artifact root
and is represented in sanitized form by `verification.json`; its SHA-256 is
`fe19a2844a412f226a30a4935e290259b90fb0323c49b45c502388c54c3dd9c7`.

## Scope limits

This proves current-head engineering/application binding and the end-to-end
HTTP dossier lifecycle for PatEmbed. It does not establish semantic patent
relevance, exhaustive recall, adaptive superiority, final-holdout validity,
paid API equivalence, user validation, revenue, ROI, willingness-to-pay,
clinical validity, FTO, patent validity, or journal acceptance. The previous
MiniLM HTTP receipt remains valid as a separate protocol/result and is not
overwritten or pooled with this run. The multilingual-e5 bundle remains
revalidated but was not substituted into this PatEmbed provider run.

## Reproduction

Use the existing `run_http_device_cases.py` with the typed cohort, reviewed
rights matrix, private device runtime JSONL files, and the PatEmbed corpus/query
bundles. The exact command and sanitized outcome are recorded in
`verification.json`; no raw cohort, vectors, or credentials are copied into
the repository.

## Next action

Update the acceptance matrix and manuscript to distinguish PatEmbed provider
binding from the descriptive research endpoint. Keep paid O3 fail-closed until
current scoped credit/limit evidence is available, then refresh route pricing
inside the admission window before reserving the USD0.25 canary through E2.
