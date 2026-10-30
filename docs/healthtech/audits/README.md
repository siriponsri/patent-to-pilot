# HealthTech audit records — project-local convention

Owner requested this convention on 2026-10-28. It applies to future Patent-to-Pilot HealthTech task audits and continuation evidence, subject to platform/system/developer/runtime rules, explicit owner authority and applicable AGENTS instructions. It does not grant permissions to acquire, publish or disclose data.

## Canonical location

Use `docs/healthtech/audits/<run-id>/` for each task's audit report, receipt, audit manifest, verification summary and continuation/next-action note. Use a unique, descriptive run ID, for example `luna-patent-dossiers-<UTC timestamp>`. Do not use a Codex task/temp directory as the sole source of an audit or a required continuation input.

Persist at least an index/README, report or receipt, machine-readable verification/manifest, and a concise `NEXT_ACTIONS.md` when work remains. They may be combined where that keeps the package smaller. Record start/end code revisions and tree state, tested candidate/source hashes, exact commands/outcomes, evidence paths, implemented/mocked/NOT_RUN boundaries, limitations, resource use and scoped blockers. Root `memory/next-actions.md` and progress records may retain their established summary/pointer role; link the canonical run record rather than duplicating a full audit in several places.

## Evidence and privacy

Tests, scratch checkouts and temporary files may remain temporary. Before cleanup or handoff, persist the small sanitized reproduction inputs/results and source/config hashes needed to understand the finding. Keep large raw corpora, restricted source pages, weights, evaluator-only relations and private journals in permitted local storage under the existing policy; the audit folder records provenance, counts, hashes and stable references. Ordinary operational configs/data stores can stay in established repo locations. Never copy credentials, `.env`, private paths/content, patient data or raw restricted payloads into an audit record.

Local repo storage does not automatically authorize public Git redistribution. Inspect every staged audit artifact for secrets/privacy/data and code licenses; stage only permitted authored evidence and summaries. Preserve unknown rights, missing provenance and failed/uncertain outcomes honestly. A filename or passing test count is not goal completion, legal permission, publication readiness, clinical suitability or FTO evidence.

## Versioning

Keep historical receipts immutable. Write a new run/revalidation record when behavior or evidence changes and link its parent/superseded record. A documentation-only HEAD change does not require repeating a model run/full suite when relevant source hashes are unchanged; record that relationship. Existing historical evidence directories are not mass-migrated by this convention.

Current preserved follow-up: [pepo-followup-20261028-1ce0443](pepo-followup-20261028-1ce0443/README.md). Next bounded implementation handoff: [patent-linked dossiers Goal](../LUNA_PATENT_LINKED_DOSSIERS_GOAL.md).
