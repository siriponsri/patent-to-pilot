# Prompt for the next Claude account (copy everything below the line)

> **Routing amendment - 10 November 2026:** start from [AGENTS](AGENTS.md), [CLAUDE](CLAUDE.md), latest [HANDOFF](HANDOFF.md), [MASTER-PLAN](MASTER-PLAN.md), [INDEX-PLAN](INDEX-PLAN.md) and [shared memory](memory/research/patent-to-pilot/INDEX.md). The prompt below is preserved historical context. Its older dual-benchmark/continuation wording does not override the DAPFAM-first conditional programme or current scope/permissions. Do not automatically retry consumed smoke/curator work or access test. Update the index and both checkpoints at every substantive event.

Send this prompt together with the attached research handoff `PATENT_TO_PILOT_RESEARCH_AND_CLAUDE_HANDOFF_2026-11-09.md`. The live project state is always in `HANDOFF.md` in the repository.

---

You are continuing the Patent-to-Pilot / Solution Scout research project for the owner (Siripon, GitHub `siriponsri`). A previous Claude account did the work up to commit `05a4650` and ran out of weekly tokens.

**Talk to the owner in Thai, in plain language for a beginner.** Write repository research documents in English. If something is unclear, or you see a better plan, propose it and ask before acting.

## What you have
1. **The attached research handoff** (`PATENT_TO_PILOT_RESEARCH_AND_CLAUDE_HANDOFF_2026-11-09.md`, reference snapshot `05a4650`). It is the owner's chosen research direction:
   - a **method-first** paper;
   - DAPFAM as the external anchor, MTM as the MedTech evaluation;
   - **SACR** (selective abstraction with preserved requirements) as the untested candidate method;
   - work packages R0–R6, with R0/R1 integrity repairs first.

   Read sections 1, 3, 5, 7, 14, 16 and 20 before anything else, then the method sections (8–13) before writing any code.
2. **The repository** `C:/Users/User/Desktop/myProject/patent-to-pilot`, branch `main`, remote https://github.com/siriponsri/patent-to-pilot. Read, in order:
   - `CLAUDE.md` and `AGENTS.md`, the project rules;
   - the top section of `HANDOFF.md`, "Agent takeover state";
   - `docs/healthtech/research/MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md` (frozen at `7d317e7`);
   - `docs/healthtech/research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md`, every dev method with its results;
   - `docs/healthtech/audits/ptp-medtech-tm-*`, especially `ptp-medtech-tm-phase3-audit-20261109`, `-dev-phase2-`, `-dev-phase3a-` and `-dev-phase3b-`.

## How the two sources fit together
- **Research direction and the R0–R6 plan:** follow the attached handoff. The earlier phase-3 ideas recorded in `HANDOFF.md` become optional later work, under the handoff's §16.8:
  - 3d, time-safe citation fine-tuning;
  - the "cited-distractor" corpus view.

  Do not start them unless the owner asks.
- **Process, safety and permissions:** the repository rules and the owner's standing instructions below. Where the attached handoff is stricter, follow the stricter rule. One deliberate exception:
  - **Pushing:** the owner has authorised commit and push to `origin main` for this project (the handoff rule in `CLAUDE.md`). Update `HANDOFF.md`'s takeover section and push after every completed step, before any job longer than about 10 minutes, and after every owner decision.
  - No force pushes, branches, worktrees, resets, or ACL/hook/global-config changes.
- **Temporal training:** the attached handoff's audit item A04 (grant-year bins are not priority-date chronology) applies to any future citation training. The earlier "train on 2001–2009 grants" idea is not time-safe as written.

## State at `05a4650` (verify against the checkout and `HANDOFF.md`)
- **MTM:**
  - dev: 1,985 queries, grants 2010–2016;
  - test: 1,955 queries, grants 2019–2023, **sealed**. Test rankings exist for the baseline only; none have been scored.
- **Primary measure:** P/main/X hit@20. The PatEmbed-large MaxP baseline gives hit@20 / @100 / @200 of 0.180 / 0.313 / 0.388 on dev.
- **The only eligible dev method:** V4, a Qwen3-8B yes/no rerank of the X top 30, prompt R-neutral, fused with dense at λ 0.5. Out of fold +0.017 [+0.010, +0.025]. The cluster bootstrap gives the same result.
- **Null or negative, all on record:**
  - corrected BM25 and hybrid (V1b/V2b);
  - the bge reranker and its dense fusion (V3b/V5);
  - the function channel (V6);
  - vector PRF (3a);
  - the citation-reuse probe (3b): reach 30.3%, NO_GO, so citation chasing was not built.
  - Phase 1 (V1–V3) is an invalid run: a query-prefix defect, kept on record.
- **No GPU job is running.** Nothing is left half-finished.

## Owner rules (standing; do not re-ask)
- **Test split:**
  - never run anything with `--split test`, and never read or print test labels;
  - the single test read comes only after the owner freezes at most 4 methods.
  - Note: `inputs/queries-meta.jsonl` on dr-train holds the targets of both splits. That is the attached handoff's item A01; fixing it is part of R1.
- **Declare first:** every method gets a methods-log entry before it runs. Never change its settings after seeing results; a change becomes a new entry. No retries. A failed or defective run is kept and labelled, never overwritten.
- **Secrets:**
  - never read or print `.env` or `.env.bigquery`, and never show secrets;
  - BigQuery runs only through `scripts/healthtech/bq_probe.py` (dry-run first). The owner's per-query cap is currently 34 GiB;
  - every new pull needs owner approval, with the dry-run estimate shown first.
- **Spend:** no paid API calls. No model training and no full-corpus re-encoding without owner approval.
- **Git content:** keep DAPFAM texts, LLM-generated texts, rankings and private scores out of Git. Commit only aggregates, hashes and authored files.
- **Earlier work:**
  - never mention the owner's superseded, unpublished DAPFAM manuscript, its title or any of its labels;
  - the owner's published IEEE paper *Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking* (Srihangpiboon & Ploysuwan) may and should be cited. It is to be presented on 19–21 Nov 2026, with no DOI yet, so cite it as "to appear".
- **Honesty:**
  - no business or user-validation claims; NLI and developer judgements are labelled proxies;
  - report negative results honestly, and never fabricate numbers or references.
- **Licences:**
  - PatEmbed-large is CC BY-NC-SA 4.0 (research only);
  - the DAPFAM HF dataset is CC BY-NC-SA 4.0;
  - Google Patents Public Data is CC BY 4.0, attributed to IFI CLAIMS and Google, with the licence link, table, retrieval dates and modifications stated.

## Infrastructure
- **GPU:** dr-train, `ssh chaw@100.77.149.83`. Use only the V100, with `CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089`.
  - Authorised until **31 Dec 2026 16:59 UTC** (`src/patent_to_pilot/healthtech/local_execution.py`).
  - One job at a time. Launch with `setsid nohup`, and write status lines to `<job>/logs/status.log`.
  - Ship code with `git archive <pushed-sha> | ssh ... "tar -x -C <job>/code"`.
- **Paths on dr-train:**
  - venv: `/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python`;
  - models (`patembed-large`, `qwen3-8b`, `bge-reranker-v2-m3`): `.../research-product-o1-o4-20261031/models`;
  - MTM root: `/home/chaw/patent-to-pilot-jobs/mtm-20261107` (`inputs/`, `out/`, `dev1`, `dev1b`, `dev2`, `dev3a`, `dev3b`).
- **Local Python:**
  - system `python` for pytest and ruff (only lint the files you change);
  - `C:/Users/User/.ptp-scout-venv/Scripts/python` for BigQuery.
  - Private artifacts live in `../_private_artifacts/healthtech/`.
- **Commit messages** end with:

  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  ```

## Your first response (do not run experiments yet)
Follow the attached handoff's §20.2. Reply to the owner in Thai with:
1. the actual commit (`git status`, `git log -5`, `git rev-list --left-right --count main...origin/main`) and anything that changed since `05a4650`;
2. the benchmark and split manifests that exist;
3. which R1 repairs are open, starting with A01 (label separation), A03 (gold eligibility under the exact runtime mask) and A14 (binding vectors to the corpus);
4. the reusable model and index artifacts, and the current authorisation (GPU to 31 Dec, BigQuery per approval);
5. the first bounded work package and its deliverable.

Ask the owner only about decisions that are really theirs: protected evaluation, protocol amendments, spending, rights, release.

Also offer to save the attached handoff into the repository as `docs/healthtech/research/PTP_METHOD_FIRST_RESEARCH_HANDOFF_20261109_EN.md`, so that future agents have it.
