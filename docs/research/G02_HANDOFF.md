# G02 — Scoped completion and handoff

24 ตุลาคม 2026 · owner-authorized G02 only · **status: DONE — planning deliverables**

## ผลที่ใช้งานต่อได้

- สำหรับเจ้าของ: [สรุปภาษาไทย](G02_OWNER_BRIEF_TH.md) อธิบาย prior work, คำถามที่ยังเหลือ, ตัวอย่างงานเภสัช, ผลแบบสนับสนุน/หักล้างและข้อจำกัด ไม่มี owner decision เพิ่มที่ต้องรอ
- สำหรับ agent: [claim/evidence map](../product/CLAIM_EVIDENCE_MAP.md) ครบ C01–C08 พร้อม closest collision, source locator, boundary และ test/falsifier
- [Research-gap freeze v1](G02_RESEARCH_GAP_FREEZE.md) แยก within-project revision กับ confirmed-feedback learning across fresh projects พร้อมกลไกและ equal-information controls
- New reading copies: SkillOpt v2 (879,864 bytes/27 pages) + HarnessOpt-Bench v1 (716,129 bytes/27 pages), รวม 1,595,993 bytes พร้อม local-only manifest; ไม่มี blocked paper ที่ต้องให้ owner ช่วยโหลด
- [Source coverage](G02_SOURCE_COVERAGE.md) ระบุ actual local versions/pages/reading levels ของ 14 selected primary papers และ limits ไม่มี claim ว่าอ่าน/ทดลองครบทุก 35 ฉบับ

**Repository publication note:** the reading PDFs and the G02-only acquisition manifest are local-only working records and are not published in this repository. The official citation/download URLs for the two added sources are recorded in [source coverage](G02_SOURCE_COVERAGE.md); a reader should use those URLs, not expect a repository-local PDF.

## Acceptance ของ GOAL G02

| Requirement | Outcome |
|---|---|
| ใช้ bounded sources เดิมก่อน widening | PASS — selected methods/limits review; ไม่มี broad search; เพิ่มเฉพาะ SkillOpt/HarnessOpt ตาม owner request และดาวน์โหลดสำเร็จทั้งสอง |
| เปรียบเทียบ adaptive search/patent workflow/context-memory/minimal repair | PASS — source table S01–S12 และ claim map |
| แยก revision กับ longitudinal adaptation | PASS — RQ-R/T-R กับ RQ-L/T-L; no-memory/exact-feedback/retrieval-memory/ACE-style และ simple-rule controls |
| Candidate claims มี collision/boundary/falsifier ไม่มี firstness | PASS — C01–C08/X01–X07 |
| Research-gap revision และ exact claim-map output | PASS — exact `docs/product/CLAIM_EVIDENCE_MAP.md`; gap revision เป็น G02-exclusive addendum ใน `docs/research/G02_RESEARCH_GAP_FREEZE.md` เพื่อไม่เขียนทับ shared matrix |
| ทบทวนและแก้ material issue แบบจำกัด | PASS — [G02 verification receipt](G02_VERIFICATION.json): document links/claim-source locators/reading boundaries และ new-PDF integrity; ไม่ rerun global assets/models |

## Concurrency และสิ่งที่ไม่ได้เปลี่ยน

G02 เพิ่มเฉพาะ `docs/product/CLAIM_EVIDENCE_MAP.md`, `docs/research/G02_*` และ `literature-review/g02-additions/` (สอง PDFs/สอง metadata snapshots/sidecar manifest) ไม่แก้ `data/`, `methodology/datasets/`, G01/G04 outputs, root GOAL/AGENTS, shared bibliography/manifest และ original PDFs, raw receipts/results หรือ `memory/project-state.md`/`next-actions.md` ที่ Luna เป็นเจ้าของ

ข้อความ G02 pending ใน shared memory/G01 backlog อาจยังอยู่โดยตั้งใจ ไม่เขียนทับระหว่าง concurrent work ให้ Luna/user merge status จาก handoff นี้เมื่อสะดวก ไม่ต้องรอ merge เพื่อใช้ research freeze นี้ และไม่เรียก shared-file status เก่าว่า source evidence ใหม่

## Interface ถัดไป: Luna G03

ทำ acquisition/data preparation ตาม task ของ Luna ต่อ ไม่จำเป็นต้อง pause เพื่อ review G02 ทั้งคลัง ส่ง actual local paths/version/license/parsed schema-counts/family-publication-date mapping และ complete enterprise linked sample ตาม [interface §8](G02_RESEARCH_GAP_FREEZE.md) Exact expected answers/reference-doc IDs เป็น curator/evaluator data ไม่ปล่อยเป็น runtime gold ของ evaluated system

G05/G06 ใช้ข้อมูลที่ตรวจแล้วคัด independent base groups, separate tracks และ freeze final protocol หลัง calibration G02 ไม่อ้างว่าสถานะ download ล่าสุดของ Luna เป็นอย่างไร ไม่ให้ spending/large-download/cloud approval จาก handoff นี้

## Limits และ next trigger

Novelty ยัง unresolved; no empirical PTP gain, independent expert gold, semantic/clinical/legal feasibility proof หรือ acceptance guarantee Main dataset coverage/sample size/model/prices/budget/effect uncertainty ยังต้องวัดตาม goals ภายหลัง ไม่เป็น blocker ของ planning closure

Paper53 internal-only/reuse pending ตาม ledgerเดิม ไม่มี public citation เพิ่ม หากพบ primary work ที่ตรง equal-feedback patent-project transfer หรือ pilot ชี้ว่า method benefit มาจาก simple rules ให้ re-open เฉพาะ affected claim ไม่เริ่ม global audit ใหม่

ไม่มี implementation, model/API/GPU run, install, credentials, paid compute, publication/push หรือ external message ในงาน G02 นี้
