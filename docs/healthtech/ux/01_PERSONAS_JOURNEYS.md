# Personas, jobs and end-to-end journeys

The product prepares a traceable evidence dossier before a deeper technology, licensing or diligence discussion. The starting point is a **named public medical device or a comparator the user selects**. A user with an idea can save a brief and select a public comparator; idea-to-comparator recommendation is future work.

Authority: root [GOAL sections 1 and HT-G3/HT-G7](../../../GOAL.md), [PLAN sections 2/5/10](../../../PLAN.md). Screen details live in [03](03_SCREENS_DESIGN.md), testable stories in [02](02_STORY_BACKLOG.md), states/contracts in [04](04_INTEGRATION_STATES.md). All interactions in this document are target behavior unless explicitly identified as existing CLI behavior.

## Personas and jobs to be done

| Persona | Situation and job | Desired evidence/output | Product boundary |
|---|---|---|---|
| P-01 — MedTech entrepreneur, primary | Before a development or licensing discussion, organize what is known about a named comparator and the technical questions worth investigating | Device identity, dated public facts, patent shortlist with basis, feature gaps, editable TH/EN dossier and next requests | No feasibility, clinical suitability, FTO or approval prediction |
| P-02 — MedTech investor analyst, primary | Before deeper diligence, compare available evidence and identify questions requiring specialist or company follow-up | Provenance, unresolved associations, retrieval scope and costs, reusable export with version | No investment recommendation, return forecast or aggregate opportunity score |
| P-03 — Technology/RA collaborator, secondary | Check a specific factual or regulatory claim and explain its jurisdiction and date | Exact field/span, version/hash, distinction between 510(k) codes and approval claims, review notes | No automated regulatory opinion; no mandatory account or regulated role verification in prototype |
| P-04 — R&D/BD collaborator, secondary | Compare technical features and prepare an information request for an internal discussion | Side-by-side evidence rows, missing sources, questions that can be copied or exported | Draft preparation only; no automatic outreach |

Personas describe workflow roles, not identity, credentials, health status or validated customer segments. `ProjectBrief.audience` currently accepts entrepreneur/investor/researcher. P-03/P-04 are optional role tags in the proposed frontend view model; never send new audience enum values into the closed backend contract.

## Assumptions to validate

| ID | Working assumption/default | Evidence needed later; no claim made now |
|---|---|---|
| UX-A01 | Entrepreneurs and investor analysts will value a source-led dossier more than a search-hit list | Observe authorized users completing the public-case script; record corrections and time |
| UX-A02 | No-code defaults and progressive disclosure reduce avoidable setup work | Observe where users pause, open technical details or edit defaults |
| UX-A03 | Thai/English interface and editable annotations help local teams | Check comprehension in both languages with users; do not infer language from nationality |
| UX-A04 | A local-first, single-user prototype with explicit exports is useful before team services exist | Validate save/reopen and handoff tasks; no repeat-use or purchase evidence yet |
| UX-A05 | Formal themes with KMITL/ICT-inspired options satisfy the requested direction | Owner review of rendered UI later; inspiration is not official institutional branding |
| UX-A06 | Most reviews should be local decisions, not modal approvals | Measure interruption/correction burden; retain consequential ambiguity and external-action gates |

## Shared journey rules

Use one project shell with a persistent device identifier, dossier version, scope/cutoff, mode badge and save status. Let users open technical details without requiring them to understand query syntax. Optional persona selection defaults to entrepreneur and is reversible. Suggested project title uses device name + identifier; a user can edit it without changing identity. Default jurisdiction comes from the selected source (US for current FDA records); this is source jurisdiction, not the user's country. Evidence cutoff must be explicit and no earlier than included source dates. Default offline limits follow `AcquisitionBudget` (3 calls/60 returned occurrences), subject to the imported run's actual limits. A historical run's limits remain immutable.

Never request an email, phone, patient record, financial portfolio or private technical document for a public prototype. No mandatory consent wall for inspecting supplied public data. Display a short scope/storage note at import and first local save; enable optional analytics only through a separately implemented opt-in capability. A future outbound disclosure, paid run or real sharing operation needs its own applicable authorization; ordinary filters, edits, source inspection and local exports do not need repeated approvals.

Every claim view separates sourced facts, reported associations, system inference and unresolved/unjudged. Patent relationship status and integrity-check status are separate dimensions. A source match does not verify semantic support. Users may annotate a disputed association, but cannot turn a candidate into a disclosed link by clicking “confirm.”

### J-01 — Find and disambiguate a named device

**Actor/goal:** P-01/P-02 selects the correct public comparator before creating a project. **Entry:** new-project action, known identifier link, or an imported dossier needing identity confirmation. **Screens:** SCR-01 → SCR-02 → SCR-03. **Stories:** US-01–US-03.

| Step | User action | System behavior/default | Decision and lineage |
|---|---|---|---|
| 1 | Enter device name, manufacturer or exact public identifier | Show matching records from the available local catalog with its snapshot label; do not suggest global live search if unavailable | Keep entered raw string; no canonical ID before a record is chosen |
| 2 | Compare record cards | Display device name, identifier, applicant if present, source jurisdiction/type/date and exact source link | Same name across records is ambiguity, not deduplication |
| 3 | Select one record | Pin source ID/revision/hash and canonical device ID; keep raw query separately | Selection is the one consequential identity decision; no extra confirmation modal |
| 4 | Continue, or save an idea-only brief | Prefill editable brief; idea-only draft cannot run acquisition until comparator selected | No inferred match or invented identifier |

Empty catalog: explain supported import/demo choices (ST-01). No match: retain the raw query and suggest exact identifier or supported file import; do not fabricate recommendations. Loading local catalog uses ST-02 without fabricated percentages. If a record lacks applicant/date, show “not supplied,” preserving other fields. Invalid import enters ST-06 with the offending field. Cancelling selection restores the previous chosen record; changing a comparator after a dossier exists forks a proposed new project/run, preserving the original history. Resume restores the saved draft input and selection, not a guessed record.

### J-02 — Create a project and import permitted public sources

**Actor/goal:** P-01/P-02 defines the questions and sources in a bounded project. **Entry:** J-01 selection or open supported file. **Screens:** SCR-03/SCR-04. **Stories:** US-04–US-06, US-25.

| Step | User action | System behavior/default | Decision and lineage |
|---|---|---|---|
| 1 | Set objective; optionally choose role/language/theme | Prefill a neutral objective and suggested title, use current locale and formal-light theme unless preference saved | Map objective/audience/language/theme into `ProjectBrief`; UI title stays separate |
| 2 | Add features/questions in plain language | Allow blank optional lists, trim/reject blank items, retain user-authored text | Never generate queries from evaluator labels |
| 3 | Review jurisdiction/cutoff and local count cap | Explain values inline; advanced details show corpus scope and policy | Store a new `DeviceQuery`; do not silently mutate a completed run |
| 4 | Import supported JSON package/source snapshot | Parse as data, schema-check, verify hash/reference/cutoff/synthetic boundaries, preview accepted/rejected items before replacing anything | Source URI/license note is not proof of full reuse rights; unresolved intended-use rights leave affected source unavailable for acquisition |
| 5 | Save draft or open available dossier | Save in selected actual persistence mode with a truthful receipt | Keep imported original, normalized representation and local notes distinct |

Prototype file support is versioned HealthTech JSON and the authored UI fixture envelope. URL entry can save a reference/next request; it does not fetch arbitrary pages. PDF/OCR/drag-any-file and patient/private data import are unavailable. A `.env` or unsupported file is rejected by file type without printing its content. Mixed public/synthetic inputs cannot be combined as a public case. Fix one rejected source and retry it; do not erase accepted draft content. Cancel import leaves original project intact. Reload before save restores only the latest acknowledged local draft. If storage is denied/full (ST-07/ST-09), keep the draft in memory and offer a clearly labelled recovery JSON download.

### J-03 — Understand retrieval progress, limits and partial results

**Actor/goal:** P-01/P-02 understands what ran, what remains and what it cost. **Entry:** run receipt import or a future capability-backed start action. **Screens:** SCR-05 → SCR-06. **Stories:** US-07–US-10, US-26.

Current CLI is synchronous and produces output files after execution; it has no HTTP job/events/cancel/resume service. The first frontend can replay authored progress as **simulation** or inspect imported completed receipts. Never present a timer/replay as a running real search.

| Step | User action | System behavior/default | Decision and lineage |
|---|---|---|---|
| 1 | Open run details | Show imported/simulated/live capability mode, policy label, permitted sources, immutable caps | Raw run/config/input hashes are in Details; plain explanation leads |
| 2 | Read stages/events | Show returned occurrences separately from unique documents, actual calls, completed/failed queries and available evidence | Never equate candidate count with disclosed links or completeness |
| 3 | Open partial dossier while a source fails | Preserve source-specific error, completed work and gap; do not label missing source zero matches | Retry only through an implemented adapter with attempts/cost receipt |
| 4 | Cancel or later resume where supported | Pending cancellation remains pending until acknowledged; preserve all attempts and completed artifacts | UI cannot claim cancellation/refund; unsupported controls are absent with an explanation |
| 5 | Inspect end reason | Translate budget exhaustion, fixed schedule complete, unavailable source and run failure separately | Completion of a bounded run is not “all evidence found” |

Budget panel distinguishes offline count budget from money. Current imported manifest may truthfully say zero paid cost for that recorded offline run; unavailable monetary fields show “not recorded.” Future actual/estimated/reserved/unknown billing must be separate, and an unknown settlement stays unknown. Do not display trial credits, savings, billing zero or remaining dollars without ledger evidence. Pause/resume of a UI screen preserves inspection context only; a new run has a new ID and references its previous run rather than rewriting history. ST-03/ST-04/ST-05/ST-10/ST-14 cover partial, blocked, failed, cancelled and stale/simulation states.

### J-04 — Compare patent candidates and feature evidence

**Actor/goal:** P-01/P-02/P-04 compares why documents were retrieved and which features have evidence. **Entry:** dossier overview or deep link to row. **Screens:** SCR-06/SCR-07. **Stories:** US-11–US-13.

Show source facts first, candidate shortlist second, feature–evidence table and unresolved questions next. The current FDA dossiers have no patent pool: the empty message must say the imported run had no patent corpus and cannot establish absence of patents. If a permitted corpus exists and returns no candidates, say that no candidates were returned under that scope/policy/budget. Unknown corpus scope cannot use either stronger statement.

Select up to three documents or evidence rows for a comparison panel; on mobile, use stacked sections with identical headings. Keep source revision, canonical document ID/kind and jurisdiction visible. Sorting uses the named score's own direction; never sum unrelated scores or label ranking as probability. Query filters are local view state and do not re-run acquisition. Missing features remain missing, not score zero. Document kinds and countries remain distinct; family grouping is enabled only with sourced mapping. Compare mode preserves selected IDs across filters and explicitly identifies selections hidden by the current filter. Remove/cancel returns to the original row/focus. Exported comparisons cite the dossier version and selection, not a new factual relationship.

### J-05 — Inspect exact evidence and mark uncertainty

**Actor/goal:** P-03/P-02 checks the precise source basis and records consequential ambiguity. **Entry:** evidence citation, candidate basis or unresolved item. **Screens:** SCR-07 → SCR-08; returns to original row. **Stories:** US-14–US-16.

Open a side panel on desktop and full page on narrow screens. Show statement, basis/kind, integrity-check wording, raw/canonical IDs where applicable, source revision/hash, source date meaning and locator. Structured sources show the typed field/value; text sources show exact `chars:start:end` range (end exclusive, Python Unicode code-point offsets). Keep original source language alongside a user annotation; changing UI locale never rewrites the quote. Native browser UTF-16 offsets must not silently select the wrong Thai/emoji range.

An exact span/field check earns “source text/field matched,” not “claim verified.” Regulatory decision dates and snapshot dates are separate. Current `SourcePayload.source_date` for the FDA normalizer is its supplied retrieval date; do not relabel it as publication date. A dead external link still allows inspecting an available pinned payload. A missing local payload/locator/hash mismatch uses ST-12, retains the citation and explains what cannot be checked. It cannot create a green verification badge.

User annotations choose needs clarification / disputed basis / reviewed note and optional explanation in the proposed overlay. These notes do not mutate source payload/hash or system verification. Draft a next-information question from an ambiguity, with manual editing. Do not send it. Cancelling an annotation leaves source/evidence unchanged; an unsaved note triggers a discard/save choice only on destructive navigation. Resume opens the same version and cited row; a newer version is offered explicitly rather than silently replacing the basis.

### J-06 — Edit, autosave, version and reopen

**Actor/goal:** P-01/P-02 preserves work and can explain what changed. **Entry:** any editable dossier field or project history. **Screens:** SCR-06/SCR-09. **Stories:** US-17–US-20.

Edits apply to user annotations/section drafts, not source facts. Each editor displays its origin: imported/generated text, user note, or proposed inference. Default autosave batches local changes after a short idle period (800 ms target), acknowledges the actual storage scope and keeps a visible “unsaved” state until commit. Explicit Save invokes the same path. Every committed snapshot has parent/version/hash; the browser prototype's history is a **local UX snapshot**, separate from `DossierVersion.version` unless an adapter explicitly validates/commits a backend dossier version.

At present, CLI history has a concurrent-write race. Do not wire optimistic server-save success into it. Build a transactional browser store if supported, or stay in memory with recovery download. A second tab editing an old base must receive ST-08; keep local text, show base/theirs/yours and offer copy/reapply or a new local branch. No silent last-writer-wins or automatic “semantic merge.” Corrupt/gapped imported backend history is quarantined read-only with recovery export (ST-13). Restoring an older version creates a new local snapshot and preserves the old chain. Acknowledged local save should survive close/reopen in the same browser profile; it makes no promise about device sync or browser eviction. Warn about pending unsaved changes only when leaving would lose them.

### J-07 — Export Thai/English dossier and prepare next requests

**Actor/goal:** P-01/P-02/P-04 carries the dossier into a real discussion. **Entry:** overview, history, or unresolved row. **Screens:** SCR-10/SCR-11. **Stories:** US-21–US-23.

Choose explicit snapshot/version and UI/report language. Default export includes facts, candidates with association status, exact provenance, unresolved items, next requests and separately labelled user edits. Preserve quotes/IDs in their source language. TH/EN translates authored headings and static explanatory copy; it does not promise machine translation of scientific prose. Preview content before downloading and show a truthful result only after generation/download initiation. A download initiation cannot prove the user saved the file on disk.

Current backend Markdown export omits `user_edits`; disable the claim “complete edited dossier” for that exporter. An independent frontend renderer may include edits, with a distinct exporter ID, current tests and a preview; otherwise offer lossless recovery JSON plus a conspicuous missing-edits message. Do not hide the omission in a success toast. PDF/DOCX export is future capability. Next requests are local editable drafts tied to evidence/unresolved IDs where present, with optional intended recipient role and priority; do not require actual email or send automatically. Cancel export does not modify saved state; retry only the renderer. Reopen shows the exact selected version and exporter limitations.

### J-08 — Hand off to collaborators within available capability

**Actor/goal:** P-01 shares an evidence package for P-03/P-04 to inspect. **Entry:** export/next requests. **Screens:** SCR-10/SCR-11. **Stories:** US-24.

Current route is a local download and user-controlled transfer outside the app. Show “download package,” not “invite team” or “shared successfully.” No mandatory email/contact collection. A proposed team service would need actual authentication, access controls, server persistence/version conflicts, audit/retention controls and revocation before invite/comments controls appear. Preserve a proposed collaboration seam without implementing fictitious permissions. Importing another person's edited package creates a new local copy unless a verified common ancestry and merge flow exist. No hidden shared workspace or role authority is inferred from filenames.

### J-09 — Recover from errors without losing useful work

**Actor/goal:** any persona understands a local failure and continues the unaffected work. **Entry:** inline error banner or interrupted import/save/run/export. **Screens:** relevant screen, with SCR-09/SCR-10 recovery. **Stories:** US-09, US-18–US-22, US-25–US-28.

Every error names the failed action, affected data/source/version, outcome (not executed/pending/uncertain), preserved work and one next action. Validation errors stay next to the field and in a keyboard-focusable summary. Background failures do not steal focus. A retry never clears the prior attempt or silently starts paid work. If outcome is uncertain, reconcile status before another mutation. Use ST-06 for invalid input, ST-07 for denied storage, ST-08 for conflicts, ST-09 for storage limits, ST-11 for unknown cost, ST-12 for bad provenance and ST-13 for corrupt history. The user can always inspect valid preserved sources, copy notes and export a truthful recovery file where the browser permits it. Dismiss a banner without dismissing the underlying unresolved issue.

## Later validation script — prepared, not executed

Use an authorized target user and a public source package: choose a named record; explain why it is the selected comparator; identify one fact and open its exact field; explain candidate versus disclosed link; recognize that zero current candidates came from an empty corpus; add a question and note; save/reopen; export TH/EN and locate the note and source; recover from a simulated conflict. Record task completion, mistaken interpretations, time to first inspected source, correction count and review interruptions. No target success rate, market evidence or willingness-to-pay result is asserted. Recruitment/outreach and recording require separate scope; none occurs in this documentation task.
