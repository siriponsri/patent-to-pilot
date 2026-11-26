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
