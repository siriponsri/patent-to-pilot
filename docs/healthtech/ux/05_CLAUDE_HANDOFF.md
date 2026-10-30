# Claude Code UX/UI implementation handoff

Outcome to implement: a responsive TH/EN no-code **local frontend** that starts from a named public device/comparator and lets an entrepreneur or investor analyst inspect evidence, annotate uncertainty, save/reopen a local project and export a truthful dossier. Finish this bounded frontend package even while main research data, strong baselines and live service work continue separately. Read [the starter prompt](CLAUDE_STARTER_PROMPT.md), [stories](02_STORY_BACKLOG.md), [screens](03_SCREENS_DESIGN.md) and [integration/state contract](04_INTEGRATION_STATES.md).

This document grants no additional runtime authority. It records the owner's requested future workflow: **Claude implementation must use its own branch before review/merge.** This documentation task created no branch, UI or backend change and did not contact Claude.

## Implementation task contract

| Field | Bounded package |
|---|---|
| Goals/work packages | Contribute to HT-G3/HT-G7 through HT-W13; prepare HT-W16 tasks and HT-W19 local setup/recovery evidence |
| Inputs | Current GOAL/PLAN/README/AGENTS, existing schemas/contracts, this UX package and authored fixtures; optional owner-supplied public dossier copies |
| Outputs | Runnable local frontend, mock/file adapters, transactional local draft handling or honest fallback, TH/EN themes, tested local exports, frontend tests/evidence and local runbook |
| Default owned paths | Proposed new `frontend/healthtech-web/**`, and `docs/healthtech/ux/implementation/**` for evidence/runbook only; confirm these paths are free/current before writing |
| Read-only dependencies | `src/**`, `scripts/healthtech/**`, `schemas/healthtech/**`, provider/budget journals, root governing docs and this specification |
| Exclusions | No backend fix/refactor, API server implementation, live source/provider call, paid inference, evaluator changes, deployment, outreach, raw corpus/PDF publication or global tooling/auth changes |
| Completion target | Local frontend acceptance below, clearly labelled demo/file-import modes and truthful service blockers; not complete HT-G3/HT-G7 or a scientific/product-market validation claim |
| Stop condition | Acceptance evidence and branch diff ready for review; preserve known backend blockers with exact next owner/action |

If a new frontend already exists at execution time, inspect and reuse its stack/conventions rather than create a second app. If default owned paths conflict, choose an isolated frontend path and record the mapping; do not change another writer's files. Reuse existing dependencies; avoid modifying root package/config files to bootstrap the app. Dependencies and local execution require the current runtime's normal permissions. Do not install global tools or new paid services. No framework choice is a reason to delay the available local slice.

## Branch and concurrent-writer workflow

These commands are **proposed for Claude's later execution, NOT_RUN by this docs task**. Inspect state first using the applicable RTK wrapper. Do not switch the shared checkout's branch while another writer is active.

```powershell
rtk proxy git status --short
rtk proxy git rev-parse HEAD
rtk proxy git branch --list 'claude/healthtech-ux-*'
```

Use a unique branch such as `claude/healthtech-ux-local-<suffix>` in an isolated sibling worktree at an owner-accepted current base. Do not guess that the inspected SHA is still the correct integration base. A possible later command form is:

```text
rtk proxy git worktree add -b claude/healthtech-ux-local-<unique> <approved-isolated-worktree> <agreed-base-sha>
```

Replace placeholders explicitly and obey writable-root checks before creation. If this UX pack is still untracked in the original checkout, a worktree at HEAD will not contain it. Read it from the existing location or copy **only this authored pack** into the isolated workspace when permitted, recording its hashes; do not carry unrelated untracked files, raw data or credentials. Never checkout/reset/stash/clean someone else's work. Never stage with `git add .`; stage only Claude-owned implementation/evidence paths if commit is in the current scope. A later commit/push/PR must target Claude's branch. **No direct push/merge to main as part of this package.** Return the exact branch/base/candidate and reviewable diff. The owner/control plane handles integration authorization; routine reversible frontend edits and testing need no repeated confirmation.

## Suggested implementation order

### Step 1 — Inspect and establish a truthful frontend boundary

Read only the relevant current source. Recheck audited findings before relying on a fix. Record adapter capabilities and the chosen stack/owned paths. Implement typed domain JSON import based on existing closed schemas plus explicit semantic validators. Keep `DossierVersion`, local UX snapshot and incomplete project draft types separate. Add the persistent mode/capability banner first so subsequent screens cannot disguise mock behavior. Implement US-01/US-05/US-06/US-15/US-25/US-26 foundations.

Deliverable: app starts locally; demo and imported package modes are distinct; invalid and mixed public/synthetic packages are refused without destroying current content. Do not run API/provider code to “test connectivity.” No credentials are needed.

### Step 2 — Build named-device setup and inspection

Build SCR-01–SCR-04, then SCR-06–SCR-08. Use a locally loaded catalog and a labelled synthetic catalog if real records are unavailable. Project draft may stay incomplete until comparator selected. Pin identities/versions/hashes; view exact field/span; preserve code-point locator semantics. Add feature evidence, candidate comparison, gaps and local uncertainty notes. Finish the A slice without a backend job service.

Deliverable: user can select/import → brief → inspect overview → compare/inspect exact source → draft a question. Current public packages, if supplied, show their actual empty patent pool and no fabricated candidates. Synthetic patent/disclosure rows remain visibly synthetic in every screen/export.

### Step 3 — Make local edits durable and recoverable

Build SCR-09 and save indicators. Prefer a browser transaction that checks expected parent and writes the snapshot/head atomically (for example one IndexedDB transaction) if the chosen environment supports it. A BroadcastChannel notification or beforeunload warning alone is not concurrency control. Use idempotent local operation IDs and retain base/theirs/yours on conflict. A browser-storage implementation must pass reopen and two-writer tests before CAP-06 becomes available. Until then preserve in memory and offer recovery download. Keep backend history unavailable unless its known race is separately fixed and tested by its owner.

Deliverable: acknowledged save/reopen retains annotations and provenance; stale-tab conflict cannot lose edits or report both writes successful. Quota/denial/corruption recovery keeps useful text. Local snapshot counters never overwrite backend dossier version fields.

### Step 4 — Export edited work and next requests

Build SCR-10/SCR-11. Implement lossless recovery JSON and a distinct local Markdown renderer with explicit exporter ID/version. Reuse existing source semantics; do not call backend export and pretend it includes edits. In TH/EN exports, preserve original quotes/IDs, unresolved items, next requests, mode labels, selected version/snapshot and separately labelled user text. Sanitize preview/Markdown without executing HTML or fetching links. Requests are editable local drafts and copy/download only.

Deliverable: a specific Thai/English user note is present after save, reopen, preview, Markdown download and recovery JSON reimport. Backend exporter limitation remains documented until actually fixed. If local Markdown cannot be completed, mark its story incomplete and provide JSON without claiming all UX acceptance passed.

### Step 5 — Add truthful run receipt/progress views

Build SCR-05 from completed manifest/events and explicit simulated scenarios. Do not wait for G1/G2 data work. Simulated loading/partial/cancel/unknown-billing cases exercise the UI, with no real run controls advertised. Attach future run adapter seams with explicit unavailable results. Use current HT-B0b/fixed HT-B2 engineering labels; do not market an adaptive policy. Keep unknown dollars distinct from zero-cost offline receipts.

Deliverable: actual imported counts/stop reasons render consistently; simulated events are labelled; absent service calls cannot accidentally dispatch or report completion. New real service integration is a separate future package.

### Step 6 — Finish themes, bilingual flow and accessible recovery

Apply the four existing theme keys, Thai/English dictionary and full keyboard/responsive behavior across all screens. Use proposed palette tokens as a starting point; verify actual contrast and state combinations. Keep original evidence language and source dates intact. No official KMITL/ICT claims/assets. Avoid modal approvals for ordinary viewing/filtering/saving. Test errors with actionable local recovery, and preserve focus/unsaved text through theme/locale/navigation changes.

Deliverable: one complete keyboard path and responsive review at narrow/tablet/desktop widths, both locales and four themes. Screenshots must come from the actual candidate app; do not fabricate them from specifications.

### Step 7 — Package evidence and hand over for review

Write a concise implementation runbook and acceptance matrix under Claude's owned evidence path. Record exact startup/build/test commands and actual outcomes; no copied historical PASS counts. Link screenshots/recordings if created, and identify every simulated/unavailable behavior. Include source/backend mismatch list, branch/base/candidate hashes and next action. Do not update root goal statuses as complete merely because a frontend slice passes.

## Verification that matters

Use the existing project test/browser tooling if present. The following is a required behavior matrix, not a claim these tests already exist or pass. Choose meaningful hand-computable inputs; no paid benchmark/provider run substitutes for these checks.

| Check | Required evidence |
|---|---|
| Import identity/integrity | Positive authored dossier accepted; hash mismatch, missing source/disclosure, late source, wrong mode and unsupported schema rejected without losing active project |
| Evidence meaning | Candidate remains candidate after exact match/user review; synthetic disclosed example opens separate disclosure evidence; unknown/unjudged never becomes negative/zero |
| Locator | Typed field checks preserve type; Thai/emoji Python code-point range highlights exact span; bad locator cannot earn matched status |
| Persistence | Note edited → acknowledged local save → close/reopen same profile → note retained with original source hash and distinct local snapshot ID |
| Concurrent writers | Two writers sharing same base attempt different edits; stale one conflicts or creates separate explicit copy; both texts recoverable, no false dual success |
| Storage/error recovery | Denied/quota/corrupt history fixtures preserve text; recovery export contains it; unaffected source inspection still works |
| Edited TH/EN export | Distinct user note present in both previews/Markdown and lossless recovery round-trip; source quotes/IDs, unknowns and mode retained; backend omission not masked |
| Budget/run honesty | Imported counters match events; zero offline cost is scoped; unknown monetary receipt stays null/unknown; unsupported network controls absent; simulated cancel acknowledgement explicit |
| UI security/privacy | Source instructions/HTML inert; no credentials/private data requested/logged, no arbitrary source fetch, no automatic telemetry, no synthetic-to-public merge |
| Accessibility | Keyboard selection/source/editor/conflict/export path; screen-reader names/status messages; focus restoration; 200/400% zoom; reduced motion; contrast per theme/state |
| Responsive/bilingual | Narrow 320 px, representative tablet/desktop, long Thai/IDs, all four themes, both locales; no hidden primary actions or lost unsaved state |
| Local operation | Exact install/start/build commands work on stated environment; packaged app doesn't require a server or key for promised demo/file workflows |

Do not fabricate test commands before selecting the actual stack. Record test names, exit codes and evidence paths from the final candidate. Rerun only checks affected by new fixes. If shared backend/provider files unexpectedly change, stop that branch and assign integration/regression checks to its owner instead of silently expanding scope.

## Definition of UX completion

**Local frontend slice complete** only when P0 stories pass using real local browser state/file import plus labelled synthetic scenarios, and the promised P1 stories are implemented or clearly excluded from that slice. For a claim of the full specified local journey, implement all P0 and P1 local behaviors, including comparison, next requests and local package handoff. Proposed real service operations and team collaboration remain unavailable and are listed separately. No P0 failure is converted to a “nice-to-have.”

Completion evidence must include: reproducible local app commands; owned-path diff; branch/base/candidate; acceptance matrix with actual results/modes/fixtures; save/reopen and concurrent-write evidence; TH/EN edited exports and recovery round-trip; responsive/a11y review; truthful blocker list. A successful build or screenshot alone is insufficient.

**Service integration complete** is a later claim requiring real endpoints, durable expected-version history, source resolution, actual run/attempt/cost receipts and corrected backend edited export where used. **HT-G3 complete** additionally requires complete public-case dossiers with real source-backed associations/evidence as defined in GOAL; current facts-only examples do not establish patent coverage. **HT-G7 complete** additionally needs the specified operational/recovery/configuration evidence. Scientific, user/commercial validation and production deployment remain independent, with no such result asserted here.

## Known blockers and who acts next

| Blocker | Status at documentation snapshot | Exact next action/owner | Independent frontend work |
|---|---|---|---|
| No rights-cleared patent corpus/disclosed-link public case | BLOCKED_LOCAL for affected evidence/research branch | Research/data owner resolves source rights, corpus/cohort/provenance; no invented patent results | All fixture/file UI, empty scope explanation, comparison and source inspection |
| No HTTP job/history service | NOT_IMPLEMENTED | Backend owner separately scopes adapter/service endpoints and receipts | Local data adapter, run receipt view, simulation and local persistence |
| Concurrent history race | CHANGES_REQUIRED per supplied audit | Backend owner fixes exclusive expected-version commit and concurrency regression | Transactional browser-local snapshots or honest memory/recovery |
| Backend edited Markdown omission | CHANGES_REQUIRED per supplied audit | Backend owner fixes renderer/round-trip independently | Frontend renderer + recovery JSON with labelled scope |
| SciFact validity/revision and storage cap | CHANGES_REQUIRED per supplied audit | Evaluator/ingestion owners fix affected branches with appropriate checks | Avoid metrics/live fetch promises; implement local import guards |
| Actual users, commercial evidence, live scientific results | NOT_RUN | Owner authorizes/accesses bounded study/participant work | Prepared task script and usable inspectable prototype |

When blocked, report exact action, target, reason, completed independent work and whether outcome is denied/pending/uncertain/not implemented. Do not turn every backend issue into a global stop. Never retry an uncertain mutation until reconciled; respect any runtime denial and the owner's permission boundaries.
