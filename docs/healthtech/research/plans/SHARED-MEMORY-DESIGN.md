# Shared project memory for Codex and Claude

Updated: 10 November 2026. Status: LOCAL_MARKDOWN_WORKFLOW_IMPLEMENTED / AI_MEMORY_SERVICE_NOT_INSTALLED.

[Memory entry point](../../../../memory/research/patent-to-pilot/INDEX.md) · [Component index](../../../../INDEX-PLAN.md) · [Master](../../../../MASTER-PLAN.md)

## 1. Upstream inspection and decision

The owner requested a shared-memory approach informed by [akitaonrails/ai-memory](https://github.com/akitaonrails/ai-memory). We inspected its README, [current architecture](https://github.com/akitaonrails/ai-memory/blob/main/docs/ARCHITECTURE.md), [historical design rationale](https://github.com/akitaonrails/ai-memory/blob/main/docs/design-decisions.md), [Windows guide](https://github.com/akitaonrails/ai-memory/blob/main/docs/windows.md), [security policy](https://github.com/akitaonrails/ai-memory/blob/main/SECURITY.md), [license](https://github.com/akitaonrails/ai-memory/blob/main/LICENSE) and [release record](https://github.com/akitaonrails/ai-memory/releases/tag/v3.4.5) through primary web sources on 10 November 2026. No upstream program was downloaded/executed.

The useful principle is **human-readable, versioned project knowledge with a common index and explicit supersession**. Implement that in this repository now. A server, embedding index and automatic transcript capture are unnecessary for the current small solo project memory. This is an authored adaptation of ideas, not an installed ai-memory integration or copied upstream implementation.

## 2. License, architecture and maintenance assessment

| Topic | Source-supported observation | Project decision |
|---|---|---|
| License | Upstream LICENSE is MIT, copyright 2026 Fabio Akita; redistribution of copied software requires its notice | No upstream software copied; attribution/source links retained. This does not change project/third-party licenses |
| Architecture | Rust MCP service; Markdown wiki is source of truth, SQLite derived retrieval; optional vectors; lifecycle hooks and provider-backed maintenance | Reuse the file/index/supersession design only; no database/process/network endpoint |
| Continuity | Upstream supports cross-CLI handoff via stored project knowledge; optional managed workstreams can read native transcript tails | No session-store/transcript import in this project; agents explicitly read approved files |
| Installation | Windows installer changes user PATH; setup can configure agent integrations and persistence/logon; native/WSL paths differ | NOT_RUN; no PATH, hook, service, logon, MCP or account configuration change |
| Maintenance | Primary release page showed v3.4.5 on 10 November 2026, short commit ee 73c04, and nearby 3.4.x releases; security policy supports latest release only | Evidence of current activity, not a support guarantee. Moving-main docs may be newer than that release; no full source commit was pinned or audited |

The upstream [architecture document](https://github.com/akitaonrails/ai-memory/blob/main/docs/ARCHITECTURE.md) describes ingestion, derived retrieval and optional automated maintenance. This note does not claim a complete security/code audit or that repository popularity establishes safety.

## 3. Privacy/security implications

The [security policy](https://github.com/akitaonrails/ai-memory/blob/main/SECURITY.md) describes a workstation service with plain local files/SQLite, capture spools and optional provider processing. Captured or recalled content can leave the machine when a cloud provider is configured; scrubbing is best effort. Project access is not per-page privacy. Stored content remains an instruction-injection risk. These observations support a restricted manual design here; they are not evidence that an installed service has been tested in this environment.

Project boundaries remain: scope `research/patent-to-pilot`; no credentials, protected test content, raw restricted patent text, private journals, automatic account/session capture, cross-project profile or global configuration. No source data was uploaded to inspect the public repository. Memory notes contain sanitized decisions and links/hashes to canonical evidence only.

## 4. Files and single sources of truth

| Purpose | Canonical file | Update rule |
|---|---|---|
| Find current work | [memory index](../../../../memory/research/patent-to-pilot/INDEX.md) | Keep short; link authoritative files rather than copy dynamic state |
| Programme scope | [MASTER-PLAN](../../../../MASTER-PLAN.md) | Owner changes study scope/order or contribution; record previous decision |
| Components/results | [INDEX-PLAN](../../../../INDEX-PLAN.md) | Every substantive completed/change/failure/blocker event |
| Active writer, jobs, limits | [HANDOFF](../../../../HANDOFF.md) and concise [CLAUDE](../../../../CLAUDE.md) checkpoint | Paired checkpoint on every trigger; one writer |
| Durable owner decisions | [DECISIONS](../../../../memory/research/patent-to-pilot/DECISIONS.md) | Add source/date/status and what it supersedes |
| Unresolved items | [OPEN-QUESTIONS](../../../../memory/research/patent-to-pilot/OPEN-QUESTIONS.md) | Update exact blocker, dependent branch and resolving evidence |
| Session outcomes | [SESSION-LOG](../../../../memory/research/patent-to-pilot/SESSION-LOG.md) | Append sanitized outcome/audit pointer on handoff/end |
| Reproducible evidence | `docs/healthtech/audits/<run-id>/` | Immutable receipts/manifests; new version for new evidence |

Both AGENTS.md and CLAUDE.md explicitly link the same memory entry and INDEX-PLAN. The actual filename is `CLAUDE.md`; no `CLUADE.md` existed, so no duplicate/conflicting entry point was created. HANDOFF also points to this common route. Both agents can read these ordinary files when permitted; they do **not** gain access to one another's private account memory.

## 5. Start, update and handoff procedure

1. Read AGENTS, CLAUDE active checkpoint, HANDOFF latest takeover, memory INDEX and INDEX-PLAN. Verify actual branch/HEAD/dirty state and current owner. Historical notes cannot grant authority.
2. Confirm prior writer stopped/transferred before editing. Check recorded jobs before restarting anything. Reserve no resource from a plan alone.
3. Follow links for only the selected work package. Treat evidence notes as historical data; current owner/runtime instructions govern. Recheck unsafe/stale factual assumptions against original receipt/source.
4. On completion/change/decision/failure/blocker, update the relevant INDEX row; on unchanged read-only work record what was verified. Add durable decision/open-question/log entry only as needed.
5. Update HANDOFF+CLAUDE together on that event, before background/>10 minute work, at least every 30 minutes active, and before pause/end. Include Bangkok timestamp, writer/state, last verified pushed base, actual remote verification limitations, dirty files, evidence/commands, jobs/monitoring, permissions, blockers and next 3–6 steps.
6. Once a package completes, update progress and next-actions pointers. Validate relative links, schema/status consistency and disclosure boundaries. Commit/push only when currently authorized; this session is no-push and records local-only state.

Supersede stale decisions explicitly rather than deleting negative experiments or historical protocols. Resolve conflicting summaries by returning to exact evidence and current owner instructions. Do not paste whole private artifacts into memory to make recall convenient.

## 6. Verification and limitations

This package validates that all three entry files resolve to the same INDEX-PLAN and memory INDEX, that required memory files exist and that local links/schema/JSON pass. It does **not** launch Codex/Claude CLI clients, prove automatic startup ingestion, test a memory server, synchronize accounts/computers or verify remote Git synchronization. The other agent must actually read the files. Cross-machine continuity requires a separately authorized secure publication/copy path.

If native ai-memory is desired later, first select a pinned release and inspect the exact installer/configuration diff, local-only storage/provider behavior, capture exclusions and background mutation/retention. Present a concrete narrow installation plan for approval at action time. This document grants no credential generation, persistent access, hooks, server installation or external transmission permission. The current useful deliverable works without those approvals.
