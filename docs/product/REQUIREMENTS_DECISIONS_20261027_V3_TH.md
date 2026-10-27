# Patent-to-Pilot — current requirements รุ่น 3

วันที่ 27 ตุลาคม 2026 · สถานะ **DIRECTION_APPROVED / LONG_RUN_AND_BUDGET_EXPANSION_PENDING**

อ่าน [proposal ฉบับเต็ม](../research/TRANSFER_OR_RETEST_PROPOSAL_20261027_V3_TH.md) ก่อนเริ่มงานใหม่ เอกสารนี้เป็น addendum ไม่แก้ประวัติ G01–G22, protocol หรือ claims ของรุ่นก่อน

## สิ่งที่ยืนยันแล้ว

- Product vision: **Capability-Constrained Cross-Domain Technology Transfer** ผู้ใช้เป้าหมายเป็น entrepreneur/investor ที่ต้องการ technical evidence และ uncertainty มี R&D เป็นเครื่องยนต์ ไม่ใช่ automated investment execution
- Paper แรกที่เลือกศึกษา: **Transfer or Retest? Calibrated Knowledge Transfer and Experimental Design under Capability Shift** เริ่มจาก measured solvent/material หรือ operating-regime shift
- User journey: objective/capabilities → mechanisms/incompatibilities → Transfer/Retest/Insufficient Evidence → consequential experiment-plan review → measured-result import → updated comparison → evidence pack
- UI minimal/formal, EN/TH configurable และ KMITL/ICT-inspired themes เป็น design direction ของข้อเสนอนี้ ไม่อ้าง official identity/endorsement Claude ทำ UI ใน branch แยกก่อน reviewed merge
- Scoped backend/tests/docs main push ยังคงได้รับอนุญาตตามขอบเขตเดิม หลัง checks ไม่มี force push หรือ deploy โดยปริยาย

## สิ่งที่ยังไม่ได้อนุมัติ

| รายการ | สถานะ |
|---|---|
| งบ OpenRouter ใหม่ที่มีอยู่ | USD 5 ตาม approval เดิม ไม่ใช่อำนาจเริ่ม research scope ใหม่นี้โดยอัตโนมัติ |
| LEAN USD 25 รวม / RECOMMENDED USD 50 รวม | **PROPOSED ONLY** รวม $5 เดิม ไม่ใช่เพิ่มอีก $25/$50 |
| Long run ตาม paper ใหม่ | **รอเจ้าของพิจารณาคุณค่าและอนุมัติ** คำขอ proposal ไม่ใช่ launch permission |
| USD 100 | future option ที่ต้องเสนอใหม่ ไม่ใช่ recommendation รอบนี้ |
| Full dataset acquisition/training/API dispatch ในรอบนี้ | **NOT_RUN / ไม่อยู่ในงานเอกสารรอบนี้** |
| Deploy destination/auth/hosting/retention | ยังไม่เลือก ไม่ deploy |
| Wet-lab, production/regulatory release, paid compute, expert hiring, APC/submission | separate decisions ไม่อยู่ใน model API cap |

หากภายหลังอนุมัติ $50 ให้ใช้ cumulative gates $5→$15→$35→$50 ที่ผ่าน readiness จริง ไม่ใช่สี่ก้อนบวกกัน ทุก agent/retry/UI call ใช้ shared accounting เดียว ไม่ reset histories
หากเลือก $25 ให้ลด frozen matrix และ ceiling เหลือ $25 ไม่มีสิทธิ์ใช้ gates $35/$50

## Claims และหลักฐาน

Published engineering baseline `4adcdf319fb9cb8e388879fdc217a40f92e84fee` มี fresh-clone 142 tests ผ่านและ offline commands 6 รายการผ่านตาม receipt เดิม ไม่ได้รันซ้ำในงานเอกสารนี้ และไม่พิสูจน์ hypotheses ใหม่
PTP authored3 cases และ SYN dev/demo48 cases ไม่เป็น independent measured heldout evidence
Catechol เป็น primary data candidate ที่ตรวจ paper/metadata/license ระดับ repo แล้ว ยังไม่ acquire/parse local CSV; asset rights, campaign counts และ grouped split ยังเป็น gates
Helleckes dataset เป็น in-silico diagnostic และ license ยัง UNKNOWN จากสิ่งที่อ่านได้

Research novelty ยังไม่ established โดยเฉพาะเมื่อมี Catechol, Helleckes calibration design, Chen2026 robust chemical transfer และ MUSE patent analogies
Engineering capability, measured research contribution และ long-term cross-domain vision ต้องรายงานแยก ไม่ทำนาย rubric/ความเห็นอาจารย์หรือรับรอง journal ranking/acceptance

## Source precedence และงานรับช่วง

รุ่น3แทนข้อเสนอ paper/next-study ใน [รุ่น2](REQUIREMENTS_DECISIONS_20261027_V2_TH.md) เฉพาะที่ระบุ ส่วน privacy, no-code/essential human review, immutable history และ safety constraints เดิมยังใช้ต่อ
[Luna GOAL v2](../handoff/LUNA_LONG_RUN_V2_20261027_TH.md) เป็นประวัติงานรับช่วงเดิม ไม่ใช่คำสั่งให้เริ่ม patent-packet scientific matrix หลังเปลี่ยนทิศทางนี้
ให้ parent/owner review proposal และเลือกงบก่อนแปลงเป็น executable long-run manifest; เปลี่ยน scope/data/model อย่างมีนัยสำคัญต้องพิจารณาใหม่
รอบนี้ Pepo ทำเอกสาร/ตรวจเลขและ links เท่านั้น ไม่มี paid call, training, installation, UI implementation หรือ deployment
