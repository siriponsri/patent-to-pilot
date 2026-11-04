## Current owner amendment — 3 November 2026 local accounting epoch

> **Owner amendment — 4 Nov 2026 (chat):** the prospective E2 allowance is raised from USD1 to **USD10 cumulative**, including the canary's settled USD0.00054516. The USD100 project ceiling, history and journals are unchanged; no reset. The epoch code (`providers/local_epoch.py`) still enforces USD1 until a recorded append-only policy amendment is implemented and tested. Do that only when a planned paid study exceeds the current residual of USD0.99945484. Push to `origin/main` after a verified package is authorized.

> **Current key evidence — 4 Nov 2026:** [presence-preserving observation](../audits/pepo-key-limit-repair-20261104/metadata-observation-v2.json) confirms the dispatch key is UNLIMITED. Older statements below asking for its remaining limit are superseded. This does not imply unlimited account funds. Existing MCP credit evidence must be refreshed and bound to the dispatch account/key at admission. USD100 cumulative/E2USD1/unknown history remain unchanged.

This section supersedes earlier instructions below that require complete R1 recovery before all paid work or prohibit the owner-authorized accounting cutover. The USD100 cumulative ceiling and original GPU limits remain; this is not a fresh USD100 allowance. See [current repair handoff](../audits/pepo-blocked-goal-repair-20261103/README.md) and `LOCAL_ACCOUNTING_AND_GPU_FOLLOWUP.json` there.

- Owner explicitly authorized a new accounting epoch if historical R1 evidence cannot be recovered. Preserve original journals and proven 4 settled calls/USD0.0001464; unknown history remains unknown. Implemented one fixed E2 canonical journal under `%LOCALAPPDATA%/PatentToPilot/healthtech/accounting/project-api.sqlite3`, shared across updated worktrees. No repeated creation, empty-ledger substitution or automatic epoch reset.
- Prospective E2 allowance is USD1, with USD98.9998536 held as an uncertainty buffer. This is not measured spending or a proven ceiling on missing history; lifetime budget guarantee is explicitly false. Account-level credit is now observed through the owner-configured OpenRouter MCP and reconciled to the known E2 usage, but the exact dispatch-key limit/scope and fresh route pricing are still required before paid dispatch; authorization alone does not prove available funds.
- Evidence, journals, outputs and receipts stay on the owner's Windows machine. Existing local `.env` is authorized for API; do not copy credentials to dr-train. dr-train performs computation with transient scratch only, returning outputs locally.
- Fresh patent encoder work completed on the approved V100 on 3 November 12:35:56–12:36:12 UTC, under the shared slot. This supersedes older no-GPU-run/access-blocked statements as the latest result; it does not reserve future capacity or close research goals.
- Do not demand R1 completeness as a gate for the accepted E2 cutover or ask for the approved GPU dates/UUID again. Keep pending/unknown billing blocked, preserve rights checks and resource conflict checks. Resume the same goal. The owner-configured MCP connection has now been tested read-only with `get-credits`; it returned account-level `total_credits=10` and `total_usage=0.0001464`, but did not return the dispatch key's exact limit or scope. No management key was created and no paid call was made.
- Owner amendment 2026-11-04: the initial OpenRouter MCP/provider limit is USD30.00. Record it as provider-side cap metadata only; it does not replace the project USD100 cumulative ceiling, the E2 prospective USD1 allowance, the existing journals, or the exact-key/route-price admission gates.
- Latest sanitized observer r12 returned HTTP 200 for the ordinary `.env` dispatch key, but provider-reported limit and remaining limit are null, budgets are empty, and live admission is false. This confirms the paid gate remains before reservation; it does not create a new credit snapshot or alter the E2 journal.

### Earlier authorizations and observations retained for provenance

# สิทธิ์ที่มีแล้ว สิ่งที่รอ และงบสะสม

## Current precedence — owner repair instruction, 3 November 2026

This section governs current execution. The original USD8/24-hour text below is retained as historical policy and receipt context; it is not the current resource ceiling. See the recorded November 1 extension in [OWNER_ONE_TIME_INPUT_TH_EN.md](OWNER_ONE_TIME_INPUT_TH_EN.md) and the [repair handoff](../audits/pepo-blocked-goal-repair-20261103/README.md).

- API: USD100 cumulative across providers, INCLUDING prior settled spend, pending/unknown reservations and retries. Preserve the existing R1 identity/history; never create a new empty ledger, new allowance, top-up, or retry an uncertain call. A policy update may be bound only after existing history and current scoped credit are reconciled. Authorization does not prove available credit.
- Local GPU: the owner grant already identifies dr-train, UUID `GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089`, concurrency 1, through 2026-11-15 23:59 Asia/Bangkok. CPU <=8 threads, RAM <=32 GiB, combined incremental disk <=40 GiB; preserve other services. Do not request these dates/UUID again.
- Owner authorization, permitted host access, and current resource exclusivity are separate checks. Idle memory and a zero-byte lock marker do not prove exclusivity; use the shared OS lock and live process/resource checks. A distinct operator lease is required only if an applicable infrastructure policy actually requires it; do not invent that dependency or claim it exists without evidence. Owner authorization does not bypass access denial.
- Access update 2026-11-03 12:21 UTC: after explicit owner approval, the one read-only strict-host-key SSH retry succeeded. The approved V100 had no compute process or observed kernel slot lock; all three model directories resolve to one shared parent. This supersedes the earlier connection denial as the latest access observation, not as a persistent reservation. No new GPU run was started. See ACCESS_AND_HISTORY_FOLLOWUP.json in the repair audit; recheck state and acquire the shared slot at actual launch.
- Missing paid history/credit blocks paid dispatch only. Unavailable SSH blocks remote work only. CPU data validation, evaluation from stored predictions, fixes and reproducibility remain available. Resume the SAME goal and acceptance criteria; no budget or deadline reset.

### Historical original contract follows

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
