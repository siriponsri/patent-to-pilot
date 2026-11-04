# Patent-to-Pilot: WPI-focused long-run goal and execution plan

**Prepared:** 4 November 2026  
**Target journal:** World Patent Information (WPI)  
**Target working directory:** `C:\Users\User\Desktop\myProject\patent-to-pilot`  
**Working mode:** Continue the existing project on `main`; one writer; no new worktree.  
**Project constraint:** Solo research project. No external experts are available for assessment; do not make expert recruitment, external judgments, or expert approval a prerequisite.

**Document status:** Proposed instructions for Claude Code. Reconcile them with the actual repository, current owner instructions, and verified evidence before executing. This document does not claim that the repository has been inspected by its author.

**Owner amendments, 4 November 2026 (chat). These supersede conflicting text below:**

1. The prospective E2 allowance is raised from USD 1 to **USD 10**, cumulative, including the settled canary spend. The project ceiling of USD 100 is unchanged. Use only the existing canonical runner and ledger. Never reset history, and keep settled, reserved, pending and unknown amounts.
2. Commit **and push** to `origin/main` are authorized once a coherent, verified package is complete, after inspecting the diff and scanning for secrets and private data. Manuscript submission, outside contact and new spending scope remain unauthorized.
3. dr-train (V100, concurrency 1, until 15 November 2026 23:59 Asia/Bangkok) is authorized computation under the existing allocation.
4. The canonical copy of this plan is `patent-to-pilot/docs/healthtech/long-runs/PTP_JOURNAL_LONG_RUN.md`.

## 0. Start here

Continue the existing project and its scientific objective. A new session or Goal is an execution container, not a new study, ledger, budget, or permission to erase unfavorable results.

Design for a solo author: prioritize established, rights-cleared public benchmarks with documented labels, reproducible source-based checks, and feasible owner review with declared limits. Do not invent an expert panel, independent clinical validation, or customer study. A methodological claim must fit the available evaluation design.

The objective is to produce a defensible research contribution and a reproducible manuscript package suitable for the owner to assess for WPI submission. Do not equate a running app, passing tests, schema-valid answers, inexpensive API calls, or polished documentation with scientific acceptance. Do not require a positive result to finish: a properly designed negative or mixed result is a valid research outcome. Journal acceptance cannot be guaranteed.

Use the existing components and evidence wherever they are valid. Repair specific defects, run experiments that resolve a research question, and avoid repeatedly auditing unchanged dependencies. If one branch of work requires external input, continue independent useful work and prepare a precise handoff for the blocked branch.

### First actions

1. Read `AGENTS.md`, `GOAL.md`, `PLAN.md` if present, `HANDOFF.md`, `CLAUDE.md`, current acceptance matrix, current execution plan, and next-actions files. Locate project skills and read only the relevant instructions.
2. Inspect actual branch, full HEAD, remote tracking state, uncommitted changes, active writers, and the current ledger. Do not assume the short SHA or timestamps below remain current.
3. Read the latest Normal and E2 canary audits, private output journal, protocol, dataset manifests, qrels provenance, and research manuscript. Do not print secrets or private output into public logs.
4. Make a short inventory of what is verified, reported but not yet verified, historical, missing, and contradicted. Link to precise evidence rather than duplicating large audit files.
5. Reconcile this plan into the existing `GOAL.md` and `PLAN.md` or equivalent documents. Preserve useful prior requirements, O1–O4 definitions, historical receipts, owner decisions, and unresolved work. Do not blindly replace files or introduce a parallel set of conflicting instructions.
6. Choose the next action that adds evidence. Do not perform another full Normal round solely because a credit snapshot has aged.

## 1. Starting evidence: reported state, to be verified locally

The following comes from the owner's supplied Claude reports, not an independent inspection of files.

- `main` was at short HEAD `e948cd5`, one local commit ahead of `origin/main`, after consolidating the previous Normal patch and audit. Resolve the full SHA and current state before editing.
- The subsequent paid canary created uncommitted audit/document/script changes. Preserve and inspect these changes. Do not reset, clean, checkout, rebase, delete, or overwrite them.
- E2 canary used the existing canonical runner and ledger for three FDA development cases: MITRACLIP, TENDYNE, TRICLIP.
- Model reported: `qwen/qwen3-32b`, DeepInfra fp8. Reported route prices were USD 0.08 input and USD 0.28 output per million tokens. These are historical run parameters, not a fresh price quote.
- Canary: 3 successful, settled calls; no retry; 3,073 input tokens; 1,069 output tokens; summed latency 42.85 seconds; actual cost USD 0.00054516.
- Per case: MITRACLIP 1,017/363 tokens, 14.41 seconds, USD 0.000183; TENDYNE 1,036/356, 16.55 seconds, USD 0.00018256; TRICLIP 1,020/350, 11.89 seconds, USD 0.0001796.
- OpenRouter total usage reportedly increased from USD 0.0001464 to USD 0.00069156. That difference matches the canary cost. A generation lookup for the first case matched its receipt; this is not a claim that all three received individual provider-side reconciliation.
- Four legacy settled records remain. Preserve the unknown-history/cutover state and its provenance; do not rewrite history as zero usage.
- The reported prospective E2 cap remains USD 1, with USD 0.99945484 left after this canary, subject to verifying the ledger for newer settled, reserved, pending, or unknown amounts. The project cap USD 100 is distinct and is not permission to expand the prospective E2 allowance.
- Ledger integrity reportedly passed and its hash changed through the canonical runner, from prefix `d0041eda` to `d19f58ec`. Resolve full hashes from actual receipts; never manufacture them from these prefixes.
- The three outputs are private local JSONL evidence and were not committed. They passed schema validation; content correctness has not yet been established.
- Focused E2 tests reportedly passed 70 tests. Preserve their command, commit, environment, date, and scope. This is not a fresh full-suite result on later edits.
- Earlier corpus/query/qrels counts and O1–O4 results may exist. Audit their provenance and eligibility before reuse; do not discard them simply because they are older, and do not promote historical receipts into current results.

## 2. Intended contribution and journal fit

### 2.1 Research focus

Center the article on a real patent-information task. FDA enrichment can provide useful context, but FDA-only answers do not validate patent retrieval, patent-device mapping, freedom to operate, clinical safety, or commercialization success.

Select **one primary contribution and at most one tightly connected secondary contribution** from what the implementation and available data can support. Possible directions, to evaluate rather than assume:

- A reproducible method for retrieving and connecting patent information with device/regulatory evidence, with explicit provenance and evaluation.
- A source-grounded dossier workflow evaluated for verifiable extraction, citation and traceability properties against a suitable reference workflow. Do not claim professional usefulness without evidence from actual users.
- A cost-aware or adaptive information-processing policy, but only if a fixed-policy comparison and controlled ablations can test its benefit.

Do not call ordinary integration of standard components a novel method without explaining the new contribution and comparing it with close work. Do not broaden into clinical decision support, legal advice, general AI4AI, or unsupported business-impact claims to make the project appear larger.

### 2.2 Research questions

After reviewing the actual manuscript and existing protocol, formulate a small coherent set. For example:

- **RQ1, primary:** For a defined patent-information task and eligible test population, does the proposed retrieval method improve a preregistered retrieval measure compared with specified strong baselines?
- **RQ2, secondary:** Does the evidence-linked dossier/generation workflow improve source-supported factual output or traceability compared with a defined reference workflow?
- **RQ3, supporting:** What are the latency, failure, and cost tradeoffs under the same workload and resource constraints?

Adaptive superiority requires adaptive-versus-fixed experiments. Claims comparing local and API models require matched local-versus-API evaluation. If these claims are not central or cannot be supported, narrow the manuscript rather than run an unfocused model sweep.

### 2.3 Current journal instructions

Consult the official WPI aims and scope, current Guide for Authors, and relevant recent papers. Save the access date, URL, supported requirement, and any inaccessible section.

- Official journal: https://www.sciencedirect.com/journal/world-patent-information
- Official aims and scope: https://www.sciencedirect.com/journal/world-patent-information/about/aims-and-scope
- Official Guide for Authors: https://www.sciencedirect.com/journal/world-patent-information/publish/guide-for-authors
- Official Elsevier description: https://shop.elsevier.com/journals/world-patent-information/0172-2190
- Relevant editorial on IR/ML/NLP contributions: https://www.sciencedirect.com/science/article/pii/S0172219017300601

The direct current Guide for Authors and scope pages were inaccessible with HTTP 403 during preparation. Their detailed current requirements have **not** been verified. Try a permitted route later; do not bypass access controls, infer mandatory limits from an old mirror, or falsely mark the checklist complete. Distinguish actual journal requirements from our methodological recommendations. WPI does not become submission-ready merely by meeting an invented minimum sample count or checklist.

## 3. Scientific evidence plan

### 3.1 Audit existing datasets and qrels before collecting new data

Create a dataset/label manifest covering source, version, access date, rights/license, permitted uses, unit of analysis, identifiers, inclusion/exclusion rules, deduplication, transformations, split, and checksum.

Prefer a two-track evaluation: (A) an established public patent-information benchmark for claims that its task and labels genuinely support, and (B) the HealthTech/device dossier cases as a separate application demonstration and source-grounding audit. Do not transfer a result on a generic patent benchmark into a claim of validated device-patent linkage. Compare candidate public datasets for task fit, label meaning, independence, license, coverage and leakage before selecting one; a public download or an examiner citation alone is not automatically ground-truth relevance.

For every existing query and qrel source, determine:

- Who or what created the query and label, when, using which information, and for what task?
- Is the label expert/human judgment, a citation/link proxy, synthetic, model-generated, or a weak heuristic?
- Did the method under evaluation create, filter, or influence the labels or query set?
- Does the corpus include the text used to manufacture queries or labels in a way that makes evaluation circular?
- Are labels available independently of the evaluated systems, and can another person reproduce their meaning?

Retain valid existing qrels. Route weak or synthetic qrels to development/exploratory experiments with clear labels rather than deleting them. Do not relabel silver/proxy evidence as independent gold. Keep legacy metrics, but qualify them if the audit changes what they establish.

### 3.2 Prevent leakage

Define the independence unit relevant to the claim: query/topic, device family, patent family, organization, or time period. Patent duplicates, continuations, translations, near duplicates, and related device variants can create leakage.

- Deduplicate and group patent families before splitting.
- Keep related queries, family members, and evidence derived from the same case together where needed.
- Where chronological generalization is claimed, use a meaningful temporal cutoff and prevent future information from entering earlier-stage retrieval or labels.
- Separate train/development/final evaluation. Use the three canary cases as development evidence unless their prior exposure is explicitly compatible with a much narrower test claim.
- Do not reuse a final holdout for iterative prompt/model/threshold selection. If it has been exposed, mark that limitation and establish a genuinely independent evaluation if feasible.
- Save the split manifest, grouping rules, hashes, and a leakage-check report before final evaluation.

### 3.3 Labels and assessment for a solo project

Use externally established benchmark labels when they fit the task and have adequate provenance and usage rights. Independence here concerns how the labels were created relative to the evaluated method; it does not imply that an expert has reviewed this project.

For each candidate benchmark, record its actual label semantics, creators, construction method, known noise, time/family structure, and intended task. Citation prediction, semantic similarity, classification and prior-art retrieval are different tasks. Do not rename one as another to make a convenient dataset fit. Public or official labels can still be incomplete or proxy-based; report that limitation.

Reuse valid existing qrels after the provenance audit. If their construction is synthetic, model-generated, or heuristic, retain them as silver/development evidence. Do not require the owner to recruit assessors to finish the project. Instead:

1. Find a lawful established benchmark or source-labeled task that answers a defensible part of the research question.
2. Narrow the scientific claim to that task. Keep novel HealthTech mappings as exploratory unless reliable independent labels already exist.
3. Use deterministic checks against authoritative structured fields for extractive factual claims where that is appropriate.
4. Prepare a small optional owner review of ambiguous/high-impact cases with a written rubric. Declare it as single-author/owner review, not blinded expert validation. Do not block the whole project waiting for it if automated or descriptive work can continue.
5. If there is no valid label source for a proposed claim, omit or downgrade that claim and document the missing validation. Do not fabricate gold labels or use an LLM's confidence as truth.

For any new manual annotations that are feasible within the solo project, record the annotator, rubric, evidence access, uncertainty, and potential bias. A second pass by the same person or a second model is not inter-rater agreement from independent experts. Avoid reporting Cohen's kappa or similar statistics as independent expert agreement unless the underlying design genuinely supports that interpretation.

Candidate pools may be used for exploratory inspection. If judgments are incomplete, record how pooling can miss relevant documents and how unjudged items are handled. Do not automatically count all unjudged documents as nonrelevant without evaluating its effect on the metric.

External expert review, clinical assessment, user studies, business validation, and participant recruitment are outside the executable completion dependency for this solo goal. Preserve them as future work where appropriate. No outside communications, data sharing, or commitments are authorized by this plan.

### 3.4 Sample size and uncertainty

Do not invent a journal-required number of patents, cases, assessors, or queries. Justify sample size from the research question, diversity of tasks, feasibility, planned precision or power, and pilot variation.

Define the independent analysis unit and a meaningful effect size before final evaluation. Use pilot/development data to estimate variability, not repeatedly inspected final-test results. Document resource limits and expected confidence-interval width if a formal power target is infeasible.

Use paired comparisons on matched queries/cases where appropriate. Bootstrap or other intervals must resample independent units, not individual correlated documents or token outputs. Report effect sizes and uncertainty, correct or qualify multiple comparisons, and avoid interpreting a nonsignificant result as equivalence. Equivalence/noninferiority requires a justified margin and suitable design.

### 3.5 Baselines and ablations

Select strong, reproducible comparators relevant to the actual task. A reasonable starting set is lexical/BM25, dense retrieval, and a fixed hybrid reference, subject to existing implementation and related work. Include a relevant established method when a public reproducible implementation fits the task.

Ensure fair comparison: same corpus, eligible queries, label set, preprocessing, evidence access, resource limits where relevant, and documented tuning budgets. Tune on development data only.

Ablate only components needed to test the proposed mechanism, such as reranking, fusion, provenance constraints, regulatory enrichment, or adaptive routing. An adaptive method must be compared with a well-tuned fixed policy under a comparable cost budget. A local/API comparison must specify matching prompts/evidence, output limits, decoding, context truncation, failures, and provider settings. Do not add unrelated models solely to increase experiment count.

### 3.6 Metrics

Choose one primary retrieval endpoint and a limited number of secondary endpoints that answer the task. Candidate measures include Recall@k, nDCG@k, MRR, and Precision@k, but their use depends on label completeness, graded relevance, and the workflow. Define k and aggregation before final evaluation.

For generated dossiers, separate:

- Structural validity and required-field completeness.
- Field-level accuracy against authoritative sources.
- Whether each claim is supported by the cited source passage.
- Citation correctness and coverage, unsupported claims, omissions, contradictions, and calibrated abstention.
- Patent/device linkage correctness when such linkage is claimed.
- Task usefulness only where there is actual suitable user evidence; otherwise describe workflow functionality and leave professional utility validation as future work.

An LLM judge may assist triage or exploratory scoring, but do not treat it as independent scientific truth. Use existing established labeled evaluation where possible and record judge model/version and potential self-preference. Without an appropriate external validation source, keep judge scores exploratory rather than making them the sole support for a main claim.

Operational measures include end-to-end and component latency, throughput, failures, tokens, realized cost, and resource use. Distinguish cold/warm cache and serial/parallel execution. Report denominators, failed cases, and distributions, not only averages or the fastest run. Exclude or include failures only according to the prespecified analysis rule.

## 4. Immediate next work: inspect the successful canary

Before expanding paid calls, use the saved private outputs and source payloads. This should not require paying to regenerate successful results.

1. Verify all three output and payload hashes against receipts and journal entries.
2. Examine expected fields and each substantive claim against the exact FDA evidence supplied to the model, including dates, device names, identifiers, and source references.
3. Record correct, incorrect, unsupported, missing, ambiguous, or unverifiable fields with a reproducible rubric. Do not equate schema validity with truth.
4. Check for inappropriate clinical, legal, commercial, or causal inference. State what FDA evidence does and does not establish about a patent.
5. Reconcile provider-side details for the remaining calls when read-only records are available and needed; do not repeat model calls to obtain receipts.
6. Correct deterministic bugs and test with fixtures. Any new generation is a new recorded experiment with a reason, not an invisible replacement of an unfavorable output.
7. Summarize the canary as engineering/accounting evidence and exploratory content review. Keep the prior success receipt intact.

## 5. Execution, money, and compute

### 5.1 One working copy and one writer

Work on `main` in the specified local folder. Preserve existing dirty work. Identify the active writer by relevant task/process/lock evidence; a running Codex app-server alone is not proof of a conflicting writer. Do not stop unrelated processes.

Use the project's canonical locking and journal/reservation mechanisms. Do not create unnecessary worktrees or branch-cleanup work. Commit coherent, verified local changes; inspect the diff and scan for secrets and private data first. *(Amended 4 November 2026.)* Pushing to `origin/main` after a completed, verified package is authorized. Do not merge other branches, delete branches, change ACLs, or publish elsewhere without separate authorization.

### 5.2 Evidence location

Keep private outputs, raw account data, secrets, and rights-restricted material on the authorized local machine. Git should contain only the permitted code, manifests, sanitized receipts, aggregate results, and documentation. Confirm that sanitization preserves evidence meaning; do not strip so much provenance that results become irreproducible.

Use hashes and stable local references for private artifacts, and distinguish raw-file SHA-256 from normalized-content hashes. Do not edit an evidence timestamp to make an old snapshot fresh.

### 5.3 Budget and authorization

A budget cap is a limit, not by itself a new authorization to spend. Before additional paid work, verify that the owner's actual instructions cover this continuation, merchant/provider, models/routes, workload purpose, and total limit. If not, ask once for a bundled bounded experiment plan, then continue all independent offline work. Do not ask repeatedly for the same authorized scope.

*(Amended 4 November 2026.)* The owner raised the E2 allowance to USD 10 cumulative. Preserve all settled, reserved, pending and unknown amounts. Recalculate the residual from the actual ledger (USD 0.00054516 was spent in the canary). Do not treat the broader USD 100 project cap, the account balance, or an unlimited key as allowance beyond USD 10.

Estimate the complete planned study before running paid batches: cases, repeats, models, input/output ceilings, route prices, expected and worst-case cost, and remaining allowance. If the study does not fit, prioritize the questions, reduce unnecessary repeated work, use existing/local results where scientifically valid, or ask for a justified budget change. Never silently expand scope, model choice, provider fallback, or budget.

### 5.4 Paid admission without recurring false blockers

Use the existing canonical runner and ledger, not direct MCP generation that bypasses accounting.

- Prepare the runner, payloads, protocol, rights, token ceilings, output destination, and writer checks before fetching short-lived metadata.
- Refresh dispatch-key metadata through the dispatch key and credit/pricing through permitted sources immediately before admission, within the freshness interval actually enforced by the code.
- MCP OAuth key and dispatch key may differ. Do not require equal key hashes. Reconcile account/workspace identity and the dispatch key's own limit/expiry using the supported binding method.
- A verified unlimited marker with a null remaining limit is not missing metadata. A null without verified semantics is not sufficient evidence.
- A read-only credit snapshot can exist separately from the ledger. Do not make reservation a prerequisite for obtaining evidence required to reserve.
- Use exact authorized model/provider/precision and bounded price/token parameters. Disable fallback through supported settings when the design requires a fixed route; record the actual route.
- Before each new admission window, evaluate freshness and ledger state. Do not require a completed generation to fit inside a pre-dispatch freshness window unless the real system specifies that condition.
- On ambiguous billing or timeout, preserve UNKNOWN and request/generation identifiers as appropriate. Reconcile read-only before deciding anything else. Do not retry, free a reservation, reset a window, or hide an uncertain attempt automatically.
- Do not reinterpret a known settled call as unknown merely because a later snapshot is stale.

### 5.5 dr-train

Use the configured SSH profile and existing credentials without displaying, copying, changing, or creating secrets. The owner supplied `chaw@100.77.149.83` with an existing local identity file. Verify the intended host and host key through the authorized setup.

Use dr-train for computation only under the existing owner-approved resource scope. Check current jobs, GPU availability, memory, storage, and permitted runtime/concurrency before launching. An idle GPU alone does not prove ownership of the resource, but do not invent extra allocation paperwork if explicit authorization and the real scheduler/policy suffice.

Do not terminate others' jobs, alter system security settings, or overwrite shared data. Use bounded, resumable jobs with checkpoints. Keep canonical evidence on local storage; only transfer allowed inputs needed for computation and return results locally. Do not copy `.env` or private API/account data to the remote machine. If remote execution is unavailable, continue feasible local work and report the exact dependency rather than rerunning unsuccessful connection checks without a change.

## 6. Work packages and exit evidence

| Package | Work | Exit evidence |
|---|---|---|
| WP0: Reconcile | Inspect current repo, writers, protocol, budgets, receipts and old metrics; preserve current changes. | Current-state manifest; discrepancies resolved or clearly marked. |
| WP1: Canary quality | Evaluate saved canary outputs against exact evidence; fix deterministic defects. | Three-case content audit, rubric, tests, no overwritten prior results. |
| WP2: Research design | Select 1–2 contributions, RQs, analysis units, primary metrics, baselines and ablations. | Versioned protocol and claims-to-evidence map frozen before final testing. |
| WP3: Data and labels | Audit existing corpus/qrels, rights and leakage; select suitable established public labels and feasible source-grounded assessment. | Dataset/split/label manifests and defensible eligibility decisions. |
| WP4: Benchmark | Reproduce eligible baselines, tune on dev, run matched comparisons and ablations. | Complete machine-readable result tables, run manifests, failures, costs and uncertainty. |
| WP5: Robustness | Examine failure modes, affected subgroups/tasks, provenance errors, and sensitivity to design choices. | Error taxonomy and prespecified/sensitivity analyses with clear exploratory labels. |
| WP6: Reproducibility | Validate deterministic artifacts and rerun an appropriate subset from a clean environment where feasible. | Commands, dependencies, versions, hashes, reproducibility report and stated limits. |
| WP7: Manuscript | Write claims supported by results; related work, methods, results, discussion, limitations and declarations. | Manuscript and supplement with every major claim linked to evidence. |
| WP8: Readiness | Review official requirements, scientific claims, rights, ethics, author decisions and submission materials. | Honest readiness matrix plus a minimal owner decision packet. |

Run independent packages in parallel only where it does not create competing writers, contaminate held-out data, or invalidate fair timing comparisons. Do not launch large duplicate jobs before checking existing artifacts and active processes.

## 7. Required project documents and artifacts

Prefer updating the existing canonical location. Avoid multiplying copies of the same plan.

- `GOAL.md`: concise objective, supported scope, work packages, authority/budget boundaries, success and stop criteria.
- `PLAN.md` or current execution plan: dependencies, experiment matrix, compute/cost estimates, and next executable actions.
- Research protocol: RQs, hypotheses, analysis units, data selection, splits, labeling, baselines, tuning, metrics, uncertainty, missing/failure handling, and version/freeze information.
- Evidence-gap matrix: requirement/claim; evidence; source; status; limitation; next action; whether external input is needed.
- Claims-to-evidence matrix: manuscript claim; experiment/table/artifact; population; comparison; uncertainty; allowed wording; unsupported extensions.
- Dataset and qrels provenance manifests; rights register; split/leakage report; solo assessment rubric where useful; no external assessor requirement.
- Experiment registry: run ID; protocol version; full code SHA and dirty patch identity; data/config/model versions; seed if meaningful; hardware; start/end; outcomes; artifacts; costs; deviations.
- Results files: machine-readable tables and reproducible figures with actual denominators, failures, exclusions and uncertainty.
- Manuscript, supplementary material, reproducibility instructions, and submission-readiness checklist.
- `HANDOFF.md`, `CLAUDE.md`, progress and next-actions: consistent current state, the next runnable command or decision, and precise pointers. Do not use stale goal instructions as the active plan.

Use English for manuscript/research-facing documentation unless the current repo requires otherwise. A short Thai owner summary and Thai execution prompt may accompany it. Do not fabricate references or populate paper PDFs without checking their lawful access and identity.

### Evidence-gap matrix fields

`item_id | claim_or_requirement | status | evidence_path | evidence_version | limitation | next_action | dependency | owner_decision_needed`

Suggested statuses: `VERIFIED`, `PARTIAL`, `MISSING`, `NOT_APPLICABLE_WITH_REASON`, `CONTRADICTED`. Do not hide a missing central result under `NOT_APPLICABLE` merely to close the goal.

### Readiness dimensions

Track engineering readiness, data/rights readiness, scientific evaluation readiness, reproducibility readiness, manuscript readiness, and owner/submission readiness separately. A total percentage is optional and must not conceal a failed essential dimension.

## 8. Quality, tests, and provenance

Run focused tests after relevant fixes and the applicable full checks before calling the final code verified. Distinguish failed, skipped, not run, and passed. Record the exact code state for each result; do not attach an old passing count to a later HEAD.

Validate JSON/schema, links, hashes, manuscript tables and figures against source results, and the private/public boundary. Every aggregate should trace back to eligible run records. Verify that no result or citation is silently duplicated and that no test fixture is presented as real evaluation data.

Reproducibility checks should use existing caches appropriately, document cache state, and avoid changing the study to obtain a preferred result. If an independent environment or person has not reproduced the work, state that limitation instead of calling a same-author rerun independent validation.

## 9. Completion and pause rules

### A scientifically complete research package

The selected questions have defensible evidence, the protocol and deviations are documented, major claims match results, rights/provenance are adequate, reproducibility is demonstrated to the stated extent, and limitations are explicit. Negative or inconclusive results may satisfy this definition if the study is sound and conclusions are appropriately bounded.

### Submission-ready for owner review

In addition to the above, the current applicable journal requirements have been checked, required declarations/materials are prepared, and author/ethics/data decisions are clearly resolved or explicitly await the owner. This status is not editorial acceptance and does not authorize manuscript submission.

### Pause only the affected dependency

Pause a dependent action for unresolved data rights, missing necessary authorization, ambiguous accounting, missing necessary label evidence for a specific claim, unsafe concurrent writers, or an external decision. Continue useful independent work. Do not declare the whole project blocked while a concrete evidence-producing task remains ready.

If no such task remains, write one concise blocker packet: what is missing, why it changes the research or execution, what is already done, the exact minimal request, and how work will resume after the change. Do not repeatedly recheck the same unchanged state or create empty audit rounds.

### Final handoff

Report:

1. What was actually completed and on which code/data state.
2. Research questions answered, including negative or inconclusive findings.
3. Current verified metrics and uncertainty, with links to tables and artifacts.
4. Engineering checks and their scope.
5. API costs, outstanding reservations/unknowns, and verified remaining allowance.
6. GPU work/resources used and outstanding jobs.
7. Changed files, local commits, and whether anything was pushed.
8. Scientific and submission gaps, owner decisions, and the next exact action.
9. Whether to continue the same Goal/session, resume from the handoff, or stop because the defined scope is complete.

Do not submit the manuscript, contact outsiders, or start new spending scope as a side effect of marking the package complete. Pushing the verified package to `origin/main` is authorized (owner amendment, 4 November 2026).

## 10. Short Claude prompt (Thai)

```text
Continue Patent-to-Pilot ในโครงการเดิมบน C:\Users\User\Desktop\myProject\patent-to-pilot และ main เดิม อ่าน PTP_JOURNAL_LONG_RUN.md ทั้งไฟล์ พร้อม AGENTS.md, GOAL.md, HANDOFF.md และ audit E2 canary ล่าสุด ตรวจสภาพจริงแล้วผสานแผนนี้เข้าเอกสารหลักโดยรักษา dirty work, journal, งบ และหลักฐานเดิม ห้ามสร้าง worktree หรือ reset

ทำงานต่อเนื่องตาม work packages จนได้ research package สำหรับประเมินความพร้อมส่ง World Patent Information เริ่มตรวจความถูกต้องของ output 3 เคสที่มีอยู่ จากนั้น audit corpus/qrels และเลือก contribution 1–2 ข้อ กำหนด protocol, การประเมินแบบ solo โดยใช้ public benchmark/labels ที่มีที่มาและสิทธิ์ชัดเจน, baselines/ablations, metrics และ uncertainty ก่อน final test ทำงานที่พร้อมได้ทันที แก้โค้ด ทดสอบ รันการทดลองที่มีสิทธิ์และอนุญาตแล้ว และเขียน manuscript ตามผลจริง รวมผลลบด้วย

โครงการนี้ทำคนเดียวและไม่มีผู้เชี่ยวชาญมาประเมิน ห้ามตั้งการหา expert เป็น dependency ให้ใช้ public benchmark/labels ที่ตรง task และ source-grounded checks พร้อมจำกัด claim ตามหลักฐาน งานตรวจโดย owner ให้ระบุข้อจำกัดตามจริง

ใช้ cap E2 ที่ owner ปรับเป็น USD10 (สะสมรวม canary) และสิทธิ์การใช้เงิน/compute ที่อนุมัติจริง หากยังไม่มีการอนุมัติ additional paid study ให้เสนอแผนและ worst-case cost ครั้งเดียวแล้วทำงาน offline ต่อ ไม่วนตรวจ blocker เดิม ไม่แต่ง gold หรืออ้าง scientific/publication readiness จาก test หรือ canary เมื่อจบแต่ละช่วงอัปเดต evidence-gap/claims-evidence matrix และ docs พร้อมสรุปผลจริง สิ่งที่ยังขาด และคำถามที่จำเป็นต่อ owner เท่านั้น commit และ push ไป origin/main ได้เมื่อจบงานที่ตรวจแล้ว แต่ห้าม submit manuscript
```
