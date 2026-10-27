# Claude UI handoff draft — minimal + formal
วันที่ 27 ตุลาคม 2026 · **DESIGN/CONTRACT DRAFT ONLY — ไม่ได้ implement UI**

เอกสารนี้เพิ่มจาก [handoff เดิม](CLAUDE_UI_HANDOFF_TH.md) และ [requirements register](REQUIREMENTS_DECISIONS_20261027_V1_TH.md) เจ้าของยืนยัน minimal + formal แล้ว ส่วนภาษา EN/TH, palette, audience, collaboration และ delivery endpoint ยัง PENDING ห้าม freeze สิ่งเหล่านั้นจากข้อเสนอในเอกสารนี้

## งานที่ต้องช่วยผู้ใช้ทำ

เปลี่ยน approved brief/sources เป็น source-linked organization map, ทางเลือกและ draft R&D handoff แล้วรู้ว่า constraint/evidence ใหม่กระทบส่วนใด พร้อมดู history และ export
Budget/run controls เป็น support view ไม่ใช่แกนผลิตภัณฑ์ และไม่มี patient/clinical-approval workflow ที่ได้รับมอบหมาย

## Visual direction ที่ยืนยันกับสิ่งที่ยังเสนอ

**ยืนยัน:** minimal + formal  
**เสนอเพื่อทบทวน:** พื้นที่อ่านเอกสารที่สงบ, hierarchy ชัด, whitespace, typography ใช้งานจริง, accent น้อย, ตารางเปรียบเทียบอ่านง่าย, motion เฉพาะที่ช่วยรู้ state  
**ยังไม่ยืนยัน:** สี/HEX, fonts, dark mode, EN/TH/default language, final navigation, multi-user roles และ device priority

ใช้ existing logo/assets เป็น reference ของ repo ได้ ไม่อนุมานว่าเป็น brand palette ที่เจ้าของเลือกแล้ว ห้ามเพิ่ม affiliation, badges, clinical/legal trust marks หรือ fabricated metric cards
คง source quotes ภาษาเดิม ถ้ามี translation ต้องเป็น separate interpretation ไม่แก้ข้อความ/hash/offset ของหลักฐาน

## Navigation และ screens ที่เสนอ

| Screen | Data ที่ต้องเห็น | Actions | Acceptance/สิ่งที่ต้องแยก |
|---|---|---|---|
| U01 Projects/brief | project ID, goal/scope, output target, revision, mode | create/edit draft, open project | บอก unsaved/version conflict; sample ไม่ใช่ live project |
| U02 Sources | source ID/type, snapshot/version/date, permission/license note, ingest status, missing fields | inspect/import ตาม backend ที่มี, filter, open witness | source assertion ไม่ใช่ scientific truth; unavailable sourceมี next action |
| U03 Organization map | owned/external/unknown capability, policy scope/effective version, basis, confirmation queue | review/confirm critical interpretation, inspect source | public expertise ไม่เท่ากับ ownership/availability; ไม่ require approvalทุก field |
| U04 Opportunities/options/routes | option/route IDs, explicit check states, evidence links, trade-offs, unknown/conflict | compare/select draft option, inspect claim | “passes explicit check” ไม่แสดงเป็น “feasible/approved” |
| U05 Draft handoff | evidence ledger, proposed tests, risks, unresolved/reviewer questions | preview/edit permitted narrative, send to human review later | proposed test แยกจาก completed result; ready_for_review ไม่ใช่ approval |
| U06 Change/diff | confirmed event/scope, before/after versions, affected/preserved fields, reason/source | preview impact, confirm event, inspect changed claim | unrelated fieldsยังอยู่; withdrawalทำ current support unknownโดยเก็บ history |
| U07 History/activity journal | event ID/time, actor class, revision/artifact references, reason, review state | filter, inspect prior version, proposed restore request | append-only semantics; journalไม่ใช่ automatic transcript capture หรือ model learning |
| U08 Exports | selected artifact/version, provenance index, unresolved list, rights/limitations | export supported JSON/MD/HTML when integrated | PDF/CSV อื่นเป็น requirement pending; ไม่มี invented endpoint/result |
| U09 Run readiness/support | offline/mock/live, approved scope, reserved/actual/estimated/unknown cost, remaining slots, stop reason | inspect plan; execute disabledเมื่อไม่มี backend approval | key ไม่อยู่ frontend; funded balanceไม่ใช่ cap; unknownไม่เป็น 0 |

Navigation grouping เป็น proposal ที่เปลี่ยนได้โดยไม่กระทบ evidence contracts ไม่ต้องสร้างทุก screen เป็น route แยกถ้าผู้ใช้ทำ core journey ได้ชัดเจนกว่า

## Evidence และ uncertainty presentation

Inspector ควรเปิดจาก claim/option/diff ได้ทันที แสดง source ID/version, locator, quote, role/unit, basis และ evidence state ที่มีจริง
ไม่สร้าง confidence percentage หาก backend ไม่มีค่าที่ validated แยก supported literal evidence, conflicting evidence, missing evidence, withdrawn source และ interpretation ไม่ใช้สีอย่างเดียว
Null หมายถึงไม่มีค่าที่บันทึก ไม่ใช่ negative/zero Empty list ไม่ใช่ “ปลอดปัญหาทั้งหมด” และ unknown_pending cost ไม่ใช่ฟรี

## Interaction states ที่ต้องออกแบบก่อน polish

| State | สิ่งที่ผู้ใช้ต้องรู้/ทำต่อ | ข้อห้าม |
|---|---|---|
| loading | ขั้นที่กำลังทำ, scope และ cancel/reload ที่ backend รองรับ | fake progress หรือแสดง draft เป็น final |
| empty | prerequisiteที่ขาด และ next action ที่ทำได้ | เติม metrics เป็น 0 หรือ auto-generate facts |
| validation error | field/reason ที่แก้ได้ โดยคง input ที่ผู้ใช้กรอก | stack trace/key/headers |
| source conflict/withdrawal | affected claims, versions และเหตุผล | silently choose convenient value |
| blocked | scopeที่ถูก blockและส่วนที่ยังทำต่อได้ | global success/blocked bannerที่กลบ route-local states |
| unsaved/conflict | dirty fields, expected revision, save/discard/recover | overwrite concurrent versionเงียบ ๆ |
| ready_for_review | completeness/source checksและ unresolved list | “approved” หรือ clinical/regulatory badge |
| failed/cancelled | retained partial work, retry eligibility, safe run/error ID | auto retry ที่หลุดงบหรือรีเซ็ต ledger |

State labels ของ UI เป็น view model ที่เสนอ ต้อง map ไป real backend records ไม่เพิ่ม enum ใหม่ใน accepted core โดย Claude เอง

## Human review และ collaboration

เจ้าของ/ผู้ทบทวนยืนยัน critical organization assumptions และ change scope ส่วน R&D/RA/Clinical Research ตัดสิน scientific/regulatory/human-study matters เอง
Reviewer approval เป็น stateถัดจาก ready_for_review ไม่ใช่ prerequisite สร้าง draft ทุกครั้ง
จำนวนผู้ใช้, named roles, assignments, auth และ permission matrix รอ R02/R03/R04 ก่อนออกแบบ production collaboration ไม่สร้าง team admin/network exposureโดยปริยาย

## API/data boundaries สำหรับทำ mock

**มีจริง:** Python/Pydantic records ใน `core/models.py`, `integration/pipeline.py` และ append-only repository; bounded CLI export JSON/MD/HTML  
**ยังไม่ใช่ existing endpoints:** HTTP API, job service, permission system และ frontend view objects

ข้อเสนอ adapter:
- ProjectView: project_id, revision, brief, mode, review_state, unknowns
- EvidenceView: evidence_id, source/version/locator/quote, basis, evidence_state
- RevisionView: change_id, before_version, after_version, affected/preserved fields, reason
- RunView: run_id, mode, status, permitted_actions, cost components, safe errors

Proposed operations ไม่ใช่ URL ที่ implement แล้ว: create/read project, source intake/status, capability confirmation, draft/revision job, source lookup, activity history และ export
หากต้องเสนอ REST routes ให้ระบุ DRAFT CONTRACT ชัด มี expected revision/idempotency/status semantics ไม่เรียกใช้จน backend contractตรงกัน
Mock fixtures ใช้ public/fictional dataและ statusที่ตรวจได้ ไม่มี evaluator-only answers/gold graph/future changes หรือ fabricated live response

## Accessibility และ responsive acceptance

ใช้ keyboardได้, focusเห็นชัดและเรียงตามงาน, semantic headings/labels, errorเชื่อมกับ field, text contrastอ่านง่าย, ขยายข้อความได้, tablesมี header และ stateไม่พึ่งสี/hoverอย่างเดียว
Diff แบบสองคอลัมน์บนจอกว้างต้องมี narrow-view equivalent ที่รู้ว่า old/new คืออะไร ไม่ทำ source inspectorบัง contextทั้งหน้า
Source quote/pathยาวต้องอ่าน/คัดลอกได้ ไม่ซ่อน essential uncertaintyไว้ใน tooltip
Claude ต้องตรวจภาพจริงและ critical mock journeyก่อนส่ง owner review; ไม่ต้องใช้ paid providerเพื่อทดสอบ layout

## Demo acceptance ที่ตรวจได้โดยไม่ใช้ API

brief → source/org map → compare options → draft → scoped change → before/after → history/export preview ทำงานกับ fixtures
Silicon-substrate prohibition กระทบเฉพาะ optionที่เกี่ยวข้อง, project-name no-opไม่ rewrite technical fields, withdrawalทำ dependent support unknown, yield/costที่ไม่มีหลักฐานยัง unknown
ป้าย demo/mock ต้องเห็นชัด ทุก screenshot/resultมี modeและversion ไม่มี clinical/legal claims หรือ fake scientific scores

## รออะไร และใครรับต่อ

- รอ owner answers R01-R05 ก่อน freeze UI scope/language/theme/collaboration
- Claude รับ UI mock/design และ state/accessibility checks หลัง briefได้รับคำตอบ ไม่ implement backend/evaluatorหรือแก้ frozen fixtures
- Luna รับ API adaptation/integrationและ contract testsหลัง scopeชัด
- Pepo/GPT Work เตรียม fixtures/contracts/checklistsแบบ offlineได้ตาม scope ไม่ส่งข้อมูลไป Claude accountโดยอัตโนมัติ
