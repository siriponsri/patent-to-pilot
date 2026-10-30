# PR #1 backend/UI integration

Outcome: **PASS_LOCAL_FILE_INTEGRATION** on the combined main/Claude candidate. Publication status is recorded separately in `MERGE_RECEIPT.json` when verified; a test PASS alone is not a merge claim.

The owner explicitly requested backend compatibility review and merge of PR #1 into current main. This supersedes the previous overnight task's no-main-publication direction for this package only. Remote encoding, paid inference, deployment and outreach remain outside this package.

## Starting state and ownership

- Main and origin/main: `a0ec9ceaf381ebbce6e6c340a8b420189eb8474c`.
- PR #1 head: `7ca0f2eab4a157d208fe0b9b949b83814e4fbcb2`, branch `claude/healthtech-ux-local-20261028`; 144 main-only and 5 UI-only commits.
- Fresh GitHub inspection: OPEN, not draft, mergeable; no submitted reviews. No review was submitted on the owner's behalf.
- Claude's worktree was clean and remained read-only. The main worktree's pre-existing untracked `pepo-unblock-remote-20261030T2038Z` audit was preserved. No reset, stash, clean, forced push, worktree deletion or configuration change was used.
- Work took place on isolated branch `codex/pepo-ui-integration-20261031`. The two reviewed metadata-rights source changes were copied from the earlier Pepo repair worktree; vector/shard repairs were deliberately left there. The earlier worktree's dirty files were preserved.
- Selected scope: HT-W12/W13 integration and HT-W19 verification. Stop after tested local file workflow and verified main publication, or at a concrete branch-protection/concurrency blocker.

## Findings and fixes

1. **Confirmed stale schemas:** current Python `DossierVersion` produced `sources[].rights`, while the versioned schema served by UI rejected that field. Current `RunManifest` also has `rights_summary`. Regenerated `DossierInput`, `DossierVersion` and `RunManifest` schemas from current models. A new executable cross-language regression generates a fresh Python run, checks exact schema equality and imports/round-trips the edited version in JavaScript. It failed before regeneration and passes afterwards; closed-schema validation was retained.
2. **Source-derived company metadata bypassed external field policy:** reused the reviewed source-field projection repair. External JSON keeps only a reviewed field whose string value equals the pinned source; local records and separate authored edits remain intact. Two hand-computable positive/negative regressions cover product-display and redistribution purposes.
3. **Receipt identity gaps:** UI now rejects cross-query manifests/events, duplicate event steps and mixed-policy receipts instead of showing potentially misleading resource totals. Positive current-backend artifacts still import.
4. **Acceptance runner overwrote prior evidence:** browser tests now use a fresh timestamped audit destination or an explicitly empty `HEALTHTECH_E2E_OUT` directory, preserving original branch receipts.
5. **Historical F2/F4 statements were stale against current main:** current backend already uses atomic exclusive history publication and includes backend `user_edits` in TH/EN Markdown. Existing concurrency/interruption regressions were rerun; a new generated version-2 case checks both backend and browser Markdown. The browser overlay still has its own IndexedDB snapshot namespace and renderer. Updated current runbook/comment without rewriting historical acceptance results.

## Actual verification

| Check | Result |
|---|---|
| `rtk proxy python -B scripts/healthtech/verify_offline.py <fresh-private-output> --suite all` | 476 collected: **475 passed, 1 optional tokenizer skip**, 0 failures/errors; 0 guarded network attempts, 0 repository credential-file read attempts |
| `HEALTHTECH_PUBLIC_RUN_DIR=<existing-public-case> rtk proxy npm test` | **72/72**, no skip, including current-backend schema/dossier cross-check |
| `HEALTHTECH_E2E_OUT=<fresh-run-folder> ... rtk proxy npm run test:e2e` | **17/17**, headless Chrome, real IndexedDB, source checks, conflict handling, exports, responsive themes, tour/video; no page errors |
| `prepare_ui_integration.py` on supplied local MitraClip/Tendyne/TriClip snapshots | Fresh current-backend lexical runs; 41 patent inputs/case, candidates **35/20/28**, source-backed disclosed associations **21/17/23**, history 1→2, source checks and TH/EN exports |
| `HEALTHTECH_BACKEND_CASES=<private-generated-cases> rtk proxy npm run test:integration` | **3/3 actual file-input imports**, exact source inspection, receipt consistency, IndexedDB save/reload and downloaded edited TH/EN reports; 0 page errors |
| `rtk proxy python docs/healthtech/ux/validate_docs.py --repo-root .` | **8/8** documented domain/schema/link checks |
| JavaScript syntax and `git diff --check` | PASS; see `verification.json` for measured file count |

The real-source preparation uses the supplied original patent IDs as title labels and reuses pinned source text. It is a functional integration run, not a matched retrieval-quality comparison. Original local vector-backed dossiers are input snapshots, not newly produced remote vectors. Source policies correctly block product-display export for all three generated research-only cases. Restricted payloads, vectors and downloaded real-case Markdown remain in private local storage; only sanitized IDs/counts/hashes and authored code are staged.

## Failures resolved during this package

- Initial default `python -m pytest` encountered the sandbox account's existing pytest-temp ownership permissions (257 passed, 1 skipped, 216 setup errors). An explicit fresh permitted basetemp passed; final guarded verification uses its own fresh basetemp. No ACL or global tool settings were changed.
- The new cross-language regression exposed the stale-schema failures described above.
- First preparation invocation lacked the repository root on its Python import path; fixed in the script before the successful three-case run.
- First new browser harness run used an old project ID while an asynchronous import switched projects. Its wait now requires the expected query identity before capturing the project ID; the corrected three-case run passes. This was a harness failure, not a product data-loss finding.
- One browser process did not start because execution transport disconnected; the known-not-started operation was retried after reconnection. There was no approval denial or uncertain remote mutation.

## Limits and next work

This completes the checked **local CLI artifacts → browser import/inspection/notes/save/export** integration slice. Browser run-start/control and backend history HTTP services remain unavailable and honestly capability-gated. No cloud sync, deployment, paid provider call, remote job or new scientific experiment occurred. API spend in this task is USD 0; the old cumulative OpenRouter USD 8 authorization was not reset or expanded. Clinical/FTO, semantic relevance, exhaustive recall, publication and commercial claims remain unvalidated.

Supporting records: [verification](verification.json), [guarded backend](backend-verification.json), [browser acceptance](frontend-browser.json), [real backend cases](backend-cases.json), [real browser integration](browser-backend.json), [source hashes](source-hashes.json), [continuation](NEXT_ACTIONS.md). Raw historical receipts remain unchanged. The private case outputs are reproducible using the two new checked-in preparation/browser scripts and the owner-supplied source snapshots.
