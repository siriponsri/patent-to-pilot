# ตรวจ R1 และเตรียมส่งต่อ long run — 31 ตุลาคม 2026

ตรวจ key เดิมกับ OpenRouter สำเร็จ เมื่อ 13:52:45 UTC ยอดใช้สะสมของ key เท่ากับ USD 0.0001464 และยอดวันนี้เท่ากับ USD 0 ยอดสะสมตรงกับต้นทุนของ 4 attempts ใน journal pilot เก่าทั้งสองไฟล์ หลักฐานใหม่นี้ช่วยตรวจ R1 ได้โดยไม่ต้องค้น journal ทั่วเครื่องซ้ำ

## สิ่งที่ยืนยันได้

- `GET https://openrouter.ai/api/v1/key` ตอบ HTTP 200 หลัง owner อนุมัติการอ่านเฉพาะ key จาก `.env` และส่งไปยัง OpenRouter ผ่าน HTTPS ไม่มี model call ไม่มี secret ใน stdout หรือ artifacts
- key ไม่มี per-key cap (`limit` และ `limit_remaining` เป็น null), ไม่ใช่ management key, BYOK usage เป็น 0 และ metadata ไม่แสดง budget เพิ่มเติม `null` ตรงนี้ไม่ได้หมายความว่าบัญชีมีเครดิตไม่จำกัด
- journal `live.sqlite3` มีต้นทุนราย attempt USD 0.0000132 และ 0.00006; `paired-revalidation-1.sqlite3` มีจำนวนเท่ากัน รวม USD 0.0001464 ไฟล์ต้นฉบับทั้งสองมี hash เดิม ดู `legacy-journal-check.json`
- ไม่พบ generation ID ที่ใช้ lookup ได้ใน reservation/response ของ 4 records หรือใน audit/handoff ที่ตรวจ จึงไม่ได้เรียก `/generation` ห้ามใช้ local job ID แทน provider ID
- approval ของ pilot เก่าลงวันที่ 26 ตุลาคม 2026 และระบุ cumulative USD 0.60 จึงไม่เปลี่ยนชื่อย้อนหลังให้เป็น R1 วันที่ 28 ตุลาคม แม้ยอดจะตรงกับ key ปัจจุบัน
- ผลนี้เป็นยอดรวมของ key เดียว ณ เวลาที่ตรวจ ไม่ได้ยืนยันว่า R1 ไม่เคยใช้ key อื่น หรือไม่มีคำขอที่ยังไม่ลงบัญชี `reconciliation.json` เก็บ unknown เหล่านี้ไว้ จึงยังไม่ประกาศ remaining USD 8

## สิ่งที่ทำเพิ่มและทดสอบ

เพิ่ม `scripts/healthtech/collect_openrouter_metadata.py` กับโมดูล `metadata_observation.py` ตัวตรวจใช้ host คงที่ ตรวจ TLS ไม่ตาม redirect ไม่ใช้ proxy จาก environment ไม่ retry และไม่อ่าน error body อ่านข้อมูลตอบกลับได้ไม่เกิน 256 KiB เก็บเฉพาะค่าตัวเลขที่ตรวจชนิดแล้ว flags และ fingerprint ตัด label และข้อความอื่นออก

ถ้า key เดิมรายงานว่าเป็น management key และเปิด option ไว้ จึงจะตรวจ `/credits` ตัว key ที่พบเป็น ordinary key จึงไม่ส่งคำขอนั้น ไม่สร้างหรือขอ key เพิ่ม ผลลัพธ์เป็น local observation ที่มี hash ตรวจความเปลี่ยนแปลง ไม่ใช่ลายเซ็นของ provider และใช้แทน canonical budget ledger ไม่ได้

ชุดทดสอบทั้งหมดผ่าน 582 tests มี skip 1 และ warnings เดิม 2 รายการ รวม collector ใหม่ 20 tests ครอบคลุม redirect, 401/403/500, ข้อผิดพลาดที่มี secret ในข้อความ, output เดิม, ชนิดตัวเลขผิด, NaN/Infinity, negative availability และการไม่ตีความยอด key เป็นยอดบัญชี ตรวจ compile และ diff ผ่าน ดู `verification.json`, `tests.xml`, `prior-repair-binding.json`

source refs: `src/patent_to_pilot/providers/metadata_observation.py:27` เลือกเฉพาะ key, `:66` ตัด metadata, `:96` จำกัด endpoint/transport, `:126` แยก usage/credit/history; tests อยู่ `tests/test_openrouter_metadata_observation.py`

## ขอบเขตที่ยังขาด และทางปลดที่สั้นที่สุด

1. ยืนยันเพียงว่า R1 ใช้ key นี้ตัวเดียวมาตลอดหรือไม่ และไม่มี request ค้าง/runner เก่าส่งงานอยู่ หากยืนยันได้ ให้นำยอด provider ที่ตรงกับ 4 records และรายงาน R1 ที่ระบุ paid NOT_RUN มาทบทวนขอบเขต ไม่บังคับให้ owner หา SQLite ที่อาจไม่เคยถูกสร้าง หากเคยใช้ key อื่น ต้องตรวจเฉพาะ key/ช่วงนั้น ไม่ค้นทั้งเครื่องใหม่
2. บัญชีต้องมียอดเครดิตล่าสุดพร้อมเวลาใน dashboard ของบัญชีเดียวกัน Ordinary key ไม่เปิด `/credits` ตามเอกสารปัจจุบัน ไม่ใช้ยอด funding USD 10 เมื่อวันที่ 26 ตุลาคมแทนยอดวันนี้ ไม่ขออนุมัติงบ USD 8 ซ้ำ
3. เมื่อข้อมูลครบ ให้ทำ reviewed migration/initialization ใน authority เดิม เก็บ conservative historical carryover และ unknown reservations ตามจริง ปัจจุบัน `history_export.py:14` ตรวจความสอดคล้องของ export เท่านั้น ไม่ import ส่วน `history_review.py:17` และ `ledger_registry.py:78` ต้องมี reviewed anchor ก่อนเปิด live งานนี้เป็นหน้าที่ implementation ไม่ใช่เอกสารที่ owner ต้องเขียน และห้าม copy fixture มาสร้าง ledger หรืออ้างว่าสร้าง canonical ledger แล้ว
4. ก่อน paid call ต้องใช้ registry เดียว หยุด writers เดิมที่อาจข้าม controller และตรวจ fresh route/pricing/credit อีกครั้ง การแค่ตัวเลขตรงกันไม่แก้ duplicate-ledger exposure ของโปรแกรมเก่า

ข้อ 1 และยอดในข้อ 2 ถูกถามผ่านช่องคำถามแล้ว ณ checkpoint ยังไม่รับคำตอบ ไม่มีการสร้าง ledger/anchor/registry หรือเปิด paid branch

## O3/O4 ที่ต้องทำต่อจริง

ตรวจไฟล์จริง `patent-to-pilot-local-artifacts/ht-o3-evidence-pack-20261031/evidence-pack.json` แล้ว SHA256 ตรงกับ receipt `2594295d...f0043a` มี MitraClip, Tendyne และ TriClip ครบ 3 cases ตัวตรวจปัจจุบันปฏิเสธ `abbott-product-patent-disclosures` ที่ยังเป็น BLOCKED_LOCAL โมเดลยังเห็น Google Patents IDs อีก 11 แหล่งใน candidate preview แรก 6 รายการต่อ case รายละเอียด IDs และ message hashes อยู่ `current-pairing-probe.json` ไม่มี raw text ใน audit นี้

สาม source ของ openFDA มี rights ID, source hash/revision และ field allowlist อยู่แล้ว จุดที่ pack เก่าขาดคือ basis_url และ exact-message transfer review จึงเตรียม FDA-only canary ให้เรียบร้อยหลังตรวจ [openFDA Terms — Data Rights and Usage](https://open.fda.gov/terms/) ใช้เฉพาะ pma_number, trade_name และ applicant รวม 9 facts ใน 3 cases ตัด patent/disclosure, generic/GMDN terms และข้อความ query เก่าออก พร้อม authored query และ review ที่ผูก message hash ผ่าน validator ปัจจุบันแล้ว ดู fda-canary-manifest.json และ fda-canary-verification.json

Private pack และ exact messages อยู่ C:/Users/User/Documents/Codex/2026-10-31/task-5/private-fda-canary-20261031 ใช้ prepare_fda_canary.py ทำซ้ำจาก source pack ที่ pin hash เดิมได้ ตัวตรวจปฏิเสธ input ที่แก้แม้เพียงหนึ่ง byte การเตรียมนี้ไม่เรียกโมเดล ไม่มี fresh pricing และยังไม่ทำให้ R1 เปิด live ได้ ต้องรัน local/API ใหม่บนชุดกรองเดียวกัน และไม่ใช้ FDA-only canary แทนการประเมิน device–patent เต็มงาน

O4 มีหลักฐาน generation/browser เดิม 3 cases แต่ fixed-control frontier ที่นำมาอ้างยังเป็น Stryker เก่า ไม่ใช่ matched Abbott ปัจจุบัน และ `ht-o1-o4-closeout-20261031/current-candidate-frontend.json:21` ระบุ full browser E2E ค้างหลัง E03 จึงยังไม่ปิด O4 ทั้ง research และ current-candidate acceptance

## จุดส่งต่อให้ Luna

snapshot เริ่มจาก upstream `9ac38720d219b83acccaa92dcabc4480283914c4` ที่ตรวจแล้วสะอาด ต่อมาคำสั่ง recheck `git rev-parse HEAD` และ `git status --short` ของ worktree เดิมถูก Git ปฏิเสธด้วย dubious ownership (`User` ต่างจาก `CodexSandboxOffline`) ไม่แก้ safe.directory หรือ ACL จึงส่ง scoped patch จาก workspace ที่เราเป็นผู้เขียนให้ Luna ซึ่งถือ private artifacts และ runtime เดิมรับต่อ ตรวจ HEAD ปัจจุบันก่อน apply

ไม่มี paid/GPU runner ของงานนี้ค้างอยู่ ไม่ได้เปิด long runner ซ้อน ให้ยึด first runtime ไม่ช้ากว่า 2026-10-31T02:47:23Z และ deadline ไม่ช้ากว่า 2026-11-01T02:47:23Z หากพบเวลาเริ่มที่เก่ากว่าให้ใช้เวลานั้น ไม่เริ่มนับ 24 ชั่วโมงใหม่ วงเงินเดิม USD 8, admission ceiling USD 7, V100 UUID เดิม, concurrency 1, CPU 8 threads, RAM 32 GiB และ disk เพิ่มรวม 40 GiB

## เอกสาร provider ที่ตรวจ

- [Current key metadata](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key) และ [Limits](https://openrouter.ai/docs/api_reference/limits): usage/key limits และ budgets แยกจากยอดบัญชี
- [Remaining account credits](https://openrouter.ai/docs/api/api-reference/credits/get-remaining-credits): endpoint ต้องใช้ management key
- [Logs](https://openrouter.ai/docs/guides/features/logs): generation metadata ต้องมี provider generation ID; ไม่เรียก content endpoint
- [Activity](https://openrouter.ai/docs/guides/features/activity): CSV/PDF เป็น aggregates ตาม filters/date range ไม่รับรอง attempts ที่ขาดหรือ billing ค้างด้วยตัวเอง
