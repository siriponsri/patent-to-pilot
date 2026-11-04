# Claude continuation instructions for Patent-to-Pilot

This file is a project-local continuation guide. `AGENTS.md`, the current owner instruction, and the canonical HealthTech audit records remain authoritative. Do not treat this file as evidence that the research goal is complete.

## Current checkpoint

- Repository: `C:/Users/User/Desktop/myProject/patent-to-pilot`
- Branch: `main`
- Main checkpoint before this file was added: `686f8338c4b288cfe706ae16f4aae8f885b81ebb`
- Source merge already tested: `26be1c1f037c35352a5c0c4bbc8f0fbc0c135f09`
- Current task state: owner requested a detailed handoff, main verification/push, local cleanup where safe, then pause.
- Goal status: not complete overall. Engineering is complete for the current offline scope; science, paid comparison, external business validation, and WPI submission remain partial or blocked.

Read `HANDOFF.md` for the full evidence map and current worktree inventory.

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

When editing code, use an isolated branch/worktree. Keep one control plane and avoid multiple writers on the same files. Before a change, inspect current status and ownership. After a change, run focused tests and record the exact candidate SHA, command, exit code, and artifact path.

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

The owner requested local branch/worktree cleanup. A clean, unused worktree can be removed after the main push is verified. A dirty worktree remains until its owner explicitly authorizes discarding or a recoverable archive is created. Record all retained worktrees in `HANDOFF.md`.

## Resume sequence

1. Confirm `main` is clean and equal to `origin/main`.
2. Read `HANDOFF.md` and the canonical merge audit.
3. Reconcile the current acceptance matrix with actual artifacts; do not pool different heads.
4. Select one independent offline package or the paid admission package if its live gates pass.
5. Run focused tests and write a new audit receipt.
6. Update progress and next actions once for the completed package.
7. Stop at `READY_FOR_REVIEW` or an explicit partial/blocker state.

## Current final boundary

Engineering: complete for current offline scope.

Scientific evidence: partial; no admissible final semantic holdout or paid matched comparison.

Business validation: partial; solo developer proxy/scenario only.

Manuscript/WPI: partial; owner review and journal-specific checks remain; not submitted.

Paid API: blocked before reservation by stale credit evidence.

Do not close the research goal because tests or a canary pass. Do not open a second goal for the same Patent-to-Pilot work.
