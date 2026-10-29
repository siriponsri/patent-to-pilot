# HT-W26 Engineering Report

## Objective and scope

The objective was to close the confirmed HealthTech backend defects and produce a fresh, inspectable, offline Abbott development run under the existing rights, privacy, and budget boundaries.

Inputs were the existing local source tree, the ignored Abbott public-device cohort, the reviewed rights matrix, the frozen HealthTech protocol, and the existing offline retrieval stack. The original ignored cohort was not modified; the run used the derived copy at `results/healthtech/ht-public-cohort-20261029-frozen-r1`.

Excluded work includes paid inference, live-provider canaries, deployment, external outreach, clinical or FTO analysis, customer validation, public redistribution, final holdout evaluation, and publication claims.

## Implemented changes

### F1 - External rights-aware projections

Local research objects retain the full evidence and source payloads. Product-display and redistribution projections now require reviewed structured rights metadata, rebuild statements from allowed source fields, remove unsafe quotes, omit unsupported evidence with diagnostics, and filter source payloads to `displayable_fields`. The dossier, history, and CLI exporters accept `local_research`, `product_display`, and `redistribution` purposes.

Primary files:

- `src/patent_to_pilot/healthtech/rights.py`
- `src/patent_to_pilot/healthtech/engine.py`
- `scripts/healthtech/run_dossier.py`
- `scripts/healthtech/build_abbott_dossiers.py`
- `scripts/healthtech/manage_dossier_history.py`

### F2 - Frozen Abbott cohort integrity

The Abbott adapter now requires `ht-runtime-integrity-v1` metadata and validates canonical runtime, source-registry, manifest, raw-file path, size, and SHA-256 bindings. It rejects evaluator/reference/split paths in runtime inputs, duplicate IDs, missing sources, stale registry revisions, URL/hash mismatches, missing raw files, and mutated runtime, registry, or raw data.

Primary files:

- `src/patent_to_pilot/healthtech/abbott.py`
- `scripts/healthtech/fetch_public_device_cohort.py`
- `tests/test_healthtech_repairs.py`

### F3 - Typed-rights provenance assurance

Provenance now resolves typed `rights_policy_id` values against the reviewed rights matrix. Unknown, blank, ambiguous, or mismatched IDs remain unresolved with `PASS_WITH_UNRESOLVED_RIGHTS`. Legacy free-text rights remain explicitly reported as `PASS_WITH_LEGACY_RIGHTS` / `LEGACY_TEXT_ONLY`.

Primary file:

- `src/patent_to_pilot/evaluation/healthtech/provenance.py`

## Frozen cohort

The derived frozen copy contains three devices, 41 patents, 61 disclosed reference pairs, no final holdout, and one legacy text-only disclosure source. The manifest records:

- Runtime SHA-256: `6414ae59d79972fbffbf5557d378156a2c5b6daae7ff061ce3121515e58a5cad`
- Source registry SHA-256: `94c5dcebf1083d4b010dc741e7cb66dead9f9646dae1b408b5f413d25fa15a17`
- Canonical manifest hash: `64f450027097f2fbe81daa662c010c093da826482c66aa023f14c4ba718bb74e`
- Cohort hash: `b92b50716599ad6ea3cdeb5b6a692990a52ae8dd113bfc0bb5cad2cdd2148715`
- References SHA-256: `a0f15c9accbe374ce9e918c09398869d8937096cd6f6809f94ece4f7e3fcd7c2`
- Split hash: `884302a3cb813e7ef1fa34d2afe29ec5b8c1524dda9f8fd104e9e7df8f30fa57`

The structural disclosure receipt covers 61/61 pairs and reports `PASS_WITH_LEGACY_RIGHTS`. That status is not a redistribution grant and is not semantic expert relevance judgment.

## Dossier outputs

The fresh dossiers were generated from the frozen copy:

| Device | Candidate count | Disclosed links | Case manifest |
| --- | ---: | ---: | --- |
| MitraClip | 35 | 21 | `HT-DEV-MITRACLIP/case-manifest.json` |
| Tendyne | 20 | 17 | `HT-DEV-TENDYNE/case-manifest.json` |
| TriClip | 28 | 23 | `HT-DEV-TRICLIP/case-manifest.json` |

The dossier outputs preserve the distinction between `retrieved_candidate` and `disclosed_link`. Unlisted pairs remain unjudged.

## Offline frontier

The frontier receipt records protocol hash `a87acaa448f97eabccae0f1fecc5378720ecf1178869336f68b42174eb828b0f`, scoring-script SHA-256 `f82232a2cf129610aece51eeab88ef49757506016b0493ec57492499ba0b8f01`, 41-patent candidate depth, 3 devices, 61 reference pairs, and zero provider calls.

Descriptive macro known-link recall at 20 was:

| Method | Macro recall@20 |
| --- | ---: |
| HT-B0a | 0.4427394146064223 |
| HT-B0b | 0.6622417082775139 |
| HT-B1 | 0.49880241951853205 |
| HT-B2 | 0.5689116226200625 |
| HT-B3 | 0.49880241951853205 |

All three queries completed for every method in the primary run. The frontier is labeled `DESCRIPTIVE_DEVELOPMENT_FRONTIER`; it is not a final adaptive comparison. The slice has three queries, two exact-patent groups, no final holdout, and company-held-out generalization is not estimable.

## Integrity probe

The sanitized probe copied only runtime inputs and deliberately did not copy the evaluator directory. It produced:

- Valid frozen copy: `PASS`, 3 cases, 41 patents per case.
- Runtime mutation: `PASS_REJECTED`.
- Raw PMA mutation: `PASS_REJECTED`.
- Source-registry revision mutation: `PASS_REJECTED`.
- Malformed integrity metadata: `PASS_REJECTED`.
- Network calls: 0.
- Provider calls: 0.
- Original cohort modified: `false`.

## Verification evidence

| Criterion | Status | Command or evidence |
| --- | --- | --- |
| Focused HealthTech repairs | PASS | `rtk python -m pytest -q tests/test_healthtech_repairs.py` -> 28 passed |
| Non-budget regression suite | PASS | `rtk python -m pytest -q --ignore=tests/test_release_budget_process.py` -> 298 passed |
| Budget-process tests, controlled environment | PASS | `PYTHONPATH=src rtk python -m pytest -q tests/test_release_budget_process.py` -> 5 passed |
| Full suite, controlled environment | PASS | `PYTHONPATH=src rtk python -m pytest -q` -> 303 passed; one `fitz` deprecation warning |
| Compile check | PASS | `rtk python -m compileall -q src scripts/healthtech tests/test_healthtech_repairs.py` |
| Whitespace check | PASS | `rtk git diff --check` |
| CLI product-display smoke | PASS | `scripts/healthtech/run_dossier.py ... --purpose product_display` |
| Frozen integrity probe | PASS | `results/healthtech/ht-abbott-integrity-probe-20261029-frozen-r1/summary.json` |

The unqualified `rtk python -m pytest -q` invocation has a setup-only failure in the two subprocess tests because this checkout is not installed and pytest's `pythonpath = ["src"]` does not automatically propagate to child processes. The explicit `PYTHONPATH=src` rerun is the valid process-level verification.

## Risks and limitations

- The cohort is an Abbott public-disclosure development slice with one disclosure source and legacy free-text rights.
- Product-level disclosures do not establish claim-level semantic relevance, patent validity, FTO, clinical suitability, or investment merit.
- No final holdout exists; confidence intervals and broad generalization are `NOT_ESTIMABLE`.
- Google-derived patent pages and third-party source text remain local research inputs; external display and redistribution remain rights-gated.
- Rights-matrix entries with empty `source_types` are accepted only on an exact source-ID match; review or augment those catalog entries before treating them as broad typed-policy coverage.
- No paid calls, live-provider execution, deployment, or human studies were performed.

## Handoff

Next actor: owner or authorized research lead. Next action: review the M4 readiness seam without reading credentials; if gates are not all satisfied, obtain a rights-cleared independent cohort and predeclare relevance judgments plus a final holdout. End state: `READY_FOR_REVIEW` for the engineering package, not publication or product release.
