# Claude UX/UI handoff — Patent-to-Pilot

สถานะ: **PROPOSED G14 UI BRIEF; ไม่มี UI/API implementation ใน repo**
ฐานหลัก: [PATENT_TO_PILOT_MASTER_PLAN_TH.md](PATENT_TO_PILOT_MASTER_PLAN_TH.md), [PRODUCT_CONTRACT.md](PRODUCT_CONTRACT.md), [USER_JOURNEYS.md](USER_JOURNEYS.md)

เอกสารนี้เป็น brief delta สำหรับทำ mock UI ต่อจาก contract เดิม ไม่สร้าง endpoint หรือเปลี่ยนความหมายของ evidence/history/budget เอง ใช้ public/fictional fixtures เท่านั้น ห้ามส่ง private patent/docs, evaluator-only oracle, key หรือ live output เข้า mock

## P0 workflow

ผู้ใช้ต้องทำ flow ต่อไปนี้ได้โดยมี artifact และสถานะตรวจได้ทุกขั้น:

1. เริ่ม project/brief ด้วย goal, scope, output target, allowed sources และ brief version
2. ตรวจ source snapshot, capability/policy map และ confirmation queue
3. เปรียบเทียบ opportunities/routes ที่มี evidence links, constraints, unknowns และ conflicts
4. สร้าง draft pilot/R&D/RA/Clinical Research handoff พร้อม risks, reviewer questions และ next action
5. รับ confirmed change แล้วแสดง before/after revision, affected/preserved fields และ history
6. export draft pack ที่ trace source IDs/locators ได้ และติด `ready_for_review` เฉพาะเมื่อ artifact/traceability checks ผ่าน

ระบบไม่มี authority อนุมัติ clinical, regulatory, legal, patentability, FTO หรือ feasibility โดยอัตโนมัติ

## Evidence inspector

แสดง source ID, version, locator, quote ที่มีจริง, basis (`source_fact`, `stipulation`, `interpretation`, `unknown`), evidence state (`supported`, `contradicted`, `missing`, `unknown`), conflict/withdrawn/ambiguous และ confirmation checkpoint แยกจาก prose สรุป หาก evidence ไม่พอ ให้แสดงรายการที่ขาดและคง route/field เป็น `unknown` หรือ `blocked_by_missing_evidence` ตาม contract

## UI states and behavior

| State | สิ่งที่ผู้ใช้ต้องเห็น | ข้อห้าม |
|---|---|---|
| loading | step, scope, cancel/reload affordance และ stale-data warning | ห้ามแสดง fake progress เป็น result |
| empty | missing prerequisite และปุ่ม/next action ที่ทำได้ | ห้ามเติม metric เป็น 0 |
| error | safe error code, retry eligibility, correlation/run ID และ next action | ห้าม stack trace, request header หรือ key |
| blocked | blocker type, affected artifact, owner action ที่จำเป็น และ preserved work | ห้ามกลบ blocker ด้วย success banner |
| unsaved | dirty fields, save/discard/recover choice และ version conflict | ห้าม overwrite history เงียบ ๆ |
| ready_for_review | completeness/traceability checks และ unresolved list | ห้ามเรียกเป็น approved/final |

Responsive/keyboard behavior ต้องอ่านได้ที่ narrow viewport, มี focus order, visible focus, semantic labels และไม่พึ่งสีอย่างเดียวในการแยก state

## Real contracts versus proposed view model

**REAL PYTHON/PYDANTIC CONTRACTS** อยู่ที่ `src/patent_to_pilot/core/models.py` และ `src/patent_to_pilot/integration/pipeline.py`:

- `SourceRecord`: `source_id`, `source_type`, `uri`, `version_label`, `license_note`, optional `locator`, `sha256`, `retrieved_at`, `limits`
- `OrganizationProfile` / `OrganizationCapability`: profile/version/status, `owned|external|unknown`, `basis`, `confirmation_state`, source refs/locators, unknowns
- `ConstraintRecord`: organization, scope, `allowed|prohibited|conditional|unknown`, statement, basis, effective date, confirmation, source refs, supersedes
- `EvidenceRecord`: source/locator/claim, role, `supported|contradicted|missing|unknown`, optional quote/offsets
- `RouteRecord`: project, label, `draft|candidate|blocked_by_missing_evidence|unknown|ready_for_review`, evidence IDs, constraint IDs, unknowns
- `ChangeRecord`: entity/version before-after, affected/preserved fields, reason, source refs
- `FeedbackRecord`: scope, target, statement, confirmation state, source refs, effective date

Provider/accounting fields are real in `src/patent_to_pilot/providers/openrouter.py`: `ProviderRequest` carries prompt/schema/tools/parameters, input estimate, output cap, cost bound and request ID; `ProviderResponse` carries requested/reported broker/upstream/model identity, usage, cost, retry count, schema result, actual debit, budget breach and attempt receipts. Current executable entry points are `scripts/dispatch_provider_pilot.py`, `scripts/run_provider_recovery.py` and `scripts/run_provider_pair.py`.

Any HTTP API, project view model or permission matrix below is **PROPOSED CONTRACT**, not an existing endpoint:

```text
project_id: string
revision: integer
run_mode: offline | mock | live
job_state: loading | draft | blocked | ready_for_review | failed | complete
evidence_links: EvidenceLink[]
unknowns: UnknownItem[]
approval_state: not_required | pending | confirmed | rejected
permitted_actions: string[]
```

Null/error semantics: missing optional values remain `null`; unsupported values remain explicit `unknown`; empty lists mean no recorded items, not “all clear”; cost fields distinguish `actual`, `reserved`, `estimate`, and `unknown_pending`; `0` is never a fallback for missing evidence, cost, confidence, or outcome.

## Journal, fixtures and support views

Journal is a traceable user/research activity history keyed by project/revision/artifact version. It is not automatic transcript capture and not product learning. Show event type, actor class, timestamp, source/version references, change ID and next action; redact credentials/private text.

Mock/demo fixtures must use authored fictional profiles and source IDs that resolve through the existing fixtures. The demo may show a route change and typed diff, but must not embed expected answers, hidden dependency graphs, evaluator source hints or fabricated live provider output.

Budget/key/run-readiness is a support view: show approved scope, endpoint/model/route, attempt slots, retry policy, reservation, actual debit, unknown billing and stop reason. Do not turn the product into a billing dashboard or display key material. `READY_FOR_OWNER_APPROVAL`, `PAIR_FAILED`, `BLOCKED_UNKNOWN_PENDING` and `NOT_RUN` remain distinct.

## Handoff acceptance for Claude

- Build a mock screen flow from the P0 list using public/fictional data only.
- Keep real field names above and label every invented adapter/view object `PROPOSED CONTRACT`.
- Preserve source locator/basis/unknown/conflict and before/after history semantics.
- Represent loading, empty, error, blocked, unsaved and ready-for-review states without stack traces or secrets.
- Do not claim that a provider call, FastAPI endpoint, scientific pilot or product learning runtime exists.
