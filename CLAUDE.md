# Claude instructions for Patent-to-Pilot

**Plan:** the [S0–S5 master plan](docs/evidence-scope/MASTER-PLAN.md) and its [research and data freeze](docs/evidence-scope/FREEZE.md) govern new work. S0 is documentation complete. Wait for the next execution goal to start S1 and S2 in parallel. The P0–P5 owner program of 22 Nov 2026 remains the provenance of the existing measurements and software.
Phases advance by scoped deliverables. A documented null result can close a research phase and the product can advance independently. The IS2 presentation (March 2027) is context,
not a gate. The earlier program PTP-2026-11-21 (G01–G08) is history: G01/G02 are completed foundations, G03 records are
preserved, and G-identifiers keep their meanings.

**Read at session start, in this order:**
1. this file;
2. [HANDOFF.md](HANDOFF.md) (current state);
3. the [master dispatch board and phase sheets](docs/evidence-scope/MASTER-PLAN.md), then the [P0–P5 evidence board](docs/tracking/owner-note-22112026/PHASE_BOARD.md) when following inherited tasks;
4. [INDEX-PLAN.md](INDEX-PLAN.md) (plan and evidence index);
5. [AGENTS.md](AGENTS.md) (shared agent rules).

Then verify the checkout with `git status` and `git log -3`. Chat memory never substitutes for these files.

The dated history that used to live here is preserved verbatim in
[archives/HANDOFF-HISTORY-TO-20261121.md](archives/HANDOFF-HISTORY-TO-20261121.md). It is provenance, not instruction.

## 1. What the project is

**Patent-to-Pilot** (keep the name; plain descriptive method names, no invented acronyms; owner N01) is one research paper
with three linked contributions. One shared evidence engine implements it, and it is delivered through two consumers:

- **Research:** frozen configurations, benchmark adapters, isolated evaluators, ablations, uncertainty and result provenance.
- **Product:** a local Workbench (one Python server, bundled UI, SQLite, local files) that calls the same engine.

**Proposed method** (unmeasured): track whether evidence for each requirement applies in the same scope. Use a bounded controller to keep the ranking, rerank, acquire missing evidence or qualify the explanation. Compare coverage control plus compatibility reranking against the new controller. The earlier single unresolved-relation arm closed with NO_GAIN.

**Research objective:** a real matched retrieval-score win against strong comparators (owner N02). A UI or maintenance gain
does not satisfy it, and there is no automatic pivot to a maintenance headline (N03).

**Report three status fields separately:**
- `method_evidence`;
- `product_readiness`;
- `publication_readiness`.

The owner packages live in `docs/owner/`, read the newest first: `owner-note-22112026/00_START_HERE.md`. They are
**owner-local and untracked: never edit, move, delete or commit anything under `docs/owner/`.**

## 2. Current state (details in HANDOFF.md and the live board)

**Inherited phases.** P0 control/readiness, P1 A3 model-panel experiment, P2 structural candidate acquisition, P3 Thai transfer,
P4 product usability/explainability, P5 manuscript/release/IS2. The live registry is
`docs/tracking/owner-note-22112026/goal_registry.json`; update it **only** through `python scripts/tracking/ptp_tracker.py`,
which renders the CSV, the board and the AFFiNE pages.

**Foundations (complete).**
- G01 local Workbench: [G01/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G01/STATUS.md).
- G02 providers, ingestion and datasets: [G02/STATUS.md](artifacts/owner-program/PTP-2026-11-21/G02/STATUS.md).
- 22 Nov add-ons:
  - PDF text-layer ingestion (pypdf);
  - OpenRouter chat templates with reasoning off and spend caps.

**G03 history.**
- v1, A1 and A2 are PARKED.
- A3r0 (LLM query expansion) has a frozen protocol, but only a **format smoke** has run: 4 calls on 1 TRAIN query. There is
  no effectiveness result.
- A3r1 (Qwen3-32B, DeepSeek V4 Flash, Gemini 2.5 Flash-Lite, Typhoon2.5; 800-token cap) is FROZEN.
  - Pilot: frozen rule **GO**, m\* = DeepSeek V4 Flash, Δ = +0.0245 ALL R@200. The pilot is optimistic and only gates
    spending.
  - Stage B and the full evaluation ran on 24 Nov: frozen rule **CONTINUE**, VAL F3\* − F\* = +0.0213 [0.0146, 0.0280].
    This is exploratory (fourth VAL look; F\* uses C0 routes). P1 is closed.
  - Documents: [amendment](docs/healthtech/research/g03-dev/G03-DEV-AMENDMENT-3R1-PROPOSED.md) and
    [P1-T04 receipt](docs/tracking/owner-note-22112026/receipts/P1-T04_pilot_generation.md).
- **P2-T02 (complete-content control): COMPLETE.** Arctic C1 and BM25-full are the new representation baselines (+0.0165 /
  +0.0223). Structure gets no credit.
- Memo: [G03-DEV-DECISION-MEMO.md](docs/healthtech/research/g03-dev/G03-DEV-DECISION-MEMO.md).

**Money (24 Nov).**
- OpenRouter **E1R** (D11; USD 50, notify 40): USD 3.85 committed. Keys are set as user environment variables.
- RunPod: **R1** (D20, USD 20, P2-T02): about USD 5.1 used. **R2** (D22/D24, USD 60, notify 45): about USD 11.3 used.
- D26 approves D19 RunPod dispatch, delegates US machine selection and raises the D19 sub-cap within R2 to USD 20.
- D21 allows a network volume for reused data (none exists). Use US data centres only (see the 24 Nov handoff).

**PatEmbed on DAPFAM.** The two datasets share a family pool and training overlap is unmeasured (PatenTEB's train split is
unreleased). Report PatEmbed separately, with that caveat:
[audit](docs/healthtech/research/b53-0/PATENTEB-OVERLAP-AUDIT-20261122.md).

**Writing.**
- One manuscript draft: [docs/writing/journal/MANUSCRIPT-DRAFT-v1.md](docs/writing/journal/MANUSCRIPT-DRAFT-v1.md).
  Every unmeasured result is NOT_RUN.
- Corrections register: [WRITING-CORRECTIONS-20261122.md](docs/maintenance/WRITING-CORRECTIONS-20261122.md).
- IS2 arc (D1, D10, including Paper 86's exposure ceiling, IS2-only): [docs/writing/is2/](docs/writing/is2/).

**Owner decisions.** D1–D27 are in [OWNER-DECISIONS-20261122.md](docs/maintenance/OWNER-DECISIONS-20261122.md), and
N01–N12 are in the owner note.

**AFFiNE tracker.** Self-hosted upstream v0.27.4, outside the repo (`C:\Users\User\ptp-tools\affine-tracker`,
http://127.0.0.1:3010). It is a tracker only, never a research dependency. See
[P0-T02 receipt](docs/tracking/owner-note-22112026/receipts/P0-T02_affine_setup.md).

**New account?** Start at the [current handoff](HANDOFF.md) and [master plan](docs/evidence-scope/MASTER-PLAN.md). For dr-train use [the dated handoff §2a](docs/maintenance/NEXT-ACCOUNT-HANDOFF-20261124.md) and [agent lessons](docs/maintenance/AGENT-LESSONS.md).

**Older parked lines.** P1/AM-7 and B53 Stage 1–2 are measured and kept with their original scope; see INDEX-PLAN §3.

## 3. Standing rules (all remain in force)

1. **Never open protected TEST data** (research TEST splits, sealed qrels, per-query TEST outputs). Exposed sets stay exposed;
   they never select methods.
2. **No paid API, RunPod or other GPU rental without an owner envelope** (a recorded amount and scope). Quote each pod's hourly rate before creation, get owner approval, and delete the pod after use. D27 approves in-scope installs and dataset downloads for S1–S5. Record each item's revision, rights and digest. Earlier per-item download rules still apply outside that scope.
3. **dr-train:** reach it as `ssh chaw@100.77.149.83`. Use only the approved V100, always with `CUDA_VISIBLE_DEVICES=1`.
   GPU0 (RTX 2080 Ti) is not approved. One GPU job at a time, under the shared GPU lock.
4. **Pre-declare before computing.** Freeze the protocol, endpoints and selection rule before any number exists; one settle
   per job; report failures and unknown costs, never repair outputs silently.
5. **Report to the owner in Thai.** Code, paper, product and developer docs are English-first; keep source documents in their
   original language.
6. **Commit only your own files**, with explicit paths (never `git add -A`). Push to `origin main` after a verified package.
7. **Update the handoff on major events:** a finished step, an owner decision, a new blocker, before long or background jobs,
   and before ending a session. Rewrite the current-state section of HANDOFF.md in place; update the S dispatch board and the applicable phase task state. Update inherited P rows only with the tracker CLI.
8. **After every phase, pull this project's dr-train artifacts to local, then delete the remote copies that are no longer
   needed** (this project's folders only, never other users' or services' data). Procedure:
   [docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md](docs/maintenance/DR-TRAIN-ARTIFACT-RUNBOOK.md).
9. **Paper 86 is banned in journal papers** (never mentioned, cited or reused). It is allowed only in the IS2 track.
   `tests/test_org_adaptive_terminology.py` enforces this over `docs/writing/journal/`.
10. **arXiv:2605.24297 is not used as a source.**
11. Paper 53 may be cited as the authors' own prior work (iSAI-NLP 2026 program listing; no DOI verified).
12. No LLM judge as ground truth. Literal source match is source integrity, not semantic support.
13. Never read or print `.env` or credentials. No force-push, `git reset --hard`, `git clean`, or history rewriting.

## 4. Protected code (G01 and G02 shipped)

Do not change `src/patent_to_pilot/workbench/`, `scripts/ptp_run.py`, `Start-PTP.cmd`, `tests/` or
`artifacts/owner-program/` without a goal that requires it. An activated S execution phase or an authorized P task provides scope for the code it names.
Run the test suite before committing code; the only accepted pre-existing failures are the 8 SACR r2/r3 supervisor budget
tests.
- `python -m pytest` uses the system Python, which has pytest but no pypdf, so the PDF tests skip.
- For the full gate with pypdf, run:
  `python -c "import sys; sys.path.append(r'.venv/Lib/site-packages'); import pytest; sys.exit(pytest.main(['-q']))"`

## 5. Where things are

| Need | Location |
|---|---|
| Run the Workbench | `Start-PTP.cmd`, or `python scripts/ptp_run.py --doctor` / `--smoke` / `--serve` |
| Engine and Workbench code | `src/patent_to_pilot/workbench/` (G01), legacy modules in `src/patent_to_pilot/` |
| Active S0–S5 plan and freeze | [Master plan](docs/evidence-scope/MASTER-PLAN.md) and [prospective freeze](docs/evidence-scope/FREEZE.md) |
| Inherited plan and receipts (P0–P5) | `docs/tracking/owner-note-22112026/` (board, registry, receipts, AFFiNE pages); tool `scripts/tracking/ptp_tracker.py` |
| Foundation receipts (G01/G02) | `artifacts/owner-program/PTP-2026-11-21/<goal>/` |
| Budget ledger | `src/patent_to_pilot/budget/` (shared reservations for research and Workbench calls) |
| Research evidence (frozen protocols, results, audits) | `docs/healthtech/research/`, `docs/healthtech/audits/` |
| Writing | `docs/writing/journal/` (the one paper), `docs/writing/is2/` (IS2) |
| Housekeeping record of 21 Nov 2026 | [docs/HOUSEKEEPING-20261121.md](docs/HOUSEKEEPING-20261121.md) |
| Private artifacts outside Git | `../_private_artifacts/` (never commit their contents) |
