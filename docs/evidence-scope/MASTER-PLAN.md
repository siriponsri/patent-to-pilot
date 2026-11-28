# Evidence-scope program · historical board

Dispatch moved to the [RA Pharma master plan](../ra-pharma/MASTER-PLAN.md) on 26 November 2026, then to LOE-Bench under D40 on 27 November. The active dispatch is the [Market Window Dossier plan](../loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026) under D41, with LOE-Bench as its benchmark. This board preserves the S0–S5 phase definitions and receipts.

**Effective 25 November 2026 · S0 through S4 complete at their recorded scope · Option A controlled primary NULL.**

Build a Thai-first reader that explains a legal provision or patent claim, shows the source of each condition and lets a reader see which conclusions change when the edition or claim changes. Study the same engine under a fixed search budget. Its hardest case is a plausible explanation assembled from real passages that refer to different editions, tables or embodiments.

A reader comparing two laws should be able to see *which exception changes the answer and on which date*. A Thai reader comparing two English patents should be able to see *what claim 7 inherits from claim 1, what it adds, and whether the two proposed features occur together*. Returning the right PDF alone cannot answer either question.

## Status and dispatch board

Each row has one execution sheet with stable task IDs. S1 and S2 ran together. S3 and S4 subsequently closed at the scopes below. Keep this table and the task dispositions and receipt links in each phase sheet current when work resumes. Preserve prior evidence under its original identifiers.

| Phase | Workstream and outcome | Starts after | State | Completion evidence or next action |
|---|---|---|---|---|
| [S0 · Organization](00-organization.md) | Governance, baseline inventory, prospective freeze, documentation and handoff | Owner direction | **COMPLETE** | This package and the S0 acceptance record |
| [S1 · Research data](01-research-data.md) | Authorized input manifests, family isolation, three-state fixtures, comparator design | S0 and D28 | **COMPLETE** | [Frozen packet, rights, scorer and comparator](receipts/S1-20261125.md) |
| [S2 · Product workbench](02-product-workbench.md) | An end-to-end Thai-law and English-patent reading path using one shared contract | S0 and D28 | **COMPLETE** | [Local alpha, ten public families and 23 saved traces](receipts/S2-workbench.md) |
| [S3 · Research evaluation](03-research-evaluation.md) | Matched DEV experiment, error attribution and independent result labels | S1 | **COMPLETE** | [NEGATIVE Thai primary](../healthtech/audits/S3-20261125/RESULTS.md). Uninformative English transfer |
| [S4 · Product validation](04-product-release.md) | Reproducible local alpha, rights, installation and usability evidence | S2 | **COMPLETE** | [Windows local alpha and local public-data demo READY_FOR_REVIEW](receipts/S4-integrated-verification.md) |
| [S5 · Synthesis and handoff](05-synthesis.md) | Research package, IS2 narrative and product release decision | Either finished lane for its own draft; both dispositions for closure | **NOT_STARTED** | Publish only evidence that each track actually obtained |

The [prospective freeze](FREEZE.md) governs S1 and S3. The new primary is controlled Thai DEV scope-complete success under a maximum of four retrieval actions and eight returned evidence units. English patent transfer is reported separately. Global patent-family retrieval remains a distinct benchmark objective. It fixes the questions, dataset roles, comparison and decision design. S1 pinned its immutable file lists, revisions and hashes in the [release manifest](research/manifest.json). The [historical P0–P5 board](../tracking/owner-note-22112026/PHASE_BOARD.md) retains its 35 original tasks and their outcomes. The [handoff](../../HANDOFF.md) records the next writer, last verified checkpoint and accounting context.

## What both tracks implement

Model the **question**, the **document scope** and the **retrieval trace** separately. Legal scope can depend on an instrument, provision, effective date, exception or incorporated schedule. Patent scope can depend on a publication, a claim's dependency path or an explicitly identified embodiment. A parser records the available scope and preserves unknown values. A missing embodiment identifier cannot justify combining two examples.

| Shared record or operation | Contract between research and Workbench |
|---|---|
| Requirement | A stable ID and an explicit condition, with its original-language text. Keep Thai explanations alongside the English patent source. |
| Evidence | Source ID, revision, content digest, exact locator and excerpt. Store the applicable scope and its provenance. A verified quote establishes text identity; semantic support needs a separate decision. |
| Relation | Typed endpoints, source span, explicit or inferred origin and uncertainty. Examples include “inherits”, “takes effect”, “excepts” and “supports”. Only inspectable edges enter the reader's evidence view. |
| Retrieval state | A requirement-by-evidence table retaining missing, supported, conflicting and scope-incompatible items. Preserve the original ranking for comparison. |
| Action | Keep or rerank the current pool, run a bounded search for the missing scope, or stop and qualify the answer. Store action, affected candidates, cost and reason. |
| Output | Plain Thai explanation, cited original text, changed and stable conclusions and an exportable trace. Node/edge rendering is a view of that trace. |

```mermaid
flowchart LR
    Q["Question + selected documents"] --> B["Lexical and dense retrieval"]
    B --> T["Requirements × scoped evidence"]
    T --> C{"Evidence applies together?"}
    C -->|Sufficient| E["Explain with exact sources"]
    C -->|Conflicting or missing| A{"Bounded next action"}
    A -->|Select better evidence| T
    A -->|Acquire a missing scope| B
    A -->|Budget reached| U["Explain the unresolved condition"]
    E --> W["Reader, comparison and node/edge view"]
    U --> W
    T -. action trace .-> V["Separate evaluator"]
```

The prototype starts with one local agent and a deterministic policy. Skill optimization edits task instructions. Harness optimization selects from versioned retrieval, allocation and stopping rules. An optimizer cannot edit the evaluator, source permissions or budget ledger. A benchmark adapter and the Workbench should consume the same trace schema. Keep the product fixtures and research score fixtures in separate families.

## Closest alternatives and the claim worth testing

| Evidence | Implication for design |
|---|---|
| [FinDeCrowd-RAG](https://arxiv.org/abs/2609.35782) corrects scope-induced displacement within a candidate pool. [MAP-Law](https://arxiv.org/abs/2605.01486) uses evidence coverage to control another search. | Compare against both capabilities combined with equal opportunity to search. Test what happens when the right passage is absent from the initial pool. |
| [Conjunctive cross-page retrieval](https://arxiv.org/abs/2607.24165) studies documents satisfying every requested condition. [FiNE-Patents](https://arxiv.org/abs/2605.02392) studies feature evidence within supplied prior art. | Include cases with all terms present but incompatible scopes, plus valid cross-page evidence. Distinguish global discovery from locating evidence in a supplied document. |
| [SkillOpt](https://arxiv.org/abs/2605.23904) learns editable skills. [SkillOpt-Lite and HarnessOpt](https://github.com/EvolvingLMMs-Lab/SkillOpt-Lite) can edit execution routines. | Retain skill-only, harness-only and joint variants. Budget the search for a policy as well as inference. Select on permitted development inputs. |
| [FourCorners](https://aclanthology.org/2026.acl-demo.46/) supports version-aware legal reading. [Thanoy](https://thanoy.ai/mcp) and [Thai Legal](https://legaltech.in.th/docs) provide legal search with sources. [DIP](https://search.ipthailand.go.th/invention-patent) and [PATENTSCOPE](https://www.wipo.int/en/web/patentscope) provide patent discovery. | Compare concrete reader tasks, including opening the passage responsible for a changed answer. Published feature descriptions do not establish comparative accuracy, market demand or willingness to pay. |
| [LightRAG](https://github.com/HKUDS/LightRAG) offers a reference for a locally accessible interface and graph exploration. | Target a simple first run. Compare on the same licensed documents and questions where accessible; record indexing and query costs separately. |

The closest-work search was conducted in SciSpace. Inspect the paper records for [FinDeCrowd](https://scispace.com/papers/financial-evidence-crowding-diagnosing-and-mitigating-7p927nwzciku), [MAP-Law](https://scispace.com/papers/map-law-coverage-driven-retrieval-control-for-multi-turn-bo0fkeuz3qvy), [conjunctive retrieval](https://scispace.com/papers/do-current-retrievers-cover-all-the-evidence-a-controlled-lzmup7t3rho7) and [FiNE-Patents](https://scispace.com/papers/is-it-novel-and-why-fine-grained-patent-novelty-prediction-n20ovv4rr4r0). This targeted comparison motivates a falsifiable test. It establishes no priority claim.

## Delivery and evidence gates

- A lane advances with its smallest inspectable artifact. A hand-checkable synthetic example can unlock engineering. A local demonstration can ship as an alpha under its documented rights and limits, including when a research arm fails. Real-user or commercial impact remains unmeasured until observed.
- S3 can close with a positive, mixed, null, negative or diagnostic result. A positive paired primary DEV estimate permits one bounded follow-up under the freeze. Stronger claims require a matched comparison, uncertainty and the documented independent evidence for the claim. A legacy P2 score win still has its own original criterion. Q1 is a publication ambition.
- Protected TEST stays closed. Keep unjudged material unknown. Maintain family isolation, licenses, source provenance and separate research and redistribution rights. DAPFAM and PatEmbed are research-only. Demo distribution needs an affirmative source-by-source rights record.
- The owner authorizes in-scope installs and dataset downloads for this direction. The organization-only checkpoint performed neither. When execution is activated, record source, version, license, intended use and digest. Third-party gated terms, new expenditure or unclear redistribution rights remain separate decisions. Historical R1/R2/E1R balances cannot be reassigned to new tasks by this plan.
- A solo maintainer can run either lane sequentially or delegate disjoint files. Record the writer and jobs in HANDOFF. Keep one contract owner. A research finding can change a later product policy only through a versioned change and product regression check.

## Closed dispatch and deferred synthesis

The [S3 executor prompt](S3-EXECUTOR-PROMPT.md) records the completed S3 dispatch. S4 is independently complete at its qualified Windows level. Option A's [v2 original and independent audit](alternative-evidence/RESULTS.md) closed with a Thai controlled NULL result and diagnostic-only architecture evidence. The same evidence-opening sequence occurred in all arms on the authored packet. S5 remains pending.
