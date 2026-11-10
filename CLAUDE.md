# Claude continuation instructions for Patent-to-Pilot

This file is a project-local continuation guide. `AGENTS.md`, the current owner instruction, and the canonical HealthTech audit records remain authoritative. Do not treat this file as evidence that the research goal is complete.

## Cross-account checkpoint — 2026-11-10 08:32:30 Bangkok

- Codex single active writer in chat01a1c2b7-8897-7ea1-b7bb-ad7e8a449775; Goal ACTIVE. Read HANDOFF.md takeover state. Last verified pushed base cbf433842f1d969b3a239876bab162c50153144e.
- Full quote-profile schema: 46 tests/lint passed; independent schema8/8 expected, actual tokenizer7/8. Unicode case FAILED: parser refuses first Thai character260; filter permits premature EOS at token109. Audit docs/healthtech/audits/ptp-method-first-r2-full-schema-20261110/README.md. No model calls/weights, benchmark input or GPU job.
- CPU probe and diagnostic terminal; original failed receipt preserved. SYN-SACR-001/002 unchanged. Next inspect alphabet/dead-end behavior, explicit Unicode configuration and fail-closed integration, then separately versioned CPU checks. Do not launch third model attempt yet.
- One bounded third model attempt only after engineering gate/declaration; stop generation branch on failure, no automatic fourth attempt. Actual R1 isolation/A03/parity and semantic gates remain; curator question unanswered.
- Changes: schema/tests, probe and authored fixtures/failure receipts, audit/methods log and paired handoff/progress. Preserve owner untracked handoff; standing permissions unchanged.

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
