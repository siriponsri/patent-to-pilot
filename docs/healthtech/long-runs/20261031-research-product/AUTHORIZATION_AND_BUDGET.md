# สิทธิ์ที่มีแล้ว สิ่งที่รอ และงบสะสม

เอกสารนี้แปลงคำตอบ owner เป็น execution contract ไม่ใช่ grant จาก model card/runtime scan คำสั่งล่าสุดของ owner และ runtime มีผลก่อน defaults เก่าใน repo ดู machine-readable [requirements receipt](REQUIREMENTS_RECEIPT.json)

## Authorization matrix

| เรื่อง | สถานะ | วิธีดำเนินการ |
|---|---|---|
| ปิด 4 outcomes research+product | APPROVED | goal-based execution ไม่จบแค่ scripts/receipts |
| Research/non-commercial และเตรียม commercial path | APPROVED | แยก code/model/data rights และ distribution registry ไม่ relicense NC assets |
| HF embedding weights | APPROVED | shortlist เท่านั้น ดาวน์โหลดเก็บ Windows ก่อน แล้ว controlled transfer ไป dr-train ตามสิทธิ์และ resource bounds ห้าม HF/API embeddings |
| Local LLM1 + API1 / UI เลือกได้ | APPROVED | local-first; API ทุกครั้งผ่าน backend canonical budget controller ไม่มี browser credential |
| OpenRouter USD8 | APPROVED_CUMULATIVE | เป็น old round1 cap เดียว รวม billable input/output ของ generation/judge/reasoning/retries ไม่ใช่ USD8 ใหม่ |
| GPU ใบเดียว, concurrency 1, embedding/LLM สลับ | APPROVED_CONSTRAINT | ห้าม all-GPUs/ยึด GPU อีกใบ/หยุดงานคนอื่นหรือแตะ Podi |
| ระยะ runtime24 ชั่วโมง | APPROVED_CEILING | เริ่มจาก runtime/model canary/job แรกของ goal นี้ บันทึก UTC deadline คงเดิมข้าม resume |
| V100 UUID `GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089` | APPROVED | ใบเดียวที่อนุญาต ไม่ใช้ 2080Ti หรือ all-GPUs เป็น fallback ตรวจ capacity สดก่อน job |
| CPU≤8 threads / RAM≤32 GiB / additional disk รวม≤40 GiB | APPROVED_HARD_BOUNDS | disk นับ Windows+remote copies/cache/temp/env/shards รวมกัน ไม่ใช่ 40 ต่อเครื่อง เช็ก headroom ก่อน download/setup |
| isolated venv/container + official pinned runtime setup | APPROVED_ISOLATED_ONLY | ลง dependencies ทางการใน job scope ได้ ไม่แก้ system Python/driver/security/globalsettings ไม่สร้าง credential ใหม่ |
| branch/worktree/commit/push/test PR | APPROVED_SCOPED | ตรวจ ownership/tests/secrets/license/remote base ไม่มี unrelated staging |
| merge main หลัง acceptance | APPROVED_CONDITIONAL_ON_CHECKS | verifyexactheads/retestraces, respectrequired reviews/protections ไม่ impersonate PR Approve |

สามคำตอบล่าสุดของ owner อนุมัติตามข้อเสนอ Pepo ครบแล้ว ใช้อำนาจนี้โดยไม่ขอซ้ำ การอ่าน capacity เป็น action-time check ไม่ใช่ตัวให้อำนาจ GPU Unknown historical billing หยุดเฉพาะ paid API ส่วน resource ไม่พอ/runtime ไม่ compatible/branch protection หยุดเฉพาะ dependentaction ทำงานอิสระต่อ หากต้องเพิ่มเกิน 40 GiB/24h/USD8 หรือสร้าง key/เปลี่ยน security จึงขอ requirements/approval ใหม่เฉพาะส่วนที่เพิ่มจริง

## Canonical cumulative USD8 controller

ก่อน paid call แรก ต้อง reconcile authorization `PTP-HT-OR-R1-20261028-USD8` กับ existing durable ledger/attempts/provider receipts ผ่าน approved integration ห้ามอ่าน/พิมพ์ secrets หรือ copy private journals ลง Git การเตรียมเอกสารนี้ไม่ได้อ่านยอด historical spend จึงยังไม่รู้ remaining ไม่ถือว่าเหลือ 8 เต็ม

แก้ audit gap ที่ caller เลือก `--budget-path` ใหม่แล้วได้ cap ใหม่: authorization เดียวต้องชี้ canonical ledger identity/location เดียว มี process-safe lock/transaction และ durable attempt IDs across UI/CLI/agents/resumes แยก mock ledger namespace ชัดเจน อย่า merge actual กับ simulated spend หรือ reset journal เพื่อเพิ่ม attempts

Admission ใช้ `settled_actual + all_outstanding_reserved + new_upper_bound <= authorized_ceiling - safety_margin` ด้วย Decimal/micro-USD ที่แน่นอน Unknown billing ยัง RESERVED ไม่ใช่ USD0 เก็บทุก failed/cancelled attempt ที่อาจ bill ได้ SDK hidden retry ปิด; manualretry ต้อง readmit/reserve ใหม่ทุกครั้งภายใน explicit retry bound และ budget เดียวกัน

Upper bound ครอบคลุม full serialized billable input รวม framing, maximum completion รวม reasoning ที่ bill, provider/cache/other applicable charges และ retries ที่วางแผนไว้ ไม่เดา input tokens จาก visibletext อย่างเดียว Pin model+provider endpoint, fresh exact pricing/support parameters, max tokens, timeout/retry cap และ hard amount cap ถ้าคำนวณ max bill ไม่ได้ให้ fail closed

ข้อเสนอ operational margin: admission threshold ไม่เกิน USD7 cumulative และเก็บ USD1 ภายใน cap8 สำหรับ reconciliation/uncertainty ไม่ใช่ grant สองก้อน ลด threshold ถ้า historical spent/pending ทำให้เหลือน้อยกว่า Snapshot ราคากับ timestamp ทันที ก่อน dispatch ใช้ exactroute เดิม; ปิด fallback/price escalation และ require supported parameters `max_price`เป็น rate filter ไม่ใช่ run dollar cap [Provider routing](https://openrouter.ai/docs/guides/routing/provider-selection)

API model คือ `qwen/qwen3-32b` หน้า catalog ที่อ่าน 31Oct2026 แสดง DeepInfra USD0.08/M input และ 0.28/M output เป็น illustrative observed rate เท่านั้น ผู้ให้บริการอื่นแพงกว่า ต้องตรวจ route/rate ใหม่ก่อน call ไม่ผูก budget กับหน้า marketing เก่า [Model/provider catalog](https://openrouter.ai/qwen/qwen3-32b)

เริ่ม sequential canary ที่ reserve ได้ แล้ว paired pilot ที่มี information value ตาม remaining ไม่ต้องใช้เงินให้หมด ตัวอย่าง canary cap USD0.10 และ pilot cap USD2 เป็นข้อเสนอภายใน remaining ที่ยืนยันแล้ว ไม่ใช่เงินเพิ่ม หาก balance เหลือน้อยให้ลด sample ก่อน dispatch โดยไม่ลบ failures จาก denominator

หลังตอบรับให้ settle จาก usage.cost และ generation ID/total cost reconciliation เก็บ token breakdown, actual cost, retries, latency และ reservation release หาก timeout/unknown อย่าปล่อย reservation หรือ resend โดยไม่ตรวจสถานะ [Usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting), [generation lookup](https://openrouter.ai/docs/api-reference/get-a-generation) ไม่ถือ platformin-flightlimit ว่าเป็น hardcap สากล และไม่สร้าง capped key ใหม่เอง

## เมื่อชนงบหรือสิทธิ์

หยุดเฉพาะ paid branch ก่อน cap หรือเมื่อ price/billing/ledger ไม่แน่ใจ ทำ local/offline งานต่อ ออกรายงานขอขยายงบพร้อม actual/pending/remaining, proposed extra runs, maximum additional charge, effective groups, uncertainty/power limits และ information gain ต้องมี owner อนุมัติก่อนเพิ่มวงเงิน ห้าม topup/subscription/newkey/purchases อัตโนมัติ

24h deadline ครอบคลุม canary/embedding/generation job ตั้งแต่ครั้งแรก ไม่ reset เมื่อ disconnect/เปลี่ยนโมเดล/restart Preparation/download/setup time บันทึกต่างหากแต่ไม่ใช้เลี่ยง deadline ถ้าหนึ่ง allocation มี window สั้นกว่าให้ใช้ deadline ที่สั้นกว่า ห้ามยืม GPU อื่นเมื่อเหลือเวลาน้อย
