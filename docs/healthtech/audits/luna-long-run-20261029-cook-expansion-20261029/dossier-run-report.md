# Cook Zenith dossier run

## Outcome

The Cook adapter and runner produced three local public-source dossier cases from the frozen Cook Zenith cohort. Each case has source-backed PMA facts, PDF-reconstructed product-level disclosure evidence, promoted disclosed links, acquisition events, an engine manifest, a source summary, a zero-cost receipt, contiguous history versions `1` and `2`, and local JSON/EN/TH exports.

## Case results

| Query | Patent universe | Disclosed links | History | Provider calls | Paid cost |
|---|---:|---:|---|---:|---:|
| `HT-DEV-COOK-ZENITH-DISSECTION-STENT` | 4 | 2 | 1 -> 2 | 0 | `$0.00` |
| `HT-DEV-COOK-ZENITH-FLEX-AAA` | 4 | 2 | 1 -> 2 | 0 | `$0.00` |
| `HT-DEV-COOK-ZENITH-RENU-CONVERTER` | 4 | 1 | 1 -> 2 | 0 | `$0.00` |

The runner made three bounded offline lexical search calls and returned zero lexical candidates in the tiny local result surface; the five source-backed Cook disclosures were then appended and marked `disclosed_link` from the official Cook PDF evidence. This is intentional provenance annotation, not semantic gold or exhaustive recall.

## Verification

- Adapter fixture tests cover case construction, PDF disclosure reconstruction, runtime/source/raw mutation rejection, evaluator separation, promotion, and external export blocking.
- Real-cohort assertions pass for three cases, contiguous histories, EN/TH/local JSON exports, no evaluator-reference leakage, `BLOCKED_LOCAL` product display/redistribution, zero provider calls, and `$0.00` paid cost.
- Exact code, source, and output hashes are recorded in [dossier-run-verification.json](dossier-run-verification.json).

## Boundaries

Cook product-level patent marking is a documented product association only. It does not establish component-level relevance, claim construction, patent validity, FTO, clinical suitability, investment merit, or generalization. Unlisted pairs remain unjudged. The Cook page/PDF and Google-derived patent text stay local-only, and family mappings remain `UNKNOWN_NOT_ASSUMED`.

The generated dossier results are ignored local artifacts under `results/healthtech/ht-cook-dossiers-20261029-r1/`; only the adapter, runner, tests, and sanitized audit summaries are eligible for the scoped commit.
