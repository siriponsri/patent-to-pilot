# P3-T01 — Thai dataset/profile rights and exposure contract

**Task:** P3-T01 (phase P3, lane offline). **Checked:** 22–23 Nov 2026. **Spend:** USD 0.
**Scope:** documents plus read-only registry and adapters. No data file was downloaded, no gate was accepted and no
provider was called.

**Evidence:**
- machine-readable contract: `src/patent_to_pilot/workbench/datasets/registry.json`, with a `thai_contract` block per
  Thai dataset and a top-level `thai_contract`;
- validator and permission checks: `src/patent_to_pilot/workbench/datasets/thai_contract.py`;
- tests: `tests/test_p3_t01_thai_contract.py`.

Status fields: `method_evidence` NOT_YET_DEMONSTRATED (this task is not an effectiveness task), `product_readiness` unchanged,
`publication_readiness` unchanged.

## 1. How the pins were verified

All reads were free public metadata. The query strings and dates are recorded in `registry.json` `source_keys`. Sources:

- **Hugging Face Hub API** `GET /api/datasets/<id>`, read 22 Nov 2026. It gives the commit sha, `gated`, `lastModified`,
  the card license, the config list and the file names (siblings). For original NitiBench, the statute corpus and
  ThaiOCRBench, `cardData.dataset_info` also gave column names and split counts.
- **datasets-server `/size`**, for Gazette and WangchanX row counts. This is a counts endpoint and returns no rows.
- **Hugging Face model search** `GET /api/models?filter=dataset:<id>`, to find models that declare training on each dataset.
- **Card text at the pinned revision, grep-limited.** Only the provenance, license and training-data lines were read from
  these cards:
  - original NitiBench;
  - ThaiOCRBench;
  - WangchanX-Legal-ThaiCCL-RAG;
  - the Typhoon-S legal-agent model card.

  No example rows were printed. The Gazette and NitiBench+ cards were **not** re-read in this task.
- **ACL Anthology page meta tags**, for the NLLP 2026 Gazette paper.
- **arXiv export API**, for the versions of 2611.03576, 2601.18129, 2502.10868 and 2511.04479.
- **GitHub API**, for the `vistec-AI/nitibench` license and HEAD, and the `scb-10x/typhoon-s` license.

Local check: no copy of any Thai dataset exists in the Hugging Face cache or under `C:\Users\User\Desktop\myProject`. The
only Thai rows in the repository are the synthetic G02 fixtures. dr-train was not checked in this task. G02 and the owner
audits record no Thai download there.

## 2. Resource table

The table rows are separate scoreboards (§3). "Dev" means rows may tune, design or select a method. "Held-out" means a
frozen method may be scored on the resource.

| Resource | Pin | License / terms | Gating | Unit | Native metric | Splits | Dev use | Held-out use |
|---|---|---|---|---|---|---|---|---|
| **Thai Royal Gazette evidence retrieval** `VISAI-AI/thai-gazette-evidence-retrieval` (NLLP 2026) | dataset `87e695ee4951ff34932804431433ac55991ec374` (modified 2026-09-21). Paper: Suyasri, Akarajaradwong, Chaksangchaichot, *An Empirical Study of Evidence Retrieval for RAG over the Thai Royal Gazette*, Proc. NLLP 2026, pp. 212–236, <https://aclanthology.org/2026.nllp-1.19/> | CC BY 4.0 for questions, qrels and spans. The card states no separate license for the OCR notice text. Attribution required. | none (`gated=false`) | query × notice, with qrels deduplicated by `(query-id, corpus-id)`; span rows kept separately | doc Recall/nDCG and character-union span recall/precision (paper §4.4); no answer labels | corpus 25,000; queries 2,000 (1,500 single-source, 500 multi-source); `default/test` 2,594 qrel/span rows; **no native DEV** | **None.** Use synthetic fixtures and separately sourced material. Never carve DEV from the test qrels. | Exposed public transfer, after the controller, prompts, budgets and preprocessing are frozen. PTP-proposed endpoints: nDCG@10 primary; Recall@20 and complete required-source coverage@20 secondary. |
| **Original NitiBench** `VISAI-AI/nitibench` + corpus `VISAI-AI/nitibench-statute` | `9f75697075e0f5691e3b821037b908c05f1821a7` (2025-11-26) + statute `069e774f015a50e801dbe2055a29be580c54a83c`. Paper: EMNLP 2025 (doi 10.18653/v1/2025.emnlp-main.1739), arXiv:2502.10868v4 | MIT (both cards). NitiBench-CCL is derived from WangchanX-Legal-ThaiCCL-RAG (MIT). The eval code repo `vistec-AI/nitibench` (HEAD `f3965760…`) has **no license detected**, so do not copy its code or run its setup script, which downloads test data. | none | question → relevant statutory section (retrieval) and answer (end-to-end). CCL has one positive section per question (WangchanX test card). | Retrieval hit/recall/MRR family; the end-to-end answer metrics use an LLM judge. Exact definitions must be re-verified from the paper before any freeze. | `ccl` 3,729 and `tax` 50, **both TEST**; statute `ccl` 5,127 sections (no Tax corpus released) | **None** (public test). The related WangchanX train split (8,211) is a candidate Thai legal DEV source only with owner download approval. | Optional conventional control, deterministic section-level retrieval only, with specialist exposure reported next to each comparator. |
| **NitiBench+** `VISAI-AI/nitibench-plus` | `41286bcb1eeba6721c03d581d4ca3095a1b7f7b7` (modified 2026-11-03; card v1.0, 1 Nov 2026). Paper arXiv:2611.03576**v3** (16 Nov 2026) | CC BY 4.0 (card metadata). A `LICENSE` file and canary exist (not opened). Preserve the canary and any training-use condition. | **auto-gated**, not accepted; datasets-server returns 401 | case with sub-questions; evidence is a section version joined by `version_uri` | Bar-standard answer score, graded by the release's judge prompt and rubric (file names only seen), plus Citation F1 diagnostic | public validation 498 cases / 1,228 sub-questions / 3,253 gold section versions; private test 500, reserve 672 (unavailable) | **None.** The public validation is an evaluation set. | Optional companion under a native named setting only: `parametric_public_validation`, `gold_cited_in_force_public_validation` (oracle evidence, not discovery), or a separately declared PTP update extension. An index of gold sections is answer-conditioned and is never called native retrieval. |
| **Real Thai document packets** `PTP_authorized_thai_packets` (+ `PTP_supplied_document_tasks`) | none yet (NOT_COLLECTED / NOT_DEFINED) | Per-source rights manifest, or original synthetic material. A public patent-search service is not a redistribution license. | n/a | source family (variants grouped) × predeclared question | required-evidence correctness and scope-binding accuracy (score contract §C) | start with 10 synthetic or licensed packets, then a pilot of about 60 families (feasibility target, no power claim) | Separate development families | Held-out families, and agencies/templates where feasible; judgments isolated from policy design (P3-T02) |
| **OCR diagnostics** `typhoon-ai/ThaiOCRBench` (+ `PTP_packet_ocr_diagnostics`) | `ca610d1ab33059e721251137ab1f19f936b87648` (2025-12-02). Paper arXiv:2511.04479v3 (IJCNLP-AACL 2025 per card) | **CC BY-SA 4.0**: share-alike binds any derived annotations; never bundle | none | image + question sample across 13 tasks | task-specific metrics in the paper (not re-verified) | single `test` split, 2,808 | **None.** Its local files are `data/test-*`, which the G02 path policy refuses to open. | Diagnostic of a frozen parser only. Never a retrieval, scope or applicability score. |

Related training source (not a scoreboard): `airesearch/WangchanX-Legal-ThaiCCL-RAG` at
`654e1a10afc44ecaee36fd739bc90078dcc62388`, MIT, train 8,211 / test 3,742, NOT_DOWNLOADED. Its test split is treated as the
same held-out set as NitiBench-CCL (3,729 after derivation).

## 3. Separate scoreboards (enforced)

`registry.json` declares exactly six scoreboards:

- `thai_gazette_retrieval`;
- `nitibench_original` (NitiBench + its statute corpus);
- `nitibench_plus`;
- `supplied_document_tasks`;
- `fresh_structural_packets`;
- `ocr_diagnostics`.

Every Thai resource belongs to exactly one. `thai_contract.assert_single_scoreboard(rows)` refuses three kinds of results
table:

- a table that mixes scoreboards;
- a row labelled with the wrong scoreboard;
- a NitiBench+ row whose setting is not a native named setting.

Scores are never averaged or ranked across scoreboards. None of these tables appear in the A3 or DAPFAM tables.

## 4. Prior exposure in this project

- **Gazette.** No rows were downloaded, opened or scored. The 22 Nov owner audit records that the public card page
  auto-displayed example rows during metadata reading. **Registry correction:** G02 had recorded the Gazette as
  `not_exposed_in_ptp`. It is now `public_card_auto_preview_and_public_transfer`, so the next Gazette run is an exposed
  public transfer, not fresh confirmation. G03 protocols state that the Gazette is not used.
- **NitiBench+.** Card metadata only (G02, 22 Nov audit). No acceptance and no rows.
- **Original NitiBench, statute corpus, ThaiOCRBench and WangchanX.** This task read their API metadata and the cards'
  provenance and license lines only. No rows or images were read.
- **Packets.** None exist.

## 5. Specialist / training-overlap risk

**NitiBench-CCL family: high.**
- `typhoon-ai/typhoon-s-4b-nitibench-ccl-legal-agent-research-preview` (sha `8ce7dec9…`, Apache-2.0, base
  Qwen3-4B-Instruct-2507). Its card's training data is "Question–answer tasks derived from WangchanX-Legal-ThaiCCL-RAG
  (CCL split)". The card does not say the CCL test was excluded. Its card also says the checkpoint is only meaningful in
  its own agent environment.
- Hugging Face models that declare WangchanX-Legal-ThaiCCL-RAG as training data:
  - `airesearch/WangchanX-Legal-ThaiCCL-Retriever`;
  - `airesearch/LLaMa3.1-8B-Legal-ThaiCCL-Combine`;
  - `VISAI-AI/nitibench-ccl-human-finetuned-bge-m3`;
  - `VISAI-AI/nitibench-ccl-auto-finetuned-bge-m3`;
  - `DuckerMaster/thai-legal-lora`.

These are specialist comparators only. They are never an unadapted backbone and never a zero-shot generalization claim on
this benchmark family.

**NitiBench+.** No model declares it as training data. The release postdates most checkpoints and carries a canary.
Statute text overlaps the CCL specialists for CCL-domain cases.

**Gazette.** No model declares it. Web-pretrained models may have seen the public Royal Gazette notices (unknown). The
questions were written and screened by models whose identities sit in the evaluator-only fields `author_model` and
`judge_model`. Report arms of the same model family separately once those fields are opened at evaluation.

**ThaiOCRBench.** It comes from the same organization as the Typhoon OCR models. Whether the benchmark pages were excluded
from their training is unknown, so disclose this before comparing parsers.

## 6. Blocked pending owner

`permitted_use()` returns *blocked* for every item below until the owner's record is entered in the registry. No download
approval is recorded for any Thai resource, so download, development, selection, training, held-out evaluation and product
bundling are all blocked today. Metadata reads and synthetic fixtures stay allowed.

1. **Downloads** (per-item approval), each at the pinned revision:
   - Gazette `corpus/`, `queries/` and `default/test` parquet;
   - original NitiBench `data/ccl-*` and `data/tax-*`;
   - statute `data/ccl-*`;
   - ThaiOCRBench `data/test-*` (images);
   - the WangchanX train split, as a possible Thai legal DEV source;
   - OCR parser weights (`typhoon-ocr2-2b` / `0.8b`, `PaddleOCR-VL-1.6`);
   - any real Thai document fetched from a public site.
2. **NitiBench+ gate acceptance.** The owner must read and accept the Hugging Face auto-gate conditions personally.
3. **Owner decision on judge-graded scores.** NitiBench+ Bar-standard scores and the original NitiBench end-to-end answer
   scores are judge-graded. Standing rule 12 forbids treating them as PTP ground truth. If they are reported at all, they
   appear only as the benchmark's own labelled score.
4. **Paid calls.** These need an envelope:
   - paper-matched Gazette contextual chunks (DeepSeek V4 Flash, proposed envelope E2);
   - any model run on NitiBench / NitiBench+.
5. **Rights review** before any Thai patent packet. Optional **qualified legal review** for ambiguous packet mappings;
   without it, the project may claim only evidence-binding behaviour.
6. **Whether the original NitiBench control is needed at all.** It is optional (owner 21 Nov §5).

## 7. Code delivered

- **`registry.json`.** New `source_keys`, plus these changes:
  - `thai_contract` blocks added for the Gazette and NitiBench+;
  - new pinned entries for `VISAI-AI/nitibench` (configs `ccl` and `tax`, with labels evaluator-only),
    `VISAI-AI/nitibench-statute` (`statute_ccl`) and `typhoon-ai/ThaiOCRBench` (`ocr_test`, with `answer`
    evaluator-only);
  - a top-level `thai_contract` holding the scoreboards, the planned packet resources and the WangchanX related source;
  - Gazette `product_bundle_allowed` changed from true to **false**, per the owner's 22 Nov release separation;
  - Gazette exposure corrected (§4).

  Config ids for the new datasets use split names, with `native_config_name: "default"`. This keeps the G02 rule that a
  config named `default` is evaluator-only.
- **`thai_contract.py`** (new) provides:
  - `validate_thai_contract`;
  - `load_thai_contract`;
  - `scoreboard_of`;
  - `assert_single_scoreboard`;
  - `permitted_use` (purposes: metadata_read, synthetic_fixture, gate_acceptance, download, development,
    method_selection, training, held_out_evaluation, product_bundle).

  The validator requires a download block when no approval is recorded, and a gate block when acceptance is not recorded.
  It also checks that each license and revision match the registry pin, forbids product bundling of external benchmarks,
  and requires the exact six-scoreboard membership.
- **`adapters.py`.** New `NitiBenchAdapter` builds a question-only `RequestRecord` with a positional locator
  `<split>[<index>]`, because the native rows have no identifier. New `NitiBenchStatuteAdapter` builds a `SourceRecord`
  keyed `law_code/section_num`, with text kept verbatim. Existing adapters are unchanged.
- **Tests:** `tests/test_p3_t01_thai_contract.py`, 36 tests on synthetic, fictional Thai rows.
  - It and `tests/test_ptp_g02_datasets.py` pass together: 63 passed.
  - The wider G01/G02 set also passes: workbench, openrouter profiles, pdf ingest and providers.

## 8. Discrepancies and open points

- The ACL page meta tag prints the Gazette DOI as `10.18653/2026.nllp-1.19`, without the usual `v1/`. It is recorded as
  printed. Resolution was not verified.
- NitiBench+: the card gives 105,402 statute sections and the paper gives 106,041 (both 394,943 versions; owner 21 Nov
  §2). The pool is unreleased, so this does not affect the public-validation role.
- The NitiBench repository has both `data/ccl-*` shards and `data/nitibench-ccl.parquet` / `nitibench-tax.parquet`.
  The registry pins the configured `ccl-*` / `tax-*` files and lists the others as non-config files.
- The NitiBench+ field names that G02 marked *assumed* remain assumed until authorized access.
- Gazette question-type release and span scoring stay governed by G02 and owner 21 Nov §3.2–3.3.

**Next:** P3-T02 (grouped source packets and independent judgments) and P4-T03 can consume `permitted_use` and the
scoreboard checks. Real-data steps wait on §6.
