# Claude UI handoff — entrepreneur/investor workspace รุ่น 2

วันที่ 27 ตุลาคม 2026 · UI implementation เป็นของ Claude ใน branch แยกเท่านั้น
อ้างอิง [owner requirements](REQUIREMENTS_DECISIONS_20261027_V2_TH.md) และ [journey เดิม](USER_JOURNEYS.md)

## คุณค่าที่ต้องเห็นจากหน้าจอ

ช่วยคุณเปลี่ยนโจทย์ธุรกิจที่ยังคลุมเครือให้เป็นทางเลือกที่มีหลักฐาน ข้อจำกัด และขั้นตอนตรวจต่อ โดยไม่ต้องเขียนโค้ดหรืออ่านเอกสารทั้งหมดเอง
นักลงทุนใช้ดู evidence gaps และสมมติฐานของโครงการ ผู้ประกอบการใช้เลือกสิ่งที่ควรทดสอบก่อน ทั้งสองบทบาทยังเป็น persona hypothesis
ไม่มีคะแนน “น่าลงทุนแน่นอน” ราคาเหมาะสมอัตโนมัติ หรือ legal clearance

## Journey และ user stories ตามลำดับ

1. **เริ่มโครงการ**: กรอกเป้าหมาย 1 ย่อหน้า เลือกมุมมอง entrepreneur/investor และเพิ่มเอกสาร ระบบเสนอ brief ให้แก้ ไม่บังคับแบบฟอร์มยาว
2. **รู้จักหลักฐานและองค์กร**: เห็น sources, owned/external/unknown capabilities และ assumptions ยืนยันเฉพาะประเด็นที่เปลี่ยนการตัดสินใจ ตัวที่ขาดไม่หยุด route อื่นทั้งหมด
3. **เปรียบเทียบทางเลือก**: เห็น route cards พร้อม basis, unknowns, trade-offs และ proposed next test แยก source assertion ออกจาก interpretation ไม่มีผลการทดลองที่แต่งขึ้น
4. **อ่าน decision brief**: executive summary ก่อน แล้วขยาย technical plan/evidence drawer ได้ export เป็น draft ที่มี limitations และ source versions
5. **รับมือการเปลี่ยนแปลง**: เมื่อข้อมูลถอน/นโยบายเปลี่ยน เห็น before/after, affected/preserved fields และเหตุผล ตรวจเฉพาะ consequential changes
6. **กลับมาทำต่อ**: history/journal แสดง event, actor, version และ source refs ไม่เก็บ chat transcript โดยอัตโนมัติ และไม่เรียกการแก้เคสเดิมว่า cross-project learning

Acceptance หลัก: เริ่มจาก fixture และไปถึง source-linked draft/change view/export ได้ด้วย keyboard; unknown/blocked ไม่แสดงเป็น success; mock/live/planned แสดงชัดทุกหน้าที่เกี่ยวข้อง

## หน้าจอและ states

| Screen | ข้อมูล/การกระทำ | Empty / loading / error / blocked |
|---|---|---|
| Workspace | projects, brief, version, last change; create/resume | ไม่มีโครงการ → sample SYNTHETIC; ไม่แสดง fabricated progress |
| Brief & sources | brief suggestions, privacy class, source hashes/rights; accept/edit/add | unsupported format → แนะนำชนิดที่รองรับ; parser failure แยกจาก no evidence |
| Capability review | owned/external/unknown, critical queue, locator drawer | unknown ไม่เติมเอง; critical pending ชี้เฉพาะ route ที่ได้รับผล |
| Options | comparable routes, reasons, gaps, next test | no route → อธิบายหลักฐานที่ขาด; loading ยกเลิกได้เมื่อ backend รองรับจริง |
| Decision brief | summary, assumptions, source-linked sections, draft export | readiness ≠ approval; release export ต้องมี review record |
| Changes | current vs prior version, invalidation reason, preserved content | version conflict → refresh/compare ไม่ silent overwrite |
| History | revision/event journal, rollback proposal, cost status | billing unknown → blocked; ห้าม reset journal เพื่อรันใหม่ |
| Run readiness | matrix/model/route/cost envelope/status | live disabled จน backend gates ผ่าน ไม่อ่าน key เพื่อแสดงหน้า |

## Contracts ที่มีจริง กับ HTTP API ที่เสนอ

มีจริง: `src/patent_to_pilot/product/contracts.py` ประกอบด้วย `ProjectBrief`, `EvidenceCard`, `ReviewDecision`, `JobStatus` เป็น closed Pydantic schemas
ใช้ `model_json_schema()` สร้าง fixtures/type adapters ได้ ฟิลด์เพิ่มต้องตกลง backend ก่อน ไม่ใช้ dictionary เปิดรับ evaluator fields

**ยังไม่มี product HTTP API** ตารางต่อไปเป็น proposed integration contract ไม่ใช่ endpoint ที่เรียกได้แล้ว

| Proposed endpoint | Input/output | Failure rules |
|---|---|---|
| POST /projects | ProjectBrief → project/version | 422 invalid schema, no implicit live call |
| GET /projects/{id}/evidence | EvidenceCard[] | no evaluator/future/secret export |
| POST /projects/{id}/reviews | ReviewDecision | expected_version mismatch → 409; scope/evidence refs required |
| GET /jobs/{id} | JobStatus | blocked/failed มี reason; unknown_pending ไม่แปลงเป็น $0 |
| GET /projects/{id}/changes | versioned before/after + affected/preserved refs | shape ต้องรอ backend adapter; no invented current result |
| POST /projects/{id}/exports | reviewed version → draft artifact | critical confirmation/rights/privacy gate; no legal endorsement |

Pepo เตรียม schemas/fixtures; Luna รับ server/job/idempotency/auth integration หลังเลือก deploy/access model Claude ใช้ mock adapter ชื่อชัดและสลับ backend ตาม contract ได้ ไม่สร้าง API ฝั่งเดียว

## Visual และ accessibility

- Minimal/formal: typographic hierarchy ชัด พื้นที่ว่างพอ อ่าน evidence ได้จริง ไม่ใช้ dashboard widgets เพื่อเติมพื้นที่
- Theme identifiers: formal-light, formal-dark, kmitl-inspired, ict-inspired สองรายการหลังเป็น placeholder จนตรวจ official identity ไม่ใช้ตราหรืออ้าง affiliation
- ภาษา en/th เป็น configurable draft ยังไม่ใช่คำยืนยันภาษาเริ่มต้น
- WCAG 2.2 AA เป็น acceptance target: keyboard, visible focus, labeled controls, contrast, reduced motion, responsive 360px/tablet/desktop และสถานะมีข้อความไม่ใช้สีอย่างเดียว
- ไม่มี key input ใน mock UI, ไม่มี secret ใน screenshot/log/browser storage; credential setup อยู่นอก demo
- Synthetic badge ต้องคงอยู่ใน cards, exports และ screenshots ข้อมูล real source ต้องมี provenance แทน

## Demo fixtures และ review

ใช้ `methodology/development/synthetic-20261027-v2/current/` ทีละไฟล์เท่านั้น ไม่ mount `corpus.json` ซึ่งมี future events
SYN-000-0 แสดง unknown/withdrawal, SYN-001-0 policy revision, SYN-002-0 contradiction, SYN-003-0 partner delay; ทั้งหมดแต่งเพื่อพัฒนา ไม่ใช่ลูกค้าหรือผลวิจัยจริง
Claude ส่ง screenshots ที่แสดง default, empty, error, blocked, change diff และ narrow viewport พร้อม branch/commit ให้ Pepo review ก่อน merge
ไม่แก้ comparison/evaluator/protected histories/G11 เพื่อให้ UI demo ดูผ่าน
