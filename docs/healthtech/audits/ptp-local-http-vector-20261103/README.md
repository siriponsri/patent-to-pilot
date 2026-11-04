# Current-head local vector HTTP verification — 3 named cases

This audit continues the existing Patent-to-Pilot O1–O4 goal. It is a fresh
engineering verification at candidate `88dc40471cb9078f929c02bb893cfa1e364da841`.
It does not open a new paid/API window, change the canonical ledger, or create a
scientific final evaluation batch.

## Outcome

`PASS_CURRENT_HEAD_LOCAL_VECTOR_HTTP_3_OF_3_ENGINEERING`

The runner completed MitraClip, Tendyne, and TriClip through the current local
vector HTTP path. Each case succeeded and completed source inspection, an
expected-parent edit from history version 1 to version 2, history readback,
reopen-by-history, and JSON/Thai/English export. Vector errors were zero in all
three cases. Provider calls and paid cost were zero.

## Inputs and binding

- Frozen typed public cohort: 3 devices and 41 canonical patent documents.
- Rights matrix: the existing reviewed local-research matrix; unresolved Google
  patent redistribution remains blocked.
- Encoder: `sentence-transformers/all-MiniLM-L6-v2`, revision
  `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, ONNX CPU quantized AVX2.
- Corpus bundle: 41 rows, dimension 384, `passage` role,
  manifest SHA-256 `e69ffe77ad463ba17512e5415933a15a4e3e5eb0609730b5649b5e417525503e`.
- Query bundle: 3 rows, dimension 384, `query` role,
  manifest SHA-256 `5c1b83583a18e6316d8cbd47c2d9ca17f5ba8efeed07e6d64bf58c8ed8b707f9`.
- Query runtime SHA-256: `8d144151ecaf98b87f09ab673e1c3ac6f07c0df69d66ec162c4c36949ac3b2b6`.
- Model artifact SHA-256: `b941bf19f1f1283680f449fa6a7336bb5600bdcd5f84d10ddc5cd72218a0fd21`.
- Tokenizer artifact SHA-256: `be50c3628f2bf5bb5e3a7f17b1f74611b2561a3a27eeab05e5aa30f411572037`.

The private vector files remain outside Git. Only sanitized binding hashes and
aggregate results are kept here.

## Verification

The complete machine-readable result is in `verification.json`. Bundle
validation is summarized in `vector-validation.json`; its paths are sanitized.
The command output is retained in `run.log`. Candidate-bound regression logs
record Python `29 passed`, frontend unit `74 passed`, and browser HTTP
integration `PASS`.

## Boundaries

This run proves current-head local engineering and application-path behavior.
It does not prove semantic relevance, exhaustive recall, adaptive superiority,
paid API equivalence, clinical/legal/FTO validity, user validation, revenue,
ROI, willingness-to-pay, or journal acceptance. The three named cases remain
application examples and are not a sufficient sample for a scientific claim.

The local HTTP runner does not dispatch local Qwen generation. Existing local
generation receipts remain separate artifacts and are not silently pooled with
this retrieval receipt.
