# Owner decisions, 22 Nov 2026 (answered in chat)

| # | Question | Owner's decision | What it means for the work |
|---|---|---|---|
| D1 | What should the IS2 core story emphasise? (the owner had already chosen the current research as the core) | **Research + demo** | Story arc: Paper 53 → B53 (bridge) → G03 DEV experiments, honestly including the parked results → B53.0 (our pipeline matches the DAPFAM paper) → Workbench demo of selective update after a source change. Thai and English papers and slides are rebuilt on this arc. |
| D2 | If G03 amendment 2 (learned selector) also does not beat F\* | **Keep working on acquisition** | Do not pivot the headline to maintenance yet. Design and pre-declare new acquisition mechanisms that bring in *new* candidates, e.g. LLM query rewriting or obligation decomposition through OpenRouter (D7), or additional candidate sources. Each is frozen before its numbers, on allowed DEV only. |
| D3 | Download the PatenTEB train split for the PatEmbed–DAPFAM overlap audit | **Approved** | Accept the Hugging Face terms through the owner's normal account flow if a login is needed, and record the revision. Run a family-level overlap audit (DAPFAM 1,247 queries + 45,336 families vs PatenTEB train). Store only aggregates in Git. |
| D4 | Delete the read-only `b53/inputs` on dr-train | **Approved, and done 22 Nov** | See `artifacts/maintenance/20261122-b53-pull/SUMMARY.md`. |
| D5 | English byline for the advisor | **"Tuchsanai Ploysuwan"** in the author line; the title "Assistant Professor" goes only in footnote 2 | For the Thai edition, retain the advisor-approved local spelling and footnote title from D5 at Git revision a3fe54ba. |
| D6 | Acknowledgments | **AI-use statement only** | Keep only the sentence declaring AI assistance (Claude) and the author's responsibility; no other thanks. |
| D7 | Paid model API | **Use the OpenRouter API, with several models chosen for relevance to the research (not just one)** | Use G02's `openai_compatible` adapter (endpoint `https://openrouter.ai/api/v1`, `allow_remote` true, key by environment-variable name, e.g. `OPENROUTER_API_KEY`). Pick 3–5 candidate models by research fit and check their live availability and price first (examples to verify: Qwen3 family, Claude Haiku/Sonnet 5.5, DeepSeek V4 Flash, which the Thai Gazette paper used for contextualisation). **The owner has not yet set a USD amount:** CLAUDE.md rule 2 needs a recorded cap (`spend_cap_usd`, `max_requests`) before the first paid request, so ask the owner for the number. Note: the `openrouter` MCP server in Claude Code needs `/mcp` authorisation by the owner. |
| D8 | Optional installs | **`pypdf` approved.** No local Ollama: GPU and local-model work goes to **dr-train (V100) and RunPod via MCP** | Install `pypdf` into `.venv` and enable the G02 PDF ingestion adapter, with tests. RunPod use still needs a per-job envelope (amount + scope) under CLAUDE.md rule 2; confirm the amount before creating any pod, and delete pods after use. |

**D7 follow-up (22 Nov):** the owner reconnected the OpenRouter MCP. Budget proposal:
[API-BUDGET-PROPOSAL-20261122.md](API-BUDGET-PROPOSAL-20261122.md).
- Envelope E1 = USD 8.00 / 35,000 requests, for G03 amendment 3 (LLM query expansion as new acquisition routes) and
  Workbench checks.
- Remaining account balance ≈ USD 8.37.
- **D9 (22 Nov 2026, owner in chat: "Approve E1 USD 8"): E1 APPROVED.**
  - Cap USD 8.00; max 35,000 requests.
  - Scope: G03 amendment 3 (LLM query expansion as new acquisition routes; pilot, then one full run) and Workbench
    profile checks (≤ USD 0.20).
  - Stop rules as in the proposal: no full run if the pilot shows no P1-DEV gain; stop and report at USD 6 spent.
  - The approval covers OpenRouter only. It does not cover E2 or RunPod.

**D10 (22 Nov 2026, owner requested inclusion in IS2): Paper 86 enters the IS2 story arc.** This amends D1. The arc becomes
Paper 53 → B53 (bridge) → **Paper 86 exposure ceiling** → G03 DEV (re-weighting the same routes does not help; v1/A1/A2
parked) → A3 (new candidates via LLM expansion) → B53.0 → Workbench demo.
- The owner asked whether to return to the Paper 86 line. The agent's assessment:
  - Paper 86's headline (+0.111) rests on PatEmbed, which is possibly contaminated on DAPFAM;
  - it is a diagnosis paper;
  - its historical records are incomplete.
  So it serves best as motivation for the acquisition work.
- Paper 86 stays **IS2-only** (rule 9) and is presented as the owner's own **unpublished** work (withdrawn from IEEE,
  19 Nov). arXiv:2605.24297, its ref [2], is not cited (rule 10).
- Revised outline: [docs/writing/is2/IS2-OUTLINE-v3-20261122.md](../writing/is2/IS2-OUTLINE-v3-20261122.md).

Still open:
- the Paper 53 DOI (`DOI pending` stays in the reference list);
- E2 (later);
- RunPod caps (D8).

## Decisions of 22 Nov 2026, evening (owner in chat, answering one consolidated question)

| # | Decision | Effect |
|---|---|---|
| D11 | **Approve E1R: USD 50 cumulative** (it includes E1 spend), notify at USD 40, hard limit USD 50, 100,000 attempted requests, no GPU rental | Recorded in the shared budget ledger (`approve --envelope E1R`), which now dispatches under E1R. Providers: OpenRouter and Typhoon. Scope: A3r1 plus bounded structural expansion and Thai checks under owner-note-22112026 |
| D12 | **Typhoon:** the owner has an OpenTyphoon API key and reports the API as free | Typhoon2.5 stays in the A3r1 panel (4 models, 3 lineages). The owner sets `TYPHOON_API_KEY` as a user environment variable; the key never goes into chat. Zero price and free-tier status are to be confirmed from the API's usage fields during calibration. A rate limit of 200 requests/min applies |
| D12a | **Other Thai LLMs suggested by the owner:** iApp (iapp.co.th API) and `nectec/pathumma-thaillm-8b-think-3.0.0` | Recorded as **P3 (Thai) candidates**, not added to the A3r1 panel, which is English patents. iApp needs its own key and price check under E1R. Pathumma 8B is a weight download (per-item approval at the time) and needs dr-train hosting; fp16 does not fit the free V100 memory next to the other user's service |
| D13 | **OpenRouter:** set `OPENROUTER_API_KEY` and top up credits (about USD 15 recommended) | The owner's action. A3r1 calibration and the pilot start when the key is present |
| D14 | **PatenTEB:** accept the partial audit | PatEmbed is reported separately with the shared-pool caveat. BM25, Qwen3 and Arctic are the main DAPFAM comparators. No further PatenTEB download |

## Decision of 23 Nov 2026 (owner in chat, with the plan `PTP_Thai_Search_Structure_Requirements_Fix_Plan_20261123.md`)

| # | Decision | Effect |
|---|---|---|
| D15 | **Use PyThaiNLP** for Thai search (the owner proposed it) | `pythainlp 5.4.0` (Apache-2.0) installed into `.venv`, declared as the optional extra `thai`. The plan's three Workbench repairs are being implemented: Thai search, Remove/Undo, then structural acquisition before assessment. The Hugging Face collection "datasets for pretrained Thai LLM" is **not downloaded**: it is pretraining data, not needed for search, and would need a per-item approval |
| D16 | **A3r1 Stage B runs automatically on a pilot GO** (frozen rule), within E1R | No further question after the pilot. On STOP, nothing more is spent. If OpenRouter credit runs short, the ledger pauses and the owner tops up |
| D17 | **Merge and push worktree work automatically** when the full suite passes (only the 8 known SACR failures) and smoke is 15/15 | Applies to the Thai-search and Remove/Undo branches and similar verified product work |
| D18 | **Thai downloads approved:** Thai Gazette evidence retrieval (CC BY 4.0), NitiBench + nitibench-statute (MIT), WangchanX-Legal-ThaiCCL-RAG train split (MIT) | Copies are kept **locally** (`../_private_artifacts/thai-data/`) **and on dr-train** for GPU work. Never committed, never product-bundled. Pin revisions per the P3-T01 contract. Test splits stay held out; NitiBench+ (gated) is not covered |
| D19 | **P2-T02 follow-up GPU runs approved:** if Arctic shows a coverage effect, build the same complete-content index for PatEmbed and Qwen3 on the V100 | A declared amendment is written before running. One job at a time under the GPU lock, at no cost |


## Decision of 23 Nov 2026, afternoon (owner in chat: "Approve USD 20")

| # | Decision | Effect |
|---|---|---|
| D20 | **RunPod envelope R1: USD 20 cap for P2-T02** (coverage control, frozen protocol bd30d3f7, memory-safe build 92465abd), started once the inputs that exist only on dr-train can be copied | Prepaid balance at approval USD 37.21. Scope: one P2-T02 run (content build, BM25-full, Arctic C1/C2 encode and retrieval) on one community GPU pod (RTX 6000 Ada or RTX 4090); estimate USD 4–10. Stop and report at USD 15. **No network volume** (owner declined a volume at that time): data goes onto the pod's own disk only, is uploaded after the pod is created, and is removed when the pod is deleted after the results are pulled. Nothing is pre-staged. Never copy TEST splits, sealed qrels or per-query TEST outputs to RunPod. Spend is recorded in the P2-T02 receipt |

**Dry-run correction (same day).** The earlier dry run said the PatentsView sources had to be downloaded again. That was
wrong: the owner pointed out `data/raw/uspto/` (git-ignored, 69 files, 17 GB, downloaded 16–18 Nov). It holds every
claims file the corpus needs (grant units 1976–2012 inside `g_claims_1976–2013`; pre-grant units 2001–2012 inside
`pg_claims_2001–2016`) and the four text sources of `build_bridgeret_texts.py`. No new download is needed. Only the C0
baseline runs (`runs/z-arctic` passages and P1-DEV run, `runs/bm25` P1-DEV run), `ser-arctic-v1`,
`texts-v1/corpus.jsonl` and `splits/private/tasks.tsv` still exist only on dr-train.

## Decision of 23 Nov 2026, evening (owner approved a volume for data reused until the research concludes)

| # | Decision | Effect |
|---|---|---|
| D21 | **A RunPod network volume is allowed for data that will be reused until the research closes.** This amends D20's "no network volume" | Only reusable inputs and derived indexes go on it: PatentsView sources, rebuilt C0, C1/C2 content and vectors. One-off scratch files do not. No TEST data, sealed files or credentials. Storage is billed monthly (about USD 0.07 per GB-month) and is recorded in the P2-T02 receipt and HANDOFF. The volume is deleted when the research closes or the owner asks. The running pod `jd41r4cvv171q6` sits in US-KS-2, which offers no network storage, so at the end of the run the reusable outputs move to a volume in a US data centre that does (through a cheap CPU pod), and then the GPU pod is deleted |

## Decisions of 23 Nov 2026, night (owner in chat: long autonomous run, parallel pods approved; one consolidated question)

| # | Decision | Effect |
|---|---|---|
| D22 | **RunPod envelope R2: USD 60** for parallel pods, on top of R1 (USD 20, P2-T02). Notify at USD 45 | Scope: (a) the A3r1 pilot evaluation on RunPod; (b) the D19 complete-content follow-ups (PatEmbed, Qwen3) if P2-T02 shows a coverage effect; (c) Thai GPU work for P3-T03; (d) the D21 network volume. Several pods may run at once. Each pod's hourly price is stated before creation, and each pod is deleted after use. Spend is recorded per pod in its receipt |
| D23 | **The A3r1 pilot evaluation runs on RunPod now**, not on dr-train | Its dr-train-only inputs (Qwen3 / PatEmbed / BM25 C0 runs, PatEmbed vectors, serialised texts, G03 v0 evaluations) are rebuilt on pods under a declared amendment, with a rebuild gate against the archived records **before** the frozen GO/STOP rule is applied. The PatEmbed and Qwen3 weights are the previously approved items at their recorded revisions. Stage B still runs automatically on GO (D16), within E1R |

## Decisions of 24 Nov 2026, early morning (owner in chat, one consolidated question)

| # | Decision | Effect |
|---|---|---|
| D24 | **R2 scope extended to the A3r1 full evaluation** after Stage B (complete P1-DEV arms, F3\* selection, VAL principal under the frozen continue/revise/park rule) | One pod under [A3R1-FULL-EVAL-RUNPOD.md](../healthtech/research/g03-dev/A3R1-FULL-EVAL-RUNPOD.md), launched when the Stage B ledgers are complete. Estimate USD 4–5.5 on an RTX PRO 4500, or USD 9–12 on an A100 |
| D25 | **P4-T04 defect D2: fix it as structural-acquisition policy v2.1.** All seed searches run first, and anchors come from current seed hits, so results no longer depend on run order or store history | A new policy version (`ptp-structural-acquisition/2.1.0`), with tests proving order independence. The P4-T04 harness is re-run to confirm the d1 scenario now matches |

## Decision of 24 Nov 2026, evening

| # | Decision | Effect |
|---|---|---|
| D26 | **Approve D19 RunPod launch, parallel work and sub-agents, a long-run goal, and a USD 20 D19 cap. The agent may select the machines.** | The D19 cap replaces the USD 15 sub-cap within R2; R2 remains USD 60 with notification at USD 45. Verify US stock and fit the combined compute, disk and retry exposure within D19's USD 20 before dispatch. State each pod's hourly price before creation, pull and hash outputs and terminate after use. |

## D27 · Evidence-scope program (25 November 2026)

The owner approved the direction developed from the IS1 and Paper 53 review, the Thai market survey and the evidence-scope gap analysis. Organize the project now, write the master and phase plans, design the README and assets, and hand back a new execution-goal prompt. New product and research work may run in parallel after activation. S0 is the only active deliverable in this handoff.

Freeze the research questions and dataset design now. The owner approves installing needed dependencies and acquiring additional in-scope datasets. Record file-level sources, versions, licenses, access basis and hashes when materialized. This approval supersedes the former per-item owner confirmation for these in-scope installs/downloads. It grants no new paid service envelope, gated third-party terms or redistribution rights. Never open protected TEST, sealed judgments or credentials. Pod price, prior creation approval and cleanup requirements continue.

Progress with the documented feasibility gates. Any positive paired primary DEV estimate permits one bounded follow-up. A supported scientific gain needs matched and uncertainty-qualified evidence. A local engineering alpha can proceed independently of that result. Preserve negative findings, historical gates and exact old task identities. See the [new plan](../evidence-scope/MASTER-PLAN.md) and [freeze](../evidence-scope/FREEZE.md).

## D28 · Execute S1 and S2 in this goal

The owner added both phases to the current goal. Deliver the frozen research fixtures and local Workbench alpha together. D27 permissions and existing cost envelopes still apply. Hand back the phase receipts before taking up S3 or S4.

During D28 the owner requested multiple real pharmaceutical patent and Thai law examples across subfields, followed by an S3 executor prompt. This session will serve as planner and auditor on the subsequent dispatch. The public examples are reserved for display and excluded from S1/S3.

## D29 · Three-specialist RA Pharma program and parallel dispatch (26 November 2026)

The owner selected one dossier with patent/FTO, Thai and foreign regulatory, and Thai official-correspondence specialists. Research continues IS1 under GPT 6.2 high. Product uses Claude Sonnet 5.5 medium. The owner opens each session on its own branch. The Planner may organize files, remove verified unused material, maintain HANDOFF, commit and publish the plan and branch starting points. Necessary project-local skills, harnesses, tools and MCP integrations may be downloaded. Record their provenance and rights. Existing data, spending and pod rules retain their original scope.

The owner requires English-only project documentation, a professional README and logo informed by references, a repository writing skill, and mandatory documentation and memory updates after each task for all agents. Preserve historical owner quotations, original-language evidence, frozen inputs and Thai product output in their evidentiary roles. The [dispatch board](../ra-pharma/MASTER-PLAN.md) governs new work.

## D30 · Park the eight IS1 cells and continue the architecture study (26 November 2026)

The owner confirmed the historical patent family exclusion list is unavailable. Keep the four instructions at two depths as NOT_RUN. The Planner and Research Executor continue the [architecture study](../ra-pharma/READING-ARCHITECTURE-REVIEW.md) using scoped, traceable evidence. Preserve the published EPO source preflight for a future cohort with demonstrable eligibility.

## D31 · Evaluate attribution of historical Thai public inquiries (26 November 2026)

The owner selected public Thai legal inquiries as the next primary research task. Across multiple matters, trace the incoming letter to the official response and identify where that response answers the issue. Use the authentic documents and a separate reference key. Opinion 344/2532 is an exposed development example. The applicant-dossier completeness endpoint remains unmeasured. The [architecture review](../ra-pharma/READING-ARCHITECTURE-REVIEW.md) records the preceding comparisons and the reason for choosing this endpoint.

## D32 · Require a paper and a comparator for Planner work (26 November 2026)

For every Planner assignment, proposal or substantive claim, cite a relevant primary research paper and identify a benchmark or named competitor. Link both sources and explain which task, metric or product workflow they support. Distinguish a measured head-to-head result from an external reference or an untested hypothesis. For a comparison across jurisdictions or languages, specify the difference in scope. An owner decision, source hash or receipt remains the authority for its own facts.

## D33 · Research first and bounded architecture search

The owner selected GPT 6.2 Sol with medium effort for the next Research Executor. Planner/Reviewer owns MCP evidence discovery and owner consultation. Compare zero-shot and few-shot generation, general RAG, ChatGPT Pro and NotebookLM. Defer further Product work until the architecture has research support. The [research-first plan](../ra-pharma/RESEARCH-FIRST.md) proposes a bounded autoresearch loop. Dataset, endpoint, numerical thresholds and release remain prospective.

## D34 · Start the unchanged-source pilot

The owner selected Option A, authorized the Planner/Research Executor loop and offered an authenticated Chrome browser for Planner operation. Separate system time from human work. New Product development remains deferred. The [input checkpoint](../ra-pharma/OPTION-A-IMPORT.md) records the exact practice packet and open product access checks.

## D35 · Plan B v2 Section 9 items 1–5 (27 November 2026)

1. Approve B1 v2 with descriptive claim and document metadata, the existing deterministic prefix of up to 24 groups and zero new service charges.
2. Approve machine counting of public redaction markers. Preserve missing text as NA, log full-text processing and prohibit reconstruction.
3. Approve B1-ext existence and identity metadata only, one query per optional class per matter for other regulator assessments, prosecution and public litigation.
4. Accept an engineering-only route initially if independent reviewers are unavailable. B2–B4 still require separate release.
5. Disqualify any future Arm C that exceeds the fixed checklist on unsupported issued assertions at matter or element level (G1), or on false definite states on independently judged unknown matters (G2). Solo checks are provisional.

The owner designated GPT 6.2 Sol medium for Research and Opus 5.5 medium for Product. Product implementation is held. [Review and release](../ra-pharma/ip-pharma/B1-PLANNER.md)

## D36 · Generic pharmaceuticals, biologic discovery and biologics markets (27 November 2026)

The owner prioritizes exploration of generic pharmaceuticals and follow-on biologics for drug discovery, alongside biologics market research. The Planner interprets follow-on biologics as biosimilars when the jurisdiction identifies a reference relationship. Novel target or indication hypotheses have a separate evidence question. This direction applies to portfolio discovery. D35 still governs the current oral small-molecule intake, exclusions and budget. [Research questions and public comparators](../ra-pharma/MASTER-PLAN.md#discovery-and-market-research)

## D37 · Authorize B1E v1.0 descriptive source feasibility (27 November 2026)

The project owner explicitly approved the Planner's immediately preceding B1E v1.0 decision request. The [approved text](https://github.com/siriponsri/patent-to-pilot/blob/b0e7ba42480d5c64e3af8c54ac5e34cbffcccb87/docs/ra-pharma/ip-pharma/B1E-AMENDMENT.md) has Git-content SHA-256 75fe128312b96321a8d5ed522a1054e88269c7c835b34a43e2a458ebcec0d96b. That exact text is the frozen protocol. The execution lock is a separate artifact.

Authorize at most 24 active-moiety-set and NDA groups in deterministic order, bounded known exclusions, UNKNOWN historical overlap, all failures retained, local CPU and USD 0 in new service charges. Include the three optional existence checks. Planner must verify selector, inputs and exclusions before selection and reproduce the prefix before Research checks any source. All selected groups are exposed development material. Original B1 stays BLOCKED_FRAME; B2–B4 remain NOT_RUN. D36 opportunity discovery has its own scope.

## D38 · Two synthetic rituximab evidence-readiness inventories (27 November 2026)

The owner approved the D36 proposed desk check, conditional on Planner reviewing Research and Product impact first. Planner completed the [impact review and bounded release](../ra-pharma/ip-pharma/D38-IMPACT-REVIEW.md) before dispatch. Compare the manual guidance checklist and a one-row evidence record using identical inputs. Product implementation, operator recruitment, private data and broader B2–B4 research remain outside this decision.

## D39 - Public opportunity discovery, option A (27 November 2026)

The owner approved up to twelve sequential public desk-research batches, Thailand first with US comparators and USD 0 incremental service spend. Planner reviews each batch and reports at 4, 8 and close. The first release covers the prospective discovery lock only. See the [approved scope](../ra-pharma/ip-pharma/D39-DECISION-REQUEST.md).

Owner authorized impact-driven redirection within D39. The [Planner field evidence review](../ra-pharma/ip-pharma/D39-FIELD-EVIDENCE.md) prioritizes the Thai pre-submission decision and documents the separate patent-to-counsel workflow. Batch releases remain prospective.

Owner requires demonstrable differentiation from both ChatGPT and NotebookLM and an independently scorable local AI workflow. See the D39 protocol amendment on main. All three platform checks remain NOT_RUN.

D39 closed after Batch 4 under the approved early stop. Empty deep-review queue at e495570d. Batches 5-12 and platform comparisons NOT_RUN.

## D40 · LOE-Bench becomes the active program (27 November 2026)

The owner replaced the RA Pharma mandate with [LOE-Bench](../loe-bench/PLAN.md). LOE-Bench forecasts generic and biosimilar entry from open regulatory data, using abstention-aware, evidence-traced prediction. RA Pharma is not discarded. The program must include a Thai-context demo, and the owner considers D40 to cover RA Pharma's scope. All data must be open, because the owner holds no proprietary data.

- The owner delegated the evidence design (test exposure and the Track A clock) to the Orchestrator, choosing for maximum impact and minimum reviewer objection. See [PLAN.md](../loe-bench/PLAN.md#evidence-design-orchestrator-recommendation-owner-delegated).
- The Orchestrator alone may copy and manage files in `docs/owner/`. Other agents still never edit that folder.
- The owner approved T10, the LLM arm, on dr-train under the standing V100 rules. Purple Book access is to be verified with open sources only.
- Roles: Claude Opus 5.5 is Orchestrator, GPT-6.2 Sol medium is co-planner and co-reviewer, and Claude Sonnet 5.5 executes at low token cost.
- The owner-only items from the package are deferred to a document pack after the research closes: expert review of exclusivity assumptions, journal quartile and APC checks, the OSF account, customer discovery and the Paper 53 venue.
- 27 Nov 2026: The owner approved the C′ primary-test design in [PLAN.md](../loe-bench/PLAN.md#cp2-co-planner-review-and-main-planner-decision-27-november-2026): C′ at 24 months on the test cutoffs from 2017 onward, with a sealed test and a candid disclosure of the earlier aggregate baseline exposure. The strict post-2023 cohort is a descriptive sensitivity subset, and Track A is the fully clean confirmation.
- 27 Nov 2026: The owner approved [confirmatory criteria v2](../loe-bench/PLAN.md#confirmatory-criteria-v2-main-planner-proposal-owner-approved-27-november-2026), a fixed-sequence test of H1 (M3 − B1 at 24 months), then H2 (M3 − M1 at 24 months), then H3 (M3 − B1 at 12 months), each one-sided at α = 0.025. M1 − B1, E-AURC and calibration are secondary. The owner also asked the GPT-6.2 Astra co-planner to search for alternative patent-challenge evidence sources (E6-alt).
- 27 Nov 2026, role update: this supersedes the initial D40 role split above. Claude Opus is the main planner and the only reviewer, GPT-6.2 Astra high is co-planner, and GPT models are executors (owner-approved model mapping in [PLAN.md](../loe-bench/PLAN.md#roles)).
- 27 Nov 2026: The owner approved [confirmatory criteria v3](../loe-bench/PLAN.md#confirmatory-criteria-v3-owner-approved-27-november-2026-supersedes-v2-endpoints).
  - Primary endpoint: entry recall at a 20% review budget, ranked by native scores, using the fixed sequence H1 → H2 → H3.
  - Useful effect: +10 percentage points.
  - α: chosen by the pre-declared T4 rule, 0.025 or 0.020.
  - Secondary endpoints: AP, decision loss and the v2 metrics.

  The owner asked that reasons and references be recorded, and stated that no external domain expert is available. Regulatory assumptions will instead be verified against primary sources (REG) and disclosed as a limitation.
- 27 Nov 2026, GPU envelope: the owner approved the T10 LLM arm on RunPod with a **cap of USD 20** total, covering pods and storage, and allowing for an RTX 4090 not being available.
  - First stage: an executor creates and deletes a test pod to validate the setup and estimate upload time.
  - Inputs may be pre-staged. The plan is a network volume, so no pod sits idle.
  - Every pod's rate, start, stop and cost is logged, and pods are deleted after each stage.
  - The LLM arm is secondary and non-confirmatory. Its configuration must be frozen before the test unlock.
- 28 Nov 2026, **D41: Market Window Dossier.**
  - The owner approved a full-option plan and renamed the product Market Window Dossier (working name). It is a pharma market-research workflow from a pre-development launch-window forecast to an FTO hand-off report. LOE-Bench remains its benchmark.
  - Where data cannot support an as-of test, the component is evaluated retrospectively and labelled as such.
  - Authors are the owner and Asst. Prof. Dr. Tuchsanai Ploysuwan.
  - IS2 draft is due end of December 2026, and the final version end of January 2027.
  - The owner will submit OSF through a GPT-6.2 Sol high browser agent, using a copy sheet that the main planner audits.
  - The owner authorized deleting documents and data no longer used by this work. This is done from a reviewed inventory with `git rm`.
  - [Plan](../loe-bench/PLAN.md#d41-market-window-dossier-owner-approved-28-november-2026)
- 28 Nov 2026, OSF settings: the registration is public immediately, with no embargo. The owner's account is the only OSF contributor. The advisor is named as co-author in the registration text and in the IS2 paper.
- 28 Nov 2026: the authors confirmed the four disclosure statements in preregistration v2 and approved the audited package for OSF submission. [Copy sheet](../loe-bench/OSF-COPY-SHEET.md)
- 28 Nov 2026, writing workflow: Antigravity Gemini 4 Hydrogen (xhigh) drafts writing deliverables such as registrations, IS short papers and reports. GPT-6.2 Astra high critiques them, and Claude audits and finalizes. The owner had asked for Gemini 4 Carbon, but this machine's Antigravity does not advertise it. The advertised models are gemini-4-hydrogen, gemini-3.8-flash, claude-sonnet-4-6, claude-opus-4-6-thinking and gpt-oss-120b-medium. A Hydrogen smoke test passed.
- 28 Nov 2026: Antigravity hit its individual quota, which resets about 5 December 2026. Until the reset the owner approved GPT-6.2 Sol high as drafter for writing deliverables; the Astra critique and Claude audit are unchanged. The first IS2D attempt on Gemini failed with no output.
- 28 Nov 2026: Claude, the main planner, designs and creates all figures and slide presentations. Executors and drafters supply data and text only.
- 28 Nov 2026: OSF registration p2smd (doi:10.17605/OSF.IO/P2SMD) was submitted by the owner's browser agent and is public. The main planner wrote PREREG_LOCK from the canonical registration record, because no attachments or OSF PDF exist. The deviations are recorded in the lane memory.
- 28 Nov 2026: as first author, the owner authorized opening the sealed test under the registered sequence. The sequence is the custodian's blinded projection, then the C′ gate (PASS or FAIL only), then scoring of H1→H2→H3 and the registered exploratory analyses if the gate passes. It is conditional on the co-planner's audit of the registered text against the audited preregistration finding no blocker.
- 28 Nov 2026: the owner approved the accelerated plan, with a working product and the IS2 package by 15 December 2026, adjusting as needed. This includes moving C9 training to December via OSF update 1 and an early Track A freeze around 6 December.
- 28 Nov 2026: Claude designs and builds applications and the product, including the UI, the demo app and the report design. PRD planning may use Claude or ChatGPT. The GPT executor PRD2 (demo app) was cancelled and redispatched to Claude. PRD1 continues on GPT for the data pipeline, builder and audit; Claude redesigns its report renderer afterwards.
- 28 Nov 2026: the owner approved RunPod GPU use of about USD 1–3 to score L1 and L1e on the sealed C′ rows after a PASS gate, within the existing USD 20 LLM-arm envelope (about USD 0.97 used). Each pod's rate is quoted and logged, and pods are deleted after use.
- 28 Nov 2026, product design: the owner rejected the first demo UI and the novel directions A, B and C, and asked for a formal web style with plain wording, English headings and switchable TH/EN content. The owner chose F2, Regulatory agency (DESIGN.md). Build: web app, landing page and a Tauri desktop GUI, all by Claude.
- 28 Nov 2026, about 13:35 Bangkok time: the owner raised the RunPod GPU envelope by USD 3, from USD 20 to USD 23 total. This covers the SCORELLM pod left running while the owner's PC is off and a possible rerun. The owner wants work done as early as possible regardless of the planned dates. C9 training before 1 December needs OSF update 3 (`OSF-UPDATE-3-SHEET.md`), to be filed when the owner returns at 16:00. The owner shut the PC down while SCORELLM was running.
- 28 Nov 2026: OSF update 3 (C9 training no longer limited to December or January) was filed by the owner, approved at 09:09 UTC and verified by the main planner. C9 training is dispatched.
- 28 Nov 2026, evening: C9TRAIN found no US Secure Cloud L4, so no pod was created. The owner approved one Secure Cloud NVIDIA L4 (24 GB) in an EU data center, EU-RO-1 or EUR-IS-2, at up to USD 0.69/hour. The allowances are unchanged: USD 4.50 all-in for the card, 2.5 GPU-hours and USD 3.50 per arm, and USD 23 for the envelope. The GPU type matches the C9RUN2 hardware deviation, so only the data-center region changes and no new hardware deviation is needed. The owner declined the US RTX 4090 at USD 0.89/hour and declined to wait for US stock.
- 28 Nov 2026, evening: the owner asked for a like-for-like comparison with prior work and approved two routes together. (1) Reproduce prior methods (for example, the machine-learning approach of Hu et al. 2019 and the random survival forest of Hopefl et al. 2025) as exploratory Track A arms. They use the same open as-of features, rows and metric as M3, are preregistered in OSF update 4 and are frozen with the core predictions before 2027-01-31. (2) Report our arms in the metrics that prior studies use, such as AUC or C-index, as labelled external references and not head-to-head results. A post-hoc rerun of new arms on the opened C′ set was not approved. The co-planner first extracts each study's methods, features and reported metrics, and the main planner then locks the arm list before the freeze.
- 28 Nov 2026, late evening: the owner asked for (a) IS2 slides in Thai, told as a story through animation in the style of the IS1 HyperFrames deck, for 15 minutes of presentation and 10 minutes of questions, and (b) a comprehensive formal Thai report in PDF covering the whole journey from DAPFAM instruction rewriting and retriever fine-tuning to Market Window Dossier. The owner reads the report and the short paper before slide work starts. The report follows the writing workflow: Sol high drafts (Gemini out of quota), Astra critiques, and Claude audits and designs the PDF. The GPU pod for the Track A predictions has not yet been approved.
- 28 Nov 2026, late evening: the owner approved one RunPod Secure Cloud NVIDIA L4 (US or EU data center, whichever has stock first) at up to USD 0.69/hour, with an all-in cap of USD 1.50. It produces the Track A t0 predictions for L1 and L1e (Qwen2.5-7B, 651 rows per horizon) and for C9 SFT and GRPO (Qwen2.5-1.5B adapters, 651 rows at 24 months). The card produces predictions only; the freeze, tag and OSF timestamp belong to the freeze card. The pod is deleted after use. The envelope is USD 23, with about USD 3.73 used.
- 28 Nov 2026, night: the owner approved the [endgame plan](../loe-bench/ENDGAME-PLAN.md): product v1.0 by about 15 Dec, one journal manuscript beyond IS2 by 15 Jan, and a Track A prediction set that others can score. No owner work remains after 31 Jan 2027.
  - **D-L.** Apache-2.0 for the whole repository, including `product/` and `loe-bench/`. Data with redistribution limits, such as NBER, ships as download recipes.
  - **D-W.** The web app goes on a public static host (Vercel or GitHub Pages), with the disclaimer on every page.
  - **D-F.** If no L4 is available by 10 Dec 2026, use another GPU type for all remaining GPU arms (L1, L1e, C9), with a dated hardware deviation. C9 would then predict on a different GPU than it trained on, and the deviation must say so. Each pod's rate is still quoted before creation, within the USD 1.50 all-in cap unless the owner raises it.
  - **D-J.** The journal choice (CPT or Pharmaceutical Sciences Asia) is due by 8 Jan.
- 28 Nov 2026, late night: the owner asked that the writing skills no-ai-slop and zero-slop (both MIT, installed project-locally) be used on the IS2 text in both languages. After seeing the IS2STORY revision, the owner asked for an audit and a new revision:
  - more formal, professional language
  - professional Thai and English titles; the question-form title is withdrawn pending research on research-writing and title guidelines
  - figures in academic style rather than slide style, after research on academic-figure guidelines
  The co-planner is consulted anew. The revision may wait until all experimental results are in (the Track A freeze).
- 28 Nov 2026, late night: the owner chose the formal IS2 title, option 1 in the [style guide](../writing/is2/mwd/STYLE-GUIDE.md): TH การประเมินหลักฐานด้านการกำกับดูแลยาเพื่อจัดลำดับการทบทวนรายการยาก่อนการอนุมัติยาสามัญครั้งแรกในสหรัฐอเมริกา / EN Evaluating Regulatory Evidence for Prioritizing Drug Reviews Ahead of First US Generic Approvals.
- 28 Nov 2026, night: owner instructions.
  - Figures use direction A (Nature clean).
  - OSF update 4 was filed; the planner verified it as approved at 11:30:06 UTC.
  - Journal manuscripts are wanted for Pharmaceutical Sciences Asia and Science & Technology Asia (Thai journals, both of which publish in English) and for Medical Decision Making and JAMIA (international). The co-planner is always consulted on journal writing. The owner will help find author guidelines if they are missing.
  - IS2, slides and journal documents are delivered to `C:/Users/User/Desktop/myDegree/IS/IS_2_new` in a categorized structure. Misplaced originals on the Desktop may be deleted.
  - For KMITL graduation, IS2 alone suffices, but the owner wants a "wow" result that extends to a real product, so the product line opens now.
  - Slides wait until the owner reads the new short paper; only the folder structure is created.
- 28 Nov 2026, night (D42): the owner made Claude Sonnet 5.5 (medium effort) the Product Owner for Market Window Dossier. The main planner (Claude Opus 5.5) and the co-planner (GPT-6.2 Astra high) draft the product plan and PRD for the Product Owner ([PRD](../product/prd/PRD-MWD-v1.md)). The main planner remains the only reviewer; GPT executors still build data pipelines behind the product.
  - Requirement answers for v1.0: serve both audiences with the IS2 demo first; search within the 651-drug current queue with a planned-launch-date window (no new forecasts); the Thai layer shows unknown plus the next question; public hosting on GitHub Pages.
  - The owner asked to be consulted on requirements whenever the planner is unsure.
- 28 Nov 2026, night (D43): the owner asked that Market Window Dossier become a real AI-assisted product, using API providers first for presentation and later a local model on a server, through an interface compatible with Typhoon, OpenRouter, GPT, Claude, Gemini, Qwen and DeepSeek. Codex executors build the backend. Requirement answers:
  - AI tasks: all four (Thai dossier summary, hand-off letter draft, questions about the open drug, patent-claim reading aid).
  - Platform: both a web app and a desktop GUI app, ready for a later mobile app, and a trial for people in the organization. The planner proposes the platform in [PRD section 4b](../product/prd/PRD-MWD-v1.md#4b-ai-assistance-and-platform-d43-proposal-for-owner-approval).
  - API envelope: USD 10 all-in until 15 Dec 2026.
  - Journals: four venue-tailored drafts (PSA, STA, MDM, JAMIA) for the advisor; submit one at a time, the others as ordered fallbacks.
  - The orchestrator alternates between two Claude accounts; the HANDOFF resume point and lane MEMORY are updated, committed and pushed after every step.
- 28 Nov 2026, night (D43 platform answers): run the AI package on the owner's machine first for a team demonstration, and prepare the same package for an external server such as dr-train; sign-in by email and one-time code; 3–5 invited colleagues; Typhoon's free tier is allowed with public dossier data only. The owner asked whether ChatGPT Plus or Claude Pro subscriptions could replace API keys; the planner's answer is recorded in [PRD section 4b](../product/prd/PRD-MWD-v1.md#4b-ai-assistance-and-platform-d43-proposal-for-owner-approval) (not for a shared product; an MCP connector is the v1.1 candidate).
- 28 Nov 2026, night (journals): after the co-planner's [strategy](../writing/journal/JOURNAL-STRATEGY-4V.md) found that MDM prohibits "Generation of data or submission using a series of prompts" and that PSA limits generative AI to readability and language (both verified by the planner in the saved guideline files), the owner chose to submit only to journals that allow AI drafting. PSA and MDM are dropped. The owner approved the co-planner's order, which leaves **STA, then JAMIA**. JAMIA (OUP) allows AI use with disclosure. STA's AI policy was not found, so STA stays conditional until its policy or an editor's answer confirms AI drafting with disclosure is acceptable.
- 28 Nov 2026, night (deployment): the owner deploys through their own Cloudflare account. The public web app moves from GitHub Pages to Cloudflare Pages on a free `*.pages.dev` address. There is no domain for now, so the AI demonstration runs only on the owner's machine (localhost), with one allowlisted account: the owner's own email, stored outside Git. Remote sign-in for colleagues (Cloudflare Access one-time PIN behind a Cloudflare Tunnel) waits for a domain on Cloudflare.
- 28 Nov 2026, night (MCP and agents): the owner asked to add an MCP connector now and to support AI agents such as computer-use agents, Grok and "OpenBot" (to be identified). The planner added [PRD section 4c](../product/prd/PRD-MWD-v1.md#4c-mcp-connector-and-ai-agent-access-owner-request-28-november-2026): a read-only MCP server over public data (local stdio plus a remote server on Cloudflare Workers `*.workers.dev`), an agent-ready web UI for computer-use agents, an optional draft-checking tool and an OpenAPI description. Codex card B5 builds it.
- 28 Nov 2026, night (journal author facts, owner-confirmed): IS2 has not been published or publicly disseminated anywhere. Asst. Prof. Dr. Tuchsanai Ploysuwan's role is advisor (CRediT: Supervision); Siripon Srihangpiboon holds the other roles. No funding. No conflicts of interest. No KMITL ethics review was sought; the study uses only public regulatory records and involves no human participants. Planner notes for the declarations: an author with Supervision only should also review and approve the final manuscript (CRediT: Writing – review and editing) to meet common authorship criteria, which the advisor confirms; and the ethics statement must say that review was not sought because no human participants or private data were involved.
- 28 Nov 2026, night (journal drafts and public repository): the repository is public, so the IS2 drafts (TH and EN) and JAMIA draft v1 are already readable on GitHub; history is not rewritten. From JAMIA v2 onward, journal manuscript text is kept outside Git in `C:/Users/User/Desktop/myDegree/IS/IS_2_new/04_journals/<journal>/manuscript/`; the repository keeps receipts, strategy and critiques without manuscript text. Cover letters disclose that the IS2 short paper (TH and EN) and an earlier manuscript draft are publicly readable in the GitHub repository, with links. JAMIA accepts preprints; STA's position is asked together with its AI policy.
- 28–29 Nov 2026, night (D44): the PDF report exported from the app is designed and built by a Codex executor, not by the Claude Product Owner. The co-planner first researches how FTO and patent-landscape reports are written and laid out; the target is formal and easy to read. The renderer merged in PO-PDF (02e432e5) stays as the baseline until the Codex card replaces it.
