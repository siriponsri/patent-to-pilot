# Next-account handoff, 22 Nov 2026 (b, after the afternoon session)

Paste the prompt in §1 into a new Claude Code session opened in `C:\Users\User\Desktop\myProject\patent-to-pilot`.
It replaces [NEXT-ACCOUNT-HANDOFF-20261122.md](NEXT-ACCOUNT-HANDOFF-20261122.md), whose task list is done or blocked.

## 1. Prompt to paste

```text
You are continuing program PTP-2026-11-21 (patent-to-pilot) from another Claude account. Read, in order:
CLAUDE.md, HANDOFF.md, INDEX-PLAN.md, AGENTS.md, docs/maintenance/AGENT-LESSONS.md,
docs/maintenance/OWNER-DECISIONS-20261122.md, docs/maintenance/API-BUDGET-PROPOSAL-20261122.md,
docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261122b.md, docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3-20261122.md.
Then run `git status` and `git log -8`. Report to the owner in plain Thai. All standing rules in CLAUDE.md §3 apply.

Do these in order, without asking about routine choices:
1. G03 amendment 3 pilot (frozen; code committed). Check that OPENROUTER_API_KEY is set (never print it). If not, ask
   the owner once in Thai to set it as a Windows user environment variable and restart the app. Read get-credits.
   Then run the caller for the 4 pilot models exactly as in HANDOFF "Next steps" 1, write a3/pilot-costs.json, upload
   the ledgers, and run code/g03_queue_a3_pilot.sh detached on dr-train. Apply the frozen GO/STOP rule. Stage B
   (one full run with m*) only on GO, within E1 (stop at USD 6). Then add memo §4c, pull and prune per the runbook.
2. IS2 re-scope (D1/D5/D6) after the owner approves the Thai outline (if the owner has not answered, show it again).
3. Workbench OpenRouter check (one profile, <= USD 0.20) once the key is set; record the receipt under G02.
4. G04 planning (DAPFAM headline routes BM25/Qwen3/Arctic; PatEmbed separate, "possibly contaminated").
Finish each step with a commit, a push and a HANDOFF update. At the end, write a new next-account handoff file.
```

## 2. State (all pushed to origin/main)

| Item | State | Where |
|---|---|---|
| G03 A2 learned selector | **PARKED** (VAL ALL +0.0017 [−0.0019, +0.0054]; IN lower −0.0060) | memo §4b, `g03-dev-results-a2.json` |
| G03 A1 | PARKED; a mask defect in T/C routes is disclosed in §4a (cannot have helped A1) | memo §4a |
| G03 A3 LLM query expansion | **FROZEN**, code ready, smoke OK on 4 models (USD 0.00064), pilot waiting for the API key | `G03-DEV-AMENDMENT-3-20261122.md`, `scripts/research/g03_a3_*.py`, `g03_queue_a3_pilot.sh` |
| A3 inputs | `queries-dev-val.jsonl` (P1-DEV 26,575 + VAL 2,000), `apps-pilot.json` (2,000), `apps-P1-DEV.json` (25,626), `apps-VAL.json` (1,919) | dr-train `g03-dev/a3/`, local `../_private_artifacts/g03-a3/inputs/` |
| D3 PatenTEB | Train split **not released**; partial audit: DAPFAM is inside PatenTEB's pool (50 queries, 466 corpus families in 3 test files) | `docs/healthtech/research/b53-0/PATENTEB-OVERLAP-AUDIT-20261122.md` |
| D8 PDF | pypdf 6.21.4 in `.venv`; Workbench PDF ingestion active with tests | `workbench/ingest.py`, `tests/test_ptp_g02_pdf_ingest.py` |
| D7 profiles | 4 OpenRouter chat templates, reasoning off, USD 0.05 / 20 requests each | `workbench/providers.py`, `tests/test_ptp_g02_openrouter_profiles.py` |
| dr-train | g03-dev pulled (826 OK) and compressed (24.44 GB freed); nothing running | `artifacts/maintenance/20261122-g03-pull/SUMMARY.md` |
| OpenRouter balance | total credits 10, usage 1.63501 (≈ USD 8.365 left) | `g03-dev-a3-spend.json` |

## 3. Lessons from this session

- `python -m pytest` uses the system Python (it has pytest and pyarrow, but no pypdf), and the PDF tests skip there. To
  run them with pypdf:
  `python -c "import sys; sys.path.append(r'.venv/Lib/site-packages'); import pytest; sys.exit(pytest.main(['-q']))"`.
  The `.venv` has no pip and no pytest; install into it with `uv pip install --python .venv/Scripts/python.exe <pkg>`.
- Writing Python through a Bash heredoc can turn `"\\n"` into real newlines (a NUL byte also appeared). Write patch
  scripts with the Write tool instead.
- OpenRouter: Haiku 5.5 hits `max_tokens` 400 with the A3 prompt. The caller keeps complete priors (`salvaged`); keywords
  are lost for those. Qwen3.7-Flash and DeepSeek V4 Flash default to reasoning on, so the caller sends reasoning off.
- A remote `cmd1 && … && setsid nohup job & disown` backgrounds the whole chain; that is harmless, but the ssh call
  then waits until the tool times out.

## 4. Open with the owner

- `OPENROUTER_API_KEY` (blocks A3 and the Workbench check).
- The IS2 Thai outline approval.
- The PatenTEB option (audit §5).
- RunPod caps, the Paper 53 DOI, the G01 launcher check.
