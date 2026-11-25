# S2 · Thai-first evidence Workbench

**Status:** COMPLETE (D28). **Lane:** Product. **Entry:** S0 handoff. Start alongside S1. **Exit:** a local alpha receipt and a versioned example trace for S4. [Execution receipt](receipts/S2-workbench.md) · [Public samples](receipts/S2-sources.md) · [Saved exports](receipts/S2-example-traces.json).

The [master plan](MASTER-PLAN.md) defines the shared evidence contract. The [research freeze](FREEZE.md) governs research inputs. S2 owns product behavior and display-only sample material. Give S1 the contract version and fixture IDs as soon as they exist. Research labels stay in the evaluator. S2 can ship a deterministic local policy while S3 measures alternatives.

## Outcome

A Thai reader selects a legal document or an English patent, asks a question in Thai, and opens the original passage behind each part of a plain-Thai explanation. Switching the edition, date or dependent claim shows which conclusions changed and which ones survived. A case can finish with partial support and a precise account of the missing link. The user can export the trace and another reader can reopen its citations on the same document versions.

## Existing entry points

| Reuse | Relevant behavior |
|---|---|
| [Launcher](../../scripts/ptp_run.py), [Windows shortcut](../../Start-PTP.cmd) | Existing local service, health, sample bootstrap, doctor, smoke and data-directory options. Keep one user launch path. |
| [Ingestion](../../src/patent_to_pilot/workbench/ingest.py), [Thai analyzer](../../src/patent_to_pilot/workbench/thai_analyzer.py), [structure](../../src/patent_to_pilot/workbench/structure.py) | Preserve original bytes, PDF text-layer page mapping and original Thai spelling. Treat searchable normalization and reader-visible text as distinct views of one version. |
| [Core](../../src/patent_to_pilot/workbench/core.py), [workflow](../../src/patent_to_pilot/workbench/workflow.py), [acquisition](../../src/patent_to_pilot/workbench/acquisition.py), [trace schema](../../src/patent_to_pilot/workbench/schemas/evidence_trace.schema.json) | Reuse Search, Compare, Inspect, existing budgets, local store and trace identities. Check existing callers before extending a schema. |
| [HTTP actions](../../src/patent_to_pilot/workbench/server.py), [browser bundle](../../src/patent_to_pilot/workbench/static/), [existing fictional sample](../../src/patent_to_pilot/workbench/sample/) | Serve Thai-first views in the Workbench. The existing sample has its own CC0 notice. The sample is useful for engineering checks and remains visibly fictional. |

## Work packages

| Task | Implementation and decision | Acceptance evidence |
|---|---|---|
| **S2-T01 · Select two demo families** | Select one real Thai act with a prior version and amendment, and an English patent publication with a dependent claim. Assign display-only family IDs; keep the entire family out of policy tuning and evaluation. Start with the candidates below. Track original URL, publisher, document ID and edition, retrieval timestamp, SHA-256 of original and canonical text, exact page or section locator, license evidence, permitted use and attribution for every asset. | Each selector entry resolves to a version. The manifest distinguishes permission to download, inspect, quote, redistribute documents, and redistribute derivatives. If bundling is unresolved, ship the link/import recipe where allowed and continue offline work with the existing fictional material. Describe exactly which paths work offline. |
| **S2-T02 · Preserve structures and locators** | Map Thai sections, paragraphs, explicit cross-references and commencement clauses; map English claims to their stated parent and retain qualifiers. Identify issue and effective dates separately, including transitional provisions. Model table/footnote bindings only where the source exposes an unambiguous header or locator. Preserve original English, Thai numbers and raw offsets; keep normalized values for search. | Small fixtures exercise a Thai digit, two editions with identical section numbers, one missing effective date, a dependent claim, separate embodiments, and a referenced table. Offset inspection reproduces the recorded span. A text-layer PDF does not acquire invented coordinates or cell bindings. |
| **S2-T03 · Connect one scoped action loop** | Use the existing search, requirements and acquisition paths. For each requirement record spans and scope (source, version, parent, and applicable date or example when evidenced). First retrieve with the frozen baseline, then select the least expensive eligible next action: keep, rerank available evidence, acquire missing support, or return a qualified result. Start from a deterministic fixed policy. Record action, reason, budget consumed, candidates accepted/displaced and bound evidence. Prevent candidate text or a model-generated search hypothesis becoming asserted evidence by itself. | Replay one case with complete support, one with eligible evidence below a distracting span, and one with missing compatible evidence. Show which action occurred, candidate identity before and after, and what was actually supported. A zero-remaining-budget case returns the known evidence and the unresolved requirement. |
| **S2-T04 · Explain and inspect** | In Search/Compare, expose a short Thai explanation, inherited versus newly added material, the applicable edition and any grounds for uncertainty. Keep English patent text next to its Thai gloss. Selecting a clause or graph edge opens Inspect on the exact recorded version and span. Distinguish source-stated relations from system inferences using both words and visual style. A source-bound relation still needs a check that its meaning supports the displayed claim. | The same evidence trace drives the explanation, node/edge display, accessible text list and export. Keyboard selection opens the same passage as pointer selection. A version switch updates the affected evidence, retains independent conclusions and allows comparison with the earlier trace. |
| **S2-T05 · Persist and hand off the alpha** | Reuse the local project store, capture input and policy identities and implement a versioned export if the existing export cannot carry the new fields. Include source links and evidence spans only within the asset's redistribution rights. Retain the source identifier, locator and hash when a quote cannot be exported. Add targeted regressions that exercise the normal HTTP workflow, persist an older run and reopen it after a source change. | Restart preserves a run and resolves its original citations. A rerun on the amended source has a distinct version reference. An explicit unresolved state replaces broken links. Publish the alpha receipt and give S4 the launch path, fixture IDs, license outcomes, known gaps and replay instructions. |

### Candidate public demo sources

- **Thai law.** Start with the Electronic Transactions Act B.E. 2544, its amendment No. 2, and No. 3 B.E. 2562. Amendment No. 3, section 7 is a locatable candidate for explaining the change to section 9. Check the deposited editions, commencement provisions, page references and terms for the selected files before binding dates or packaging excerpts. This is a source-selection lead, not an approved interpretation or a bundled dataset. [ETDA source index](https://www.etda.or.th/th/Useful-Resource/laws-sharing.aspx) · [ETDA copy of the amendment](https://www.etda.or.th/getattachment/fd89f39c-c28f-41ef-a3c6-9d90554a3d67/Electronic-Transactions-Act-%28No-3%29-B-E-2562.aspx)
- **English patent.** Inspect US20140137391A1, *Paper clip*, as a low-complexity candidate for showing how a dependent claim narrows claim 1. Verify the publication ID, claim numbers, dependency and any third-party notices against the official record before accepting the packet. Record the allowed uses of text separately from drawings. [Publication text](https://patents.google.com/patent/US20140137391A1/en) · [USPTO Patent Public Search](https://www.uspto.gov/patents/search/patent-public-search) · [USPTO terms](https://www.uspto.gov/terms-use-uspto-website)
- **Product retrieval.** Start the local route with the existing lexical engine. A multilingual embedding route is optional; BGE-M3's card declares MIT. Check and pin the exact revision, dependencies and notices before distributing a model. Keep PatEmbed, DAPFAM, their indexes and research-only evaluation resources outside the product bundle and default runtime. [BGE-M3](https://huggingface.co/BAAI/bge-m3) · [PatEmbed](https://huggingface.co/datalyes/patembed-base) · [project rights audit](../tracking/owner-note-22112026/receipts/P3-T01_thai_data_contract.md)

### Reader-level checks

| Example | What to inspect |
|---|---|
| Thai sample question: “มาตรานี้เปลี่ยนอย่างไร และมีผลตั้งแต่เมื่อใด” | The date switch changes only the conclusions bound to the amendment. Clicking the cited commencement text explains the effective date. If that text is absent, the date remains unresolved. |
| English patent, Thai question: “ข้อถือนี้เพิ่มอะไรจากข้อแม่” | The answer distinguishes parent features from the newly added qualifier. The original and translation preserve quantities and scope. Evidence from an alternative embodiment cannot silently satisfy a claim bound to another. |
| Negative control | A harmless wording change leaves the result stable. Removing or replacing the only compatible support downgrades that conclusion. A disappearing quotation stays traceable to its earlier version. |

## Exit, exceptions and restart

Start S4 on the first reproducible local slice. For **engineering alpha**, one end-to-end path per domain on rights-cleared or visibly fictional packets, resolving citations, a replayable trace, and a recorded failure/abstention example suffice. A missing lawful source bundle or unavailable independent reviewer is a named deferral; the receipt must name the actual sample type and cannot claim a real public-data demonstration on fixtures alone. A full public-data demo in S4 requires real sources or a verified permitted import path in both domains.

The [S2 receipt](receipts/S2-workbench.md) records normal-entrypoint checks, the code gate and replay instructions. Raw captures are private and pinned. Use a new data directory for independent reproduction, or reuse the same directory to reopen an existing trace. S4 owns the clean-install and user-validation gate.

## Dispatch status

| Task | State | Receipt |
|---|---|---|
| S2-T01 | COMPLETE | [Sources and reuse](receipts/S2-sources.md) |
| S2-T02 | COMPLETE | [Source spans and version tests](../../tests/test_scope_reader.py) |
| S2-T03 | COMPLETE | [Action and abstention checks](../../tests/test_scope_reader.py) |
| S2-T04 | COMPLETE | [Chromium workflow](../../tests/test_scope_reader_browser.py) |
| S2-T05 | COMPLETE | [Replay and dispatch](receipts/S2-workbench.md) |
