# NEW GOAL — research engine และผลิตภัณฑ์ที่รันงานจริง

## จุดหมายและคำสั่งเริ่ม

ทำงานใน `C:/Users/User/Desktop/myProject/patent-to-pilot` ใช้ Luna Max ตามชื่อ executor ที่ owner เลือก ไม่ใช้ชื่อนั้นเป็น scientific model ID ทำตาม system/developer/runtime และ scoped AGENTS อ่าน [AGENTS](../../../../AGENTS.md), [GOAL sections 0–4](../../../../GOAL.md), [PLAN](../../../../PLAN.md), [README](../../../../README.md), [progress](../../progress.json) และ [next actions](../../../../memory/next-actions.md) ก่อนตรวจ HEAD/status/ownership ใหม่

นี่คือ **NEW GOAL** แทน M42 coverage และ overnight scope เดิม งานต่อจากนี้ resume ได้จาก checkpoint ใหม่เท่านั้น ห้ามใช้ชื่อ goal ใหม่รีเซ็ตงบหรือ deadline เก็บหลักฐานเดิมไว้ ไม่เริ่ม broad audit ซ้ำโดยไม่มี source drift ที่เกี่ยวข้อง

North star จากแชต “Pepo patent-to-pilot”: Medical Device evidence dossier สำหรับผู้ประกอบการและนักลงทุน เริ่มจาก named device/comparator แล้วได้ facts, patent candidates/disclosed associations, feature–evidence table, source spans/locators, gaps, next information requests, edits/history และ TH/EN export Research ใช้ retrieval/evidence engine เดียวกับ product และศึกษาว่า adaptive acquisition ช่วย quality ที่ fixed budget หรือไม่เมื่อเทียบกับวิธี fixed ที่แข็งแรง

ไม่มี expert หรือ organizational data ใหม่ไม่ใช่ global gate ใช้ published labels ตามความหมายจริงและ deterministic source checks Bridge เป็น conditional main task; ถ้าสิทธิ์/cohort ยังไม่พร้อมให้ block เฉพาะ branch นั้น ทำ FDA facts, SciFact component, permitted known-link recovery และ workflow ต่อ ไม่ fabricate semantic gold

## ผลลัพธ์ที่ owner อนุญาต 4 ข้อ

| Outcome | Acceptance ที่ต้องเห็นจริง |
|---|---|
| O1 — UI สั่ง backend จริง | Browser เริ่ม HTTP job → status/progress → cancel acknowledgment → resume/retry ที่ปลอดภัย → inspect source → edit/reopen selected history version → export JSON/TH/EN จาก backend จริง มี provider selector local/API พร้อม estimates, actual/reserved/unknown spend และ budget gate ไม่มี fake success |
| O2 — remote embeddings → local vectors | HF weights ของ PatEmbed-base และ multilingual-e5-base อยู่ Windows ก่อน พร้อม revision/hash/license จากนั้น encode บน dr-train ตาม allocation เป็น resumable shards ส่งกลับ/import ตรวจ hash/order/model/config แล้วใช้ทั้ง retrieval evaluation และ dossier engine จริง |
| O3 — local LLM 1 + API 1 | `Qwen/Qwen3-8B` local กับ OpenRouter `qwen/qwen3-32b` บน frozen evidence/order/schema เดียวกัน รายงาน source/locator/schema/cost/latency/failures non-thinking เป็น primary condition ต้องมี actual run ของแต่ละ branch หรือแสดง PARTIAL พร้อม blocker ไม่ใช้ mock แทน |
| O4 — 3 real device cases + research report | Named cases เดินครบ browser→jobs→returned-vector retrieval→evidence→generation→history/export พร้อม raw run references, grouped retrieval analysis, failure analysis และ cost-quality trade-offs ที่แยกจาก product/commercial validity |

สามกรณีเริ่มจาก MitraClip, Tendyne, TriClip ที่มี pinned local sources แล้ว ใช้ research purpose ตามสิทธิ์ของแต่ละ source ถ้า case ใดไม่รองรับ outbound API ให้เปรียบเทียบบน intersection ของ evidence ที่อนุญาตทั้งสองระบบ หรือเปลี่ยน case อย่างมีเหตุผลโดยรักษา task เดิม ไม่ส่ง restricted text เพื่อทำยอดครบ 3

สิ่งที่มีเดิมคือ file-based UI integration ไม่ใช่ live HTTP jobs: backend475pass/1skip, frontend72, browser17 และ real file-import cases3 เป็น historical evidence ที่ main0d04980 อ้างไว้ ไม่ใช่ผลรันทดสอบของ goal นี้ [Current integration](../../audits/pepo-ui-integration-20261031/README.md) ระบุ run-start/control unavailable และ `healthtech/api.py` เป็น dry-run/mock seam

## แกนวิจัยและความสำเร็จ

คง HT-B0a company/metadata, HT-B0b lexical, HT-B1 strong fixed hybrid, HT-B2 fixed multi-query, HT-B3 simple adaptive และ HT-B4 bounded controller เทียบที่ shared corpus/cohort/actions/metadata/K และ budget ที่ตรึงก่อน test Reranker เพิ่มได้เมื่อมีเหตุผลและใช้เทียบอย่างเป็นธรรม ไม่เป็น gate ใหม่ Learned router ไม่บังคับ

Primary คือ **quality at fixed budget** เลือก endpoint และ budget unit/จำนวนจาก development แล้ว freeze ก่อน final เช่น macro known-link Recall@20 ใน eligible device/groups พร้อม realized resource records Cost-quality frontier เป็น secondary ห้ามเอาเพียง equal dollar cap มาอ้างว่า compute/metadata เท่ากันทั้งหมด ห้ามบังคับ adaptive win หาก fixed baseline ดีพอให้ product ใช้วิธีนั้นและรายงาน negative finding

Generation comparison ตรึง evidence แยกจาก acquisition-policy comparison เพื่อไม่ปนผลจากคนละ retrieved context Local8B กับ API32B เป็น comparison ของ deployment/model configurations คนละ weights/size ไม่ใช่ causal proof ว่า local หรือ API ดีกว่าโดยตัวมันเอง

COMPLETE ต้องมีหลักฐานทั้ง 4 outcome ตาม scope ที่ได้รับสิทธิ์ 24 ชั่วโมงเป็น resource ceiling ไม่ใช่นิยามเสร็จและไม่ใช่คำรับประกัน full sweep ถ้าบาง branch ยัง pending/หมดงบ ให้ส่งสิ่งที่ใช้ต่อได้เป็น PARTIAL และระบุ BLOCKED_LOCAL เฉพาะส่วนนั้น ห้ามเปลี่ยน authoritative goals ให้ผ่านเอง

## งานที่ทำต่อได้ทันทีและ boundaries

ใช้ [execution plan](EXECUTION_PLAN.md) และ [authorization](AUTHORIZATION_AND_BUDGET.md) เป็นคู่กัน เดิน local service/contracts/UI integration, evaluator regressions, canonical budget guard, manifests และ protocol ควบคู่กับ authorized isolated setup ตาม dependency จริง ห้ามตีความ access ได้ว่า license อนุญาต commercial redistribution

สร้าง isolated branch/worktree สำหรับ goal นี้ Preserve every dirty/untracked file และตรวจ Claude/Luna ownership ก่อนแก้ UI หรือ backend ที่ใช้ร่วมกัน Owner อนุญาตการต่อ UI ใน goal ใหม่ แต่ไม่อนุญาต takeover concurrent writer ถ้าชนให้ทำ new adapter/contracts/independent work ก่อน ไม่ reset/stash/clean หรือ merge งานคนอื่นเงียบๆ

Git branch/worktree/commit/push/test PR และ **merge main เมื่อผ่าน acceptance tests ได้รับอนุญาตแล้ว** ใช้ scoped tested files และ license/secret checks ตรวจ exact PR/main heads ก่อน merge และ retest เมื่อ head เปลี่ยน ไม่ impersonate owner review, force push หรือ bypass required review/protections หาก protection ต้องการ review จริงให้คงเฉพาะ merge เป็น BLOCKED_LOCAL ไม่มี deployment/public release, paid customer pilot/outreach, security/global settings change หรือรับประกัน journal/clinical/FTO/business outcome
