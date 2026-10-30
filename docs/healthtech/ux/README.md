# HealthTech UX documentation and Claude Code handoff

Status: **READY_FOR_REVIEW — documentation only**. Source snapshot inspected: `96c63b14a1a2df8e8f8b816edee0dff7feddc3d3`, 27 October 2026 UTC. This package contributes specifications to HT-W13/HT-W16/HT-W19; it does not complete HT-G3 or HT-G7.

## Start here

| Reader's job | Document |
|---|---|
| Understand users, assumptions and complete journeys | [01 — Personas and journeys](01_PERSONAS_JOURNEYS.md) |
| Implement and accept specific behavior | [02 — Story backlog](02_STORY_BACKLOG.md) |
| Build navigation, screens, bilingual copy and themes | [03 — Screens and design](03_SCREENS_DESIGN.md) |
| Connect real contracts and honest mock adapters | [04 — Integration, states and fixtures](04_INTEGRATION_STATES.md) |
| Execute bounded frontend work and demonstrate completion | [05 — Claude Code handoff](05_CLAUDE_HANDOFF.md) |
| Paste the bounded goal into Claude Code | [Claude starter prompt](CLAUDE_STARTER_PROMPT.md) |
| Load authored demonstration data | [UI fixtures](fixtures/ui-fixtures.json), [fixture schema](fixtures/ui-fixtures.schema.json) |
| Inspect checks and source fingerprints | [Verification receipt](verification.json), [validator](validate_docs.py) |

Read the root [GOAL](../../../GOAL.md), [PLAN](../../../PLAN.md), [README](../../../README.md) and [AGENTS](../../../AGENTS.md) first. These govern the new HealthTech track. Historical pharma/Transfer-or-Retest workflows are not the product described here. The current [progress](../progress.json) and [next actions](../../../memory/next-actions.md) remain owned by the control plane; this documentation task does not edit them.

## Package contract

Goal: give Claude a concrete, independently implementable no-code frontend specification for named public medical device/comparator → inspectable, editable evidence dossier → next information requests. Primary users are entrepreneurs and MedTech investor analysts; demand and workflow fit remain assumptions.

Permitted inputs: governing repository documents, current public-source contracts/modules/schemas, existing authored fixtures, and the supplied read-only audit. Outputs are authored Markdown, synthetic fixture JSON/schema and documentation validation evidence under `docs/healthtech/ux/` only. No UI, backend fix, branch, commit, push, provider call, deployment or outreach is performed by this package.

Acceptance: all story/screen/journey/state references resolve; local Markdown links resolve; fixture envelopes validate; embedded dossiers validate against actual Pydantic/JSON contracts and source-integrity checks; current capabilities and proposals are distinguished. Passing these checks is documentation engineering evidence. Screenshots, UI tests, human usability, business validation and scientific results are **NOT_RUN**.

Stopping condition: a coherent reviewed-by-author package plus verification receipt and actionable Claude prompt. Next actor: Claude implements the bounded frontend slice on its own branch after confirming actual repository state and isolated path ownership. No branch is created by this task.

## Evidence boundaries

The supplied audit is `C:\Users\User\Documents\Codex\2026-10-27\task-3\pepo-luna-readonly-audit-r1\AUDIT_TH.md`, inspected locally and fingerprinted in the receipt. It reported 269 clean tests passing and **CHANGES_REQUIRED**; this package does not repeat that suite. Findings include SciFact duplicate inflation, concurrent history lost updates, unenforced cumulative storage limits, edits omitted from Markdown export, and an invalid default SciFact revision. Exact backend/UI separation appears in document 04.

The three current public dossiers K190167/K163345/K121849 have empty patent input pools and zero candidates. They demonstrate public FDA field provenance, not device–patent recovery. Overall audited goals: HT-G0 contract done; HT-G1/2/3/5/6/7 partial; HT-G4 not run; HT-G8 deferred. Neither documentation nor frontend mock completion changes these statuses.

All `UX-*`, `J-*`, `US-*`, `SCR-*`, `CMP-*`, `ST-*`, `CAP-*` and `FX-*` identifiers below belong to this UX specification, not scientific task/result namespaces. G3/G7 shorthand always means **HT-G3/HT-G7**, not historical G03/G07.
