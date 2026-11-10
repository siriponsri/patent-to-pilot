# Claude continuation instructions for Patent-to-Pilot

This file is a project-local continuation guide. `AGENTS.md`, the current owner instruction, and the canonical HealthTech audit records remain authoritative. Do not treat this file as evidence that the research goal is complete.

## Cross-account checkpoint — 10 Nov 2026

- **A14 launch checkpoint (latest):** implementation/56 tests pass; CPU-only real identity inspection PLANNED after publication. See `docs/healthtech/audits/ptp-method-first-r1-vectors-20261110/README.md` and HANDOFF.md for exact job/log/PID paths and no-restart rule. Base/last pushed before package `f3f3a42b3b78097a0b23f197e2efc695b31da277`; Codex active, goal ACTIVE. No label input, GPU job, paid call or re-encoding. Next record actual inspection then DAPFAM parity/integration; physical isolation and real ranking parity remain unverified. Preserve untracked owner research handoff.

- **Latest A03 checkpoint:** exact frozen-mask dev auditor implemented and covered by 44 targeted tests including CLI; real dev audit NOT_RUN. See `docs/healthtech/audits/ptp-method-first-r1-eligibility-20261110/README.md`. Base/last pushed before package: `9378a2c4e777d639cb7f78f8775be575883c0b12`. Codex active, goal ACTIVE; no new jobs/spend/protected-label access. Next A14, DAPFAM parity and runtime integration; trusted staging still required for real dev checks. Details/changed files in HANDOFF.md. Earlier A03 implementation-next notes are superseded; A01/A03 are not closed.

- **Latest R1 checkpoint:** prospective metadata/staging/dev-evaluator boundary implemented; 39 targeted tests and Ruff pass. See `docs/healthtech/audits/ptp-method-first-r1-boundary-20261110/README.md` and `verification.json`. Base/last pushed before package: `b72cea102d880781b3e1da269a956a54da4d9af9`. Codex active writer, goal ACTIVE. Real staging/isolation and actual ranking parity NOT_RUN; A01 not closed, A03/A14/native DAPFAM parity open. No real protected-label access, experiments, paid calls or jobs. Next: A03 auditor, A14 binding, DAPFAM parity and prospective runner integration; trusted curator staging outside agent label access remains a dependency for real-data checks. Detailed changed files and next actions are in HANDOFF.md. Existing untracked research handoff preserved. This supersedes earlier activation-only/documentation-only notes below.

- **Active long-run goal (owner request, 10 Nov):** created in Codex chat `01a1c2b7-8897-7ea1-b7bb-ad7e8a449775`, following `HANDOFF_PROMPT.md` and the local method-first research handoff. Codex is the active writer; do not start a second account writer without transfer. This supersedes the documentation-only session status below. R0 reconciliation is next, followed by R1 A01/A03/A14 and authorized bounded R2–R4 work. R5 requires owner-approved freeze; R6 is draft preparation only. All existing spending, test, protocol and release gates remain.
- **Goal activation checkpoint:** last verified pushed commit `aed40d4d781708fba29f683554c22e71cd2e935c`; only this file and `HANDOFF.md` changed for activation. The full local research handoff remains untracked and preserved. Read `HANDOFF_PROMPT.md` and research-handoff sections 16/20; complete remaining required reading and current-state inventory before implementation/experiments. No experiment, paid call or GPU job launched; remote artifacts/jobs NOT_VERIFIED. Goal creation succeeded; documentation whitespace and publication checks follow this checkpoint. No activation blocker.

- Owner decision: every checkpoint must update **both `HANDOFF.md` and `CLAUDE.md`**, for Codex and Claude across accounts. The mandatory rule in `AGENTS.md` applies, including before a final response or account transfer and after read-only work.
- Detailed current checkpoint: `HANDOFF.md`, top of `Agent takeover state`. Older checkpoint sections below are historical when they conflict with that state.
- Session: Codex; bounded documentation update, handed off after successful publication; no ongoing writer or job launched by this session.
- Last verified pushed commit before this update: `c3ff405396b73c25027505da70af6258604acf71`; local `main` and cached `origin/main` matched (0/0).
- Changed files: `AGENTS.md`, `HANDOFF.md`, `CLAUDE.md`. Existing untracked research handoff preserved and excluded from this commit.
- Verification: documentation change scope inspected; `git diff --check` PASS (exit 0). Publication is verified separately after the containing commit is pushed; no experiments or runtime tests required for this rule-only change. Remote GPU/job state NOT_VERIFIED in this session.
- Next: verify the containing checkpoint commit and publication; confirm writer ownership; read the existing research handoff and assess R0/R1 under the recorded research boundaries. No new research execution is authorized by this update.

## Handoff rule (owner rule, 6 Nov; extended 10 Nov 2026; always in force)

**Mandatory extension:** every update below must update `CLAUDE.md`'s cross-account checkpoint together with `HANDOFF.md`. Follow `AGENTS.md`'s mandatory cross-account rule for triggers, required fields, single-writer ownership, and publication failures. End-of-session, pause, account transfer, failed attempts and read-only outcomes are checkpoints too. Use a maximum 30-minute interval during active work.

Sessions can end without warning when an account hits its usage limit. Another agent, possibly on another account, must be able to continue from `HANDOFF.md` alone. So:

1. **Start of session:** read the `## Agent takeover state` section at the top of `HANDOFF.md` before anything else. It overrides older sections in that file.
2. **Update it every time** one of these happens:
   - a step finishes (code, data, analysis or document);
   - before starting anything that runs in the background or for more than about 10 minutes (downloads, GPU jobs, subagents, long test suites). Record what runs, where, its log and output paths, and how to check it or wait for it;
   - an owner decision or a new blocker;
   - at least once every 30–60 minutes of active work.
3. **Keep it current, not historical.** Rewrite the takeover section in place. Include:
   - the last pushed commit;
   - milestone status;
   - running jobs;
   - decisions;
   - the next 3–6 concrete steps;
   - blockers.

   Move superseded detail to the audits, not into this section.
4. **Commit and push** the HANDOFF update right away (owner-authorized), together with the work it describes when there is any. Never include secrets, `.env` contents, DAPFAM text or generated text.

## Current checkpoint

- Repository: `C:/Users/User/Desktop/myProject/patent-to-pilot`
- Branch: `main`
- Main checkpoint before this file was added: `686f8338c4b288cfe706ae16f4aae8f885b81ebb`
- Initial pushed handoff checkpoint: `d407d61eb14c3fbde0163bc7d54207a00dc4f05d`
- Cleanup-record checkpoint: `46421f0d99f3425af1e841991411f80a21031a72`
- Source merge already tested: `26be1c1f037c35352a5c0c4bbc8f0fbc0c135f09`
- Current task state (4 Nov 2026): the WPI long-run plan is active on `main` per `docs/healthtech/long-runs/PTP_JOURNAL_LONG_RUN.md` and the owner amendments (E2 USD10 cumulative; push after a verified package; dr-train V100). Track A (PAR4PC) is complete; see `docs/healthtech/audits/ptp-wpi-research-package-20261104/`. Do not create worktrees, reset ledgers, submit the manuscript or contact outsiders.
- Earlier task state: Normal main-only audit (superseded).
- Goal status: not complete overall. Engineering is complete for the current offline scope; science, paid comparison, external business validation, and WPI submission remain partial or blocked.

Read `HANDOFF.md` for the full evidence map and current worktree inventory.

The earlier 2026-11-04 push and cleanup receipt is historical evidence only: its verified handoff SHA was `d407d61eb14c3fbde0163bc7d54207a00dc4f05d`, and its retained-worktree/orphan details remain in `HANDOFF.md`. Do not repeat push, cleanup, branch deletion, worktree creation, or ACL bypass in the current Normal round.

## Required reading before any future change

Read these files before changing code, tests, protocol, or manuscript:

1. `AGENTS.md`
2. `GOAL.md` sections 0-4
3. `PLAN.md`
4. `docs/healthtech/progress.json`
5. `memory/next-actions.md`
6. `docs/healthtech/long-runs/CURRENT_ACCEPTANCE_MATRIX.json`
7. `docs/healthtech/audits/ptp-main-merge-handoff-20261104/README.md`
8. `docs/healthtech/audits/ptp-main-merge-handoff-20261104/verification.json`
9. `docs/healthtech/audits/ptp-main-merge-handoff-20261104/CHECKPOINT.json`

Verify the actual checkout rather than trusting an old receipt:

```powershell
rtk git status --short --branch
rtk git rev-parse HEAD
rtk git rev-parse origin/main
rtk git rev-list --left-right --count main...origin/main
```

## Non-negotiable research boundaries

This is a solo reproducible computational study. There are no external participants or recruitment channels. Do not ask for participant information again. Do not report independent user validation, customer demand, revenue, willingness-to-pay, or ROI. Developer self-evaluation is a proxy and must be labelled with its bias. Scenario labor rates and workload volumes are assumptions, not observations.

The scientific question is whether adaptive evidence acquisition improves inspectable device-patent dossiers or cost trade-offs relative to declared fixed and simple-adaptive baselines under the same cohort, evidence access, and budget. Freeze the evaluation before looking at final results. Keep development and final holdout groups separated by device or patent family where applicable. Report uncertainty, ablations, failures, retries, latency, tokens, and cost. Do not infer significance from three demonstration cases.

Keep these distinctions explicit:

- `disclosed_link` is not `retrieved_candidate`;
- `unjudged` is not negative;
- literal source match is not semantic entailment;
- schema validity is not content correctness;
- historical diagnostic material is not final gold;
- known-link recall is not exhaustive recall;
- a cached or old receipt is not a current-head run.

## Engineering scope

The current offline engineering scope covers the UI-to-dossier path, retrieval/evidence projection, source inspection, editing/history/reopen, export, local generation, and guarded accounting. Preserve raw and canonical identifiers, kind codes, revision/hash, jurisdiction, date, and exact locator. Keep source facts, reported associations, system inference, and unresolved items separate.

Use existing repository patterns. Do not add a new ledger, reset the accounting epoch, duplicate a provider binding, or copy secrets into logs, Git, audit files, manuscript artifacts, or examples. Never read or print `.env` contents. Do not change ACLs, hooks, `safe.directory`, or global configuration.

For this Normal round, edit only the existing `main` checkout; do not create a branch or worktree. Keep one control plane and avoid multiple writers on the same files. Before a change, inspect current status and ownership. After a change, run focused tests and record the exact base/candidate SHA, command, exit code, and artifact path.

## Paid/API admission

Paid work is independent from local work and must remain bounded. The canonical ledger is:

`%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`

Known state at the handoff:

- four legacy settled receipts;
- known actual spend `USD0.0001464`;
- no operational or pending/unknown attempts;
- prospective E2 allowance `USD1` in the existing handoff;
- history completeness unknown and preserved.

The last credit snapshot was stale for the 300-second gate. If paid work is later resumed, obtain one fresh non-secret credit snapshot for the existing key, observe current exact-route pricing in the same admission window, verify export rights and writer quiescence, and reserve/dispatch only one bounded canary through the existing ledger. Do not retry a request with unknown outcome. Do not reset budget or timestamp. Do not treat owner visual credit evidence as an API balance unless the adapter explicitly records it as such.

## Evidence and manuscript

Use `docs/healthtech/audits/` as the canonical record. Every new receipt should include, where applicable:

- candidate revision;
- source/config hashes;
- exact prompts/messages and output schema;
- model and revision;
- input/output hashes;
- response, failure, retry, latency, token, and cost fields;
- rights/provenance state;
- explicit `PASS`, `FAIL`, `PARTIAL`, `BLOCKED`, or `NOT_RUN` status.

Keep private or restricted payloads outside Git. Publish only permitted links, identifiers, hashes, and authored fixtures. Do not submit to World Patent Information or accept an author agreement for the owner. The manuscript is a draft package, not a submitted article.

## Cleanup and ownership

Do not delete a dirty worktree, branch, untracked artifact, or sole-copy evidence merely to make the repository clean. Before deleting a worktree, verify its absolute path, ownership, status, and whether its branch tip or dirty-only files are preserved elsewhere. `git reset --hard`, `git clean -fd`, force push, pack deletion, ACL changes, and safe-directory changes are prohibited.

Cleanup is paused for this Normal round. Preserve every branch, worktree, untracked artifact, and sole-copy receipt; do not remove or archive anything unless a later owner instruction explicitly authorizes that separate action.

## Current Normal-round sequence

1. Confirm the existing `main` checkout, HEAD, authorship, and worktree inventory.
2. Read the current handoff and E2 audit without resuming the long-run worktree.
3. Make only bounded documentation/test/audit corrections on `main`.
4. Run offline fixtures and an isolated test ledger; record exact outcomes.
5. Update the handoff, progress pointer, and next action once, then stop.

No paid dispatch/reservation, GPU job, long run, push, merge, branch deletion, or worktree creation is allowed in this round.

## Current final boundary

Engineering: complete for current offline scope.

Scientific evidence: Track A has a preregistered PAR4PC test result with paired CIs and negative fusion and cascade findings. Track B (device links) is descriptive only; there is no matched local-vs-API comparison yet.

Business validation: partial; solo developer proxy/scenario only.

Manuscript/WPI: partial. Track A sections are written. The Guide for Authors is still HTTP 403. The reframing, declarations and license await the owner. Not submitted.

Paid API: owner-authorized E2 canary passed on 2026-11-04 (3/3 settled, USD 0.00054516; `docs/healthtech/audits/ptp-e2-paid-canary-20261104T1354Z/`). This is engineering evidence only. Further paid work needs new owner authorization and a new 300-second admission window.

Do not close the research goal because tests or a canary pass. Do not open a second goal for the same Patent-to-Pilot work.
