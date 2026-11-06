# Patent-to-Pilot HealthTech Handoff

Status: `ACTIVE_WPI_RESEARCH_PACKAGE_TRACK_A_COMPLETE_TRACK_B_DESCRIPTIVE`

## Agent takeover state — 6 Nov 2026 (read this first)

Last pushed commit before this note: `69efd30`. All work is on `main` in this checkout; there are no worktrees or branches.

### Where the study stands

- **Direction (owner-approved 6 Nov 2026):** a product-led WPI paper for **Solution Scout** (Cross-Industry Solution Scout).
  - A short problem brief goes in. Out comes a two-lane shortlist (own field / other fields), a descriptive field map, and quote-checked LLM transfer rationales.
  - Spec: [SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md](docs/healthtech/research/SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md). §2 holds the evidence table, §6 the evaluation E1–E5, §7 the milestones, §9 the owner approvals.
- **Pre-declared dev results behind the design.** The DAPFAM test split has never been read.

  | Check | Result | Audit |
  |---|---|---|
  | Stage 1 | Original gate PASS, learnable headroom FAIL | [audit](docs/healthtech/audits/ptp-org-adaptive-stage1-20261105/README.md) |
  | Scout feasibility | `PARTIAL_LANE_ONLY` | [audit](docs/healthtech/audits/ptp-solution-scout-feasibility-20261105/README.md) |
  | Atlas headroom | `GO_ORACLE_ONLY` | [audit](docs/healthtech/audits/ptp-solution-atlas-headroom-20261106/README.md) |

  The claims of LLM retrieval gain, org-adaptive gain and class-prior gain are all **not** carried forward.
- **Owner approvals (spec §9):**
  - a public demo corpus with V100 encoding;
  - one DAPFAM test read for E1–E2, **only after a freeze commit**;
  - E5, the PatenTEB replication;
  - the name "Solution Scout".

### Milestones

- **M0 done** (`7162078`): `src/patent_to_pilot/healthtech/scout.py`, holding the contracts, lane partition and literal quote check.
- **M1 done** (`69efd30`): replay-mode backend in `src/patent_to_pilot/healthtech/scout_service.py`, plus `/scout/replay` and `/scout-sessions…` routes in `http.py` and `serve_http.py --scout-replay`. Tests: `tests/test_healthtech_scout*.py`. Suites at that commit: Python 738 passed / 1 skipped; frontend `npm test` 73 passed / 1 skipped.
- **M2 in progress:** frontend screens S1–S6. The owner asked for a "modern + minimal" design with wow impact, on real public data with V100-prepared vectors.

### Decisions made 6 Nov 2026 (owner answers)

1. **Demo corpus: HUPD** (Harvard USPTO Patent Dataset, `HUPD/hupd` on Hugging Face), licence **CC BY-SA 4.0**, not gated.
   - PatentsView was the first choice, but its bulk data now needs a USPTO.gov login with MFA. The data.uspto.gov Open Data Portal has required this since June 2026, and the legacy S3 URLs return 403.
   - Agents must not create accounts or log in.
   - HUPD per-year archives are 2.6–5.6 GB (`data/2016.tar.gz` 5.57 GB, `data/2017.tar.gz` 4.67 GB); `data/sample-jan-2016.tar.gz` is 0.39 GB.
   - Not yet downloaded. Plan: one year on dr-train, then a stratified subset across IPC sections A–H, built from title + abstract (+ first claim) and IPC labels.
   - Share-alike applies to the derived corpus. Record the rights through `rights.py` / `provenance.py`.
2. **Live search: a local CPU encoder.** CPU torch + transformers in an isolated venv (not the repo's global env), with PatEmbed-large weights locally. Not yet installed: torch is absent in the local Python. Qwen rationales are recorded on the V100 and replayed.
3. **Licence flag found 6 Nov 2026:**
   - `datalyes/patembed-large` (revision `2d5c0f92…`) is **CC BY-NC-SA 4.0, non-commercial**.
   - The demo and paper are research use. Any commercial or business deployment would need a different encoder.
   - This must appear in the spec, the demo and the paper.

### Next steps for a new agent

1. Download one HUPD year to dr-train (`chaw@100.77.149.83`, about 115 GB free, two V100s; approved GPU `GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089`). Build the subset and write a rights record.
2. Encode with PatEmbed-large on the V100. Reuse `scripts/healthtech/run_dapfam_dense_pool.py` logic and `dense_passages`, and run a 3-query canary first. Keep vectors and texts out of Git, under `../_private_artifacts/healthtech/scout-public-demo/`.
3. Add a local live dense-search mode to `scout_service.py`: CPU query encoding plus a numpy dot product over the vectors. Keep the replay mode.
4. Record 6–8 authored demo briefs and Qwen3-8B rationales on the V100 into a replay bundle (`ptp-scout-replay-v1`).
5. Build M2 in `frontend/healthtech-web`: panels S1–S6, TH/EN, keyboard paths, no build step. Then run `npm test` and `npm run test:e2e`.
6. Write an audit under `docs/healthtech/audits/`, then commit and push. The owner allows a push after verified work.

### Running or external state

- **HUPD download** (started 6 Nov 2026, about 05:36 server time) on dr-train:
  - Command: `curl -sSL --fail -o raw/hupd-2017.tar.gz https://huggingface.co/datasets/HUPD/hupd/resolve/main/data/2017.tar.gz`
  - Directory: `/home/chaw/patent-to-pilot-jobs/scout-public-demo`; log in `logs/download.log`.
  - Expected size 4,669 MB (HF listing). Check with `ls -la raw/` and `pgrep -af hupd-2017`.
  - If it died partway, delete the partial file and restart; one retry is fine because this is not a paid call.
  - Next: unpack, then build a stratified A–H subset into `subset/`.

- **Hyperresearch deep-research run** (alternative directions; may change spec §6):
  - Tool: `jordan-gibbs/hyperresearch` v0.13.0, commit `aece65f`.
  - It runs in an isolated venv at `C:/Users/User/.hrv`, with the vault at `C:/Users/User/.hrv/work`. The prompt is in `research/prompt.txt`; the report will be `research/notes/final_report_<vault_tag>.md`.
  - It was started as a background subagent of the 6 Nov session. It hit a session rate limit once and was resumed. A new agent should check `research/runs/*/run.json` for the current step, not restart it.
  - Never run `hyperresearch install` in this repo or with `--global`: it adds a PreToolUse hook and edits CLAUDE.md, which this project forbids.
- **dr-train job directory:** `/home/chaw/patent-to-pilot-jobs/org-adaptive-20261105`. Private DAPFAM artifacts are under `../_private_artifacts/healthtech/ptp-org-adaptive-20261105/`.

### Standing rules

- No paid API calls without new owner approval. Never read `.env`.
- No worktrees, resets or ACL/hook/global-config changes.
- DAPFAM texts and generated texts stay out of Git.
- Never mention the superseded unpublished manuscript or its labels. The earlier published reranking paper may be cited.
- Do not claim business or user validation.

## Current state — 4 Nov 2026 (supersedes the Normal-round hold below)

- Plan: [PTP_JOURNAL_LONG_RUN.md](docs/healthtech/long-runs/PTP_JOURNAL_LONG_RUN.md), with the owner amendments: E2 allowance USD10 cumulative, push after a verified package, dr-train V100.
- Canonical record: [WPI research package](docs/healthtech/audits/ptp-wpi-research-package-20261104/README.md).
- Track A (primary) used PANORAMA PAR4PC; the protocol was frozen at commit `ff603bb` before the test run. On test:
  - PatEmbed-claim MRR 0.933 vs BM25 0.845 (Δ +0.088, CI +0.058 to +0.120);
  - RRF hybrid was worse than dense alone (Δ −0.020, CI −0.038 to −0.004);
  - the cascade matched the hybrid with 57% escalation but did not beat dense alone.
- The PI4PC paragraph-level replication (freeze `1665075`) did **not** replicate the dense advantage (Δ +0.003, CI −0.017 to +0.022). Fusion beat dense there (Δ +0.014, Holm p = 0.042), and the cascade missed its tolerance. The best fixed policy depends on task granularity.
- Track B: canary content audit 9/9 literal-correct. The device known-link cohort stays descriptive.
- Spending this round: USD0 in paid calls and about 289 s of V100 encoding. The E2 ledger is unchanged since the canary (USD0.99945484 left under the code-enforced USD1; the owner allowance is USD10).
- Next steps: [NEXT_ACTIONS](docs/healthtech/audits/ptp-wpi-research-package-20261104/NEXT_ACTIONS.md). Owner decisions: [READINESS](docs/healthtech/audits/ptp-wpi-research-package-20261104/READINESS.md).
- 5 Nov 2026: an organization-adaptive cross-domain acquisition study on DAPFAM, written as a new self-contained manuscript. See the [protocol draft](docs/healthtech/research/ORG_ADAPTIVE_CROSS_DOMAIN_PROTOCOL_DRAFT_20261105_EN.md), the [PoC plan](docs/healthtech/research/ORG_ADAPTIVE_POC_PLAN_20261105_EN.md) and the [manuscript plan](docs/healthtech/research/ORG_ADAPTIVE_MANUSCRIPT_PLAN_20261105_EN.md).
  - Owner decisions: earlier unpublished analyses are superseded and not cited; only the neutral terms in the manuscript plan are used; organizations are IPC sections; the fixed baseline is the strongest dense passage retriever.
  - Stage 0 PASS: [audit](docs/healthtech/audits/ptp-org-adaptive-stage0-20261105/README.md). Test was not scored. Multi-window queries did not beat single-window on dev.
  - Stage 1 (dev): [audit](docs/healthtech/audits/ptp-org-adaptive-stage1-20261105/README.md).
    - The preregistered gate passed: oracle − F\* 0.099, Q-only share 23%.
    - M\* is R2. The cross-fitted global mix was below R2 (−0.014, CI −0.028 to −0.002), and the per-section mix was below the global mix (−0.008).
    - Under Amendment 1, neither claim goes forward. Test not opened. Next is an owner decision on the direction.
  - Solution-scout feasibility (dev, 6 Nov 2026): `PARTIAL_LANE_ONLY` ([audit](docs/healthtech/audits/ptp-solution-scout-feasibility-20261105/README.md)).
    - The scout pool was below the lane-only pool (−0.066, CI −0.094 to −0.040), so the LLM claim is not carried forward.
    - Post hoc, the lane gain was traced to the IPC3 mask, which matches the strict-OUT definition. Test not opened; USD0 paid.
  - Solution-atlas headroom (dev, 6 Nov 2026): `GO_ORACLE_ONLY` ([audit](docs/healthtech/audits/ptp-solution-atlas-headroom-20261106/README.md)).
    - Oracle class reordering gave +0.059 R@50. The learned class prior gave −0.044 (CI −0.070 to −0.017).
    - Building an external prior is an owner decision. Test not opened; USD0 paid.
  - Product-led paper approved (6 Nov 2026): [solution-scout product spec](docs/healthtech/research/SOLUTION_SCOUT_PRODUCT_SPEC_20261106_EN.md). Status: M0 done (contracts, lane logic and the quote check in `src/patent_to_pilot/healthtech/scout.py`). The owner approved the four decisions in spec §9. M1 is done: replay-mode routes under `/scout-sessions` in `http.py`. Next is M2 (frontend).

Earlier status: `PAUSED_BY_OWNER_NORMAL_MAIN_ONLY_AUDIT`

Observed: 2026-11-04, Asia/Bangkok

Repository: `C:/Users/User/Desktop/myProject/patent-to-pilot`

This file is the resumable handoff for the existing Patent-to-Pilot goal. It records what is verified, what is still partial or blocked, which artifacts are authoritative, and which local worktrees must not be removed without preserving their uncommitted work. It is not a claim that the research goal, business validation, or journal submission is complete.

## Current Normal-round hold — 2026-11-04

This round works only in the existing `main` checkout. Base HEAD before the round was `a8c8e229e6489bb29ae6f88f310f7307c8a09441`, and `origin/main` matched it. Do not resume the goal, start a long run, create a worktree, dispatch or reserve paid work, push, merge, delete branches, or clean worktrees. The bounded deliverable is the E2 documentation/hash correction, offline fixture verification, isolated test-ledger verification, and this handoff update.

The canonical evidence for this round is `NORMAL_ROUND_20261104.md` plus `normal-verification.json` in `docs/healthtech/audits/ptp-e2-admission-recheck-20261104/`. The prior merge push/cleanup actions and the 20261103 candidate worktree remain historical receipts only.

Follow-up read-only check (2026-11-04T13:31–13:36Z): `docs/healthtech/audits/ptp-normal-mcp-admission-check-20261104/`. OpenRouter MCP account credit, exact-route pricing, account binding (hashed creator/workspace match), rights, writer quiescence, the E2 ledger, and dr-train SSH all passed. Paid admission remains blocked because the MCP key is not the dispatch key: the ledger needs a fresh key-scoped observation of `sha256:7cbe4013…`, plus owner authorization. A one-character erratum in the recorded normalized credit hash was fixed in all five affected files, with owner approval (correct value `…80408f9e9a5f06c5d`).

E2 paid canary (owner-authorized, 2026-11-04T13:54–13:56Z): `docs/healthtech/audits/ptp-e2-paid-canary-20261104T1354Z/`. Status is PASS as engineering/accounting evidence: 3/3 schema-valid, 3 settled attempts, 0 retries, USD 0.00054516 total, reconciled with MCP account usage. The ledger is now `d19f58ec…`, and the E2 epoch has USD 0.99945484 remaining. The paid API state is no longer "blocked before reservation". Any further paid work needs a new owner authorization and a new 300-second admission window.

## 1. Objective and scope

The goal is to deliver a usable Patent-to-Pilot HealthTech evidence workflow and a reproducible computational study suitable for owner review and possible submission to *World Patent Information*. The current study concerns device-patent known-link recovery and adaptive evidence acquisition under incomplete judgments.

The current round is a solo reproducible computational study. There are no external participants, no recruitment route, and no independent customer validation. Human pilot work, revenue, willingness-to-pay, and ROI are future work unless separately measured. A three-case product demonstration is engineering evidence only; it is not a powered scientific evaluation and is not user validation.

The product claim remains bounded: prepare an inspectable evidence dossier for an entrepreneur or investment analyst starting from a named public medical device or comparator. A retrieved candidate is not automatically a disclosed link. A literal field or quote match establishes source integrity only; it does not establish semantic entailment, clinical suitability, FTO, patent validity, regulatory approval, or investment merit.

## 2. Repository and revision state

The main checkout was clean before this handoff-document change.

- Repository: `C:/Users/User/Desktop/myProject/patent-to-pilot`
- Branch: `main`
- Main HEAD before this documentation update: `686f8338c4b288cfe706ae16f4aae8f885b81ebb`
- Pushed handoff HEAD: `d407d61eb14c3fbde0163bc7d54207a00dc4f05d`
- `origin/main` after push verification: `d407d61eb14c3fbde0163bc7d54207a00dc4f05d`
- Source merge already tested: `26be1c1f037c35352a5c0c4bbc8f0fbc0c135f09`
- Candidate integration commit: `a71d808`
- Preserved owner-main commit: `f77c502`
- Prior handoff documentation commit: `7e8fd1a`
- Initial handoff-document commit: `d407d61eb14c3fbde0163bc7d54207a00dc4f05d`.
- Cleanup-record commit already pushed: `46421f0d99f3425af1e841991411f80a21031a72`.

The following was the historical handoff check; it is retained for provenance and is not a current push instruction:

```powershell
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git rev-parse origin/main
rtk git rev-list --left-right --count main...origin/main
```

Historical result after push: clean `main`, identical local and remote SHA, and `0 0` ahead/behind.

The push completed on 2026-11-04 at approximately `2026-11-04T12:34:00Z` with `main -> origin/main`. The exact post-push verification at `2026-11-04T12:38:09.5419286Z` returned the same SHA on both sides and `0 0` ahead/behind.

## 3. Verified delivery boundary

### Engineering: COMPLETE for the current offline scope

The merged implementation covers the current offline engineering contract:

- local HTTP/UI path;
- retrieval and evidence projection;
- source inspection;
- edit, save, reopen, and history behavior;
- JSON and Markdown export;
- local generation and guarded accounting paths;
- candidate-bound regression coverage.

Recorded verification from the canonical merge audit:

- Python regression: exit `0`;
- exact candidate-bound receipt: `655 passed, 2 skipped`;
- frontend unit tests: `73 passed, 1 optional skip`;
- HealthTech JSON receipts parsed: `964`;
- source merge-marker scan: clean;
- non-audit `git diff --check`: clean.

This is an engineering statement for the current implementation and receipts. It is not a scientific or commercial completion claim.

### Scientific evidence: PARTIAL

The following remain incomplete or limited:

- no admissible final semantic device-patent holdout is bound to the current final study;
- no powered comparison has established adaptive superiority;
- no paid local/API matched comparison was completed;
- historical PatEmbed and multilingual-e5 artifacts are runtime-bound evidence and must not be silently reinterpreted as a new current-head run;
- Stryker material remains previously exposed diagnostic material, not final gold;
- DAPFAM is diagnostic and is not a semantic device-patent gold standard;
- unlisted links remain unjudged, not negative;
- known-link recall is not exhaustive recall or a lower bound on exhaustive recall.

The manuscript must keep fixed-budget, multi-query, simple-adaptive, and bounded-LLM controls distinct and must freeze cohort, splits, eligible queries, cutoffs, grouping, failure rules, endpoints, and budget controls before any final comparison.

### Business value: PARTIAL, solo proxy and scenario only

Observed engineering quantities may support a practical-potential discussion:

- citation quality and locator integrity;
- evidence coverage within the declared corpus;
- machine/GPU time;
- latency;
- recorded provider cost where an actual receipt exists;
- dossier completion and correction burden in the developer workflow.

The current evidence does not support claims of independent user validation, revenue, willingness-to-pay, customer demand, ROI, or production labor cost. Any labor-rate or volume assumption must remain a scenario or sensitivity analysis and must be labelled as such.

### Manuscript and WPI: PARTIAL

Draft manuscript, methods, figures/tables, references, appendix material, data/code availability language, ethics, funding, conflicts, author contributions, AI-use disclosure, cover letter, and checklist artifacts exist in the repository. Owner review remains required. Official journal-specific Aims and Scope and Guide for Authors details were not fully verified in the local environment, and no manuscript was submitted or accepted.

## 4. Paid/API state

No paid call, reservation, retry, GPU rerun, dataset download, ledger mutation, budget reset, or time-window reset was performed in the merged-main handoff.

Canonical ledger:

`%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`

Known ledger state:

- SQLite integrity: `ok`;
- legacy settled receipts: `4`;
- known actual spend: `USD0.0001464`;
- operational attempts: `0`;
- pending or unknown operational attempts: `0`;
- prospective E2 allowance recorded in the handoff: `USD1`;
- unknown history: preserved and not silently treated as zero.

The previous credit snapshot was stale for the 300-second live gate. The paid branch therefore stopped before reservation. Do not create a zero ledger, reset the epoch, resend an unknown request, or edit an observation timestamp.

If paid work is explicitly resumed, the smallest required gate is one fresh non-secret credit snapshot for the existing dispatch key, current exact-route pricing observed in the same admission window, verified export rights, and a single bounded canary through the canonical ledger. The key must never be read from or printed from `.env` in logs or documentation.

## 5. Evidence map

Read these artifacts in this order when resuming:

1. `AGENTS.md`
2. `GOAL.md`, sections 0-4
3. `PLAN.md`
4. `docs/healthtech/progress.json`
5. `memory/next-actions.md`
6. `docs/healthtech/long-runs/CURRENT_ACCEPTANCE_MATRIX.json`
7. `docs/healthtech/audits/ptp-main-merge-handoff-20261104/README.md`
8. `docs/healthtech/audits/ptp-main-merge-handoff-20261104/verification.json`
9. `docs/healthtech/audits/ptp-main-merge-handoff-20261104/CHECKPOINT.json`

Key source and product areas:

- `src/patent_to_pilot/healthtech/` for the current HealthTech runtime;
- `src/patent_to_pilot/providers/` for provider identity, history, credit, and ledger boundaries;
- `scripts/healthtech/` for reproducible runners and audit tools;
- `tests/` for regression and handoff-bound evidence;
- `frontend/healthtech-web/` for the local UI and browser-facing adapters;
- `docs/healthtech/research/manuscript/` for the manuscript package;
- `docs/healthtech/audits/` for canonical receipts and continuation records.

Private artifacts, credentials, restricted corpora, model weights, and local owner evidence are not publication inputs merely because they exist on disk. Publish only permitted links, identifiers, hashes, and authored fixtures.

## 6. Local branch and worktree inventory at handoff

The following inventory was observed before cleanup. A blank status after the branch line means the worktree had no reported tracked or untracked changes at inspection time. Dirty worktrees contain uncommitted work and must not be removed without an explicit decision to discard or archive that work.

Clean or apparently clean at inspection:

- `claude/healthtech-ux-local-20261028` at `7ca0f2eab4a157d208fe0b9b949b83814e4fbcb2`, worktree `_worktrees/patent-to-pilot-claude-ux-20261028`, remote marked gone;
- `codex/remote-embeddings-20261030` at `68219d78ec0de4c6ffab7fdbc2c79bcacbf612cf`, worktree `_worktrees/patent-to-pilot-codex-remote-embeddings`;
- `codex/luna-publication-20261030` at `bf416e9ab6b6d2d031e885d4b6bb0a2d08bf9ebc`, worktree `_worktrees/patent-to-pilot-luna-publication-20261030`;
- `codex/research-product-o1-20261031` at `257037ab349ec88e5600c074deccfc8a62fe5fc2`, worktree `_worktrees/patent-to-pilot-o1-20261031`, with one untracked browser artifact and therefore not fully clean;
- `codex/pepo-ui-integration-20261031` at `0d049802d36bc2eebe60331ec444d62469fd767f`, worktree `C:/Users/User/Documents/Codex/2026-10-31/task/ptp-integration`;
- `codex/pepo-paused-audit-20261101` at `a0809b4b124a6e19b8aea58c4258397aa60715df`, worktree `C:/Users/User/Documents/Codex/2026-11-01/task-3/publish-http`.

Dirty or containing uncommitted work at inspection:

- `codex/patent-to-pilot-long-run-20261031` at `0cf41e0d37cac75bc9475c8604ab3dabb5c5fd66`, worktree `_worktrees/patent-to-pilot-long-run-20261031`; this contains broad source, test, audit, manuscript, and benchmark changes;
- `codex/r1-owner-evidence-20261031` at `f826069dddb74d4df9ca820a33c07355bec8b357`, worktree `_worktrees/patent-to-pilot-o3-safety-repair-20261031`; this contains manuscript, benchmark, audit, test, and protocol changes;
- `codex/pepo-unblock-remote-20261030` at `a0ec9ceaf381ebbce6e6c340a8b420189eb8474c`, worktree `_worktrees/patent-to-pilot-pepo-unblock-20261030`; this contains source, tests, and audit changes;
- `codex/research-product-o1-o4-20261031` at `b4bc13ccf8a9a71a8f50d16346ae1c6557bc69d0`, worktree `_worktrees/patent-to-pilot-research-product-20261031`; this contains benchmark, manuscript, business-value, test, and audit changes.

The cleanup request below is historical and is not executable in the current Normal round:

- clean, unused worktrees and their local branches may be removed after the push check;
- dirty worktrees must remain until their owner explicitly authorizes discard or a recoverable archive is created;
- no `reset --hard`, `checkout --`, `clean -fd`, force push, ACL change, safe-directory change, or deletion of `.git` data is allowed.

### 6.1 Cleanup performed after owner authorization

The owner explicitly authorized removal of worktrees with no filesystem activity for more than three days, and authorized removal of worktrees whose committed branch work was already merged because a new worktree will be created. Using the observed cutoff before 2026-11-01 and the ancestry checks recorded during this session, the following local worktrees/branches were removed:

- `claude/healthtech-ux-local-20261028` at `7ca0f2e...`; branch tip was an ancestor of `main` and last non-Git file activity was 2026-10-30;
- `codex/remote-embeddings-20261030` at `68219d7...`; last non-Git file activity was 2026-10-30 and the branch tip was retained only locally;
- `codex/luna-publication-20261030` at `bf416e9...`; branch tip was an ancestor of `main` and last non-Git file activity was 2026-10-30;
- `codex/research-product-o1-20261031` at `257037a...`; branch tip was an ancestor of `main`, its remaining untracked artifact was older than three days, and the worktree was removed;
- `codex/r1-owner-evidence-20261031` at `f826069...`; last non-Git file activity was 2026-11-01 09:59:41Z, more than 72 hours before cleanup;
- `codex/pepo-unblock-remote-20261030` at `a0ec9ce...`; branch tip was an ancestor of `main`, last activity was 2026-10-30, and the owner authorized cleanup of the old dirty worktree;
- `codex/pepo-ui-integration-20261031` at `0d04980...`; branch tip was an ancestor of `main` and the branch was deleted. Git removed the worktree registry entry, but Windows refused physical directory deletion because the exact orphan directory contained a protected `.pytest_cache` subtree. No ACL or permission bypass was attempted. The remaining orphan path is `C:/Users/User/Documents/Codex/2026-10-31/task/ptp-integration/.pytest_cache`.
- `codex/o3-safety-repair-20261031` at `9ac3872...`; branch-only local reference, no worktree, last commit 2026-10-31, deleted after the more-than-three-day inactivity check.

The following active worktrees were intentionally retained because they had filesystem activity within the last three days or contained newer uncommitted work:

- `codex/patent-to-pilot-long-run-20261031` at `0cf41e0...`; latest observed file activity 2026-11-02 16:59:23Z; dirty source/tests/audits;
- `codex/research-product-o1-o4-20261031` at `b4bc13c...`; branch tip is an ancestor of `main`, but the worktree contains newer uncommitted benchmark/manuscript/audit changes, latest observed file activity 2026-11-02 13:58:15Z;
- `codex/pepo-paused-audit-20261101` at `a0809b4...`; latest observed file activity 2026-11-01 14:20:18Z, which was still within the three-day window at cleanup.

After cleanup, the local branch set is exactly `main` plus the three retained branches above. Remote branches were not deleted because the owner requested local cleanup and a main push only.

## 7. Current Normal-round instructions

Treat `main` and the canonical audit files as the current control plane, but do not resume the goal in this round. Do not combine receipts from different heads into one PASS. A receipt is admissible only when its candidate revision, inputs, configuration, and output hashes match the claim being made.

First perform:

```powershell
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git rev-parse origin/main
Get-Content -Raw AGENTS.md
Get-Content -Raw GOAL.md
Get-Content -Raw PLAN.md
Get-Content -Raw docs/healthtech/long-runs/CURRENT_ACCEPTANCE_MATRIX.json
```

For this round, complete only these local actions:

1. Verify the current `main` status, HEAD, authorship, and preserved worktree inventory.
2. Correct the E2 hash reference without changing the private snapshot or timestamp.
3. Run offline fixtures and the isolated test ledger; record exact commands and outcomes.
4. Update the handoff and stop before fresh credit, paid admission, GPU, long run, push, merge, or cleanup.

Do not rerun completed GPU work merely to refresh a receipt. Do not use the FDA-only canary as the main scientific result. Do not turn schema validity into content or retrieval validity. Do not claim user validation, revenue, willingness-to-pay, or ROI without measured evidence. Do not submit a paper or accept publisher terms for the owner.

## 8. Stop conditions and unresolved permissions

Stop and report when:

- a paid request lacks a fresh credit snapshot or current price;
- account/key binding is not reconciled;
- a request may have unknown billing state;
- source or dataset rights are unclear;
- an artifact is restricted or contains secrets;
- a worktree is owned by another writer and contains dirty changes;
- a result would require merging different candidate heads;
- a claim would exceed the declared cohort, gold, or evaluation design.

The next actor must preserve the existing ledger and historical receipts. The next actor must not manufacture a zero baseline, change timestamps, reopen a completed offline queue, or delete dirty worktrees merely to make the repository look clean.

## 9. Handoff outcome

Engineering: `COMPLETE_CURRENT_OFFLINE_SCOPE`

Scientific evidence: `PARTIAL`

Business validation: `PARTIAL_SOLO_PROXY_ONLY`

Manuscript/WPI readiness: `PARTIAL_OWNER_REVIEW_REQUIRED_NOT_SUBMITTED`

Paid API: `PASS_E2_CANARY_3_OF_3_USD0.00054516` (engineering only; see `ptp-e2-paid-canary-20261104T1354Z`); further paid work needs new owner authorization

Repository handoff: `READY_FOR_REVIEW`

Owner pause instruction: stop this Normal round after the local audit and test evidence. Resume only after the owner requests a new goal prompt; do not open a new goal for the same work.
