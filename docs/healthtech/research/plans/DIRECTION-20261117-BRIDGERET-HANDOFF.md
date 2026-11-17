# Direction change 2026-11-17: Paper 1 → BridgeRet (handoff for the next agent)

Status: **OWNER DIRECTION; OWNER DECISIONS RECORDED 2026-11-17** in [owner-decisions-20261117-bridgeret.json](owner-decisions-20261117-bridgeret.json). The study is not frozen yet, and nothing has been run.

**Decided:**
- TRAIN = filing 2006-2009; n1 = 10,000; Arctic-embed-m-v2.0; reranker denoise; full FT with a LoRA fallback.
- DAPFAM single look: local only, labelled exploratory.
- Budget: Tier A+ (USD 175 = API 100 + GPU 75).
- Publish IDs, manifests and scripts after the licence check.
- RunPod via MCP OAuth, with the owner approving each action.
- PatentsView text download approved up to 60 GB (list the files first).
- Fine-tuning allowed for P1-BridgeRet.
- Proposals 1-5 all accepted.

Source of the direction: the owner's planning notes in `docs/owner/owner-note-17112026/`. Those files are owner-local and untracked; do not commit or publish them without the owner's OK.
- `master_plan_and_go_assessment.md`: read this first. Section 7 is the patch note for Paper 2/3; section 10 lists the owner decisions.
- `paper_1_introduction.md`, `paper_1_literature_review.md`, `paper_1_methodology.md`: the new Paper 1.
- `paper_2_*`, `paper_3_*`, `budget_plan.md`, `product_roadmap.md`.

Previous state: the final checkpoint at the top of `HANDOFF.md` (commit 3732056) is still valid for everything not changed here.

## 1. What changes (owner direction, kept as written)

| Item | Before | Now |
|---|---|---|
| Paper 1 | DAPFAM query-rewriting study (FA/GR/SACR); test done, H1 INCONCLUSIVE | **BridgeRet:** fine-tune a commercially licensed dual encoder (snowflake-arctic-embed-m-v2.0, Apache-2.0; fallback Qwen3-Embedding-0.6B) on examiner 102/103 citations from the USPTO Office Action data, then RRF with BM25 |
| Data | OA splits DEV 2011 / P2-TEST 2012 / P3-TEST 2013 | + TRAIN = filing 2006-2009 (about 100,376 tasks, 440k pairs); VAL = about 2,000 tasks from 2010; DEV = 2011 (a stripe separate from P2's DEV); **P1-TEST = the last n₁ ≈ 8-10k tasks of 2012 in reverse hash order** (P2-TEST takes the first n) |
| Corpus | P2 open population (5.5-7.9M documents) | P1 uses a **fixed benchmark corpus of about 1M documents**, 1 passage per doc (title + abstract + first claim, ≤ 512 tokens), with RPD visibility per query |
| Primary endpoint | — | OUT Recall@200 (RPD, query-macro), Holm, α = 0.05, δ = 0.010. Wins A-D (+ optional E/F) as in `paper_1_methodology.md` section 9 |
| Paper 2 | arms E0-E3 | + E0-P1 and E3-P1 (the P1 checkpoint as dense_search). Contrasts C3′ = E0-P1 − E0 and C4′ = E3-P1 − E0-P1. The reranker FT becomes optional. P2-TEST excludes the P1-TEST tail |
| Paper 3 | EG-SHE | unchanged (the tool surface uses E0-P1 if P1 passes) |
| Product | static baseline | the P1 retriever (Apache) is the main commercial candidate (M2) |
| Rule "no training" | in force | **lifted by the owner for P1 fine-tuning** (record this when the owner confirms O1-O10) |

## 2. Feasibility review and the few changes proposed (minimal; the owner decides)

The direction is feasible. I found **no blocker that forces a change**, but there is one critical-path item. The proposals below are improvements, not replacements.

**Critical path (not a change, but the plan depends on it):**
- Query and corpus text needs abstract and claim-1 text for 2006-2013 applications and for the cited documents.
- Not yet downloaded: the PatentsView pre-grant (`pg_*`) and grant (`g_*`) text and claims tables.
- G1.0 cannot be checked without them. This is the R5 download decision and should be asked first, with exact file names and sizes.
- Cited documents granted before 1976 are not in PatentsView. Count them in G1.0.

**Proposed improvements (each optional):**
1. **Name the two Paper 1 studies distinctly** in every file, to stop agents confusing them: `P1-DAPFAM` (closed, H1 INCONCLUSIVE) and `P1-BridgeRet` (new).
   - Keep P1-DAPFAM as a short pre-registered negative report, or as the motivation section of BridgeRet. The work and the test look are already paid for.
2. **Pre-declare the "unseen-doc" subset as a co-reported analysis**, not only a sensitivity analysis. The subset is P1-TEST tasks whose positives never appear in TRAIN.
   - Add one rule: the sign of the primary contrast must not flip on this subset.
   - This answers the obvious memorisation critique: OA-SPLITS found about 20k cited documents shared between yearly splits.
3. **Use the free V100 for encoding and mining; use RunPod mainly for fine-tuning.** S8 is finished, so the V100 is idle.
   - The fp16 rate (about 105 passages/s in the owner's note) is not measured on our V100 yet; measure it in the RunPod pilot / S3.
   - This should cut the GPU USD of the plan.
4. **Give every zero-shot baseline its own recommended query/document prompt** (PatEmbed's published retrieval prompt pair, Arctic's query prefix), with the same 1-passage text. A prompt mismatch would inflate Win-C.
5. **DAPFAM single look (O5):** if approved, run it locally only (CC BY-NC-SA), on the frozen checkpoint, and label it external and exploratory. The DAPFAM test was already opened once by P1-DAPFAM.

Things I would NOT change: the model choice, the TRAIN/VAL/DEV/TEST years, the n₁ range, the endpoint, the win ladder, the budget tiers.

## 3. Order of work for the next agent

1. **DONE 2026-11-17: the owner answered the decision package.** See the decisions JSON. Do not ask these questions again.
   - O1-O10 from `master_plan_and_go_assessment.md` section 10: TRAIN 2006-2009, n₁, model, denoise, DAPFAM single look, Tier (A+ recommended by the owner's note), publishing manifests, licence check, OAER, LoRA vs full FT.
   - Plus: the R5 text downloads (exact files and sizes), the RunPod pod-creation method (console or MCP via OAuth), proposals 1-5 above, and confirmation that the "no training" rule is lifted for P1.
2. **S0:** licence checks (Arctic Apache-2.0, PatentsView, OA dataset), approved downloads, and the G1.0 coverage report (CPU on dr-train; reuse `docs/healthtech/research/paper2-precheck/oa/` scripts).
3. **S1:** split manifest (TRAIN/VAL/DEV/P1-TEST, reverse-tail rule, decontamination). Commit the pre-declaration (`plans/P1-BRIDGERET-PREDECLARATION.md`) BEFORE any retrieval number.
4. **RunPod pilot** (already approved, USD 10 cap): runbook `docs/healthtech/research/paper2-precheck/runpod/RUNPOD-PILOT-RUNBOOK.md`. Extend it to measure Arctic fp16 encode and a short FT step if the cap allows.
5. **S2-S7** on DEV only, then freeze (G1.4) and open P1-TEST once (S8).
6. Update the P2 plan per the owner's patch note (section 7) when plan v2 is frozen.

## 4. Fixed rules (unchanged)
- Never re-run P1-DAPFAM S8 jobs and never re-open its test qrels.
- Pre-declare before computing. Open each test set once. No LLM judge. One settle per job.
- No paid API, rental or download without a recorded per-item owner approval.
  - RunPod pilot: approved, USD 10 hard cap (the account holds USD 57, which does not raise the cap).
  - Only USPTO public-domain text and model weights go to RunPod. No DAPFAM, no test labels.
- Do not install ai-memory; use the repo memory only.
- Commit only your own files. Report to the owner in Thai.
- Do not name the withdrawn earlier configuration study in new study files. Paper 53 may be cited.
