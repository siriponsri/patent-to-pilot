# Patent-to-Pilot HealthTech — execution instructions

Read root [GOAL.md](GOAL.md) sections 0–4, the selected HT-W in [PLAN.md](PLAN.md), [progress](docs/healthtech/progress.json) and [next actions](memory/next-actions.md). Root GOAL/PLAN define current HealthTech scope; this file controls execution. Current owner directions and runtime permissions take precedence. Read only relevant sources and applicable `.agents/skills` instructions when present.

## Current scope and task contract

- Start from a named public medical device or user-selected comparator. Produce an inspectable evidence dossier for entrepreneurs/investor analysts; idea-to-comparator discovery is future work.
- Main research candidate: device–patent known-link recovery under incomplete judgments. SciFact is a separate evidence-verification component. Pharma/Biologics are later branches.
- Use HT-G/HT-W/HT-B/HT-T namespaces. Historical G01–G22 and B0–B4 results/protocols retain their original meanings; they are not HealthTech results. See [migration](docs/healthtech/MIGRATION.md).
- Choose a bounded package: goal, permitted inputs, outputs, acceptance, targeted checks, stopping condition and next step. Own routine implementation/debugging within authorization. A local blocker stops its dependent branch only.
- The owner requested a capable coding/research model. The label `gpt 5.6 luna max` in older notes is not a verified provider ID. Do not silently configure accounts or use executor labels as experiment model IDs.
- Do not spawn agents by default. Delegate only under explicit current authorization and with isolated writers; one control plane owns execution.

## Evidence and software invariants

- Preserve raw and canonical IDs, kind codes, source revision/hash, jurisdiction, date and exact locator. Do not merge patent families without a sourced mapping.
- `retrieved_candidate` is not `disclosed_link`. Independent source provenance is needed for a disclosed link; benchmark gold without disclosure URLs cannot serve as a product citation.
- Literal quote/field matches establish source integrity only. The legacy extractor's `SUPPORTED` means a literal match in that slice; it does not establish semantic entailment, clinical suitability, approval, FTO, patent validity or investment merit.
- Runtime source/query/action/dossier inputs exclude evaluator labels, gold-derived queries and hidden oracles. `evaluation/healthtech` may read labels; `healthtech/engine.py` does not.
- Freeze eligible queries, universe, cohort, cutoffs, grouping, failure/retry rules and endpoints before a final study. Include failed queries and all attempts/costs. Unlisted links are unjudged, never automatically negative.
- Known-link recall is not exhaustive recall or an established lower bound of it. Use shared-patent/family groups and appropriate group-level uncertainty; seed repeats are not independent samples.
- Bridge pack audit: 672 exported pairs/79 devices vs 585 completeness-qualified pairs/74 devices. These are supplied audit findings, not a local repeat. Do not treat `is_valid` as relevance or `kg_linked` as independent gold. Clarify data rights and cohort before the affected study.
- Keep strong fixed hybrid, fixed multi-query, simple adaptive and bounded LLM controls. Current runnable methods are offline lexical HT-B0b and fixed HT-B2 only; do not relabel them adaptive or claim scientific benefit.

## Permissions, privacy and release

- Current owner task authorizes local migration, recoverable cleanup and a tested commit/push to `main`. This is not authorization for paid inference, deployment, clinical/human studies or external outreach.
- Never read/print `.env` or credentials, change ACL/auth/global hooks/tools, bypass access controls or touch unrelated projects. Use filesystem/shell for this task; browser/native UI belongs to concurrent AWS work.
- Preserve provider identity, durable attempts, reservations, actual/unknown billing and existing budget journals. An offline count budget is not money. Future paid use must reuse the existing explicit adapter and ledger with conservative reservation and current exact authorization; never reset it for more attempts.
- Scope memory to `research/patent-to-pilot`. No session-store access, automatic capture, cross-project memory or global configuration changes.
- Keep original input pack unchanged. Third-party paper/data/code rights are separate. Publish source links/IDs/hashes and authored fixtures; do not stage paper PDFs, raw corpora, evaluator-only material or private local files.
- Delete obsolete tracked files only after checking remote/history recovery; never reset/clean, force-push, prune/gc or delete `.git` packs. Do not destroy dirty-only changes, irreplaceable untracked data or sole-copy evidence. Keep exact recovery references and measured bytes for cleanup.
- Public repository visibility does not grant a code or dataset license. Do not invent one.

## Working and verification

- Follow applicable global RTK prefix guidance; `rtk proxy` is available. Do not run `rtk init` or alter hooks to silence a notice. Check [tooling](docs/TOOLING_REGISTRY.md) before unfamiliar tooling.
- Relevant user skills: `research-synthesis`, `document-ingestion`, `technical-writing`; read their SKILL.md before use. Thai deliverables follow `kien-thai` when available. Presence of an installation file does not prove live integration.
- Test changed behavior with hand-computable positive/negative fixtures. Documentation needs link/schema checks. Run provider regressions when integrating with shared components; do not rerun paid or old scientific benchmarks as a test substitute.
- Report actual commands and outcomes, implemented/mocked/planned/NOT_RUN boundaries, exact blockers and next action. Update progress and next-actions once per completed package. Engineering PASS never means publication readiness.


## Project-local HealthTech audit records

- For future HealthTech task audits, keep all audit reports, receipts, audit manifests, verification summaries and continuation/next-action notes needed to resume work in `docs/healthtech/audits/<run-id>/`. Follow [the audit convention](docs/healthtech/audits/README.md); do not leave a Codex or temp directory as their sole source. Existing progress and memory entry points may summarize and link to the canonical run record.
- Tests and scratch artifacts may use temporary directories, but persist key sanitized reproduction evidence, command outcomes and source/config hashes in the run folder before handoff or cleanup. Preserve historical receipts; do not mass-migrate or overwrite them.
- Large raw/restricted corpora, source pages, model weights, evaluator-only relations and private journals stay in permitted local storage with provenance/hashes/references in the audit manifest. Local-repo storage does not authorize public Git redistribution; never copy credentials, private paths/content or restricted raw data into staged audit files.
- This is a project-local evidence-location rule only. It does not override higher-priority instructions, owner/runtime authority, data rights, privacy rules or scoped writer ownership, and it does not grant new acquisition/publishing permissions.
