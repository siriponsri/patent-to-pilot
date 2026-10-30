# Information architecture, screens and design rules

This is a proposed UI specification, not rendered UI. Routes are frontend navigation names, **not existing API endpoints**. Follow [story acceptance](02_STORY_BACKLOG.md) and [adapter capability rules](04_INTEGRATION_STATES.md). Choose one clear product shell; avoid dashboards that replace the evidence workflow with decorative metrics.

## Information architecture

```text
Home / local projects (SCR-01)
  New → choose public device (SCR-02) → project brief (SCR-03)
  Import → source/package review (SCR-04)
  Project /project/:localId
    Overview (SCR-06)
    Evidence and compare (SCR-07)
      Source detail (SCR-08, pinned version)
    Run receipt/status (SCR-05)
    History/save recovery (SCR-09)
    Next information requests (SCR-11)
    Export (SCR-10)
Global: TH/EN, theme, storage/mode details, help
```

Local IDs are navigation identifiers; do not treat them as authorization tokens. Preserve project/row/version context when opening sources or history. Browser back closes a source detail or returns to the original row with focus restored. A deep link with missing local data offers import/reopen rather than inventing a project or making arbitrary server requests.

On desktop, use a compact left navigation and one content column (comfortable reading width about 72–84 rem for tables, 42–50 rem for prose); source detail can use a right panel. On mobile, use a compact header and menu, single-column forms, evidence cards with consistent field labels, and a full-screen source route. At 320 CSS px the page must not overflow; a labelled data-table region may scroll horizontally without trapping keyboard focus. Keep primary actions visible but avoid a sticky bar obscuring the focused field at zoom.

## Screen specifications

### SCR-01 — Home and local projects

**Route:** `/`. **Goal/entry:** resume a local project or choose named-device/import/demo start. **Components:** CMP-01/CMP-02/CMP-03/CMP-12. **Stories:** US-01/US-19/US-26–US-28.

Show an understated product statement, three start actions, and recent local projects with device ID, last acknowledged local snapshot, storage scope and mode. Default order: last opened. Demo cards are visually and textually distinct. Do not display fabricated “projects analyzed,” investor ROI or study success figures. Empty ST-01 gives a useful start action. Loading ST-02 has a text status. Corrupt entries ST-13 open read-only recovery; permission/quota states ST-07/ST-09 keep import/demo available. Selecting delete names the local project and warns only about that local copy, after offering recovery export. No sign-up modal.

### SCR-02 — Named-device selection and disambiguation

**Route:** `/new/device`. **Goal/entry:** choose the specific comparator from current local records or an imported catalog. **Components:** CMP-04/CMP-05/CMP-13. **Stories:** US-02/US-03.

Single labelled search field accepts name/manufacturer/public ID, with source scope stated beside it. Result rows show identifier, device name, applicant when present, source jurisdiction/type/date and pin-able record. One primary action, “Use this device.” If no catalog/search capability exists, offer validated import and labelled demo instead of a nonfunctional search box. Ambiguous results stay separate; no auto-selection based on popularity. Selection pins source lineage and returns a draft to SCR-03. An imported deep link with an unrecognized source uses ST-06. Keyboard arrows are used only for a correctly implemented listbox; ordinary links/buttons are an acceptable simpler default.

### SCR-03 — Project brief

**Route:** `/new/brief` or `/project/:id/brief` for a new draft. **Goal:** define purpose and questions. **Components:** CMP-01/CMP-04/CMP-11/CMP-12. **Stories:** US-03/US-04/US-17/US-20.

Order fields: selected comparator summary/change, objective, optional audience, optional features/questions, jurisdiction/cutoff, source selection, count limits under Details. Project title is optional UI metadata; backend project ID is safely generated and validated. Default objective is a neutral editable sentence about inspecting evidence for the chosen device. Explain why a cutoff conflicts with included sources inline. Keep draft save and continue available independently of a run service. An incomplete idea-only draft has a missing-comparator callout, not a fabricated `DeviceQuery`. Save indicator has actual persistence scope. Changing a comparator in a completed project starts a new draft/copy after explaining what is preserved; it does not rewrite the old run.

### SCR-04 — Sources and import review

**Route:** `/import` or `/project/:id/sources`. **Goal:** inspect what will be read and what passed validation. **Components:** CMP-05/CMP-10/CMP-13. **Stories:** US-05/US-06/US-25.

Provide a constrained JSON picker with supported schema/version, size guard and explicit public/synthetic scope. Display validation results per file/source: accepted, unresolved rights, bad hash, bad reference, newer than cutoff or unsupported data class. Before creating a copy, show device ID/mode, evidence/candidate counts with knownness, source revisions and import destination. Never preview credentials or raw arbitrary text files. URL references are metadata only unless a future permitted source adapter says otherwise. A short privacy note states local processing/storage truthfully. Current capability does not include PDF/OCR or arbitrary web ingestion. Cancel returns without replacing the project. Bad source fails its branch while valid existing projects remain usable.

### SCR-05 — Run receipt, progress and budget

**Route:** `/project/:id/runs/:runId`. **Goal:** explain recorded work; simulate job states for frontend acceptance. **Components:** CMP-02/CMP-06/CMP-10/CMP-13. **Stories:** US-07–US-10/US-26.

Lead with “Imported completed run,” “Simulation,” or an actual service state. Show scope, declared policy, completed/failed queries and current stop reason. Progress is a sequence of known stages/events; do not infer elapsed time remaining or claim 80% without a measurable denominator. Default budget summary is calls used/cap and unique candidates; Details separates returned occurrences, retries, elapsed time, offline count basis and recorded cost. Future paid accounting needs estimated/reserved/actual/unknown fields from its adapter. Do not offer “upgrade,” live model selector, cancel, resume or retry when absent. Partial facts open SCR-06 while source errors remain. Cancel has a pending state before acknowledgement. Historical receipts stay immutable.

### SCR-06 — Dossier overview and editing

**Route:** `/project/:id`. **Goal:** understand available evidence and continue the investigation. **Components:** CMP-01/CMP-02/CMP-03/CMP-07/CMP-11/CMP-12. **Stories:** US-11/US-15–US-17/US-20.

Header: device name + raw/canonical ID, source jurisdiction, cutoff, dossier version and local snapshot, mode badge and save status. Main sections: product/regulatory facts; patent candidates with relationship status; feature evidence; unresolved items; next requests. A fact summary links to source detail. An evidence counter is a count, not a quality score. Do not call a 510(k) decision code “FDA approved.” Editing controls attach clearly marked user notes/section drafts. Source facts remain read-only. Empty candidate sections distinguish absent corpus, searched-with-no-result and unknown scope. Retain unresolved and request sections even when facts exist. Primary actions: inspect evidence, add question, export; avoid repeated “approve” buttons.

### SCR-07 — Feature evidence and candidate comparison

**Route:** `/project/:id/evidence`. **Goal:** compare basis and identify gaps. **Components:** CMP-03/CMP-07/CMP-08/CMP-11. **Stories:** US-12/US-13/US-15/US-16.

Two tabs or clearly separated regions: feature–evidence rows and candidate documents. Feature rows show feature/question, statement, evidence kind, relationship if applicable, integrity-check label, source/date and uncertainty. Current contract lacks feature-to-evidence mapping; show the imported evidence list first and label any user-created local mapping. Candidate rows show document ID/kind/jurisdiction, association status and basis, with optional named score details. Default ranking preserves imported order; a sort names its field/direction. Compare up to three selections in an accessible panel; missing values read “not supplied.” Pin selected IDs through filtering. Family collapsing is unavailable without source mapping. Notes do not change backend relationship status. ST-12 rows retain their identifiers but cannot appear validated.

### SCR-08 — Exact source viewer

**Route:** `/project/:id/source/:sourceId?dossierVersion=…&evidenceId=…`. **Goal:** inspect the pinned source basis. **Components:** CMP-03/CMP-09/CMP-13. **Stories:** US-14–US-16.

Order: cited statement and basis; exact field/value or quote with locator; source title/ID/type/revision/date semantics/jurisdiction; external URI; expandable full hash/available payload/rights note. Show full IDs with copy buttons, never truncate the only recoverable reference. Highlight Python Unicode code-point ranges; structured nested field support must be explicitly implemented beyond current top-level `source_view --field`. External source failure is separate from local snapshot availability. Inline note editor records local review state without promoting evidence. On a bad locator/hash, render ST-12, explain the failed check, preserve raw locator, and offer return/import-correct-revision. Treat source HTML/links as inert data until safe explicit navigation.

### SCR-09 — History, save status and conflict recovery

**Route:** `/project/:id/history`. **Goal:** reopen acknowledged work and resolve competing changes. **Components:** CMP-10/CMP-11/CMP-12/CMP-13. **Stories:** US-17–US-20/US-28.

List imported backend dossier version and local UX snapshot IDs separately. Each local snapshot shows parent, time, changed note/section keys, storage scope and source dossier hash. Do not imply author identity when only a browser-local label exists. Version comparison displays changed user text and reference changes; no automatic semantic conclusion. Restore creates a new snapshot. Conflict panel shows base/theirs/yours, copy/download recovery, reapply and separate-copy options; unsaved text remains until resolved. ST-07/ST-09 show memory retention/recovery; ST-13 quarantines corrupt history read-only. Browser eviction and cross-device sync are limitations, not hidden failures. No cloud-backup icon unless a tested service exists.

### SCR-10 — Export and package handoff

**Route:** `/project/:id/export`. **Goal:** prepare a truthful selected-version deliverable. **Components:** CMP-02/CMP-10/CMP-14. **Stories:** US-21/US-22/US-24.

Controls: selected snapshot/version, report language, supported formats (JSON/recovery and tested frontend Markdown), preview/download. Include source facts, candidates/status, basis/locators, unresolved items, questions and separate user edits. Raw JSON “dossier only” and UX recovery envelope are different choices with explicit scope. Preview names exporter/version and omissions before download. Current backend Markdown omits user edits; do not label it complete. After browser download starts, say “Download started,” not “sent” or “saved to disk.” No PDF/DOCX button without implementation. No email field or invite action. Rendering errors preserve saved data; recovery JSON remains useful. Cancel closes export without editing the dossier.

### SCR-11 — Next information requests

**Route:** `/project/:id/requests`. **Goal:** turn unresolved evidence into useful local questions. **Components:** CMP-07/CMP-11/CMP-14. **Stories:** US-16/US-23/US-24.

Show existing `next_information_requests` strings and locally authored drafts separately. Proposed richer draft has question, optional intended role, priority, target evidence/unresolved refs and local status draft/done-by-user. No address is required. “Done” means a user marked the preparation task done, not that an answer was received or validated. Copy/export preserves provenance and unresolved wording. No outbound communications are sent. Failed local save keeps text and directs to SCR-09 recovery. If no questions exist, invite one precise question rather than inventing a persuasive business conclusion.

## Component inventory

| ID | Component | Contract/behavior |
|---|---|---|
| CMP-01 | Project shell/context header | Device, mode, source cutoff, version/snapshot, navigation; never loses context on locale change |
| CMP-02 | Mode and capability banner | Explicit imported public draft / synthetic demo / simulation / unavailable; persists into export |
| CMP-03 | Evidence/basis/relationship badges | Separate dimensions; icon + text + accessible description, no green “verified claim” |
| CMP-04 | Brief and selector fields | Native labels/help/errors; plain language; optional inputs labelled optional |
| CMP-05 | Device/source cards | Stable IDs, missingness, source/date semantics and rights note |
| CMP-06 | Acquisition/budget panel | Actual event data/units, unknown fields, stop reason, no synthetic billing |
| CMP-07 | Evidence/unresolved/request row | Expandable details and stable reference links, copyable source identity |
| CMP-08 | Compare/filter controls | Named sorts, explicit selected count, at most three items, keyboard operation |
| CMP-09 | Source detail | Typed structured value or exact text span, pinned revision/hash/locator |
| CMP-10 | State/error/recovery banner | Action/target/outcome/preserved work/next step; unobtrusive background failures |
| CMP-11 | User annotation editor | Origin/basis, target/version, autosave state; never rewrites source text |
| CMP-12 | Save/history indicator | Unsaved → saving → acknowledged local saved; conflict/quota can never show success |
| CMP-13 | Technical details disclosure | Hashes, named scores, attempts, schema errors, scope; hidden by default, accessible |
| CMP-14 | Export/request preview | Snapshot/exporter label, notes/provenance retained, static safe text rendering |

## Bilingual key microcopy

Use stable translation keys; these are suggested product strings. Thai tone is clear and formal without bureaucratic phrasing. Use consistent “แฟ้มหลักฐาน” for dossier, with “Dossier” in help where useful. No inline scientific quote translation is implied.

| Key | English | ไทย |
|---|---|---|
| start.namedDevice | Start from a named device | เริ่มจากอุปกรณ์ที่ระบุชื่อแล้ว |
| start.import | Import an evidence package | นำเข้าชุดหลักฐาน |
| start.demo | Explore a synthetic demo | เปิดตัวอย่างข้อมูลสมมติ |
| device.select | Use this device | ใช้อุปกรณ์นี้เป็นจุดเริ่มต้น |
| device.none | No matching record in this catalog | ไม่พบรายการที่ตรงกันในชุดข้อมูลนี้ |
| device.chooseComparator | Select a public comparator to continue | เลือกอุปกรณ์อ้างอิงจากข้อมูลสาธารณะเพื่อดำเนินงานต่อ |
| mode.synthetic | Synthetic engineering example | ตัวอย่างข้อมูลสมมติสำหรับตรวจการทำงานของระบบ |
| mode.public | Public-source engineering draft | ฉบับร่างจากแหล่งข้อมูลสาธารณะ |
| mode.simulation | Simulation — no search is running | กำลังจำลองสถานะ ระบบไม่ได้ค้นข้อมูลจริง |
| mode.importedRun | Imported completed run | ผลการทำงานที่เสร็จแล้วจากไฟล์นำเข้า |
| basis.fact | Source-reported fact | ข้อเท็จจริงตามที่ต้นทางระบุ |
| basis.reported | Reported association | ความเชื่อมโยงที่แหล่งข้อมูลรายงาน |
| basis.inference | System inference | ข้ออนุมานของระบบ |
| basis.unresolved | Unresolved / unjudged | ยังหาข้อสรุปไม่ได้ / ยังไม่ได้ประเมิน |
| patent.candidate | Retrieved candidate | สิทธิบัตรที่ค้นพบเป็นรายการเบื้องต้น |
| patent.disclosed | Source-backed disclosed link | ความเชื่อมโยงที่มีแหล่งเปิดเผยอ้างอิง |
| integrity.span | Exact source text matched | ข้อความตรงกับต้นฉบับ |
| integrity.field | Source field and value matched | ชื่อฟิลด์และค่าตรงกับต้นทาง |
| integrity.limit | This check does not verify the conclusion | การตรวจนี้ยังไม่ได้ยืนยันข้อสรุป |
| candidate.emptyCorpus | This imported run included no patent corpus. Patent coverage is unknown. | รอบงานที่นำเข้านี้ไม่มีชุดข้อมูลสิทธิบัตร จึงยังประเมินความครอบคลุมไม่ได้ |
| candidate.noResults | No candidates returned within this scope and budget | ไม่พบรายการเบื้องต้นภายใต้ขอบเขตและงบรอบนี้ |
| value.unknown | Not recorded | ไม่มีข้อมูลบันทึกไว้ |
| budget.offline | Offline search limits — counts, not money | ขีดจำกัดการค้นแบบออฟไลน์ นับเป็นจำนวนครั้ง ไม่ใช่วงเงิน |
| cost.pending | Cost pending reconciliation | ค่าใช้จ่ายยังรอกระทบยอด |
| state.partial | Some evidence is available; one source needs attention | เปิดดูหลักฐานบางส่วนได้แล้ว มีแหล่งข้อมูลที่ต้องตรวจเพิ่ม |
| save.unsaved | Changes are not saved yet | ยังไม่ได้บันทึกการแก้ไข |
| save.saving | Saving in this browser… | กำลังบันทึกในเบราว์เซอร์นี้… |
| save.local | Saved in this browser | บันทึกในเบราว์เซอร์นี้แล้ว |
| save.memory | Kept in this tab only — download a recovery file | ข้อมูลยังอยู่เฉพาะแท็บนี้ โปรดดาวน์โหลดไฟล์กู้คืน |
| save.conflict | A newer version exists. Your changes are preserved. | มีฉบับใหม่กว่า ระบบยังเก็บข้อความที่คุณแก้ไว้ |
| save.quota | Storage is full. Keep this tab open and download a recovery file. | พื้นที่จัดเก็บเต็ม โปรดเปิดแท็บนี้ไว้แล้วดาวน์โหลดไฟล์กู้คืน |
| source.mismatch | This source revision does not match the citation | ฉบับของแหล่งข้อมูลไม่ตรงกับที่อ้างอิง |
| run.cancelPending | Cancellation requested; waiting for acknowledgement | ขอหยุดงานแล้ว กำลังรอระบบยืนยัน |
| run.scopeComplete | This bounded run ended; completeness is unknown | รอบงานตามขอบเขตนี้จบแล้ว ยังไม่ทราบว่าข้อมูลครบถ้วนหรือไม่ |
| export.omitsEdits | This exporter omits user edits. Choose recovery JSON or a supported edited export. | ตัวส่งออกนี้ไม่รวมข้อความที่คุณแก้ โปรดเลือกไฟล์ JSON กู้คืนหรือตัวส่งออกที่รองรับ |
| export.started | Download started | เริ่มดาวน์โหลดแล้ว |
| request.copy | Copy information requests | คัดลอกรายการข้อมูลที่ต้องขอเพิ่ม |
| privacy.scope | Use permitted public sources. This prototype does not accept private or patient data. | ใช้แหล่งข้อมูลสาธารณะที่มีสิทธิ์ใช้ ต้นแบบนี้ยังไม่รองรับข้อมูลส่วนตัวหรือข้อมูลผู้ป่วย |
| scope.help | Evidence preparation for further review; no medical, legal or investment conclusion is provided. | ใช้เตรียมหลักฐานเพื่อตรวจต่อ ระบบไม่ได้ให้ข้อสรุปทางการแพทย์ กฎหมาย หรือการลงทุน |

Source/tool errors use a short localized sentence with a diagnostic ID; do not expose stack traces, credentials or provider response bodies. Keep the scope explanation in help/overview/export context, not a mandatory modal on every action.

## Themes and accessibility

Theme keys already exist in `ProjectBrief`: `formal-light`, `formal-dark`, `kmitl-inspired`, `ict-inspired`. These are starting **design token proposals**; no official branding or institutional affiliation is claimed. Do not add institutional logos/seals or exact-brand claims without supplied rights/assets. Theme choice changes appearance only, never evidence meaning.

| Role token | formal-light | formal-dark | kmitl-inspired | ict-inspired |
|---|---|---|---|---|
| canvas | `#F5F7FA` | `#0B1220` | `#FAF7F3` | `#F4F8F9` |
| surface | `#FFFFFF` | `#152033` | `#FFFFFF` | `#FFFFFF` |
| text | `#172033` | `#E8EDF5` | `#28201B` | `#102E38` |
| mutedText | `#475569` | `#B8C4D6` | `#62544A` | `#415D67` |
| primary | `#173F6B` | `#9DC6F0` | `#93400A` | `#0A5967` |
| onPrimary | `#FFFFFF` | `#0B1220` | `#FFFFFF` | `#FFFFFF` |
| focusRing | `#215EB0` | `#9DC6F0` | `#93400A` | `#0A5967` |

Use a neutral table/evidence style with restrained orange or teal accents. Define semantic danger/warning/success/info tokens separately and verify their actual background/text combinations in each theme. Never reuse branding color as the only meaning of uncertainty. A “source matched” label is informational even if an accent is used; it does not mean clinical/legal verification.

Target WCAG 2.2 AA behavior: normal text contrast at least 4.5:1; large text and meaningful control boundaries/focus indicators at least 3:1 where applicable; visible keyboard focus and no obscured focus; minimum 24×24 CSS px targets with spacing, preferably 44×44 for primary touch actions. Verify actual implemented pairs, hover/focus/disabled/selected/error states; a token table alone cannot certify accessibility. Thai text uses a Thai-capable system stack (for example Tahoma/Leelawadee UI with system sans fallbacks), comfortable line-height around 1.6 and no forced letter spacing/uppercase. Do not download fonts silently. Long source IDs wrap or copy in full; text remains selectable.

Use semantic headings/forms/tables, labelled buttons and row headers, `aria-expanded` disclosures, logical focus order and Escape/return-focus behavior for dialogs. Do not trap focus in ordinary source panels. `aria-live=polite` reports save/job status once per meaningful transition; blocking submit errors use a summary with focus. Status icons require text. Respect reduced motion; avoid skeleton shimmer and animated counts by default. At 200%/400% zoom keep navigation/actions operable. Switch HTML `lang` for app chrome and mark original quote language where known. Show source ISO dates and timezone when relevant; optional localized dates must not silently change year/calendar. Keyboard-only source opening, comparison, note editing, save recovery and export are completion checks, not optional polish.
