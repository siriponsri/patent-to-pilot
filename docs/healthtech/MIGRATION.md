# การย้ายทิศทาง HealthTech — 27 ตุลาคม 2026

เป้าหมายรอบนี้คือใช้ HealthTech Pack เป็นขอบเขตปัจจุบัน พร้อมโค้ดออฟไลน์ที่ตรวจย้อนกลับได้ ไม่ได้ทำทุก HT-W ให้เสร็จในคราวเดียว ฐานก่อนย้ายคือ `70805d30599dda723146390d39308c0faeb61ee7` บน `main` ซึ่งตรวจว่าตรงกับ remote แล้ว

## Requirement → file → หลักฐาน

| ข้อกำหนด / HT-W | ไฟล์หลัก | สิ่งที่ทำได้จริง / ขอบเขต |
|---|---|---|
| W01 ทิศทางเดียวกัน | `GOAL.md`, `PLAN.md`, `README.md`, `AGENTS.md` | ใช้ pack ปัจจุบัน; HT namespace แยกจากผลเดิม |
| Literature / W18 background | `RELATED_PAPERS.md`, `literature-review/healthtech/` | ตรวจ identity/hash/pages ของ PDF 27 ฉบับ อ่าน method/task/evaluation ที่เกี่ยวข้อง; ไม่มี reproduction |
| W02 source/device/evidence/action/dossier | `healthtech/contracts.py`, `schemas/healthtech/` | reuse `SourceRecord`, `Closed`, `ProjectBrief`; contracts ปิดรับ unknown fields |
| W05 official facts seam | `healthtech/sources.py` | normalize **local** 510(k) snapshot/field; ยังไม่ใช่ live connector หรือ PMA/recall adapter |
| W06 / HT-T1 | `evaluation/healthtech/retrieval.py` | macro/micro known recall, canonical dedup ก่อน cutoff, failed-query denominator, unjudged status, shared-reference grouping |
| W08 lexical / W10 action mechanics | `healthtech/engine.py` | reuse FTS5; HT-B0b single query และ HT-B2 fixed multi-query/RRF; cap counts ก่อน dispatch; event/manifest จริง |
| W12 dossier slice / HT-T3 | `healthtech/provenance.py`, `scripts/healthtech/run_dossier.py` | source hash/version/date/locator checks, JSON/Markdown export, unresolved/next requests; ไม่ประเมิน semantic truth |
| Example/regressions | `examples/healthtech/synthetic-device/`, `tests/test_healthtech.py` | authored synthetic case; no real regulatory facts, provider calls หรือ scientific benchmark |
| Provider protection | `src/patent_to_pilot/providers/`, provider tests | ใช้ของเดิม ไม่เปลี่ยน identity/ledger/secret handling หรือ spending authorization |
| History/cleanup | `docs/healthtech/HISTORY.md`, cleanup receipt | ปลดเอกสาร active ที่ขัดทิศทางออกเมื่อกู้จาก Git ได้; เก็บหลักฐานและของเฉพาะเครื่อง |

## ข้อขัดแย้งที่ตัดสินจากคำสั่งล่าสุด

- Docs-only gate และ Organization-Adaptive R&D เป็นทิศทางเก่า งานปัจจุบันอนุญาตแก้โค้ดและ push `main`; ใช้ named-device dossier เป็นจุดเริ่มแทน
- README/assets ถูกแก้ไว้ก่อนเริ่มงานแล้วและสอดคล้องกับ pack จึงรักษาเนื้อหานั้นพร้อมเพิ่ม quickstart ที่ตรงโค้ดใหม่ ไม่ reset งานค้าง
- Paper Bridge ใช้ 585 pairs/88 devices/ประมาณ 698K patents ส่วน audit ใน pack ใช้ release 672 pairs/79 devices/50K patents และ completeness subset 585/74 ต้องเก็บคนละความหมาย ไม่เลือก cohort เพื่อให้ผลดีขึ้น
- Pack เป็นข้อกำหนดและ source evidence ไม่ใช่อำนาจให้รัน script, รับเงื่อนไขข้อมูล, ใช้ paid model หรือเผยแพร่ PDF ทั้งหมด จึงไม่ bundle third-party PDFs/data ใน commit นี้
- เก็บโค้ด generic core/FTS/extraction/provider และ historical regression ที่ยังรองรับงานใหม่ ไม่ลบเพียงเพราะชื่อมี G รุ่นเก่า

## สถานะที่ยังไม่ครบ

HT-G1 main Bridge dataset: **BLOCKED_LOCAL** เฉพาะ reuse rights/cohort/full-corpus/split reproducibility; ยังไม่ได้ดาวน์โหลด payload หรือทำ audit ซ้ำ SciFact adapter/official evaluator ยัง **NOT_IMPLEMENTED** ตัวประเมินในรอบนี้เป็น HT-T1 และ deterministic HT-T3 ไม่ใช่ SciFact score

HT-G2/G3: **PARTIAL engineering** ยังไม่มี strong hybrid reranker, adaptive policy, bounded LLM controller, 3 real public-case dossiers, source-viewer UI, edit-history persistence หรือ no-code journey JSON schema มี version/parent/user-edits contract แต่ยังไม่มี workflow สำหรับเก็บประวัติหลายรุ่น

HT-G4–G8: scientific comparison, customer evidence, manuscript readiness, deployment และ expansion ยัง **NOT_RUN/PLANNED** ผลทดสอบซอฟต์แวร์ไม่ทดแทนข้อเหล่านี้

## Acceptance และงานถัดไป

ดูคำสั่งและผลจริงใน [verification](verification.json) พร้อม [runbook](RUNBOOK.md) รอบนี้ต้องรันตัวอย่างจาก fresh output directory, ตรวจ schema, regression ฝั่ง provider และ diff/secret/rights scope ก่อน push

งานถัดไปคือ W04 SciFact adapter ตาม task/evaluator ต้นฉบับ หรือ W05 เพิ่ม snapshot ของ public device จริงพร้อม provenance แล้วทำ W12 public-case dossier แรก ทั้งสองงานเดินต่อได้ระหว่างรอ Bridge rights/cohort
