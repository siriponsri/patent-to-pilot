# Checkpoint คู่ขนาน Local / Paid API

สถานะรวม: `PASS_SHARED_CONTRACT_LOCAL_RUNTIME_NOT_RUN_API_DISPATCH_BLOCKED`

## สิ่งที่ทำสำเร็จ

- ผูก local และ API เข้ากับ evidence pack, messages และ output schema ชุดเดียวกัน
  โดยใช้ 3 cases: MitraClip, Tendyne และ TriClip
- ตรวจ source-backed transfer review กับข้อมูลที่โมเดลเห็นจริงแล้ว
  `3/3` cases ผ่านสิทธิ์ `ALLOWED_WITH_ATTRIBUTION`
- manifest API ไม่ส่ง raw source payload, evaluator labels, gold-derived queries,
  generated output หรือ credentials
- focused regression `33 passed`; full Python `611 passed, 1 skipped`; compile
  และ diff check ผ่าน

## Local

ทำ current-head contract preflight ได้ `3/3` และ message hashes ตรงกับ API
แต่ยังไม่ได้รัน Qwen3-8B รอบใหม่ เพราะ model root ที่อนุญาตไม่ถูก expose ใน
worktree นี้, SSH ไป `dr-train` ถูกปฏิเสธด้วย `Permission denied
(publickey,password)` และ HTTP port `18787` ปฏิเสธการเชื่อมต่อ การรัน prior
receipt ซ้ำจะทำให้ผลปนคนละ candidate จึงไม่นับเป็นผลใหม่

guard ยังคงบังคับ V100 UUID
`GPU-277ccc57-c3e5-0731-cd49-f4f8695f7089`, concurrency `1`, หน้าต่างเดิมถึง
15 พฤศจิกายน 2026 เวลา 23:59 ไทย และไม่เขียนทับ receipt เดิม

## Paid API

API dry-run ผ่าน payload/rights validation และมี provider calls `0`, paid cost
`USD0.00` แต่ยังหยุดก่อน reservation เพราะไม่พบ canonical R1 registry/journal
ในตำแหน่งที่กำหนดและไม่มี current v2 account/key credit snapshot

historical visible debit `USD0.0001464` ถูกเก็บไว้เป็นหลักฐานเดิม ไม่สร้าง
zero ledger, ไม่ reset งบหรือเวลา, ไม่ allocate attempt ใหม่ และไม่ retry คำขอ
ที่ยังไม่ทราบผล

คำสั่ง owner ระบุ cumulative ceiling `USD100` แต่ executable runner ใน worktree
ยังผูกกับ historical R1 policy `ptp-ht-openrouter-r1-20261028-usd8-v1` การ
reconcile policy/ledger จึงต้องใช้ canonical journal เดิมและหลักฐาน binding จริง
ก่อน dispatch; ผมไม่ตีความยอด `USD100` เป็นการสร้างหรือขยาย ledger ใหม่เอง

## สิ่งที่ owner ต้องช่วยครั้งเดียว

ส่งอย่างใดอย่างหนึ่งโดยไม่ส่ง secret:

1. ตำแหน่ง canonical R1 journal เดิม หรือ sanitized all-attempt export ที่มี
   attempt ID, reservation/settlement state, pending/unknown และต้นทุนจริง
2. current sanitized v2 account/key credit snapshot จากช่องทางที่อนุญาต หาก
   integration ที่ได้รับอนุญาตไม่สามารถอ่านให้ได้

จากนั้นจะตรวจ route/pricing/current credit/writer quiescence แล้ว dispatch
paired canary เดียวเท่านั้นถ้า gate ครบ ส่วน local/offline/manuscript เดินต่อได้
โดยไม่รอ API
