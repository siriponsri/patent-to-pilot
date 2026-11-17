# Prompt for the next Claude account (copy-paste)

```text
You are taking over Patent-to-Pilot (repo C:/Users/User/Desktop/myProject/patent-to-pilot, branch main). Report to the owner in Thai.

1. Read, in this order:
   a. docs/healthtech/research/plans/DIRECTION-20261117-BRIDGERET-HANDOFF.md (the owner's new direction + review + work order).
   b. The owner's notes in docs/owner/owner-note-17112026/ (start with master_plan_and_go_assessment.md, then paper_1_methodology.md).
   c. HANDOFF.md top sections (DIRECTION CHANGE, then FINAL CHECKPOINT) and docs/healthtech/research/paper2-precheck/README.md (do-not-repeat ledger).
2. Verify: git log -5, git status (only owner untracked files), nothing running on chaw@100.77.149.83 (docker ps | grep ptp-).
3. P1-DAPFAM is closed (H1 INCONCLUSIVE). Never re-run its jobs or re-open its test qrels.
4. First action: send the owner ONE decision package (O1-O10, R5 text downloads with exact files and sizes, RunPod method, the proposals 1-5 in the handoff note, confirmation that fine-tuning is allowed for P1-BridgeRet). Run nothing costly before the answer.
5. Then follow the work order in section 3 of the handoff note. Pre-declare before computing; open each test once; no LLM judge; no paid API, rental or download without a recorded approval; commit only your own files; do not install ai-memory.
```
