# HT-M38 current-head Philips dossier audit

- Run ID: `luna-long-run-20261030-m38-philips-dossiers-r6-20261030`
- Date: `2026-10-30`
- Tested code commit: `285eb74ee0d45321867b618b0aa5d28a7fb38534`
- Status: `PASS_CURRENT_HEAD_PHILIPS_DOSSIERS`

## Scope

This package reruns the local Philips dossier pipeline at the current repository head using the frozen Philips cardiovascular cohort and the reviewed M13 rights matrix. It exercises the real adapter/runner path, history save and edit, selected-version export, source summaries, source views, and resource receipts without network or provider calls.

## Results

The run produces three inspectable dossiers:

| Device | Candidates | Disclosed links | History | Rights boundary |
|---|---:|---:|---|---|
| AngioSculpt Scoring Balloon | 1 | 1 | versions 1 and 2 | product display/redistribution blocked for marking and patent sources |
| Thromcat Thrombectomy System | 2 | 2 | versions 1 and 2 | product display/redistribution blocked for marking and patent sources |
| Turbo-Elite Laser Catheter | 4 | 4 | versions 1 and 2 | product display/redistribution blocked for marking and patent sources |

Totals are 7 product-level disclosed links, 3 local search calls, 0 returned lexical candidates, 0 provider calls, and USD 0.00 paid cost. The result manifest SHA-256 is `16722af3e72ee10aaec18ee22593d2dc5741b4b6f06be9d9b7784dea2520af36`; the receipt SHA-256 is `db57c3865833c8b1bce1138c525fa494a8b10ce42e321d2bf4189af93fdcac3a`.

## Verification

Philips dossier, cohort, repair, and pre-live regressions pass. `compileall` passes. The current-head validator confirms required JSON/Markdown/history artifacts for all three cases, 6 allowed source views return only declared displayable fields, and 48 blocked source-view requests fail closed with `RightsBoundaryError`.

Machine-readable evidence is in [`verification.json`](verification.json). The full local result remains at `results/healthtech/ht-philips-dossiers-20261030-r6/` and is intentionally not copied into this audit folder.

## Boundaries

- The run is `local_research` only. Philips marking material and Google-derived patent text remain local-only.
- Product-level disclosed links are not semantic relevance gold, claim support, exhaustive recall, clinical evidence, FTO, patent validity, investment merit, or publication evidence.
- Unlisted pairs remain `UNJUDGED` and are not negatives.
- Live/provider HT-B4 remains `BLOCKED_LOCAL`; semantic judgment intake, user/commercial validation, deployment, outreach, and Claude UX/UI remain pending or paused.

## Next action

Obtain an owner-authorized rights-cleared semantic device-patent judgment source, validate it through M23/M25/M24, and preserve this package as local product-level disclosure evidence while rerunning frozen controls only after the semantic cohort is authorized.
