# Patent-to-Pilot completion audit R7 — 2026-11-03

Status: `PARTIAL_NOT_COMPLETE`.

This audit continues the original Patent-to-Pilot O1–O4 objective on one
candidate. It preserves dirty Claude/Luna/owner work, keeps historical and
current-head evidence separate, and does not redefine completion as passing
tests, a three-case demo, or a documentation-only package.

## Candidate

- Worktree: `C:/Users/User/Desktop/myProject/_worktrees/patent-to-pilot-long-run-20261103`
- Branch: `codex/patent-to-pilot-long-run-20261103`
- HEAD: `88dc40471cb9078f929c02bb893cfa1e364da841`
- Deadline: `2026-11-15 23:59 Asia/Bangkok`
- Dirty worktree: preserved; no reset, clean, mixed-snapshot merge, or push

## Requirement decision

| Area | Status | Evidence boundary |
|---|---|---|
| O1 UI → HTTP → source inspection → edit/history → reopen → export | COMPLETE | Current-head browser/vector receipts cover three named real-device cases. |
| O2 PatEmbed/e5 encode and retrieval | PARTIAL | Prior remote artifacts are hash-reconciled; no new authorized dr-train allocation or encode is evidenced. |
| O3 local generation | PASS_CONTRACT_SMOKE | Guided local Qwen3-8B is schema-valid for 3/3 cases; semantic correctness is not established. |
| O3 paid API generation | BLOCKED_BEFORE_RESERVATION | Canonical R1 history/registry and current scoped credit snapshot remain unavailable. |
| O4 engineering application slice | COMPLETE_CURRENT_HEAD_ENGINEERING | Three cases pass retrieval/source/history/export workflow and local generation contract. |
| O4 scientific comparison | PARTIAL_DESCRIPTIVE_NOT_ESTIMABLE | No admissible semantic device–patent gold, final holdout, sufficient independent groups, or equal realized total budgets. |
| Business value | PARTIAL_SCENARIO_ONLY | Machine-time/cost-quality proxies exist; external validation, revenue, ROI, and willingness-to-pay are not measured. |
| Manuscript | PASS_INTEGRITY_OWNER_REVIEW_PENDING | Exact-head hash and 45-link closure pass; owner declarations, release choice, and WPI final review remain. |
| Merge/submission | NOT_DONE | Owner review and candidate-bound acceptance are still required. |

## Current evidence

- Full offline suite on the candidate: `617 total / 616 passed / 1 skipped / 0 failed / 0 errors`.
- Current focused metadata/API/local regression: `62 passed / 0 failed / 0 errors / 0 skipped`.
- Documentation validation: `8/8` checks passed.
- JSON validation: acceptance/progress/audit JSON files passed readback.
- Scoped `git diff --check`: pass; pre-existing line-ending noise in `memory/next-actions.md` remains untouched.
- Current manuscript: `50,363` bytes, SHA-256 `b21f7d38b49f873575a5c74ac46ac4c431c06122df999bda818e8d02aa2b213a`, `45` relative links checked, `0` missing.

## Research metrics retained without overclaim

Current-head descriptive macro known-link Recall@20 is HT-B0a `0.442739`,
HT-B0b `0.662242`, HT-B1 `0.498802`, HT-B2 `0.568912`, HT-B3 `0.498802`, and
offline HT-B4 `0.498802`. The post-hoc first-action control ties HT-B1,
HT-B2-prefix-1, and HT-B3-prefix-1 at `0.498802`; it is not a confirmatory
adaptive comparison. PANORAMA component test hit@1 is `0.715124` for PAR4PC
and `0.401235` for PI4PC, with hit@8 `1.0` for both; these are component
diagnostics, not device–patent semantic gold.

## Paid/API gate

- Owner parallel authorization: recorded, conditional on all live gates.
- Key endpoint: HTTP 200; lifetime usage `USD0.0001464`; daily/weekly/monthly usage `USD0`.
- Key class: ordinary non-management; scoped credit unavailable.
- Account scope: not reconciled; R1 history completeness: not proven.
- Canonical registry/journal: absent at the reviewed default path.
- Provider calls/reservations/attempts/retries/ledger mutations: `0`.
- Zero ledger, budget reset, and 24-hour window reset: `false`.

Lifetime usage is not a credit balance and aggregate equality with legacy
journals is not proof of complete R1 history. No legacy journal is promoted.

## Resource and release boundary

No new GPU job, dataset download, participant contact, public release, merge,
push, or submission occurred in this audit. The approved V100 and deadline
remain available only after action-time allocation/ownership checks; idle
capacity is not treated as an allocation.

## Resume

Continue local/offline and manuscript work without rerunning the frozen
benchmark. When the two non-secret paid-gate artifacts arrive, inspect any
export with `scripts/healthtech/inspect_r1_history_export.py`, reconcile the
existing canonical ledger, recheck route/pricing/rights/pending exposure and
writer quiescence, and reserve one small paired canary only if every live gate
passes. Separately, run the existing resumable dr-train encoder only after an
authorized allocation reference/window is evidenced.
