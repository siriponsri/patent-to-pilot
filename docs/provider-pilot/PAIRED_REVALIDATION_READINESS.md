# Fresh paired revalidation and scientific pilot readiness

วันที่: 26 ตุลาคม 2026
สถานะ: **ENGINEERING_ECHO_READY; SCIENTIFIC_PILOT_NOT_RUN**

เอกสารนี้แยก transport/accounting echo ออกจาก development evaluation และ main study ตาม G10/G13/G15/G16 ไม่อ้างว่า model ช่วยงาน R&D ได้จริง และไม่ใช่หลักฐานด้าน clinical, regulatory, legal, patentability หรือ FTO

## สถานะที่ตรวจได้

| ชั้นงาน | สถานะ | หลักฐาน/ขอบเขต |
|---|---|---|
| Phase A เดิม | PASS ในฐานะ historical receipt; aggregate terminal `PHASE_FAILED` | 2 attempts, debit USD 0.0000732; journal เดิมคงเดิม |
| Fresh pair contract | PASS | exact model/route/prompt/schema/body hashes ใน `configs/provider-paired-revalidation-plan.json` |
| Offline provider guards | PASS | affected suite 107 passed; mock-only pair tests 10 passed |
| Public endpoint preflight | PASS | unauthenticated metadata matched model, route, context, price and required parameters in `paired-public-preflight-2026-10-26.json` |
| B0-B3/P offline comparison slice | PASS | public PTP-0001 `S0 → S1 → S2`; mechanics-only evidence in `results/development/g10-offline-comparison/`; B4-RG is `READY_FOR_FUTURE / NOT_RUN` |
| Scientific pilot | NOT_RUN | no held-out batch, no model comparison, no outcome or utility claim |
| Cross-task learning | NOT_RUN | within-project revision remains separate from G12 learning |

## Same-input comparison contract

ทุกวิธีใน comparison track ต้องเห็น staged brief, allowed source packet, organization profile version, policy/event, output schema และ deterministic validators ชุดเดียวกัน ห้ามส่ง expected answers, evaluator-only IDs, hidden changes, gold dependencies หรือ source hints ที่ให้คำตอบล่วงหน้าเข้า agent

| Method | บทบาท | สิ่งที่ต้องวัด |
|---|---|---|
| B0 direct rule path | deterministic extraction + explicit policy checks | unsupported values, false unknowns, policy errors |
| B1 full regeneration | สร้าง draft ใหม่ทั้งชุดทุก change | affected/preserved fields, calls, tokens, latency, cost |
| B2 direct revision | แก้จาก draft เดิมด้วย change + allowed evidence | collateral edits, unsupported carry-over, revision cost |
| B3 deterministic invalidation + same generator | required comparator สำหรับ scoped invalidation | invalidated scope, preservation, full generation cost |
| Proposed workflow | source-linked options/routes, scoped invalidation, unknown handling, typed diff/read-back | traceability, policy errors, preservation, cost and failure rate |

`full_generator_then_scoped_merge` ต้องนับ full generation ตามจริง ไม่รายงานเป็น saved recomputation จาก selective label และ within-project revision ไม่ใช่ cross-project learning

## Next scientific decision

| Gate | ยังขาด | สถานะ |
|---|---|---|
| Case coverage | ขยาย development cases พร้อม source versions, family IDs, locators และ explicit unknowns | BLOCKED / NOT_READY |
| Organization groups | เตรียม fictional profiles อย่างน้อยสามกลุ่มและแยก dev/held-out reuse | BLOCKED / NOT_READY |
| Split freeze | กำหนด final dev/validation/test grouping หลัง coverage และ calibration | NOT_RUN |
| Evaluator boundary | สร้าง curator-only expected outputs/source witnesses โดยไม่ expose ให้ agent | NOT_RUN |
| Provider freeze | ตรึง model/provider/version, routing, retries, cost worksheet และ stop rules | READY สำหรับ echo; NOT_READY สำหรับ scientific batch |
| Feedback separation | ตรึง chronological feedback/memory controls ก่อน longitudinal run | NOT_RUN |

## Cost worksheet (planning, not a scientific authorization)

| รายการ | ค่า |
|---|---:|
| Historical Phase A API-reported debit | USD 0.0000732 |
| Gemini conservative reservation | USD 0.1054576 |
| GPT conservative reservation | USD 0.4214304 |
| Fresh pair reservation | USD 0.5268880 |
| Cumulative reservation including history | USD 0.5269612 |
| Cumulative cap | USD 0.6000000 |
| Scientific batch beyond the pair | **UNAPPROVED / NOT_RUN** |

Reservation values are conservative plan bounds derived from the public endpoint snapshot and exact serialized request contract. They are not actual debit, tokenizer guarantees, account balance, or spending-limit verification. Missing usage/cost remains `unknown_pending` and blocks further dispatch.

## Decision rule

การตัดสินใจเปิด scientific pilot ต้องใช้ pre-specified summary ที่ตรวจ cost, failure rate, leakage checks, grouping และ validator quality ตาม ceiling ที่อนุมัติ ผลอาจเป็น material improvement, no material advantage หรือ `INCONCLUSIVE`; ไม่ตั้ง winning outcome ไว้ล่วงหน้า หากผลเท่ากัน, complexity เพิ่มต้นทุน, ไม่เห็น advantage ที่มีนัยต่อเป้าหมาย, หรือ coverage/evaluator quality ยังไม่พอ ให้ mark pilot `NO_ADVANTAGE` หรือ `INCONCLUSIVE` ตาม protocol แล้วลด claim/เตรียมข้อมูลเพิ่ม
