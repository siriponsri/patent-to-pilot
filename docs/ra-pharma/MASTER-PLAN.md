#

Owner authorized impact-driven redirection within D39. The [Planner field evidence review](ip-pharma/D39-FIELD-EVIDENCE.md) prioritizes the Thai pre-submission decision and documents the separate patent-to-counsel workflow. Batch releases remain prospective.

**Owner approved option A.** [D39 public opportunity discovery](ip-pharma/D39-DECISION-REQUEST.md) authorizes up to twelve batches. Batch 1 released for protocol lock; Product held.
**D38 closed after independent review.** [Planner impact review and handback](ip-pharma/D38-IMPACT-REVIEW.md). Two ties on two synthetic inventories. Keep the checklist and park the proposed Product feature. Operator benefit remains unmeasured.

**D36 reviewed.** Prioritize a synthetic rituximab evidence-readiness desk check for owner decision. Generic formulation and Thai market sizing are parked. [Planner review](ip-pharma/D36-REVIEW.md)

The [remaining phase proposal](ip-pharma/REMAINING-PHASES.md) recommends D36 opportunity discovery next and maps the separate research and Product decisions through M7. Execution status follows the D37 review below.

**D37 closed after independent review.** Original labels 24/24, locally usable exact-edition pairs 22/24. One processing deviation and one unresolved formulation. All optional checks NOT_CHECKED. [Planner handback](ip-pharma/b1e/PLANNER-REVIEW.md)

**B1 review, 27 November.** BLOCKED_FRAME accepted. Both FDA ZIPs passed verification. Family mapping and exposure coverage could not be established before selection. B1-ext and scoring are NOT_RUN. [Independent review](ip-pharma/PLANNER-REVIEW.md)
 RA Pharma Workbench

Owner decision of 26 November 2026. Patent-to-Pilot keeps its repository name. The product is a Thai-first regulatory affairs workbench for a solo operator. Three specialists work from one product dossier and produce a patent claim chart, a registration evidence checklist and an editable letter. The research question is whether learned reading actions and evidence handoffs improve results on unseen dossiers under a matched budget. The next phase prioritizes architecture research. The [research-first study](RESEARCH-FIRST.md) governs active work.

## Dispatch board

| Milestone | Writer and branch | Starting state | Inspect at handback |
|---|---|---|---|
| Planning and common evidence interface | Planner on main | Prepared | This board, [handoff contract](EVIDENCE-CONTRACT.md), both lane briefs and branch pointers |
| IS1 continuity and adaptive reading study | GPT 6.2 Sol, medium for the next session on `research/ra-pharma` | Owner parked all eight IS1 scores. Patent and Thai FDA conformance reviewed. Two-read dossier comparison tied 15/24. R4 natural transfer remains NOT_RUN. | [Research tasks](research/BRIEF.md), [Planner audit](RESEARCH-AUDIT-20261126.md) and [architecture review](READING-ARCHITECTURE-REVIEW.md) |
| Three-specialist local dossier | Claude Opus 5.5 medium on `product/ra-pharma` | P1–P5 local demo published. Further development deferred until research review | [Product tasks](product/BRIEF.md) and [product handoff](product/HANDOFF.md) |
| Integration and claim review | Planner on main after lane receipts | Pending | Verify branch heads, evidence compatibility, clean launch, rights and the suite on the integrated revision |

### From one question to one letter

The [current architecture review](READING-ARCHITECTURE-REVIEW.md) connects reading depth to branch-specific evidence and missing-item requests. The EPO source preflight is published on the Research branch. Complete exclusion coverage is still missing. The first branch-reading check uses exposed developer material.

The [D31 independent source key and audit](THAI-INQUIRY-AUDIT.md) cover 11 inquiry issues in seven official opinions. The sealed primary tied at 3/11 complete answers. The closed follow-up linked 7/7 adjudicated issues in four new opinions. All three selectors returned incomplete extracts on those seven. One further issue was unjudged. The six handoff cases and 12 synthetic dossiers stay closed.

For a fictional taste-masked tablet, the patent agent compares the product facts with inherited and added claim limitations. A country-specific FTO evidence file records the missing legal-status checks. The regulatory agent maps applicable Thai registration requirements to the applicant's evidence and identifies missing attachments. The correspondence agent reads the questions on a sample incoming letter and drafts a reply in the sender's template. A reviewer can open the precise page behind a sentence, see which product it describes, and decide whether to sign. The product operator controls issuance.

The first demo covers Thai correspondence, an English patent and Thai registration guidance alongside an English ASEAN source. Foreign legal support is organized by authority, jurisdiction and effective date. A regional guideline or a US patent publication alone cannot establish the law or patent status in Thailand. A foreign-country regulatory pack is a later extension with its own official sources and fixtures.

The learning loop records a corrected decision, proposes a versioned change to a reading skill, tests it on different development families and checks regressions before promotion. Keep the old version for replay. Preserve the identity of the model, prompts, tools, skill and harness in each trace. A static demonstration of this loop earns an engineering result. A claim of transfer requires the research comparison.

## Planner dispatch evidence

For every Planner assignment, proposal or substantive claim, cite a relevant primary research paper and identify a benchmark or named competitor. Link both sources and explain which task, metric or product workflow they support. Distinguish a measured head-to-head result from an external reference or an untested hypothesis. For example, rhetorical-role tagging in Indian judgments informed a hypothesis about selecting conclusions and qualifications. The actual Thai comparison measured complete answers under identical page and extract budgets. [LegalSeg](https://aclanthology.org/2025.findings-naacl.63/) · [Matched Thai benchmark](https://github.com/siriponsri/patent-to-pilot/blob/93f3705e38907bc2ee0c12a7471b0bc683ca6eef/docs/ra-pharma/research/official-correspondence/page2/RECEIPT.md).

## Concurrent work

Use the [research-first start](RESEARCH-FIRST.md#read-only-starting-prompt). The [original lane prompts](SESSION-PROMPTS.md) document the initial allocation. At every task close each writer updates the affected English documentation, their HANDOFF and their lane MEMORY.md. Use the [repository writing skill](../../.agents/skills/ra-pharma-writing/SKILL.md). The [shared memory](MEMORY.md) carries accepted lessons across the two branches.

Use one checkout per branch, based on the published planning revision. Check the selected branch, model and effort at startup. An unavailable requested configuration goes back to the owner. On a lane branch, update its HANDOFF at each decision, failure, before a long job and at closeout. That is the branch's project handoff. Push only that lane to origin. The Planner owns the root handoff, board, shared interface, tool configuration shared by the lanes and integration into main. Propose a change to the interface in the lane handoff with a fixture showing the need. Both lanes may continue with the published version while the Planner reviews the proposal.

| Owner | Writable areas |
|---|---|
| Research | `docs/ra-pharma/research/`, `scripts/research/ra_pharma/`, `tests/ra_pharma_research/`; separate private research captures |
| Product | `docs/ra-pharma/product/`, `src/patent_to_pilot/workbench/`, `examples/ra_pharma/`, `tests/ra_pharma_product/`; launcher and its normal entry script if required; separate private product workspace |
| Planner | Root instructions and navigation, shared contract, integration, root dependency files, historical tracker routing |

The owner authorizes necessary project-local skills, harnesses, tools and MCP integrations. Start from the existing Python launcher, SQLite FTS5, PDF extra and QA harness. A branch may install a necessary tool in its own project environment and record its source, version or commit, digest, license, purpose, network behavior and smoke result in its handoff. Request integration for shared dependency edits. Use synthetic or cleared material for cloud tools. Project-local installation authority does not authorize new paid envelopes, acceptance of gated terms, external filing or publication. Scope any remote work under the existing [resource rules](../../CLAUDE.md).

## Evidence carried forward

The [S4 receipt](../evidence-scope/receipts/S4-integrated-verification.md) establishes the existing Windows reader, source verification and recovery. The [IS1 bridge](../healthtech/audits/S3-20261125/BRIDGE.md) identifies the unrun depth matrix. [S3](../healthtech/audits/S3-20261125/RESULTS.md) closed negative and [Option A](../evidence-scope/alternative-evidence/RESULTS.md) closed null. Neither run measured the three-agent system. The former [S board](../evidence-scope/MASTER-PLAN.md) and P registry remain evidence indexes. S5 synthesis is deferred. Research, product readiness and publication readiness are reported separately.

## Current research checkpoint

Overnight Phase 1 closed at its portfolio scope; the dossier replay passed on Planner's machine. Both the original three-case intake and same-case metadata recovery closed with zero admissions. The [final Planner review](ip-pharma/OVERNIGHT-REVIEW.md#owner-handback) records the verified artifacts and the reason no fresh policy comparison ran.

For the new owner-requested IP Pharma portfolio direction, the [architecture report](ip-pharma/REPORT.md) is the current proposal. Landscape and public engineering pilots are complete. The proposed next Research deliverable is one pharmaceutical dossier showing the exact listing, grant ancestry and missing Thai evidence. Fresh comparative evaluation, customer validation and Product implementation are pending. Compare the architecture against [PatentAgentBench](https://arxiv.org/abs/2610.35031), [Priorbit](https://github.com/Lawless-Inc/priorbit) and the exact-checklist control. The entries below preserve the earlier unchanged-source pilot.

The [feasibility review](RESEARCH-FIRST.md#feasibility-review-and-owner-checkpoint) is complete. The owner selected unchanged-source checking. New baselines remain NOT_RUN.

The owner approved unchanged-source checking. The [Option A checkpoint](OPTION-A-IMPORT.md) supersedes the earlier pending choice. The first exposed zero-shot run is recorded below.

The [first live zero-shot observation](OPTION-A-IMPORT.md#first-commercial-zero-shot-observation) is complete on exposed material. Both tools recovered the material qualification. Fresh confirmation, the same-model mechanism comparison and human time savings remain unmeasured.

The [owner-requested repeat](OPTION-A-IMPORT.md#owner-requested-repeat-and-chat-preservation) reproduced the material answer on the same issue. Private chat preservation is verified. No new family was enrolled.

## Discovery and market research

D36 adds three portfolio questions. The US provides an initial public-data example. Geography for commercial decisions remains open, including Thailand. A proposed deliverable is a short opportunity brief per reference product: what warrants R&D attention, which evidence could change that decision, which competitors actually participate in the specified market, and what remains unknown. Each entry carries jurisdiction, date, source and locator.

| Operator question | Evidence and baseline | Limit on interpretation |
|---|---|---|
| Generic pharma discovery: which known active ingredient and reference formulation leave a documented delivery, dosage-form or patient-use gap worth investigating? | Link the exact reference product, formulation and marketed alternatives to the published observation. Compare the hypothesis with the existing formulation and the fixed field-aware checklist. [Orange Book](https://www.fda.gov/drugs/drug-approvals-and-databases/orange-book-data-files) | A reformulation or new indication is a separate development hypothesis. Clinical benefit, feasibility and demand need their own evidence. |
| Biologic discovery: for a biosimilar, which reference product, indication and publicly measured quality attributes define the comparison? For a novel biologic, what target–indication evidence supports further investigation? | Start the biosimilar comparison with the regulator-linked reference product. Lee et al. compared CT-P10 with US and EU rituximab. The issuer review permits checking which comparator supported the US assessment. Keep target hypotheses and product-specific analytical findings in separate fields. [Primary study](https://pubmed.ncbi.nlm.nih.gov/29469653/) · [FDA BLA 761088 quality review](https://www.accessdata.fda.gov/drugsatfda_docs/nda/2018/761088Orig1s000ChemR.pdf) | Evidence from another manufacturer's lots cannot establish similarity of a proposed candidate. Record missing applicant measurements explicitly. |
| Biologics market research: which products are licensed, which show observed use, and how do uptake and spending vary by payer, geography and year? | Map regulator-confirmed reference relationships, then bind utilization and spending to a defined population and period. Use HHS ASPE's Medicare Part B analysis as the public benchmark. Report users or units, denominator, spending currency/year, and source coverage. [FDA Purple Book](https://purplebooksearch.fda.gov/) · [ASPE 2018–2023 analysis](https://aspe.hhs.gov/reports/biosimilars-medicare-part-b) | Approval, launch, use and revenue require distinct evidence. A US payer estimate supports that population only. Thai sizing needs Thai registration, procurement or utilization evidence and a defined market segment. |

Current status is exploratory source mapping. No opportunity ranking, commercial forecast, new cohort or comparative PTP result has been produced. Product remains on hold. Research returned a blocked preflight on its own branch.
