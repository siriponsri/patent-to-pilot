# Prompt for the next Claude agent (copy everything below the line)

The owner keeps this file current so that another Claude account can take over without loss. The live state is always in `HANDOFF.md`, not here.

---

You are continuing a solo research project for the owner (Siripon, GitHub `siriponsri`). The repository is `C:/Users/User/Desktop/myProject/patent-to-pilot`, on branch `main`, pushed to https://github.com/siriponsri/patent-to-pilot. Work only on `main` in this checkout: no worktrees, no branches, no resets, no force pushes.

**Talk to the owner in Thai, in plain language for a beginner.** If anything is unclear, or you see a better plan, propose it and ask before acting.

## Read first, in this order
1. `HANDOFF.md`, section "Agent takeover state" at the top. It is the live state: running jobs, the next steps and blockers. It overrides everything below.
2. `CLAUDE.md` and `AGENTS.md`, the project rules, including the **handoff rule**:
   - update the takeover section of `HANDOFF.md` and push after every step, before any long job, and after every owner decision;
   - never include secrets.
3. The current study, the **Medtech Time Machine (MTM) benchmark**:
   - rules: `docs/healthtech/research/MEDTECH_TIME_MACHINE_BENCHMARK_RULES_DRAFT_20261107_EN.md` (frozen at `7d317e7`);
   - every dev method, declared before its run, with its results: `docs/healthtech/research/MEDTECH_TIME_MACHINE_DEV_METHODS_LOG_20261108_EN.md`;
   - the plan audit and literature check: `docs/healthtech/audits/ptp-medtech-tm-phase3-audit-20261109/README.md`;
   - the audits of each phase: `docs/healthtech/audits/ptp-medtech-tm-*`.

## Where the study stands (check HANDOFF.md for anything newer)
- **Task:** retrieve older, cross-field (no shared CPC3), examiner-cited prior art for US medical-device grants under a publication-date time filter.
  - Dev: grants 2010–2016, 1,985 queries.
  - Test: grants 2019–2023, 1,955 queries. **The test split is sealed.**
  - Primary measure: lane X, query view P (an LLM problem brief), corpus view main, hit@20.
- **Dev results so far** (X baseline: PatEmbed-large MaxP, hit@20 0.180):
  - **V4** (a Qwen3-8B yes/no rerank of the X top 30, prompt R-neutral, fused with dense at λ 0.5): +0.017 [+0.010, +0.025]. It is the only eligible method so far.
  - BM25, the hybrid, the bge-reranker, bge + dense, and the function-text channel are null or negative.
  - Phase 1 had a query-prefix defect; its corrected re-run is phase 1b.
- **Bottleneck:** exposure. 61% of dev queries have no target in the top 200. Phase 3 targets first-stage recall:
  - 3a: vector PRF;
  - 3b: a citation-reuse gating probe, with a fixed go/no-go rule;
  - then a cited-distractor corpus view, 3c citation chasing (only if the 3b gate says GO), 3d time-safe citation fine-tuning, and DAPFAM as a secondary benchmark.
- **Critical caution:** the corpus is enriched with cited documents. Every citation-derived method needs the popularity-null control and the cited-distractor view.

## Hard rules
- **Test split:**
  - never run any analysis with `--split test`, and never read test labels;
  - the single test read happens only after the owner freezes at most 4 methods (rules §14).
- **Declare first:** every method gets a methods-log entry before it runs. Its settings never change after results are seen; a change becomes a new entry. No retries; a failed step is reported, not overwritten.
- **Secrets:**
  - never read or print `.env` or `.env.bigquery`, and never show secrets;
  - BigQuery runs only through `scripts/healthtech/bq_probe.py` (dry-run first; the owner's per-query cap is final).
- **Spend:** no paid API calls without new owner authorisation.
- **Git:** keep DAPFAM texts, LLM-generated texts and rankings out of Git. Commit only aggregates, hashes and authored files.
- **Earlier work:**
  - never mention the owner's superseded unpublished DAPFAM manuscript or its labels;
  - the owner's published IEEE reranking paper (*Diagnosing Near-Zero Instruction Effects in Cross-Domain Patent Reranking*, to be presented 19–21 Nov 2026, no DOI yet) may be cited.
- **Honesty:**
  - do not claim business or user validation; NLI and developer judgements are labelled proxies;
  - report results honestly, including negative ones; never fabricate numbers.
- **Licences:**
  - PatEmbed-large is CC BY-NC-SA 4.0 (research only);
  - Google Patents Public Data is CC BY 4.0, which requires attribution, the licence link, the table, retrieval dates and a statement of modifications.

## Infrastructure
- **GPU:** dr-train, `ssh chaw@100.77.149.83`. Use only the V100 with `CUDA_VISIBLE_DEVICES=GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089`.
  - The window is authorised until **31 Dec 2026 16:59 UTC**.
  - One job at a time. Launch long jobs with `setsid nohup`, and log status to `<job>/logs/status.log`.
- **Paths on dr-train:**
  - venv: `/home/chaw/patent-to-pilot-jobs/research-product-o1-o4-20261031/venv/bin/python`;
  - models: `.../research-product-o1-o4-20261031/models`;
  - MTM job root: `/home/chaw/patent-to-pilot-jobs/mtm-20261107` (inputs, out, dev1, dev1b, dev2, dev3a, ...).
- **Code for jobs:** `git archive <sha> | ssh ... tar -x -C <job>/code`. Always archive a pushed commit.
- **Local Python:** use system `python` for pytest and ruff. BigQuery uses `C:/Users/User/.ptp-scout-venv/Scripts/python`.
- **Commits** end with:

  ```
  Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
  ```

## How to start
1. Run `git status`, `git log -5` and `git rev-list --left-right --count main...origin/main`.
2. Read the takeover section of `HANDOFF.md`.
3. Check any running job's `status.log` over ssh.
4. Tell the owner, in Thai, where things stand and what you propose next. Then continue with the next step in `HANDOFF.md`.
