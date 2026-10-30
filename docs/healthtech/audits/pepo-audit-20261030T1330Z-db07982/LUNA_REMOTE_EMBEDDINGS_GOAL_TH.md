# Luna Goal — remote embedding compute แล้วใช้ vectors บน local

โหมด **Goal** ทำงานใน `C:\Users\User\Desktop\myProject\patent-to-pilot` อ่าน [AUDIT_TH.md](AUDIT_TH.md), [SOURCE_CONTEXT_TH.md](SOURCE_CONTEXT_TH.md), [REMOTE_EMBEDDINGS_PLAN_TH.md](REMOTE_EMBEDDINGS_PLAN_TH.md), [DATASET_GAPS_TH.md](DATASET_GAPS_TH.md), AGENTS และ root GOAL/PLAN/README ตาม applicable instruction hierarchy ก่อนเริ่ม ตรวจ HEAD/status/ownership ใหม่ ฐาน audit คือ `db0798276e3158b04131b4e910abc0a11511e94c`

**เลือก Goal ใหม่ ไม่ใช่ Normal หรือ Resume Goal ของ M42 เดิม** เพราะ objective เปลี่ยนจาก coverage/semantic-source intake เป็น remote compute + vector portability + application integration M42 เป็น completed coverage checkpoint ที่มี dependent scientific blockers เก็บประวัติไว้แล้วตั้ง objective ใหม่ หากระบบใช้ goal session เดิมได้ ให้บันทึก scope amendment นี้อย่างชัดเจนก่อนเดินงาน ไม่อ้างว่ากด mode/UI ใดให้แล้ว

**Claude UX/UI ACTIVE ตามคำสั่ง owner ล่าสุด** แทนบริบท paused เก่า Read-only metadata พบ branch `claude/healthtech-ux-local-20261028`, worktree `C:\Users\User\Desktop\myProject\_worktrees\patent-to-pilot-claude-ux-20261028` ที่ `96c63b14a1a2df8e8f8b816edee0dff7feddc3d3` ตอนตรวจ tracked status ว่างไม่ได้แปลว่า idle/ไม่มี untracked งาน ห้าม takeover/switch/merge/stash/reset หรือแก้ UI-ownedfiles ให้ Luna สร้าง isolated backend/data/vector worktree+branch ของตัวเอง บันทึก API/schema/version compatibility และ contract handoff ให้ Claude อ่าน ไม่มี unsolicited message หรือ automaticUImerge

## Outcome ที่ต้องส่ง

Implement เส้นทาง **Windows runtime inputs → SSH/dr-train batched encoding → resumable vector shards → secure transfer → verified local import/index → retrieval evaluation และ dossier backend ที่ใช้ vectors จริง** ไม่จบด้วย coverage audit, authorization schema หรือ receipt ใหม่อย่างเดียว

Owner ต้องการ compute offload ไม่ใช่ semantic gold server และแชตเดิมระบุว่าไม่มี experts/organizational data ใช้ existing published/reference annotations ตามความหมายจริงได้ ไม่สร้าง mandatory owner adjudication queue ก่อน remote embeddings/SciFact/FDA/known-link/backend งาน semantic relevance ที่ต้องมี labels เพิ่มให้คงเป็น optional dependent branch ห้าม fabricate labels หรือ promote model opinion เป็น gold

## R0 — snapshot และ scope repair

เริ่มจาก audited HEAD หรือ integrate newer owner work อย่างปลอดภัย Preserve every dirty/untracked/active Claude file ไม่ reset/clean/stash งานคนอื่น ใช้ isolated backend/data/vector worktree เมื่อมี concurrent writer หนึ่ง control plane/หนึ่ง writer ต่อไฟล์ Record source/config hashes แล้วเลือก meaningful checks ตามสิ่งที่เปลี่ยน ไม่ audit102commits ซ้ำ

ปิด confirmed gaps ที่เกี่ยวกับงานนี้:

- External query/company metadata projection ต้องเคารพ origin/field policy เดียวกับ source/evidence ทั้ง JSON/TH/EN display/export คง local values และ user-authored origins
- DAPFAM evaluator validate query IDs, dedup task IDs ก่อน cutoff, enforce metric bounds และ explicit missing/failure denominator เพิ่ม hand-computable duplicate probe ที่เคยได้ nDCG1.6309 ไม่ clamp scores เพื่อซ่อนปัญหา
- Cross-cohort tests ใช้ authored fixtures หรือ explicit integration opt-in ไม่พึ่ง ignored results ใน default suite จัด fixture newline/hash contract ให้ portable โดยไม่ weaken frozen raw integrity
- แก้ “globally untouched”/full-context8 เป็น scoped descriptive history/full11 ตามหลักฐาน ไม่กล่าวหา tune-on-test ที่ไม่พบ และใช้ new untouched groups เมื่อจะยืนยันผลใหม่

Budget canonical-ledger/pricing และ semantic draft-stage assurance เป็น repair branch ตาม audit ต้องแก้ก่อนใช้ live/authorized-source stage ที่พึ่งมัน แต่ **ไม่เป็น gate หยุด embedding compute ที่ไม่ใช้ OpenRouter**

## R1 — data/model contract ที่ไม่มี gold

Reuse existing verified DAPFAM corpus/queries และ local permitted device corpus ไม่ต้อง redownload1.21GB เดิมเพื่อเริ่ม Export task-neutral dataset-scoped opaque IDs + exact text/source hashes + revision/representation/rights metadata แยก DAPFAM family IDs จาก canonical patent publication IDs

ไม่ส่ง qrels, gold relevance, adjudications หรือ split answer features ไป encoder เริ่ม DAPFAM title+abstract แบบเดิมก่อน representation extension ตรวจ self-ID/duplicate-text policy จาก pinnedofficialsetting แล้ว freeze identical policy สำหรับ BM25/dense; report self-excludeddiagnostic ถ้ายังไม่มี paritybasis ไม่ dropeligiblequeries เงียบๆ

Pin model/artifact/tokenizer revision และ hashes, prefixes, max length, truncation/chunk rules, pooling, L2 norm, dimension, inference/export dtype และ software versions MiniLM 384 dimensions/max_length256 เป็น integration/portability baseline ไม่ใช่เพดานประสิทธิภาพหรือ semantic context สำหรับสิทธิบัตร ระบุส่วนข้อความที่ truncation ทำให้หายและออกแบบ chunking อย่างชัดเจน การเปรียบเทียบ alternative model, longer context หรือ chunking ใหม่ต้องเป็น separately specified condition พร้อม hypotheses, resource/rights bounds และ matched controls ไม่ silently replace frozen baseline

## R2 — remote readiness และ bounded canary

ใช้ existing approved SSH connection/host verification เท่านั้น ไม่อ่าน/print keys/tokens/.env ไม่สร้าง credential ใหม่ ไม่ปิด host-key checking Audit ยังไม่ได้ตรวจ dr-train จริง ให้ตรวจ read-only environment/storage/job/GPUUUID usage ก่อน execution

ใช้ resource allocation ที่มี authorization อยู่แล้ว หากยังไม่มีให้เตรียม code/export/import/tests ต่อ แล้วส่งคำขอ **เฉพาะ host/jobroot + GPUUUID หรือ CPUquota + wall/VRAM/RAM/disk budget + window ที่ไม่ชน Podi** พร้อม estimated canary/full-job footprint ไม่ถาม owner เรื่อง naming/batch parameters และไม่เดาว่า GPU0 ว่าง ห้าม kill/restart/ปรับ priority/shared services หรือทำ remote GPU job ก่อนมี allocation ชัดเจน

ตรวจ controlled-remote-processing rights ตาม source/use จริง Broad download permission ไม่ใช่ license/access bypass/commercial redistribution Model/corpus downloads ที่จำเป็นและ lawful อยู่ในสิทธิ์เดิม ใช้ bounded/resumable/disk-aware acquisition ไม่ซื้อ cloud/GPU/storage และไม่ executeunknownremote-code

Canary32–100docs+10queries ผ่านจริง ตรวจ exact IDs/text/config, model/backend/tokenizer/dim/norm/numeric consistency และ observed resource budget Backend/precision ต่างจากเดิมให้เป็น newcondition ไม่ silentmixdocument/queryvectors

## R3 — actual resumable full encoding และ return vectors

Implement batching ไม่ encodeallN ใน call เดียว เริ่ม16–32 แล้วปรับจาก VRAM/tokens ภายใน allocation แบ่ง≤5000rows/shard เป็น default ที่ปรับได้พร้อมเหตุผล Write.partial → validate/hash/fsync → atomiccommitmanifest เก็บ ordered IDs, text hashes, model/config parent hashes, counts/shape/dtype/dim/endianness/norm policy และ source provenance

Resume matchingcompletedshards เท่านั้น Inject interruption แล้วพิสูจน์ว่าไม่ recompute สำเร็จแล้ว/ไม่ duplicate/miss rows ไม่ใส่ zero vector แทน failedrow ไม่มี freshledger/cache เพื่อซ่อน failure ต้อง report incomplete coverage เป็น PARTIAL ตามจริง

ส่งกลับด้วย approvedSSH/SFTP/SCP เฉพาะ namedartifacts ตรวจ SHA256 ทั้งต้นทาง/ปลายทางก่อน localpublish ไม่ sync/delete ทั้ง volume ไม่ใส่ rawNC/restrictedtext หรือ derivedvectors เข้า publicGit โดยไม่มี rights รองรับ

เป้าหมายแรกเมื่อ allocation พร้อมคือ **45,336 corpus +1,247 query vectors** ของ permittedDAPFAMsetting หรือ exact documented eligible counts ตาม inputmanifest ไม่เพิ่ม gold เพื่อให้ encode ได้ Final384float32 corpus ประมาณ66.4MiB ไม่รวม IDmap/shards/index จัด planned/actualGPUminutes/storage/transfer/error/OOMretries แยกจาก APIspend

## R4 — local importer และ shared retrieval/application seam

Implement precomputed vector injection สำหรับ `SharedRetriever` หรือ task-neutral retrieval provider และต่อให้ `healthtech/engine.py` ใช้จริงด้วย Current product FTS/token-overlap approximation ต้องคงชื่อ/limits ชัด ไม่แปะ hybridlabel โดยไม่ใช้ dense

Importer reject wrong model/config/text/ID-order/shard hash, missing/extra/duplicate/swapped rows, wrong shape/dtype/dimension/nonfinite/partial bundle ก่อน index เริ่ม exact NumPy/memmap search และ deterministic ID ties ที่45K scale ANN optional เมื่อจำเป็นและต้องวัด recallvs exact

Dynamic queries บน local ใช้ matching CPUqueryencoder; fixedqueryvectors ใช้เมื่อ text/confighash ตรง Cross-encoder ยังเป็น query-documentreranker คนละ component กับ documentvectors ใช้ chunk→document/family aggregation ก่อน K ตาม declaredtask ไม่ count หลาย chunk เป็นหลาย hits

## R5 — matched measurable evaluation และ backend demo

รัน actual BM25 vs dense vs hybrid บน same eligible corpus/queries/qrels/K/self-policy/representation budget พร้อม corrected evaluator ดึง existing fixed/multiquery/heuristic controls มาใช้ตาม actualAPIs คง model/query/reranker/actions ให้เทียบกันได้เมื่อศึกษาตัว controller

DAPFAM วัด citation-familyretrieval ด้วย qrels เดิม ไม่เรียกว่า device-patentsemanticgold Localdevicecorpus วัด known/disclosed-linkrecovery ใน scope ของมัน SciFact แยก component เก็บ per-query/group ranks/metrics/cost/latency/errors/failure denominators/cache provenance และ confidence ตาม effectivegroups Seed repetitions ไม่เพิ่ม independent n ไม่มี forcedadaptivewin

Freeze protocol ก่อน newuntouchedevaluation ห้ามเอา Stryker ที่เคยใช้ development มา renamefinal ใหม่ Sharedcandidateindex ไม่ใช่ leakage โดยตัวมันเอง สิ่งที่ห้ามคือ gold-derivedruntimefeatures และ tune-on-final

ส่ง local backenddemo ที่ใช้ returnedvectors จริงจาก nameddevice/comparator→facts/candidates/evidence/gaps→source/version/hash/locator→edit/reopenhistory→selected-version JSON/TH/EN export อย่างน้อย3realpermittedcases ตาม G3backendminimum ยังคง disclosedvscandidate/unjudged/rights boundaries ไม่อ้าง no-codeUI หรือ businessvalidation จาก CLI

## Acceptance และ stopping

| Milestone | Evidence ต้องมี |
|---|---|
| Repairs | Before/aftersemanticcounterexamples; clean exact-headtests; skips ระบุ dependency จริง |
| Runtime bundle | No gold access, stableID/text hashes, rights/model/config manifest |
| Remote job | Exact SSH/jobcommands+allocation+actualcanary/fullrun receipts ไม่ใช่ proposed อย่างเดียว |
| Vector portability | Shards/hash/order/count ครบ; interruptedresume; verifiedlocalimport และ negativechecks |
| Shared retrieval | Actualreturnedvectors ใช้ทั้ง evaluation และ dossierbackend;localqueryencodercompatible |
| Results | MatchedBM25/dense/hybridrawranks+correctmetrics/resources;task/label/self-policylimits ชัด |
| Backend | Real source/edit/history/exportdemo;ClaudeUIpreservedandpending |
| Handoff | Repo-localaudit/report/manifests/nextactions+exacttestedrevision;noinventedcompletion |

OpenRouter ไม่จำเป็นต่อ goal นี้ งบ round1 เดิมยัง cumulativeUSD8 acrossmilestones/resumes/agents ไม่ใช่ grant ใหม่ ต้องดู actualspent/pending/remaining จาก canonicalledger เดิม ไม่ถือว่าเหลือ8 ใหม่ แก้ canonicalledgergap ก่อน futurelive และไม่ resetoldjournal ไม่เติมเงิน/ซื้อ subscription/newkey/securitysettings/deploy/outreach เอง

Commit เฉพาะ scoped tested backend/data/vector files บน branch ของ Luna เอง รักษา Claude UI branch/worktree และทุก dirty/untracked file ไม่ automatic merge หรือ push เข้า main จาก goal นี้ บันทึก publication authority, file ownership, tests, secret/privacy/license checks และ remote/base state แยกก่อนเสนอการ publish ตาม current explicit owner/workflow authority การอนุญาต commit/push main ในอดีตคงเป็น historical context ไม่ใช่อำนาจ publish ใหม่จาก audit ห้าม force push หรือแก้ branch ของ Claude
