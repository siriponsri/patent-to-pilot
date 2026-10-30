# Backend integration map, UI state and safe fixtures

Inspected source: `96c63b14a1a2df8e8f8b816edee0dff7feddc3d3`. The repository is Python-first. No frontend package manifest or HTTP HealthTech server was found in the scoped source inventory. **An `api.py` module is not a running web API.** This specification allows a complete local frontend inspection/edit/export slice through adapters without waiting for a live study or silently modifying backend.

## Existing interfaces and artifacts

| Existing source | Actual contract/output | Honest frontend use and limitation |
|---|---|---|
| [product/contracts.py](../../../src/patent_to_pilot/product/contracts.py) | `ProjectBrief`, `EvidenceCard`, `ReviewDecision`, `JobStatus`; closed enums; TH/EN and four theme keys | Reuse field semantics. `ReviewDecision` is a type, not a requirement for confirmation on every action. EvidenceCard source_version is integer; HealthTech EvidenceItem source_version is string revision. Never coerce these as equivalent. |
| [healthtech/contracts.py](../../../src/patent_to_pilot/healthtech/contracts.py) and [schemas](../../../schemas/healthtech/DossierVersion.schema.json) | `DeviceQuery`, `SourcePayload`, `EvidenceItem`, `PatentCandidate`, `AcquisitionEvent`, `DossierVersion`, `RunManifest`, local `AcquisitionBudget` | Validate imported data using generated JSON schema plus semantic hash/reference/locator checks. Extra UI fields cannot be inserted into closed contracts. |
| [engine.py](../../../src/patent_to_pilot/healthtech/engine.py) | `DossierInput`, synchronous `run_dossier(...) -> (dossier, events, manifest)`, `export_markdown(...)` | Offline in-memory corpus/policies, no runtime gold/provider/network. Backend Markdown currently omits user_edits. No HTTP job/event stream. |
| [run_dossier.py](../../../scripts/healthtech/run_dossier.py) | `input output`; fresh output directory; `dossier.json`, `dossier.md`, `dossier.en.md`, `dossier.th.md`, `manifest.json`, `acquisition_events.jsonl` | Import completed artifact files. Do not execute shell commands from the browser or expose arbitrary filesystem paths. Runner is synchronous; no status API. |
| [sources.py](../../../src/patent_to_pilot/healthtech/sources.py) | `normalize_510k_record`, `source_payload`, `field_evidence`; allowlisted fields | Already supplied FDA snapshots can populate a local catalog. Source date here is supplied retrieval date; decision_date remains an independent field. This is not PMA/UDI/recall ingestion or device–patent linking. |
| [provenance.py](../../../src/patent_to_pilot/healthtech/provenance.py) | `check_evidence` verifies identity/revision/hash/date/jurisdiction and exact span/typed field | Show source integrity only. Frontend must match canonical JSON hashing and Unicode code-point locators before claiming an equivalent check. |
| [history.py](../../../src/patent_to_pilot/healthtech/history.py) | `save_version`, `load_versions`, `append_user_edits`, `source_view`, `history_manifest` | File-based local functions. No HTTP/auth/team service and no safe concurrent commit guarantee at audited revision. |
| [manage_dossier_history.py](../../../scripts/healthtech/manage_dossier_history.py) | `init dossier history_dir`; `edit history_dir --key --value`; `manifest history_dir` | Exact CLI signatures, not frontend endpoints. Current edit value is a string map, without rich author/structured review metadata. |
| [view_dossier_source.py](../../../scripts/healthtech/view_dossier_source.py) | `dossier source_id [--field FIELD]` prints pinned source | Viewer supports a top-level field here. `check_evidence` understands dot paths for nested objects; do not claim the CLI viewer already implements every nested locator. |
| [api.py](../../../src/patent_to_pilot/healthtech/api.py), [run_api_dry_run.py](../../../scripts/healthtech/run_api_dry_run.py) | Config/request/receipt models, `dispatch_healthtech_request`; dry_run and injected mock only; live rejected | Current receipt is DRY_RUN_NOT_EXECUTED or MOCK_COMPLETE, not a dossier job. Dry-run response/schema-validation result may be null. Placeholder model healthtech-not-used is not a configured research model. |
| [fetch_public_510k.py](../../../scripts/healthtech/fetch_public_510k.py) | Bounded allowlist acquisition script exists | Do not call it from this docs/frontend task. Audit found cumulative storage limit gap; future ingestion service requires corrected accounting first. |
| [evaluation/healthtech](../../../src/patent_to_pilot/evaluation/healthtech/scifact.py) | Separate retrieval/SciFact evaluation | Not a product data feed. No evaluator labels/gold/cited-doc oracle in UI queries, runtime sources or simulated real output. SciFact is a separate component, not patent-link validation. |

Existing current public examples: local `results/healthtech/public-dossiers-20261027-r3/{K190167,K163345,K121849}/`. Their input packages in `results/healthtech/public-510k-20261027-r1/inputs/` contain `patents=[]`; dossiers have seven field-evidence items each and no candidates. Those local result folders are not guaranteed in a clean checkout. **Do not copy their raw third-party source payloads into this docs pack.** The frontend can inspect user-supplied copies; authored fixtures work independently. Public source links/IDs/hashes remain references, never synthetic proof.

## Audited backend limitations and independent frontend work

Audit source/fingerprint is recorded in [verification.json](verification.json). These are reported/reviewed source limitations, not newly repeated adversarial experiments in this package. Check current revision before claiming they remain or are fixed.

| Finding | Frontend acceptance/recovery now | Backend-owned fix/evidence required | Scope it blocks |
|---|---|---|---|
| F1, P1: duplicate SciFact rationale IDs inflate metrics; unexpected claims ignored | No quality percentages or study-result dashboard sourced from unvalidated component output | Reject declared invalid predictions, doc/sentence bounds/claim membership; meaningful adversarial and official-evaluator comparison | Scientific component performance claims, not dossier UI |
| F2, P1: check-then-write history race loses edits | Transactional browser snapshot with expected base or memory/recovery mode; ST-08; never label current CLI backend history concurrency safe | Atomic exclusive/transactional expected-version commit; two-writer regression proves no lost updates/false dual success | Reliable backend multiwriter save, not local UI |
| F3, P2: storage flag checks free space rather than cumulative bytes | Imported file size guards are local frontend safeguards only; unknown remote storage usage stays unknown; ST-09 | Cumulative raw+normalized+manifest storage/transfer accounting and reservation; partial/failure receipts | Larger live fetch/storage assurance |
| F4, P2: backend Markdown omits user_edits | Tested independent frontend Markdown export with labelled exporter and notes section, or recovery JSON with omission notice | Backend renderer includes edits separately plus version/basis; regression round-trip | Complete edited export through that backend exporter |
| F5, P2: invalid default SciFact revision | Do not display broken default revision as validated/pinned; keep component metadata separate | Resolve/pin actual full source revision and verify references | New SciFact preparation provenance |

Current `engine.py` also contains B1 token-overlap approximation and B3 heuristic code despite stale manifest prose/no strong validated baseline. Product defaults should use clearly labelled HT-B0b or fixed HT-B2 for supported offline examples. Expose B1/B3 only as explicit engineering approximations with current capability evidence; no “adaptive advantage,” calibrated confidence or strong hybrid claim.

## Adapter seam — proposed frontend interface

These names are a design proposal, not callable exports in this repository. Claude may implement them in its frontend directory. Keep raw domain objects immutable and return an explicit result/knownness rather than fake successes.

```ts
type Mode = 'synthetic_demo' | 'imported_public' | 'simulation';
type Result<T> =
  | { ok: true; value: T; receiptId: string }
  | { ok: false; code: string; outcome: 'not_executed'|'pending'|'uncertain';
      retryable: boolean; preservedRefs: string[]; diagnosticId: string };
interface DossierAdapter { // Proposed; domain JSON types derive from existing schemas
  capabilities(): Promise<Capabilities>;
  importPackage(bytes: Uint8Array): Promise<Result<ValidatedPackage>>;
  listDevices(text: string): Promise<Result<DeviceSummary[]>>;
  openDossier(ref: string): Promise<Result<DossierWithProvenance>>;
  inspectSource(ref: PinnedEvidenceRef): Promise<Result<SourceView>>;
  saveLocal(snapshot: LocalSnapshot, expectedParent: string|null): Promise<Result<LocalSnapshot>>;
  exportSnapshot(ref: string, language: 'th'|'en', format: 'recovery_json'|'markdown'):
    Promise<Result<PreparedFile>>;
  // Optional future RunAdapter/CollaborationAdapter; absent methods are unavailable.
}
```

`FixtureAdapter` serves authored fixture data and simulates only explicitly chosen scenarios. `FileImportAdapter` reads selected JSON without network and displays imported completed receipts. `BrowserDraftStore` implements local transactional persistence if available; the capability stays unavailable until implemented/tested. A future `ServiceAdapter` is separate and defaults to unavailable. Switching adapter never upgrades fixture/public claims or moves project data to a server implicitly. An unsupported method returns an explicit unavailable result, not a resolved fake payload.

### Capability inventory

| ID | Frontend capability key | Current honest basis/default |
|---|---|---|
| CAP-01 | `deviceCatalog` | Proposed local catalog/file adapter; unavailable until loaded, no global device search |
| CAP-02 | `packageImport` | Existing JSON contracts; frontend parsing/validation still to implement |
| CAP-03 | `sourceInspect` | Existing pinned payload/source-view seam; frontend safe viewer still to implement |
| CAP-04 | `runStart` | false for current file/demo adapters; no live service |
| CAP-05 | `runControl.{cancel,resume,retry}` | all false for current CLI artifacts; explicit simulation may demonstrate transitions |
| CAP-06 | `localDrafts` | proposed browser-local snapshots; advertised only after real persistence checks |
| CAP-07 | `backendHistory` | false for safe service persistence at inspected revision |
| CAP-08 | `export.{recoveryJson,editedMarkdown,pdf,docx}` | proposed frontend recovery/Markdown after implementation/tests; PDF/DOCX false; backend edited Markdown incomplete |
| CAP-09 | `collaboration` | false; local download handoff only |
| CAP-10 | `analytics` | false; no telemetry or opt-in UI for an absent service |

Capabilities carry adapter ID/version/mode and reason for unavailable actions. Missing capability discovery fails closed for mutations while retaining valid read-only data. A disabled control needs a short explanation and useful alternative. Hide unavailable advanced modules; avoid a page full of grey “coming soon” buttons. Demo capability booleans describe a scenario, never proof the real application implements it.

### Proposed HTTP endpoints — NOT IMPLEMENTED

Only a later separately scoped service should implement these; do not call them from an allegedly connected prototype or turn them into a backend task here.

| Proposed endpoint | Shape and guarantees needed | Local substitute now |
|---|---|---|
| `GET /api/healthtech/capabilities` | Adapter/mode, supported formats, provenance checks and persistence scope | Static local capability manifest tied to implemented adapter |
| `GET /api/healthtech/devices?q=…` | Catalog scope/revision and paginated summaries; no oracle-assisted matching | Validated local catalog/filter |
| `POST /api/healthtech/projects` | Valid brief/query/source references; idempotency key; project revision receipt | New browser-local project snapshot |
| `POST /api/healthtech/runs` | Authorized bounded config/input hash; actual durable run/attempt receipt | Import completed run or labelled simulation |
| `GET /api/healthtech/runs/:id` | JobStatus plus real events/manifest references; no invented progress | Read artifact data |
| `POST /api/healthtech/runs/:id/cancel` | Explicit pending/acknowledged/uncertain outcome; settle actual attempts/costs | Simulated transition only |
| `GET /api/healthtech/dossiers/:id/versions/:version` | Immutable closed dossier JSON and hash | Imported read-only domain dossier |
| `GET /api/healthtech/dossiers/:id/sources/:sourceId?version=…` | Pinned payload/revision/locator response, scoped access | Safe local payload viewer |
| `POST /api/healthtech/dossiers/:id/versions` | Expected version/hash, idempotency key, exclusive commit; 409 conflict preserving both edits | Transactional local UX snapshot; does not change backend version |
| `POST /api/healthtech/exports` | Snapshot/version/exporter/language/format; omission metadata and file receipt | Tested local frontend renderer |

Team invites/comments/auth, source crawling and payment routes are intentionally unspecified extensions requiring actual scope and service design. API error envelopes should include stable code, affected refs, outcome, preserved refs, retryability and diagnostic ID. Do not expose provider payloads or credential paths. No credentials belong in browser bundle, local fixture, URL or exported dossier.

## UI data model — proposed, separate from closed domain JSON

The authoritative domain remains `DossierVersion` plus manifest/events and sources. The frontend recovery envelope **does not validate as DossierVersion**; it contains one validated dossier and a separate overlay. Use `fixtures/ui-fixtures.schema.json` as the authored fixture-envelope contract, not a production HTTP schema.

| UI field/model | Semantics and persistence |
|---|---|
| `AppPreferences` | locale th/en, existing theme enum; local only, no user identity/health inference |
| `ProjectDraft` | Raw input, selected source ref, objective/questions, pending cutoff; may be incomplete and cannot enter engine until valid |
| `LocalSnapshot` | `snapshotId`, `parentSnapshotId`, `sourceDossierHash`, `backendDossierVersion`, `overlay`, `savedAt`, storage scope; own version namespace |
| `overlay.notes[]` | Target evidence/candidate/section, base dossier version, text, basis `user_note`, local review marker; no fake author identity |
| `overlay.featureLinks[]` | User-created feature-to-evidence links; label authored, not machine-verified |
| `overlay.requestDrafts[]` | Local question plus references/priority/intended role; no recipient address required |
| `KnownValue<T>` | Proposed `{status:'known',value:T}` or `{status:'unknown',reason:string}`; `null`/absent never silently becomes zero |
| `CostView` | `accounting` offline_counts/monetary/not_recorded; actual, estimated, reserved and settlement status separately; only source receipts can establish actual zero |
| `RunView` | Native `JobStatus.state` when supplied plus orthogonal mode, freshness, completeness, source errors and budget outcome; display state not forced into the JobStatus enum |
| `PinnedEvidenceRef` | dossier ID/version, source ID/revision/hash, evidence ID/locator; source date/jurisdiction carried from contract |

Source dates not present in contracts remain unknown with a reason. Do not invent publication/update dates to fill the view model. `SourceRecord.version` is a record integer while `version_label` is a source revision string; dossier version is a third independent version. A relationship label is not an integrity-check field. Feature links/review labels/proposed API metadata remain overlay data unless the backend contract is separately extended and tested.

### State inventory and recovery

These display states are orthogonal to current `JobStatus` (queued/running/ready_for_review/blocked/failed/cancelled) and never inserted as new backend enum values. A dossier can be ready for inspection and still have partial/unjudged sections.

| ID | Display state | Trigger and UI requirement | Recovery/exit |
|---|---|---|---|
| ST-01 | Empty | No project/catalog/evidence; explain what is absent without a zero-coverage claim | Select/import/demo or add question |
| ST-02 | Loading | Actual async local parse/store or capability-backed request | Preserve context, cancellable local import where safe; no fabricated progress |
| ST-03 | Partial | Valid artifacts plus failed/unavailable source | Open available evidence; retain per-source error; retry only supported branch |
| ST-04 | Blocked | Required comparator, permitted source or capability missing | Save draft; name exact missing requirement and available alternative |
| ST-05 | Failed | Requested action failed with known outcome | Preserve prior acknowledged data, retry safe action or recovery export |
| ST-06 | Invalid input | Schema/reference/cutoff/data-class validation failure | Field summary + targeted correction, no destructive replacement |
| ST-07 | Persistence unavailable | Browser denies/does not support durable local store | Memory-only label and recovery download; no saved badge |
| ST-08 | Version conflict | Expected parent/hash no longer current | Preserve base/theirs/yours, reapply or separate-copy, never silent overwrite |
| ST-09 | Storage/size limit | File guard/quota hit, known bytes if measured | Keep text, download recovery, explicitly select local cleanup; do not claim backend cap works |
| ST-10 | Cancelled | Supported operation acknowledges cancellation | Preserve completed events/artifacts/cost; new run only through actual capability |
| ST-11 | Billing unknown | No authoritative actual/settlement receipt | Display unknown/pending, reconcile before new paid mutation, no zero/default savings |
| ST-12 | Provenance mismatch | Hash/revision/locator missing or mismatched | Retain citation, withhold source-matched badge, import correct pinned revision |
| ST-13 | History corrupt | Invalid/gapped/duplicate parent chain or malformed snapshot | Quarantine read-only, preserve bytes and export valid recovery; no fabricated repair |
| ST-14 | Stale view | Open snapshot/source differs from new available revision | Keep pinned view and offer explicit update/copy, never silently rebind evidence |
| ST-15 | Ready for inspection | Import/local rendering succeeded under declared scope | Show unresolved items and actual storage/export limits; not “research validated” |

State machines: import `idle → ST-02 → ST-15 | ST-06 | ST-05`; save `dirty → saving → acknowledged local saved | ST-07 | ST-08 | ST-09`, with concurrent edits kept dirty for the next transaction; job `queued → running → ready_for_review | blocked | failed | cancelled`, with cancellation request and reconciliation as UI substates until authoritative acknowledgement. Do not auto-resume a paid job or auto-retry an uncertain mutation. Memory state is never evidence of durable persistence.

## Authored fixtures

[ui-fixtures.json](fixtures/ui-fixtures.json) contains a validated synthetic `DossierVersion` and scenario envelopes. Every source uses `urn:synthetic:` and `synthetic=true`, the brief uses `data_class=synthetic`, and all visible fixture modes retain a demo/simulation label. Fictional patent IDs preserve document kinds; they do not represent real patents. Source hashes are computed from authored payloads using actual canonical hashing. Independent-disclosure demonstration is a separate authored synthetic source, not evaluation gold or a real disclosure.

| ID | Scenario | Expected observable behavior |
|---|---|---|
| FX-01 | Ready synthetic dossier | One candidate and one synthetic disclosed-link example; exact separate disclosure basis navigable; no legal/clinical claim |
| FX-02 | Empty patent pool | Zero input/candidate items plus explicit empty-corpus reason, coverage unknown |
| FX-03 | Loading | Honest labelled simulation/loading, no real network claim |
| FX-04 | Partial source failure | Existing facts visible, patent source unavailable, no negative inference |
| FX-05 | Blocked live run | runStart false, useful import/demo alternatives |
| FX-06 | Malformed import | Authored expected-error metadata; invalid input not silently accepted |
| FX-07 | Storage denied | Unsaved text preserved with memory/recovery label |
| FX-08 | Concurrent edit conflict | Distinct base/theirs/yours retained; no false success |
| FX-09 | Quota exceeded | Quota banner; recovery JSON includes user edits |
| FX-10 | Cancelled run | Simulated acknowledged cancellation, recorded attempts preserved |
| FX-11 | Unknown billing | Actual cost null with reason; no zero coercion |
| FX-12 | Bad locator/hash | Expected invalid copy is rejected/withheld; positive original remains inspectable |
| FX-13 | Corrupt history | Expected invalid parent-chain metadata, read-only recovery |
| FX-14 | Stale imported view | Explicit old/new source references, no automatic source rebinding |
| FX-15 | Export drops edits | Legacy backend Markdown capability false; recovery JSON/frontend renderer path offered |

The fixture scenario's error metadata is not a valid backend dossier and must not be sent into the engine. Only `synthetic_dossier` and the explicitly identified empty-corpus dossier are positive domain payloads. Negative cases use small controlled patches applied by tests to a copy, preserving the original. No original public corpus, evaluator material, paper PDF or credential is included.

## Scope of verification

`validate_docs.py` checks local links/ID coverage, fixture JSON schema, embedded domain JSON schema/Pydantic validation, exact evidence integrity, and negative mutations for ID/hash/locator/disclosure/cutoff. It does not build a frontend, start a server, execute a CLI job or run a scientific benchmark. Its receipt records actual commands/result and source hashes. UI persistence, browser accessibility, screenshots, rendering and all proposed endpoints remain **NOT_RUN** until Claude provides evidence on its candidate branch.
