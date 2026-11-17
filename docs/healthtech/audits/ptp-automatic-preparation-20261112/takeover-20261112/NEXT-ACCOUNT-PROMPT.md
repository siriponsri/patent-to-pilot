# Prompt for the next Claude account (copy-paste)

```text
You are taking over Patent-to-Pilot (repo C:/Users/User/Desktop/myProject/patent-to-pilot, branch main). Report to the owner in Thai.

1. Read HANDOFF.md, top section "TAKEOVER STATE ... FINAL CHECKPOINT". It overrides all older sections. Then read
   docs/healthtech/research/paper2-precheck/README.md (do-not-repeat ledger) and
   docs/healthtech/research/plans/PAPER-2-3-MERGED-PLAN-20261116.md.
2. Verify: git log -5 (expect the final-checkpoint commit on top), git status (only owner untracked files:
   uv.lock, docs/owner/, docs/healthtech/research/PATENT_TO_PILOT_RESEARCH_AND_CLAUDE_HANDOFF_2026-11-09.md, .claude/).
   Nothing should be running: no S8 driver, no ptp-* containers on chaw@100.77.149.83.
3. Paper 1 is DONE (H1 INCONCLUSIVE). Never re-run S8 jobs or re-open test qrels.
   First task: fill the placeholders of docs/healthtech/research/PAPER1-MANUSCRIPT-DRAFT.md from
   docs/healthtech/research/paper1-report/TEST-RESULT-TABLES.md, keep conclusion branch C, delete branches A/B,
   and write the Thai owner report.
4. Then ask the owner the open decisions listed in TAKEOVER STATE section 7 as ONE package
   (RunPod method, R5 downloads, OpenRouter sub-ledger, plan v2 freeze). Do not rent, download or spend before that.
5. Rules: pre-declare before computing; one settle per job; no LLM judge; commit only your own files;
   do not install ai-memory (owner decision: repo memory only).
```
