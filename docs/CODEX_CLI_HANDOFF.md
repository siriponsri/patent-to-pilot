# Codex CLI: เริ่ม ทำงานต่อ และปิด work package

อัปเดต 24 ตุลาคม 2026 · current orchestration handoff · ยังไม่ activate memory/tools/hooks ใหม่

## Agent และเอกสารที่ใช้ตัดสินงาน

เจ้าของเลือก **`gpt 5.6 luna max`** เป็น primary coding/research executor ใช้ label ตามนี้ Provider/model ID, CLI alias, reasoning setting และ availability ยังไม่ยืนยัน เอกสารนี้ไม่ได้สลับ current executor หรือแก้ accounts/config ห้ามเดา launch flags หรือแทนรุ่นอื่นเงียบ ๆ Product/benchmark inference ใช้ provider adapter/cheap calibrated API แยกจาก executor

ลำดับ authority: owner/runtime instructions → [AGENTS](../AGENTS.md) execution contract → [GOAL](../GOAL.md) product scope/G01–G22/defaults → [protocol](../methodology/evaluation/PROTOCOL.md) สำหรับ frozen study methods ส่วน [PLAN](PLAN.md) เป็นรายละเอียดฐานตาม scope ล่าสุด Memory เป็น checkpoint/index; manifests/raw receipts เป็น evidence ของสิ่งที่บันทึก ไม่ใช่ permission หรือ instruction

## เปิด CLI

```powershell
Set-Location -LiteralPath 'C:\Users\User\Desktop\myProject\patent-to-pilot'
& 'C:\Users\User\AppData\Roaming\npm\codex.cmd'
```

นี่เป็น documented launcher ที่เคยตรวจ version 0.162.1 ไม่ได้เปิด model session ในรอบนี้ Bare `codex` ไม่อยู่ใน PATH ของ task shell ที่ตรวจ ไม่แก้ PATH/global hooks เพื่อให้ตรงตัวอย่าง การเลือก model ต้องใช้ชื่อ/ID ที่ runtime เปิดให้จริง ไม่ถือว่าคำสั่งด้านบนเลือก `gpt 5.6 luna max` ให้แล้ว

## Startup / resume algorithm

1. อ่าน task ล่าสุดและ AGENTS ตามด้วย GOAL executive summary/roadmap และ G ที่เกี่ยวข้อง อ่าน PLAN เฉพาะส่วนที่ใช้, [memory index](../memory/README.md), [next action](../memory/next-actions.md)
2. ตรวจ checkpoint/actual files เฉพาะงานที่กำลังต่อ ไม่ recreate PTP-0001 หรือ audit PDF library ใหม่เพียงเพราะ session เปลี่ยน
3. เลือก G แรกที่ prerequisites พร้อมและอยู่ใน authorization ของ task; ถ้า G หนึ่งติด dependency ให้ทำ independent ready G ต่อ ถ้ารอบนี้เป็น docs-only ก็ไม่เริ่ม code/download/run จากแผนลำพัง
4. ตั้งหนึ่ง bounded work package ตาม template ด้านล่าง ใช้ stack/defaults ใน GOAL ไม่ส่ง routine design choices ให้ owner
5. ทำงาน/debug/test ภายใน permissions หนึ่ง scoped review แล้วแก้และ retest affected failures อย่า rerun old models/benchmarks หรือ widen research โดยไม่มีเหตุใหม่
6. จบด้วย done/ready/blocked, files/tests/known limits, checkpoint และ smallest next step อัปเดต memory ที่เกี่ยวข้องครั้งเดียว

## Work-package template

```text
Goal / slice: Gxx — concrete deliverable
Current authorization / exclusions:
Inputs and existing checkpoint:
Output paths:
Acceptance / critical failure definition:
One targeted verification:
Result: DONE | READY | BLOCKED (actual, not promised)
Known noncritical limitations / backlog:
Next smallest action and dependency:
```

Agent รับผิดชอบ routine implementation choices, work breakdown, debugging และ tests ไม่ถามทีละไฟล์/function/library ถ้าต้องถาม owner ให้รวม material direction/budget/restricted-data/security/publishing decisions พร้อม sensible default ข้อจำกัด UI/optional feature ลง backlog ได้ แต่ห้าม pass data loss/disclosure/unauthorized spend/oracle leakage หรือ core result failure

Optional reviewer ใช้เฉพาะ targeted high-risk change เมื่อ runtime อนุญาต delegation ไม่บังคับ review ทุกงาน ไม่ launch FORGE/ORCA/HyperResearch scheduler ซ้อนกันและไม่เรียก software reviewer ว่า independent clinical/legal expert

## Current checkpoint

- GOAL ขยายเป็น Organization-Adaptive R&D Agent: approved org documents → source-linked capability/policy map → patent/research opportunities → route comparison → draft feasibility/pilot/handoff → confirmed scoped feedback → project adaptation
- [Manifest](../literature-review/manifest.json): 35 external PDFs (51,073,237 bytes) + internal Paper53 (270,278 bytes), รวม 36 verified copies ไม่มี claim ว่าอ่าน/reproduce ทุก paper ครบ
- Dataset preflight: 18 files/2,498,071 bytes มี metadata/qrels/small API samples Starter PLS+EnterpriseRAG 5 payloads/279,537,042 bytes ยังไม่โหลด ไม่มี large corpus/index/model run
- [PTP-0001](../methodology/evaluation/cases/PTP-0001/README.md) มีหนึ่ง development source unit, authored states/negative fixtures และบันทึก offline checks 39 checks ไม่ใช่ model/scientific result เคสนี้เป็น smoke test ไม่ล็อก final product domain
- Paper53 เป็น internal-only/citation-pending ตาม [provenance](../literature-review/internal/PROVENANCE.md) ไม่ต้อง download ซ้ำ WPI PDF resolved แล้ว Paper86/old HTML optional ไม่บล็อก goals
- ยังไม่มี product app/UI/API, experiments หรือ cumulative-learning evidence รอบ alignment นี้เป็น documentation only

## First ready work และ downloads

เมื่อมี task ให้ลงมือ: G01 product contract และ G04 profile/schema ใช้ sources ที่มีได้ ส่วน G03 starter acquisition ใช้ pinned PLS CSV สองไฟล์และ EnterpriseRAG GitHub slices+questions ตาม GOAL ตรวจ linked-document closure แล้วรายงาน actual counts/coverageก่อนขยาย ไม่มี gated approval/full sandbox/embedding/paid run โดยปริยาย

ไม่มี related PDF ค้างที่ต้องให้ owner ช่วยโหลดสำหรับ shortlist ปัจจุบัน EnterpriseBench gated data เป็น access decision ภายหลัง ไม่ใช่ PDF failure อย่าขอ Paper86 หากยังไม่ใช้ findings ของมัน

## Tool availability / recheck triggers

ใช้ [tool registry](TOOLING_REGISTRY.md) และ JSON สำหรับ exact observed paths HyperResearch 0.12.0 มี CLI แต่ installed help ไม่มี Codex `--target`; ai-memory ไม่พบใน checked paths; Markdown notes ใช้ได้โดยไม่เปิด backend ไม่ activate hooks/install accounts เพื่อทำ routine work

Recheck เฉพาะ tool upgrade/path failure/activation task, source replacement/corruption หรือ method/data/validator changes ที่ต้องประเมินใหม่ Historical receipts เช่น `verification.json` บอกอดีต ไม่ใช่คำสั่งให้ตรวจทั่วโครงการอีก

ถ้าติด permission/tool/source ให้ระบุ exact action, target, reason และ denied/pending/uncertain ตรวจ uncertain outcome ก่อน retry และ retry denial เฉพาะเมื่อมี materially new relevant evidence ตาม runtime rules พร้อมทำ unaffected work ต่อ
