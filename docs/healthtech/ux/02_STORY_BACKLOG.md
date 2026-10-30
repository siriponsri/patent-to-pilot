# User story backlog and acceptance

Implement stories against the [journeys](01_PERSONAS_JOURNEYS.md), [screens](03_SCREENS_DESIGN.md) and [state/adapter contracts](04_INTEGRATION_STATES.md). These are requirements, not a record of implemented features. P0 is necessary for an honest inspect/edit/reopen/export frontend slice; P1 completes richer preparation and resilience; P2 is a proposed extension. Dependencies are story IDs, not permission gates.

“Demo” below always means visibly labelled authored synthetic data. Existing public dossier import is a separate mode and must retain its evidence limitations. Every story maps to HT-G3/HT-G7 and selected HT-W work packages; it does not claim those goals are closed.

## Delivery sequence

| Slice | Stories | Outcome | Blocking boundary |
|---|---|---|---|
| A — Understand and inspect | US-01–US-06, US-11–US-16, US-25, US-27 | Named-device project, honest import, overview/comparison/source viewer | Works from authored fixtures and validated imported files; no G1/G2 study dependency |
| B — Preserve and hand off | US-17–US-23, US-26, US-28 | Local autosave/conflicts/history, edits included in own export, questions and resilience | Backend history/Markdown defects do not stop browser-local implementation |
| C — Explain acquisition | US-07–US-10 | Read imported receipts and simulated states; explicit future adapter seam | Real start/cancel/resume unavailable until a service exists |
| D — Team extension | US-24 | Local package handoff now; service-backed collaboration later | Invite/sync remains unavailable |

### US-01 — Start without registration

**Priority:** P0. **Persona/job:** P-01/P-02 wants to inspect the workflow without providing unrelated personal data. **Journey/screens:** J-01, SCR-01. **Depends:** none. **Map:** HT-G3/HT-G7; HT-W13/HT-W16.

- **Given** no saved project, **when** the app opens, **then** it offers named-device setup, supported file import and labelled demo, with locale/theme switch and no email wall.
- **Given** local data use, **when** storage information is opened, **then** the actual storage mode, scope and recovery path are explained without claiming cloud backup.
- **Given** a failed catalog load, **when** the user returns home, **then** importing a valid file remains usable (ST-01/ST-05).

### US-02 — Select an unambiguous comparator

**Priority:** P0. **Persona/job:** P-01/P-02 distinguishes similarly named records. **Journey/screens:** J-01, SCR-02. **Depends:** US-01. **Map:** HT-G3/HT-G7; HT-W02/HT-W05/HT-W13.

- **Given** two local records with similar names, **when** results appear, **then** identifier, source type, jurisdiction, applicant if supplied and snapshot date distinguish them.
- **Given** an entered raw string, **when** one record is selected, **then** canonical ID/source revision/hash are pinned and the raw input remains available.
- **Given** no matching record, **when** search finishes, **then** the input remains and exact-ID/import options are offered without an invented recommendation.

### US-03 — Keep an idea-only brief without pretending to match

**Priority:** P1. **Persona/job:** P-01 records a question before choosing a comparator. **Journey/screens:** J-01, SCR-03. **Depends:** US-02. **Map:** HT-G3/HT-G7; HT-W13.

- **Given** an idea and no named comparator, **when** the draft is saved, **then** it is explicitly incomplete and cannot be serialized as a valid `DeviceQuery`.
- **Given** that draft, **when** acquisition is attempted, **then** the missing comparator is explained inline and the draft text is preserved.

### US-04 — Create a bounded plain-language project

**Priority:** P0. **Persona/job:** P-01/P-02 defines purpose, features and questions without query syntax. **Journey/screens:** J-02, SCR-03. **Depends:** US-02. **Map:** HT-G3/HT-G7; HT-W02/HT-W13.

- **Given** a selected public record, **when** brief setup opens, **then** source jurisdiction, explicit cutoff and actual offline count defaults are visible and editable before a new run.
- **Given** optional features/questions, **when** blank entries are added, **then** blank items are rejected without erasing other fields; empty lists remain allowed.
- **Given** an imported completed run, **when** setup changes, **then** changes create a new draft, preserving the original query/configuration.

### US-05 — Import a permitted package safely

**Priority:** P0. **Persona/job:** P-02 brings existing evidence into inspection. **Journey/screens:** J-02/J-09, SCR-04. **Depends:** US-04. **Map:** HT-G3/HT-G7; HT-W02/HT-W12/HT-W13.

- **Given** supported versioned JSON, **when** preview validates it, **then** schema, references, hashes, source dates and synthetic/public mode are checked before creating a project copy.
- **Given** mismatched hash, dangling source or source newer than cutoff, **when** validation fails, **then** field/source-specific errors explain rejection; the current project remains unchanged (ST-06/ST-12).
- **Given** a private/sensitive or unsupported file, **when** selected, **then** the prototype rejects the unsupported input and does not log its contents. URL entry alone never implies fetched evidence.

### US-06 — See exactly which sources are usable

**Priority:** P0. **Persona/job:** P-03 understands provenance/rights gaps. **Journey/screens:** J-02, SCR-04/SCR-06. **Depends:** US-05. **Map:** HT-G3/HT-G7; HT-W05/HT-W12/HT-W13.

- **Given** a source with license note and unknown intended-use rights, **when** listed, **then** the note and unresolved status are visible; the UI does not label it universally licensed.
- **Given** one unavailable source, **when** the remaining dossier is inspected, **then** valid sources remain usable and the missing one appears in unresolved items.
- **Given** public data and synthetic fixture data, **when** a merge is attempted as public evidence, **then** it is refused or saved as a separate labelled demo project.

### US-07 — Start only a supported acquisition mode

**Priority:** P0 for capability gating; real start deferred. **Persona/job:** P-01 understands what will execute. **Journey/screens:** J-03, SCR-05. **Depends:** US-04/US-06/US-26. **Map:** HT-G3/HT-G7; HT-W10/HT-W13.

- **Given** a file/demo adapter, **when** SCR-05 opens, **then** it offers inspect receipt or simulate, and never an active real Search button.
- **Given** a future service capability, **when** start is enabled, **then** declared sources, caps, policy, mode and returned run ID are shown; a failed/uncertain dispatch cannot create a fake running receipt.
- **Given** current `api.py`, **when** inspected, **then** the UI labels it dry-run/mock seam, not HTTP service or live controller.

### US-08 — Read progress and truthful costs

**Priority:** P0. **Persona/job:** P-02 sees completed/failed work and budget basis. **Journey/screens:** J-03, SCR-05. **Depends:** US-07. **Map:** HT-G3/HT-G7; HT-W10/HT-W13/HT-W19.

- **Given** actual imported events, **when** summarized, **then** calls, returned occurrences, unique candidates, failures and stop reason agree with the run data and units.
- **Given** only a synchronous completed output, **when** viewed, **then** no fabricated historic stage timestamps or live percentage appears.
- **Given** unknown billing, **when** costs render, **then** they remain “not recorded”/“pending reconciliation” (ST-11), while the recorded zero-paid offline run may display its scoped zero.

### US-09 — Continue from a partial/source failure

**Priority:** P0. **Persona/job:** P-01 keeps useful evidence after a failed source. **Journey/screens:** J-03/J-09, SCR-05/SCR-06. **Depends:** US-08. **Map:** HT-G3/HT-G7; HT-W10/HT-W12/HT-W13.

- **Given** usable facts and a failed patent source, **when** a partial dossier opens, **then** facts remain inspectable and the failed source remains unresolved, without “zero patents” inference (ST-03).
- **Given** a retry option without supporting adapter capability, **when** the error renders, **then** instructions/import alternatives replace the action.
- **Given** supported retry, **when** retried, **then** it appends an attempt and preserves earlier costs/outcomes; it does not reset a ledger.

### US-10 — Cancel/resume with acknowledgement

**Priority:** P1; simulated tests now, service behavior proposed. **Persona/job:** P-01 stops work without losing completed artifacts. **Journey/screens:** J-03, SCR-05. **Depends:** US-07/US-08. **Map:** HT-G3/HT-G7; HT-W10/HT-W13/HT-W19.

- **Given** unsupported cancellation, **when** inspecting CLI output, **then** no cancel/resume network control appears.
- **Given** a simulated/service cancel request, **when** awaiting acknowledgement, **then** status is pending; after acknowledgement it becomes ST-10 and preserves events/results.
- **Given** an uncertain response, **when** reopening, **then** state is reconciled before resubmitting; a new run references its predecessor rather than reusing its costs/identity.

### US-11 — Read the dossier overview honestly

**Priority:** P0. **Persona/job:** P-01/P-02 identifies evidence and gaps quickly. **Journey/screens:** J-04, SCR-06. **Depends:** US-05/US-06. **Map:** HT-G3/HT-G7; HT-W12/HT-W13.

- **Given** a dossier, **when** overview renders, **then** it shows pinned device, version, mode, cutoff, facts, candidates, unresolved items and next requests.
- **Given** current public FDA input `patents=[]`, **when** candidate count is zero, **then** text explains “no patent corpus in this imported run”; it makes no absence/coverage claim.
- **Given** unknown candidate total or unsupported section, **when** summarized, **then** it displays unknown/unavailable rather than numeric zero or demo substitutions.

### US-12 — Compare candidates without a misleading score

**Priority:** P1. **Persona/job:** P-02/P-04 compares candidate basis. **Journey/screens:** J-04, SCR-07. **Depends:** US-11. **Map:** HT-G3/HT-G7; HT-W02/HT-W12/HT-W13.

- **Given** two candidates, **when** compared, **then** raw/canonical IDs, kinds, source revisions, association states and named scores appear side by side or stacked accessibly.
- **Given** an unsourced family mapping or different score scales, **when** grouping/sorting is requested, **then** the app preserves documents and score names; it does not invent a family merge/probability.
- **Given** a filter hides a selected document, **when** comparison remains open, **then** the selection is retained with a “hidden by filter” explanation.

### US-13 — Link features to evidence and missing information

**Priority:** P0. **Persona/job:** P-01/P-04 sees which questions have source basis. **Journey/screens:** J-04, SCR-07. **Depends:** US-11. **Map:** HT-G3/HT-G7; HT-W12/HT-W13.

- **Given** feature rows with evidence, **when** expanded, **then** each supporting item opens the exact referenced version/locator.
- **Given** a feature without mapped evidence, **when** rendered, **then** it is unresolved, not contradicted or scored zero; mapping annotations remain separate from imported evidence.
- **Given** only the current contract's evidence list, **when** no feature links exist, **then** source evidence remains visible and the user may author local links without claiming a backend-generated feature map.

### US-14 — Inspect exact provenance

**Priority:** P0. **Persona/job:** P-03 checks a source instead of trusting a badge. **Journey/screens:** J-05, SCR-08. **Depends:** US-11. **Map:** HT-G3/HT-G7; HT-W02/HT-W12/HT-W13.

- **Given** a structured field or span, **when** opened, **then** typed value/original quote, locator, source ID/revision/hash, jurisdiction, available dates and URI appear.
- **Given** Thai/emoji text, **when** `chars:start:end` is applied, **then** Python code-point offsets select the exact span; UTF-16 indexing cannot shift it.
- **Given** missing payload, invalid locator or hash mismatch, **when** opened, **then** ST-12 prevents a verified badge and preserves the citation for recovery.

### US-15 — Understand relationship, inference and integrity separately

**Priority:** P0. **Persona/job:** P-02 avoids mistaking retrieval for a disclosure/legal result. **Journey/screens:** J-04/J-05, SCR-06/SCR-07/SCR-08. **Depends:** US-14. **Map:** HT-G3/HT-G7; HT-W02/HT-W12/HT-W13.

- **Given** `retrieved_candidate` plus an exact text match, **when** shown, **then** badges say candidate and source text matched; neither says disclosed/clinically suitable/FTO clear.
- **Given** `disclosed_link`, **when** rendered, **then** independent source-backed `patent_disclosure` evidence is navigable; absent basis invalidates the imported relationship.
- **Given** reported experiment, system inference or unjudged association, **when** rendered, **then** each retains its distinct basis; missing judgments never become negatives.

### US-16 — Record a consequential ambiguity

**Priority:** P0. **Persona/job:** P-03/P-02 annotates uncertainty without rewriting facts. **Journey/screens:** J-05, SCR-07/SCR-08/SCR-11. **Depends:** US-14/US-15. **Map:** HT-G3/HT-G7; HT-W12/HT-W13.

- **Given** a questionable association, **when** a note is saved, **then** the note's target/version/basis stay separate from source payload and verification status.
- **Given** a user marking “reviewed,” **when** saved, **then** this means user review only and cannot promote a candidate to disclosed link.
- **Given** an ambiguity, **when** converted to a next request, **then** an editable local question is created with references and nothing is sent.

### US-17 — Autosave a local draft truthfully

**Priority:** P0. **Persona/job:** P-01 preserves edits with little interruption. **Journey/screens:** J-06, SCR-06/SCR-09. **Depends:** US-11/US-26. **Map:** HT-G3/HT-G7; HT-W13/HT-W19.

- **Given** editable user notes, **when** idle autosave commits, **then** “saved in this browser” appears only after the actual storage transaction acknowledgement; before it, notes are unsaved/saving.
- **Given** memory-only mode or storage failure, **when** Save runs, **then** it preserves text and offers recovery download rather than “saved.”
- **Given** autosave, **when** multiple keystrokes arrive, **then** they batch into a local snapshot; they do not imply backend versions on every keypress.

### US-18 — Resolve stale-version and concurrent-tab conflicts

**Priority:** P0. **Persona/job:** P-02 keeps both people's/tab's changes. **Journey/screens:** J-06/J-09, SCR-09. **Depends:** US-17. **Map:** HT-G3/HT-G7; HT-W13/HT-W19.

- **Given** two writers on the same acknowledged local base, **when** each commits a distinct edit, **then** one wins and the stale write enters ST-08; neither falsely reports both changes saved.
- **Given** conflict, **when** displayed, **then** base/theirs/yours remain copyable and the user can reapply changes or save a separate local copy.
- **Given** audited CLI history, **when** an adapter lacks safe expected-version commit, **then** it cannot advertise reliable concurrent backend persistence.

### US-19 — Reopen, inspect and restore versions

**Priority:** P0. **Persona/job:** P-01 can return to acknowledged work. **Journey/screens:** J-06, SCR-01/SCR-09. **Depends:** US-17/US-18. **Map:** HT-G3/HT-G7; HT-W12/HT-W13/HT-W19.

- **Given** an acknowledged local save, **when** reopening in the same profile, **then** that snapshot/notes/settings load with the recorded mode and references.
- **Given** restore of an older snapshot, **when** accepted, **then** a new snapshot cites that ancestor; existing versions are preserved.
- **Given** malformed/gapped imported history, **when** validation fails, **then** ST-13 allows read-only valid artifacts/recovery, with no invented repaired chain.

### US-20 — Keep source facts immutable while editing prose

**Priority:** P0. **Persona/job:** P-01 writes an explanation without fabricating provenance. **Journey/screens:** J-06, SCR-06/SCR-07. **Depends:** US-16/US-17. **Map:** HT-G3/HT-G7; HT-W02/HT-W12/HT-W13.

- **Given** generated/imported text, **when** a user writes a revised explanation, **then** the overlay is labelled user-authored and the source text/hash stays unchanged.
- **Given** a genuine source correction, **when** a new source revision is imported, **then** a new validated dossier/run copy is required; the prior citation remains pinned.
- **Given** language switch, **when** display changes, **then** authored notes and quotes are not silently translated or overwritten.

### US-21 — Export a complete edited package in TH/EN

**Priority:** P0. **Persona/job:** P-01/P-02 takes the current work into a discussion. **Journey/screens:** J-07, SCR-10. **Depends:** US-19/US-20. **Map:** HT-G3/HT-G7; HT-W12/HT-W13/HT-W19.

- **Given** saved/imported dossier plus user edits, **when** JSON/recovery export is generated, **then** IDs, mode, source basis, overlay, snapshot/version and all notes survive round-trip.
- **Given** frontend Markdown exporter enabled, **when** TH/EN previews/downloads are generated, **then** edits are present in a separate section; original quotes, unknowns and provenance remain intact.
- **Given** current backend Markdown exporter, **when** edits exist, **then** complete-edit export is unavailable with a clear reason; a generic success toast cannot conceal dropped edits.

### US-22 — Recover from export/render/download failure

**Priority:** P0. **Persona/job:** P-02 retains work when export fails. **Journey/screens:** J-07/J-09, SCR-10. **Depends:** US-21. **Map:** HT-G3/HT-G7; HT-W13/HT-W19.

- **Given** renderer failure, **when** export is attempted, **then** selected version and notes remain; retry applies to rendering only and recovery JSON remains offered if feasible.
- **Given** browser download initiation, **when** successful, **then** copy says file prepared/download started, not that remote delivery or disk save is verified.
- **Given** malicious HTML or formula-like text in a note, **when** preview/export renders, **then** it stays inert text; no script/link fetch executes.

### US-23 — Prepare next information requests

**Priority:** P1. **Persona/job:** P-04/P-02 turns gaps into a focused follow-up draft. **Journey/screens:** J-07, SCR-11. **Depends:** US-16/US-21. **Map:** HT-G3/HT-G7; HT-W12/HT-W13/HT-W16.

- **Given** an unresolved item, **when** a request is drafted, **then** question, source/evidence references and optional role/priority are editable and saved locally.
- **Given** a request list, **when** copied/exported, **then** source facts and user questions remain distinguishable; no automatic email or contact lookup occurs.

### US-24 — Hand off locally and gate team capabilities

**Priority:** P1 local handoff; P2 team service. **Persona/job:** P-01/P-03 exchanges an inspectable package. **Journey/screens:** J-08, SCR-10/SCR-11. **Depends:** US-21/US-26. **Map:** HT-G3/HT-G7; HT-W13/HT-W16/HT-W19.

- **Given** only local adapters, **when** handoff is chosen, **then** download/copy is available and team invites, cloud sync and fake sharing success are absent.
- **Given** a later collaboration adapter, **when** team controls are enabled, **then** actual identity/access/revocation/conflict/retention behavior is tested separately; role labels alone grant no authority.

### US-25 — Understand errors and preserve unaffected work

**Priority:** P0. **Persona/job:** any persona recovers without starting over. **Journey/screens:** J-02/J-09, all relevant screens. **Depends:** US-05. **Map:** HT-G3/HT-G7; HT-W13/HT-W19.

- **Given** validation, permission, quota, stale data or source failure, **when** reported, **then** error names action/target/outcome/preserved work/next step in both locales and a safe diagnostic ID only.
- **Given** an uncertain mutation outcome, **when** reopening, **then** reconciliation precedes retry; repeated clicks cannot create duplicate local commits.
- **Given** a source/document containing instructions, **when** viewed, **then** it is inert evidence data and cannot trigger tools, navigation or system actions.

### US-26 — Show capabilities and honest modes

**Priority:** P0. **Persona/job:** P-02 knows which controls do real work. **Journey/screens:** J-03/J-09, SCR-01/SCR-05/SCR-10. **Depends:** US-01. **Map:** HT-G3/HT-G7; HT-W13/HT-W19.

- **Given** missing/failed capability discovery, **when** loading, **then** default is unavailable, with import/read-only/demo still usable where supported.
- **Given** a simulated scenario, **when** any screen/export is shown, **then** the simulation/synthetic badge persists and no real evidence identity is substituted.
- **Given** capability changes, **when** an action becomes unavailable, **then** user edits persist and the UI explains the affected action without changing historic receipts.

### US-27 — Use the workflow in Thai/English and four formal themes

**Priority:** P0. **Persona/job:** all personas reads and operates the workflow accessibly. **Journey/screens:** J-01–J-09, all screens. **Depends:** US-01. **Map:** HT-G3/HT-G7; HT-W13/HT-W16/HT-W19.

- **Given** locale/theme choice, **when** changed, **then** labels, dates and system messages update consistently, source quotes remain original, state/focus/unsaved notes persist.
- **Given** keyboard/screen reader/reduced motion and narrow viewport, **when** completing the main workflow, **then** semantic navigation, visible focus, readable tables/dialogs and noncolor statuses work.
- **Given** KMITL/ICT-inspired themes, **when** shown, **then** they do not use official identity claims or logos; all status/contrast checks pass independently for each theme.

### US-28 — Recover from local storage limits and protect privacy

**Priority:** P0. **Persona/job:** P-01 knows what is retained and recovers from storage failure. **Journey/screens:** J-06/J-09, SCR-01/SCR-09. **Depends:** US-17/US-25. **Map:** HT-G3/HT-G7; HT-W13/HT-W19.

- **Given** quota failure or unavailable persistent storage, **when** saving, **then** ST-07/ST-09 preserves in-memory changes, marks them unsaved and offers recovery export.
- **Given** local deletion, **when** requested, **then** only the selected local project is targeted with scope/count visible and a recovery option; imported original files and unrelated projects are untouched.
- **Given** prototype analytics/auth absent, **when** used, **then** no sensitive data, automatic telemetry or credential input is required; any future analytics is separate explicit opt-in.

## Acceptance evidence format

For each implemented story record: candidate commit; adapter/mode; fixture ID or imported artifact hash; command/browser action; actual result; screenshot/video path if created; limitation. Mark **IMPLEMENTED**, **SIMULATED**, **PROPOSED**, **BLOCKED_LOCAL** or **NOT_RUN** per behavior. A screenshot proves appearance at a moment; persistence requires close/reopen evidence, and conflicts require concurrent-write evidence. Tests must check the before/after invariant, not merely match the implementation's DOM labels. Do not copy the audit's 269-pass result into a new frontend test report.
