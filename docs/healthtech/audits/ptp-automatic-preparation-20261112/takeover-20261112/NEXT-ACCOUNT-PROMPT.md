# Prompt for the next Claude account (copy-paste)

```text
You are taking over Patent-to-Pilot (repo C:/Users/User/Desktop/myProject/patent-to-pilot, branch main) as the sole writer. Report to the owner in Thai, short and plain.

READ FIRST (in order):
1. docs/healthtech/research/plans/DIRECTION-20261117-BRIDGERET-HANDOFF.md (the new direction, review and work order)
2. docs/healthtech/research/plans/owner-decisions-20261117-bridgeret.json (owner decisions, ALREADY ANSWERED; do not ask them again)
3. The owner's notes in docs/owner/owner-note-17112026/ (master_plan_and_go_assessment.md, then paper_1_methodology.md). These are owner-local and untracked; never commit or publish them.
4. HANDOFF.md top sections (DIRECTION CHANGE, then FINAL CHECKPOINT) and docs/healthtech/research/paper2-precheck/README.md (do-not-repeat ledger)

VERIFY before acting: git log -5; git status (only the owner's untracked files); nothing running on chaw@100.77.149.83 (docker ps | grep ptp-).

STATE: P1-DAPFAM is closed (H1 INCONCLUSIVE). Never re-run its jobs or re-open its test qrels. The new study is P1-BridgeRet: fine-tune Snowflake/snowflake-arctic-embed-m-v2.0 on USPTO Office Action 102/103 citations, then RRF with BM25. Primary endpoint: OUT Recall@200 (RPD) on P1-TEST.

OWNER DECISIONS (recorded):
- TRAIN = filing 2006-2009.
- P1-TEST = the last 10,000 tasks of 2012 in reverse sha256 order.
- Full fine-tuning (LoRA only as a recorded fallback); reranker denoise.
- DAPFAM single look: local only, labelled exploratory.
- Tier A+ (USD 175 = API 100 + GPU 75).
- Fine-tuning allowed for this study.
- PatentsView text download approved up to 60 GB: list exact files and sizes first and record them, then download to dr-train /data/ptp-paper2/.
- RunPod via the official MCP with hosted OAuth: every create/delete needs the owner's approval; never store API keys. The RunPod pilot keeps its USD 10 cap.
- Proposals 1-5 accepted:
  1. study names P1-DAPFAM / P1-BridgeRet;
  2. unseen-doc subset reported alongside the primary result, with a no-sign-flip rule;
  3. V100 for encoding/mining, RunPod for fine-tuning;
  4. native prompts for every baseline;
  5. DAPFAM look labelled exploratory.

WORK ORDER:
S0 Licence check (Arctic, PatentsView, OA dataset). List, record and download the text tables (≤ 60 GB). G1.0 coverage report on CPU; reuse docs/healthtech/research/paper2-precheck/oa/ scripts.
S1 Split manifest (TRAIN/VAL 2010/DEV 2011 stripe/P1-TEST) + decontamination. Commit docs/healthtech/research/plans/P1-BRIDGERET-PREDECLARATION.md BEFORE any retrieval number.
Pilot Run the RunPod pilot (runbook docs/healthtech/research/paper2-precheck/runpod/RUNPOD-PILOT-RUNBOOK.md), extended to Arctic fp16 encoding and a short fine-tuning step, within USD 10. Measure the V100 fp16 rate too.
S2-S7 Corpus (~1M docs), zero-shot baselines, σ from DEV, mining, denoise, recipe pilots, full fine-tuning, ablations. DEV only.
S8 Freeze (hash) and open P1-TEST ONCE. S9 optional DAPFAM local look. S10 Write-up.
Also: update the Paper 2 plan per the owner's patch note (master plan section 7) when plan v2 is frozen.

RULES: pre-declare before computing; open each test set once; no LLM judge; one settle per job; record the expected cost of every paid run and stop before it; only USPTO public-domain text and model weights go to RunPod; commit only your own files with explicit paths; update HANDOFF.md, CLAUDE.md and INDEX-PLAN.md at each step; do not install ai-memory; never name the withdrawn earlier configuration study in new study files (Paper 53 may be cited).
```
