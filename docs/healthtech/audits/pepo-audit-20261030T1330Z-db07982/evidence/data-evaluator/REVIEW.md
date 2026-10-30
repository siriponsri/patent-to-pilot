# Independent data/evaluator review — db0798276

Scope: local read-only review of DAPFAM acquisition/coverage/BM25, current public-device cohort counts/splits, semantic-judgment intake gates, and holdout chronology. This is a sub-review, not an exhaustive inspection of every Luna milestone. Root auditor will persist selected sanitized evidence inside the project. No repository implementation/status files were written. No SSH, providers, neural inference, credentials, downloads, installs, or network source checks occurred.

Inspected revision: `db0798276e3158b04131b4e910abc0a11511e94c`. Applicable root AGENTS and research-synthesis skill/team contract were read. Test/source/receipt review was source-first; no broad regression rerun was necessary for the targeted aggregate and authored counterexample probes below.

## Independently verified M42 facts

Actual local parquet files were read via existing DuckDB CLI 2.0.0 using no-agent mode, disabled extension autoload/autoinstall, two threads, 512MB memory and audit-owned spill directory. The aggregate/hash probe completed in 4.28 seconds. SHA-256 matches both Luna receipt and the local pinned HuggingFace release-tree LFS metadata; that is a local provenance comparison, not a fresh upstream attestation.

| Input | Bytes | Rows / unique IDs | SHA256 |
|---|---:|---|---|
| corpus.parquet | 1,149,928,014 | 45,336 / 45,336 | `469fe8e04d8bd8775a1116eccf0983e570a03444bef9c6e14c97aabafb7526d6` |
| queries.parquet | 62,667,355 | 1,247 / 1,247 | `b5ad91a650349a0096911fadcb7bc35a0399eb12d1470fb2601d73af5fc2bcbe` |
| qrels_all.parquet | 828,375 | 49,869 / 49,869 pairs | `e51ae4e13abee0fc7523560ecddd272bc85dc98befc8ab4466155a0c2d2d4f74` |

Reproduced exactly: medical-device lexical corpus hits 2,859, query hits 86; positive qrel both-side lexical hits 836 IN and 65 OUT; no missing title/abstract fields. All qrel IDs join to local query/corpus files. Positive labels total 24,929 = IN19,736 + OUT5,193; NC24,940 have relevance0. No qrel null key/label rows. Count/schema/hash outputs are in `data-probe-result.json`.

M42's medical-device screen is correctly declared case-insensitive **substring** matching over title+abstract; terms such as `valve`, `balloon`, `cell`, `compound` are broad. This is not a validated medical-device subset, device identity resolution, or semantic device–patent relevance evaluation. The source code and receipt correctly avoid those claims. The coverage numbers should not be presented to the owner as semantic gold size.

Local pinned card `methodology/datasets/metadata/DAPFAM_README.md:43` defines 1,247 **query patent families** and 45,336 target families with **citation-based relevance**, IN if IPC3 overlaps and OUT otherwise. The recorded collection license is CC-BY-NC-SA4.0. Research diagnostic use is distinct from commercial dossier/product use; vectors do not automatically remove the collection's NC/SA rights constraints. Remote private research processing needs a separate recorded compute/transfer decision, not the semantic-judgment authorization schema.

Actual schema supports vector work now without new human labels: corpus ID `relevant_id`, query ID `query_id`, shared `title_en`, `abstract_en`, `claims_text`, `description_en`, IPC/date metadata. Existing BM25 uses only title+abstract (`run_dapfam_bm25.py:357–358`), not claims/full text. IDs are family IDs and must not be coerced into the US patent-document canonical-ID contract.

## Confirmed findings / bounded concerns

### D1 — P1 work-order drift: optional semantic-label intake became a global prerequisite

Authoritative project requirements explicitly permit progress without owner experts:

- `GOAL.md:105`: no new expert annotator → use existing gold labels/deterministic checks, start work.
- `PLAN.md:37`: MVP must not depend on organizational data or finding new expert annotators.
- `PLAN.md:308`: primary outcome is macro **known-link Recall@K**.
- `PLAN.md:580`: absence of new expert labels blocks only claims that require those labels; existing-gold tasks/source integrity continue.

By contrast, `docs/healthtech/audits/luna-long-run-20261030-authorization-bound-judgment-ingest-20261030/README.md:42–44` says to pass M23, ingest real semantic judgments, and **only then** rerun HT-B0a/B0b/B1/B2/B3. The M26 landscape README's final paragraph says not to rerun scientific controls until M23→M25→M24. M42 README:62–64 continues the semantic-source dependency as the next action.

`source_authorization.py:87–88` accepts only `semantic_relevance_judgment`; `:123` requires both label names in the schema; `:128–129` requires the adjudicator-role-required flag; `:138–139` requires predeclared holdout. These are a specialized optional semantic-judgment contract, not prerequisites for embedding compute, existing published benchmark evaluation, or scoped positive known-link recovery. Keep the strict contract for the semantic claim branch, but remove its promotion into a universal compute/evaluation gate.

Nuance: actual `judgments.py:174–184` supports `benchmark_gold` and only requires actual adjudicator_role for expert_adjudication basis. It does not require a human for every benchmark row or actual negative examples. The stronger proven problem is **work-order scope** and repeated semantic-source dependency, not that every label row technically requires a new human annotator.

### D2 — P2 scientific claim: Stryker is not globally untouched after prior development exposure

Immutable Git chronology:

1. `71c8d6658ad2e115cfa61a0c8b768ae02cefe94a`, 2026-10-29 09:20:07+07, already committed actual Stryker HT-B0a–B3 development scores (3 devices,13 patents) in `.../luna-long-run-20261029-m2-m3-stryker-20261029/README.md`. It explicitly had no final holdout, and K20 was ceiling-limited.
2. `dbcac2f10be1bcac8e492d4b76056e79a48da8d8`,09:36:05+07, later introduced composite builder holding out the same Stryker source devices.
3. Current `scripts/healthtech/compose_multicompany_cohort.py:358` and `:375` state that the final holdout was not used for development/tuning and is predeclared untouched. Current multicompany README describes “untouched Stryker holdout.” These blanket statements exceed chronological evidence.

This does not prove tuning on test. Fixed-policy descriptive cross-company transfer remains useful. M20 correctly calls itself sensitivity analysis of the existing development proxy. Do not silently delete/rewrite old results; annotate exposure and use **new untouched groups/source snapshots** for future confirmatory claims. Sharing a declared candidate index is not itself leakage.

### D3 — P2 evaluator blind spot: invalid external rankings can exceed nDCG bounds

`scripts/healthtech/run_dapfam_bm25.py:186–197` adds gain for every ranked item, with no dedup/bounds check. `evaluate:200–214` iterates qrels only, so unexpected prediction query IDs are silently ignored.

Authored repro in `data-probe-result.json`:

```python
evaluate({'Q':['P','P']}, {'Q':{'P':1.0}}, k=2)
# macro_recall_at_k=1.0, macro_ndcg_at_k=1.6309297535714575
evaluate({'Q':['P'], 'UNKNOWN':['P']}, {'Q':{'P':1.0}}, k=2)
# accepted, UNKNOWN silently ignored
```

Saved actual r3 rankings were independently checked:1,247 rows/unique query IDs, every width100, **zero duplicate ranked IDs**, zero non-finite scores. Thus there is no evidence current reported BM25 scores are inflated by these malformed-input bugs. The narrow helper issue matters before remote chunk vectors map multiple chunk hits back to family IDs: aggregate/dedup before K and validate expected-query membership/finite scores/evaluator bounds. Core HT-T1 `evaluate_known_links` already has stronger canonical dedup/unknown-query/failure handling; do not weaken it.

### D4 — P2 protocol ambiguity: identical query/family self-matches affect DAPFAM diagnostic

Independent SQL and saved-ranking inspection (`self-match-probe-result.json`):

- 135 query IDs overlap corpus target IDs; all135 have identical title+abstract text.
- All135 retrieve their self family in saved top100;134 at rank1,one at rank2.
- qrels contain40 identical query_id==relevant_id pairs scored1.0/IN.

This is not yet labelled an official-evaluator violation: the exact pinned MTEB/DAPFAM identical-ID convention must be checked before claiming parity. Current local diagnostic is internally reproducible but should explicitly declare self-match inclusion, report a sensitivity/exclusion diagnostic, and use the same policy for lexical and vector methods. Do not call the medical lexical slice an independent medical validation set. No official-parity code was fetched or executed by this sub-review.

### D5 — P2 assurance gap in a specialized optional gate: DRAFT is accepted for staging

`source_authorization.py:10–13` allows both DRAFT_SOURCE_AUTHORIZATION and APPROVED_LOCAL_RESEARCH_SOURCE. `source_acquisition.py:152` calls that validator, then stages without requiring approved status. `judgment_submission.py:60` uses the same validator.

Authored safe probe changed only the fixture status to DRAFT; validation returned PASS/DRAFT and `stage_authorized_semantic_source` returned PASS/copying2files12bytes. Saved `authorization-probe-result.json`. No real source was accessed or authorized by this test.

If these functions claim an approval-enforcement boundary, distinguish valid draft preflight from executable approval; otherwise label the helper as structural validation rather than proof of owner authorization. This should **not** become a new approval gate for already authorized existing benchmark/embedding work. Real user/runtime authority remains separate from self-authored approval fields.

## Current actual cohort counts / denominator clarification

Independent JSON reads, no neural rerun:

| Cohort | Devices | Patents | Product-disclosed pairs | Role |
|---|---:|---:|---:|---|
| Abbott existing |3|41|61|legacy development|
| Boston WATCHMAN|2|7|13|development|
| Stryker Neurovascular|3|13|13|previously exposed development/transfer|
| Cook Zenith|3|4|5|development|
| Philips cardiovascular|3|7|7|development|
| Latest composite r4-philips-family full|11|31|38|4company groups;31mapped patents/24observed families in recorded mapping|

Latest composite **development view** has8queries/31patents/25pairs, all8have nonempty references,6exact/family groups. Holdout view has3queries/31patents/13pairs,all3have references,3groups. Full has11queries/9groups. The earlier r3-family full8queries/24patents/31pairs/6groups had development5queries/18pairs/3groups. A “dev8 but eligible5” combination mixes vintages/paths; it is not current r4 denominator evidence.

`split-counts-summary.json` contains aggregate counts across all actual composite views. Recorded family metadata counts were inspected but raw source pages/family extraction were not independently replayed here. No claim all rights clauses across all device sources were reverified; DAPFAM local license/card/provenance and the explicit local-use boundaries were inspected.

## DAPFAM sufficiency and next-goal implication

DAPFAM alone is sufficient to begin **separate patent-family embedding/retrieval component experiments** with existing published citation qrels. It is insufficient to validate named medical-device product-to-patent semantics, dossier evidence correctness, clinical/FTO, commercial product rights, or broad HealthTech generalization.

Complementary work should reuse existing device facts/independent marking known links for scoped HT-T1 recovery and HT-T3, published annotated evidence task(s) such as the already-local SciFact for HT-T2, and an explicitly licensed general patent retrieval benchmark/dataset for representation transfer if useful. Do not require owner-created expert annotations or organizational data. Commercial/external product use requires a compatible dataset/text license and intended-use decision beyond DAPFAM NC diagnostic status. Fresh independent companies/families/source groups are needed for genuinely untouched confirmation; no new semantic human labels are required merely to compute embeddings.

Vectors must preserve family IDs, query/target roles, selected TA/TAC/full-text view and chunk→family mapping. Keep qrels/evaluator fields out of embedding inputs, use declared long-text chunking instead of silently first256tokens, and record self-match/dedup policies before comparing vector to lexical. These changes directly advance remote-compute→local-vector implementation without waiting on M23.

## Reproduction/evidence files

- `probe_data.py`, `data-probe-result.json`, `probe_data.log` — aggregate/hash/schema/rank integrity/helper probes.
- `probe_authorization.py`, `authorization-probe-result.json` — authored draft-staging probe; helper writes only audit-owned temp data.
- `self-match-probe-result.json` — independent aggregate self-family checks.
- `cohort-inventory.json`, `split-counts-summary.json` — sanitized count-only current source/split inventory.

Do not copy `split-counts.json` or the authored staging directory wholesale: the former contains expanded evaluator-side group records used for inspection, the latter is scratch. Root should persist only sanitized summaries/scripts/report listed above, under project-local audit convention. No broad dataset cleanup was performed.
